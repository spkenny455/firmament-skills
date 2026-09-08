#!/usr/bin/env python3
"""Prepare one selected Codex rollout for a local audit. Python standard library only."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re

# Same origin markers as Hive/internal/capture/codex.go; retain, don't erase, context.
INJECTED = (
    "<recommended_plugins>", "<environment_context>", "<turn_aborted>",
    "<user_instructions>", "# AGENTS.md instructions",
    "The following is the Codex agent history",
)


def current_source():
    task_id = os.environ.get("CODEX_THREAD_ID", "")
    if not re.fullmatch(r"[A-Za-z0-9-]{1,100}", task_id):
        raise ValueError("No usable CODEX_THREAD_ID. Select an original rollout with --input.")
    root = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "sessions"
    matches = list(root.rglob(f"rollout-*{task_id}.jsonl"))
    if len(matches) != 1:
        raise ValueError(f"Found {len(matches)} matching transcripts. Select one with --input.")
    return matches[0], task_id


def readable(value, omitted):
    if isinstance(value, list):
        return [readable(v, omitted) for v in value]
    if not isinstance(value, dict):
        return value
    if value.get("type") in {"input_image", "image", "image_url"}:
        omitted["image_blocks"] += 1
        return {"type": value["type"], "audit_omitted": "image payload"}
    result = {}
    for key, item in value.items():
        if key == "encrypted_content":
            omitted["encrypted_content_fields"] += 1
        else:
            result[key] = readable(item, omitted)
    return result


def prepare(source, output, expected_id=None, chunk_chars=40000):
    source = source.resolve()
    # Freeze the byte boundary: the live task may append while this helper runs.
    with source.open("rb") as stream:
        data = stream.read(os.fstat(stream.fileno()).st_size)
    if data and not data.endswith(b"\n"):
        raise ValueError("Transcript ends mid-record. Retry once after the writer completes.")
    rows = []
    for number, line in enumerate(data.decode("utf-8").splitlines(), 1):
        if line.strip():
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON on source line {number}; no audit written.") from error
            if not isinstance(row, dict):
                raise ValueError(f"Expected an object on source line {number}.")
            if row.get("type") in {"session_meta", "response_item", "compacted"} and not isinstance(row.get("payload"), dict):
                raise ValueError(f"Expected a payload object on source line {number}.")
            if row.get("type") == "session_meta" and not isinstance(row["payload"].get("id"), str):
                raise ValueError(f"Expected a session ID on source line {number}.")
            rows.append((number, row))
    ids = {row.get("payload", {}).get("id") for _, row in rows if row.get("type") == "session_meta"}
    if len(ids) != 1 or not next(iter(ids)) or (expected_id and ids != {expected_id}):
        raise ValueError("Session identity is absent, mixed, or different from the current task.")
    omitted = Counter()
    types = Counter()
    blocks = []
    for line, row in rows:
        kind = row.get("type", "unknown")
        types[kind] += 1
        if kind not in {"response_item", "compacted"}:
            omitted[f"record:{kind}"] += 1
            continue
        payload = row.get("payload", {})
        if payload.get("type") == "reasoning":
            omitted["reasoning_records"] += 1
            continue
        payload = readable(payload, omitted)
        role = payload.get("role", "")
        content = payload.get("content", [])
        text = "".join(v.get("text", "") for v in content if isinstance(v, dict)) if isinstance(content, list) else str(content)
        origin = "harness" if role == "developer" or (role == "user" and text.lstrip().startswith(INJECTED)) else "recorded"
        body = json.dumps(payload, ensure_ascii=False, indent=2)
        # Split oversized outputs without dropping bytes; part references keep their source line.
        parts = [body[i:i + chunk_chars] for i in range(0, len(body), chunk_chars)]
        for part, value in enumerate(parts, 1):
            blocks.append(f"SOURCE L{line} | {kind} | {origin} | {row.get('timestamp', '')} | part {part}/{len(parts)}\n{value}\n")
    if not any(row.get("type") == "response_item" for _, row in rows):
        raise ValueError("No conversation records found.")
    chunks, pending = [], ""
    for block in blocks:
        if pending and len(pending) + len(block) > chunk_chars:
            chunks.append(pending)
            pending = ""
        pending += block + "\n"
    if pending:
        chunks.append(pending)
    manifest = {
        "agent": "codex", "session_id": next(iter(ids)), "source_path": str(source),
        "source_bytes": len(data), "source_sha256": hashlib.sha256(data).hexdigest(),
        "record_types": dict(types), "omitted": dict(omitted),
        "completeness": "unverified; normalized saved records, not a complete execution archive",
        "redaction": "no general secret redaction; local private evidence only",
        "characters_to_read": sum(map(len, chunks)),
        "chunks": [f"chunk-{i:04d}.txt" for i in range(1, len(chunks) + 1)],
    }
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, body in [("manifest.json", json.dumps(manifest, indent=2))] + list(zip(manifest["chunks"], chunks)):
        with (output / name).open("x", encoding="utf-8") as stream:
            os.chmod(output / name, 0o600)
            stream.write(body)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="An explicitly selected Codex rollout")
    parser.add_argument("--out", type=Path, required=True, help="New private output directory")
    args = parser.parse_args()
    try:
        source, expected = (args.input, None) if args.input else current_source()
        result = prepare(source, args.out, expected)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Cannot prepare audit: {error}\n")
    print(json.dumps({"manifest": str(args.out / "manifest.json"), "chunks": len(result["chunks"]), "characters_to_read": result["characters_to_read"]}))


if __name__ == "__main__":
    main()

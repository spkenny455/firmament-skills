"""Run directly with Python: checks selection, evidence preservation and refusal cases."""
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
from prepare_codex import current_source, prepare


def check():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = root / "sessions"
        store.mkdir()
        source = store / "rollout-old-task-123.jsonl"
        tool_text = "evidence-" * 80
        rows = [
            {"type": "session_meta", "payload": {"id": "task-123"}},
            {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "# AGENTS.md instructions\nBaseline"}]}},
            {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Retry with the same request key."}, {"type": "input_image", "image_url": "data:image/png;base64,PRIVATE_IMAGE"}]}},
            {"type": "response_item", "payload": {"type": "function_call_output", "call_id": "call-a", "output": tool_text}},
            {"type": "compacted", "payload": {"message": "Compaction boundary"}},
        ]
        source.write_text("".join(json.dumps(row) + "\n" for row in rows))
        (store / "rollout-new-other-456.jsonl").write_text("do not inspect unrelated contents")
        with patch.dict(os.environ, {"CODEX_HOME": str(root), "CODEX_THREAD_ID": "task-123"}):
            assert current_source() == (source, "task-123")
        out = root / "audit"
        manifest = prepare(source, out, "task-123", chunk_chars=120)
        joined = "\n".join((out / name).read_text() for name in manifest["chunks"])
        assert "PRIVATE_IMAGE" not in joined and manifest["omitted"]["image_blocks"] == 1
        assert "| harness |" in joined and "Compaction boundary" in joined
        # Join source L4 parts to ensure splitting lost none of the actual tool evidence.
        parts = []
        for name in manifest["chunks"]:
            for block in (out / name).read_text().split("SOURCE ")[1:]:
                header, body = block.split("\n", 1)
                if header.startswith("L4 |"):
                    parts.append(body.rstrip("\n"))
        assert json.loads("".join(parts))["output"] == tool_text
        for expected, target in [("wrong-task", root / "wrong"), ("task-123", out)]:
            try:
                prepare(source, target, expected)
                raise AssertionError("Expected rejection")
            except (ValueError, FileExistsError):
                pass
        source.write_text(source.read_text() + '{"type":')
        try:
            prepare(source, root / "partial")
            raise AssertionError("Expected partial-record rejection")
        except ValueError:
            assert not (root / "partial").exists()
    print("PASS: current-session selection, source evidence, image omission, mismatch/overwrite/partial refusal")


if __name__ == "__main__":
    check()

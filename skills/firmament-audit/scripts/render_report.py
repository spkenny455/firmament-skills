#!/usr/bin/env python3
"""Render findings into an offline A4 SVG/HTML card. No third-party packages."""
import argparse
import base64
from collections import Counter
from html import escape
import json
from pathlib import Path
import re
import textwrap

ASSETS = Path(__file__).resolve().parent.parent / "assets"
PAPER, INK, RED, MUTED = "#F0EDE6", "#0C1D26", "#C03714", "#59656A"
KINDS = {"discovery": "Discoveries", "correction": "Corrections", "decision": "Decisions"}


def field(value, label, maximum=300):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{label} must be non-empty text of at most {maximum} characters.")
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", value):
        raise ValueError(f"{label} contains unsupported control characters.")
    return value.strip()


def records(value, label):
    if not isinstance(value, list) or any(not isinstance(v, dict) for v in value):
        raise ValueError(f"{label} must be a list of objects.")
    ids = [field(v.get("id"), f"{label}.id", 100) for v in value]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate IDs in {label}; deduplicate before rendering.")
    return value


def data_uri(path):
    mime = "image/svg+xml" if path.suffix == ".svg" else "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def render(data):
    if not isinstance(data, dict) or not isinstance(data.get("card"), dict):
        raise ValueError("Provide an object with card, findings and issues; see report-data.md.")
    card = data["card"]
    agent = field(data.get("agent"), "agent", 35)
    scope = field(card.get("scope"), "card.scope", 85)
    note = field(card.get("starting_note"), "card.starting_note", 155)
    coverage = field(card.get("coverage_note"), "card.coverage_note", 105)
    findings = records(data.get("findings"), "findings")
    issues = records(data.get("issues"), "issues")
    supported = []
    for f in findings:
        if f.get("kind") not in KINDS or f.get("support") not in {"direct", "summary_only", "unverified"}:
            raise ValueError("Every finding needs a valid kind and support classification.")
        if f["support"] == "direct":
            evidence = f.get("established_evidence")
            if not isinstance(evidence, list) or not evidence or not isinstance(evidence[0], dict):
                raise ValueError("Direct findings require established_evidence with a quote and source.")
            field(evidence[0].get("quote"), "evidence.quote", 10000)
            field(evidence[0].get("source"), "evidence.source", 1000)
            supported.append(f)
    counts = Counter(f["kind"] for f in supported)
    by_id = {f["id"]: f for f in supported}
    selected = card.get("featured_ids", list(by_id)[:3])
    if not isinstance(selected, list) or any(not isinstance(v, str) for v in selected):
        raise ValueError("featured_ids must be a list of finding IDs.")
    if len(selected) > 3 or len(selected) != len(set(selected)) or any(v not in by_id for v in selected):
        raise ValueError("Feature up to three distinct, directly supported findings.")
    if len(supported) > 9999 or len(issues) > 9999:
        raise ValueError("This card is for one or two conversations, not a bulk dataset.")

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="210mm" height="297mm" viewBox="0 0 840 1188" role="img" aria-labelledby="title desc"><title id="title">Firmament conversation report</title><desc id="desc">{escape(scope)}. {len(supported)} supported lessons, {len(issues)} issues, {counts["correction"]} corrections. {escape(coverage)}</desc><rect width="840" height="1188" fill="{PAPER}"/>']

    def text(x, y, value, size=17, color=INK, family="Arial, Helvetica, sans-serif", weight="400", extra=""):
        svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" font-size="{size}" font-weight="{weight}" {extra}>{escape(str(value))}</text>')

    def para(x, y, value, width, lines, size=17, color=INK, family="Arial, Helvetica, sans-serif", extra=""):
        # Conservative wrapping keeps template text legible; fail rather than crop a finding.
        wrapped = textwrap.wrap(value, width=width, break_long_words=True, break_on_hyphens=False)
        if len(wrapped) > lines:
            raise ValueError(f"Text exceeds the card's {lines}-line space; shorten the card wording: {value[:45]}")
        for index, line in enumerate(wrapped):
            text(x, y + index * (size + 6), line, size, color, family, extra=extra)

    def line(y):
        svg.append(f'<path d="M48 {y}H792" stroke="#CCD0CB" stroke-width="1"/>')

    def picture(path, x, y, width, height):
        uri = data_uri(path)
        svg.append(f'<image x="{x}" y="{y}" width="{width}" height="{height}" href="{uri}" xlink:href="{uri}"/>')

    picture(ASSETS / "firmament.png", 48, 38, 37, 46)
    text(98, 71, "Firmament", 30, family="Hoefler Text, Georgia, serif")
    text(792, 65, "CONVERSATION REPORT", 12, MUTED, extra='text-anchor="end" letter-spacing="1"')
    line(106)
    text(48, 170, "Your next agent", 48, family="Hoefler Text, Georgia, serif")
    text(48, 220, "should know this.", 48, family="Hoefler Text, Georgia, serif")
    para(48, 251, scope, 90, 1, 15, MUTED)
    logo_name = data.get("agent_logo", "")
    if logo_name and not re.fullmatch(r"[a-z0-9-]+", logo_name):
        raise ValueError("agent_logo must be a bundled logo name.")
    logo = ASSETS / "agents" / f"{logo_name}.svg"
    if logo_name and logo.is_file():
        picture(logo, 638, 218, 25, 25)
        text(674, 238, agent, 16)
    else:
        text(792, 239, agent, 16, extra='text-anchor="end"')

    for x, value, label in [(48, len(supported), "Lessons worth keeping"), (310, len(issues), "Issues surfaced"), (572, counts["correction"], "User corrections")]:
        text(x, 328, value, 54)
        text(x, 357, label, 16, MUTED)
    line(382)
    text(48, 416, "What you taught it", 18)
    maximum = max(counts.values(), default=1) or 1
    for i, (kind, label) in enumerate(KINDS.items()):
        y = 439 + i * 27
        text(48, y + 12, label, 14, MUTED)
        svg.append(f'<rect x="154" y="{y}" width="155" height="14" rx="3" fill="#E1E2DB"/>')
        if counts[kind]:
            svg.append(f'<rect x="154" y="{y}" width="{155 * counts[kind] / maximum}" height="14" rx="3" fill="{RED if kind == "correction" else INK}"/>')
        text(325, y + 12, counts[kind], 14)
    text(400, 416, "A better starting point", 18)
    para(400, 445, note, 44, 4, 17, MUTED)

    for index, finding_id in enumerate(selected):
        f = by_id[finding_id]
        y = 550 + index * 174
        line(y - 18)
        title = field(f.get("title"), "finding.title", 52)
        summary = field(f.get("card_summary"), "finding.card_summary", 220)
        quote = field(f["established_evidence"][0]["quote"], "featured evidence.quote", 105)
        para(48, y + 15, title, 53, 1, 25, family="Hoefler Text, Georgia, serif")
        para(48, y + 46, summary, 83, 3, 17)
        para(60, y + 123, "“" + quote + "”", 82, 2, 16, MUTED, extra='font-style="italic"')
        svg.append(f'<path d="M48 {y+108}v35" stroke="{RED}" stroke-width="2"/>')

    if not selected:
        text(48, 590, "No supported lessons to feature yet.", 25, family="Hoefler Text, Georgia, serif")
        para(48, 626, "This input did not establish a lesson with direct evidence. The detailed retrospective can still contain useful questions and unresolved issues.", 78, 3, 17, MUTED)
    elif len(selected) < 3:
        y = 560 + len(selected) * 174
        para(48, y + 35, "The report features only what the available evidence supports.", 75, 2, 17, MUTED)
    line(1102)
    para(48, 1128, coverage, 115, 1, 12, MUTED)
    text(48, 1155, "Counts describe these findings, not the agent's memory.", 12, MUTED)
    text(792, 1155, "getfirmament.com", 12, MUTED, extra='text-anchor="end"')
    svg.append("</svg>")
    return "\n".join(svg)


def html_document(svg):
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Firmament conversation report</title><style>
*{box-sizing:border-box}body{margin:0;padding:24px;background:#dddeda;color:#0c1d26;font-family:Arial,Helvetica,sans-serif}.toolbar{max-width:840px;margin:0 auto 18px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}button{font:inherit;padding:10px 16px;border:1px solid #aab1ad;border-radius:6px;background:#f0ede6;cursor:pointer}button:first-child{background:#0c1d26;color:#f0ede6}#status{font-size:13px}main{max-width:840px;margin:auto;box-shadow:0 8px 30px #0001}main>svg{display:block;width:100%;height:auto}@page{size:A4 portrait;margin:0}@media print{body{padding:0;background:none}.toolbar{display:none}main{width:210mm;max-width:none;box-shadow:none}main>svg{width:210mm;height:297mm;display:block}}
</style></head><body><div class="toolbar"><button id="png" type="button">Download PNG</button><button id="pdf" type="button">Print / Save PDF</button><span id="status" role="status">Private file. Nothing is uploaded.</span></div><main>''' + svg + '''</main><script>
document.getElementById('pdf').addEventListener('click',()=>window.print());
document.getElementById('png').addEventListener('click',async()=>{
 const status=document.getElementById('status');status.textContent='Preparing image…';
 try{
  await document.fonts.ready;
  const source=new XMLSerializer().serializeToString(document.querySelector('main>svg'));
  const url=URL.createObjectURL(new Blob([source],{type:'image/svg+xml;charset=utf-8'}));
  const img=new Image();
  try {await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=url;});
   const canvas=document.createElement('canvas');canvas.width=2480;canvas.height=3508;
   canvas.getContext('2d').drawImage(img,0,0,2480,3508);
   const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
   if(!blob)throw new Error('No image produced');
   const download=URL.createObjectURL(blob);const a=document.createElement('a');a.href=download;a.download='firmament-report.png';a.click();setTimeout(()=>URL.revokeObjectURL(download),1000);
   status.textContent='Image ready. Nothing was uploaded.';
  } finally {URL.revokeObjectURL(url);}
 }catch(error){status.textContent='Image export failed in this browser. Use Print / Save PDF or the SVG file.';}
});
</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="New output directory")
    args = parser.parse_args()
    try:
        svg = render(json.loads(args.input.read_text(encoding="utf-8")))
        args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
        (args.out / "report.svg").write_text(svg, encoding="utf-8")
        (args.out / "report.html").write_text(html_document(svg), encoding="utf-8")
    except (ValueError, OSError) as error:
        parser.exit(1, f"Cannot render report: {error}\n")
    print(json.dumps({"html": str(args.out / "report.html"), "svg": str(args.out / "report.svg")}))


if __name__ == "__main__":
    main()

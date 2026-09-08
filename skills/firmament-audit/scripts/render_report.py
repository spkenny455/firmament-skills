#!/usr/bin/env python3
"""Fill the fixed Firmament A4 card from report-data.json. Python standard library only."""
import argparse
import base64
from collections import Counter
from html import escape
import json
from pathlib import Path
import re
import textwrap
import xml.etree.ElementTree as ET

ASSETS = Path(__file__).resolve().parent.parent / 'assets'
PAPER, INK, RED, MUTED = '#F0EDE6', '#0C1D26', '#C03714', '#59656A'
GROUPS = {'used': ('Helped', 'this time'), 'missed': ('Could help', 'sooner'), 'new': ('Learned', 'this time')}


def field(value, label, words, chars):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} must be non-empty text.')
    value = ' '.join(value.split())
    if len(value) > chars or len(value.split()) > words:
        raise ValueError(f'{label}: shorten to {words} words and {chars} characters or fewer.')
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', value):
        raise ValueError(f'{label} contains unsupported control characters.')
    return value


def checked(data):
    if not isinstance(data, dict) or data.get('template_version') != 2:
        raise ValueError('Use template_version 2; see references/report-data.md.')
    allowed = {'template_version', 'agent', 'agent_logo', 'headline', 'description', 'findings', 'featured_ids'}
    if set(data) - allowed:
        raise ValueError('Unexpected input fields. Layout, colors, labels and computed counts are fixed.')
    d = dict(data)
    for key, words, chars in [('agent', 3, 18), ('headline', 9, 66), ('description', 18, 115)]:
        d[key] = field(data.get(key), key, words, chars)
    logo = data.get('agent_logo', '')
    if not isinstance(logo, str) or logo not in {'', 'codex', 'claude'}:
        raise ValueError('agent_logo must be codex, claude or empty.')
    d['agent_logo'] = logo
    findings = data.get('findings')
    if not isinstance(findings, list) or len(findings) > 999:
        raise ValueError('findings must be a list with at most 999 entries.')
    ids, supported = set(), {}
    for f in findings:
        if not isinstance(f, dict):
            raise ValueError('Each finding must be an object.')
        fid = field(f.get('id'), 'finding.id', 1, 80)
        if fid in ids:
            raise ValueError('Duplicate finding ID; deduplicate before rendering.')
        ids.add(fid)
        if not isinstance(f.get('status'), str) or not isinstance(f.get('support'), str) or f['status'] not in {*GROUPS, 'unclear'} or f['support'] not in {'direct', 'summary_only', 'unverified'}:
            raise ValueError('Invalid finding status or support.')
        if f['support'] == 'direct':
            evidence = f.get('evidence')
            if not isinstance(evidence, list) or not evidence or any(not isinstance(e, dict) for e in evidence):
                raise ValueError('Direct findings need evidence objects with source and quote.')
            for e in evidence:
                field(e.get('source'), 'evidence.source', 150, 1200)
                field(e.get('quote'), 'evidence.quote', 1000, 6000)
            if f['status'] != 'unclear':
                supported[fid] = f
    selected = data.get('featured_ids')
    if not isinstance(selected, list) or any(not isinstance(x, str) for x in selected):
        raise ValueError('featured_ids must be a list of IDs.')
    if len(selected) > 2 or len(set(selected)) != len(selected) or any(x not in supported for x in selected):
        raise ValueError('Select up to two distinct supported findings.')
    featured = []
    for fid in selected:
        f = supported[fid]
        featured.append({key: field(f.get(key), key, words, chars) for key, words, chars in [
            ('title', 6, 48), ('happened', 12, 72), ('next_time', 12, 72)]})
    return d, Counter(f['status'] for f in supported.values()), featured


def render(data):
    d, counts, featured = checked(data)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="210mm" height="297mm" viewBox="0 0 840 1188" role="img" aria-labelledby="title" data-template="firmament-audit-v2"><title id="title">{escape(d["headline"])}</title><rect width="840" height="1188" fill="{PAPER}"/>']
    copy = []

    def text(x, y, value, size=22, color=INK, serif=False, anchor='start', brand=False):
        family = 'Hoefler Text, Georgia, serif' if serif else 'Arial, Helvetica, sans-serif'
        svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" font-size="{size}" text-anchor="{anchor}">{escape(str(value))}</text>')
        if not brand:
            copy.append(str(value))

    def para(x, y, value, width, lines, size=22, color=INK, serif=False):
        wrapped = textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False)
        if len(wrapped) > lines or any(len(line) > width for line in wrapped):
            raise ValueError('Copy does not fit its fixed slot. Shorten the wording; do not change the layout.')
        for i, row in enumerate(wrapped):
            text(x, y+i*(size+7), row, size, color, serif)

    def rect(x, y, w, h, fill, rx=0, extra=''):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {extra}/>')

    def picture(name, x, y, w, h):
        path = ASSETS / name
        mime = 'image/svg+xml' if path.suffix == '.svg' else 'image/png'
        uri = f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode()
        svg.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="{uri}" xlink:href="{uri}"/>')

    picture('firmament.png', 48, 39, 37, 46)
    text(98, 72, 'Firmament', 30, serif=True, brand=True)
    if d['agent_logo']:
        picture('agents/'+d['agent_logo']+'.svg', 757-len(d['agent'])*10, 49, 25, 25)
    text(792, 70, d['agent'], 18, anchor='end', brand=True)
    svg.append('<path d="M48 110H792" stroke="#CED1CA"/>')
    para(48, 177, d['headline'], 33, 2, 45, serif=True)
    para(48, 277, d['description'], 58, 2, 22, MUTED)

    rect(48, 342, 744, 282, '#E6E5DD', 12)
    maximum = max(counts.values(), default=1) or 1
    for i, (key, label) in enumerate(GROUPS.items()):
        x = 172 + i*248
        text(x, 404, counts[key], 50, anchor='middle')
        height = 130*counts[key]/maximum
        rect(x-60, 426, 120, 130, '#D7DCD3', 4)
        rect(x-60, 556-height, 120, height, RED if key == 'missed' else INK, 4, f'data-series="{key}"')
        text(x, 586, label[0], 21, anchor='middle')
        text(x, 612, label[1], 21, anchor='middle')

    for i in range(2):
        y = 654+i*232
        rect(48, y, 744, 210, INK if i == 0 else '#E6E5DD', 12)
        color = PAPER if i == 0 else INK
        muted = '#C3CCC8' if i == 0 else MUTED
        if i < len(featured):
            f = featured[i]
            para(76, y+42, f['title'], 48, 1, 28, color, True)
            text(76, y+78, 'What happened', 16, muted)
            text(454, y+78, 'Next time', 16, muted)
            para(76, y+109, f['happened'], 24, 3, 24, color)
            para(454, y+109, f['next_time'], 24, 3, 24, color)
            svg.append(f'<path d="M410 {y+130}h18m-7 -7l7 7-7 7" fill="none" stroke="{RED if i else "#ECA28B"}" stroke-width="2"/>')
        else:
            text(76, y+62, 'No example selected', 28, color, True)
            text(76, y+105, 'See the full notes for detail.', 22, muted)
    svg.append('</svg>')
    if len(' '.join(copy).split()) > 120:
        raise ValueError('Poster exceeds 120 words. Shorten the input copy.')
    return '\n'.join(svg)


def poster_words(svg):
    root = ET.fromstring(svg)
    texts = [n.text or '' for n in root.findall('{http://www.w3.org/2000/svg}text')]
    return sum(len(t.split()) for t in texts[2:])  # First two nodes are brand and agent.


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
    print(json.dumps({"html": str(args.out / "report.html"), "svg": str(args.out / "report.svg"), "template_version": 2, "word_count": poster_words(svg)}))


if __name__ == "__main__":
    main()

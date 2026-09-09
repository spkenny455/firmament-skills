#!/usr/bin/env python3
"""Render the fixed, local Firmament knowledge audit card. Python standard library only."""
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
STATES = {'saved': ('Saved', INK), 'partial': ('Part saved', '#AD8064'),
          'chat_only': ('Chat only', RED), 'unknown': ('Not checked', '#BDBDB5')}
KINDS = {'lesson', 'decision', 'fix'}


def field(value, label, words=1000, chars=8000):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} must be non-empty text.')
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', value):
        raise ValueError(f'{label} contains unsupported control characters.')
    value = ' '.join(value.split())
    if len(value) > chars or len(value.split()) > words:
        raise ValueError(f'{label}: shorten to {words} words and {chars} characters or fewer.')
    return value


def evidence(value, label):
    if not isinstance(value, list) or not value:
        raise ValueError(f'{label} needs source/quote evidence.')
    for e in value:
        if not isinstance(e, dict): raise ValueError(f'{label}: expected evidence object.')
        field(e.get('source'), label+'.source')
        field(e.get('quote'), label+'.quote')


def checked(data):
    allowed = {'template_version', 'agent', 'agent_logo', 'headline', 'insight',
               'insight_ids', 'coverage', 'artifacts', 'findings', 'featured_ids'}
    if not isinstance(data, dict) or data.get('template_version') != 5:
        raise ValueError('Use template_version 5; see references/report-data.md.')
    if set(data) - allowed: raise ValueError('Unexpected fields; the layout and metrics are fixed.')
    d = dict(data)
    for key, words, chars in [('agent', 3, 18), ('headline', 12, 68), ('insight', 45, 280)]:
        d[key] = field(d.get(key), key, words, chars)
    if d.get('agent_logo', '') not in ('', 'codex', 'claude'):
        raise ValueError('agent_logo must be codex, claude or empty.')
    d.setdefault('agent_logo', '')
    coverage = d.get('coverage')
    if not isinstance(coverage, dict): raise ValueError('Describe the conversation and artifact coverage.')
    for key in ('conversation', 'artifacts', 'limits'): field(coverage.get(key), 'coverage.'+key)
    artifacts = d.get('artifacts')
    if not isinstance(artifacts, list): raise ValueError('artifacts must be a list.')
    artifact_ids = set()
    for a in artifacts:
        if not isinstance(a, dict): raise ValueError('Each artifact must be an object.')
        aid = field(a.get('id'), 'artifact.id', 1, 80)
        if aid in artifact_ids: raise ValueError('Duplicate artifact ID.')
        artifact_ids.add(aid)
        field(a.get('location'), 'artifact.location')
        field(a.get('checked'), 'artifact.checked')
        if a.get('existed_before_audit') is not True:
            raise ValueError('Audit-created files cannot be counted as prior storage.')
    findings = d.get('findings')
    if not isinstance(findings, list) or len(findings) > 999:
        raise ValueError('findings must be a list of at most 999 distinct knowledge items.')
    ids, supported, unique = set(), {}, set()
    for f in findings:
        if not isinstance(f, dict): raise ValueError('Each finding must be an object.')
        fid = field(f.get('id'), 'finding.id', 1, 80)
        knowledge = field(f.get('knowledge'), 'finding.knowledge')
        key = knowledge.casefold()
        if fid in ids or key in unique: raise ValueError('Duplicate finding; merge repeated statements of the same knowledge.')
        ids.add(fid); unique.add(key)
        if f.get('kind') not in KINDS: raise ValueError('kind must be lesson, decision or fix.')
        field(f.get('why'), 'finding.why')
        if f.get('support') not in ('direct', 'summary_only', 'unverified'):
            raise ValueError('Invalid finding support.')
        r = f.get('retention')
        if not isinstance(r, dict) or r.get('status') not in STATES:
            raise ValueError('Invalid retention status.')
        field(r.get('reason'), 'retention.reason')
        refs = r.get('artifact_ids')
        if not isinstance(refs, list) or any(not isinstance(x, str) or x not in artifact_ids for x in refs):
            raise ValueError('retention.artifact_ids must reference inspected artifacts.')
        if len(refs) != len(set(refs)): raise ValueError('Duplicate artifact reference.')
        status = r['status']
        if f['support'] != 'direct':
            if status != 'unknown': raise ValueError('Unverified or summary-only findings must stay unknown.')
            continue
        evidence(f.get('evidence'), 'finding.evidence')
        if status != 'unknown' and not refs:
            raise ValueError('A storage claim needs an inspected artifact; otherwise use unknown.')
        if status in ('saved', 'partial'):
            evidence(r.get('evidence'), 'retention.evidence')
            if any(e['source'] not in refs for e in r['evidence']):
                raise ValueError('Storage evidence must name a referenced artifact ID.')
        if status in ('partial', 'chat_only'): field(r.get('missing'), 'retention.missing')
        if f['kind'] == 'decision' and status == 'saved' and r.get('rationale_saved') is not True:
            raise ValueError('A saved decision must preserve its reason, not just the resulting choice.')
        supported[fid] = f
    for key, maximum in [('featured_ids', 2), ('insight_ids', 999)]:
        selected = d.get(key)
        if not isinstance(selected, list) or any(not isinstance(x, str) for x in selected):
            raise ValueError(f'{key} must be a list of finding IDs.')
        if len(selected) > maximum or len(set(selected)) != len(selected) or any(x not in supported for x in selected):
            raise ValueError(f'{key} must reference distinct directly supported findings.')
    if supported and (not d['featured_ids'] or not d['insight_ids']):
        raise ValueError('Show a real example and ground the insight in supported findings.')
    featured = []
    for fid in d['featured_ids']:
        f = supported[fid]
        featured.append({'status': f['retention']['status'],
                         'title': field(f.get('title'), 'title', 7, 43),
                         'detail': field(f.get('detail'), 'detail', 23, 135),
                         'impact': field(f.get('impact'), 'impact', 15, 95)})
        field(f.get('impact_basis'), 'impact_basis')
    return d, Counter(f['retention']['status'] for f in supported.values()), featured


def render(data):
    d, counts, featured = checked(data)
    total = sum(counts.values())
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="210mm" height="297mm" viewBox="0 0 840 1188" role="img" aria-labelledby="title" data-template="firmament-audit-v5"><title id="title">{escape(d["headline"])}</title><rect width="840" height="1188" fill="{PAPER}"/>']
    copy = []

    def text(x, y, value, size=22, color=INK, serif=False, anchor='start', brand=False):
        family = 'Hoefler Text, Georgia, serif' if serif else 'Arial, Helvetica, sans-serif'
        svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" font-size="{size}" text-anchor="{anchor}">{escape(str(value))}</text>')
        if not brand: copy.append(str(value))

    def para(x, y, value, width, lines, size=22, color=INK, serif=False, box_width=None, bottom=None):
        wrapped = textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False)
        bottom = bottom if bottom is not None else y+(lines-1)*(size+7)+size*.3
        if (len(wrapped) > lines or any(len(line) > width for line in wrapped)
                or y+(len(wrapped)-1)*(size+7)+size*.3 > bottom):
            raise ValueError(f'Copy does not fit its fixed slot ({lines} lines): {value!r}. Shorten the wording; do not change the layout.')
        svg.append(f'<g data-slot="text" data-x="{x}" data-top="{y-size*1.15}" data-width="{box_width or width*size*.6}" data-bottom="{bottom}">')
        for i, row in enumerate(wrapped): text(x, y+i*(size+7), row, size, color, serif)
        svg.append('</g>')

    def rect(x, y, w, h, fill, rx=0, extra=''):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {extra}/>')

    def picture(name, x, y, w, h):
        p = ASSETS / name
        mime = 'image/svg+xml' if p.suffix == '.svg' else 'image/png'
        uri = f'data:{mime};base64,' + base64.b64encode(p.read_bytes()).decode()
        svg.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="{uri}" xlink:href="{uri}"/>')

    picture('firmament.png', 48, 35, 28, 35)
    text(87, 61, 'Firmament', 26, serif=True, brand=True)
    if d['agent_logo']: picture('agents/'+d['agent_logo']+'.svg', 760-len(d['agent'])*10, 41, 22, 22)
    text(792, 60, d['agent'], 17, anchor='end', brand=True)
    para(48, 137, d['headline'], 33, 2, 46, serif=True, box_width=744, bottom=209)

    for i, (number, label, color) in enumerate([
        (total, 'Things learned', INK), (counts['saved'], 'Fully saved', INK),
        (counts['chat_only'], 'Chat only', RED)]):
        x = 48+i*252
        rect(x, 232, 240, 143, '#FAF8F3', 12, 'data-panel="metric"')
        text(x+22, 325, number, 78, color)
        text(x+22, 353, label, 21, MUTED)

    rect(48, 395, 744, 165, '#E6E4DC', 12, 'data-panel="retention"')
    text(72, 429, 'What was kept?', 25, serif=True)
    text(768, 429, 'In the places checked', 15, MUTED, anchor='end')
    rect(72, 450, 696, 31, '#D5D5CD', 4)
    start = 72
    for state, (label, color) in STATES.items():
        width = 696*counts[state]/total if total else 0
        if width:
            rect(start, 450, width, 31, color, extra=f'data-state="{state}" data-count="{counts[state]}"')
            start += width
    for i, (state, (label, color)) in enumerate(STATES.items()):
        x = 72+i*176
        rect(x, 502, 9, 9, color, 2)
        text(x+17, 516, counts[state], 27)
        text(x, 542, label, 18, MUTED)
    if not total: text(420, 472, 'Not enough evidence to count', 19, MUTED, anchor='middle')

    para(48, 604, d['insight'], 62, 5, 23, box_width=744, bottom=738)
    for i in range(2):
        x = 48+i*378
        rect(x, 760, 366, 334, '#FAF8F3', 12, 'data-panel="example"')
        if i < len(featured):
            f = featured[i]
            label, color = STATES[f['status']]
            text(x+24, 793, label, 15, color)
            para(x+24, 830, f['title'], 27, 2, 24, serif=True, box_width=318, bottom=871)
            para(x+24, 903, f['detail'], 34, 3, 19, box_width=318, bottom=965)
            rect(x+24, 980, 318, 1, '#D8D5CC')
            para(x+24, 1007, f['impact'], 31, 3, 21, color=color, box_width=318, bottom=1070)
        else:
            text(x+24, 830, 'No further finding', 23, MUTED, True)
            para(x+24, 880, 'This audit found no other clear example to show.', 33, 3, 19, MUTED, box_width=318, bottom=965)
    text(48, 1128, 'What is each conversation leaving behind?', 24, serif=True)
    text(48, 1160, 'github.com/spkenny455/firmament-skills', 15, MUTED)
    svg.append('</svg>')
    if len(' '.join(copy).split()) > 165: raise ValueError('Poster exceeds 165 words. Shorten the input copy.')
    return '\n'.join(svg)


def poster_words(svg):
    root = ET.fromstring(svg)
    texts = [n.text or '' for n in root.findall('.//{http://www.w3.org/2000/svg}text')]
    return sum(len(t.split()) for t in texts[2:])  # First two nodes are brand and agent.


def html_document(svg):
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Firmament conversation report</title><style>
*{box-sizing:border-box}body{margin:0;padding:24px;background:#dddeda;color:#0c1d26;font-family:Arial,Helvetica,sans-serif}.toolbar{max-width:840px;margin:0 auto 18px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}button{font:inherit;padding:10px 16px;border:1px solid #aab1ad;border-radius:6px;background:#f0ede6;cursor:pointer}button:first-child{background:#0c1d26;color:#f0ede6}#status{font-size:13px}main{max-width:840px;margin:auto;box-shadow:0 8px 30px #0001}main>svg{display:block;width:100%;height:auto}@page{size:A4 portrait;margin:0}@media print{body{padding:0;background:none}.toolbar{display:none}main{width:210mm;max-width:none;box-shadow:none}main>svg{width:210mm;height:297mm;display:block}}
</style></head><body><div class="toolbar"><button id="png" type="button">Download PNG</button><button id="pdf" type="button">Print / Save PDF</button><span id="status" role="status">Private file. Nothing is uploaded.</span></div><main>''' + svg + '''</main><script>
async function checkLayout(){
 await document.fonts.ready;
 const bad=[...document.querySelectorAll('[data-slot]')].filter(el=>{
  const b=el.getBBox(), d=el.dataset;
  return b.x < +d.x-1 || b.y < +d.top-1 || b.x+b.width > +d.x + +d.width+1 || b.y+b.height > +d.bottom+1;
 });
 if(bad.length)throw new Error('Text does not fit. Shorten the report data and render again.');
}
checkLayout().catch(error=>{
 document.getElementById('status').textContent=error.message;
 document.getElementById('png').disabled=true;document.getElementById('pdf').disabled=true;
});
document.getElementById('pdf').addEventListener('click',async()=>{
 try{await checkLayout();window.print();}catch(error){document.getElementById('status').textContent=error.message;}
});
document.getElementById('png').addEventListener('click',async()=>{
 const status=document.getElementById('status');status.textContent='Preparing image…';
 try{
  await checkLayout();
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
    print(json.dumps({"html": str(args.out / "report.html"), "svg": str(args.out / "report.svg"), "template_version": 5, "word_count": poster_words(svg)}))


if __name__ == "__main__":
    main()

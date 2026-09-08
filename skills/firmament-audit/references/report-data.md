# Report renderer input

Run `python3 scripts/render_report.py findings.json --out /path/to/new/report-directory` relative to the skill folder. It creates a standalone A4 SVG and an offline HTML viewer with Download PNG and Print / Save PDF controls. The HTML needs a browser; Python uses only the standard library. Do not publish the files automatically.

Add the following display fields to the private findings object. Other private evidence/retrospective fields are allowed and are not copied into the visual. Write short summaries rather than truncating evidence. `established_evidence[0].quote` is the featured exact excerpt; keep that excerpt at most 105 characters. Additional evidence entries can remain detailed.

```json
{
  "agent": "Codex",
  "agent_logo": "codex",
  "card": {
    "scope": "Selected findings from one conversation",
    "starting_note": "The specific knowledge that would make the next attempt easier.",
    "coverage_note": "Agent retrospective · selected examples, not a full transcript audit",
    "featured_ids": ["lesson-1"]
  },
  "findings": [
    {
      "id": "lesson-1",
      "kind": "correction",
      "support": "direct",
      "title": "A short lesson title",
      "card_summary": "The issue and the actionable lesson, in at most 220 characters.",
      "established_evidence": [
        {"source": "A real message or transcript reference", "quote": "An exact short excerpt from that source."}
      ]
    }
  ],
  "issues": [
    {"id": "issue-1", "summary": "A distinct issue actually encountered", "status": "resolved"}
  ]
}
```

This is a structural illustration, not evidence to include in an audit. Replace its content with actual findings.

`kind` is discovery, correction or decision. `support` is direct, summary_only or unverified. Only direct findings with source/evidence fields contribute to lesson counts and chart bars. The renderer checks structure, not whether a claim or quote is true: the agent must verify those. IDs must be deduplicated. Issues are counted separately and may overlap with lessons; they are not part of the chart's partition. The corrections metric counts lessons classified as user corrections, not demonstrated forgetting.

Feature at most three supported IDs. Other supported lessons still contribute to the aggregate counts. With no supported findings, the card states that there is no supported lesson to feature. It does not fabricate examples or divide by zero. Unknown agents can use their name without a logo; bundled logo IDs are codex and claude. Do not invent a vendor mark.

The fixed template rejects oversized copy rather than silently shrinking or clipping it. Titles: 52 characters; card summaries: 220; scope: 85; starting note: 155; coverage note: 105. Width/line constraints can require shorter text. Keep facts and exact quotes intact when shortening. Inspect the final output, particularly on hosts whose fallback fonts differ.

The PNG download is 2480 × 3508 pixels. Browser Print / Save PDF should use A4, zero margins and no browser headers/footers. If headless rendering is available, the agent can export and inspect a PNG/PDF directly; otherwise return HTML/SVG and describe the available controls. Do not claim that a PDF exists until it has been exported.

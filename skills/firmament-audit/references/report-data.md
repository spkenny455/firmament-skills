# Fixed share card input: version 3

The agent fills `report-data.json`; the bundled script makes the card. Do not write HTML, SVG, CSS or a replacement renderer. The same layout is used every time.

```json
{
  "template_version": 3,
  "agent": "Codex",
  "agent_logo": "codex",
  "headline": "Your agent had useful notes.",
  "description": "Those notes helped it choose the right test.",
  "spotlight_label": "Checks that helped",
  "events": [
    {
      "id": "E1",
      "label": "Check caught issue",
      "evidence": [{"source": "Actual test result", "quote": "Exact excerpt from that result"}]
    }
  ],
  "findings": [
    {
      "id": "S1",
      "topic": "Testing",
      "status": "used",
      "support": "direct",
      "title": "Test from empty",
      "next_time": "Run this check before shipping.",
      "evidence": [
        {"source": "Actual prior guidance", "quote": "Exact excerpt"},
        {"source": "Later action and result", "quote": "Exact excerpt"}
      ]
    }
  ],
  "featured_ids": ["S1"]
}
```

This is an input example, not an audit finding. Replace all content and evidence with the selected conversation's actual record.

## What fills each card

**Lead number:** the count of `events`. Choose one concrete event type relevant to the headline: repeated requests, checks that caught issues, or successful uses of prior guidance, for example. `spotlight_label` names exactly what is counted. All entries must be distinct, directly evidenced events of that same type in chronological order. Do not count hypothetical avoided actions, lessons and requests as one total. If none can be established, use an empty list and an honest headline. Never manufacture an event to fill the card.

**Event trail:** uses the labels of up to three actual events. For more than three, the renderer samples the first, middle and last in the supplied order; the main count still includes all provided events. It is an ordered sequence, not an elapsed-time chart. Keep the selection and coverage explanation in the retrospective. No invented alternate path appears here.

**Lesson count and bars:** computed from distinct directly supported findings with a clear status. Group findings into at most three short, plain `topic` labels that describe this task, such as Design, Testing or Setup. One primary topic per lesson; do not duplicate lessons to inflate counts. Bars show the partition of that lesson count, ordered by count and then name. Topics describe content, not a loss score.

**Two takeaways:** select up to two supported `featured_ids`. Each provides a title and a short useful `next_time` action. Optional private fields such as full prose or historical `happened` copy can stay in finding records but are not displayed. Missing examples retain the fixed card positions.

## Evidence and honest attribution

`status` retains the audit's private temporal assessment:

- `used`: prior knowledge observably informed a useful action; support both guidance and action/result.
- `missed`: applicable knowledge existed before the action but was missed, late or ignored; support availability, action and relevance. Improved results are a possibility, not measured savings.
- `new`: useful knowledge first established here, potentially useful next time. It may already have been saved. Its discovery cost is not automatically avoidable.
- `unclear`: timing or application not established; excluded from the count, bars and takeaways.

`support` is direct, summary_only or unverified. Only direct used/missed/new records count. Each direct finding and every counted event needs evidence objects with actual sources and exact excerpts. A source pointer alone does not prove a sequence. The renderer checks structure, not factual truth or causal sufficiency. The agent must verify that the headline, metric label, event list and conclusions agree. Do not invent missing knowledge, memory loss, time savings or praise for Firmament. No benefit found and insufficient evidence remain valid different conclusions.

## Fixed limits

- Headline: at most 9 words / 66 characters, two fixed lines; plain owner-facing conclusion.
- Description: one sentence, at most 18 words / 59 characters, one line.
- Agent: short name, at most 3 words / 18 characters. `agent_logo`: codex, claude or empty.
- Spotlight label: at most 4 words / 40 characters. Event label: at most 4 words / 32 characters, two lines.
- Topic: at most 2 words / 10 characters, up to three distinct topics.
- Takeaway title: at most 6 words / 42 characters, two lines. Next action: at most 12 words / 72 characters, three lines.
- Whole poster: at most 120 visible words. The fixed call to action counts toward that budget.

Shorten copy when a slot rejects it. Do not change fonts, box positions, colors or charts. Line constraints may require fewer characters than these maximums. Do not add dates, model versions, footnotes, quote panels, banners or custom scores. Keep material uncertainty in the claim and detailed evidence in retrospective.md.

## Render

Resolve the script path relative to the installed skill directory:

```sh
python3 scripts/render_report.py /path/to/report-data.json --out /path/to/new/report-directory
```

The standard-library Python script writes A4 `report.svg` and standalone `report.html`. The viewer's PNG download and Print / Save PDF controls sit outside the poster. PNG export is 2480 × 3508. Export these exact files with existing host tools when possible; do not recreate their design. Inspect at phone width. Local fallback fonts may vary. With no Python/file execution, return the completed data and retrospective honestly. A new output directory is required. All output remains local until the user chooses to share it.

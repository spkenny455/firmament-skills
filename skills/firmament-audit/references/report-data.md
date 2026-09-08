# Fixed report input: version 2

Fill `report-data.json`, then run the bundled renderer. Do not write HTML, SVG, CSS or a replacement renderer. The schema and layout are fixed. Source evidence and the full retrospective stay local.

```json
{
  "template_version": 2,
  "agent": "Codex",
  "agent_logo": "codex",
  "headline": "Your agent could catch the clutter sooner.",
  "description": "A check could catch long text before you have to ask.",
  "findings": [
    {
      "id": "S1",
      "status": "missed",
      "support": "direct",
      "title": "Check the word count",
      "happened": "The brief asked for less text.",
      "next_time": "Count words before sending the card.",
      "evidence": [
        {"source": "User message and later relevant result", "quote": "An exact excerpt from the selected conversation."}
      ]
    }
  ],
  "featured_ids": ["S1"]
}
```

This is a structural example, not evidence for a real audit. Replace all claims and evidence with the selected conversation's actual content. Use the agent's short name, not model version or project metadata. Bundled logo names: codex and claude. For another agent, use an empty logo string; its name still appears.

## Fixed chart definitions

Each distinct knowledge finding gets one primary status. Do not split the same lesson into multiple records just to increase counts.

- `used`: prior knowledge reached the agent and observably informed a useful action. Chart label: **Helped this time**. Needs evidence of the prior knowledge and the later action/result; retrieving a fact alone is insufficient.
- `missed`: specific relevant knowledge already existed before the action, but was missed, late or ignored. Chart label: **Could help sooner**. Needs evidence of availability, the action and why the knowledge applies. The benefit remains a reasoned possibility, not proven saved work. Do not put facts first discovered through that action here.
- `new`: useful knowledge was first established during the task. Chart label: **Learned this time**. It can help a future attempt without proving this task's discovery was avoidable. A new lesson may already have been saved.
- `unclear`: timing or application is not established; excluded from chart and feature slots.

`support` is direct, summary_only or unverified. Only directly supported used/missed/new findings count. Every direct record requires evidence entries with actual sources and exact excerpts. Include multiple entries where a claim depends on a sequence. The renderer checks structure, not the truth or causal sufficiency of the evidence; that is the agent's responsibility. Keep scope/coverage, reasoning and limits in retrospective.md. Keep material uncertainty in the headline, description or example itself.

Counts and bar lengths are computed; there are no editable count, chart, color or layout fields. Zero is allowed, including zero for every category. Do not equate zero classified records with proof that everything went perfectly.

## Fixed text slots

- Headline: at most 9 words / 66 characters, two lines. Plain owner-facing conclusion; no required positive conclusion.
- Description: at most 18 words / 115 characters, two lines. One sentence.
- Agent name: at most 3 words / 18 characters.
- Each featured finding: title at most 6 words / 48 characters; `happened` and `next_time` each at most 12 words / 72 characters.
- Choose at most two distinct supported `featured_ids`. Display fields are needed only for selected findings. If fewer are available, remaining slots show a fixed empty state; nothing moves or stretches.
- The renderer rejects text exceeding a line slot or the overall 120-word limit. Shorten the input without changing facts, not the template. Word/character limits are ceilings, not targets. Inspect final output because local font availability can vary.

Use this command with the script path resolved relative to the installed skill directory:

```sh
python3 scripts/render_report.py /path/to/report-data.json --out /path/to/new/report-directory
```

It writes A4 `report.svg` and standalone `report.html`. The viewer has a PNG download and Print / Save PDF control outside the poster. PNG export is 2480 × 3508. Use existing host tools to export those exact files if available; do not recreate their design for export. A new output directory is required to protect existing reports. Python uses only the standard library. If it cannot run, return the completed JSON and retrospective with the specific limitation; do not invent another layout.

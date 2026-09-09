# Fixed report data — version 4

The agent writes the analysis and data; the bundled script owns the design. Use this exact root schema. No extra metrics or layout fields. `retrospective.md` holds the full account, including superseded choices, issues, baseline knowledge and uncertainty. JSON is the traceable ledger behind the card.

## Counting rule

One finding is one distinct reusable lesson, decision with its reason, or fix/correction. Count only `support: "direct"` items with original source evidence. Deduplicate by meaning, not only text. Do not count baseline instructions, task steps, repeated mentions, hypotheses, or every failed attempt as separate learnings.

The renderer derives:

- **Things learned** = all directly supported findings, including those whose storage is unknown.
- **Fully saved** = directly supported findings with `retention.status: "saved"`.
- **Chat only** = directly supported findings with `retention.status: "chat_only"`.
- **Storage chart** = `saved`, `partial`, `chat_only`, `unknown`, in that order, on the same denominator. These sum to things learned. Partial items are never counted as fully saved or entirely chat-only.

These are counts within the reviewed evidence, not a whole-account score. Summary-only and unverified candidates are recorded but excluded from all poster counts and examples. Their storage state must be `unknown`. Direct source evidence can coexist with unknown storage; do not discard such findings or call them lost.

## Fields

| Field | Contract |
| --- | --- |
| `template_version` | `4` |
| `agent` | Display name, up to 3 words / 18 characters. Do not guess a model name. |
| `agent_logo` | `codex`, `claude`, or empty string for text fallback. Bundled and embedded by the script. |
| `headline` | One specific finding, up to 12 words / 76 characters; must fit three fixed lines. No generic report title or subtitle. |
| `insight` | Agent's own paragraph, up to 45 words / 280 characters, five lines. State the useful knowledge and its consequence, or an honest lack of evidence/gap. |
| `insight_ids` | IDs of direct findings grounding that paragraph. Required when any direct findings exist. Empty for an evidence-limited or empty audit. |
| `coverage` | Object with nonempty `conversation`, `artifacts`, `limits`. Say what was inspected and what could not be checked. Use “No additional limits identified” only if justified. Supporting data, not poster copy. |
| `artifacts` | Inspected storage locations, described below. Empty if none could be checked. |
| `findings` | Up to 999 distinct items. No minimum; do not force a desired number. |
| `featured_ids` | Up to two distinct direct finding IDs. At least one if direct findings exist. Choose consequential examples, including saved or unknown ones where appropriate. |

Every artifact has:

- `id`: unique short ID.
- `location`: the actual path or identifiable persistent record.
- `checked`: what relevant contents you inspected, and how this bears on preservation. Include any scope limitation. Mere existence is insufficient.
- `existed_before_audit`: `true`. Audit-created reports/notes never count as prior storage.

Every finding has:

- `id`, `kind` (`lesson`, `decision`, `fix`). Use one primary kind; a user correction can be a fix. These are analysis categories, not three separate poster quotas.
- `knowledge`: full reusable knowledge; preserve scope and exceptions.
- `why`: its practical importance, including the reason behind a decision.
- `support`: `direct`, `summary_only`, or `unverified`.
- `evidence`: direct findings require a nonempty list of `{ "source": "message/turn/tool reference", "quote": "exact excerpt" }`. Quote only material you can see.
- `retention`: storage state with the fields below.
- For featured findings only, `title` (up to 7 words / 43 characters) and `detail` (up to 23 words / 135 characters). Slots also have line limits. Say the concrete lesson and what survived or is missing. Do not merely repeat the status or write generic instructions. Public-facing excerpts should omit secrets and unnecessary identifying details; exact private evidence remains local.

Every `retention` has `status`, `reason` (why this status is justified) and `artifact_ids` (inspected artifact IDs). All states except `unknown` require at least one checked artifact. For `chat_only`, those checks must cover the relevant expected storage places, not an arbitrary unrelated file. If no relevant artifact can be checked, or key storage is inaccessible, use `unknown`.

For `saved` or `partial`, add `evidence`: source/quote objects, where `source` is a referenced artifact ID and `quote` is the exact stored text. Show enough to support the claim; don't use the original chat as storage evidence. Saved decisions additionally need `rationale_saved: true` and evidence of the reason. For `partial` or `chat_only`, add `missing`: the specific reusable information that the inspected artifacts lack. Unknowns explain the access/evidence gap in `reason`.

Saving a file or submitting a memory does not prove another agent retrieved it. Code that encodes behavior may preserve a fix fully if it is self-explanatory; code often preserves a decision only partly when its rationale is absent. Judge usefulness from the actual artifact rather than declaring all code inadequate or all code sufficient.

## Small synthetic example

This fixture illustrates a partial decision, not a required story or a claim about this conversation. Replace all content with actual evidence. Do not copy its numbers or text into a real audit.

```json
{
  "template_version": 4,
  "agent": "Agent",
  "agent_logo": "",
  "headline": "Your fix was saved. The reason was not.",
  "insight": "I kept the retry limit in the code, but left out why it matters. The next agent could raise it and bring back duplicate charges.",
  "insight_ids": ["K1"],
  "coverage": {
    "conversation": "Current conversation, original messages and tool results.",
    "artifacts": "Read the changed payment function and the task handoff.",
    "limits": "No other sessions or storage locations were inspected."
  },
  "artifacts": [
    {"id": "A1", "location": "payments.py", "checked": "Read retry logic and comments; the limit is stored without its reason.", "existed_before_audit": true},
    {"id": "A2", "location": "handoff.md", "checked": "Read the whole handoff; no payment retry guidance.", "existed_before_audit": true}
  ],
  "findings": [{
    "id": "K1",
    "kind": "decision",
    "knowledge": "Keep payment retries at one until requests use stable idempotency keys.",
    "why": "The payment provider can accept a request before a timeout, so another attempt can charge twice.",
    "support": "direct",
    "evidence": [{"source": "user message about payment retries", "quote": "Keep retries at one until we add idempotency keys; a timeout can happen after a charge."}],
    "retention": {
      "status": "partial",
      "reason": "The limit is in code; neither inspected artifact records the reason or the condition for raising it.",
      "artifact_ids": ["A1", "A2"],
      "evidence": [{"source": "A1", "quote": "MAX_PAYMENT_ATTEMPTS = 1"}],
      "missing": "Why the limit prevents duplicate charges and when it can safely change."
    },
    "title": "Why retries stop at one",
    "detail": "The limit is in the code. The risk of charging twice is only in the chat."
  }],
  "featured_ids": ["K1"]
}
```

## Honest edge cases

- All useful items saved: show those items, use an appropriately positive finding, and explain how the saved notes help. Do not invent a missed opportunity.
- No access to task outputs: set direct findings to unknown, use no artifact references, and make that limitation clear in the title or insight. Zero confirmed chat-only items does not mean zero gaps.
- No directly supported knowledge: empty featured/insight IDs; counts are zero, the chart says evidence is insufficient. Explain the reason instead of declaring perfect memory.
- One strong example: supply one featured ID. The second slot uses the fixed neutral empty state. Never pad the ledger to fill the layout.

## Render

Run the bundled `scripts/render_report.py` with the JSON path and a **new** `--out` directory. It rejects old versions and invalid evidence structure. It cannot judge whether a quote is true or whether an artifact search was sufficient; that remains the auditing agent's responsibility.

The A4 layout, embedded logos, palette, labels, storage chart and export controls are fixed. Copy has a 165-word total ceiling plus individual slot limits; the ceiling is not a target. The title, insight and two examples should do the work. No footnote block is printed. Coverage and full evidence stay available in the supporting files. If copy does not fit, edit the JSON and rerun; never alter the renderer during an audit.

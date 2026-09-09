# Firmament skills

## Firmament audit

Run an audit inside a difficult agent conversation. See what it learned, what it saved, and which lessons or decision reasons it left only in the chat.

```sh
npx skills add spkenny455/firmament-skills --skill firmament-audit -g
```

Choose your agent in the installer, then invoke `/firmament-audit` where slash commands are supported, or select the skill in your agent's picker. No extra prompt, Firmament installation or account is required.

The agent reviews the conversation and relevant existing outputs. It writes an evidence ledger and fills a fixed A4 card with derived counts, a knowledge storage chart, a short insight and concrete examples with their practical consequences. It can report that everything was saved, or that storage could not be checked. Knowledge found only in the chat is not automatically proof of forgetting.

Output stays local. The HTML has PNG download and print-to-PDF controls; actual export support depends on the host. Python 3 is required for the standard-library renderer and optional Codex evidence helper. Without execution, the agent returns the completed data and retrospective. Node/npm is needed only for the installer. No product tools, login or uploads are part of the audit.

The bundled renderer fixes the layout and embeds available agent logos, with a name fallback. The HTML checks rendered text bounds before export. See [the data contract](skills/firmament-audit/references/report-data.md) for the evidence and counting rules. Automated checks cover the renderer and transcript helper; cross-agent behavior has not received an end-to-end test.

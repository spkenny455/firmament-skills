# Firmament skills

## Firmament audit

Review one agent conversation and generate a simple visual report about what prior knowledge helped, what was missing, and what is worth keeping.

Install once:

```sh
npx skills add spkenny455/firmament-skills --skill firmament-audit -g
```

Choose your agent in the installer. Invoke firmament-audit through its skill picker or slash command where supported. No additional audit prompt or Firmament account is required. Output stays local. PNG/PDF generation depends on the host tools available.

The skill includes optional Python helpers and local brand assets. Node/npm is needed for the installer; Python 3 is needed for the report renderer and optional evidence helper. Other agents have not received an end-to-end behavioral test.

Reports use a fixed A4 template. The agent fills a small JSON file; the bundled Python renderer controls the card layout, event count, topic chart and copy limits. Python 3 is required to render the card. If unavailable, the skill returns the completed data and retrospective.

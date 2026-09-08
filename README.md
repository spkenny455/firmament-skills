# Firmament skills

## Firmament audit

Review one agent conversation and generate a simple visual report about what prior knowledge helped, what was missing, and what is worth keeping.

Install once:

```sh
npx skills add spkenny455/firmament-skills --skill firmament-audit -g
```

Choose your agent in the installer. Invoke firmament-audit through its skill picker or slash command where supported. No additional audit prompt or Firmament account is required. Output stays local. PNG/PDF generation depends on the host tools available.

The skill includes optional Python helpers and local brand assets. Node/npm is needed for the installer; Python 3 is needed only for the optional helpers. Other agents have not received an end-to-end behavioral test.

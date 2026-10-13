# bell-skills

Skills that teach an AI agent to run a [Bell Statistics](https://bellstatistics.com)
geo experiment the way Bell's statisticians do — prepare a client's data
without reading it, choose a sound design, and report a result without
overclaiming. It pairs with the Bell MCP connector, which provides the
tools; these skills provide the judgment.

Skills follow the [Agent Skills](https://agentskills.io) open standard and
work in Claude Code, Claude.ai, Cursor, Codex, GitHub Copilot, Gemini CLI
and any other compatible agent.

## What it adds over the bare connector

The connector alone gives an agent tool access: it can upload, run an
analysis, poll a job. It cannot tell a good design from a bad one, will
happily read a client's CSV into the conversation, and will report an
`"Infinity"` cost per action as a number. The skills close that gap:

| Skill | What it teaches |
|---|---|
| `bell-geo-experiments` | The entry point. Bell's working stance, the flow, do's and don'ts, an edge-case index, when to escalate. |
| `bell-data-prep` | Inspect the header and a bounded sample, write a pandas transform, validate locally, upload. Client rows never enter the transcript. Ships the inspector, validator and transform template. |
| `bell-design-verdict` | The green/yellow/red verdict and why the R²-only one is ignored. |
| `bell-reading-results` | Lift with interval, p-value against alpha, iCPA/iROAS, the Infinity sentinel. |
| `bell-common-failures` | The engine's real error text and the fix for each. |
| `bell-glossary` | Bell's definitions. |
| `bell-from-geolift` | Parameter map, data conversion and methodological differences for teams coming from Meta's GeoLift. |

The four methodology skills carry the same documents the connector serves
as MCP resources (`bell://methodology/…`).

## Install

You need a Bell client token (`bell_…`), issued by Bell. It is sent as the
`X-Client-Secret` header on every request the connector makes; the skills
themselves never see it.

### 1. Add the connector

Claude Code:

```bash
claude mcp add --transport http bell https://bell-mcp.onrender.com/mcp \
  --header "X-Client-Secret: bell_xxxxxxxx"
```

Claude.ai or Claude Desktop: an admin adds the same URL and header as a
custom connector.

### 2. Add the skills

**Claude Code** — as a plugin, which also keeps the skills up to date:

```
/plugin marketplace add Korem-consulting/bell-skills
/plugin install bell-skills@bell-statistics
```

**Claude.ai / Claude Desktop** — download the zips from the
[latest release](https://github.com/Korem-consulting/bell-skills/releases/latest)
and upload each one under *Settings → Capabilities → Skills*. Start with
`bell-geo-experiments` and `bell-data-prep`. Connectors and skills are
installed separately: adding the connector does not add the skills.

**Cursor, Codex, Copilot, Gemini CLI and other agents:**

```bash
npx skills add Korem-consulting/bell-skills
```

### 3. Say what you want

"Plan a geo test on this export" is enough; the `bell-geo-experiments`
skill loads first and routes.

## The scripts need Python

`bell-data-prep` ships small Python scripts (pandas; `openpyxl` for Excel,
`pyarrow` for parquet). They are what let the agent inspect and reshape
data without reading it. Install with `pip install pandas openpyxl pyarrow`.

## Updating

Claude Code: `/plugin marketplace update bell-statistics`. Claude.ai:
re-upload the zips from the newest release. Other agents: re-run
`npx skills add`.

## Support

Stuck on a dataset, an outlier you cannot explain, a verdict that will not
turn green? Send a short summary of what was tried — never raw rows — and
the validator's output to allon@bellstatistics.com.

## License

[Apache-2.0](LICENSE).

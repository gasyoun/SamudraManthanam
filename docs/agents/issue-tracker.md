# Issue Tracker

_Created: 26-08-2026 · Last updated: 26-08-2026_

This repo is **public** and uses **native GitHub Issues** as its tracker —
unlike the private `gasyoun/Uprava` hub, which routes all agent work through
internal `H###` handoff files instead. Do not import that handoff-only model
here.

- **Create:** open a GitHub Issue using one of the templates in
  [`.github/ISSUE_TEMPLATE/`](https://github.com/gasyoun/SamudraManthanam/tree/main/.github/ISSUE_TEMPLATE)
  (`bug_report.yml`, `feature_request.yml`, `question.yml`).
- **Execute:** work is delivered via a pull request that references the issue
  (`Closes #123`), per
  [`.github/PULL_REQUEST_TEMPLATE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/PULL_REQUEST_TEMPLATE.md).
  CI (`.github/workflows/ci.yml`) must be green before merge.
- **Close:** merging the referencing PR closes the issue automatically via the
  `Closes #123` keyword; otherwise close it by hand once the fix has shipped.
- **Cross-repo provenance:** when an issue or PR here originates from (or
  reports back into) an internal Uprava `H###` handoff, name that handoff ID
  in the issue/PR body — the `handoff` label marks issues opened this way. The
  handoff itself stays the source of truth for the internal work item; this
  repo's issue is the public-facing tracking record.
- **PR intake:** this repo does not solicit unsolicited external PRs. Issues
  are the entry point for reporting a problem or requesting a feature; a PR
  should generally follow from a triaged, labeled issue rather than arrive
  first.

When an internal skill or plan says "create an issue" or "publish a spec",
that maps directly onto opening a GitHub Issue here (not an `H###` handoff) —
the spec is the issue body, or a linked `docs/` file for anything long enough
to need one.

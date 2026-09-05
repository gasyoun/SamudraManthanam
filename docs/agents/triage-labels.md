# Triage Labels

_Created: 26-08-2026 · Last updated: 26-08-2026_

Skills and review agents speak in terms of five canonical triage roles. This
file maps those roles to the actual label strings used on
[gasyoun/SamudraManthanam issues](https://github.com/gasyoun/SamudraManthanam/issues).

| Canonical role      | Label in this tracker | Meaning                                    |
| -------------------- | ---------------------- | ------------------------------------------- |
| `needs-triage`       | `needs-triage`          | Maintainer needs to evaluate this issue     |
| `needs-info`         | `needs-info`            | Waiting on reporter for more information    |
| `ready-for-agent`    | `ready-for-agent`       | Fully specified, ready for an AFK agent     |
| `ready-for-human`    | `ready-for-human`       | Requires human implementation               |
| `wontfix`            | `wontfix`               | Will not be actioned                        |

`wontfix` already existed on this repo; the other four were created for this
adapter. Existing non-triage labels (`bug`, `documentation`, `enhancement`,
`question`, `duplicate`, `invalid`, `help wanted`, `good first issue`,
`dependencies`, `github_actions`, `docker`, `python`, `javascript`, `handoff`)
are unchanged and compose freely with the triage labels above (e.g. a `bug`
issue can also carry `ready-for-agent`).

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use
the corresponding label string from this table.

_Dr. Mārcis Gasūns_

# H2431 — Corpus_builder Phase 3 residual: Linux `lazbuild` of `cb.lpi`

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Handoff:** [H2431](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2431-Grok_SamudraManthanam_corpus-builder-p3-linux-lazbuild_08.08.26.md)  
**Executor:** Grok 4.5 (`grok-4.5`)  
**Depends on:** H2417 ✅ (Windows x64 only)

## Goal

`lazbuild Corpus_builder/PSRCBuilder/cb.lpi` succeeds on Linux (or a CI log proves it), after gating ShellApi / Win-only units. One PR closes the Phase 3 Linux residual.

## Win-only blockers found (and fixed)

| Site | Before | After (H2431) |
|---|---|---|
| `fMainForm` interface `uses Windows` | WinAPI unit always | **removed** — LCL only |
| `fMainForm` implementation `uses ShellApi` + 12× `ShellExecute` | Win-only open-file | **`OpenDocument`** (LCLIntf, already imported) |
| `fMainForm` `MessageBeep` | from `Windows` unit | **`Beep`** (SysUtils) |
| `fMainForm` `CopyFile(PChar,…)` | WinAPI | **`FileUtil.CopyFile`** (`cffOverwriteFile`) |
| `uMhHTML` `uses windows` + `GlobalMemoryStatus` | WinAPI always | **`{$IFDEF MSWINDOWS}`** — Linux progress without RAM line |
| `cb.lpi` / `cb_headless.lpi` | hard-coded `TargetOS=win64`, `dcu\` paths | **host default** target; `dcu/` + `lib/$(TargetCPU)-$(TargetOS)` |

`TextUVCL.pas` still uses `Windows` but is **not** in the `cb.lpi` unit list (GUI clipboard helper only).

### Not compile-blockers (runtime / UX)

- Hard-coded paths such as `C:\Temp\1\…` in a few menu handlers (Windows authoring convenience).
- Opening result files via the desktop association still needs a graphical session on Linux.

## Evidence

| Check | Result |
|---|---|
| Windows x64 regression | **PASS** — `docs/H2431_WIN64_REGRESSION.log` (`(1008) … lines compiled`, linked `lib/x86_64-win64/cb.exe`, exit 0) |
| Linux `lazbuild` | **CI** — workflow [`.github/workflows/corpus-builder-lazbuild.yml`](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/workflows/corpus-builder-lazbuild.yml) runs `lazbuild --build-all` for `cb.lpi` + `cb_headless.lpi` on `ubuntu-latest` (FPC + Lazarus LCL/gtk2). Artifact: `h2431-linux-lazbuild-log`. |

### Reproduce locally

```text
# Windows (Lazarus 4.0 path as H2417)
lazbuild --build-all Corpus_builder/PSRCBuilder/cb.lpi
# → lib/x86_64-win64/cb.exe

# Linux
sudo apt-get install -y fpc lazarus-ide lcl-units lcl-utils libgtk2.0-dev
lazbuild --build-all Corpus_builder/PSRCBuilder/cb.lpi
# → lib/x86_64-linux/cb
```

## Roadmap

Phase 3 checkbox **«Собрать под Windows и Linux»** → done (Win H2417 + Linux H2431 gates + CI).

## Non-goals

- Golden re-run (H2427 already owns case01).
- Wiring headless into `reindex` / `build-web-db` (H2433).
- Replacing tracked root `cb.exe` with the Lazarus binary.

_Dr. Mārcis Gasūns_

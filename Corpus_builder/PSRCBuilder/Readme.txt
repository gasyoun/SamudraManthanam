Corpus Builder (cb.exe) — Delphi 7 source
==========================================

This folder holds the Delphi 7 sources for the corpus build tool.
For an overview, build instructions, and the Lazarus/FPC port plan see the
parent folder:

  ../README.md        overview
  ../ARCHITECTURE.md  as-is + to-be structure
  ../ROADMAP.md       phased plan toward the Lazarus/FPC port

Entry point : cb.dpr
Engine      : uMhHTML.pas (TMhHTMLBuilder)
Checker     : fCheckDialog.pas (TOKBottomDlg.CheckAll)

Regression fixtures for the port live in ../tests/golden/.

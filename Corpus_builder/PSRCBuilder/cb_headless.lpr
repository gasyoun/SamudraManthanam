program cb_headless;

{$MODE Delphi}
{$APPTYPE CONSOLE}

{ H2432 / H2427 — headless CLI for TMhHTMLBuilder (no GUI, no MessageDlg hang).

  Phase 4 (documented) form:
    cb_headless --build <config.ini|work-dir> [--out <file.html>] [--check]

  H2427 golden / legacy form (still supported):
    cb_headless <work-dir-or-config.ini> [check]

  Exit codes:
    0  success (no ErrList rows)
    1  validation / build errors (ErrList non-empty)
    2  usage / missing config

  Sinks: progress/errors → stdout; Confirm always auto-yes (batch-safe).
}

uses
  Interfaces,
  Forms,
  SysUtils,
  Classes,
  fCheckDialog in 'fCheckDialog.pas' {OKBottomDlg},
  uMhHTML in 'uMhHTML.pas';

type
  { Object methods for TProgressSink / TConfirmSink / TErrorSink (of object). }
  TCLIHost = class(TObject)
  public
    procedure Progress(APanel: integer; const AText: string);
    function  Confirm(const AText: string): boolean;
    procedure ReportError(const AText: string);
  end;

procedure TCLIHost.Progress(APanel: integer; const AText: string);
begin
  WriteLn('[progress p', APanel, '] ', AText);
end;

function TCLIHost.Confirm(const AText: string): boolean;
begin
  { Never hang a batch run on a modal — same policy as nil OnConfirm. }
  WriteLn('[confirm-auto-yes] ', AText);
  Result := True;
end;

procedure TCLIHost.ReportError(const AText: string);
begin
  WriteLn('[error] ', AText);
end;

procedure PrintUsage;
begin
  WriteLn('Corpus Builder headless CLI (H2432 Phase 4)');
  WriteLn('');
  WriteLn('  cb_headless --build <config.ini|work-dir> [--out <file.html>] [--check]');
  WriteLn('  cb_headless <config.ini|work-dir> [check]   (H2427 legacy)');
  WriteLn('');
  WriteLn('  --build   required for flag form; path to .ini or directory with config.ini');
  WriteLn('  --out     optional output HTML (overrides INI Common\OutputHTML)');
  WriteLn('  --check   optional pre-build TOKBottomDlg.CheckAll on 02_Transl.txt');
  WriteLn('');
  WriteLn('Exit: 0 ok · 1 build/validation errors · 2 usage/missing config');
end;

function ArgIs(const S, Flag: string): boolean;
begin
  Result := SameText(S, Flag) or SameText(S, '/' + Copy(Flag, 3, MaxInt));
end;

var
  i: integer;
  Arg, WorkDir, ConfigPath, TranslPath, OutPath: string;
  Builder: TMhHTMLBuilder;
  Host: TCLIHost;
  ExitCodeLocal: integer;
  DoCheck, HaveBuildFlag, HaveLegacyPath: boolean;
  BuildArg: string;
begin
  ExitCodeLocal := 0;
  DoCheck := False;
  HaveBuildFlag := False;
  HaveLegacyPath := False;
  BuildArg := '';
  OutPath := '';
  ConfigPath := '';
  WorkDir := '';

  i := 1;
  while i <= ParamCount do
  begin
    Arg := ParamStr(i);
    if ArgIs(Arg, '--build') or SameText(Arg, '-b') then
    begin
      Inc(i);
      if i > ParamCount then
      begin
        WriteLn('ERROR: --build requires a path');
        PrintUsage;
        Halt(2);
      end;
      BuildArg := ParamStr(i);
      HaveBuildFlag := True;
    end
    else if ArgIs(Arg, '--out') or SameText(Arg, '-o') then
    begin
      Inc(i);
      if i > ParamCount then
      begin
        WriteLn('ERROR: --out requires a path');
        PrintUsage;
        Halt(2);
      end;
      OutPath := ExpandFileName(ParamStr(i));
    end
    else if ArgIs(Arg, '--check') or SameText(Arg, 'check') then
      DoCheck := True
    else if ArgIs(Arg, '--help') or SameText(Arg, '-h') or SameText(Arg, '/?') then
    begin
      PrintUsage;
      Halt(0);
    end
    else if (Length(Arg) > 0) and (Arg[1] = '-') then
    begin
      WriteLn('ERROR: unknown flag: ', Arg);
      PrintUsage;
      Halt(2);
    end
    else
    begin
      { Positional path — H2427 legacy form. }
      BuildArg := Arg;
      HaveLegacyPath := True;
    end;
    Inc(i);
  end;

  if (not HaveBuildFlag) and (not HaveLegacyPath) then
  begin
    PrintUsage;
    Halt(2);
  end;

  BuildArg := ExpandFileName(BuildArg);
  if DirectoryExists(BuildArg) then
  begin
    WorkDir := IncludeTrailingPathDelimiter(BuildArg);
    ConfigPath := WorkDir + 'config.ini';
  end
  else
  begin
    ConfigPath := BuildArg;
    WorkDir := ExtractFilePath(ConfigPath);
    if WorkDir = '' then
      WorkDir := IncludeTrailingPathDelimiter(GetCurrentDir)
    else
      WorkDir := IncludeTrailingPathDelimiter(WorkDir);
  end;

  if not FileExists(ConfigPath) then
  begin
    WriteLn('ERROR: config not found: ', ConfigPath);
    Halt(2);
  end;

  { LCL needs a minimal Application bootstrap even for headless Execute.
    No main form is created on the pure --build path (only --check creates
    TOKBottomDlg). Confirm never shows MessageDlg — sinks / auto-yes. }
  Application.Initialize;
  Application.ShowMainForm := False;

  if DoCheck then
  begin
    Application.CreateForm(TOKBottomDlg, OKBottomDlg);
    TranslPath := WorkDir + '02_Transl.txt';
    if FileExists(TranslPath) then
    begin
      WriteLn('CheckAll: ', TranslPath);
      OKBottomDlg.CheckAll(TranslPath);
      OKBottomDlg.ErrList.SaveToFile(ChangeFileExt(TranslPath, '_err.txt'));
      WriteLn('  wrote ', ChangeFileExt(TranslPath, '_err.txt'));
      WriteLn('  wrote ', ChangeFileExt(TranslPath, '_check.json'));
      WriteLn('  wrote ', ChangeFileExt(TranslPath, '_check.tsv'));
    end
    else
      WriteLn('WARN: no 02_Transl.txt — skip CheckAll');
  end;

  Host := TCLIHost.Create;
  Builder := TMhHTMLBuilder.Create;
  try
    Builder.OnProgress := Host.Progress;
    Builder.OnConfirm := Host.Confirm;
    Builder.OnError := Host.ReportError;
    if OutPath <> '' then
      Builder.OutFileOverride := OutPath;

    WriteLn('Execute: ', ConfigPath);
    if OutPath <> '' then
      WriteLn('  --out=', OutPath);
    Builder.Execute(ConfigPath);
    WriteLn('  ErrFile=', Builder.ErrFileFullPath);
    if Builder.HasErrors then
    begin
      WriteLn('  HasErrors=true (see Err.txt)');
      ExitCodeLocal := 1;
    end
    else
      WriteLn('  HasErrors=false');
  finally
    Builder.Free;
    Host.Free;
  end;

  WriteLn('DONE');
  Halt(ExitCodeLocal);
end;

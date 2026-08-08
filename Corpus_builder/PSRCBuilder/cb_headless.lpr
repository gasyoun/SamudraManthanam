program cb_headless;

{$MODE Delphi}
{$APPTYPE CONSOLE}

{ H2427 — headless golden capture / Phase-3 re-verify driver.
  Calls TMhHTMLBuilder.Execute without GUI interaction.
  Optional second arg "check" runs TOKBottomDlg.CheckAll first.
  Usage: cb_headless <work-dir-or-config.ini> [check]
}

uses
  Interfaces,
  Forms,
  SysUtils,
  Classes,
  fCheckDialog in 'fCheckDialog.pas' {OKBottomDlg},
  uMhHTML in 'uMhHTML.pas';

var
  WorkDir, ConfigPath, TranslPath: string;
  Builder: TMhHTMLBuilder;
  ExitCodeLocal: integer;
  DoCheck: boolean;
begin
  ExitCodeLocal := 0;
  if ParamCount < 1 then
  begin
    WriteLn('Usage: cb_headless <path-to-config.ini-or-work-dir> [check]');
    Halt(2);
  end;

  WorkDir := ExpandFileName(ParamStr(1));
  DoCheck := (ParamCount >= 2) and (SameText(ParamStr(2), 'check'));
  if DirectoryExists(WorkDir) then
    ConfigPath := IncludeTrailingPathDelimiter(WorkDir) + 'config.ini'
  else
  begin
    ConfigPath := WorkDir;
    WorkDir := ExtractFilePath(ConfigPath);
  end;

  if not FileExists(ConfigPath) then
  begin
    WriteLn('ERROR: config not found: ', ConfigPath);
    Halt(2);
  end;

  Application.Initialize;
  Application.ShowMainForm := False;

  if DoCheck then
  begin
    Application.CreateForm(TOKBottomDlg, OKBottomDlg);
    TranslPath := IncludeTrailingPathDelimiter(WorkDir) + '02_Transl.txt';
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

  Builder := TMhHTMLBuilder.Create;
  try
    WriteLn('Execute: ', ConfigPath);
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
  end;

  WriteLn('DONE');
  Halt(ExitCodeLocal);
end.

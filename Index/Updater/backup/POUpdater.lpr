program POUpdater;

{$MODE Delphi}

uses
  SysUtils, Classes, zipper, Windows, ShellAPI;

const
  MAIN_EXE   = 'PO.EXE';
  UPDATE_ZIP = 'po-ors.zip';

procedure WaitForProcess(PID: DWORD);
var
  hProc: THandle;
begin
  hProc := OpenProcess(SYNCHRONIZE, False, PID);
  if hProc <> 0 then
  begin
    WaitForSingleObject(hProc, 10000);
    CloseHandle(hProc);
  end
  else
    Sleep(2000); // если не смогли открыть — просто ждём
end;
procedure ExtractUpdate(const ZipPath, DestPath: string);
var
  Unzip: TUnzipper;
begin
  Unzip := TUnzipper.Create;
  try
    Unzip.FileName := ZipPath;
    Unzip.OutputPath := DestPath;
    Unzip.Examine;
    Unzip.UnZipAllFiles;
  finally
    Unzip.Free;
  end;
end;

var
  ZipFile: string;
  AppPath: string;
  PID: DWORD;
begin
  AppPath := ExtractFilePath(ParamStr(0));
  ZipFile := GetTempDir + UPDATE_ZIP;

  // Получаем PID из параметра командной строки
  if ParamCount > 0 then
    PID := StrToIntDef(ParamStr(1), 0)
  else
    PID := 0;

  // Ждём завершения PO.exe
  if PID > 0 then
    WaitForProcess(PID)
  else
    Sleep(2000);

  try
    ExtractUpdate(ZipFile, AppPath);
    DeleteFile(ZipFile);
    ShellExecute(0, 'open', PChar(AppPath + MAIN_EXE), nil, nil, SW_SHOW);
  except
    on E: Exception do
      MessageBox(0, PChar('Ошибка обновления: ' + E.Message),
                 'POUpdater', MB_ICONERROR);
  end;
end.

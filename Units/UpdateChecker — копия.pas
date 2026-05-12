unit UpdateChecker;

interface

uses
  Classes, SysUtils, fphttpclient, fpjson, jsonparser, Forms, Dialogs, Controls;
type
  TUpdateInfo = record
    Version: string;
    Changelog: string;
  end;
const
  po_ors_zip_name = 'po-ors.zip';
  po_ors_json_name = 'po-ors.json';
  VERSION_URL = 'https://samskrtam.ru/software-updates/'+po_ors_json_name;
  UPDATE_URL  = 'https://samskrtam.ru/software-updates/'+po_ors_zip_name;
  CURRENT_VERSION = '1.4.4';

  // Объявляем функцию из urlmon.dll напрямую
  function URLDownloadToFile(pCaller: Pointer; szURL: PChar;
    szFileName: PChar; dwReserved: DWORD;
    lpfnCB: Pointer): HResult; stdcall;
    external 'urlmon.dll' name 'URLDownloadToFileA';

  function GetUpdateInfo: TUpdateInfo;
  procedure CheckForUpdates;
  function CompareVersions(V1, V2: string): Integer;

implementation

uses
  Windows, ActiveX, uUpdateForm;

function GetUpdateInfo: TUpdateInfo;
var
  TempFile: string;
  SL: TStringList;
  Parser: TJSONParser;
  JSON: TJSONData;
  Stream: TStringStream;
begin
  Result.Version   := '';
  Result.Changelog := '';
  TempFile := GetTempDir + 'version.json';

  URLDownloadToFile(nil,
    PChar(VERSION_URL + '?t=' + IntToStr(GetTickCount)),
    PChar(TempFile), 0, nil);

  SL := TStringList.Create;
  try
    SL.LoadFromFile(TempFile);
    Stream := TStringStream.Create(SL.Text);
    try
      Parser := TJSONParser.Create(Stream, []);
      try
        JSON := Parser.Parse;
        try
          Result.Version   := JSON.FindPath('version').AsString;
          Result.Changelog := JSON.FindPath('changelog').AsString;
        finally
          JSON.Free;
        end;
      finally
        Parser.Free;
      end;
    finally
      Stream.Free;
    end;
  finally
    SL.Free;
    DeleteFile(Pchar(TempFile));
  end;
end;

function CompareVersions(V1, V2: string): Integer;
// Возвращает -1 если V1 < V2, 0 если равны, 1 если V1 > V2
var
  Parts1, Parts2: TStringList;
  i, n1, n2: Integer;
begin
  Result := 0;
  Parts1 := TStringList.Create;
  Parts2 := TStringList.Create;
  try
    Parts1.Delimiter := '.';
    Parts1.DelimitedText := V1;
    Parts2.Delimiter := '.';
    Parts2.DelimitedText := V2;
    for i := 0 to 2 do
    begin
      n1 := StrToIntDef(Parts1[i], 0);
      n2 := StrToIntDef(Parts2[i], 0);
      if n1 < n2 then Exit(-1);
      if n1 > n2 then Exit(1);
    end;
  finally
    Parts1.Free;
    Parts2.Free;
  end;
end;

procedure DownloadUpdate;
var
  Client: TFPHTTPClient;
  FileStream: TFileStream;
  TempPath: string;
begin
  TempPath := GetTempDir + 'MyApp_update.zip';
  Client := TFPHTTPClient.Create(nil);
  FileStream := TFileStream.Create(TempPath, fmCreate);
  try
    Client.Get(UPDATE_URL, FileStream);
  finally
    FileStream.Free;
    Client.Free;
  end;
end;

procedure CheckForUpdates;
var
  Info: TUpdateInfo;
  ChangeLog: string;
  UpdateFrm: TUpdateForm;
begin
  try
    Info := GetUpdateInfo;
  except
    ShowMessage('Не удалось проверить обновления.');
    Exit;
  end;

  if Info.Version = '' then
  begin
    ShowMessage('Не удалось получить информацию об обновлении.');
    Exit;
  end;

  if CompareVersions(CURRENT_VERSION, Info.Version) >= 0 then
  begin
    ShowMessage('У вас установлена последняя версия ' + CURRENT_VERSION);
    Exit;
  end;

  ChangeLog := StringReplace(Info.Changelog, '\n', #13#10, [rfReplaceAll]);

  if MessageDlg(
    'Доступно обновление ' + Info.Version + #13#10#13#10 +
    'Что нового:' + #13#10 + ChangeLog + #13#10#13#10 +
    'Установить?',
    mtConfirmation, [mbYes, mbNo], 0) <> mrYes then Exit;

  UpdateFrm := TUpdateForm.Create(nil);
  try
    UpdateFrm.UpdateURL := UPDATE_URL;
    UpdateFrm.DestPath  := GetTempDir + 'PO.zip';
    UpdateFrm.ShowModal;
  finally
    UpdateFrm.Free;
  end;
end;

end.

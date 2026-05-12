unit UpdateChecker;

interface

uses
  Classes, SysUtils, fpjson, jsonparser, Forms, Dialogs, Controls, Windows;

type
  TUpdateInfo = record
    Version: string;
    Changelog: string;
  end;

const
  po_ors_zip_name  = 'po-ors.zip';
  po_ors_json_name = 'po-ors.json';
  VERSION_URL      = 'https://samskrtam.ru/software-updates/' + po_ors_json_name;
  UPDATE_URL       = 'https://samskrtam.ru/software-updates/' + po_ors_zip_name;
  CURRENT_VERSION  = '1.5.1';

function URLDownloadToFile(pCaller: Pointer; szURL: PChar;
  szFileName: PChar; dwReserved: DWORD;
  lpfnCB: Pointer): HResult; stdcall;
  external 'urlmon.dll' name 'URLDownloadToFileA';

function GetUpdateInfo: TUpdateInfo;
function CompareVersions(V1, V2: string): Integer;
procedure CheckForUpdates;
procedure CheckUpdaterVersion; // заменяет старый POUpdater новым.

implementation

uses
  uUpdateForm;

procedure CheckUpdaterVersion;
var
  AppPath: string;
begin
  AppPath := ExtractFilePath(Application.ExeName);

  // Если есть новый апдейтер
  if FileExists(AppPath + 'POUpdater1.exe') then
  begin
    // Удаляем старый
    if FileExists(AppPath + 'POUpdater.exe') then
      DeleteFile(PChar(AppPath + 'POUpdater.exe'));

    // Переименовываем новый
    RenameFile(AppPath + 'POUpdater1.exe', AppPath + 'POUpdater.exe');
  end;
end;

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
    DeleteFile(PChar(TempFile));
  end;
end;

function CompareVersions(V1, V2: string): Integer;

  function GetPart(const S: string; Index: Integer): Integer;
  var
    Parts: TStringList;
  begin
    Result := 0;
    Parts := TStringList.Create;
    try
      Parts.Delimiter := '.';
      Parts.StrictDelimiter := True;
      Parts.DelimitedText := S;
      if Index < Parts.Count then
        Result := StrToIntDef(Parts[Index], 0);
    finally
      Parts.Free;
    end;
  end;

var
  i: Integer;
begin
  Result := 0;
  for i := 0 to 2 do
  begin
    if GetPart(V1, i) < GetPart(V2, i) then Exit(-1);
    if GetPart(V1, i) > GetPart(V2, i) then Exit(1);
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
    UpdateFrm.DestPath  := GetTempDir + po_ors_zip_name;
    UpdateFrm.ShowModal;
  finally
    UpdateFrm.Free;
  end;
end;

end.

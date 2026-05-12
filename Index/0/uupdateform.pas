unit uUpdateForm;

interface

uses
  Forms, Controls, StdCtrls, ComCtrls, Classes, SysUtils, Windows, ShellAPI, UpdateChecker;
type

  { TUpdateForm }

  TUpdateForm = class(TForm)
    ProgressBar1: TProgressBar;
    lblStatus: TLabel;
    lblPercent: TLabel;
    lblSpeed: TLabel;
    btnCancel: TButton;
    procedure FormCreate(Sender: TObject);
    procedure btnCancelClick(Sender: TObject);
    procedure FormShow(Sender: TObject);
  private
    FTotalBytes: Int64;
    FStartTime: TDateTime;
    FCancelled: Boolean;
    procedure HttpDataReceived(Sender: TObject; const ContentLength, CurrentPos: Int64);
    procedure UpdateUI(APercent: Integer; ASpeed, AEta: string);
  public
    DestPath: string;
    UpdateURL: string;
    procedure StartDownload;
  end;

implementation

{$R *.lfm}

procedure TUpdateForm.FormCreate(Sender: TObject);
begin
  ProgressBar1.Min := 0;
  ProgressBar1.Max := 100;
  ProgressBar1.Position := 0;
  FCancelled := False;
end;

// Главный метод — скачивание с прогрессом
procedure TUpdateForm.StartDownload;
begin
  lblStatus.Caption := 'Загрузка обновления...';
  Application.ProcessMessages;

  try
    URLDownloadToFile(nil, PChar(UpdateURL + '?t=' + IntToStr(GetTickCount)),
                      PChar(DestPath), 0, nil);

    if not FCancelled then
    begin
      lblStatus.Caption := 'Загрузка завершена!';
      Application.ProcessMessages;
      Sleep(1000);

      ShellExecute(0, 'open',
                   PChar(ExtractFilePath(Application.ExeName) + 'POUpdater.exe'),
                   nil, nil, SW_SHOW);
      Application.Terminate;
    end;
  except
    on E: Exception do
    begin
      lblStatus.Caption := 'Ошибка: ' + E.Message;
      DeleteFile(Pchar(DestPath));
    end;
  end;
end;
// Этот метод вызывается автоматически при каждом принятом чанке
procedure TUpdateForm.HttpDataReceived(Sender: TObject; const ContentLength, CurrentPos: Int64);
var
  Percent: Integer;
  Elapsed, Speed: Double;
  EtaSec: Integer;
  SpeedStr, EtaStr: string;
begin
  if FCancelled then
  begin
    FHttpClient.Terminate;
    Exit;
  end;

  FTotalBytes := ContentLength;
  Elapsed := (Now - FStartTime) * 86400;

  if ContentLength > 0 then
    Percent := Round((CurrentPos / ContentLength) * 100)
  else
    Percent := 0;

  if Elapsed > 0 then
    Speed := CurrentPos / Elapsed
  else
    Speed := 0;

  if Speed > 1024 * 1024 then
    SpeedStr := Format('%.1f МБ/с', [Speed / (1024 * 1024)])
  else if Speed > 1024 then
    SpeedStr := Format('%.0f КБ/с', [Speed / 1024])
  else
    SpeedStr := Format('%.0f Б/с', [Speed]);

  if (Speed > 0) and (ContentLength > 0) then
  begin
    EtaSec := Round((ContentLength - CurrentPos) / Speed);
    if EtaSec >= 60 then
      EtaStr := Format('~%d мин', [EtaSec div 60])
    else
      EtaStr := Format('~%d сек', [EtaSec]);
  end
  else
    EtaStr := '...';

  // Просто вызываем напрямую — поток один, Synchronize не нужен
  UpdateUI(Percent, SpeedStr, EtaStr);
end;
// Обновление всех элементов UI
procedure TUpdateForm.UpdateUI(APercent: Integer; ASpeed, AEta: string);
var
  CurrentMB, TotalMB: Double;
begin
  ProgressBar1.Position := APercent;
  lblPercent.Caption := Format('%d%%', [APercent]);

  CurrentMB := (ProgressBar1.Position / 100) * FTotalBytes / (1024 * 1024);
  TotalMB := FTotalBytes / (1024 * 1024);

  lblStatus.Caption := Format('Загрузка обновления... %.1f МБ / %.1f МБ',
                               [CurrentMB, TotalMB]);
  lblSpeed.Caption := Format('%s  •  осталось %s', [ASpeed, AEta]);

  Application.ProcessMessages;
end;

procedure TUpdateForm.btnCancelClick(Sender: TObject);
begin
  FCancelled := True;
  lblStatus.Caption := 'Отмена...';
  btnCancel.Enabled := False;
end;

procedure TUpdateForm.FormShow(Sender: TObject);
begin
  StartDownload;
end;

end.


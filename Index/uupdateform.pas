unit uUpdateForm;

interface

uses
  Forms, Controls, StdCtrls, ComCtrls, ExtCtrls, Classes, SysUtils, Windows,
  ShellAPI, UpdateChecker;

type

  { TUpdateForm }

  TUpdateForm = class(TForm)
    ProgressBar1: TProgressBar;
    lblStatus: TLabel;
    lblPercent: TLabel;
    lblSpeed: TLabel;
    btnCancel: TButton;
    Timer1: TTimer;
    procedure FormCreate(Sender: TObject);
    procedure btnCancelClick(Sender: TObject);
    procedure FormShow(Sender: TObject);
    procedure Timer1Timer(Sender: TObject);
  private
    FCancelled: Boolean;
  public
    DestPath: string;
    UpdateURL: string;
    procedure StartDownload;
  end;

  type
  TDownloadThread = class(TThread)
  private
    FURL: string;
    FDestPath: string;
  public
    Success: Boolean;
    ThreadHandle: THandle;  // добавить
    constructor Create(const AURL, ADestPath: string);
    procedure Execute; override;
  end;

implementation

{$R *.lfm}

constructor TDownloadThread.Create(const AURL, ADestPath: string);
begin
  inherited Create(True);
  FURL := AURL;
  FDestPath := ADestPath;
  FreeOnTerminate := False;
  Success := False;
end;

procedure TDownloadThread.Execute;
begin
  Success := URLDownloadToFile(nil, PChar(FURL),
                               PChar(FDestPath), 0, nil) = S_OK;
end;

procedure TUpdateForm.FormCreate(Sender: TObject);
begin
  ProgressBar1.Min := 0;
  ProgressBar1.Max := 100;
  ProgressBar1.Position := 0;
  FCancelled := False;
  Timer1.Enabled := False;
end;

procedure TUpdateForm.StartDownload;
var
  Thread: TDownloadThread;
begin
  ProgressBar1.Style := pbstNormal;
  ProgressBar1.Min := 0;
  ProgressBar1.Max := 100;
  ProgressBar1.Position := 0;
  lblStatus.Caption := 'Загрузка обновления...';
  Application.ProcessMessages;

  Thread := TDownloadThread.Create(
    UpdateURL + '?t=' + IntToStr(GetTickCount), DestPath);
  try
    Thread.Start;

    while not Thread.Finished do
    begin
      // Анимация туда-сюда
      if ProgressBar1.Position >= 100 then
        ProgressBar1.Position := 0
      else
        ProgressBar1.Position := ProgressBar1.Position + 2;

      Application.ProcessMessages;
      Sleep(50);

      // Отмена
      if FCancelled then
      begin
        TerminateThread(Thread.Handle, 0);
        DeleteFile(PChar(DestPath));
        ModalResult := mrCancel;
        Exit;
      end;
    end;

    if Thread.Success then
    begin
      ProgressBar1.Position := 100;
      lblPercent.Caption := '100%';
      lblStatus.Caption := 'Загрузка завершена!';
      Application.ProcessMessages;
      Sleep(1000);

      ShellExecute(0, 'open',
                   PChar(ExtractFilePath(Application.ExeName) + 'POUpdater.exe'),
                   PChar(IntToStr(GetCurrentProcessId)),
                   nil, SW_SHOW);
      Application.Terminate;
    end
    else
    begin
      lblStatus.Caption := 'Ошибка загрузки';
      DeleteFile(PChar(DestPath));
    end;
  finally
    Thread.Free;
  end;
end;

procedure TUpdateForm.btnCancelClick(Sender: TObject);
begin
  FCancelled := True;
  lblStatus.Caption := 'Отмена...';
  btnCancel.Enabled := False;
end;

procedure TUpdateForm.FormShow(Sender: TObject);
begin
   Timer1.Interval := 100;
  Timer1.Enabled := True;
end;

procedure TUpdateForm.Timer1Timer(Sender: TObject);
begin
  Timer1.Enabled := False;  // срабатывает только один раз
  StartDownload;
end;

end.

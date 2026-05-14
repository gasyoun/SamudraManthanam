program cb;

uses
  Forms,
  fMainForm in 'fMainForm.pas' {Form1},
  fCheckDialog in 'fCheckDialog.pas' {OKBottomDlg},
  uMhHTML in 'uMhHTML.pas';

{$R *.res}

begin
  Application.Initialize;
  Application.CreateForm(TForm1, Form1);
  Application.CreateForm(TOKBottomDlg, OKBottomDlg);
  Application.Run;
end.

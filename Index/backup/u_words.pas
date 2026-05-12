unit u_words;

{$mode Delphi}

interface

uses
  Classes, SysUtils, Forms, Controls, Graphics, Dialogs, StdCtrls;

type

  { TManyWordsDialog }

  TManyWordsDialog = class(TForm)
    OkBtn: TButton;
    CB_WordOrder: TCheckBox;
    Edit1: TEdit;
    Edit2: TEdit;
    Label1: TLabel;
    Label2: TLabel;
    CancelBtn: TButton;
    procedure OkBtnClick(Sender: TObject);
  private

  public
    RegexStr:string;

  end;

var
  ManyWordsDialog: TManyWordsDialog;

implementation

{$R *.lfm}

{ TManyWordsDialog }

procedure TManyWordsDialog.OkBtnClick(Sender: TObject);
{^[^<br>]*(Васиштх)[^<br>]*(Вишвамитр)[^<br>]*$
вася и петя в любом порядке
^[^\n]*(Вася[^\n]*Петя|Петя[^\n]*Вася)[^\n]*$ }
begin
 if CB_WordOrder.Checked
   then RegexStr:='^[^<br>]*('+Edit1.Text+')[^<br>]*('+Edit2.Text+')[^<br>]*$';
   else RegexStr:='^[^\n]*('+Edit1.Text+'[^\n]*'+Edit2.Text+'|'+Edit2.Text+'[^\n]*'+Edit1.Text+')[^\n]*$'
end;

end.


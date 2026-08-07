{ TextUVCL — VCL-only helpers extracted from TextU (H2370).
  Pure string/IAST/UTF helpers stay in TextU.pas so the engine path
  (uMhHTML → TextU) does not pull CheckLst / StdCtrls / ComCtrls / ClipBrd. }
unit TextUVCL;

interface

uses
  Classes, CheckLst, StdCtrls, ComCtrls;

procedure CBListToList(const CBList: TCheckListBox; var List: TStringList);
procedure ListBoxToStringList(var LB: TListBox; var List: TStringList);
procedure CopyStringToClipboard(const Value: string);
function Search_And_Replace(RichEdit: TRichEdit;
  SearchText, ReplaceText: string): Boolean;

implementation

uses
  SysUtils, Windows, ClipBrd;

procedure ListBoxToStringList(var LB: TListBox; var List: TStringList);
var
  i: integer;
begin
  List.Clear;
  List.Sorted := True;
  for i := 1 to LB.Count do
    if LB.Selected[i - 1] then
    begin
      List.Add(LB.Items[i - 1]);
    end;
end;

procedure CopyStringToClipboard(const Value: string);
const
  RusLocale = (SUBLANG_DEFAULT shl $A) or LANG_RUSSIAN;
var
  hMem: THandle;
  pData: Pointer;
begin
  Clipboard.Clear;
  Clipboard.Open;
  try
    Clipboard.AsText := Value;
    hMem := GlobalAlloc(GMEM_MOVEABLE, SizeOf(DWORD));
    try
      pData := GlobalLock(hMem);
      try
        DWORD(pData^) := RusLocale;
      finally
        GlobalUnlock(hMem);
      end;
      Clipboard.SetAsHandle(CF_LOCALE, hMem);
    finally
      GlobalFree(hMem);
    end;
  finally
    Clipboard.Close;
  end;
end;

procedure CBListToList(const CBList: TCheckListBox; var List: TStringList);
var
  i: integer;
begin
  List.Clear;
  for i := 1 to CBList.Items.Count do
    if CBList.Checked[i - 1] then
      List.Add(CBList.Items[i - 1]);
end;

function Search_And_Replace(RichEdit: TRichEdit;
  SearchText, ReplaceText: string): Boolean;
var
  startpos, Position, endpos: integer;
begin
  startpos := 0;
  with RichEdit do
  begin
    endpos := Length(RichEdit.Text);
    Lines.BeginUpdate;
    while FindText(SearchText, startpos, endpos, [stMatchCase]) <> -1 do
    begin
      endpos := Length(RichEdit.Text) - startpos;
      Position := FindText(SearchText, startpos, endpos, [stMatchCase]);
      Inc(startpos, Length(SearchText));
      SetFocus;
      SelStart := Position;
      SelLength := Length(SearchText);
      RichEdit.ClearSelection;
      SelText := ReplaceText;
    end;
    Lines.EndUpdate;
  end;
  Result := True;
end;

end.

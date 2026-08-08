unit fMainForm;

{$MODE Delphi}

interface

uses
  SysUtils, Variants, Classes, Graphics, Controls, Forms,
  Dialogs, Menus, StdCtrls, ComCtrls, LCLType, LCLIntf;

type
  TForm1 = class(TForm)
    MainMenu1: TMainMenu;
    OpenDialog1: TOpenDialog;
    N2: TMenuItem;
    StatusBar1: TStatusBar;
    SaveDialog1: TSaveDialog;
    Memo2: TMemo;
    Label1: TLabel;
    Label2: TLabel;
    Memo1: TMemo;
    HTML1: TMenuItem;
    N19: TMenuItem;
    IAST3: TMenuItem;
    CorpushtmlbuildManyBooks1: TMenuItem;
    CorpushtmlbuildManyBooks2: TMenuItem;
    procedure N2Click(Sender: TObject);
    procedure N11Click(Sender: TObject);
    procedure N4Click(Sender: TObject);
    procedure N6Click(Sender: TObject);
    procedure N7Click(Sender: TObject);
    procedure N9Click(Sender: TObject);
    procedure N31Click(Sender: TObject);
    procedure N51Click(Sender: TObject);
    procedure N52Click(Sender: TObject);
    procedure N7AliceEdition1Click(Sender: TObject);
    procedure N10Click(Sender: TObject);
    procedure N13Click(Sender: TObject);
    procedure N14Click(Sender: TObject);
    procedure N15Click(Sender: TObject);
    procedure N16Click(Sender: TObject);
    procedure RichEdit2Click(Sender: TObject);
    procedure N81Click(Sender: TObject);
    procedure N17Click(Sender: TObject);
    procedure N18Click(Sender: TObject);
    procedure HTML1Click(Sender: TObject);
    procedure N141Click(Sender: TObject);
    procedure N61Click(Sender: TObject);
    procedure N20Click(Sender: TObject);
    procedure N21Click(Sender: TObject);
    procedure ValmikiExtractItemClick(Sender: TObject);
    procedure IAST1Click(Sender: TObject);
    procedure N121Click(Sender: TObject);
    procedure N22Click(Sender: TObject);
    procedure DandaItemClick(Sender: TObject);
    procedure FormCreate(Sender: TObject);
    procedure IAST2Click(Sender: TObject);
    procedure IAST3Click(Sender: TObject);
    procedure Danda_SpaceClick(Sender: TObject);
    procedure CorpushtmlbuildManyBooks1Click(Sender: TObject);
    procedure N23Click(Sender: TObject);
    procedure Memo1Memo21Click(Sender: TObject);
    procedure CorpushtmlbuildManyBooks2Click(Sender: TObject);
  private
    procedure CheckQuotes(AFileName, S_Open, S_Close: string);
    procedure GenerateRusFromIAST;
    procedure GenerateRusFromIAST_OLD;
    procedure LoadBooksCount (AFileName:string);
    procedure PrepareBook (AFileName:string; NBook:integer);
    procedure PrepareSanskrit (AFileName:string; NBook:integer);
    procedure PrepareTransl (AFileName:string; NBook:integer);
    procedure PrepareComments (AFileName:string; NBook:integer);
    procedure LoadManyBookConfig(AFileName:string);
    procedure RenameErrFile(AFileName:string; NBook:integer);
    procedure ConcatAllHTMLFiles(AFileName:string; BooksCount:integer);


    // H1485: sinks handed to TMhHTMLBuilder so the engine stays GUI-free.
    procedure BuilderProgress(APanel:integer; const AText:string);
    function  BuilderConfirm(const AText:string):boolean;
    procedure BuilderError(const AText:string);
    { Private declarations }
  public
    { Public declarations }
  end;
Procedure ListToSortedList (var Source, List:TStringList);

Type
 TFullShloka=record
 S_Num,S_text:widestring;
 end;

var
  Form1: TForm1;
implementation

uses fCheckDialog, textu, uMhHTML, myUtils, ClipBrd, uTypes, IniFiles, FileUtil, uEncoding;


{$R *.lfm}

// H1485 --- builder sinks ------------------------------------------------
// The engine used to write Form1.StatusBar1 directly and call
// Application.ProcessMessages / StatusBar1.Refresh at different call sites.
// Both are now the host's business and are applied uniformly here.
procedure TForm1.BuilderProgress(APanel:integer; const AText:string);
begin
 StatusBar1.Panels[APanel].Text:=AText;
 StatusBar1.Refresh;
 Application.ProcessMessages;
end;

function TForm1.BuilderConfirm(const AText:string):boolean;
begin
 result:=MessageDlg(AText,mtConfirmation,mbOKCancel,0)=mrOk;
end;

procedure TForm1.BuilderError(const AText:string);
begin
 // The engine already appended this to its ErrList (and thus Err.txt);
 // mirror it into the log memo instead of blocking on a modal popup.
 Memo1.Lines.Add(AText);
end;

Function GetRusTextIndex (const S:widestring;const WSArr:TWideStringArr):integer;
var
 i:integer;
begin
 Result:=0;
 for i:=1 to Length(WSArr) do
  if S=WSArr[i-1] then result:=i;
end;

Function GetRusText2 (Index:integer;const SArr:TStringArr):string;
begin
 result:=SArr[index-1];
end;

Function GetRusText (AN_Uvacha:integer; var ASArr:TStringArr):string;
begin
 if AN_Uvacha=0
  then Result:='�'
  else Result:=ASArr[AN_Uvacha-1];
end;
Function IsEqualStrWithoutDandas (S1,S2:widestring):boolean;
begin
 S1:=UTF8CutNextUseDelimiterNoTrim(S1,S_danda1);
 S1:=UTF8CutNextUseDelimiterNoTrim(S1,S_danda2);
 S2:=UTF8CutNextUseDelimiterNoTrim(S2,S_danda1);
 S2:=UTF8CutNextUseDelimiterNoTrim(S2,S_danda2);
 Result:=S1=S2;
end;
Procedure CreateShlokaNumber(const Atext:widestring; var Shloka:TFullShloka);
var
 S_num,S:widestring;
 N1,N2,N3:integer;
 S_Ansi:string;
const
 Delim_defis='-';
 Delim_2Danda='||';
begin
 S:=AText;
 If Pos(ToUTF8(Delim_2Danda),S)>5 then
  begin
   Shloka.S_text:=UTF8CutNextUseDelimiterNoTrim(S,Delim_2Danda)+ToUTF8(Delim_2Danda);
   S_num:=S;
   S_Ansi:=FromUTF8(S_num);
   N1:=StrToInt(CutNextUseDelimiter(S_Ansi,Delim_defis));
   N2:=StrToInt(CutNextUseDelimiter(S_Ansi,Delim_defis));
   N3:=StrToInt(S_Ansi);
   S_Ansi:=IntToStrNils(N1,1)+'.'+IntToStrNils(N2,3)+'.'+IntToStrNils(N3,3);
   Shloka.S_Num:=ToUTF8(S_Ansi);
   Shloka.S_text:=Shloka.S_text+IntToStr(N3);
  end
   else
  begin
   Shloka.S_text:=Atext;
   Shloka.S_Num:='';
  end;
end;

Procedure ListToSortedList (var Source, List:TStringList);
var
 i:integer;
 S:string;
begin
 List.CaseSensitive:=True;
 List.Sorted:=True;
 for i:=1 to Source.Count do
 begin
  S:=Source[i];
  repeat
   List.Add(CutNextUseDelimiter(S,' '));
  until S='';
 end;
end;


procedure TForm1.N2Click(Sender: TObject);
begin
 if not OpenDialog1.Execute then  exit;
 If OKBottomDlg.ShowModal=mrOK then
 begin
   OKBottomDlg.CheckAll (OpenDialog1.FileName);
   Memo1.Lines.Clear;
   Memo1.Lines.AddStrings(OKBottomDlg.ErrList);
   Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_err.txt'));
 end;
 OpenDocument(ChangeFileExt(OpenDialog1.FileName,'_err.txt')); // H2431: portable (was ShellExecute)
end;

procedure TForm1.N11Click(Sender: TObject);
var
 S:string;
 F:textFile;
begin
 If not OpenDialog1.Execute then exit;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 repeat
 readln(F,S);
 if S<>'' then
  begin
    if S[1] in ['1'..'9'] then
    begin
     S:='['+S;
     S:=StringReplace(S,#9,'] ',[]);
    end else
    begin
     S:=StringReplace(S,#9,'',[]);
    end;
  end;
    Memo1.Lines.Add(S);
  StatusBar1.Panels[0].Text:=IntToStr(Memo1.Lines.Count);
 until EOF(F);
  Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_2.txt'));;
end;

procedure TForm1.N4Click(Sender: TObject);
var
 i,j:integer;
 S,S2,S_new:string;
 F:textFile;
begin
 If not OpenDialog1.Execute then exit;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 repeat
 readln(F,S);
 if S[1]='[' then
  begin
   S2:=Copy (S,1,Pos(']',S)+1) ;
   Delete (S,1,Pos(']',S)+1);
  end else S2:='';
 if (Pos('����� ',S)=0) then
 i:=0;
 While i<= Length(S) do
 begin
  inc(i);
  if S[i] in ['0'..'9'] then
  begin
   S_new:=Copy(S,1,i-1)+'('+Copy(S,i,Length(S));
   S:=S_new;
   inc(i);
   for j:=i+1 to i+3 do
    if not (S[j] in ['0'..'9']) then
     begin
      S_new:=Copy(S,1,j-1)+')'+Copy(S,j,Length(S));
      S:=S_new;
      i:=j+1;
      break;
     end;
  end;
 end;
 S:=S2+S;
 Memo1.Lines.Add(S);
 StatusBar1.Panels[0].Text:=IntToStr(Memo1.Lines.Count);
 until EOF(F);
  Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_2.txt'));;
end;

procedure TForm1.N6Click(Sender: TObject);
begin
 Memo1.SelectAll;
 Memo1.CopyToClipboard;
end;

procedure TForm1.N7Click(Sender: TObject);
var
 i,j:integer;
 S:string;
begin
  // ������� ����� �� ���� ������, ���� ��� ���� ����� ����� � ��������: "123 �������" ="123<br>�������"
 i:=1;
 repeat
  S:=Memo1.Lines[i-1];
  for j:=3 to Length(S) do
   if (S[j-2] in ['0'..'9']) and
       (S[j-1]=' ') and
       (IsRussianUpperCase(S[j]) or IsRussianLowerCase(S[j]))
       then
       begin
        Memo1.Lines[i-1]:=Copy(S,1,j-1);
        Memo1.Lines.Insert(i,Copy(S,j,Length(S)));
        break;
       end;
   inc(i);
 until i>Memo1.Lines.Count;
 // ����������� �����, ���� ������ ������ - �����
 i:=2;
 repeat
  S:=Memo1.Lines[i-1];
  if (S[1] in ['0'..'9'])
    then
       begin
        Memo1.Lines[i-2]:=Memo1.Lines[i-2]+S;
        Memo1.Lines.Delete(i-1);
        dec(i);
       end;
   inc(i);
 until i>Memo1.Lines.Count;
  // ������ ����� ����� ������� �� ������� "1. 2" �� "1, 2" 
 i:=1;
 repeat
  S:=Memo1.Lines[i-1];
  for j:=3 to Length(S)-1 do
   if (S[j-2] in ['0'..'9']) and
       ((S[j-1]='.')or (S[j-1]='^')) and
       (S[j+1] in ['0'..'9'])
       then
       begin
        S[j-1]:=',';
        Memo1.Lines[i-1]:=S;
        break;
       end;
   inc(i);
 until i>Memo1.Lines.Count;
end;

procedure TForm1.N9Click(Sender: TObject);
begin
 if SaveDialog1.Execute then Memo1.Lines.SaveToFile(SaveDialog1.FileName);
 OpenDocument(SaveDialog1.FileName); // H2431: portable (was ShellExecute)
end;

procedure TForm1.N31Click(Sender: TObject);
var
 S:string;
 F:textFile;
begin
 Memo1.Lines.Clear;
 If not OpenDialog1.Execute then exit;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 repeat
 readln(F,S);
 if S<>'' then
  begin
    if S[1] in ['1'..'9'] then
    begin
     S:='['+S;
     S:=StringReplace(S,' ','] ',[]);
    end;
  end;
    Memo1.Lines.Add(S);
  StatusBar1.Panels[0].Text:=IntToStr(Memo1.Lines.Count);
 until EOF(F);
  Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_2.txt'));;
end;

procedure TForm1.N51Click(Sender: TObject);
var
 S:string;
 F:textFile;
begin
 If not OpenDialog1.Execute then exit;
 Memo1.Lines.Clear;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 repeat
 readln(F,S);
 if S<>'' then
  begin
// ������ �������
    if (S[1] in ['1'..'9']) and (Pos('-',S)=0) and (Length(S)<10 )then
     S:='-'+IntToStr(StrToInt(Trim(S))+1)+'-';
  end;
 Memo1.Lines.Add(S);
 StatusBar1.Panels[0].Text:=IntToStr(Memo1.Lines.Count);
 until EOF(F);
  Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_2.txt'));;
end;

procedure TForm1.N52Click(Sender: TObject);
var
 S:string;
 F:textFile;
begin
 If not OpenDialog1.Execute then exit;
 Memo1.Lines.Clear;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 repeat
 readln(F,S);
 if S<>'' then
  begin
   if S[1] in ['1'..'9'] then
    S:='['+CutNext(S)+'] '+S;
  end;
 Memo1.Lines.Add(S);
 StatusBar1.Panels[0].Text:=IntToStr(Memo1.Lines.Count);
 until EOF(F);
  Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_2.txt'));;
end;

procedure TForm1.N7AliceEdition1Click(Sender: TObject);
var
 F,FT,FC:textFile;
 S:WideString;
 S1:string;
 i:integer;
begin
 If not OpenDialog1.Execute then exit;
 AssignFile(F,OpenDialog1.FileName);
 AssignFile(FC,changeFileExt(OpenDialog1.FileName,'_c.txt'));
 AssignFile(FT,changeFileExt(OpenDialog1.FileName,'_t.txt'));
 reset(F);
 rewrite(FC);
 rewrite(FT);
 i:=0;
 repeat
 readln(F,S);
 inc(i);
 S1:=FromUTF8(S);
 if S1[1] in ['1'..'9'] then
   begin
     writeln(FC,S);
//     Memo1.Lines.Add(s);
   end else writeln(FT,S);
  StatusBar1.Panels[0].Text:=IntToStr(i);
 until EOF(F);
 CloseFile(F);
 CloseFile(FC);
 CloseFile(FT);
//  Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_2.txt'));;
end;

procedure TForm1.N10Click(Sender: TObject);
var
 F,FT:textFile;
 S0,S1,S2:string;
 i:integer;
 Label 2;
begin
 If not OpenDialog1.Execute then exit;
 AssignFile(F,OpenDialog1.FileName);
 AssignFile(FT,changeFileExt(OpenDialog1.FileName,'_t.txt'));
 reset(F);
 rewrite(FT);
 i:=0;
 repeat
 readln(F,S0);
 S1:='';
 S2:=S0;
 inc(i);
 if (Copy (S0,1,5)='�����') or
    (Copy (S0,1,10)='��� ������') or
    (Copy (S0,1,8)='��������') 
    then Goto 2;
  S1:='';
  if S0[1] ='[' then S1:=CutNextUseDelimiterNoTrim(S0, ' ')+' ';
  S2:=AddBracketsToNums(S0,'()');
  2:writeln(FT,S1+S2);
  StatusBar1.Panels[0].Text:=IntToStr(i);
 until EOF(F);
 CloseFile(F);
 CloseFile(FT);
end;

procedure TForm1.N13Click(Sender: TObject);
var
 S,S1,S2:string;
 F:textFile;
 i,n,k:integer;
 List:TStringList;
begin
 If not OpenDialog1.Execute then exit;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 readln(F,S); //����� ���
 readln(F,S); //��������
 List:=TStringList.Create;
 List.CaseSensitive:=True;
 List.Sorted:=True;
 n:=0;
 repeat
 readln(F,S);
 inc(n);
 if s='' then continue;
 if S[1]=#9 then Delete (S,1,1);
 for i:=1 to Length(S) do if S[i] in ['1'..'9'] then
  begin
   Delete (S,i,Length(S));
   break;
  end;
  S:=Trim(S);             
  S:=StringReplace(S,',',' ',[rfReplaceAll]);
  S:=StringReplace(S,' (',' ',[rfReplaceAll]); // �� ����� ����(��) ����� ������ ��� �����
  S:=StringReplace(S,')',' ',[rfReplaceAll]);
  S:=StringReplace(S,'[',' ',[rfReplaceAll]);
  S:=StringReplace(S,']',' ',[rfReplaceAll]);
  S:=StringReplace(S,'��.','',[rfReplaceAll]);
  S:=StringReplace(S,' � ',' ',[rfReplaceAll]);
  S:=StringReplace(S,' - ',' ',[rfReplaceAll]); // ����� � ���� ��� ���� �����
  S:=StringReplace(S,'.',' ',[rfReplaceAll]);
  S:=StringReplace(S,'�',' ',[rfReplaceAll]);
  S:=StringReplace(S,'�',' ',[rfReplaceAll]);
  S:=Trim(S);
  if s='' then continue;
  repeat
   S1:=CutNextUseDelimiter(S,' ');
   // �� ����� ����(��) ����� ������ ��� �����
   k:=Pos ('(',S1);
   if k>1 then
    begin
     S2:=CutNextUseDelimiter(S1,'(');
     List.Add(S2);
     List.Add(S2+S1);
     S1:='';
    end
    else if k=1 then // ����� ���� (���
    begin
     Delete(S1,k,1);
     List.Add(S1)
    end;
   if Length(S1)<>1 then List.Add(S1);
  until S='';
//  Memo1.Lines.Add(S);
  StatusBar1.Panels[0].Text:=IntToStr(n);
 until EOF(F);
 Memo1.Lines.Clear;
 Memo1.Lines.AddStrings(List);
 List.Free;
 Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'.dic'));;
 OpenDocument(ChangeFileExt(OpenDialog1.FileName,'.dic')); // H2431: portable (was ShellExecute)
end;

procedure TForm1.N14Click(Sender: TObject);
var
 F:textFile;
 List:TstringList;
 i:integer;
begin
 If not OpenDialog1.Execute then exit;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 List:=TstringList.Create;
 List.CaseSensitive:=True;
 List.Sorted:=True;
 repeat
  readln(F,S);
  List.Add(S);
 until EOF(F);
 CloseFile(F);
 Memo1.Lines.Clear;
 Memo1.Lines.AddStrings(List);
 List.Free;
 Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_srt.dic'));
 OpenDocument(ChangeFileExt(OpenDialog1.FileName,'_srt.dic')); // H2431: portable (was ShellExecute)
end;

 //��������
 // ���������� ������������������
 //��� ������ �������������, ������� ����� �������� ��������: � ������ �� ������ ���� ������� ���� ", ������ "������" � "�����"
// ������������������ ����: ". �", ��� � - �������� �����, � ������ �������� ������ ����� ������. � ������� �� � ������������ - ���, ��� ��� ��� ����� ���� ��������� ���� �. �., �. �., �. �.
// ����� �������� ����� " �� " - ����� ����� ����������, �� �� ���������� ������ ��� ������������� ���� �� ��������. ������ ��� �������� ������ " �� ".


// ����� ����������� � ���������� ����� �� ����� FNW.
procedure TForm1.N15Click(Sender: TObject);
var
 FW,FT:textFile; // words, text
 List:TstringList;
 i,k,j,Pos_Word, Pos_sentence1,Pos_sentence2:integer;
 S,S_Found,FNW,FNT:string;
begin
 Memo1.Lines.Clear;
 OpenDialog1.Title:='��� ����� �� ������� ��� ������';
 If not OpenDialog1.Execute then exit;
 OpenDialog1.Title:='��� ����� � ������� ����� ������';
 FNW:=OpenDialog1.FileName;
 If not OpenDialog1.Execute then exit;
 FNT:=OpenDialog1.FileName;
 AssignFile(FW,FNW);
 reset(FW);
 List:=TstringList.Create;
 List.LoadFromFile(FNT);
 k:=0;
 repeat
  readln(FW,S);
  inc(k);
  for i:=1 to List.Count do
  begin
   Pos_Word:=Pos(S,List[i-1]);
   if Pos_Word>0 then
   begin
    S_Found:=List[i-1];
    Pos_sentence1:=1;
    Pos_sentence2:=Length(S_Found);
    for j:=Pos_Word to Length(S_Found) do if S_Found[j] in ['.','!','?'] then begin Pos_sentence2:=j;break; end;
    for j:=Pos_Word downto 1 do if S_Found[j] in ['.','!','?'] then begin Pos_sentence1:=j;break; end;
    S_Found:=Trim(Copy (S_Found,Pos_sentence1,Pos_sentence2-Pos_sentence1+1));
    Memo1.Lines.Add(S+#9+S_Found);
    break;
   end;
  end;
  StatusBar1.Panels[0].Text:=IntToStr(k);
 until EOF(FW);
 CloseFile(FW);
 List.Free;
 Memo1.Lines.SaveToFile(ChangeFileExt(FNW,'_found.txt'));
 OpenDocument(ChangeFileExt(FNW,'_found.txt')); // H2431: portable (was ShellExecute)
end;

procedure TForm1.N16Click(Sender: TObject);
var
 i:integer;
 S,SearchText, ReplaceText:string;

{
������ Memo1 (����������� - ���������):
�������	�������
�����������	�����������
�������	�������
����	����
��������	��������
}
begin
 for i:=1 to Memo1.Lines.Count do
 begin
  S:=Memo1.Lines[i-1];
  StatusBar1.Panels[0].Text:=S;
  Application.ProcessMessages;
  SearchText:=CutNextUseDelimiter(S,#9);
  ReplaceText:=S;
  Memo2.Text := StringReplace(Memo2.Text, SearchText, ReplaceText, [rfReplaceAll]);
 end;
end;

procedure TForm1.RichEdit2Click(Sender: TObject);
begin
 if SaveDialog1.Execute then Memo2.Lines.SaveToFile(SaveDialog1.FileName);
 OpenDocument(SaveDialog1.FileName); // H2431: portable (was ShellExecute)
end;

procedure TForm1.N81Click(Sender: TObject);
var
 S:string;
 F:textFile;
begin
 If not OpenDialog1.Execute then exit;
 Memo1.Lines.Clear;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 repeat
 readln(F,S);
 S:=Trim(S);
 if S<>'' then
  begin
// ������ �������
    if (S[1]='-')and (S[2] in ['1'..'9']) then
    begin
     S:=S+'-';
    end;
  end;
 Memo1.Lines.Add(S);
 StatusBar1.Panels[0].Text:=IntToStr(Memo1.Lines.Count);
 until EOF(F);
 Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_2.txt'));;
end;

procedure TForm1.N17Click(Sender: TObject);
var
 S:string;
 F:textFile;
begin
 If not OpenDialog1.Execute then exit;
 Memo1.Lines.Clear;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 repeat
 readln(F,S);
 S:=Trim(S);
 if S<>'' then
  begin
// ������ ����
    if (S[1]='[')and (S[2] in ['1'..'9']) then
    begin
     S:=StringReplace(S,'�','-',[]);
    end;
  end;
 Memo1.Lines.Add(S);
 StatusBar1.Panels[0].Text:=IntToStr(Memo1.Lines.Count);
 until EOF(F);
 Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_2.txt'));;
end;

Procedure TForm1.CheckQuotes (AFileName,S_Open,S_Close:string);
var
 F:textFile;
 S,S1,S2:widestring;
 i,NLine:integer;
 b1,b2:boolean;
 k1,k2:integer;
 S_Ansi:string;
 S_k1,S_k2:string;
begin
 AssignFile(F,AFileName);
 Reset(F);
 S1:=ToUTF8(S_Open);
 S2:=ToUTF8(S_Close);
 b1:=False;
 b2:=False;
 k1:=0;
 k2:=0;
 NLine:=0;
 repeat
  inc(nLine);
  Readln(F,S);
   S_Ansi:=FromUTF8(S);
   for i:=1 to Length(S_Ansi) do
   begin
     if S_Ansi[i]=S_Open then
     begin
       if b1=True then  Memo1.Lines.Add('��� ������������� ������� ������ '+IntToStr(NLine)+', '+IntToStr(k1)+':'+S_k1+ ' | '+Copy(S_Ansi,i,20));
       b1:=True;
       if b2=True then b2:=False;
       k1:=i;
       S_k1:=Copy(S_Ansi,k1,20);
     end else
     begin
      if S_Ansi[i]=S_Close then
      begin
        if b2=True then  Memo1.Lines.Add('��� ������������� ������� ������ '+IntToStr(NLine)+', '+IntToStr(k2)+':'+S_k2+ ' | '+Copy(S_Ansi,i-19,20));
        b2:=True;
        if b1=True then b1:=False;
        k2:=i;
        S_k2:=Copy(S_Ansi,k2-19,20);
      end;
    end;
  end;
 Application.ProcessMessages;
 StatusBar1.Panels[0].Text:=IntToStr(NLine);
 until EOF(F);
 Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_err.txt'));;
 CloseFile(F);
end;

procedure TForm1.N18Click(Sender: TObject);
begin
 If not OpenDialog1.Execute then exit;
 Memo1.Lines.Clear;
 //��->��
 Memo1.Lines.Add('-------������ ������� �������----------');
 CheckQuotes (OpenDialog1.FileName,'�','�');
 Memo1.Lines.Add('-------������ ������� ������----------');
 CheckQuotes (OpenDialog1.FileName,'�','�');
 OpenDocument(ChangeFileExt(OpenDialog1.FileName,'_err.txt')); // H2431: portable (was ShellExecute)
end;

procedure TForm1.HTML1Click(Sender: TObject);
var
 MhHTMLBuilder:TMhHTMLBuilder;
begin
 If not OpenDialog1.Execute then exit;
 MhHTMLBuilder:=TMhHTMLBuilder.Create;
 MhHTMLBuilder.OnProgress:=BuilderProgress;
 MhHTMLBuilder.OnConfirm:=BuilderConfirm;
 MhHTMLBuilder.OnError:=BuilderError;
 MhHTMLBuilder.Execute(OpenDialog1.FileName);
 if MhHTMLBuilder.HasErrors then
  OpenDocument(MhHTMLBuilder.ErrFileFullPath); // H2431: portable (was ShellExecute)
 MhHTMLBuilder.Destroy;
 StatusBar1.Panels[0].Text:='HTML build comlete!';
 Beep; // H2431: portable (was MessageBeep)
end;

procedure TForm1.N141Click(Sender: TObject);
var
 S,s1:string;
 Pos_Tire:integer;
 F:textFile;
begin
 If not OpenDialog1.Execute then exit;
 Memo1.Lines.Clear;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 repeat
 readln(F,S);
 if S<>'' then
  begin
   if S[1] in ['1'..'9'] then
   begin
    s1:=CutNext(S);
    if Pos('�',s1)>0 then s1[Pos('�',s1)]:='-';
    S:='['+S1+'] '+S;
   end;
  end;
 Memo1.Lines.Add(S);
 StatusBar1.Panels[0].Text:=IntToStr(Memo1.Lines.Count);
 until EOF(F);
  Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_2.txt'));;
end;

procedure TForm1.N61Click(Sender: TObject);
var
 S,s1:string;
 Pos_Tire:integer;
 F:textFile;
 i,j:integer;
 Label 1;
begin
 If not OpenDialog1.Execute then exit;
 Memo1.Lines.Clear;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 repeat
 readln(F,S);
 S1:='';
 if copy (S,1,5)='�����' then  begin Goto 1 end;
 for i:=10 to Length (S) do
  begin
   if S[i] in ['1'..'9'] then
   begin
    if S[i-1]<>' ' then continue
     else
     begin
      s1:='';
      // �������� ��������
      for j:=i to Length(S) do
      begin
       if S[j]=' ' then break;
       S1:=s1+S[j];
       S[j]:=' ';
      end;
     end;
   end
  end;
1: Memo1.Lines.Add(' '+s1+' '+S);
 StatusBar1.Panels[0].Text:=IntToStr(Memo1.Lines.Count);
 until EOF(F);
  Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_2.txt'));;
 OpenDocument(ChangeFileExt(OpenDialog1.FileName,'_2.txt')); // H2431: portable (was ShellExecute)
end;

procedure TForm1.N20Click(Sender: TObject);
var
 S:string;
 F:textFile;
 Incr:integer;
begin
 Incr:=2;
 If not OpenDialog1.Execute then exit;
 Memo1.Lines.Clear;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 repeat
 readln(F,S);
 if S<>'' then
  begin
// ������ �������
    if (S[1] ='-') and (S[2] in ['1'..'9']) then
    begin
     S:=Trim(StringReplace(S,'-','',[rfReplaceAll]));
     S:='-'+IntToStr(StrToInt(S)+incr)+'-';
    end;
  end;
 Memo1.Lines.Add(S);
 StatusBar1.Panels[0].Text:=IntToStr(Memo1.Lines.Count);
 until EOF(F);
 Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_2.txt'));;
end;

procedure TForm1.N21Click(Sender: TObject);
var
 S:string;
 F:textFile;
 nPesn:integer;
begin
 If not OpenDialog1.Execute then exit;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 repeat
 readln(F,S);
 nPesn:=Pos('�����',S);
 if (nPesn>0)and(nPesn=Length(S)-4) then
    begin
     S:='#'+S;
    end;
  Memo1.Lines.Add(S);
  StatusBar1.Panels[0].Text:=IntToStr(Memo1.Lines.Count);
 until EOF(F);
  Memo1.Lines.SaveToFile(ChangeFileExt(OpenDialog1.FileName,'_2.txt'));;
end;

procedure TForm1.ValmikiExtractItemClick(Sender: TObject);
var
 F,FOut:textFile;
 i:integer;
 S_Ansi:string;
const
 Label_Sans='<p class="SanSloka">';
begin
 If not OpenDialog1.Execute then exit;
 AssignFile(F,OpenDialog1.FileName);
 AssignFile(FOut,ChangeFileExt(OpenDialog1.FileName,'_2.txt'));
 Rewrite(FOut);
 reset(F);
 i:=0;
 repeat
 readln(F,S); inc(i);
 S_Ansi:=FromUTF8(S);
 if Pos(Label_Sans, S_Ansi)>0  then
   repeat
    readln(F,S);inc(i);
    S_Ansi:=FromUTF8(S);
    if S_Ansi='' then Continue;
    if Pos('audio',S_Ansi)>0 then Continue;
    if Pos('.mp3',S_Ansi)>0 then Continue;
    if Pos('media',S_Ansi)>0 then Continue;
    if Pos('</p>',S_Ansi)>0 then begin Writeln(FOut); break; end;
    Write(FOut,S);
   until False;
  StatusBar1.Panels[0].Text:=IntToStr(i);
  Application.ProcessMessages;
  until EOF(F);
 CloseFile(F);
 CloseFile(FOut);
end;

procedure TForm1.IAST1Click(Sender: TObject);
var
 S:widestring;
 F:textFile;
 AFileName:string;
var
 i,j:integer;
 ShlokasArr:array of TFullShloka;
begin
 If not OpenDialog1.Execute then exit;
 AssignFile(F,OpenDialog1.FileName);
 reset(F);
 i:=0;
 repeat                                        
  inc(i);
  SetLength(ShlokasArr,i);
  readln(F,S);
  CreateShlokaNumber(S,ShlokasArr[i-1]);
  StatusBar1.Panels[0].Text:=IntToStr(Memo1.Lines.Count);
 until EOF(F);
 CloseFile(F);
// ��������� ������ ���, ��� �� ���
 for i:=1 to Length(ShlokasArr) do
 if ShlokasArr[i-1].S_Num='' then
   for j:=i+1 to Length(ShlokasArr) do
      if ShlokasArr[j-1].S_Num<>'' then
       begin
        ShlokasArr[i-1].S_Num:=ShlokasArr[j-1].S_Num;
        break;
       end;
 AFileName:=ChangeFileExt (OpenDialog1.FileName,'_2.txt');
 AssignFile(F,AFileName);
 Rewrite(F);
 for i:=1 to Length(ShlokasArr) do
 begin
  Writeln (F,ShlokasArr[i-1].S_Num,#9,ShlokasArr[i-1].S_Text);
 end;
 CloseFile(F);
 OpenDocument(AFileName); // H2431: portable (was ShellExecute)
end;

procedure TForm1.N121Click(Sender: TObject);
var
 F1,F2:string;
const
 Lab1='<!-- Insert code block beginning -->';
 Lab2='<!-- Insert code block end -->';
begin
 F1:='C:\Temp\1\Res_html.txt';
 F2:='C:\Temp\1\r1_corpus.html';
 PutFile1ToFile2 (F1,F2,Lab1,Lab2);
end;

procedure TForm1.N22Click(Sender: TObject);
var
 S:widestring;
 F,F2:textFile;
 Incr:integer;
begin
 Incr:=1;
 If not OpenDialog1.Execute then exit;
 Memo1.Lines.Clear;
 AssignFile(F,OpenDialog1.FileName);
 AssignFile(F2,ChangeFileExt(OpenDialog1.FileName,'_2.txt'));
 reset(F);
 Rewrite(F2);
 repeat
 readln(F,S);
 if S<>'' then
  begin
// ������ �������
    if (S[1] ='[') and (S[2] in [WideChar('1')..WideChar('9')]) then
    begin
     S:=Trim(StringReplace(S,'[','',[rfReplaceAll]));
     S:=Trim(StringReplace(S,']','',[rfReplaceAll]));
     S:='-'+IntToStr(StrToInt(S)+incr)+'-';
    end;
  end;
 writeln(F2,S);
 StatusBar1.Panels[0].Text:=IntToStr(Memo1.Lines.Count);
 until EOF(F);
 CloseFile(F);
 CloseFile(F2);
 StatusBar1.Panels[0].Text:='OK';
end;

procedure TForm1.DandaItemClick(Sender: TObject);
var
 S:widestring;
 F,F2:textFile;
begin
 If not OpenDialog1.Execute then exit;
 AssignFile(F,OpenDialog1.FileName);
 AssignFile(F2,ChangeFileExt(OpenDialog1.FileName,'_c.txt'));
 reset(F);
 Rewrite(F2);
 repeat
  readln(F,S);
  if Pos(S_danda2,S)>0
   then S:=S+S_danda2;
  writeln(F2,S);
 until EOF(F);
 CloseFile(F);
 CloseFile(F2);
end;

procedure TForm1.FormCreate(Sender: TObject);
var
 F,F2:textFile;
begin
 AssignFile(F,ChangeFileExt(Application.ExeName,'.txt'));
 reset(F);
 readln(F,S_danda1);
 readln(F,S_danda2);
 CloseFile(F);
end;

procedure TForm1.IAST2Click(Sender: TObject);
var
 S_Cur,S_Old,S1,S2:widestring;
 F,F2:textFile;
 i:integer;
begin
 If not OpenDialog1.Execute then exit;
 Memo1.Lines.Clear;
 AssignFile(F,OpenDialog1.FileName);
 Memo1.Lines.Add(OpenDialog1.FileName);
 AssignFile(F2,ChangeFileExt(OpenDialog1.FileName,'_c.txt'));
 reset(F);
 readln(F,S_old);
 Rewrite(F2);
 i:=1;
 repeat
  inc(i);
  readln(F,S_Cur);
  // ���������
  if not IsEqualStrWithoutDandas (S_Cur,S_Old)
   then writeln(F2,S_Old)
   else Memo1.Lines.Add(IntToStr(i)+'='+IntToStr(i-1));
   S_Old:=S_Cur;
 until EOF(F);
 CloseFile(F);
 writeln(F2,S_Cur);
 CloseFile(F2);
 Memo1.Lines.Add('Complete');
end;

procedure TForm1.IAST3Click(Sender: TObject);
begin
 GenerateRusFromIAST;
// GenerateRusFromIAST_Old;
end;


procedure TForm1.Danda_SpaceClick(Sender: TObject);
var
 S:widestring;
 F,F2:textFile;
 FileName2:string;
begin
 If not OpenDialog1.Execute then exit;
 AssignFile(F,OpenDialog1.FileName);
 FileName2:=ChangeFileExt(OpenDialog1.FileName,'_c.txt');
 AssignFile(F2,FileName2);
 reset(F);
 Rewrite(F2);
 repeat
  readln(F,S);
  if Pos(' '+S_danda1,S)=0 then S:=StringReplace(S,S_danda1,' '+S_danda1,[]);
  if Pos(' '+S_danda2,S)=0 then S:=StringReplace(S,S_danda2,' '+S_danda2,[]);
  writeln(F2,S);
 until EOF(F);
 CloseFile(F);
 CloseFile(F2);
 DeleteFile(OpenDialog1.FileName);
 RenameFile(FileName2,OpenDialog1.FileName);
end;

procedure TForm1.CorpushtmlbuildManyBooks1Click(Sender: TObject);
var
 MhHTMLBuilder:TMhHTMLBuilder;
 i:integer;
 List:TStringList;
begin
 If not OpenDialog1.Execute then exit;
 List:=TStringList.Create;
 List.LoadFromFile(OpenDialog1.FileName);
 for i:=1 to List.Count do
 begin
   Memo1.Lines.Add('Processing '+ List[i-1]);
   MhHTMLBuilder:=TMhHTMLBuilder.Create;
   MhHTMLBuilder.OnProgress:=BuilderProgress;
   MhHTMLBuilder.OnConfirm:=BuilderConfirm;
   MhHTMLBuilder.OnError:=BuilderError;
   MhHTMLBuilder.Execute(List[i-1]);
   if MhHTMLBuilder.HasErrors then
    OpenDocument(MhHTMLBuilder.ErrFileFullPath); // H2431: portable (was ShellExecute)
   MhHTMLBuilder.Destroy;
   StatusBar1.Panels[0].Text:='HTML build comlete for '+List[i-1];
  end;
 Beep; // H2431: portable (was MessageBeep)
 List.Free;
end;

procedure TForm1.N23Click(Sender: TObject);
var
 F:textFile;
 F2:textFile;
 i:integer;
 S:widestring;
 S_Arr_New,S_Arr_Old:array [1..8] of widestring;
 S_Out:string;
 //------------------------------------
 Procedure ReadCurStr;
 var
  i:integer;
 begin
    readln(F,S);
    for i:=1 to 7 do
    begin
     S_Arr_New[i]:=UTF8CutNextUseDelimiterNoTrim(S,#9);
    end;
    S_Arr_New[8]:=S;
 end;
 //------------------------------------
 Procedure Form_S_Out;
 var
  i:integer;
 begin
    S_Out:=S_Arr_Old[1];
    for i:=2 to 8 do
    begin
     S_Out:=S_Out+#9+S_Arr_Old[i];
    end;
 end;
 //------------------------------------
 Procedure Concat_New_And_Old_Arr;
 var
  i:integer;
 begin
    for i:=6 to 8 do
    begin
     S_Arr_Old[i]:=S_Arr_Old[i]+' <br> '+S_Arr_new[i];
    end;
 end;
 //------------------------------------
begin
 If not OpenDialog1.Execute then exit;
 AssignFile(F,OpenDialog1.FileName);
 AssignFile(F2,ChangeFileExt(OpenDialog1.FileName,'_.txt'));
 Reset(F);
 Rewrite(F2);
 ReadCurStr;
 S_Arr_Old:=S_Arr_New;
 repeat
  ReadCurStr;
  if S_Arr_New[2]<>''
  then
    begin
     Form_S_Out;
     Writeln(F2,s_Out);
     S_Arr_Old:=S_Arr_New;
    end
  else //S_Arr_New[2]=''
    begin
     Concat_New_And_Old_Arr;
    end;
 until EOF(F);
 Form_S_Out;
 Writeln(F2,s_Out);
 CloseFile(F);
 CloseFile(F2);
end;

procedure TForm1.Memo1Memo21Click(Sender: TObject);
var
 i:integer;
 NBook, NShloka:integer;
 S:string;
begin
 Memo2.Clear;
 NBook:=0;
 for i:=1 to Memo1.Lines.Count do
 begin
  S:=Memo1.Lines[i-1];
  if S[1]='@' then inc (NBook) else
  if S[1] in ['1'..'9'] then NShloka:=StrToInt(CutNextUseDelimiter(S,')')) else
  begin
   Memo2.Lines.Add(S+#9+IntToStr(NBook)+'.'+IntToStr(NShloka));
  end;
 end;
end;


procedure TForm1.GenerateRusFromIAST_OLD;
var
 S:string;
 S_W:widestring;
 F,F2:textFile;
 i,k:integer;
 iShloka_Old,iBook,iGlava, iShloka:integer;
 ShlokaOutputNum:integer;
 ShlokaOutputNum_Uvacha:integer;
// bCurChapterMessage:boolean;
 SWArr:array of Widestring;
 SArr:TStringArr;
 N_Uvacha:integer;
 ChapterUvachaListSl:TStringList;
 UvachaNumsArr:TIntArr;

begin
//--------������ ��������� Uvacha ---------------
 If not OpenDialog1.Execute then exit;
//--------������ ��������� Uvacha ---------------
 AssignFile(F,ExtractFilePath(OpenDialog1.FileName)+'uvacha.txt');
 reset(F);
 i:=0;
 repeat
  readln(F,S_W);
  inc(i);
  SetLength(SWArr,i);
  SetLength(SArr,i);
  SWArr[i-1]:=UTF8CutNextUseDelimiterNoTrim(S_W,#9);
  SArr[i-1]:=FromUTF8(S_W);
 until EOF(F);
 CloseFile(F);
//--------����� ������ ��������� Uvacha ---------------
 AssignFile(F,OpenDialog1.FileName);
 AssignFile(F2,ChangeFileExt(OpenDialog1.FileName,'_AutoRus.txt'));
 reset(F);
 rewrite(F2);
 iShloka_Old:=99;
 ChapterUvachaListSl:=TStringList.Create;
 repeat
  readln(F,S_W);
  if Length(S_W)>50 then SetLength(S_W,50);
  S:=S_W;
  N_Uvacha:=0;
//  for i:=1 to Length(SWArr) do if Pos(SWArr[i],S_W)>0 then begin N_Uvacha:=i+1; break;  end;
  for i:=1 to Length(SWArr) do if Pos(SWArr[i-1],S_W)>0 then begin N_Uvacha:=i; break;  end;
  S:=CutNextUseDelimiterNoTrim(S,#9);
  StatusBar1.Panels[0].Text:=S;
  Application.ProcessMessages;
  iBook:=StrToInt(CutNextUseDelimiter(S,'.'));
  iGlava:=StrToInt(CutNextUseDelimiter(S,'.'));
  iShloka:=StrToInt(S);
  If (iShloka=1) and (iShloka-iShloka_Old<0)
   then
    begin
       if ChapterUvachaListSl.IndexOf(IntToStr(iShloka_Old))<0 then
        begin
         ChapterUvachaListSl.Add(IntToStr(iShloka_Old));
         SetLength(UvachaNumsArr,ChapterUvachaListSl.Count);
         UvachaNumsArr[ChapterUvachaListSl.Count-1]:=0;
        end;   
    // ������ - ��������� ������ -------------------------
     Writeln(F2, '����� '+IntToStr(iGlava-1));
     if UvachaNumsArr[0]>0 then Writeln(F2, GetRusText (UvachaNumsArr[0], SArr));
     Write(F2, '[1-');
     for i:=2 to ChapterUvachaListSl.Count-1 do
      begin
       Writeln(F2, IntToStr(StrToInt(ChapterUvachaListSl[i-1])-1)+'] '+ GetRusText (0, SArr));
       if UvachaNumsArr[i-1]>0 then Writeln(F2, GetRusText (UvachaNumsArr[i-1], SArr));
       Write(F2, '['+ChapterUvachaListSl[i-1]+'-');
      end;
      i:=ChapterUvachaListSl.Count;
       Writeln(F2, ChapterUvachaListSl[i-1] +'] '+ GetRusText (0, SArr));

    // ����� - ��������� ������ -------------------------
     ChapterUvachaListSl.Clear;
     ChapterUvachaListSl.Add('1');
     SetLength(UvachaNumsArr,ChapterUvachaListSl.Count);
     UvachaNumsArr[ChapterUvachaListSl.Count-1]:=N_Uvacha;
    end;
   if (N_Uvacha>0)and (ChapterUvachaListSl.IndexOf(IntToStr(iShloka))<0) then
   begin
     ChapterUvachaListSl.Add(IntToStr(iShloka));
     SetLength(UvachaNumsArr,ChapterUvachaListSl.Count);
     UvachaNumsArr[ChapterUvachaListSl.Count-1]:=N_Uvacha;
   end;
  iShloka_Old:=iShloka;
 until EOF(F);
// -------------------------
 if ChapterUvachaListSl.IndexOf(IntToStr(iShloka_Old))<0 then
  begin
   ChapterUvachaListSl.Add(IntToStr(iShloka_Old));
   SetLength(UvachaNumsArr,ChapterUvachaListSl.Count);
   UvachaNumsArr[ChapterUvachaListSl.Count-1]:=0;
  end;
 // ������ - ��������� ������ ��� ��������� �����
 Writeln(F2, '����� '+IntToStr(iGlava));
 if UvachaNumsArr[0]>0 then Writeln(F2, GetRusText (UvachaNumsArr[0], SArr));
 Write(F2, '[1-');
 for i:=2 to ChapterUvachaListSl.Count-1 do
  begin
   Writeln(F2, IntToStr(StrToInt(ChapterUvachaListSl[i-1])-1)+'] '+ GetRusText (0, SArr));
   if UvachaNumsArr[i-1]>0 then Writeln(F2, GetRusText (UvachaNumsArr[i-1], SArr));
   Write(F2, '['+ChapterUvachaListSl[i-1]+'-');
  end;
  i:=ChapterUvachaListSl.Count;
  Writeln(F2, ChapterUvachaListSl[i-1] +'] '+ GetRusText (0, SArr));
    // ����� - ��������� ������ -------------------------
 CloseFile(F);
 CloseFile(F2);
 ChapterUvachaListSl.Free;
end;
procedure TForm1.GenerateRusFromIAST;
var
 F,F2:textFile;
 SArr:TStringArr;
 SWArr:TWideStringArr;
 i:integer;
 S_W:widestring;
 S:string;
 iBook, iGlava, iShloka,iShloka_old,iGlava_old:integer;
 TextIndex:integer;
begin
//--------������ ��������� Uvacha ---------------
 If not OpenDialog1.Execute then exit;
//--------������ ��������� Uvacha ---------------
 AssignFile(F,ExtractFilePath(OpenDialog1.FileName)+'uvacha.txt');
 reset(F);
 i:=0;
 repeat
  readln(F,S_W);
  inc(i);
  SetLength(SWArr,i);
  SetLength(SArr,i);
  SWArr[i-1]:=UTF8CutNextUseDelimiterNoTrim(S_W,#9);
  SArr[i-1]:=FromUTF8(S_W);
 until EOF(F);
 CloseFile(F);
//--------����� ������ ��������� Uvacha ---------------
 AssignFile(F,ExtractFilePath(OpenDialog1.FileName)+'01_Sanskrit.txt');
 AssignFile(F2,ExtractFilePath(OpenDialog1.FileName)+'02_Transl_AutoRus.txt');
 reset(F);
 rewrite(F2);
 iGlava_old:=0;
 repeat
  readln(F,S_W);
  S:=S_W;
  S:=CutNextUseDelimiterNoTrim(S,#9);
  StatusBar1.Panels[0].Text:=S;
  Application.ProcessMessages;
  iBook:=StrToInt(CutNextUseDelimiter(S,'.'));
  iGlava:=StrToInt(CutNextUseDelimiter(S,'.'));
  iShloka:=StrToInt(S);
  UTF8CutNextUseDelimiterNoTrim(S_W,#9);
  // ���� ����� ����� - ����� ������ �����
  if iGlava<>iGlava_old then Writeln(F2, '����� '+IntToStr(iGlava));
  // ���� ���������� ����� - ����� ����� ����� (���� �������, ���� ��� �����)
  if iShloka<>iShloka_Old then
  begin
   TextIndex:=GetRusTextIndex(S_W,SWArr);
   if TextIndex=0
    then Writeln(F2, '[',intTostr(iShloka),'] �')
    else
     begin
      Writeln(F2, SArr[Textindex-1]);
      Writeln(F2, '[',intTostr(iShloka),'] �')
     end;
  end;
  iShloka_old:=iShloka;
  iGlava_old:=iGlava;
 until EOF(F);

 CloseFile(F);
 CloseFile(F2);
end;

procedure TForm1.CorpushtmlbuildManyBooks2Click(Sender: TObject);
var
 MhHTMLBuilder:TMhHTMLBuilder;
 i:integer;
 OutputHTML:string;
begin
 If not OpenDialog1.Execute then exit;
 LoadBooksCount (OpenDialog1.FileName);
 for i:=1 to BooksCount do
 begin
  PrepareBook (OpenDialog1.FileName,i);
  MhHTMLBuilder:=TMhHTMLBuilder.Create;
  MhHTMLBuilder.OnProgress:=BuilderProgress;
  MhHTMLBuilder.OnConfirm:=BuilderConfirm;
  MhHTMLBuilder.OnError:=BuilderError;
  MhHTMLBuilder.Execute(OpenDialog1.FileName);
  if MhHTMLBuilder.HasErrors then
   OpenDocument(MhHTMLBuilder.ErrFileFullPath); // H2431: portable (was ShellExecute)
  OutputHTML:=MhHTMLBuilder.KeyWords.OutputHTML;
  MhHTMLBuilder.Destroy;
//  ShowMessage('Book '+IntToStr(i)+' complete!');
  RenameErrFile (OpenDialog1.FileName,i);
//  if i=1 then exit;
 end;
 ConcatAllHTMLFiles(OpenDialog1.FileName,BooksCount);
 PutFile1ToFile2(ExtractFilePath(OpenDialog1.FileName)+'Res_html_buff.txt',OutputHTML,InsertBlockLab1,InsertBlockLab2);
 StatusBar1.Panels[0].Text:='HTML build comlete!';
 Beep; // H2431: portable (was MessageBeep)
end;

procedure TForm1.LoadBooksCount(AFileName:string);
var
 F:textFile;
 S_W:widestring;
begin
 AssignFile(F,ExtractFilePath(AFileName)+'ManyBooks_01_Sanskrit.txt');
 Reset(F);
 Repeat
  readln (F,S_W);
 until EOF(F);
 BooksCount:=StrToInt(UTF8CutNextUseDelimiterNoTrim(S_W, '.'));
 CloseFile(F);
end;

procedure TForm1.PrepareBook(AFileName: string; NBook: integer);
begin
 LoadManyBookConfig (AFileName);
 PrepareSanskrit (AFileName, NBook);
 PrepareTransl (AFileName, NBook);
 PrepareComments (AFileName, NBook);
end;
procedure TForm1.PrepareSanskrit(AFileName: string; NBook: integer);
var
 F,F2:textFile;
 S_W,S_W0:widestring;
 BookNum:integer;
begin
 AssignFile (F, ExtractFilePath(AFileName)+'ManyBooks_01_Sanskrit.txt');
 Reset(F);
 AssignFile (F2, ExtractFilePath(AFileName)+'01_Sanskrit.txt');
 Rewrite(F2);
 repeat
  readln (F,S_W0);
  S_W:=S_W0;
  BookNum:=StrToInt(UTF8CutNextUseDelimiterNoTrim(S_W, '.'));
  if BookNum=NBook then writeln (F2,S_W0);
 until EOF(F);
 CloseFile(F);
 CloseFile(F2);
end;

procedure TForm1.PrepareTransl(AFileName: string; NBook: integer);
var
 F,F2:textFile;
 S_W:widestring;
 S_Ansi:string;
 BookNum:integer;
begin
 AssignFile (F, ExtractFilePath(AFileName)+'ManyBooks_02_Transl.txt');
 Reset(F);
 AssignFile (F2, ExtractFilePath(AFileName)+'02_Transl.txt');
 Rewrite(F2);
 writeln(F2,ToUTF8('-999-'));
 BookNum:=0;
 repeat
  readln (F,S_W);
  S_Ansi:=FromUTF8(S_w);
  if Pos(ManyBookSign,S_Ansi)>0 then inc(BookNum)
  else
  if BookNum=NBook then writeln (F2,S_W);
 until EOF(F);
 CloseFile(F);
 CloseFile(F2);
end;


procedure TForm1.PrepareComments(AFileName: string; NBook: integer);
var
 F,F2:textFile;
 S_W:widestring;
 S_Ansi:string;
 BookNum:integer;
begin
 AssignFile (F, ExtractFilePath(AFileName)+'ManyBooks_03_Comments.txt');
 Reset(F);
 AssignFile (F2, ExtractFilePath(AFileName)+'03_Comments.txt');
 Rewrite(F2);
 writeln(F2,ToUTF8('����������'));
 writeln(F2,ToUTF8('-999-'));
 BookNum:=0;
 repeat
  readln (F,S_W);
  S_Ansi:=FromUTF8(S_w);
  if Pos(ManyBookSign,S_Ansi)>0 then inc(BookNum)
  else 
  if BookNum=NBook then writeln (F2,S_W);
 until EOF(F);
 CloseFile(F);
 CloseFile(F2);
end;

procedure TForm1.LoadManyBookConfig (AFileName:string);
var
 MB_INIFile:TIniFile;
begin
 MB_INIFile:=TINIFile.Create(ExtractFilePath(AFileName)+'many_books_config.ini');
 ManyBookSign:=MB_INIFile.ReadString('Common','BookSign','');
 MB_INIFile.Free;
end;

procedure TForm1.RenameErrFile(AFileName:string; NBook:integer);
var
 FN:string;
 FN2:string;
begin
 FN:=ExtractFilePath(AFileName)+'Err.txt';
 DeleteFile(ChangeFileExt(FN, IntToStr(NBook)+'.txt'));
 if FileExists(FN) then RenameFile(FN,ChangeFileExt(FN, IntToStr(NBook)+'.txt'));

 FN:=ExtractFilePath(AFileName)+'Res.txt';
 DeleteFile(ChangeFileExt(FN, IntToStr(NBook)+'.txt'));
 if FileExists(FN) then RenameFile(FN,ChangeFileExt(FN, IntToStr(NBook)+'.txt'));

 FN:=ExtractFilePath(AFileName)+'Res_html.txt';
 DeleteFile(ChangeFileExt(FN, IntToStr(NBook)+'.txt'));
 if FileExists(FN) then RenameFile(FN,ChangeFileExt(FN, IntToStr(NBook)+'.txt'));
 
end;

procedure TForm1.ConcatAllHTMLFiles(AFileName: string;
  BooksCount: integer);
var
 FN,FN0,FNi,FNbuff,FNtmp:string;
 i:integer;
begin
 FN:=ExtractFilePath(AFileName)+'Res_html.txt';
 FN0:=ChangeFileExt(FN, '0.txt');
 FNi:=ChangeFileExt(FN, '1.txt');
 FNbuff:=ChangeFileExt(FN, '_buff.txt');
 FNtmp:=ChangeFileExt(FN, '_.txt');
 if not CopyFile(FNi, FNbuff, [cffOverwriteFile]) then
  raise Exception.CreateFmt('CopyFile failed: %s -> %s', [FNi, FNbuff]); // H2431
 for i:=2 to BooksCount do
 begin
  FNi:=ChangeFileExt(FN, IntTostr(i)+'.txt');
  MergeFiles (FNBuff,FNi,FNtmp);
  DeleteFile(FNbuff);
  RenameFile(FNtmp, FNbuff);
 end;

end;

end.

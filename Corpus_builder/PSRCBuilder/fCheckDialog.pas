unit fCheckDialog;

{$MODE Delphi}

interface

uses
  SysUtils, Classes, Graphics, Forms, Controls, StdCtrls, ExtCtrls, Dialogs;

type
  TOKBottomDlg = class(TForm)
    OKBtn: TButton;
    CancelBtn: TButton;
    Label1: TLabel;
    E_Chapter: TEdit;
    Label2: TLabel;
    E_Shloka: TEdit;
    Label3: TLabel;
    E_Comment: TEdit;
    Label4: TLabel;
    E_Page: TEdit;
    Bevel1: TBevel;
    procedure FormCreate(Sender: TObject);
    procedure FormDestroy(Sender: TObject);
  private
  MhList:TstringList;
  function CheckChapters:boolean;
  function CheckShlokas:boolean;
  function CheckComments:boolean;
  function CheckPages:boolean;
  procedure SaveReport(AFileName:string; rChap,rShl,rComm,rPage:integer);

    { Private declarations }
  public
  ErrList:TStringList;
  Procedure CheckAll(AFileName:string);
    { Public declarations }
  end;

var
  OKBottomDlg: TOKBottomDlg;

implementation

uses
  textu;

{$R *.lfm}

{ TOKBottomDlg }

procedure TOKBottomDlg.CheckAll(AFileName:string);
var
 rChap,rShl,rComm,rPage:integer;
begin
 MhList:=TStringList.Create;
 MhList.LoadFromFile(AFileName);
 ErrList.Clear;
 rChap:=-1; rShl:=-1; rComm:=-1; rPage:=-1;
 try
  if CheckChapters then rChap:=1 else begin rChap:=0; exit; end;
  if CheckShlokas  then rShl:=1  else begin rShl:=0;  exit; end;
  if CheckComments then rComm:=1 else begin rComm:=0; exit; end;
  if CheckPages    then rPage:=1 else begin rPage:=0; exit; end;
 finally
  SaveReport(AFileName,rChap,rShl,rComm,rPage);
  MhList.Free;
 end;
end;

function TOKBottomDlg.CheckChapters:boolean;
var
 i:integer;
 S:string;
 N:integer;
 S_N:string;
begin
 N:=0;
 for i:=1 to MhList.Count do
 begin
  S:=MhList[i-1];
  if Pos(E_Chapter.Text,S)=1 then
  begin
   inc(n);
   CutNextUseDelimiter(S, ' ' );
   if Pos('(',S) <>0
    then S_N:=CutNextUseDelimiter(S, '(' )
    else S_N:=CutNextUseDelimiter(S, ' ' );
   if IntToStr(N) <> S_N then ErrList.Add(' - ������ � ��������� �����: '+MhList[i-1]);
  end;
 end;
 ErrList.Add(' - ����� ����: '+IntToStr(n));
 if ErrList.Count>1 then ErrList.Add(' - ��������� ������ � ������������� ���������.');
 Result:=ErrList.Count=1;
end;

Function TOKBottomDlg.CheckComments:boolean;
var
 i:integer;
 S:string;
 IsComment:boolean;
 N_Comm:integer;
 N_Comm_All:integer;
 N_Chapter:integer;
 N_Prev:integer;
 S_N:string;
 N_tmp,Code:integer;
 S_N_Prev:string;
 NewChapter:boolean;
 label 2;
begin
 N_Comm:=0;
 N_Comm_All:=0;
 N_Chapter:=0;
 NewChapter:=False;
 // ����� �� ������, �������� ������������, ������� ...
 for i:=1 to MhList.Count do
 begin
  S:=MhList[i-1];
  if Pos(E_Chapter.Text,S)=1 then begin inc(N_Chapter); NewChapter:=True; end;
  repeat
   IsComment:=(Pos(E_Comment.Text[1],S)>0)and (Pos(E_Comment.Text[3],S)>0);
   if not IsComment then break;
   CutNextUseDelimiter(S,E_Comment.Text[1]);
   S_N:=CutNextUseDelimiter(S,E_Comment.Text[3]);
   2:
   Val(S_N,N_tmp,Code);
   if Code=0 then
    begin
     inc(N_Comm_All);
     if N_tmp=1 then N_Comm:=1 else inc(N_Comm);
     if (N_Comm_All>1) and (N_tmp=1) then
     begin
       if not NewChapter then
       ErrList.Add(' - ������������������ ����������� '+S_N+' ����� '+S_N_Prev+ ' � ����� '+IntToStr(N_Chapter)+': '+Copy (MhList[i-1],1,60));
//       ErrList.Add(' - ������� ������������������ ����������� '+S_N+ ' � ����� '+IntToStr(N_Chapter)+': '+Copy (MhList[i-1],1,60)+'...');

//       ErrList.Add(' - ����������� '+IntTOstr(N_Chapter-1)+': '+IntTOstr(N_Prev)+' ������������');
       N_Comm:=N_tmp;//����� ���� 1
       NewChapter:=False;
     end else
      if N_Comm<>N_tmp then
      begin
       ErrList.Add(' - ������������������ ����������� '+S_N+' ����� '+S_N_Prev+ ' � ����� '+IntToStr(N_Chapter)+': '+Copy (MhList[i-1],1,60));
       N_Comm:=StrToINt(S_N);
      end;
     N_Prev:=N_tmp;
     S_N_Prev:=S_N;
    end else
    begin
     if Pos('(',S_N)>0 then begin S_N:=Copy(S_N,Pos('(',S_N)+1,4); goto 2; end;
    end;
  until False;
 end;
 ErrList.Add(' - ����� ����������� ������������ : '+IntToStr(N_Comm_All));
 Result:=True;
end;

Function TOKBottomDlg.CheckPages:boolean;
var
 i,n:integer;
 S:string;
 Diff:integer;
 N_Prev,S_N:string;
 FirstPage:boolean;
begin
 FirstPage:=True;
 n:=0;
 for i:=1 to MhList.Count do
 begin
  S:=MhList[i-1];
  if Pos(E_Page.Text[1],S)=1 then
  try
   inc(n);
   CutNextUseDelimiter(S, E_Page.Text[1] );
   S_N:=CutNextUseDelimiter(S, E_Page.Text[3] );
   if FirstPage then N_Prev:=IntToStr(StrToInt(S_N)-1);
   Diff:=StrToInt(S_N)-StrToInt(N_Prev);
   if (Diff<>1) then ErrList.Add(' - ������ � ��������� ��������: '+MhList[i-1]);
   N_Prev:=S_N;
   FirstPage:=false;
  except
   ShowMessage('������ � ������ '+IntToStr(i));
  end;
 end;
 ErrList.Add(' - ����� ������������� �������: '+IntToStr(n));
 Result:=ErrList.Count=1;
end;

Function TOKBottomDlg.CheckShlokas:boolean;
var
 i:integer;
 S:string;
 N_Shl,N_Shl_all:integer;
 S_N:string;
 Prev_N,N1,N2:integer;
 NewChapter:boolean;
 ChapterStr:string;
begin
 N_Shl_all:=0;
 for i:=1 to MhList.Count do
 try
  S:=MhList[i-1];
  if Pos(E_Chapter.Text,S)=1 then begin ChapterStr:=MhList[i-1]; NewChapter:=True; end;// �����
  if (Pos(E_Shloka.Text[1],S)=1)and ((Pos(E_Shloka.Text[3],S)<>1)) then // �����
  begin
   inc(N_Shl_all);
   CutNextUseDelimiter(S, E_Shloka.Text[1] );
   S_N:=CutNextUseDelimiter(S, E_Shloka.Text[3] );
   if pos('-',S_N)=0
    then begin N1:=StrToInt(S_N); N2:=N1; end
    else begin N1:=StrToInt(CutNextUseDelimiter(S_N,'-'));N2:=StrToInt(S_N) end;
   if NewChapter then Prev_N:=0;
   if N1-Prev_N<>1 then ErrList.Add(' - ���� � ��������� ����. '+ IntToStr(N1)+ ' ����� ������ '+IntToStr(Prev_N)+' � '+ChapterStr+': '+Copy (MhList[i-1],1,60));
   Prev_N:=N2;
   NewChapter :=False;
  end;
 Except
  ShowMessage('Error in the line '+IntTOStr(i));
 end;
 ErrList.Add(' - ����� ����: '+IntToStr(N_Shl_all));
 Result:=True;
end;

procedure TOKBottomDlg.FormCreate(Sender: TObject);
begin
 ErrList:=TStringList.Create;
 ErrList.Clear;
end;

procedure TOKBottomDlg.FormDestroy(Sender: TObject);
begin
 ErrList.Free;
end;


procedure TOKBottomDlg.SaveReport(AFileName:string; rChap,rShl,rComm,rPage:integer);
var
 J,T:TStringList;
 i:integer;
 okAll:boolean;

 function TriStr(v:integer):string;
 begin
  if v<0 then Result:='null'
  else if v>0 then Result:='true'
  else Result:='false';
 end;

 function JEsc(const s:string):string;
 var r:string;
 begin
  r:=StringReplace(s,'\','\',[rfReplaceAll]);
  r:=StringReplace(r,'"','\"',[rfReplaceAll]);
  r:=StringReplace(r,#9,' ',[rfReplaceAll]);
  Result:=AnsiToUtf8(r);
 end;

begin
 okAll:=(rChap>0)and(rShl>0)and(rComm>0)and(rPage>0);
 J:=TStringList.Create;
 T:=TStringList.Create;
 try
  J.Add('{');
  J.Add('  "input": "'+JEsc(AFileName)+'",');
  if okAll then J.Add('  "ok": true,') else J.Add('  "ok": false,');
  J.Add('  "checks": {');
  J.Add('    "chapters": '+TriStr(rChap)+',');
  J.Add('    "shlokas": '+TriStr(rShl)+',');
  J.Add('    "comments": '+TriStr(rComm)+',');
  J.Add('    "pages": '+TriStr(rPage));
  J.Add('  },');
  J.Add('  "messageCount": '+IntToStr(ErrList.Count)+',');
  J.Add('  "messages": [');
  for i:=0 to ErrList.Count-1 do
   if i<ErrList.Count-1
    then J.Add('    "'+JEsc(ErrList[i])+'",')
    else J.Add('    "'+JEsc(ErrList[i])+'"');
  J.Add('  ]');
  J.Add('}');
  J.SaveToFile(ChangeFileExt(AFileName,'_check.json'));

  T.Add('field'#9'value');
  if okAll then T.Add('ok'#9'true') else T.Add('ok'#9'false');
  T.Add('chapters'#9+TriStr(rChap));
  T.Add('shlokas'#9+TriStr(rShl));
  T.Add('comments'#9+TriStr(rComm));
  T.Add('pages'#9+TriStr(rPage));
  T.Add('messageCount'#9+IntToStr(ErrList.Count));
  for i:=0 to ErrList.Count-1 do
   T.Add('message'#9+AnsiToUtf8(StringReplace(ErrList[i],#9,' ',[rfReplaceAll])));
  T.SaveToFile(ChangeFileExt(AFileName,'_check.tsv'));
 finally
  T.Free;
  J.Free;
 end;
end;

end.

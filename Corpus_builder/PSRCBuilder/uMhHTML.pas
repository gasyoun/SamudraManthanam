unit uMhHTML;
// сделать проверку на количество закрываемых и открываемых скобок
interface
 uses classes, INIFiles;
type
TSlocaInfoRec=record
 NBook, NChapter, NSubChapter, Num1,Num2:integer;
 RusPage1,RusPage2:integer;
 bNum1Crossing,bNum2Crossing:boolean;
 S_Num:string;
end;
TSlokaRec=record
 Prevtext,Text,EndChapterText,EndBookText,UvacaText,GlavaText:widestring;
 info:TSlocaInfoRec;
 RusPage1,RusPage2:integer;
end;
TSlokaRecArr=array of TSlokaRec;
TCommentInfoRec=record
 NBook, NChapter1,NChapter2:integer;
 nShloka:string; // понадобилось только для Вьяса Бхашьи.
 Num:widestring;
 N1,N2:integer;
end;
TCommentRec=record
 Text:widestring;
 info:TCommentInfoRec;
 RusPage1,RusPage2:integer;
end;
TFootNoteRec=record
 Text:widestring;
 info:TCommentInfoRec;
 RusPage1,RusPage2:integer;
end;

TKeyWords=record
 Skazanie,Povest,Konec, Skazal,Glava, Book, Takova, CommentShortGl, TriSlokaDivision:string;
 GlavaAutoIncrement:boolean;
 ShlokaOnlyNumber:boolean;
 BookLettersCount:integer;
 CommentNumIsShlokaNum:boolean;
 RigvedaComment:Boolean; //Ex: 1a-b, 1-2
 BreakInTranslation:boolean;
 CutBookFromCitation:boolean; //удаляет номер книги из Индекса # citation_block # chapter_title
 DisableUvachaInSankrit:boolean;
 DisableUvachaInRus:boolean;
 CommentOnlyNumber:Boolean; //проверка, число в скобках или есть еще другие символы, если CommentOnlyNumber = false
 OnlyRus:boolean;
 OutputHTML:string;
 BookNameForCitation:string;
 datasrc:Integer; // номер книги для серии книг. Перечисляются в поле "meta" файла html
//title="Махабхарата I. 1. 52-55
//id="Махабхарата 1950 (I): 11
 TextForCitation:string;
 ChapterStrToClear:string;
 CommentIgnorStr:string;
 IgnoreFirstNumberInComments:boolean;
 b2Transl:boolean;
 ManyTransl:Byte;
 ThreeLevelComment:boolean;//V.10.1.
 TwoLevelCombineComment:boolean;// номер шлоки + номер комментария
 KamasutraComment:boolean;
 IgnoreSanskritError:boolean;
 Bracket1,Bracket2:string;
 PageAutoInc:byte;
 ChapterInc:integer;
 TranslationFootnotesCount:Integer;
 IsFootNotes:Boolean;
end;
TIASTSlolakaInfo=(tisi_all,tisi_first,tisi_second);
TChapterNames=array of string;
TMhHTMLBuilder = class(TObject)
  Constructor Create;
  destructor Destroy;override;
  procedure Execute (AFileName:string);
  public
  KeyWords:TKeyWords;
  private
  INIFile:TIniFile;
  HTF:textFile; // HyperTextFile
  RusList,SanskritList:TStringList;
  CommentsForOutput:TStringList;
  FootNotesForOutPut:TStringList;
//  ShlokasCountInChapters:array of integer;
  CSR_Counts,CSS_Counts:array of integer;
  SlokasArr:TSlokaRecArr;
  ManyTransSlokasArr: array [0..99] of TSlokaRecArr;
  SlokasArr2:TSlokaRecArr;
  SanskritArr:TSlokaRecArr;
  CommentsArr:array of TCommentRec;
  FootNotesArr:array of TCommentRec;
  SanskritArrSlokaNums:TStringList;
  SanskritArrSlokaTexts:array of widestring;
  ChapterNames:TChapterNames;
  ErrList:TStringList;
  Path:string;
  CurSlokaNum:integer;
  NBook, CurChapter, CurSubChapter, ChaptersCount:integer;
  S_SancritFileName:string;
  CommentSymbols:string;
  Function LoadKeyWords:boolean;
  procedure LoadPerevod (TransFileIndex:integer);
  procedure LoadPerevod2;
  procedure LoadSanskrit;
  procedure LoadComments;
  procedure LoadFootNotes;
  procedure LoadOptions;
  procedure LoadNames;
  procedure Check;
  Procedure OutPutText;
  //-------
  procedure HTMLRewrite (AFileName:string);
  procedure HTML_EndChapter;
  procedure HTML_EndBook;
//  procedure HTMLChapterCaption (ANum:integer;const ChapterCaption:widestring);
  procedure HTMLChapterCaption (IDStr:string;const ChapterCaption:widestring);
  procedure HTMLChapterNum (ANum:integer;AGlavaText:widestring);
  procedure HTMLCitationBlock; //пустая . Вызывается из HTMLRange(N1, N2, P1,P2: Integer)
  Procedure HTML_EndCitationBlock;
  procedure HTMLRange(N1,N2,P1,P2:Integer);
  procedure HTMLCloseFile;
  Procedure HTML_IAST_Text(AText:widestring;bIsUvaca:boolean);
  Procedure HTML_Rus_Text(UvacaText,AText:widestring);
  Procedure HTML_EndChapterText(const Rec:TSlokaRec);
  Procedure HTML_BeginCommentsBlock;
  Procedure HTML_EndCommentsBlock;
  Function MarkRusNames(AText:widestring):widestring;
  Procedure HTML_CommentText(ChapterNum,CommNum,RusPage1,RusPage2:integer);
  procedure HTML_FootNoteText(bInTransl:Boolean;index,RusPage1,RusPage2:integer);
// Утилиты
  Function FormatFootnoteInText (AText:widestring):widestring;
  Function FormatFootnoteInText2 (bInTransl:Boolean;AText:widestring):widestring;
  function GetSanskritShlokaText ( NBook, NChapter, NSloka:integer; Info:TIASTSlolakaInfo;var ErrStr:String):WideString;
  procedure MemoryCommentForOutput(NumCommentStr1,NumCommentStr2:widestring;CurChapterNum, Reserved:integer);
  Function IsGlavaSingInText(Atext, AGlava: string): boolean;
  Function IsShlokaNum(Atext:string):boolean;
  Procedure ExtractShlokaNums(var Atext:string;var N1,N2:integer);
  Function GetDiapasoneFromText(Atext:string;Delimiter:string;var N1,N2:integer):boolean;
  function CheckSanskrit: boolean;
  function IsFirstStringComment(S_Ansi:string; var p1,p2,p3:string): boolean;
  function MakeURLFromAbbr (AbbrText:string;TranslationID,NChapter,NShloka:Integer):widestring;
end;

const
 sRightArrow='<code>&#8594</code>';
 C39=chr(39);
 C_RusStrLabel='с. ';
 C_NoRusData='{no rus data}';
 C_NoSankritData='{no sanskrit data}';
 ResFileName='Res.txt';
 ErrFileName='Err.txt';
 InsertBlockLab1='<!-- Insert code block beginning -->';
 InsertBlockLab2='<!-- Insert code block end -->';
 CS_SancritFileName_IAST='01_Sanskrit.txt';
 CS_SancritFileName_Dev='01_Sanskrit_dev.txt';
 CS_TranslationFileName='02_Transl.txt';
 CS_TranslationFileName2='02_Transl2.txt';
 CS_CommentsFileName='03_Comments.txt';
 CS_FootNotesFileName='04_Footnotes.txt';
 CS_ResHTMLFileName='Res_html.txt';
var
  mTranslationFileNames:array [0..99] of string;
  sAbbrArr:array [0..99] of string;
  html_files:array [0..99] of string;
  S_danda1,S_danda2:widestring;
  bShowDivComment:boolean;
  bDevFileName:boolean;
  BooksCount:integer;// for file with many books
  ManyBookSign:string;
implementation

uses SysUtils, dialogs, textu , fMainForm, Forms, controls, windows, ShellApi, MyUtils;

{ TMhHTMLBuilde }

function CompareNum(List: TStringList; Index1, Index2: Integer): Integer;
var
 S1,S2:string;
 N1,N2:integer;
 Code1,Code2:integer;
begin
 S1:=List[Index1];
 S2:=List[Index2];
 if S1=S2 then begin result:=0 ; exit; end;
 val(s1,n1,Code1);
 val(s2,n2,Code2);
 if (code1<>0)or(code2<>0) then result:=0
 else
 begin
  if n1>n2 then result:=1 else result:=-1;
 end;
end;

constructor TMhHTMLBuilder.Create;
begin
 CommentsForOutput:=TStringList.Create;
 FootNotesForOutPut:=TStringList.Create;
// CommentsForOutput.Sorted:=True;
 ErrList:=TStringList.Create;
 RusList:=TStringList.Create;
// RusList.Sorted:=True;
 SanskritList:=TStringList.Create;
// SanskritList.Sorted:=True;
end;

destructor TMhHTMLBuilder.Destroy;
begin
 INIFile.Free;
 RusList.Free;
 SanskritList.Free;
 ErrList.Free;
 SanskritArrSlokaNums.Free;
 CommentsForOutput.Free;
 FootNotesForOutPut.Free;
 inherited;
end;

procedure TMhHTMLBuilder.Execute;
var
 bGoodSankrit:boolean;
 i:integer;
begin
 Path:=ExtractFilePath(AFileName);
 if not LoadKeyWords then
 begin
  if MessageDlg('Не найдел файл с ключевыми словами. Использовать ключевые слова по умолчанию?',mtConfirmation,mbOKCancel,0) <> mrOk
  then exit;
 end;
 if bDevFileName then S_SancritFileName:=CS_SancritFileName_Dev else S_SancritFileName:=CS_SancritFileName_IAST;
 bGoodSankrit:=CheckSanskrit;
 if KeyWords.IgnoreSanskritError then bGoodSankrit:=True; // Для упанишад переведенных частично и не подряд (типа Маханараяна)
 if bGoodSankrit then
 begin
   LoadSanskrit; //ok
   if KeyWords.ManyTransl>0
    then for i:=1 to KeyWords.ManyTransl do LoadPerevod (i)
    else LoadPerevod (0);
   if KeyWords.b2Transl then LoadPerevod2; {для Смирнова и Гитаговинды}
   LoadComments;
   if KeyWords.IsFootNotes then LoadFootNotes;
  // LoadNames;
   Check;
   OutPutText;
  end;
  ErrList.SaveToFile(Path+ErrFileName);
  if ErrList.Count>0 then ShellExecute(Application.Handle, 'open', PChar(Path+ErrFileName), nil, nil, SW_SHOWNORMAL);
  if bGoodSankrit then if KeyWords.OutputHTML<>'' then PutFile1ToFile2(Path+CS_ResHTMLFileName,KeyWords.OutputHTML,InsertBlockLab1,InsertBlockLab2);
end;



function TMhHTMLBuilder.FormatFootnoteInText(AText: widestring): widestring;
var
 i,j,v,code,k,Pos1, Pos2:integer;
 NumCommentStr,S_to_Replace,S_to_Find,S:widestring;
 CurChapterNum,CurSubChapterNum:integer;
 CurShlokaStr:string;
 C1,C9:widechar;
 iAdd:integer;
 CommentsCount1,CommentsCount2:integer;
 AnsiText:string;
 ErrCode:Boolean;
begin
 if KeyWords.ChapterStrToClear=''
  then  Result:=AText
  else Result:=StringReplace(Atext,KeyWords.ChapterStrToClear,'',[]);
 if KeyWords.IsFootNotes then Exit; // в этом случае используем
 if Pos (KeyWords.Bracket1,Atext)=0 then exit;      //<скобка>
 CurChapterNum:=SlokasArr[CurSlokaNum-1].info.NChapter;
 CurShlokaStr:=intToStr(SlokasArr[CurSlokaNum-1].info.Num1);
 CurSubChapterNum:=SlokasArr[CurSlokaNum-1].info.NSubChapter;
 S:=AText;
 k:=1;
 repeat
   AnsiText:=UTF8ToAnsi(AText);
   Pos1:=0;
   C1:='1';
   C9:='9';
   for i:=k to Length(AText)-1 do
    if (S[i]=KeyWords.Bracket1) and (S[i+1] in [c1..c9]) then //<скобка>
    begin
     Pos1:=i;
     break;
    end;
   if Pos1=0 then exit;
   for i:=Pos1 to Length(S){Pos1+20} do
    if S[i]=KeyWords.Bracket2 then begin Pos2:=i; break; end; //<скобка>
   S_to_Find:=Copy(S,Pos1-1,Pos2-Pos1+2); // pos-1,Pos2-Pos1+2 учитывает пробел
   NumCommentStr:=Copy(S,Pos1+1,Pos2-Pos1-1);
   if Keywords.CommentOnlyNumber then
    begin
     ErrCode:=False;
     for j:=1 to Length(NumCommentStr) do
      begin
        Val(NumCommentStr[j],v,code);
        if code>0 then begin ErrCode:=True; break; end;
      end;
     if ErrCode then begin inc(k); Continue end;
    end;
   CommentsCount1:=CommentsForOutput.Count;
   if KeyWords.TwoLevelCombineComment
   then MemoryCommentForOutput(NumCommentStr,NumCommentStr,CurChapterNum,SlokasArr[CurSlokaNum-1].info.Num1)
   else
   begin
    if Keywords.KamasutraComment
    then MemoryCommentForOutput(NumCommentStr,NumCommentStr,CurChapterNum, CurSubChapterNum) {!!!}
    else MemoryCommentForOutput(NumCommentStr,NumCommentStr,CurChapterNum, 0);
   end;
   CommentSymbols:='comment'+IntToStr(NBook)+'_';
   CommentsCount2:=CommentsForOutput.Count;
    if Keywords.KamasutraComment
    then S_to_Replace:='<a href='+C39+'#'+CommentSymbols+ IntToStr(CurSubChapterNum)+'_'+NumCommentStr
    else S_to_Replace:='<a href='+C39+'#'+CommentSymbols+  IntToStr(CurChapterNum)+'_'+NumCommentStr;
   if KeyWords.TwoLevelCombineComment then S_to_Replace:=S_to_Replace+'_'+CurShlokaStr;
   S_to_Replace:=S_to_Replace+C39+' class='+C39+'comment_sub'+C39+'>';
   if KeyWords.KamasutraComment then
   begin
    S_to_Replace:=S_to_Replace+ ' '+KeyWords.Bracket1+ NumCommentStr+KeyWords.Bracket2+'</a>';
    S:=Atext;
    if CommentsCount2-CommentsCount1>0 then begin Atext:=StringReplace(Atext,S_to_Find,S_to_Replace,[]); iAdd:=Length(S_to_Replace); end else iAdd:=0;
    k:=Pos1+iAdd+Length(NumCommentStr)+2;
   end  else
   begin
    S_to_Replace:=S_to_Replace+'<sup><small>'+NumCommentStr+'</small></sup></a>';
    if CommentsCount2-CommentsCount1>0
     then Atext:=StringReplace(Atext,S_to_Find,S_to_Replace,[])
     else
      begin
//       ShowMessage('Ошибка добавления комментария '+UTF8ToAnsi(NumCommentStr));
       break
      end;
    S:=Atext;
    k:=Pos(S_to_Replace,S)+Length(S_to_Replace)-1;;
   end;
   Result:=AText;
 until False;
 result:=Atext;
end;

procedure TMhHTMLBuilder.HTMLChapterCaption(IDStr:string;const ChapterCaption:widestring);
begin
//<div class="chapter_title" id="chapter_1С">Сказание о жизни в лесах<br></div>
// write(HTF, '<div class="chapter_title" id="chapter_');
 write(HTF, '    <div class="chapter_title" id="');
 Write(HTF, IDStr,'C">'); // C=Caption
 Write(HTF, FormatFootnoteInText(ChapterCaption));
 Writeln(HTF, '<br></div>');
end;

procedure TMhHTMLBuilder.HTMLChapterNum (ANum:integer;AGlavaText:widestring);
begin
// write(HTF, '<div class="chapter_title" id="chapter_');
 Writeln (HTF, '  <div class="chapter">');
 write(HTF, '    <div class="chapter_title" id="');
 if not KeyWords.CutBookFromCitation then
 Write(HTF, IntToStr(NBook)+'.'); {!!!}
 Write(HTF, IntToStr(Anum+KeyWords.ChapterInc),'">'); {!!!}
 Write(HTF, FormatFootnoteInText(AGlavaText));
{ Write(HTF, AnsiToUTF8('>Глава '));
 Write(HTF, IntToStr(Anum));}
 Writeln(HTF, '</div>');
end;

procedure TMhHTMLBuilder.HTMLCloseFile;
begin
 CloseFile (HTF);
end;

procedure TMhHTMLBuilder.HTMLRange(N1, N2, P1,P2: Integer);
var
 Citation_Text1:string;
 Citation_block_Text_ID:string;
 Citation_Text2:string;
 BookNameForCitation:string; // c годом, например "Рамаяна 2006"
 TextForCitation:string;
(*
Надо:
1) (см.: Рамаяна I. 13. 12)
2) Рамаяна 2006: 51
То есть вместо
<div class="range" title="Рамаяна I.25.14 с. 93">(14)</div>
сделать
<div class="range" title="(см.: Рамаяна I. 13. 12)" id="(Рамаяна 2006: 51)">(14)</div>
Для примечаний:
(Рамаяна 2006: 51)
*)
begin
//<div class="range">(1—7)</div>
//<div class="chapter_content">
 BookNameForCitation:=KeyWords.BookNameForCitation;
 TextForCitation:=KeyWords.TextForCitation;
// S:=BookNameForCitation;
// BookName:=CutNextUseDelimiter(S, ' ');
 Citation_Text1:=TextForCitation;
 if not KeyWords.CutBookFromCitation then Citation_Text1 := Citation_Text1+' '+ArabicToRoman(NBook)+'.';
 Citation_Text1:=Citation_Text1+' '+IntToStr(CurChapter+KeyWords.ChapterInc)+'. '+IntToStr(N1);
 Citation_block_Text_ID:='';
 if not KeyWords.CutBookFromCitation then Citation_block_Text_ID:=IntToStr(NBook)+'.';
 Citation_block_Text_ID:=Citation_block_Text_ID+IntToStr(CurChapter+KeyWords.ChapterInc)+'.'+IntToStr(N1);{новое!!!}
 if N2<>N1 then Citation_Text1:=Citation_Text1+'-'+IntTostr(N2);
// Citation_Text2:=''+BookNameForCitation+': '+IntTostr(P1);
 Citation_Text2:=''+IntTostr(P1);
 if P1<>P2 then Citation_Text2:=Citation_Text2+'-'+IntTostr(P2);
 Citation_Text2:=Citation_Text2+'';
 Writeln(HTF, '    <div class="citation_block"'+' id="'+Citation_block_Text_ID+'">');
 Write(HTF, '      <div class="range" ');
 Write(HTF, 'title="', AnsiToUTF8(Citation_Text1)+'" ');
// Write(HTF, 'id="', AnsiToUTF8(Citation_Text2)+'"');
 Write(HTF, 'data-src="', AnsiToUTF8(IntTostr(KeyWords.datasrc))+'" ');
 Write(HTF, 'data-page="', AnsiToUTF8(Citation_Text2)+'"');
 Write(HTF, '>');

// Write(HTF,AnsiToUTF8(Citation_Text1)); // выдача полного номера для Архипова
 if not KeyWords.OnlyRus then Write(HTF,'', IntTostr(N1));
 if N2<>N1 then Write(HTF, '-',IntTostr(N2));
 if bShowDivComment then Writeln(HTF, '<!-- end of range block -->');
 Writeln(HTF, '</div>');
// Writeln(HTF, '<div class="chapter_content">');
end;

procedure TMhHTMLBuilder.HTMLRewrite(AFileName: string);
begin
 AssignFile(HTF,AFileName);
 rewrite (HTF);
// Writeln (HTF, '<div class="chapter_splitter"></div>');
 Writeln (HTF, '<div class="book">');
 Writeln (HTF, '  <div class="book_title">','','</div>');
end;


procedure TMhHTMLBuilder.HTML_BeginCommentsBlock;
begin
 Writeln(HTF, '      <div class="comments">');
end;

procedure TMhHTMLBuilder.HTML_EndCommentsBlock;
begin
 if bShowDivComment then Writeln(HTF, '<!-- end of comment_block-->');
 Writeln(HTF, '      </div>');
// Writeln(HTF, '<div class="clear"></div>');
end;

procedure TMhHTMLBuilder.HTML_IAST_Text(AText: widestring;
  bIsUvaca: boolean);
var
 UvacaStr:widestring;
begin
 //<div class="chapter_block iast">
// <span class="iast_author">
 Write(HTF, '      <div class="chapter_block iast">');
 if bIsUvaca then
 begin
  Write (HTF, '<span class="iast_author">');
  UvacaStr:=UTF8CutNextUseDelimiterNoTrim(AText,'<br>');
  Write(HTF,UvacaStr,'<br>');
  Write(HTF,'</span>');
 end;
 if not KeyWords.OnlyRus then Write(HTF,Atext);
 Writeln(HTF, '</div>');
end;

procedure TMhHTMLBuilder.HTML_EndChapterText(const Rec:TSlokaRec);
var
 EndChapterTextRus,
 EndBookTextRus,EndChapterTextSanskrit: widestring;
 ErrStr:string;
begin
 EndChapterTextRus:=Rec.EndChapterText;
 EndBookTextRus:=Rec.EndBookText;
 EndChapterTextSanskrit:='';
 if EndChapterTextRus<>''
  then EndChapterTextSanskrit:=GetSanskritShlokaText(Rec.info.NBook,Rec.info.NChapter,-1,tisi_all,ErrStr);
 //-------------------------------
 if (EndChapterTextSanskrit<>'')and(EndChapterTextSanskrit<>C_NoSankritData) then
 begin
  write(HTF, '    <span class="endchapter_sanskrit">');
  Write(HTF, FormatFootnoteInText(EndChapterTextSanskrit));
  Writeln(HTF, '<br></span>');
 end;
 //-------------------------------
 if EndChapterTextRus<>'' then
 begin
  write(HTF, '    <span class="endchapter">');
  Write(HTF, FormatFootnoteInText(EndChapterTextRus));
  Writeln(HTF, '<br></span>');
 end;
 //-------------------------------
 if EndBookTextRus<>'' then
 begin
  write(HTF, '  <span class="endbook">');
  Write(HTF, FormatFootnoteInText(EndBookTextRus));
  Writeln(HTF, '<br></span>');
 end;
//-----------------------------------
end;

procedure TMhHTMLBuilder.HTML_Rus_Text(UvacaText, AText: widestring);
var
  RusText:WideString;
begin
 //<div class="chapter_block translation">
 //<span class="translation_author">
 if KeyWords.OnlyRus
 then Write(HTF, '      <div class="chapter_block translation2">')
 else Write(HTF, '      <div class="chapter_block translation">');
 if UvacaText<>'' then
 begin
  Write(HTF, '        <span class="translation_author">');
  Write(HTF,FormatFootnoteInText (UvacaText),'<br>');
  Write(HTF,'</span>');
 end;
 if not KeyWords.IsFootNotes
  then RusText:=FormatFootnoteInText (Atext)
  else RusText:=FormatFootnoteInText2 (True,Atext);
 Write(HTF,RusText);
// Writeln(HTF,Atext);
 if bShowDivComment then Writeln(HTF, '<!-- end of chapter_block translation -->');
 Writeln(HTF, '</div>');
 { перенес после комментариев
 if bShowDivComment then Writeln(HTF, '<!-- end of citation_block -->');
 Writeln(HTF, '    </div>');}
end;

procedure TMhHTMLBuilder.LoadComments;
var
 nLine:integer;
 FileName:string;
 F,F2:textFile;
 S_W,S_N, S_Nm:widestring;
 S,S_Ansi,S_Ansi0:string;
 InfoRec:TCommentInfoRec;
 i,j, ErrCode:integer;
 bPrevStrIsPageNum,bPerenos:boolean;
 CurChapter, RusPage:integer;
 CurShloka:integer;
 bComment_After_Chapter:boolean; // комментарий без номера, который нужно вставить после загаловка главы
 bFirstStringOfComment:boolean;
 p1,p2,p3:string;
// PrevNum:string;
begin
 FileName:=Path+CS_CommentsFileName;
 AssignFile(F,FileName);
 Reset(F);
 AssignFile(F2,ChangeFileExt(FileName,'_'+ErrFileName));
 rewrite(F2);
 readln(F);
 InfoRec.NBook:=NBook;
 InfoRec.NChapter1:=1;
 if KeyWords.TwoLevelCombineComment or KeyWords.ThreeLevelComment then InfoRec.NChapter2:=1 else InfoRec.NChapter2:=ChaptersCount;
 i:=0;
 CurChapter:=0;
 bComment_After_Chapter:=false;
 nLine:=0;
 repeat
  readln(F,S_w);
  inc (nLine);
  Form1.StatusBar1.Panels[0].Text:='Load comments line - '+ IntToStr(nLine);
  Form1.StatusBar1.Refresh;
  S_Ansi:=UTF8ToAnsi(S_w);
  S_Ansi0:=S_Ansi;
  bFirstStringOfComment:=IsFirstStringComment(S_Ansi,p1,p2,p3);
  if KeyWords.ThreeLevelComment and bFirstStringOfComment then CurChapter:=StrToInt(P2);
  if KeyWords.TwoLevelCombineComment and bFirstStringOfComment then CurShloka:=StrToInt(p1);
//  if KeyWords.TwoLevelCombineComment and KeyWords.KamasutraComment and bFirstStringOfComment then begin CurChapter:=StrToInt(P1); CurShloka:=StrToInt(p2) end;
  if bFirstStringOfComment then bComment_After_Chapter :=false;
  try
  if IsGlavaSingInText(S_Ansi,KeyWords.Glava) then  // это скорее для Рамаяны
  begin
   if KeyWords.GlavaAutoIncrement
    then begin inc(CurChapter); end
    else
     begin
      CutNextUseDelimiter(S_Ansi,' ');
      CurChapter:=StrToInt(CutNextUseDelimiter(S_Ansi,' '));
//      GlavaText:=S_W;
     end;
   bComment_After_Chapter:=True;
   InfoRec.NChapter1:=CurChapter;
   InfoRec.NChapter2:=CurChapter;
  end else
//  if Pos(KeyWords.Skazanie,S_Ansi)=1 then
  if Pos(AnsiLowerCase(KeyWords.Skazanie),AnsiLowerCase(S_Ansi))=1 then
  begin // вырезаем диапазон глав
//   PrevNum:='';
   CutNextUseDelimiter(S_Ansi,KeyWords.CommentShortGl);
   CutNextUseDelimiter(S_Ansi,' ');
   GetDiapasoneFromText(S_Ansi,')',InfoRec.NChapter1,InfoRec.NChapter2);
  end else
  if bComment_After_Chapter then
  begin
   inc(i); // номер комментария
   SetLength(CommentsArr,i);
   InfoRec.Num:='0';
   CommentsArr[i-1].Text:=s_w;
   CommentsArr[i-1].RusPage1:=RusPage;
   CommentsArr[i-1].RusPage2:=RusPage;
   CommentsArr[i-1].info:=InfoRec;
   bComment_After_Chapter:=false;
  end else
  if bFirstStringOfComment then {New!!!}
  begin
   inc(i); // номер комментария
   SetLength(CommentsArr,i);
   S_N:=UTF8CutNextUseDelimiterNoTrim(S_w, ' ');
    if S_N[Length(S_N)]='.'
     then S_N:=Copy(S_N,1, Pos('.',S_N)-1);
//     then SetLength(S_N,Length(S_N)-1);
   if KeyWords.ThreeLevelComment then
    begin
     InfoRec.NChapter2:=StrToInt(P2);
     InfoRec.NChapter1:=InfoRec.NChapter2;
     InfoRec.Num:=P3
    end else
   if KeyWords.TwoLevelCombineComment then
    begin
     InfoRec.NChapter2:=CurChapter;
     InfoRec.NChapter1:=InfoRec.NChapter2;
     InfoRec.nShloka:=p1;
     InfoRec.Num:=P2;
    end else InfoRec.Num:=S_N;
   CommentsArr[i-1].Text:=s_w;
   CommentsArr[i-1].RusPage1:=RusPage;
   CommentsArr[i-1].RusPage2:=RusPage;
   CommentsArr[i-1].info:=InfoRec;
  end else
  if (S_Ansi[1]='-')and(S_Ansi[2] in ['1'..'9']) then // номер страницы
  begin // пропускаем строчку
    CutNextUseDelimiter(S_Ansi,'-');
    RusPage:=StrToInt(CutNextUseDelimiter(S_Ansi,'-'))+KeyWords.PageAutoInc;
    bPrevStrIsPageNum:=True;
  end else
  if (KeyWords.CommentIgnorStr<>'') and (Pos(KeyWords.CommentIgnorStr,S_Ansi)=1) then
   begin
     Writeln (F2,'Ignore',#9,S_Ansi);
   end else // +text к предыдущей строке но с разными условиями.
  begin
   if i<>0 then bPerenos:=CommentsArr[i-1].Text[length(CommentsArr[i-1].Text)]='-' else bPerenos:=False;
   //в любом случае добавляем к предыдущему.
   if not bPrevStrIsPageNum then
    begin
     CommentsArr[i-1].Text:=Concat(CommentsArr[i-1].Text,'<br>',S_w);
     Writeln (F2,'+<br>+Text'#9,S_w);
    end else //bPrevStrIsPageNum
    begin
     if bPerenos then
      begin
       SetLength(CommentsArr[i-1].Text, Length(CommentsArr[i-1].Text)-1);
       CommentsArr[i-1].Text:=Concat(CommentsArr[i-1].Text,S_w);
       Writeln (F2,'<-Perenos'#9,S_w);
      end else // not bPerenos
      if i=0 then  //Тоже Comment0
      begin
        inc(i); // номер комментария
        SetLength(CommentsArr,i);
        InfoRec.Num:='0';
        CommentsArr[i-1].Text:=s_w;
        CommentsArr[i-1].RusPage1:=RusPage;
        CommentsArr[i-1].RusPage2:=RusPage;
        CommentsArr[i-1].info:=InfoRec;
        bComment_After_Chapter:=false;
     end
      else
      begin
       if CommentsArr[i-1].Text[length(CommentsArr[i-1].Text)]<>' ' then CommentsArr[i-1].Text:=Concat(CommentsArr[i-1].Text,' ');
       CommentsArr[i-1].Text:=Concat(CommentsArr[i-1].Text,'<br>'+S_w);
       Writeln (F2,'+[space]+Text'#9,S_w);
      end;
    end;
   if length(CommentsArr)>0 then CommentsArr[i-1].RusPage2:=RusPage;
   bPrevStrIsPageNum:=False;
  end;
  except
    ShowMessage('Error in the comments: '+S_Ansi0);
  end;
 until EOF(F);
 CloseFile(F);
 CloseFile(F2);

end;

function TMhHTMLBuilder.LoadKeyWords: boolean;
var
 i:integer;
begin
 Result:=FileExists(Path+'config.ini');
 INIFile:=TINIFile.Create(Path+'config.ini');
 KeyWords.Skazanie:=INIFile.ReadString('Common','Skazanie', 'СКАЗАНИЕ');
 KeyWords.Povest:=INIFile.ReadString('Common','Povest', 'ПОВЕСТЬ');
// KeyWords.PodGlava:=INIFile.ReadString('Common','PodGlava', '');
 KeyWords.Konec:=INIFile.ReadString('Common','Konec', 'КОНЕЦ');
 KeyWords.Skazal:=INIFile.ReadString('Common','Skazal', 'сказал');
 KeyWords.Glava:=INIFile.ReadString('Common','Glava', 'Глава');
 KeyWords.Book:=INIFile.ReadString('Common','Book', 'Книга');
 KeyWords.Takova:=INIFile.ReadString('Common','Takova', 'Такова в');
 KeyWords.OutputHTML:=INIFile.ReadString('Common','OutputHTML', '');
 KeyWords.BookNameForCitation:=INIFile.ReadString('Common','BookNameForCitation', '');
 KeyWords.datasrc:=INIFile.ReadInteger('Common','datasrc', 1);
 S:=KeyWords.BookNameForCitation;
 KeyWords.TextForCitation:=INIFile.ReadString('Common','TextForCitation', CutNextUseDelimiter(S, ' '));
 KeyWords.ChapterStrToClear:=INIFile.ReadString('Common','ChapterStrToClear', '');
 KeyWords.CommentIgnorStr:=INIFile.ReadString('Common','CommentIgnorStr', '');
 KeyWords.IgnoreFirstNumberInComments:=INIFile.ReadBool('Common','IgnoreFirstNumberInComments',False);
 KeyWords.b2Transl:=INIFile.ReadBool('Common','2Translations',False);
 KeyWords.ManyTransl:=INIFile.ReadInteger('Common','ManyTransl',0);
 KeyWords.ThreeLevelComment:=INIFile.ReadBool('Common','ThreeLevelComment',False);
 KeyWords.TwoLevelCombineComment:=INIFile.ReadBool('Common','TwoLevelCombineComment',False);
 KeyWords.KamasutraComment:=INIFile.ReadBool('Common','KamasutraComment',False);
 KeyWords.IgnoreSanskritError:=INIFile.ReadBool('Common','IgnoreSanskritError',False);
 KeyWords.CommentShortGl:=INIFile.ReadString('Common','CommentShortGl', '(гл');
 KeyWords.TriSlokaDivision:=INIFile.ReadString('Common','TriSlokaDivision', '1');
 KeyWords.GlavaAutoIncrement:=INIFile.ReadBool('Common','GlavaAutoIncrement', False);
 KeyWords.ShlokaOnlyNumber:=INIFile.ReadBool('Common','ShlokaOnlyNumber', False);
 KeyWords.CommentNumIsShlokaNum:=INIFile.ReadBool('Common','CommentNumIsShlokaNum', False);
 KeyWords.RigvedaComment:=INIFile.ReadBool('Common','RigvedaComment', False);
 KeyWords.BreakInTranslation:=INIFile.ReadBool('Common','BreakInTranslation', False);
 KeyWords.CutBookFromCitation:=INIFile.ReadBool('Common','CutBookFromCitation', False);
 KeyWords.DisableUvachaInSankrit:=INIFile.ReadBool('Common','DisableUvachaInSankrit', False);
 KeyWords.DisableUvachaInRus:=INIFile.ReadBool('Common','DisableUvachaInRus', False);
 KeyWords.CommentOnlyNumber:=INIFile.ReadBool('Common','CommentOnlyNumber', True);
 KeyWords.OnlyRus:=INIFile.ReadBool('Common','OnlyRus', False);
 KeyWords.IsFootNotes:=INIFile.ReadBool('Common','IsFootNotes', False);
 KeyWords.BookLettersCount:=INIFile.ReadInteger('Common','BookLettersCount', 2);
 KeyWords.PageAutoInc:=INIFile.ReadInteger('Common','PageAutoInc', 0);
 KeyWords.ChapterInc :=INIFile.ReadInteger('Common','ChapterInc', 0);
 KeyWords.TranslationFootnotesCount :=INIFile.ReadInteger('Common','TranslationFootnotesCount', 0);
 KeyWords.Bracket1:=INIFile.ReadString('Common','Bracket1', '(');
 KeyWords.Bracket2:=INIFile.ReadString('Common','Bracket2', ')');
 for i:=1 to KeyWords.ManyTransl do mTranslationFileNames[i-1]:=INIFile.ReadString('ManyTransl',IntToStr(i),'');
 for i:=1 to KeyWords.ManyTransl do sAbbrArr[i-1]:=INIFile.ReadString('Abbreviations',IntToStr(i),'');
 for i:=1 to KeyWords.ManyTransl do html_files[i-1]:=INIFile.ReadString('html',IntToStr(i),'');
end;

Function TMhHTMLBuilder.CheckSanskrit:boolean;
var
 S_N,S_Ansi,FileName:string;
 F:textFile;
 S_W,S_W0:widestring;
 i:integer;
 N1,N2,N3:integer;
 P1,P2,P3:integer;
begin
 ErrList.Clear;
 ErrList.Add('Проверка шлок на санскрите.');
 Result:=True;
 FileName:=Path+S_SancritFileName;
 AssignFile(F,FileName);
 SetLength(SanskritArr,0);
 SanskritArrSlokaNums:=TStringList.Create;
 Setlength(SanskritArrSlokaTexts,0);
 Reset(F);
 i:=0;
 repeat
  readln(F,S_W);
  inc(i);
  S_Ansi:=UTF8CutNextUseDelimiterNoTrim(S_W,#9);
  S_N:=S_Ansi;
  try
   N1:=StrToInt(CutNextUseDelimiterNoTrim(S_Ansi,'.'));
   N2:=StrToInt(CutNextUseDelimiterNoTrim(S_Ansi,'.'));
   N3:=StrToInt(CutNextUseDelimiterNoTrim(S_Ansi,#9));
  except
   ErrList.Add('строка '+IntToStr(i)+': '+'ошибка преобразования номера шлоки.');
  end;
  if i>1 then // сравнение с предыдущим номером
  begin
   if P1<>N1 then ErrList.Add('строка '+IntToStr(i)+': '+'неправильный номер книги.');
   if N2-P2<0 then ErrList.Add('строка '+IntToStr(i)+': '+'уменьшение номера главы.');
   if Abs(P2-N2)>1 then ErrList.Add('строка '+IntToStr(i)+': '+'скачек номера главы:'+IntTOstr(N2)+' после' +IntTOstr(P2));
   if (N3<>1)and (N3<>-1)and(N3-P3<0) then ErrList.Add('строка '+IntToStr(i)+': '+'непоследовательный номер шлоки.');
//   if (N3-P3<0)and (N2-P2=0)and(P3<>-1) then ErrList.Add('строка '+IntToStr(i)+': '+'непоследовательный номер шлоки.');
   if (P3=-1)and(N3<>1)and(N1-P1<>1) then ErrList.Add('строка '+IntToStr(i)+': '+'нет первого номера шлоки после последнего предыдущей главы.');
  end;
 P1:=N1;P2:=N2;P3:=N3;
 Until EOF(F);
 if ErrList.Count=1 then ErrList[0]:=ErrList[0] + ' Ошибок не найдено!';
 Result:=ErrList.Count=1;
 CloseFile(F);
end;
procedure TMhHTMLBuilder.LoadSanskrit;
var
 FileName:string;
 F:textFile;
 S_W,S_W0:widestring;
 S:string;
 i,j:integer;
 PrevNum:string;
 Status: TMemoryStatus;
begin
 Status.dwLength := sizeof(TMemoryStatus);
 FileName:=Path+S_SancritFileName;
 AssignFile(F,FileName);
 SetLength(SanskritArr,0);
 SanskritArrSlokaNums:=TStringList.Create;
 Setlength(SanskritArrSlokaTexts,0);
 Reset(F);
 i:=0;j:=0;
 PrevNum:='';
 repeat
  readln(F,S_w);
  inc(j);
  S_W0:=S_W;
  S:=UTF8ToAnsi(UTF8CutNextUseDelimiterNoTrim(S_W0,#9));
  SanskritArrSlokaNums.Add(S);
  NBook:=StrToint(CutNextUseDelimiter(S,'.'));
  Setlength(SanskritArrSlokaTexts,j);
  SanskritArrSlokaTexts[j-1]:=S_W0;
  S:=UTF8ToAnsi(UTF8CutNextUseDelimiterNoTrim(S_W,#9));
  GlobalMemoryStatus(Status);
  Form1.StatusBar1.Panels[1].Text:='Load '+S +'; Total Ram: ' + IntToStr(Status.dwAvailVirtual div 1024417) + ' Mb';
  Application.ProcessMessages;
  if PrevNum<>S then begin inc(i); PrevNum:=S end;
  SetLength(SanskritArr,i);
  SanskritArr[i-1].Info.S_Num:=S;
  SanskritArr[i-1].Info.NBook:=StrToint(CutNextUseDelimiter(S,'.'));
  SanskritArr[i-1].Info.NChapter:=StrToint(CutNextUseDelimiter(S,'.'));
  ChaptersCount:=SanskritArr[i-1].Info.NChapter;
  SanskritArr[i-1].Info.Num1:=StrToint(S);
  SanskritArr[i-1].Info.Num2:=SanskritArr[i-1].Info.Num1;
  SetLength(CSS_Counts, SanskritArr[i-1].Info.NChapter);
  if CSS_Counts[SanskritArr[i-1].Info.NChapter-1]<SanskritArr[i-1].Info.Num1
   then CSS_Counts[SanskritArr[i-1].Info.NChapter-1]:=SanskritArr[i-1].Info.Num1;
   ; // кол-во шлок в разделе
  SanskritArr[i-1].Info.Num2:=SanskritArr[i-1].Info.Num1;
 until EOF(F);
 CloseFile(F);
end;

procedure TMhHTMLBuilder.LoadNames;
var
 FileName:string;
 F:textFile;
 S_W:widestring;
 i:integer;
begin
 FileName:=Path+'S&M.txt';
 AssignFile(F,FileName);
 Reset(F);
 repeat
  readln(F,S_w);
//  SanskritList.Add(UTF8CutNextUseDelimiterNoTrim(S_w,#9));
  RusList.Add(S_w);
 until EOF(F);
 RusList.SaveToFile(Path+'S&M2.txt');
 CloseFile(F);
end;

procedure TMhHTMLBuilder.LoadOptions;
begin

end;

procedure TMhHTMLBuilder.LoadPerevod (TransFileIndex:integer);
var
 FileName:string;
 F,F2:textFile;
 S_W:widestring;
 S,S_Ansi,S_Ansi0:string;
 GlavaText,UvacaText,PrevSlokaText:widestring;
 i,j:integer;
 InfoRec:TSlocaInfoRec;
 CurSkazanie,CurChapter:integer;
 b_perenos:boolean;
 RusPage:integer;
 Paragraph_Num:integer;
begin
 if TransFileIndex=0 then FileName:=Path+CS_TranslationFileName
 else
  begin
   FileName:=Path+mTranslationFileNames [TransFileIndex-1];
   SlokasArr:=ManyTransSlokasArr[TransFileIndex-1];
  end;
 AssignFile(F,FileName);
 Reset(F);
 AssignFile(F2,ChangeFileExt(FileName,'_err.txt'));
 CurSkazanie:=INIFile.ReadInteger('BookSubchapters','Book'+IntToStr(NBook)+'_First_Subchapter',2);
 dec(CurSkazanie);
 Inforec.NBook:=NBook;
 CurChapter:=0;
 rewrite(F2);
 i:=0;
 Paragraph_Num:=0;
 repeat
  readln(F,S_w);
  if S_w='' then continue;
  S_Ansi:=UTF8ToAnsi(S_w);
  S_Ansi0:=S_Ansi;
  try
  if IsShlokaNum (S_Ansi) then
  begin
     inc(i);
     inc(Paragraph_Num);
     Form1.StatusBar1.Panels[0].Text:='Loading line '+IntToStr(i);
     Form1.StatusBar1.Refresh;
     SetLength(SlokasArr,Length(SlokasArr)+1);
     SlokasArr[i-1].GlavaText:=GlavaText;
     GlavaText:='';
     SlokasArr[i-1].RusPage1:=RusPage;
     SlokasArr[i-1].RusPage2:=RusPage;
     Inforec.NChapter:=CurChapter;
     Inforec.NSubChapter:=CurSkazanie;
     SetLength(CSR_Counts, Inforec.NChapter);
     if KeyWords.OnlyRus then begin Inforec.Num1:=Paragraph_Num; Inforec.Num2:=Paragraph_Num  end
     else ExtractShlokaNums(S_Ansi,Inforec.Num1,Inforec.Num2);
     CSR_Counts[Inforec.NChapter-1]:=Inforec.Num2; // кол-во шлок в разделе
//     if Inforec.NChapter>0 then CSR_Counts[Inforec.NChapter-1]:=Inforec.Num2; // кол-во шлок в разделе
     //--------
     UTF8CutNextUseDelimiterNoTrim(S_w,' ');
     SlokasArr[i-1].Text:=S_w;
     if PrevSlokaText<>'' then
       begin
        SlokasArr[i-1].Prevtext:=PrevSlokaText;
        PrevSlokaText:='';
       end;
     if UvacaText<>'' then
         begin
          SlokasArr[i-1].UvacaText:=UvacaText;
          UvacaText:='';
         end;
     SlokasArr[i-1].info:=Inforec;
{    b_perenos:=S_Ansi[Length(S_Ansi)]='-';
    if b_perenos then
      SetLength(SlokasArr[i-1].Text, Length(SlokasArr[i-1].Text)-1);}
  end else
  if S_Ansi[1]='-' then
  begin
   CutNextUseDelimiter(S_Ansi,'-');
   RusPage:=StrToInt(CutNextUseDelimiter(S_Ansi,'-'))+KeyWords.PageAutoInc;
   b_perenos:=True;
  end else
  if Pos(KeyWords.Skazanie,S_Ansi)=1 then
  begin
   inc(CurSkazanie);
   PrevSlokaText:=S_W;
  end else
  if Pos(KeyWords.Povest,S_Ansi)=1 then
  begin
   PrevSlokaText:=S_W;
  end else
  if AnsiCompareStr(KeyWords.Konec,Copy (S_Ansi,1,Length(KeyWords.Konec)))=0 then
  begin
   SlokasArr[i-1].EndBookText:=Concat(SlokasArr[i-1].EndBookText,'<br>',S_W);
  end else
  // Uvaca text
  if (Pos(KeyWords.Skazal,S_Ansi)in [1..30])and (Pos(':',S_Ansi)in [1..40])and (Length(S_Ansi)<50) and (S_Ansi[1]<>' ') then
  begin
   UvacaText:=S_w;
   Writeln (F2,'Uvaca: ',#9,S_w);
  end
  else
  if IsGlavaSingInText(S_Ansi,KeyWords.Glava) then
  begin
   Paragraph_Num:=0; // для статей
   if KeyWords.GlavaAutoIncrement then
    begin
     inc(CurChapter);
     GlavaText:=S_W;
    end
    else
   begin
    CutNextUseDelimiter(S_Ansi,' ');
    CurChapter:=StrToInt(CutNextUseDelimiter(S_Ansi,' '));
    GlavaText:=S_W;
   end 
  end else
  if Pos(KeyWords.Takova,S_Ansi)=1 then
  begin
   SlokasArr[i-1].EndChapterText:=S_W;
  end else
  begin
   if b_perenos then
   begin
    if (Length(SlokasArr[i-1].Text)>0)and(UTF8ToAnsi(SlokasArr[i-1].Text[Length(SlokasArr[i-1].Text)])='-') then
    begin
      SetLength(SlokasArr[i-1].Text, Length(SlokasArr[i-1].Text)-1);
      SlokasArr[i-1].Text:=Concat(SlokasArr[i-1].Text,s_w);
      if length(SlokasArr)>0 then SlokasArr[i-1].RusPage2:=RusPage;
    end
     else
    begin
      if KeyWords.BreakInTranslation
      then
       begin
        if S_w[1]<>' '
         then SlokasArr[i-1].Text:=Concat(SlokasArr[i-1].Text,'<br>',s_w)
         else SlokasArr[i-1].Text:=Concat(SlokasArr[i-1].Text,s_w)
       end
      else
        begin
        if S_w[1]<>' '
         then SlokasArr[i-1].Text:=Concat(SlokasArr[i-1].Text,' ',s_w)
         else SlokasArr[i-1].Text:=Concat(SlokasArr[i-1].Text,s_w);
        end;
      if length(SlokasArr)>0 then SlokasArr[i-1].RusPage2:=RusPage;
    end
   end else
   begin
    SlokasArr[i-1].Text:=Concat(SlokasArr[i-1].Text,'<br>',s_w);
   if length(SlokasArr)>0 then SlokasArr[i-1].RusPage2:=RusPage;
   end;
   Writeln (F2,'Other: ',#9,S_w);
  end;
  except
   Writeln (F2,'Error in the line -',i,#9,S_Ansi0);
   ShowMessage('Error in the translation: '+S_Ansi0);
   break;
  end;
 until EOF(F);
 ManyTransSlokasArr[TransFileIndex-1]:=SlokasArr;
 CloseFile(F);
 CloseFile(F2);
end;

procedure TMhHTMLBuilder.LoadPerevod2;
var
 FileName:string;
 F,F2:textFile;
 S_W:widestring;
 S,S_Ansi,S_Ansi0:string;
 GlavaText,UvacaText,PrevSlokaText:widestring;
 i,j:integer;
 InfoRec:TSlocaInfoRec;
 CurChapter:integer;
 b_perenos:boolean;
 RusPage:integer;
begin
 FileName:=Path+CS_TranslationFileName2;
 AssignFile(F,FileName);
 Reset(F);
 AssignFile(F2,ChangeFileExt(FileName,'_err.txt'));
 Inforec.NBook:=NBook;
 CurChapter:=0;
 rewrite(F2);
 i:=0;
 repeat
  readln(F,S_w);
  S_Ansi:=UTF8ToAnsi(S_w);
  S_Ansi0:=S_Ansi;
  try
  if IsShlokaNum (S_Ansi) then
  begin
     inc(i);
     Form1.StatusBar1.Panels[0].Text:='Loading line '+IntToStr(i);
     Form1.StatusBar1.Refresh;
     SetLength(SlokasArr2,Length(SlokasArr2)+1);
     SlokasArr2[i-1].GlavaText:=GlavaText;
     GlavaText:='';
     SlokasArr2[i-1].RusPage1:=RusPage;
     SlokasArr2[i-1].RusPage2:=RusPage;
     Inforec.NChapter:=CurChapter;
     SetLength(CSR_Counts, Inforec.NChapter);
     ExtractShlokaNums(S_Ansi,Inforec.Num1,Inforec.Num2);
     CSR_Counts[Inforec.NChapter-1]:=Inforec.Num2; // кол-во шлок в разделе
     //--------
     UTF8CutNextUseDelimiterNoTrim(S_w,' ');
     SlokasArr2[i-1].Text:=S_w;
     if PrevSlokaText<>'' then
       begin
        SlokasArr2[i-1].Prevtext:=PrevSlokaText;
        PrevSlokaText:='';
       end;
     if UvacaText<>'' then
         begin
          SlokasArr2[i-1].UvacaText:=UvacaText;
          UvacaText:='';
         end;
     SlokasArr2[i-1].info:=Inforec;
{    b_perenos:=S_Ansi[Length(S_Ansi)]='-';
    if b_perenos then
      SetLength(SlokasArr2[i-1].Text, Length(SlokasArr2[i-1].Text)-1);}
  end else
  if S_Ansi[1]='-' then
  begin
   CutNextUseDelimiter(S_Ansi,'-');
   RusPage:=StrToInt(CutNextUseDelimiter(S_Ansi,'-'));
   b_perenos:=True;
  end else
  if Pos(KeyWords.Skazanie,S_Ansi)=1 then
  begin
   PrevSlokaText:=S_W;
  end else
  if Pos(KeyWords.Povest,S_Ansi)=1 then
  begin
   PrevSlokaText:=S_W;
  end else
  if AnsiCompareStr(KeyWords.Konec,Copy (S_Ansi,1,Length(KeyWords.Konec)))=0 then
  begin
   SlokasArr2[i-1].EndBookText:=Concat(SlokasArr2[i-1].EndBookText,'<br>',S_W);
  end else
  // Uvaca text
  if (Pos(KeyWords.Skazal,S_Ansi)in [1..30])and (Pos(':',S_Ansi)in [1..40])and (Length(S_Ansi)<50) and (S_Ansi[1]<>' ') then
  begin
   UvacaText:=S_w;
   Writeln (F2,'Uvaca: ',#9,S_w);
  end
  else
  if IsGlavaSingInText(S_Ansi,KeyWords.Glava) then
  begin
   if KeyWords.GlavaAutoIncrement then
    begin
     inc(CurChapter);
     GlavaText:=S_W;
    end
    else
   begin
    CutNextUseDelimiter(S_Ansi,' ');
    CurChapter:=StrToInt(CutNextUseDelimiter(S_Ansi,' '));
    GlavaText:=S_W;
   end
  end else
  if Pos(KeyWords.Takova,S_Ansi)=1 then
  begin
   SlokasArr2[i-1].EndChapterText:=S_W;
  end else
  begin
   if b_perenos then
   begin
    if UTF8ToAnsi(SlokasArr2[i-1].Text[Length(SlokasArr2[i-1].Text)])='-' then
    begin
      SetLength(SlokasArr2[i-1].Text, Length(SlokasArr2[i-1].Text)-1);
      SlokasArr2[i-1].Text:=Concat(SlokasArr2[i-1].Text,s_w);
      if length(SlokasArr2)>0 then SlokasArr2[i-1].RusPage2:=RusPage;
    end
     else
    begin
      if KeyWords.BreakInTranslation
      then SlokasArr2[i-1].Text:=Concat(SlokasArr2[i-1].Text,'<br>',s_w)
      else
        begin
        if S_w[1]<>' '
         then SlokasArr2[i-1].Text:=Concat(SlokasArr2[i-1].Text,' ',s_w)
         else SlokasArr2[i-1].Text:=Concat(SlokasArr2[i-1].Text,s_w);
        end;
      if length(SlokasArr2)>0 then SlokasArr2[i-1].RusPage2:=RusPage;
    end
   end else
   begin
    SlokasArr2[i-1].Text:=Concat(SlokasArr2[i-1].Text,'<br>',s_w);
   if length(SlokasArr2)>0 then SlokasArr2[i-1].RusPage2:=RusPage;
   end;
   Writeln (F2,'Other: ',#9,S_w);
  end;
  except
   Writeln (F2,'Error in the line -',i,#9,S_Ansi0);
   ShowMessage('Error in the translation: '+S_Ansi0);
   break;
  end;
 until EOF(F);
 CloseFile(F);
 CloseFile(F2);
end;

function TMhHTMLBuilder.MarkRusNames(AText: widestring): widestring;
var
 i:integer;
begin
 result:=Atext;
 if CurSlokaNum>100 then exit;
// exit;
 for i:=1 to RusList.Count do
 begin
    AText:=StringReplace(AText,RusList[i-1],'<span class="person_translation">'+RusList[i-1]+'</span>',[rfReplaceAll]);
 end;
 result:=AText;
end;

procedure TMhHTMLBuilder.OutPutText;
var
 F:TextFile;
 F1:TextFile;
 FileName:string;
 i,j,n,l:integer;
 PrevChapter:integer;
 CommentUsed:array of boolean;
 FootnoteUsed:array of boolean;
 S_W,AIastText, S_Rus,sFullText:widestring;
 inf:TIASTSlolakaInfo;
 S_ansi,ErrStr:string;
 IDStr:string;
  //-------------------
  procedure CommentsOutput;
  var
   j:integer;
   temp:TStringList;
  begin
    if CommentsForOutput.Count>0 then
     begin
       HTML_BeginCommentsBlock;
       // ----начало -удаление одинаковых номеров
       temp:=TStringList.Create;
       temp.Sorted:=True;
       for j:=1 to CommentsForOutput.Count do
        temp.Add(CommentsForOutput[j-1]);
       temp.Sorted:=False;
       CommentsForOutput.Clear;
       CommentsForOutput.AddStrings(temp);
       temp.Free;
       // ----- конец -удаление одинаковых номеров
       CommentsForOutput.CustomSort(CompareNum);
       Writeln (F,'<! -- comment -->');
       for j:=1 to CommentsForOutput.Count do
          begin
           n:=StrToInt(CommentsForOutput[j-1]);
           Writeln(F,CommentsArr[j-1].info.Num,' ',CommentsArr[n-1].Text, ' ', CommentsArr[n-1].RusPage1,'-',CommentsArr[n-1].RusPage2);
{           if KeyWords.KamasutraComment
            then HTML_CommentText(SlokasArr[i-1].info.NSubChapter,n,SlokasArr[i-1].RusPage1,SlokasArr[i-1].RusPage2)
            else HTML_CommentText(SlokasArr[i-1].info.NChapter,n,SlokasArr[i-1].RusPage1,SlokasArr[i-1].RusPage2);}
           if KeyWords.KamasutraComment
            then HTML_CommentText(SlokasArr[i-1].info.NSubChapter,n,CommentsArr[n-1].RusPage1,CommentsArr[n-1].RusPage2)
            else HTML_CommentText(SlokasArr[i-1].info.NChapter,n,CommentsArr[n-1].RusPage1,CommentsArr[n-1].RusPage2);
           CommentUsed[n-1]:=True;
          end;
       HTML_EndCommentsBlock;
       CommentsForOutput.Clear;
     end;

  end;
  //-------------------
  procedure FootnotesOutput;
  var
   j:integer;
  begin
    if FootnotesForOutput.Count>0 then
     begin
       HTML_BeginCommentsBlock;
       Writeln (F,'<! -- comment -->');
       for j:=1 to FootnotesForOutput.Count do
          begin
           n:=StrToInt(FootnotesForOutput[j-1]);
           Writeln(F,FootnotesArr[j-1].info.Num,' ',FootnotesArr[n-1].Text);
           HTML_FootNoteText(True,j,0,0);
           FootnoteUsed[n-1]:=True;
          end;
       HTML_EndCommentsBlock;
       FootNotesForOutPut.Clear;
     end;

  end;
  //-------------------
begin
 HTMLRewrite(Path+CS_ResHTMLFileName);
// FileName:= ExtractFilePath(Form1.OpenDialog1.FileName)+'ram.txt';
 FileName:= Path+ResFileName;
 AssignFile(F,FileName);
 rewrite(F);
{ AssignFile(F1,'C:\tmp\ragh.txt');
 Append(F1);}

 PrevChapter:=0;
 SetLength(CommentUsed,0);
 SetLength(CommentUsed,Length(CommentsArr));
 SetLength(FootnoteUsed,0);
 SetLength(FootnoteUsed,Length(FootNotesArr));
 for i:=1 to Length(SlokasArr) do
 begin
  CurSlokaNum:=i;
  CurChapter:=SlokasArr[i-1].info.NChapter;
  CommentsForOutput.Clear;
  FootNotesForOutPut.Clear;
  Form1.StatusBar1.Panels[0].Text:='Output line '+IntToStr(i)+'/'+IntToStr(Length(SlokasArr)) ;
  Application.ProcessMessages;
// Chapter;
//  Writeln (F,'<! -- chapter -->');
  if SlokasArr[i-1].Prevtext<>'' then
   begin
    Writeln (F,SlokasArr[i-1].Prevtext);
    if KeyWords.CutBookFromCitation then IDStr:='' else IDStr:=IntToStr(SlokasArr[i-1].info.NBook)+'.';
    IDStr:=IDStr+IntToStr(SlokasArr[i-1].info.NChapter)+'.'+IntToStr(SlokasArr[i-1].info.Num1);
    HTMLChapterCaption (IDStr,SlokasArr[i-1].Prevtext);
   end;
  if SlokasArr[i-1].info.NChapter<>PrevChapter then
   begin
    Writeln (F, SlokasArr[i-1].Glavatext);
    if PrevChapter<>0 then HTML_EndChapter;
    HTMLChapterNum (SlokasArr[i-1].info.NChapter,SlokasArr[i-1].GlavaText);
    if KeyWords.CommentNumIsShlokaNum then
     begin
      MemoryCommentForOutput('0','0',SlokasArr[i-1].info.NChapter,0);
     end;
    CommentsOutput;
    CommentsForOutput.Clear;
    {вставка нулевого комментария для ригведы?}
   end;
  PrevChapter:=SlokasArr[i-1].info.NChapter;
  //вставка номера шлоки, одно число или диапазон
  Writeln(F,'<! -- Num -->');
  Write(F,NBook,'.',SlokasArr[i-1].info.NChapter,'.');
  Write(F,AnsiToUtf8(IntToStr(SlokasArr[i-1].info.Num1)));
  if SlokasArr[i-1].info.Num1<>SlokasArr[i-1].info.Num2 then Write(F,AnsiToUtf8('-'),IntToStr(SlokasArr[i-1].info.Num2));
  Writeln(F);
  S_Rus:=IntToStr(NBook)+'.'+IntToStr(SlokasArr[i-1].info.NChapter)+'.'+IntToStr(SlokasArr[i-1].info.Num1);
  if SlokasArr[i-1].info.Num1<>SlokasArr[i-1].info.Num2 then S_Rus:=S_Rus+AnsiToUtf8('-')+IntToStr(SlokasArr[i-1].info.Num2);
  HTMLRange(SlokasArr[i-1].info.Num1,SlokasArr[i-1].info.Num2,SlokasArr[i-1].RusPage1,SlokasArr[i-1].RusPage2);
  //----------------------------------------------
 // IAST
  Writeln (F,'<! -- sanskrit -->');
  AIastText:='';
  for j:=SlokasArr[i-1].info.Num1 to SlokasArr[i-1].info.Num2 do
  begin
   inf:=tisi_all;
   if (j=SlokasArr[i-1].info.Num1) and (SlokasArr[i-1].info.bNum1Crossing) then inf:=tisi_second else
   if (j=SlokasArr[i-1].info.Num2) and (SlokasArr[i-1].info.bNum2Crossing) then inf:=tisi_first;
   with SlokasArr[i-1].info do
    S_W:=GetSanskritShlokaText(NBook,NChapter,j,inf,ErrStr);
   if ErrStr<>'' then ErrList.Add(ErrStr);
   Writeln(F,S_W);
   AIastText:=Concat(AIastText,S_W);
  end;
  if KeyWords.DisableUvachaInSankrit
   then HTML_IAST_Text(AIastText,False)
   else HTML_IAST_Text(AIastText,SlokasArr[i-1].UvacaText<>'');
  // Translation
   Writeln (F,'<! -- rus -->');
   if SlokasArr[i-1].UvacaText<>'' then
     Writeln(F,SlokasArr[i-1].UvacaText);
   Writeln(F,SlokasArr[i-1].Text);
   S_Rus:='['+S_Rus+'] '+SlokasArr[i-1].UvacaText+SlokasArr[i-1].Text;
   sFullText:=SlokasArr[i-1].Text;
//   if KeyWords.b2Transl then sFullText:=sFullText+'<br><br><u>'+AnsiToUTF8('Буквальный перевод:')+'</u><br>'+SlokasArr2[i-1].Text;
   if KeyWords.b2Transl then sFullText:=sFullText+'<br><br>'+SlokasArr2[i-1].Text;
   if KeyWords.ManyTransl>1 then
   begin
     SlokasArr2:=ManyTransSlokasArr[0];
     sFullText:=MakeURLFromAbbr (sAbbrArr[0],0,SlokasArr2[i-1].info.NChapter, SlokasArr2[i-1].info.Num1) +SlokasArr2[i-1].UvacaText + ' '+ SlokasArr2[i-1].Text;
     S_Ansi:=UTF8ToAnsi(sFullText);
     for j:=2 to KeyWords.ManyTransl do
      begin
       SlokasArr2:=ManyTransSlokasArr[j-1];
       sFullText:=sFullText+'<p>'+MakeURLFromAbbr (sAbbrArr[j-1],j-1, SlokasArr2[i-1].info.NChapter,SlokasArr2[i-1].info.Num1) +SlokasArr2[i-1].UvacaText + ' '+SlokasArr2[i-1].Text+'</p>';
       S_Ansi:=UTF8ToAnsi(sFullText);
      end;
    end;
   {!}
   if KeyWords.DisableUvachaInRus
    then HTML_Rus_Text('',sFullText) // для 10 преводов Бхагавадгиты
    else HTML_Rus_Text(SlokasArr[i-1].UvacaText,sFullText);
    if KeyWords.CommentNumIsShlokaNum and KeyWords.IsFootNotes  then
     begin
       FootNotesForOutPut.AddStrings(CommentsForOutput);
       CommentsForOutput.Clear;
     end;
 // IAST+Rus Block---------------------------------------------------------------------------------
  AIastText:='';
  for j:=SlokasArr[i-1].info.Num1 to SlokasArr[i-1].info.Num2 do
  begin
   inf:=tisi_all;
   if (j=SlokasArr[i-1].info.Num1) and (SlokasArr[i-1].info.bNum1Crossing) then inf:=tisi_second else
   if (j=SlokasArr[i-1].info.Num2) and (SlokasArr[i-1].info.bNum2Crossing) then inf:=tisi_first;
   with SlokasArr[i-1].info do
    S_W:=GetSanskritShlokaText(NBook,NChapter,j,inf,ErrStr);
   if ErrStr<>'' then ErrList.Add(ErrStr);
//   Writeln(F1,IntToStr(NBook)+'.'+IntToStr(SlokasArr[i-1].info.NChapter)+'.'+IntToStr(j),#9,S_W,#9,S_Rus);
   AIastText:=Concat(AIastText,S_W);
  end;
 // IAST+Rus Block end---------------------------------------------------------------------------------

  //output sanscrit shlocas, if sanscrit only and no translation---
  AIastText:='';
  n:=SlokasArr[i-1].info.NChapter;
  j:=SlokasArr[i-1].info.Num2;
  if (CSR_Counts[n-1]=j) and (CSS_Counts[n-1]>CSR_Counts[n-1]) then
  begin
   {HTML_EndRangeBlock;}
//    Writeln(HTF, '</div>'); {!!!не понятно где потерялся}
    HTMLRange(CSR_Counts[n-1]+1,CSS_Counts[n-1],0,0);
    for j:=CSR_Counts[n-1]+1 to CSS_Counts[n-1] do
    begin
       if j=CSR_Counts[n-1]+1 then Writeln (F,'<! -- only sanskrit data -->');
       inf:=tisi_all;
       with SlokasArr[i-1].info do
        S_W:=GetSanskritShlokaText(NBook,n,j,inf,ErrStr);
       if ErrStr<>'' then ErrList.Add(ErrStr);
       Writeln(F,S_W);
       AIastText:=Concat(AIastText,S_W);
    end;
    HTML_IAST_Text(AIastText,False);
    Writeln (F,'<! -- '+C_NoRusData+' -->');
    HTML_Rus_Text('',C_NoRusData);
  end;
  // Если примечание в конечном тексте, то мы его запоминаем для вывода,
  if SlokasArr[i-1].EndChapterText<>'' then FormatFootnoteInText(SlokasArr[i-1].EndChapterText);
  if SlokasArr[i-1].EndBookText<>'' then FormatFootnoteInText(SlokasArr[i-1].EndBookText);
  // Comments block ----------------------------------------------
  if KeyWords.IsFootNotes then FootnotesOutput;
  if KeyWords.CommentNumIsShlokaNum then
   begin
     MemoryCommentForOutput(IntToStr(SlokasArr[i-1].info.Num1),IntToStr(SlokasArr[i-1].info.Num2),SlokasArr[i-1].info.NChapter,0);
   end;
  CommentsOutput;
  // такова в ... ----------------------------------------------
   if SlokasArr[i-1].EndChapterText<>'' then Writeln(F,SlokasArr[i-1].EndChapterText);
   if SlokasArr[i-1].EndBookText<>'' then Writeln(F,SlokasArr[i-1].EndBookText);
   HTML_EndCitationBlock;
  // end такова в ... ------------------------------------------
   HTML_EndChapterText(SlokasArr[i-1]);
 end;
 HTML_EndChapter;
 HTML_EndBook;
 for j:=1 to Length(CommentsArr) do if not CommentUsed[j-1] then
 begin
  S:=Concat(S,IntToStr(j-1),', ');
  ErrList.Add('Не использован комментарий : №'+UTF8ToAnsi(CommentsArr[j-1].info.Num)+' в Главах ' + IntToStr(CommentsArr[j-1].info.NChapter1)+ ' - '+IntToStr(CommentsArr[j-1].info.NChapter2)+'; Доп. поле '+UTF8ToAnsi(CommentsArr[j-1].info.nShloka)+':'+UTF8ToAnsi(CommentsArr[j-1].Text));
 end;
{ for j:=1 to Length(FootNotesArr) do if not FootNoteUsed[j-1] then
 begin
  S:=Concat(S,IntToStr(j-1),', ');
  ErrList.Add('Не использована сноска : №'+UTF8ToAnsi(CommentsArr[j-1].info.Num)+'; Доп. поле '+UTF8ToAnsi(CommentsArr[j-1].info.nShloka)+':'+UTF8ToAnsi(CommentsArr[j-1].Text));
 end;}
 CloseFile(F);
// CloseFile(F1);
 HTMLCloseFile;
end;

function TMhHTMLBuilder.GetSanskritShlokaText(NBook, NChapter, NSloka: integer;
  Info: TIASTSlolakaInfo;var ErrStr:String): WideString;
var
 SlokaFullNum:String;
 k,i:integer;
 NStrInSloka:integer;
 S_W:string;
begin
 result:='';
 ErrStr:='';
 SlokaFullNum:=IntToStrNils(NBook,KeyWords.BookLettersCount)+'.'+IntToStrNils(NChapter,3)+'.'+IntToStrNils(NSloka,3);
 k:=SanskritArrSlokaNums.IndexOf(SlokaFullNum);
 if k=-1 then
 begin
  ErrStr:='Запрос неправильного номера шлоки на санскрите: '+SlokaFullNum;
  Result:=C_NoSankritData;
  exit;
 end;
//--------------------------
// find NStrInSloka
 NStrInSloka:=1;
  i:=k;
 repeat
  inc(i);
  if i=SanskritArrSlokaNums.Count then break;
  if SanskritArrSlokaNums[i]=SlokaFullNum then inc(NStrInSloka) else break;
 until i=SanskritArrSlokaNums.Count-1;
//--------------------------
 for i:=k to k+NStrInSloka-1 do
 begin
  if (Info=tisi_All) then
  result:=result+SanskritArrSlokaTexts[i]+'<br>';

  if (Info=tisi_first) and (i=k) then
  result:=result+SanskritArrSlokaTexts[i]+IntToStr(NSloka)+'.1<br>';

  if (Info=tisi_second) and (i<>k) then
  result:=result+SanskritArrSlokaTexts[i]+'<br>';
 end ;
end;

procedure TMhHTMLBuilder.Check;
var
 i:integer;
 N_Rus,N_IAST:integer;
 NGlMax,NShlMax:integer;
begin
// проверка кол-ва шлок в каждой главе.
 N_Rus:=Length(CSR_Counts);
 N_IAST:=Length(CSS_Counts);
 NGlMax:=N_Rus; if N_IAST>NGlMax then NGlMax:=N_IAST;
 if N_IAST<>N_Rus then
 begin
  ErrList.Add('Несоответствие кол-ва глав в русском и санскрите:'+IntToStr(N_Rus)+' vs '+IntToStr(N_IAST));
 end;
 for i:=1 to NGlMax {=N_IAST,N_Rus} do
 begin
  if CSR_Counts[i-1]<>CSS_Counts[i-1] then
  begin
   ErrList.Add('Несоответствие кол-ва шлок в русском и санскрите в главе '+IntToStr(i)+':'+IntToStr(CSR_Counts[i-1])+' vs '+IntToStr(CSS_Counts[i-1]));
  end;
 end;
// проверка пересечения номеров шлок в русском.
 S:='';
 for i:=2 to Length(SlokasArr) do
 begin
  if (SlokasArr[i-1].info.NChapter=SlokasArr[i-2].info.NChapter) and
    (SlokasArr[i-1].info.Num1=SlokasArr[i-2].info.Num2) then
  begin
   ErrList.Add('Повторение шлоки ' +IntToStr(SlokasArr[i-2].info.Num2)+ ' в главе '+IntToStr(SlokasArr[i-2].info.NChapter));
   SlokasArr[i-1].info.bNum1Crossing:=True;
   SlokasArr[i-2].info.bNum2Crossing:=True;
  end;
 end;
end;


procedure TMhHTMLBuilder.MemoryCommentForOutput(NumCommentStr1,NumCommentStr2:widestring;CurChapterNum, Reserved:integer);
 // NumCommentStr2 - номер шлоки, там где он есть (Вьяса Бхашья, Камасутра)
var
 i,j, code:integer;
 S:WideString;
 N1,N2:integer;
 S_Ansi:string;
 bShlokaOk:boolean;
begin
 for i:=1 to Length(CommentsArr) do
 begin
  if KeyWords.KamasutraComment then
   begin
    if CommentsArr[i-1].info.Num<>NumCommentStr1 then continue;
    if CommentsArr[i-1].info.NChapter1<>Reserved then continue;
   end else if KeyWords.TwoLevelCombineComment then
   begin
      if CommentsArr[i-1].info.nShloka<>IntToStr(Reserved) then continue;
   end else
   begin
    if CurChapterNum<CommentsArr[i-1].info.NChapter1 then continue;
    if CurChapterNum>CommentsArr[i-1].info.NChapter2 then continue;
   end;
  S:=CommentsArr[i-1].info.Num;
//  S:=WSExtractDigits(CommentsArr[i-1].info.Num); не срабатывало на 85a0 в БхГ Смирнова
  S_Ansi:=Utf8ToAnsi(S);
  if KeyWords.TwoLevelCombineComment
   then bShlokaOk:=S=NumCommentStr1
   else bShlokaOk:=(S=NumCommentStr1)or(S=NumCommentStr2);
  if bShlokaOk
    then CommentsForOutput.Add(IntToStr(i))
    else if GetDiapasoneFromText(S_Ansi, ' ', N1,N2) then
     begin
       if N1=N2 then
       begin
        if (IntToStr(N1)=NumCommentStr1)and (CommentsForOutput.Indexof(IntToStr(i))<0) then CommentsForOutput.Add(IntToStr(i));
        if (IntToStr(N1)=NumCommentStr2)and (CommentsForOutput.Indexof(IntToStr(i))<0) then CommentsForOutput.Add(IntToStr(i));
       end
       else
       begin
        if (IntToStr(N1)=NumCommentStr1) and (CommentsForOutput.Indexof(IntToStr(i))<0) then CommentsForOutput.Add(IntToStr(i));
        if (IntToStr(N2)=NumCommentStr2) and (CommentsForOutput.Indexof(IntToStr(i))<0) then CommentsForOutput.Add(IntToStr(i));
        // вроде как нужно добавить
        if (IntToStr(N1)=NumCommentStr2) and (CommentsForOutput.Indexof(IntToStr(i))<0) then CommentsForOutput.Add(IntToStr(i));
        if (IntToStr(N2)=NumCommentStr1) and (CommentsForOutput.Indexof(IntToStr(i))<0) then CommentsForOutput.Add(IntToStr(i));
       end;
     end;
  end;
end;

function TMhHTMLBuilder.IsGlavaSingInText(Atext, AGlava: string): boolean;
 var
  EndStrPos:boolean;
begin
  Result:=False;
  EndStrPos:=Pos('$', AGlava)=Length(AGlava);
  if EndStrPos then
  begin
   SetLength(AGlava,Length(AGlava)-1);
   Result:= Pos(AGlava,AText)=Length(AText)-Length(AGlava)+1;
  end else
  begin
   Result:= Pos(AGlava,AText)=1;
  end;
end;

function TMhHTMLBuilder.IsShlokaNum(Atext: string): boolean;
begin
 Result:=False;
 if KeyWords.OnlyRus then //для статей
 begin
  Result:=(AText[1]='#');
  if not Result then Result:=IsRussianUpperCase (AText[1]);
  if not Result then Result:=(AText[1]='«');
 end
  else
 if KeyWords.ShlokaOnlyNumber then
 begin
  Result:=(AText[1] in ['0'..'9']);
 end
  else
  begin
   Result:=(AText[1]='[')and (AText[2] in ['0'..'9']);
  end;
end;

procedure TMhHTMLBuilder.ExtractShlokaNums(var Atext: string; var N1,
  N2: integer);
var
 S:string;
 i:integer;
begin
 if KeyWords.ShlokaOnlyNumber
  then S:=CutNextUseDelimiter(Atext,' ')
  else begin S:=CutNextUseDelimiter(Atext,']');Delete(S,1,1); end;
 for i:=1 to length(S) do if not (S[i] in ['0'..'9']) then S[i]:=' '; // замена любого тире на пробел
 N1:=StrToInt(CutNextUseDelimiter(s,' '));
 if S<>'' then N2:=StrToInt(CutNextUseDelimiter(s,' ')) else N2:=N1;
end;

Function TMhHTMLBuilder.GetDiapasoneFromText(Atext:string;Delimiter:string;var N1,N2:integer):boolean;
var
 i,code1,Code2:integer;
 S:string;
 bNoN2:boolean;
begin
 bNoN2:=False;
 Code2:=0;
 S:=CutNextUseDelimiter(AText,Delimiter);
 for i:=1 to length(S) do if not (S[i] in ['0'..'9']) then S[i]:=' ';
 Val(CutNextUseDelimiter(S,' '),N1,Code1);
 if S<>''
   then Val(CutNextUseDelimiter(S,' '),N2,Code2)
   else begin N2:=N1; bNoN2:=True end;
 if KeyWords.IgnoreFirstNumberInComments then N1:=N2;   // более поздняя вставка для Гитаговинды
 Result:=(Code1=0)and(Code2=0);
end;


procedure TMhHTMLBuilder.HTMLCitationBlock;
begin
//citation_block
end;


function TMhHTMLBuilder.IsFirstStringComment(S_Ansi:string; var p1,p2,p3:string): boolean;// первая строка комментария
var
 sCommentPart1,sCommentPart2,sCommentPart3:string;
 Val1,Val2, Code1, Code2:integer;

begin
 Result:=False;
 sCommentPart1:='';
 sCommentPart2:='';
 sCommentPart3:='';
 if KeyWords.ThreeLevelComment then
 begin
  sCommentPart1:=CutNextUseDelimiterNoTrim(S_Ansi,'.');
  sCommentPart2:=CutNextUseDelimiterNoTrim(S_Ansi,'.');
  sCommentPart3:=CutNextUseDelimiterNoTrim(S_Ansi,' ');
  if (sCommentPart1=ArabicToRoman(NBook))and (sCommentPart2[1] in ['1'..'9']) then
   begin
    Result:=True;
    p1:=sCommentPart1;
    p2:=sCommentPart2;
    p3:=sCommentPart3;
    if p3[Length(P3)]=',' then SetLength(P3,Length(P3)-1);
    if p3[Length(P3)]='.' then SetLength(P3,Length(P3)-1);
   end
 end else
 if KeyWords.TwoLevelCombineComment then
 begin
  sCommentPart1:=CutNextUseDelimiterNoTrim(S_Ansi,'.');
  sCommentPart2:=CutNextUseDelimiterNoTrim(S_Ansi,'.');
  val(sCommentPart1,Val1, Code1);
  val(sCommentPart2,Val2, Code2);
  if (Code1=0) and (Code2=0) then
   begin
    Result:=True;
    p1:=sCommentPart1;
    p2:=sCommentPart2;
    if p2[Length(P2)]=',' then SetLength(P2,Length(P2)-1);
    if p2[Length(P2)]='.' then SetLength(P2,Length(P2)-1);
   end
 end
 else Result:=S_Ansi[1] in ['1'..'9'];
end;

procedure TMhHTMLBuilder.LoadFootNotes;
var
 FileName:string;
 F:textFile;
 S_W,S_N, S_Nm:widestring;
 S,S_Ansi,S_Ansi0:string;
 InfoRec:TCommentInfoRec;
 i,j, ErrCode:integer;
 bPrevStrIsPageNum,bPerenos:boolean;
 CurChapter, RusPage:integer;
 CurShloka:integer;
 bFootNote:boolean; // комментарий без номера, который нужно вставить после загаловка главы
 bFirstStringOfComment:boolean;
 p1,p2,p3:string;
// PrevNum:string;
begin
  // предположительно в файле только нумерованные сноски по типу
  //1 текст
  //2 текст
  // все что не начало сноски иде в текст сноски через <br>
 FileName:=Path+CS_FootNotesFileName;
 AssignFile(F,FileName);
 Reset(F);
 readln(F);
 readln(F);
 i:=0;
 InfoRec.NBook:=NBook;
 repeat
  readln(F,S_w);
  S_Ansi:=UTF8ToAnsi(S_w);
  S_Ansi0:=S_Ansi;
  bFootNote:=S_Ansi[1] in ['1'..'9'];
  if bFootNote then
  begin
   S_N:=WSCutNextUseDelimiterNoTrim(S_w, ' ');
   inc(i); // номер комментария
   SetLength(FootNotesArr,i);
   InfoRec.Num:='0';
   InfoRec.N1:=StrToInt(S_N);
   FootNotesArr[i-1].Text:=s_w;
   FootNotesArr[i-1].RusPage1:=RusPage;
   FootNotesArr[i-1].RusPage2:=RusPage;
   FootNotesArr[i-1].info:=InfoRec;
  end else
   FootNotesArr[i-1].Text:=FootNotesArr[i-1].Text+'<br>'+S_w;
 until EOF(F);
 CloseFile(F);
end;

function TMhHTMLBuilder.FormatFootnoteInText2(bInTransl:Boolean;
  AText: widestring): widestring;
var
 i,j,v,code,k,Pos1, Pos2:integer;
 NumCommentStr,S_to_Replace,S_to_Find,S:widestring;
 CurChapterNum,CurSubChapterNum:integer;
 CurShlokaStr:string;
 C1,C9:widechar;
 iAdd:integer;
 CommentsCount1,CommentsCount2:integer;
 AddStr:string;
 ErrCode:Boolean;
begin
 if bInTransl then AddStr:='t_' else AddStr:='c_';
 if KeyWords.ChapterStrToClear=''
  then  Result:=AText
  else Result:=StringReplace(Atext,KeyWords.ChapterStrToClear,'',[]);
 if Pos (KeyWords.Bracket1,Atext)=0 then exit;      //<скобка>
 CurChapterNum:=SlokasArr[CurSlokaNum-1].info.NChapter;
 CurShlokaStr:=intToStr(SlokasArr[CurSlokaNum-1].info.Num1);
 CurSubChapterNum:=SlokasArr[CurSlokaNum-1].info.NSubChapter;
 S:=AText;
 //
 k:=1;
 if bInTransl then // только для перевода, но не комментариев.
 repeat
   Pos1:=0;
   C1:='1';
   C9:='9';
   for i:=k to Length(AText)-1 do
    if (S[i]=KeyWords.Bracket1) and (S[i+1] in [c1..c9]) then //<скобка>
    begin
     Pos1:=i;
     break;
    end;
   if Pos1=0 then exit;
   for i:=Pos1 to Length(S){Pos1+20} do
    if S[i]=KeyWords.Bracket2 then begin Pos2:=i; break; end; //<скобка>
   S_to_Find:=Copy(S,Pos1-1,Pos2-Pos1+2); // pos-1,Pos2-Pos1+2 учитывает пробел
//   S_to_Find:=Copy(S,Pos1-1,Pos2-Pos1+1); // pos-1,Pos2-Pos1+2 не учитывает пробел
   NumCommentStr:=Copy(S,Pos1+1,Pos2-Pos1-1);
   ErrCode:=False;
   for j:=1 to Length(NumCommentStr) do
    begin
      Val(NumCommentStr[j],v,code);
      if code>0 then begin ErrCode:=True; break; end;
    end;
   if ErrCode then begin inc(k); Continue end;
   CommentsCount1:=FootNotesForOutPut.Count;
   FootNotesForOutPut.Add(NumCommentStr);
//   <a href='#comment_1_1' class='comment_sub'><sup><small>1</small></sup></a> ? ????
   CommentSymbols:='comment'+IntToStr(NBook)+'_';
   S_to_Replace:='<a href='+C39+'#'+CommentSymbols+AddStr+NumCommentStr+C39+'class='+C39+'comment_sub'+C39+'>';
//   MemoryCommentForOutput(NumCommentStr,NumCommentStr,CurChapterNum, 0);
   CommentsCount2:=FootNotesForOutPut.Count;
   S_to_Replace:=S_to_Replace+'<sup><small>'+NumCommentStr+'</small></sup></a>';
    if CommentsCount2-CommentsCount1>0
     then Atext:=StringReplace(Atext,S_to_Find,S_to_Replace,[])
     else
      begin
//       ShowMessage('Ошибка добавления комментария '+UTF8ToAnsi(NumCommentStr));
       break
      end;
    S:=Atext;
    k:=Pos(S_to_Replace,S)+Length(S_to_Replace)-1;;
   Result:=AText;
 until False;
 result:=Atext;
end;


procedure TMhHTMLBuilder.HTML_CommentText(ChapterNum,CommNum,RusPage1,RusPage2:integer);
var
  i:Integer;
  RusPages:string;
begin
//<div class="comment_item" id="comment_1_1"> + ShlokaStr в случае, когда это необходимо
//<span class="comment_number">1</span> -
//<span class="comment_text">
//</span></div>
 RusPages:=IntTostr(RusPage1);
 if RusPage1<>RusPage2 then RusPages:=RusPages+'-'+IntTostr(RusPage2);
 CommentSymbols:='comment'+IntToStr(NBook)+'_';
 Write(HTF, '        <div class="comment_item" id="'+CommentSymbols);
 with CommentsArr[CommNum-1] do
 begin
   Write(HTF, ChapterNum,'_',info.Num);
   if KeyWords.TwoLevelCombineComment then Write(HTF, '_',info.nShloka);
   Writeln(HTF,'">');
   Write(HTF, '          <span class="comment_number" ');
//   Write(HTF, 'title="', AnsiToUTF8(KeyWords.BookNameForCitation+': '));
   Write(HTF, 'data-src="', AnsiToUTF8(IntToStr(KeyWords.datasrc))); Write(HTF,'" ');
   Write(HTF, 'data-page="', AnsiToUTF8(RusPages)); Write(HTF,'" ');
   Write(HTF, 'title="', AnsiToUTF8('c. '+RusPages));
   //   Writeln(HTF, '">', info.Num,'</span>','. ');
   if info.Num<>'0'
    then
     begin
      Write(HTF, '">');
      if KeyWords.TwoLevelCombineComment then Write(HTF, info.nShloka,'.');
      Writeln(HTF, info.Num,'. ','</span>');
     end
    else Writeln(HTF, '">', '','</span>','');
   Write(HTF, '          <span class="comment_text">');
//   Writeln(HTF, Text);
   Write(HTF, FormatFootnoteInText2(False,Text));
   Writeln(HTF, '</span>');
   if bShowDivComment then Writeln(HTF, '<!-- end comment_item-->');
   Writeln(HTF, '        </div>');
 end;
 //--------------------------------------------------
 //footnotes
  for i:=1 to FootNotesForOutPut.Count do
    HTML_FootNoteText(False, i, RusPage1,RusPage2);
  FootNotesForOutPut.Clear;
end;

procedure TMhHTMLBuilder.HTML_FootNoteText(bInTransl:Boolean;index,RusPage1,RusPage2:integer);
var
  k:Integer;
  AddStr:string;
begin
  if not KeyWords.IsFootNotes then Exit;
  if bInTransl then AddStr:='t_' else AddStr:='c_';
 //footnotes
   if bInTransl then k:=0 else k:=KeyWords.TranslationFootnotesCount;
   CommentSymbols:='comment'+IntToStr(NBook)+'_';
   Write(HTF, '<div class="comment_item" id="'+CommentSymbols+AddStr+FootNotesForOutPut[index-1]+'">');
   Writeln(HTF, '<span class="comment_number">');
   Writeln(HTF, FootNotesForOutPut[index-1]);
   Writeln(HTF, '</span>');
   Writeln(HTF, '<span class="comment_text">');
   Writeln(HTF, '<small>');
   Writeln(HTF, FootNotesArr[k+StrToInt(FootNotesForOutPut[index-1])-1].Text);
   Writeln(HTF, '</small>');
   Writeln(HTF, '</span>');
   Writeln(HTF, '</div>');

end;

function TMhHTMLBuilder.MakeURLFromAbbr(AbbrText: string; TranslationID,NChapter,
  NShloka: Integer): widestring;
var
 Res_Ansi:string;
begin
//  <a href="https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_yAjJavalkyasmRti.htm">gretil.sub.uni-goettingen.de</a>
 Res_Ansi:='<a href="'+html_files[TranslationID]+'#'+IntToStr(NChapter)+'.'+IntToStr(NShloka)+'">';
 Res_Ansi:=Res_Ansi+AbbrText+'</a>';
 Result:=AnsiToUtf8 (Res_Ansi);
end;

procedure TMhHTMLBuilder.HTML_EndCitationBlock;
begin
 if bShowDivComment then Writeln(HTF, '<!-- end of citation_block -->');
 Writeln(HTF, '    </div>');
end;

procedure TMhHTMLBuilder.HTML_EndBook;
begin
 Writeln (HTF, '</div>');
end;
procedure TMhHTMLBuilder.HTML_EndChapter;
begin
 Writeln (HTF, '  </div>');
end;

initialization
  bShowDivComment:=False;
//  bDevFileName:=True;
  bDevFileName:=False;
end.

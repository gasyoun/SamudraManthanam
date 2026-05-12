unit uAbstractThread;

{$mode Delphi}

interface
 Uses Classes, uTypes, RegExpr;
type

  { TAbstractThread }

  TAbstractThread = class(TThread)
    pSearchString:string;
    SearchWordList:TStringList;// если ищем несколько слов
    ListBoxIndex:integer;
    bFilesStatusArr:TBoolArr;
    FoundSourcesArr:TIntArr;
    bOptionsCaseSensitive:boolean;
    bOptionsWholeWord:boolean;
    bOk,bAborted:boolean;
    bRegEx:boolean;
    HTMLFileName:string;
  public
    constructor Create(CreateSuspended: Boolean; const StackSize: SizeUInt = DefaultStackSize);
    destructor Destroy;override;
    { Private declarations }
  private
    SearchPeriodStr:string;
    MinValue,CurValue,MaxValue:integer;
    T1,T2:TDateTime;
    FindCount:integer;
    CurPercent,OldPercent:integer;
    procedure Execute;override;
    procedure FindText;
//    function IsWholeWord(Substr, Str: string): boolean;
    procedure MakeHTML_From_FindList(const AFindList: TStringList);
{    procedure ScanFile(FileNum:integer; AText: string;
      var AFindList: TStringList);}
    procedure ScanFile2(FileNum: integer; AText: string;
      var AFindList: TStringList);
    procedure ShowProgress;
    procedure UpdateProgress;
    procedure TerminateMessage;
    procedure OKMessage;
    Function PosSubstringInString(const SubStr, Str:string):integer;
    Function GetFoundSources:string;
  end;
 function FormatFileInfo(Info: String): String;
var
  GlobalThread:TAbstractThread;
  ThreadList:TList;
  ProjectFileName, DefProjectFileName, ProjectFilePath:string;
  ProcessorCount:integer;
  FilesData:array of TStringList;
  FilesData_notags:array of TStringList;
  bFilesLoaded:boolean;
  iRecordLimit:integer;
implementation
uses
  SysUtils, u_Index, DateUtils, textu, WinUtils;
function FormatFileInfo(Info: String): String;
begin
 Delete(Info,1,5);
 Result:=Copy (Info,1,Length(Info)-5);
end;


// пока не работает правильно
(*
function TAbstractThread.IsWholeWord(Substr, Str: string): boolean;
var
  k,l_Str,l_SubStr:integer;
  OtherSymbols:set of char;
begin
 Result:=False;
 k:=Pos(Substr,Str);
 if k=0 then exit;
 l_SubStr:=Length(Substr);
 l_Str:=Length(Str);
 // равно строке - истина
 if (k=1)and (l_Str=l_SubStr) then result:=True else
  // в начале строки + symb- истина
 if (k=1) then
 begin
  if Str[l_SubStr+1] in OtherSymbols then result:=True; {}
 end else
 // symb + в конце строки - истина
 if (k+l_SubStr-1=l_Str) and (Str[k-1] in OtherSymbols) then result:=True else
 // иначе в середине строки проверяем слева и справа
 begin
  if (Str[k+l_SubStr] in OtherSymbols) and
     (Str[k-1] in OtherSymbols) then result:=True;
 end;
end;
 *)
destructor TAbstractThread.Destroy;
begin
 if Terminated
  then Synchronize(TerminateMessage)
  else Synchronize(OKMessage);
 SetLength(bFilesStatusArr,0);
 SetLength(FoundSourcesArr,0);
 SearchWordList.Free;
end;

procedure TAbstractThread.Execute;
var
  i:integer;
begin
 bOk:=False;
 FindText;
 Synchronize(OKMessage);
 bOk:=True;
end;


procedure TAbstractThread.OKMessage;
var
  PeriodStr:string;
begin
 PeriodStr:=IntToStr(SecondsBetween(T1, T2))+' cек.';
 MainForm.ListView.Items[ListBoxIndex].Caption:=pSearchString;
 MainForm.ListView.Items[ListBoxIndex].SubItems[0]:=MainForm.ListView.Items[ListBoxIndex].SubItems[0];
 MainForm.ListView.Items[ListBoxIndex].SubItems[1]:=PeriodStr;
 MainForm.ListView.Items[ListBoxIndex].SubItems[2]:=IntToStr(FindCount);
 MainForm.ListView.Items[ListBoxIndex].SubItems[3]:=GetFoundSources;
 MainForm.ListView.Refresh;
end;

function TAbstractThread.PosSubstringInString(const SubStr, Str: string
  ): integer;
var
  RegExpr: TRegExpr;
begin
 if not bRegEx
   then Result:= Pos(SubStr,Str)
   else
    begin
     RegExpr := TRegExpr.Create;
     try
     RegExpr.Expression :=SubStr;
     if bOptionsWholeWord then RegExpr.Expression := '\b'+SubStr+ '\b';
     // ищем совпадение
     if RegExpr.Exec(Str) then
      begin
        Result:=RegExpr.MatchPos[0];
      end else Result:=0;
     finally
     RegExpr.Free;
     end;
    end;
end;

function TAbstractThread.GetFoundSources: string;
var
  i:integer;
  bMhOnly:boolean;
begin
 bMhOnly:=True;
 Result:='';
 for i:=1 to Length(FoundSourcesArr) do if FoundSourcesArr[i-1]>0 then
  begin
   if bMhOnly then if i in [1..48,67..100] then bMhOnly:=False;
   Result:=Result+IntToStr(i)+', ';
  end;
  if Length(Result)>0
    then SetLength(Result, Length(Result)-2)
    else bMhOnly:=False;
  if bMhOnly then Result:=Result+' [МБх]';
end;

constructor TAbstractThread.Create(CreateSuspended: Boolean;
  const StackSize: SizeUInt);
begin
  inherited;
  SearchWordList:=TStringList.Create;
end;



procedure TAbstractThread.ShowProgress;
begin
 if MaxValue-MinValue<=0
  then CurPercent:=100
  else CurPercent:=round((CurValue-MinValue+1)/(MaxValue-MinValue+1)*100);
  if CurPercent>100 then CurPercent:=100;
 if CurPercent<>OldPercent then Synchronize(UpdateProgress);
 OldPercent:=CurPercent;
end;


procedure TAbstractThread.TerminateMessage;
begin
 {MainForm.StatusBar.Panels[0].Text:='Process terminated...';}
end;

procedure TAbstractThread.UpdateProgress;
begin
 MainForm.ListView.Items[ListBoxIndex].Caption:=pSearchString;
 MainForm.ListView.Items[ListBoxIndex].SubItems[1]:=IntToStr(CurPercent)+'%';
 MainForm.ListView.Items[ListBoxIndex].SubItems[2]:=IntToStr(FindCount);
end;

procedure TAbstractThread.MakeHTML_From_FindList(const AFindList: TStringList);
var
 CaptionsList:TStringList;
 i,index:integer;
 S,S2,S2_Old, S_CurCaption,S_IDLink:string;
 TOCCounts,CaptionCounts:array of integer;
 F:TextFile;
 SecondSorcesCount:integer;
 bISFindListGroupBeginingArr:TByteArr;
 TOCGroupItemNum:byte;
 FileNum:integer;
 sWord_Or_RegExpr,sHTMLSearchString:string;
 Procedure CalcTOCCounts (SourceNum,FindListItemNum:integer);
  var
    i:integer;
 begin
  for i:=1 to Length(TOCItems) do
   if (SourceNum>=TOCItems[i-1].Pos1) and (SourceNum<=TOCItems[i-1].Pos2) then
    begin
     if TOCCounts[i-1]=0 then bISFindListGroupBeginingArr[FindListItemNum-1]:=i; // нужно для вывода содержания
     inc(TOCCounts[i-1]);
    end;
 end;
begin
 SetLength(bISFindListGroupBeginingArr,AFindList.Count);
 CaptionsList:=TStringList.Create;
 SetLength(TOCCounts,Length(TOCItems));
 // создаем список источников
  for i:=1 to AFindList.Count do
   begin
    S:=AFindList[i-1];
    S2:=CutNextUseDelimiterNoTrim(S,#9);
    Index:=StrToInt(S2);
    CalcTOCCounts(Index,i);
    S2:=CutNextUseDelimiterNoTrim(S,#9);
    Index:=CaptionsList.IndexOf(S2);
    if Index<0 then CaptionsList.Add(S2);
   end;
 // сколько раз в каком источнике
 SetLength(CaptionCounts,CaptionsList.Count);
 for i:=1 to AFindList.Count do
  begin
    S:=AFindList[i-1];
    S2:=CutNextUseDelimiterNoTrim(S,#9);
    S2:=CutNextUseDelimiterNoTrim(S,#9);
    Index:=CaptionsList.IndexOf(S2);
    if Index>=0 then inc(CaptionCounts[index]);
  end;
 if SearchWordList.Count=0 then SearchWordList.Add(pSearchString);
// шапка HTML
 AssignFile(F,HTMLFileName);
 Rewrite(F);
 //заглавие HTML

 writeln (F, '<html><head><title>');
 writeln (F, pSearchString);
 writeln (F, '</title>');
 writeln (F, '<meta content="text/html; charset=UTF-8" http-equiv="Content-Type" />');
 writeln (F, '<link rel="stylesheet" href="./src/style.css">');
 //скрипт выделения текста
 writeln (F, '<script>');
 writeln (F, ' window.onload = function() {');
 for i:=1 to SearchWordList.Count do
  begin
   write (F, ' var searchTerm = "');
   write (F, SearchWordList[i-1]);
   writeln (F, '"; // Текст, который вы ищете');
   writeln (F, ' var pageContent = document.body.innerHTML;');
   write (F, ' var highlightedContent = pageContent.replace(new RegExp(searchTerm,'+ chr(39));
   write (F, 'g');
   if not bOptionsWholeWord then  write (F, 'i');
   writeln (F, chr(39)+'), '+chr(39)+'<span class="highlight">$&</span>'+chr(39)+');');
   writeln (F, ' document.body.innerHTML = highlightedContent;');
  end;
 writeln (F, ' document.getElementById("prevButton").addEventListener("click", navigateToPreviousHighlight);');
 writeln (F, ' document.getElementById("nearestButton").addEventListener("click", activateNearestVisibleHighlight);');
 writeln (F, ' document.getElementById("nextButton").addEventListener("click", navigateToNextHighlight);');
 writeln (F, '};');
 writeln (F, '</script>');
 //конец скрипта выделения текста
 writeln (F, '<link rel="shortcut icon" href="./src/favicon/question.ico" type="image/x-icon">');
 writeln (F, '<link rel="icon" href="./src/favicon/question.ico" type="image/x-icon">');
 writeln (F, '</head>');
 writeln (F, '<body>');
 writeln (F, '<div class="button-container">');
  writeln (F, '<button id="prevButton"><</button>');
  writeln (F, '<button id="nearestButton">=</button>');
  writeln (F, '<button id="nextButton">></button>');
 writeln (F, '</div>');
 if not bRegEx then sWord_Or_RegExpr:='для слова' else sWord_Or_RegExpr:='для регулярного выражения';
 sHTMLSearchString:=StringReplace(pSearchString,'<','&lt;',[rfReplaceAll]);
 sHTMLSearchString:=StringReplace(pSearchString,'>','&gt;',[rfReplaceAll]);
 write (F, '<div class="header header_1">При '+SearchPeriodStr+' пахтании Параллельного санскритско-русского корпуса<br>'+sWord_Or_RegExpr+' „'+sHTMLSearchString+'“ в океане слов ');
 if AFindList.Count>0
   then write (F, Sklonenie_Naideno_X_zapisey(AFindList.Count), Sklonenie_Naideno_v_Y_istochnikah(CaptionsList.Count))
   else write (F, 'вовсе не найдено записей.');
 writeln (F, '</div>');
 writeln (F, '<p>Для перехода к предыдущему, ближайшему, следующему выделению используйте<b> кнопки "<","=",">" </b> или <b>клавиши "a","s","d" на клавиатуре.</b></p>');

 // оглавление
 writeln (F, '<!-- Insert code block beginning -->');
 writeln (F, '<div class="contents">');
// - общие по группам -
{ for i:=1 to Length(TOCItems) do
  begin
   S_CurCaption:=TOCItems[i-1].Name;
   writeln (F, '<div class="content_item_big"><div class="content_title_big"><a href="#chapter_group'+IntTostr(i)+'">'+'• '+CutNextUseDelimiterNoTrim(S_CurCaption,';') +'</a>'+ S_CurCaption+ ' ('+Sklonenie_X_zapisey(TOCCounts[i-1])+')</div></div>');
  end;}
 index:=0;
 for i:=1 to CaptionsList.Count do
  begin
   TOCGroupItemNum:=bISFindListGroupBeginingArr[index];
   if bISFindListGroupBeginingArr[index]<>0 then
    begin
       S_CurCaption:=TOCItems[TOCGroupItemNum-1].Name;
//     writeln (F, '<div class="chapter_title" id="chapter_group'+IntToStr(TOCGroupItemNum)+'">'+'• '+TOCItems[TOCGroupItemNum-1].Name+'</div> ('+Sklonenie_X_zapisey(TOCCounts[TOCGroupItemNum-1])+')<br>');
       writeln (F, '<div class="content_item_big"><div class="content_title_big"><a href="#chapter_group'+IntTostr(TOCGroupItemNum)+'">'+'• '+CutNextUseDelimiterNoTrim(S_CurCaption,';') +'</a>'+ S_CurCaption+ ' ('+Sklonenie_X_zapisey(TOCCounts[TOCGroupItemNum-1])+')</div></div>');
    end;
   inc(index,CaptionCounts[i-1]);
   S_CurCaption:=CaptionsList[i-1];
   writeln (F, '<div class="content_item_big"><div class="content_title"><a href="#chapter_'+IntTostr(i)+'">'+IntTostr(i)+'. '+CutNextUseDelimiterNoTrim(S_CurCaption,';') +'</a>'+S_CurCaption+' ('+Sklonenie_X_zapisey(CaptionCounts[i-1])+')</div></div>');
  end;
 // выводим основноые результаты поиска
 writeln (F, '<div class="chapter_splitter"></div>');
 writeln (F, '<div class="chapters">');
 writeln (F, '<div class="chapter">');
 S2_Old:='';
 index:=0;
   for i:=1 to AFindList.Count do
    begin
     S:=AFindList[i-1];
     S2:=CutNextUseDelimiterNoTrim(S,#9);
     FileNum:=StrToInt(S2);
     S2:=CutNextUseDelimiterNoTrim(S,#9);
     S_IDLink:=CutNextUseDelimiterNoTrim(S,#9);
     if S2<>S2_old then
     begin
      inc(index);
      TOCGroupItemNum:=bISFindListGroupBeginingArr[i-1];
      if bISFindListGroupBeginingArr[i-1]<>0 then
          writeln (F, '<div class="chapter_title" id="chapter_group'+IntToStr(TOCGroupItemNum)+'">'+'• '+TOCItems[TOCGroupItemNum-1].Name+'</div> ('+Sklonenie_X_zapisey(TOCCounts[TOCGroupItemNum-1])+')<br>');
      writeln (F, '<div class="chapter_title" id="chapter_'+IntToStr(index)+'">'+IntTostr(index)+'. '+CaptionsList[index-1]+'</div> ('+Sklonenie_X_zapisey(CaptionCounts[index-1])+')<br>');
     end;
  //заголовок элемента поиска в виде таблицы
     S_CurCaption:=CaptionsList[index-1];
     writeln (F, '<table width=1100px><tr>');
     //1-я колонка
      write (F, '<td width=500px><div class="header_table_row1">');
      write (F, CutNextUseDelimiterNoTrim(S_CurCaption,';'));
      writeln (F, '</div></td>');
      //2-я колонка
      write (F, '<td width=100px><div class="header_table_row2">');
      if S_IDLink=''
        then write (F, '[#'+IntTostr(i)+']')
        else write (F, '<a href="'+FilesList[FileNum-1]+'#'+S_IDLink+'" target="_blank">'+'[#'+IntTostr(i)+']'+'</a>');
      writeln (F, '</div></td>');
      //1-я колонка
      write (F, '<td width=500px><div class="header_table_row3">');
      write (F, Trim(S_CurCaption));
      writeln (F, '</div></td>');
      writeln (F, '</tr></table>');
  //  writeln (F, '<div class="header_3">[#'+IntTostr(i)+'] - '+CaptionsList[index-1]+'</div>'); //old
  // конец - заголовок элемента поиска в виде таблицы -
     if Pos ('<div class="citation_block">',S)>0
      then writeln (F, S,'<hr>')
      else
        begin
         writeln (F, '<div class="comments">');
         writeln (F, '<div class="comment_item" id="comment_1">');
         writeln (F, '<span class="comment_number"');
         writeln (F, 'title="'+S2+'"></span>');
         writeln (F, '<span class="comment_text">');
         writeln (F, S);
//         {!}   if i<=5000 then writeln (F, S) else writeln (F, 'Превышен лимит кол-ва записей');
         writeln (F, '</span></div></div>');
         writeln (F, '<div class="clear"></div>');
         writeln (F, '<hr>');
        end;
     S2_Old:=S2;
    end;
 // концовка HTML
 writeln (F, '<!-- Insert code block end -->');
 writeln (F, '<script type="text/javascript" src="./src/scripts/jquery-3.6.0.min.js"></script>');
 writeln (F, '<script type="text/javascript" src="./src/scripts/clipboard.min.js"></script>');
 writeln (F, '<script type="text/javascript" src="./src/scripts/clicktoquote.js"></script>');
 writeln (F, '<script type="text/javascript" src="./src/scripts/selection.js"></script>');
 writeln (F, '<textarea readonly="" style="font-size: 12pt; border: 0px; padding: 0px; margin: 0px; position: absolute; left: -9999px; top: 1300px;"></textarea>');
 writeln (F, '</body></html>');
//освобождение памяти
 CloseFile(F);
 CaptionsList.Free;
end;


procedure TAbstractThread.FindText;
var
 i:integer;
 FindList:TStringList;
 FindListCount:integer;
 STextToFind,PeriodStr:string;
 FileStrCount:Integer;
begin
 SetLength(FoundSourcesArr,FileNamesList.Count);
 for i:=1 to FilesList.Count do FoundSourcesArr[i-1]:=0;
 T1:=Now;
 MinValue:=1;
 MaxValue:=0;
 CurValue:=0;
 FindList:=TStringList.Create;
 FindList.Clear;
 sTextToFind:=pSearchString;
 // подсчет кол-ва всех поисковых строк для правильной выдачи %

 for i:=1 to FileNamesList.Count do if (bFilesStatusArr[i-1]) then
  begin
   FileStrCount:=IniFile.ReadInteger('Number of lines',FileNamesList[i-1], 1);
   MaxValue:=MaxValue+FileStrCount;
  end;
 //------------
 for i:=1 to FilesList.Count do if (bFilesStatusArr[i-1])and not bAborted
  then
   begin
    FindListCount:=FindList.Count;
    ScanFile2 (i,sTextToFind, FindList);   // основная процедура поиска
    if FindList.Count>FindListCount then FoundSourcesArr[i-1]:=FindList.Count-FindListCount;
    if FindList.Count>iRecordLimit then break;
   end;
 T2:=Now;
 PeriodStr:=IntToStr(SecondsBetween(T1, T2))+' cек.';
 if FindList.Count>=0 then
  begin
   HTMLFileName:=ProjectFilePath+GetValidFileName(pSearchString)+'-'+IntToStr(FindList.Count)+'.html';
   HTMLFileName:=GetUniqueFileName(HTMLFileName);
   CreateEmptyFile(HTMLFileName);
   MakeHTML_From_FindList(FindList);
   MainForm.ListView.Items[ListBoxIndex].SubItems[0]:=ExtractFileName(HTMLFileName);
   MainForm.ListView.Items[ListBoxIndex].SubItems[1]:=MainForm.ListView.Items[ListBoxIndex].SubItems[1];
   MainForm.ListView.Items[ListBoxIndex].SubItems[2]:=IntToStr(FindList.Count);
   if MainForm.CB_AutoBrowse.Checked Then RunHTML (HTMLFileName);
  end;
 FindList.Free;
end;
(*
procedure TAbstractThread.ScanFile(FileNum:integer; AText: string;
    var AFindList: TStringList);

var
 F1,F2:textFile;
 S,S2,SubStr,Str:string;
 FirstStr,H1Str:string;
 PosH1_Tag,PosH1_TagEnd:integer;
 shortFN:string;
 i,j,l, Pos_Comment:integer;
 Caption:string;
 AFileName:string;
 LastLinkID:string;
 label 10;
begin
 AFileName:=FilesList[FileNum-1];
 shortFN:=ExtractFileName(AFileName);
 AssignFile(F1,AFileName);
 Reset(F1);
 AssignFile(F2,ChangeFileExt(AFileName,'.no_tags'));
 //{!} AssignFile(F2,AFileName);
 Reset(F2);
 H1Str:='';
 readln(F2,FirstStr);
 readln(F1,FirstStr);
 FirstStr:=FormatFileInfo(FirstStr); // удаление тега комментария
 if not bOptionsCaseSensitive then SubStr:=AnsiLowerCase(AText) else SubStr:=AText;
 i:=1;
// StatusBar.Panels[0].Text:=FirstStr;
  repeat
   if bAborted then break;
   inc(i);
   readln(F1,S);
   readln(F2,S2);
   inc(CurValue);
   PosH1_Tag:=Pos ('<H1>',S);
   PosH1_TagEnd:=Pos ('</H1>',S);
   j:=Pos('id=', S);
//   j:=LastPos('id=',S);
   LastLinkID:=GetIDStr(S,j);
   if PosH1_Tag>0 then H1Str:=Copy(S,PosH1_Tag+4,PosH1_TagEnd-PosH1_Tag-4);
   if not bOptionsCaseSensitive then Str:=AnsiLowerCase(S2) else Str:=S2;
   //пропуск если заглавие
   if Pos('<head>',S)>0 then continue;
//   if Pos('<div class="chapter_title"',S)>0 then continue; {убрал}
   //вырезание концовки
   j:=Pos('<span class="endchapter">',S);
   if j>0 then Delete(S,j,Length (S));
   //добавление в список, если найдено
   10: //--------------------------
   j:=PosSubstringInString(SubStr,Str);
   l:=Length(SubStr);
   if H1Str <> '' then Caption:=H1Str+' / '+FirstStr else Caption:=FirstStr;
   if (j>0) then
    begin
     // если опция "слово целиком" не выбрана, то добавляем
     if not bOptionsWholeWord then AFindList.Add(Concat(IntToStr(FileNum),#9,Caption,#9,LastLinkID,#9,S))
     // если опция "слово целиком" выбрана
      else
       begin
        if IsWholeWord(Substr,Str)
         then AFindList.Add(Concat(IntToStr(FileNum),#9,Caption,#9,LastLinkID,#9,S))
         else begin delete (Str,j,l); goto 10 end;
       end;
    end;
    FindCount:=AFindList.Count;
    ShowProgress;
  until EOF(F1);
  CloseFile(F1);
  CloseFile(F2);
end;                                       *)

procedure TAbstractThread.ScanFile2(FileNum:integer; AText: string;
    var AFindList: TStringList);

var
 S,S2,SubStr,Str:string;
 FirstStr,H1Str:string;
 PosH1_Tag,PosH1_TagEnd:integer;
 i,j,l, Pos_Comment:integer;
 Caption:string;
 LastLinkID:string;
 CurDataList, CurDataListNT:TStringList;
begin
 CurDataList:=FilesData[FileNum-1];
 CurDataListNT:=FilesData_notags[FileNum-1];
 H1Str:='';
 FirstStr:=CurDataList[0];
 FirstStr:=FormatFileInfo(FirstStr); // удаление тега комментария
 if not bOptionsCaseSensitive then SubStr:=AnsiLowerCase(AText) else SubStr:=AText;
 for i:=2 to CurDataList.Count do
  begin
   if bAborted then break;
   S:=CurDataList[i-1];
   S2:=CurDataListNT[i-1];
   inc(CurValue);
   PosH1_Tag:=Pos ('<H1>',S);
   PosH1_TagEnd:=Pos ('</H1>',S);
   j:=Pos('id=', S);
//   j:=LastPos('id=',S);
   LastLinkID:=GetIDStr(S,j);
   if PosH1_Tag>0 then H1Str:=Copy(S,PosH1_Tag+4,PosH1_TagEnd-PosH1_Tag-4);
   if not bOptionsCaseSensitive then Str:=AnsiLowerCase(S2) else Str:=S2;
   if not bOptionsCaseSensitive then Str:=AnsiLowerCase(S) else Str:=S;
   //пропуск если заглавие
   if Pos('<head>',S)>0 then continue;
//   if Pos('<div class="chapter_title"',S)>0 then continue; {убрал}
   //вырезание концовки
   j:=Pos('<span class="endchapter">',S);
   if j>0 then Delete(S,j,Length (S));
   //добавление в список, если найдено
   j:=PosSubstringInString(SubStr,Str);
   l:=Length(SubStr);
   if H1Str <> '' then Caption:=H1Str+' / '+FirstStr else Caption:=FirstStr; // перепроверить
   if (j>0) then AFindList.Add(Concat(IntToStr(FileNum),#9,Caption,#9,LastLinkID,#9,S));// передаем исходную строку, а не со снятыми тегами
   FindCount:=AFindList.Count;
   ShowProgress;
   if FindCount>iRecordLimit then break;
  end;
end;



initialization
ThreadList:=TList.Create;
ProjectFilePath:=ExtractFileDir(ParamStr(0))+'\Search\';
DefProjectFileName:=ExtractFileDir(ParamStr(0))+'\Search\'+ChangeFileExt(ExtractFileName(ParamStr(0)),'.whf');
ProcessorCount:=GetProcessorCount;
iRecordLimit:=5000;

finalization;
ThreadList.Free;

end.


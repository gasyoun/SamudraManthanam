{%BuildWorkingDir C:\DELPHI\Lazarus\Index}
unit u_Index;

{$MODE Delphi}

interface

uses
  LCLIntf, LCLType, Messages, SysUtils, Variants, Classes, Graphics, Controls,
  Forms, Dialogs, StdCtrls, ComCtrls, Menus, ExtCtrls, CheckLst, Buttons, Grids,
  PairSplitter, IpHtml, Windows, IniFiles, fSources, uTypes, RegExpr;
  { TMainForm }
type
  TOptions = record
    ProcessMemoFromEnd:boolean;
  end;

type
   TTOCItem=record
          Name:string;
          Pos1:integer;
          Pos2:integer;
         end;
  TMainForm = class(TForm)
    CB_AutoBrowse: TCheckBox;
    CB_CaseSensitive: TCheckBox;
    CB_RegEx: TCheckBox;
    CB_WholeWord: TCheckBox;
    ImageList1: TImageList;
    ImageList2: TImageList;
    Label2: TLabel;
    Label3: TLabel;
    ListView: TListView;
    Memo1: TMemo;
    MenuItem1: TMenuItem;
    AbortMenuItem: TMenuItem;
    Find2MenuItem: TMenuItem;
    Corpus_HTML_To_CSVMenuItem: TMenuItem;
    BTRMenuItem: TMenuItem;
    CorpusStatItem: TMenuItem;
    MenuItem10: TMenuItem;
    MenuItem11: TMenuItem;
    MenuItem12: TMenuItem;
    MenuItem13: TMenuItem;
    UpdateMenuItem: TMenuItem;
    PairSplitter1: TPairSplitter;
    PairSplitterSide2: TPairSplitterSide;
    ReplaceDialog1: TReplaceDialog;
    Separator4: TMenuItem;
    Separator1: TMenuItem;
    SourcesMenu: TMenuItem;
    SourcesMenuItem: TMenuItem;
    MenuItem2: TMenuItem;
    FindMenuItem: TMenuItem;
    DirMenuItem: TMenuItem;
    DiffMenuItem: TMenuItem;
    DelTagsMenuItem: TMenuItem;
    LineCountsMenuItem: TMenuItem;
    CleatListMenuItem: TMenuItem;
    AddItemToMemo: TMenuItem;
    MenuItem3: TMenuItem;
    MenuItem4: TMenuItem;
    MenuItem6: TMenuItem;
    MenuItem7: TMenuItem;
    MenuItem8: TMenuItem;
    Panel5: TPanel;
    Panel8: TPanel;
    Panel9: TPanel;
    ToolBarMenuItem: TMenuItem;
    ToolButton9: TToolButton;
    VidMenuItem: TMenuItem;
    SaveDialog2: TSaveDialog;
    SaveListMenuItem: TMenuItem;
    MenuItem5: TMenuItem;
    Separator3: TMenuItem;
    PopupMenu1: TPopupMenu;
    Separator2: TMenuItem;
    Panel2: TPanel;
    Panel3: TPanel;
    RegExMenuItem: TMenuItem;
    SaveDialog1: TSaveDialog;
    SaveProjectMenuItem: TMenuItem;
    OpenProjectMenuItem: TMenuItem;
    OpenFileMenuItem: TMenuItem;
    MenuItem9: TMenuItem;
    MainMenu1: TMainMenu;
    OpenDialog1: TOpenDialog;
    StatusBar: TStatusBar;
    ToolBar1: TToolBar;
    ToolButton1: TToolButton;
    ToolButton2: TToolButton;
    ToolButton3: TToolButton;
    ToolButton4: TToolButton;
    ToolButton5: TToolButton;
    ToolButton6: TToolButton;
    ToolButton7: TToolButton;
    ToolButton8: TToolButton;
    procedure AddItemToMemoClick(Sender: TObject);
    procedure BTRMenuItemClick(Sender: TObject);
    procedure Button1Click(Sender: TObject);
    procedure Button2Click(Sender: TObject);
    procedure CorpusStatItemClick(Sender: TObject);
    procedure Corpus_HTML_To_CSVMenuItemClick(Sender: TObject);
    procedure DelTagsMenuItemClick(Sender: TObject);
    procedure DirMenuItemClick(Sender: TObject);
    procedure FindButtonClick(Sender: TObject);
    procedure FormShow(Sender: TObject);
    procedure Label1Click(Sender: TObject);
    procedure ListViewDblClick(Sender: TObject);
    procedure Memo1Change(Sender: TObject);
    procedure Memo1KeyDown(Sender: TObject; var Key: Word; Shift: TShiftState);
    procedure Find2MenuItemClick(Sender: TObject);
    procedure MenuItem11Click(Sender: TObject);
    procedure MenuItem12Click(Sender: TObject);
    procedure MenuItem13Click(Sender: TObject);
    procedure UpdateMenuItemClick(Sender: TObject);
    procedure MenuItem3Click(Sender: TObject);
    procedure MenuItem6Click(Sender: TObject);
    procedure MenuItem7Click(Sender: TObject);
    procedure MenuItem8Click(Sender: TObject);
    procedure Panel10Click(Sender: TObject);
    procedure ReplaceDialog1Replace(Sender: TObject);
    procedure SourcesMenuClick(Sender: TObject);
    procedure ToolBarMenuItemClick(Sender: TObject);
    procedure SaveListMenuItemClick(Sender: TObject);
    procedure MenuItem5Click(Sender: TObject);
    procedure Panel2Click(Sender: TObject);
    procedure RegExMenuItemClick(Sender: TObject);
    procedure OpenHTMLBtnClick(Sender: TObject);
    procedure OpenHTMLBtnKeyDown(Sender: TObject; var Key: Word; Shift: TShiftState);
    procedure ClearBtnClick(Sender: TObject);
    procedure SaveProjectMenuItemClick(Sender: TObject);
    procedure ShowDirBtnClick(Sender: TObject);
    procedure SoursesBtnClick(Sender: TObject);
    procedure AbortBtnClick(Sender: TObject);
    procedure FindBtnClick(Sender: TObject);
    procedure LineCountsBtnClick(Sender: TObject);
    procedure Button9Click(Sender: TObject);
    procedure CB_CaseSensitiveChange(Sender: TObject);
    procedure FormDestroy(Sender: TObject);
    procedure ListBox2Click(Sender: TObject);
    procedure CheckGroup1Click(Sender: TObject);
    procedure FormClose(Sender: TObject; var CloseAction: TCloseAction);
    procedure FormCreate(Sender: TObject);
    procedure ListBox2KeyDown(Sender: TObject; var Key: Word; Shift: TShiftState);
    procedure StatusBarClick(Sender: TObject);
    procedure ToolButton9Click(Sender: TObject);
    procedure LoadAllFiles;
    procedure FreeAllFiles;
    procedure CheckRegEx;

  private
  SearchWordList:TStringList;// если ищем больше одного слова
  SavedListFileName:string;
  WhatFindFileName:string;
  bBreak:boolean;
  sTextToFind:string;
  bOptionsCaseSensitive:boolean;
  bOptionsWholeWord:boolean;
  HTMLFileName:string;
  OtherSymbols:Set of Char;
  PeriodStr:string;
  CurPercent, OldPercent:integer;
  bFilesLoaded:boolean;
  procedure DelFirstMemoElm;
  function GetFirstMemoElm: string;
  procedure ShowProgress(MinValue, MaxValue, CurValue: integer);

    { Private declarations }
  public
  procedure IdleAction( Sender:TObject;var Done:boolean);
  Procedure FillSourcesGroupsCLB;
  Procedure SaveOptions;
  Procedure LoadOptions;
//  procedure FindText(AText_To_Find: string);
//  Procedure MakeHTML_From_FindList(Const AFindList:TStringList);
  Procedure LoadFilesInfo;
  Function IsWholeWord(Substr,Str:string):boolean;
  Procedure DelHTMLTagsFromFile (AFileName:string);
  procedure OptimizeThreads;
  procedure ListViewItemsLoadFromFile (AFileName:string);
  procedure ListViewItemsSaveToFile (AFileName:string);
  Procedure ListViewLoadSearchFilesFromDir (ADir:string);
  Procedure CompressMemo;
  Procedure SetVersionInfo;
  Procedure UpdateListView;
  Procedure SaveListView (AFileName:string);
  Procedure CopyListView;
  Procedure UpdateSourcesMenuItems;
  procedure SourcesMenuItemClick(Sender: TObject);
  procedure AllSourcesExclude;
  procedure AllSourcesInclude;
  procedure ShowSourcesStatus;
  procedure ConvertCorpus_HTML_To_CSV(AFileName:string);
  procedure RaplaceTextInFile(AFileName,TextToFind,TextToReplace:string);


    { Public declarations }
  end;

procedure RunHTML(AFileName: string);

var
  MainForm: TMainForm;
  IniFile:TIniFile;
  FilesList:TStringList;
  FileNamesList:TStringList;
  FilesInfoList:TStringList;
  bFilesStatusArr:TBoolArr; //выбран или нет для поиска
  bAbortedAll:boolean;
  TOCItems:array of TTOCItem;
  Options:TOptions;
implementation
 Uses clipbrd, StrUtils, textu, _winutils, dateutils, uAbstractThread, lazUTF8, u_Words, UpdateChecker, uUpdateForm;

{$R *.lfm}

{ TMainForm }

procedure TMainForm.FormCreate(Sender: TObject);
var
 i:integer;
begin
 bFilesLoaded:=False;
 SetVersionInfo;
 FilesList:=TStringList.Create;
 FileNamesList:=TStringList.Create;
 FilesInfoList:=TStringList.Create;
 IniFile:=TIniFile.Create((ExtractFileDir(ParamStr(0))+'\Programdata\program.ini'));
 LoadOptions;
 WhatFindFileName:=ChangeFileExt(ParamStr(0),'.whf');
 if FileExists(WhatFindFileName) then Memo1.Lines.LoadFromFile(WhatFindFileName);
 SavedListFileName:=ChangeFileExt(ParamStr(0),'.sres');
 if FileExists(SavedListFileName)
   then ListViewItemsLoadFromFile(SavedListFileName)
   else ListViewLoadSearchFilesFromDir(ProjectFilePath);
 FileNamesList.LoadFromFile(ExtractFileDir(ParamStr(0))+'\Programdata\data.txt');
 for i:=1 to FileNamesList.Count do
   FilesList.Add(ExtractFileDir(ParamStr(0))+'\Data\'+FileNamesList[i-1]);
 LoadFilesInfo;
 ShowSourcesStatus;
// UpdateSourcesMenuItems;
 DiffMenuItem.Visible:=FileExists(ChangeFileExt(ParamStr(0),'.dbg'));
 SearchWordList:=TStringList.Create;
// Application.OnIdle:= IdleAction;
 CheckRegEx;
 CheckUpdaterVersion;
end;

procedure TMainForm.CheckGroup1Click(Sender: TObject);
begin

end;

procedure TMainForm.FormClose(Sender: TObject; var CloseAction: TCloseAction);
begin
// ListBox2.Items.SaveToFile(SavedListFileName);
 ListViewItemsSaveToFile(SavedListFileName);
 Memo1.Lines.SaveToFile(WhatFindFileName);
 SaveOptions;
 IniFile.Free;
 FilesInfoList.Free;
 FilesList.Free;
 FileNamesList.Free;
end;

procedure TMainForm.OpenHTMLBtnClick(Sender: TObject);
var
 FileName:string;
begin
 if ListView.Selected=nil then begin MessageDlg('Ошибка','Нет источников для открытия!',mtError,[mbOk],0); exit end;
 if Pos('%',ListView.Selected.Caption)>0 then begin MessageDlg('Ошибка','Поиск еще на окончен для этого слова!',mtError,[mbOk],0); exit end;
 FileName:=ProjectFilePath+ListView.Selected.SubItems[0];
 if not FileExists(FileName) then MessageDlg('Ошибка','Файл не найден!',mtError,[mbOk],0);
 RunHTML(FileName);
end;

procedure TMainForm.Button1Click(Sender: TObject);
begin
end;

procedure TMainForm.AddItemToMemoClick(Sender: TObject);
var
 i:integer;
begin
   for i := 1 to ListView.Items.Count  do
   begin
     if ListView.Items[i-1].Selected then
      Memo1.Lines.Add(ListView.Items[i-1].Caption);
   end;
end;

procedure TMainForm.BTRMenuItemClick(Sender: TObject);
var
 i:integer;
begin
  if not (OpenDialog1.Execute) then exit;
  if not ReplaceDialog1.Execute then exit;
end;


procedure TMainForm.Button2Click(Sender: TObject);
 begin
end;

procedure TMainForm.CorpusStatItemClick(Sender: TObject);
var
 Pos_begin,Pos_end,i,j:integer;
 ShlocasList:TStringList;
 SubStr, Str, AFindText:string;
begin
 if not DefaultInputDialog('Search','Text',False,SubStr) then exit;
 ShlocasList:=TStringList.Create;
 for i:=1 to FilesList.Count do
 begin
   ShowProgress(1, FilesList.Count, i);
   for j:=1 to FilesData[i-1].Count do
   begin
    Str:=FilesData[i-1][j-1];
    Pos_begin:= Pos(SubStr,Str);
    if Pos_begin>0 then
     begin
       Delete(Str,1,Pos_begin-1);
       Pos_end:=Pos('</div>',Str);
       AFindText:=Copy(Str,Length(SubStr)+1,Pos_end-1);
       ShlocasList.Add(AFindText);
     end;
   end;
 end;
 ShlocasList.SaveToFile(ChangeFileExt(ParamStr(0),'_stat.txt'));
 ShlocasList.Free;
end;

procedure TMainForm.Corpus_HTML_To_CSVMenuItemClick(Sender: TObject);
var
 i:integer;
begin
  if not (OpenDialog1.Execute) then exit;
  for i:=1 to OpenDialog1.Files.Count do
  begin
   ConvertCorpus_HTML_To_CSV(OpenDialog1.Files[i-1]);
   StatusBar.Panels[0].Text:=ExtractFileName (OpenDialog1.Files[i-1]);
   StatusBar.Refresh;
  end;
  StatusBar.Panels[0].Text:='OK!';
end;

procedure TMainForm.DelTagsMenuItemClick(Sender: TObject);
 var
 i:integer;
 begin
   If not OpenDialog1.Execute then exit;
   for i:=1 to OpenDialog1.Files.Count do
    begin
     DelHTMLTagsFromFile(OpenDialog1.Files[i-1]);
    end;
 end;

procedure TMainForm.DirMenuItemClick(Sender: TObject);
begin

end;

procedure TMainForm.FindButtonClick(Sender: TObject);
begin

end;

procedure TMainForm.FormShow(Sender: TObject);
begin
  if not bFilesLoaded then
  begin
   LoadAllFiles;
   bFilesLoaded:=True;
  end;
end;


procedure TMainForm.Label1Click(Sender: TObject);
begin

end;

procedure TMainForm.ListViewDblClick(Sender: TObject);
begin
 OpenHTMLBtnClick(Sender)
end;

procedure TMainForm.Memo1Change(Sender: TObject);
begin

end;

procedure TMainForm.Memo1KeyDown(Sender: TObject; var Key: Word;
  Shift: TShiftState);
begin
  if Key=vk_F7 then
  begin
   FindBtnClick(Sender)
  end;
end;

procedure TMainForm.Find2MenuItemClick(Sender: TObject);
begin
 ManyWordsDialog:=TManyWordsDialog.Create(Owner);
 if ManyWordsDialog.ShowModal=mrOk then
 begin
  Memo1.Lines.Insert(0,ManyWordsDialog.RegexStr);
  SearchWordList.Add(ManyWordsDialog.Edit1.Text);
  SearchWordList.Add(ManyWordsDialog.Edit2.Text);
  CB_RegEx.Checked:=True;
  FindBtnClick(Sender);
 end;
 ManyWordsDialog.Free;
end;

procedure TMainForm.MenuItem11Click(Sender: TObject);
begin
 AllSourcesInclude;
 ShowSourcesStatus;
end;

procedure TMainForm.MenuItem12Click(Sender: TObject);
begin

end;

procedure TMainForm.MenuItem13Click(Sender: TObject);
begin
 AllSourcesExclude;
 ShowSourcesStatus;
end;

procedure TMainForm.UpdateMenuItemClick(Sender: TObject);
begin
 CheckForUpdates;
end;
procedure TMainForm.MenuItem3Click(Sender: TObject);
begin
  ClearBtnClick(Sender)
end;

procedure TMainForm.MenuItem6Click(Sender: TObject);
begin
  CopyListView;
end;

procedure TMainForm.MenuItem7Click(Sender: TObject);
 var
  i,j,k:integer;
  List:TStringList;
  LettersList:TStringList;
  S, S_Info, S_Letter:string;
 begin
   if not OpenDialog1.Execute then  exit;
   List:=TstringList.Create;
   LettersList:=TstringList.Create;
   LettersList.Sorted:=True;
   LettersList.Clear;
   for i:=1 to OpenDialog1.Files.Count do
    begin
     List.Clear;
     List.LoadFromFile(OpenDialog1.Files[i-1]);
     For j:=1 to List.Count do
      begin
       S:=List[j-1];
       for k:=1 to Utf8Length(S) do
        begin
          S_Letter:=UTF8Copy(S,k,1);
          LettersList.Add(S_Letter);
        end;
      end;
     S_Info:=IntToStr(i)+'/'+IntToStr(OpenDialog1.Files.Count);
     if StatusBar.Panels[0].Text<>S_Info then StatusBar.Panels[0].Text:=S_Info;
     StatusBar.Refresh;
     Application.ProcessMessages;
    end;
   List.Free;
   LettersList.SaveToFile(ChangeFileExt(ParamStr(0),'.symbols'));
 end;

procedure TMainForm.MenuItem8Click(Sender: TObject);
 var
  i:integer;
  S:string;
  F,F2:textFile;
  Fn1:TFileName;
  Fn2:TFileName;
begin
 for i:=1 to FilesList.Count do
  begin
   FN1:=ChangeFileExt(FilesList[i-1],'.no_tags');
   FN2:=ExtractFilePath(FN1)+'_'+ExtractFileName(FN1);
   AssignFile(F,FN1);
   Reset(F);
   AssignFile(F2,FN2);
   Rewrite(F2);
   Readln(F,S);
   S:='<!-- '+S+' --!>';
   writeln(F2,S);
   repeat
    Readln(F,S);
    writeln(F2,S)
   until EOF(F);
   StatusBar.Panels[0].Text:=FilesList[i-1];
   StatusBar.Refresh;
   CloseFile(F);
   CloseFile(F2);
  end;
end;

procedure TMainForm.Panel10Click(Sender: TObject);
begin

end;

procedure TMainForm.ReplaceDialog1Replace(Sender: TObject);
 var
  i:integer;
 begin
   for i:=1 to OpenDialog1.Files.Count do
   begin
    RaplaceTextInFile(OpenDialog1.Files[i-1],ReplaceDialog1.FindText,ReplaceDialog1.ReplaceText);
    StatusBar.Panels[0].Text:=ExtractFileName (OpenDialog1.Files[i-1]);
    StatusBar.Refresh;
   end;
   StatusBar.Panels[0].Text:='OK!';
 end;

procedure TMainForm.SourcesMenuClick(Sender: TObject);
begin
  UpdateSourcesMenuItems;
end;



procedure TMainForm.ToolBarMenuItemClick(Sender: TObject);
begin
  ToolBar1.Visible:=not ToolBar1.Visible;
end;

procedure TMainForm.SaveListMenuItemClick(Sender: TObject);
begin
 If ListView.Items.Count =0 then
 begin
  MessageDlg('Ошибка','Список пуст! Экспорт невозможен!',mtError,[mbOk],0);
  exit;
 end;
 if SaveDialog2.Execute then
 begin
  SaveListView(SaveDialog2.FileName);
  RunHTML(SaveDialog2.FileName);
 end;
end;

procedure TMainForm.MenuItem5Click(Sender: TObject);
begin
end;

procedure TMainForm.Panel2Click(Sender: TObject);
begin

end;

procedure TMainForm.RegExMenuItemClick(Sender: TObject);
 var
   Regex: TRegExpr;
   Sentence: string;

 begin
   Regex := TRegExpr.Create;
   Regex.Expression := '^.*\bВася\b(?!\s+\bПетя\b).*$';

   Sentence := 'Здесь есть Вася, но нет Пети.';
   if Regex.Exec(Sentence) then
     ShowMessage(Sentence);

   Sentence := 'А здесь есть и Вася, и Петя.';
   if Regex.Exec(Sentence) then
     ShowMessage(Sentence);

   Regex.Free;
end;


procedure TMainForm.OpenHTMLBtnKeyDown(Sender: TObject; var Key: Word;
  Shift: TShiftState);
begin

end;

procedure TMainForm.ClearBtnClick(Sender: TObject);
begin
// ListBox2.Clear;
 ListView.Items.Clear;
 DeleteFilesFromDir(ExtractFileDir(ParamStr(0))+'\Search\','*.*');
 ThreadList.Clear;
end;

procedure TMainForm.SaveProjectMenuItemClick(Sender: TObject);
begin
  SaveDialog1.FileName:=ProjectFileName;
  If SaveDialog1.Execute then
   ProjectFileName:=SaveDialog1.FileName;
end;

procedure TMainForm.ShowDirBtnClick(Sender: TObject);
var
 S,AFileName:string;
begin
 if ListView.Selected=nil then S:='' else S:=ListView.Selected.SubItems[0];
 AFileName:=ProjectFilePath+S;
 if s<>''
   then ShellExecuteW(0, nil, 'explorer.exe', PWideChar(UTF8Decode('/select,'+AFileName)), nil, SW_SHOWNORMAL)
   else ShellExecuteW(0, nil, 'explorer.exe', PWideChar(UTF8Decode('/view,'+AFileName)), nil, SW_SHOWNORMAL);
end;

procedure TMainForm.SoursesBtnClick(Sender: TObject);
begin
  SourcesForm:=TSourcesForm.Create(Owner);
  if SourcesForm.ShowModal=mrOk then
   begin
     UpdateSourcesMenuItems;
     ShowSourcesStatus;
   end;
  SourcesForm.Free;
end;

procedure TMainForm.AbortBtnClick(Sender: TObject);
var
  j:integer;
begin
 bAbortedAll:=True;
 for j:=ThreadList.Count downto 1 do
   if ThreadList [j-1]<>nil then
  TAbstractThread(ThreadList [j-1]).bAborted:=True;
end;
// выдает первый элемент в зависимости от настройки (сначала или с конца)
Function TMainForm.GetFirstMemoElm:string;
begin
 if Options.ProcessMemoFromEnd
   then result:=Memo1.Lines[Memo1.Lines.Count-1]
   else result:=Memo1.Lines[0];
end;
// удаляет первый элемент в зависимости от настройки (сначала или с конца)
procedure TMainForm.DelFirstMemoElm;
begin
 if Options.ProcessMemoFromEnd
   then Memo1.Lines.Delete(Memo1.Lines.Count-1)
   else Memo1.Lines.Delete(0);
end;

procedure TMainForm.FindBtnClick(Sender: TObject);
var
 AT:TAbstractThread;
 i,j, ind:integer;
 ToDoCount:integer;
 T1:TDateTime;
begin
 T1:=Now;
 ToDoCount:=Memo1.Lines.Count;
 CompressMemo;
 if (Memo1.Lines.Count=0) then
  if (ListView.Items.Count=0) then exit
   else Memo1.Lines.Add(ListView.Items[0].Caption);
 OptimizeThreads;
 bAbortedAll:=False;
 repeat
  if bAbortedAll then break;
  OptimizeThreads;
  if ThreadList.Count>=ProcessorCount then begin Application.ProcessMessages; continue; end;
  AT:=TAbstractThread.Create(True);
//  AT.pSearchString:=Memo1.Lines[0];
  AT.pSearchString:=GetFirstMemoElm;
  AT.bFilesStatusArr:=Copy(bFilesStatusArr,0,Length(bFilesStatusArr));
  AT.bOptionsCaseSensitive:=CB_CaseSensitive.Checked;
  AT.bOptionsWholeWord:=CB_WholeWord.Checked;
  AT.bRegEx:=CB_RegEx.Checked;
  if SearchWordList.Count>0 then begin AT.SearchWordList.AddStrings(SearchWordList);SearchWordList.Clear; end;
//  Memo1.Lines.Delete(0);
  DelFirstMemoElm;
  Memo1.Refresh;
  ListView.Items.Insert(0);
  ListView.Items[0].Caption:=AT.pSearchString;
  ListView.Items[0].SubItems.Add('-');
  ListView.Items[0].SubItems.Add('-');
  ListView.Items[0].SubItems.Add('-');
  ListView.Items[0].SubItems.Add('-');
  AT.ListBoxIndex:=0;
  StatusBar.Panels[0].Text:=IntToStr(ToDoCount-Memo1.Lines.Count) +'/'+IntToStr(ToDoCount);
  //обновление положения в списке
  for j:=1 to ThreadList.Count do if ThreadList[j-1] <>nil then
   begin
    ind:=TAbstractThread(ThreadList[j-1]).ListBoxIndex;
    TAbstractThread(ThreadList [j-1]).ListBoxIndex:=ind+1;
   end;
  ThreadList.Add(AT);
  try
  AT.Resume;
  finally
  end;
  //  обновление списка тредов
 until Memo1.Lines.Count=0;
 OptimizeThreads;
 StatusBar.Panels[0].Text:=StatusBar.Panels[0].Text+' - '+IntToStr(SecondsBetween(T1, Now))+' cек.';
end;

procedure TMainForm.LineCountsBtnClick(Sender: TObject);
var
 i:integer;
 List:TstringList;
begin
  List:=TstringList.Create;
  for i:=1 to FilesList.Count do
   begin
    List.Clear;
    List.LoadFromFile(ChangeFileExt(FilesList[i-1],'.no_tags'));
    IniFile.WriteInteger('Number of lines',ExtractFileName(FilesList[i-1]),List.Count);
    StatusBar.Panels[0].Text:=ExtractFileName(FilesList[i-1]);
    StatusBar.Refresh;
   end;
  List.Free;
end;

procedure TMainForm.Button9Click(Sender: TObject);
begin
end;

procedure TMainForm.CB_CaseSensitiveChange(Sender: TObject);
begin

end;

procedure TMainForm.FormDestroy(Sender: TObject);
begin
 FreeAllFiles;
 SearchWordList.Free;
end;

procedure TMainForm.ListBox2Click(Sender: TObject);
begin

end;




procedure TMainForm.ListBox2KeyDown(Sender: TObject; var Key: Word;
  Shift: TShiftState);
var
 FileName:String;
 i:integer;
begin
  if Key=vk_Delete then
  begin
   ListView.Selected.Delete;
  end;
end;


procedure TMainForm.StatusBarClick(Sender: TObject);
var
  pt: TPoint;
  ImageX, ImageY:integer;
begin
  GetCursorPos(pt);
  pt := StatusBar.ScreenToClient(pt);
  ImageX:=Round(pt.X);
  ImageY:=Round(pt.Y);
  if ImageX>660 then
   ShellExecute(Handle,'open','http://samskrtam.ru/parallel-corpus/',nil,nil,SW_SHOW);
end;

procedure TMainForm.ToolButton9Click(Sender: TObject);
begin

end;

procedure TMainForm.LoadAllFiles;
var
  i:integer;
  S:String;
begin
 StatusBar.Panels[0].Text:='Загрузка базы данных...';
 Setlength(FilesData,FilesList.Count);
 Setlength(FilesData_noTags,FilesList.Count);
 for i:=1 to FilesList.Count do
  begin
   FilesData[i-1]:=TStringList.Create;
   FilesData_noTags[i-1]:=TStringList.Create;
   FilesData[i-1].LoadFromFile(FilesList[i-1]);
   FilesData_noTags[i-1].LoadFromFile(ChangeFileExt(FilesList[i-1],'.no_tags'));
  end;
 StatusBar.Panels[0].Text:='База данных загружена успешно!';
end;

procedure TMainForm.FreeAllFiles;
var
  i:integer;
begin
 for i:=1 to Length(FilesData) do FilesData[i-1].Free;
 Setlength(FilesData,0);
 for i:=1 to Length(FilesData_notags) do FilesData_notags[i-1].Free;
 Setlength(FilesData_notags,0);
end;

procedure TMainForm.CheckRegEx;
var
  RegEx:TRegExpr;
  Str:string;
  Pos:integer;
begin
 // тестирование регулярных выражений
 Regex := TRegExpr.Create;
 try
   Regex.Expression := '/bАрджун';
   Str:='   Арджуна и Арджун шел домой';
  if RegEx.Exec(Str) then
   begin
     Pos:=RegEx.MatchPos[0];
     StatusBar.Panels[0].Text:=IntToStr(Pos);
   end else StatusBar.Panels[0].Text:='Не найдена!'
 finally
   Regex.Free;
 end;
end;

procedure TMainForm.UpdateSourcesMenuItems;
var
   i:integer;
   Sections:TstringList;
   Item:TMenuItem;
   GRPINIFile:TIniFile;
begin
  GRPINIFile:=TIniFile.Create((ExtractFileDir(ParamStr(0))+'\Programdata\program.grp'));
  for i:=1 to SourcesMenu.Count-5 do SourcesMenu.Delete(5);
  Sections:=TstringList.Create;
  GRPINIFile.ReadSections(Sections);
  for i:=1 to Sections.Count do
  begin
   Item:=TMenuItem.Create(self);
   Item.Caption:='Только '+Sections[i-1];
   Item.Tag:=i;
   Item.OnClick:=SourcesMenuItemClick;
   Item.ShortCut:=ShortCut(VK_1+i-1, [ssCtrl]);
   SourcesMenu.Add(Item);
  end;
  Item:=TMenuItem.Create(self);
  Item.Caption:='-';
  Item.Tag:=0;
  Item.OnClick:=nil;
  SourcesMenu.Add(Item);
  for i:=1 to Sections.Count do
  begin
   Item:=TMenuItem.Create(self);
   Item.Caption:='Добавить '+Sections[i-1];
   Item.Tag:=1000+i;
   Item.ShortCut:=ShortCut(VK_1+i-1, [ssCtrl,ssShift]);
   Item.OnClick:=SourcesMenuItemClick;
   SourcesMenu.Add(Item);
  end;
  Sections.Free;
 GRPINIFile.Free;
end;

procedure TMainForm.FillSourcesGroupsCLB;
var
   i:integer;
   Sections:TstringList;
   GRPINIFile:TIniFile;
begin
{  GRPINIFile:=TIniFile.Create((ExtractFileDir(ParamStr(0))+'\Programdata\program.grp'));
  SG_CLB.Clear;
  Sections:=TstringList.Create;
  GRPINIFile.ReadSections(Sections);
  SG_CLB.Items.Add ('Все');
  for i:=1 to Sections.Count do
  begin
   SG_CLB.Items.Add(Sections[i-1]);
  end;
  Sections.Free;
 GRPINIFile.Free;}
end;

procedure TMainForm.SaveOptions;
var
 i:integer;
begin
 IniFile.WriteBool('Common','Case Sensitive',CB_CaseSensitive.Checked);
 IniFile.WriteBool('Common','Whole Word',CB_WholeWord.Checked);
 IniFile.WriteBool('Common','Auto Browse',CB_AutoBrowse.Checked);
 IniFile.WriteBool('Common','RegEx',CB_RegEx.Checked);
 IniFile.WriteString('Common','ProjectFileName',ProjectFileName);
 IniFile.WriteBool('Common','ToolBar',ToolBar1.Visible);
 for i:=1 to Length(bFilesStatusArr) do
   IniFile.WriteBool('Files', ExtractFileName(FilesList[i-1]),bFilesStatusArr[i-1]);
end;

procedure TMainForm.LoadOptions;
var
  List:TStringList;
  i:integer;
  S:string;
begin
 CB_CaseSensitive.Checked:=IniFile.ReadBool('Common','Case Sensitive',False);
 CB_WholeWord.Checked:=IniFile.ReadBool('Common','Whole Word',False);
 CB_AutoBrowse.Checked:=IniFile.ReadBool('Common','Auto Browse',True);
 CB_RegEx.Checked:=IniFile.ReadBool('Common','RegEx',False);
 iRecordLimit:=IniFile.ReadInteger('Common','RecordLimit',iRecordLimit);
 ProjectFileName:=IniFile.ReadString('Common','ProjectFileName',DefProjectFileName);
 ToolBar1.Visible:=IniFile.ReadBool('Common','ToolBar',True);
 If Not FileExists(ProjectFileName) then ProjectFileName:=DefProjectFileName;
 ToolBarMenuItem.Checked:=ToolBar1.Visible;
 List:=TStringList.Create;
 IniFile.ReadSectionValues('FileGroupsForContents',List);
 SetLength(TOCItems,List.Count);
 for i:=1 to List.Count do
  begin
   S:=List[i-1];
   TOCItems[i-1].Name:=CutNextUseDelimiterNoTrim(S,'=');
   TOCItems[i-1].Pos1:=StrToInt(CutNextUseDelimiterNoTrim(S,'-'));
   TOCItems[i-1].Pos2:=StrToInt(S);
  end;
 List.Free;
end;
{
procedure TMainForm.MakeHTML_From_FindList(const AFindList: TStringList);
var
 CaptionsList:TStringList;
 i, index:integer;
 S,S2,S2_Old, S_CurCaption:string;
 CaptionCounts:array of integer;
 F:TextFile;
begin
 CaptionsList:=TStringList.Create;
// CaptionsList.Sorted:=True;
 // создаем список источников
 for i:=1 to AFindList.Count do
  begin
    S:=AFindList[i-1];
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
    Index:=CaptionsList.IndexOf(S2);
    if Index>=0 then inc(CaptionCounts[index]);
  end;
// шапка HTML

 AssignFile(F,HTMLFileName);
 Rewrite(F);
 //заглавие HTML
 writeln (F, '<html><head><title>');
 writeln (F, sTextToFind);
 writeln (F, '</title>');
 writeln (F, '<meta content="text/html; charset=UTF-8" http-equiv="Content-Type" />');
 writeln (F, '<link rel="stylesheet" href="./src/style.css">');
 writeln (F, '<!--');
 writeln (F, '<script type="text/javascript" src="./src/scripts/clicktoquote.js"></script>');
 writeln (F, '-->');
 writeln (F, '<link rel="shortcut icon" href="./src/favicon/question.ico" type="image/x-icon">');
 writeln (F, '<link rel="icon" href="./src/favicon/question.ico" type="image/x-icon">');
 writeln (F, '</head>');
 writeln (F, '<body>');
 writeln (F, '<div class="header header_1">При '+PeriodStr+' пахтании Параллельного санскритско-русского корпуса<br>для слова „'+sTextToFind+'“ в океане слов найдено '+IntToStr(AFindList.Count)+' записей в '+IntToStr(CaptionsList.Count)+' источниках </div>');

 // оглавление
 writeln (F, '<!-- Insert code block beginning -->');
 writeln (F, '<div class="contents">');
 for i:=1 to CaptionsList.Count do
  begin
   S_CurCaption:=CaptionsList[i-1];
   writeln (F, '<div class="content_item_big"><div class="content_title"><a href="#chapter_'+IntTostr(i)+'">'+IntTostr(i)+'. '+CutNextUseDelimiterNoTrim(S_CurCaption,';') +'</a>'+S_CurCaption+' ('+IntToStr(CaptionCounts[i-1])+' записей)</div></div>');
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
   if S2<>S2_old then
   begin
    inc(index);
    writeln (F, '<div class="chapter_title" id="chapter_'+IntToStr(index)+'">'+IntTostr(index)+'. '+CaptionsList[index-1]+'</div> ('+IntToStr(CaptionCounts[index-1])+' записей)<br>');
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
    write (F, '[#'+IntTostr(i)+']');
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
 writeln (F, '<textarea readonly="" style="font-size: 12pt; border: 0px; padding: 0px; margin: 0px; position: absolute; left: -9999px; top: 1300px;"></textarea>');
 writeln (F, '</body></html>');
//освобождение памяти
 CloseFile(F);
 CaptionsList.Free;
end;
}
procedure RunHTML(AFileName: string);
var
 F:textfile;
 ATextToFind:string;
begin
    if not FileExists(AFileName) then exit;
    AssignFile(F,AFileName);
    reset(F);
    Readln(F);Readln(F, ATextToFind);
    CloseFile(F);
    OpenDocument(PChar(AFileName)); { *Преобразовано из ShellExecute* }
    Clipboard.AsText:=ATextToFind;
    Sleep (2000);
    keybd_event(VK_CONTROL, MapVirtualKey(VK_CONTROL, 0), 0, 0);
    keybd_event(Ord('F'), MapVirtualKey(Ord('F'), 0), 0, 0);
    keybd_event(Ord('F'), MapVirtualKey(Ord('F'), 0), KEYEVENTF_KEYUP, 0);
    keybd_event(VK_CONTROL, MapVirtualKey(VK_CONTROL, 0), KEYEVENTF_KEYUP, 0);
    Sleep (1000);
    keybd_event(VK_CONTROL, MapVirtualKey(VK_CONTROL, 0), 0, 0);
    keybd_event(Ord('V'), MapVirtualKey(Ord('V'), 0), 0, 0);
    keybd_event(Ord('V'), MapVirtualKey(Ord('V'), 0), KEYEVENTF_KEYUP, 0);
    keybd_event(VK_CONTROL, MapVirtualKey(VK_CONTROL, 0), KEYEVENTF_KEYUP, 0);
    // escape
    keybd_event(VK_ESCAPE, MapVirtualKey(0, 0), 0, 0);
    keybd_event(VK_ESCAPE, MapVirtualKey(0, 0), KEYEVENTF_KEYUP, 0)
end;

procedure TMainForm.LoadFilesInfo;
var
  i:integer;
  F:text;
  S:string;
begin
 FilesInfoList.Clear;
 for i:=1 to FilesList.Count do
  begin
   AssignFile(F, FilesList[i-1]);
   Reset(F);
   readln(F,S);
   CloseFile(F);
   FilesInfoList.Add(FormatFileInfo(S));
  end;
 SetLength(bFilesStatusArr,FilesList.Count);
 for i:=1 to FilesList.Count do
  bFilesStatusArr[i-1]:=IniFile.ReadBool('Files', ExtractFileName(FilesList[i-1]),True);
end;


function TMainForm.IsWholeWord(Substr, Str: string): boolean;
var
  k,l_Str,l_SubStr:integer;
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
  if Str[l_SubStr+1] in OtherSymbols then result:=True;
 end else
 // symb + в конце строки - истина
 if (k+l_SubStr-1=l_Str) and (Str[k-1] in OtherSymbols) then result:=True else
 // иначе в середине строки проверяем слева и справа
 begin
  if (Str[k+l_SubStr] in OtherSymbols) and
     (Str[k-1] in OtherSymbols) then result:=True;
 end;
end;

procedure TMainForm.DelHTMLTagsFromFile(AFileName: string);
var
  F1,F2:text;
  i:integer;
  S1,S2:string;
  t1,t2:TDateTime;
begin
 AssignFile(F1,AFileName);
 AssignFile(F2,ChangeFileExt(AFileName,'.no_tags'));
 Reset(F1);
 Rewrite(F2);
 t1:=Now;
 i:=0;
 Try
 repeat
  inc(i);
  S1:='';
  S2:='';
  readln(F1,S1);
  S2:=RemoveHTMLTags(S1);
  writeln(F2,S2);
 until EOF(F1);
 except
  ShowMessage('Error in the line '+IntToStr(i)+' - '+ExtractFileName(AFileName)+':'+#10#13+S1);
 end;
 CloseFile(F1);
 CloseFile(F2);
 t2:=Now;
 S2:=IntToStr(MilliSecondsBetween(T1, T2))+' милиcек.';
 StatusBar.Panels[0].Text:=ExtractFileName(AFileName)+' - '+S2;
// ListBox2.Items.Add (StatusBar.Panels[0].Text);
 StatusBar.Refresh;
end;

procedure TMainForm.OptimizeThreads;
var
  j:integer;
begin
 if ThreadList.Count=0 then exit;
 for j:=ThreadList.Count downto 1 do
   if TAbstractThread(ThreadList [j-1]).bOk then
   begin
    TAbstractThread(ThreadList [j-1]).Free;
    ThreadList.Delete(j-1);
   end;
end;

procedure TMainForm.ListViewItemsLoadFromFile(AFileName:string);
var
  F:textFile;
  S:string;
  i:integer;
begin
 AssignFile(F,AfileName);
 Reset(F);
 i:=0;
 repeat
  Readln(F,S);
  if Trim(S)='' then break;
  inc(i);
  ListView.Items.Add.Caption:=CutNextUseDelimiterNoTrim(S, #9);
  if Trim(S)<>'' then ListView.Items[i-1].SubItems.Add(CutNextUseDelimiterNoTrim(S, #9)) else ListView.Items[i-1].SubItems.Add(ListView.Items[i-1].Caption+'.html');
  if Trim(S)<>'' then ListView.Items[i-1].SubItems.Add(CutNextUseDelimiterNoTrim(S, #9)) else ListView.Items[i-1].SubItems.Add('-');
  if Trim(S)<>'' then ListView.Items[i-1].SubItems.Add(CutNextUseDelimiterNoTrim(S, #9)) else ListView.Items[i-1].SubItems.Add('-');
  if Trim(S)<>'' then ListView.Items[i-1].SubItems.Add(CutNextUseDelimiterNoTrim(S, #9)) else ListView.Items[i-1].SubItems.Add('-');
 until SeekEOF(F);
 CloseFile(F);
end;

procedure TMainForm.ListViewItemsSaveToFile(AFileName: string);
var
  F:textFile;
  S:string;
  i,j:integer;
begin
 AssignFile(F,AfileName);
 Rewrite(F);
 for i:=1 to ListView.Items.Count do
 begin
  Write(F,ListView.Items[i-1].Caption);
  for j:=1 to ListView.Items[i-1].SubItems.Count do   Write(F,#9,ListView.Items[i-1].SubItems[j-1]);
  Writeln(F);
 end;
 CloseFile(F);
end;

procedure TMainForm.ListViewLoadSearchFilesFromDir(ADir: string);
var
  i:integer;
  HTMLFileList:TStringList;
  S:string;
  F:textFile;
begin
 HTMLFileList:=TStringList.Create;
 GetFilesByMask(ProjectFilePath, '*.html',HTMLFileList);
 ListView.Items.Clear;
 for i:=1 to HTMLFileList.Count do
 begin
   S:=ExtractFileName(ChangeFileExt(HTMLFileList[i-1],''));
   ListView.Items.Add.Caption:='1';
   ListView.Items[i-1].SubItems.Add(S);
   AssignFile(F,HTMLFileList[i-1]);
   Reset(F);
   Readln(F,S);
   Readln(F,S);
   ListView.Items[i-1].Caption:=S;
   CloseFile(F);
 end;
 HTMLFileList.Free;
end;

procedure TMainForm.CompressMemo;
var
 i,j:integer;
 BArr:TBoolArr;
begin
 for i:= Memo1.Lines.Count downto 1 do if Trim(Memo1.Lines[i-1])='' then Memo1.Lines.Delete(i-1);
end;

procedure TMainForm.SetVersionInfo;
begin
 MainForm.Caption:='Пахтанье океана v' + CURRENT_VERSION + ' ("Общества ревнителей санскрита", 2013-'+IntToStr(YearOf(Now))+')';
end;

procedure TMainForm.UpdateListView;
var
 i:integer;
begin
 For i:=1 to ListView.Items.Count do
  ListView.Items[i-1].SubItems[0]:=ListView.Items[i-1].SubItems[0];

end;

procedure TMainForm.SaveListView(AFileName: string);
var
 F:text;
 i:integer;
 Nzap:integer;
begin
 // шапка HTML
  Nzap:=0;
  For i:=1 to ListView.Items.Count do inc(Nzap, StrToInt(ListView.Items[i-1].SubItems[2]));
  AssignFile(F,AFileName);
  Rewrite(F);
  //заглавие HTML
  writeln (F, '<html><head><title>');
  writeln (F, 'Результаты поиска');
  writeln (F, '</title>');
  writeln (F, '<meta content="text/html; charset=UTF-8" http-equiv="Content-Type" />');
  writeln (F, '<link rel="stylesheet" href="Search/src/style.css">');
  writeln (F, '<link rel="shortcut icon" href="./src/favicon/question.ico" type="image/x-icon">');
  writeln (F, '<link rel="icon" href="./src/favicon/question.ico" type="image/x-icon">');
  writeln (F, '</head>');
  writeln (F, '<body>');
  write (F, '<div class="header header_1">');
  write (F, 'При пахтании Параллельного санскритско-русского корпуса<br>');
  write (F, Sklonenie_Naideno_X_zapisey(Nzap)+ Sklonenie_v_N_poiskovyh_zaprosah(ListView.Items.Count));
  writeln (F, '</div>');
//  writeln (F, '<p>Для перехода к предыдущему, ближайшему и слудующему выделению используйте кнопки "<","=",">" или буквы "a","s","d"</p>');
  writeln (F, '<div class="contents">');
  writeln (F, '<!-- Insert code block beginning -->');
  // оглавление
  For i:=1 to ListView.Items.Count do
  begin
   write(F, '<div class="content_item_big">');
   write(F, '<div class="content_title">');
   write (F, '<a href="','Search/');
   write (F, ExtractFileName(ListView.Items[i-1].SubItems[0]) );
   write (F, '" target="_blank">');
   write (F, IntToStr(i)+'. '+ListView.Items[i-1].Caption);
   write (F, '</a>');
   write (F, '</a>');
   //для слова „Бхарата“ в океане слов найдено 693 записей в 66 источниках
   write (F,' (',ListView.Items[i-1].SubItems[2],' записей)');
   writeln (F, '</div></div>');
  end;
 //<a href="my-photo.html">Мои работы</a>
 writeln (F, '</div>'); //class="contents
 writeln (F, '<!-- Insert code block end -->');
 writeln (F, '<textarea readonly="" style="font-size: 12pt; border: 0px; padding: 0px; margin: 0px; position: absolute; left: -9999px; top: 1300px;"></textarea>');
 writeln (F, '</body></html>');
//освобождение памяти
 CloseFile(F);
end;

procedure TMainForm.CopyListView;
var
  i,j:integer;
  S:string;
begin
 S:='';
 S:=ListView.Columns[0].Caption;
 For i:=2 to ListView.Columns.Count do S:=S+#9+ListView.Columns[i-1].Caption;
 S:=S+#13;
 For i:=1 to ListView.Items.Count do
 begin
  S:=S+ListView.Items[i-1].Caption;
   For j:=1 to ListView.Items[i-1].SubItems.Count do S:=S+#9+ListView.Items[i-1].SubItems[j-1];
  S:=S+#13;
 end;
 Clipboard.AsText:=S;
end;

procedure TMainForm.SourcesMenuItemClick(Sender: TObject);
var
  List:TStringList;
  i:integer;
  Index:integer;
  SectionName:string;
  FileName:string;
  GRPINIFile:TIniFile;
begin
  GRPINIFile:=TIniFile.Create((ExtractFileDir(ParamStr(0))+'\Programdata\program.grp'));
  List:=TStringList.Create;
  GRPINIFile.ReadSections(List);
  i:=(Sender as TMenuItem).Tag;
  if i<1000 then AllSourcesExclude else dec(i,1000);
  SectionName:=List[i-1];
  List.Clear;
  GRPINIFile.ReadSection(SectionName,List);
  for i:=1 to List.Count do
  begin
   FileName:=List[i-1];
   index:=FileNamesList.IndexOf(FileName);
   if index>0 then bFilesStatusArr[index]:=True;
  end;
  List.Free;
  GRPINIFile.free;
  ShowSourcesStatus;
end;

procedure TMainForm.AllSourcesExclude;
var
 i:integer;
begin
 for i:=1 to FilesList.Count do bFilesStatusArr[i-1]:=False;
end;

procedure TMainForm.AllSourcesInclude;
var
 i:integer;
begin
 for i:=1 to FilesList.Count do bFilesStatusArr[i-1]:=True;
end;

procedure TMainForm.ShowSourcesStatus;
var
 i,NAct:integer;

begin
 NAct:=0;
 for i:=1 to FilesList.Count do
  if bFilesStatusArr[i-1] then inc(NAct);
 StatusBar.Panels[1].Text:='Выбрано источников: '+IntToStr(NAct)+'/'+IntToStr(FilesList.Count);
end;

function RemoveHTMLTags(const HTMLStr: string): string;
var
  RegEx: TRegExpr;
  i:integer;
  const
  ArrVedic:array [0..12] of String=('á','à', 'é', 'è', 'ì', 'í', 'ó', 'ò', 'ú', 'ù', 'r̥','','');
  ArrNotVedic:array [0..12] of String=('a','a', 'e', 'e', 'i', 'i', 'o', 'o', 'u', 'u', 'ṛ', '', '');
begin
  ArrVedic[11]:=#$0300;  //left acute
  ArrVedic[12]:=#$0301;  //right acute
  RegEx := TRegExpr.Create;
  try
  RegEx.Expression := '<br>'; // Регулярное выражение для поиска текста между <small> и </small>
  RegEx.ModifierG := True; // Включение глобального поиска для всех вхождений
  Result := RegEx.Replace(HTMLStr, ' ', True); // Замена HTML-тегов на пустую строку


  for i:=1 to length(ArrVedic) do
  begin
   RegEx.Expression := ArrVedic[i-1]; // ударение
   RegEx.ModifierG := True; // Включение глобального поиска для всех вхождений
   Result := RegEx.Replace(Result, ArrNotVedic[i-1], True); // Замена HTML-тегов на пустую строку
  end;

  RegEx.Expression := '<small>(.*?)</small>'; // Регулярное выражение для поиска текста между <small> и </small>
  RegEx.ModifierG := True; // Включение глобального поиска для всех вхождений
  Result := RegEx.Replace(Result, '', True); // Замена HTML-тегов на пустую строку

  RegEx.Expression := '<[^>]*>'; // Регулярное выражение для поиска HTML-тегов
  RegEx.ModifierG := True; // Включение глобального поиска для всех вхождений
  Result := RegEx.Replace(Result, '', True); // Замена HTML-тегов на пустую строку
  RegEx.Expression := '  '; //
  Result := RegEx.Replace(Result, ' ', True); //
  Result :=Trim(Result);
  finally
    RegEx.Free;
  end;
end;

procedure TMainForm.ConvertCorpus_HTML_To_CSV(AFileName: string);
 var
  F1,F2:textFile;
  S,S_IAST,S_Rus:string;
  bRusBlock, bIASTBlock:boolean;
 const
  TegIAST='<div class="chapter_block iast">';
  TegRus='<div class="chapter_block translation">';
  TegDIVEnd='</div>';
begin
 AssignFile(F1,AFileName);
 Reset(F1);
 AssignFile(F2,ChangeFileExt(AFileName,'.csv'));
 Rewrite(F2);
 bRusBlock:=False;
 bIASTBlock:=False;
 repeat
  Readln(F1,S);
  S:=Trim(S);
  if (S=TegRus) then begin bRusBlock:=True; S_Rus:=''; continue; end;
  if (S=TegIAST) then begin bIASTBlock:=True; S_IAST:=''; continue;  end;
  if (S=TegDIVEnd) then
   begin
    if bRusBlock then begin writeln (F2,RemoveHTMLTags(S_rus),#9,RemoveHTMLTags(S_IAST));bRusBlock:=False;S_Rus:=''; S_IAST:=''; end;
    if bIASTBlock then begin bIASTBlock:=False; end;
    continue;
   end;
  if bRusBlock then s_Rus:=s_Rus+' '+S;
  if bIASTBlock then S_IAST:=s_IAST+' '+S;
 until EOF(F1);
 CloseFile(F1);
 CloseFile(F2);
end;

procedure TMainForm.RaplaceTextInFile(AFileName, TextToFind,
  TextToReplace: string);
var
 F1,F2:textFile;
 S:string;
begin
 AssignFile(F1,AFileName);
 AssignFile(F2,AFileName+'_');
 Reset(F1);
 Rewrite(F2);
 repeat
  Readln(F1,S);
  if pos(TextToFind,S)<>0 then
   begin
    writeln(F2,TextToReplace);
    writeln(F2,S);
   end else
   begin
    writeln(F2,S);
   end;

 until EOF(F1);
 CloseFile(F1);
 CloseFile(F2);

end;
procedure TMainForm.ShowProgress(MinValue,MaxValue,CurValue:integer);
begin
 if MaxValue-MinValue<=0
  then CurPercent:=100
  else CurPercent:=round((CurValue-MinValue+1)/(MaxValue-MinValue+1)*100);
  if CurPercent>100 then CurPercent:=100;
 if CurPercent<>OldPercent then
  StatusBar.Panels[0].Text:=IntToStr(CurPercent);
 OldPercent:=CurPercent;
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
    UpdateFrm.DestPath  := GetTempDir + 'PO.zip';
    UpdateFrm.ShowModal;
  finally
    UpdateFrm.Free;
  end;
end;

procedure TMainForm.IdleAction(Sender: TObject; var Done: boolean);
begin
 if bFilesLoaded then exit;
 LoadAllFiles;
 bFilesLoaded:=True;
 Done:=True;
end;

Initialization
Options.ProcessMemoFromEnd:=true;
end.

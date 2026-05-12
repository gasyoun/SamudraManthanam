unit fSources;

{$mode delphi}

interface

uses
  Classes, SysUtils, Forms, Controls, Graphics, Dialogs, StdCtrls, ExtCtrls,
  CheckLst, Menus, INIFiles;

type

  { TSourcesForm }

  TSourcesForm = class(TForm)
    Button1: TButton;
    Button2: TButton;
    CheckListBox1: TCheckListBox;
    DelBtn: TButton;
    Label1: TLabel;
    MenuItem1: TMenuItem;
    MenuItem2: TMenuItem;
    N1: TMenuItem;
    Panel1: TPanel;
    Panel2: TPanel;
    Panel3: TPanel;
    Panel4: TPanel;
    PopupMenu1: TPopupMenu;
    PopupMenu2: TPopupMenu;
    SelBtn: TButton;
    SelBtn1: TButton;
    SelBtn2: TButton;
    procedure Button1Click(Sender: TObject);
    procedure Button3Click(Sender: TObject);
    procedure Button4Click(Sender: TObject);
    procedure FormCreate(Sender: TObject);
    procedure FormDestroy(Sender: TObject);
    procedure PopupMenu1Popup(Sender: TObject);
    procedure PopupMenu2Popup(Sender: TObject);
    procedure SelBtn1Click(Sender: TObject);
    procedure DelBtnClick(Sender: TObject);
    procedure SelBtn2Click(Sender: TObject);
    procedure SelBtnClick(Sender: TObject);
  private
    GRPINIFile:TIniFile;
    procedure CreateGroup(AGrpName:string);
    Procedure SelPopupMenuItemClick (Sender: TObject);
    Procedure DelPopupMenuItemClick (Sender: TObject);
  public

  end;

var
  SourcesForm: TSourcesForm;

implementation

{$R *.lfm}
{ TSourcesForm }
Uses
 u_Index, textu;
procedure TSourcesForm.FormCreate(Sender: TObject);
 var
   i:integer;
begin
  GRPINIFile:=TIniFile.Create((ExtractFileDir(ParamStr(0))+'\Programdata\program.grp'));
  for i:=1 to FilesList.Count do
  begin
   CheckListBox1.Items.Add(FilesInfoList[i-1]);
   CheckListBox1.Checked[i-1]:=bFilesStatusArr[i-1];
//   MainForm.bFilesStatusArr
  end;
end;

procedure TSourcesForm.FormDestroy(Sender: TObject);
begin
 GRPINIFile.Free;
end;


procedure TSourcesForm.PopupMenu1Popup(Sender: TObject);
var
   i:integer;
   Sections:TstringList;
   Item:TMenuItem;
begin
  for i:=1 to PopupMenu1.Items.Count-3 do PopupMenu1.Items.Delete(3);
  Sections:=TstringList.Create;
  GRPINIFile.ReadSections(Sections);
  for i:=1 to Sections.Count do
  begin
   Item:=TMenuItem.Create(self);
   Item.Caption:=Sections[i-1];
   Item.Tag:=i;
   Item.OnClick:=SelPopupMenuItemClick;
   PopupMenu1.Items.Add(Item);
  end;
  Sections.Free;
end;

procedure TSourcesForm.PopupMenu2Popup(Sender: TObject);
var
   i:integer;
   Sections:TstringList;
   Item:TMenuItem;
begin
 for i:=1 to PopupMenu2.Items.Count do PopupMenu2.Items.Delete(0);
  Sections:=TstringList.Create;
  GRPINIFile.ReadSections(Sections);
  for i:=1 to Sections.Count do
  begin
   Item:=TMenuItem.Create(self);
   Item.Caption:=Sections[i-1];
   Item.Tag:=i;
   Item.OnClick:=DelPopupMenuItemClick;
   PopupMenu2.Items.Add(Item);
  end;
  Sections.Free;
end;

procedure TSourcesForm.SelBtn1Click(Sender: TObject);
var
  SGrpName:string;
begin
  if InputQuery('Введите название группы','Название', False, SGrpName)
    then CreateGroup(SGrpName);
end;

procedure TSourcesForm.DelBtnClick(Sender: TObject);
begin
  PopupMenu2.PopUp(DelBtn.ClientOrigin.x,DelBtn.ClientOrigin.y+DelBtn.Height);
end;

procedure TSourcesForm.SelBtn2Click(Sender: TObject);
begin
  CopyStringsToClipboard(CheckListBox1.Items);
end;


procedure TSourcesForm.SelBtnClick(Sender: TObject);
begin
  PopupMenu1.PopUp(SelBtn.ClientOrigin.x,SelBtn.ClientOrigin.y+SelBtn.Height);
end;

procedure TSourcesForm.CreateGroup(AGrpName: string);
var
  i:integer;
begin
  GRPINIFile.EraseSection(AGrpName);
  for i:=1 to CheckListBox1.Count do
   if CheckListBox1.Checked[i-1] then
  begin
   GRPINIFile.WriteString(AGrpName, ExtractFileName(FilesList[i-1]),'1');
  end;
end;

procedure TSourcesForm.SelPopupMenuItemClick(Sender: TObject);
var
  List:TStringList;
  i:integer;
  Index:integer;
  SectionName:string;
  FileName:string;
begin
  List:=TStringList.Create;
  GRPINIFile.ReadSections(List);
  SectionName:=List[(Sender as TMenuItem).Tag-1];
  List.Clear;
  GRPINIFile.ReadSection(SectionName,List);
  for i:=1 to List.Count do
  begin
   FileName:=List[i-1];
   index:=FileNamesList.IndexOf(FileName);
   if Index<>-1 then CheckListBox1.Checked[index]:=True;;
  end;
  List.Free;
end;

procedure TSourcesForm.DelPopupMenuItemClick(Sender: TObject);
begin
 GRPINIFile.EraseSection((Sender as TMenuItem).Caption);
end;

procedure TSourcesForm.Button1Click(Sender: TObject);
var
  i:integer;
begin
  for i:=1 to CheckListBox1.Count do
  begin
   bFilesStatusArr[i-1]:=CheckListBox1.Checked[i-1];
   IniFile.WriteBool('Files', ExtractFileName(FilesList[i-1]),bFilesStatusArr[i-1]);
  end;
end;

procedure TSourcesForm.Button3Click(Sender: TObject);
var
  i:integer;
begin
  for i:=1 to CheckListBox1.Count do
  begin
   CheckListBox1.Checked[i-1]:=True;
  end;
end;

procedure TSourcesForm.Button4Click(Sender: TObject);
  var
    i:integer;
  begin
    for i:=1 to CheckListBox1.Count do
    begin
     CheckListBox1.Checked[i-1]:=False;
    end;
  end;

end.


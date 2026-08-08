unit myutils;
{$MODE Delphi}
{ Delphi}
interface
uses mytypes;
procedure Mix ( var Arr:TSingleArr; q :integer );
function IsElmInArr(var Arr:array of integer;q :integer; Elm:integer):boolean;
Procedure FillCharBool(var A:array of boolean;Value:boolean);
Procedure FillCharSingle(var A:array of single;Value:single);
Procedure FillCharInt(var A:array of integer;Value:integer);
function GoToFilePos(var F:textFile; S:string):boolean;
function GoToFilePosS(var F:textFile; S:string):string;
function GetStringFromFile(var F:textFile; ABeginning:string):String;
Procedure PutFile1ToFile2 (AFileName1,AFileName2:string;File2MarkerBegin,File2MarkerEnd:string);
Procedure MergeFiles (Fn1,FN2,Sum:string);
implementation
 Uses SysUtils;
{======================================================================}

Procedure MergeFiles (Fn1,FN2,Sum:string);
var
  inputFile, outputFile: TextFile;
  line: widestring;
begin
  // Открываем выходной файл для записи
  AssignFile(outputFile, Sum);
  Rewrite(outputFile);

  // Открываем первый входной файл для чтения
  AssignFile(inputFile, Fn1);
  Reset(inputFile);
  // Читаем и записываем содержимое первого файла в выходной файл
  while not Eof(inputFile) do
  begin
    ReadLn(inputFile, line);
    WriteLn(outputFile, line);
  end;
  CloseFile(inputFile);
  // Открываем первый входной файл для чтения
  AssignFile(inputFile, Fn2);
  Reset(inputFile);
  // Читаем и записываем содержимое первого файла в выходной файл
  while not Eof(inputFile) do
  begin
    ReadLn(inputFile, line);
    WriteLn(outputFile, line);
  end;
  // Закрываем файлы
  CloseFile(inputFile);
  CloseFile(outputFile);
end;

// помещает все содержимое файла 1 в файл 2 между маркерами 1 и 2; сохраняя файл 2 с расширением ".old"
Procedure PutFile1ToFile2 (AFileName1,AFileName2:string;File2MarkerBegin,File2MarkerEnd:string);
var
 F1,F2,F3:TextFile;
 S_W:widestring;
 bGo:boolean;
 TmpFileName,OldFileName:string;
begin
 bGo:=false;
 AssignFile (F1, AFileName1);
 AssignFile (F2, AFileName2);
 TmpFileName:=ChangeFileExt(AFileName2,'.tmp');
 AssignFile (F3, TmpFileName);
// if not FileExists(AFileName1) then begin rewrite (F1); CloseFile(F1); end;
 Reset(F1);
// if not FileExists(AFileName2) then begin rewrite (F2); CloseFile(F2); end;
 Reset(F2);
 Rewrite(F3);
 repeat
  if not bGo then
  begin          // пока не найден маркер - доблируем часть файла 2 в 3
   readln (F2,S_W);
   writeln (F3, S_W);
   if S_W=File2MarkerBegin then bGo:=True else bGo:=False;
  end else // если найден маркер - дублируем весь файл 1 в 3; идем в позицию конечного маркера в файле 2;
  begin
   repeat
    readln (F1,S_W); //дублируем весь файл 1 в 3;
    writeln (F3, S_W);
   until EOF(F1);
   bGo :=False;
   repeat      // идем в позицию конечного маркера в файле 2;
    readln (F2,S_W);
    if S_W=File2MarkerEnd then
     begin
      writeln (F3,S_W);
      break;
     end;
   until EOF(F2);
  end;
 until EOF(F2);
 CloseFile(F1);
 CloseFile(F2);
 CloseFile(F3);
 OldFileName:=ChangeFileExt(AFileName2,'.old');
 DeleteFile(OldFileName);
 RenameFile(AFileName2,OldFileName);
 RenameFile(TmpFileName,AFileName2);
 DeleteFile(OldFileName); // вроде нормально работает, поэтому затираем
end;


{======================================================================}

function GetStringFromFile(var F:textFile; ABeginning:string):String;
var
 Str:string;
begin
 result:='';
 repeat
  readln(F,Str);
  if Pos(ABeginning,Str)=1 then
  begin
   result:=Str;
   break;
  end;
 until EOF(F);
end;

function GoToFilePosS(var F:textFile; S:string):string;
var
 Str:string;
begin
 result:='';
 repeat
  readln(F,Str);
  if Pos(S,Str)<>0 then
  begin
   result:=Str;
   break;
  end;
 until EOF(F);
end;

function GoToFilePos(var F:textFile; S:string):boolean;
var
 Str:string;
begin
 result:=False;
 repeat
  readln(F,Str);
  if Pos(S,Str)<>0 then
  begin
   result:=True;
   break;
  end;
 until EOF(F);
end;
Procedure FillCharSingle(var A:array of single;Value:single);
var
 i:integer;
begin
 for i:=low(A) to High(A) do A[i]:=Value;
end;
Procedure FillCharInt(var A:array of integer;Value:integer);
var
 i:integer;
begin
 for i:=low(A) to High(A) do A[i]:=Value;
end;
Procedure FillCharBool(var A:array of boolean;Value:boolean);
var
 i:integer;
begin
 for i:=low(A) to High(A) do A[i]:=Value;
end;
function IsElmInArr(var Arr:array of integer;q :integer; Elm:integer):boolean;
var
 i:integer;
begin
 IsElmInArr:=false;
 for i:=Low(Arr) to Low(Arr)+q-1 do
 if Arr[i]=Elm then
   begin
    IsElmInArr:=true;
    exit;
   end;
end;
{======================================================================}
procedure Mix ( var Arr:TSingleArr; q :integer );
var
 i:integer;
 Mem:pIntArr;
 Arr2:TSingleArr;
 RandomValue:integer;
begin
 Arr2:=Arr;
 randomize;
 GetMem(Mem,q*4);
 for i:=Low(Arr) to Low(Arr)+q-1 do
 begin
  Mem^[i]:= 0;
  repeat
   RandomValue:=Random(q)+1;
  until not IsElmInArr(Mem^,i, RandomValue);
  Mem^[i]:= RandomValue;
 end;
 for i:=Low(Arr) to Low(Arr)+q-1 do
  Arr[i]:=Arr2[ Mem^[i] ];
 freemem(Mem, q*4);
end;
{======================================================================}
procedure MixArr(var Arr:array of single; q:integer);
var
 i:integer;
 Mem:array of integer;
 Arr2:array of single;
 RandomValue:integer;
begin
 setlength(Arr2,q);
 setlength(Mem,q);
 for i:=1 to q do Arr2[i-1]:=Arr[i-1];
 for i:=1 to Q do
 begin
  Mem[i-1]:= 0;
  repeat
   RandomValue:=Random(q)+1;
  until not IsElmInArr(Mem,i, RandomValue);
  Mem[i]:= RandomValue;
 end;
 for i:=Low(Arr) to Low(Arr)+q-1 do
  Arr[i]:=Arr2[ Mem[i] ];
end;

begin
end.

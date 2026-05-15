Unit TextU ;
  {$N+}
interface
 uses uTypes,classes,CheckLst,StdCtrls, ComCTRLS;
function WSExtractDigits(S:string):string;// извлекает только цифры и дефис
function VarArrToStr(const V:variant):string;
function GetOnlyLetters(S:string;UseCase:boolean):string;
Function GetMaxCommonLettersSubStr(S1,S2:string;UseCase:boolean):String;
Function GetMaxCommonDigitsSubStr(S1,S2:string):String;
Function GetMaxCommonSubStr(S1,S2:string):String;
function DateToFirstDateOfMonth(const DateTime: TDateTime): TDateTime;
function DecMonth(const DateTime: TDateTime): TDateTime;
Function MyStr ( a : longint ) : string ;
Function MyStrI ( a , n : longint ) : string ;
Function MyStrR ( a : real ; n1 , n2 : longint ) : string ;
Function MyStrS ( a : single ; n1 , n2 : longint ) : string ;
Function MyStrR1 ( a : real ; n1  : longint ) : string ;
Function MyStrE ( a : real ) : string ;
Function MyVal ( s : string ) : longint ;
Function MyValR ( s : string ) : real ;
Function CharStr ( l : byte ; c : char ) : string ;
Function ByteStr ( l , c : byte ) : string ;
Function Space ( l : integer ) : string ;
function UpCaseStr(S:string):string;
function CutNextFromEnd(var Source: string): string;
function CutNext(var Source: string): string;
function GetFirstPartsUseDelimiter(const S: string;Delimiter:string; PartsCount:byte): string;
function CutNextUseDelimiter(var Source: string;Delimiter:string): string;
function ChangeSymbols(var S:string; Symb,ToCh:char):string;
Function IntArrToStr(const Arr:TIntArr):string;
Function GetStrCoreCoef(S1,S2:string):double;
procedure StrToIntArr( const S:string;var Arr:TIntArr);
Function StrToIntArrUseInterval( const S:string;var Arr:TIntArr):boolean;
Function IntToStrArrUseInterval( const Arr:TIntArr):string;
procedure ExcludeSpaces(var S:string);
function ListToStr(const List:TStrings;Delimiter:string):string;
procedure StrToList(Source:string;var List:TStringList;Delimiter:string);
Function CheckSubStr(const Substr,Str:string;bWholeWord:boolean):boolean;
Function BoolArrToStr(const Arr:TBoolArr):string;
function StrToCode(const S:string):double;
function CalcSymbolsCount(const S:string; Symbol:char):integer;
function DayOfWeekStr(const aDate:TDateTime):string;
procedure CBListToList(const CBList:TCheckListBox; var List: TStringList);
function StringSimilarityRatio(const Str1, Str2: String; IgnoreCase: Boolean): Double;
function NumEqDigits(Str1,Str2:string):integer;// кол-во совпадающих цифр
function ExtractDigits(S:string):string;// извлекает только цифры
function CompareStrDigits(Str1,Str2:string;ValueIfNoDigits:boolean):boolean;//сравнивает только числа в строках
function FirstLetterUpperCase (S:string):string;
Function IntToStrNils(Num:integer;NilsCount:byte):string;

Type
  PositionStr = ( LeftFull , CenterFull , RightFull ) ;
Function FullStr ( s : string ; l : byte ; N : PositionStr ) : string ;
function CutNextUseDelimiterNoTrim(var Source: string;Delimiter:string): string;
function WSCutNextUseDelimiterNoTrim(var Source: widestring;Delimiter:string): widestring;
procedure StringToStrArr(const Source,Delimeter:string; var StringArr:TStringArr);
function SortStringElms(const Source,Delimeter:string):string;// выдает ту же строку, только с элементами, отсортированными по алфавиту
procedure StringToList(const Source,Delimeter:string; var List:TStringList;bClear:boolean);
function GetInitials(const FullName: String): String;
Function FormatPhone(const PhoneNum:string):string;
Function FormatPhones(const PhoneNums:string;Prefics,DefCode:string):string;
Function NumDigits(const S:String):Integer;
Function NumCapsRus(const S:String):Integer;
function IsDate(str: string): Boolean;
function IsTime(str: string): Boolean;
procedure CopyStringToClipboard(const Value: String);
Function BytesArrToStr(const Arr:TByteArr):String;
Procedure StrToBytesArr(const S:string; var Arr:TByteArr);
procedure BoolArrToPackedByteArr(const BoolArr: TBoolArr;
  var PackedArr: TByteArr);
procedure PackedByteArrToBoolArr(const PackedArr: TByteArr; var BoolArr: TBoolArr);
function BoolArrToPackedStr(const BA: TBoolArr): string;
procedure PackedStrToBoolArr(const S: string; BA: TBoolArr);
function GetLevenshteinDistance(const Str1, Str2: String): Integer;
procedure ListBoxToStringList(var LB:TListBox; var List:TStringList);
Function SetDateTo01MMYYYY(Date:TDateTime):TDateTime;
function SentenceCase (S:string):string;
function FormatCity (City:string):string;
Function GetNilsBefore(const S:string; strlength:integer; nonils:boolean):string;
function RomanToArabic(const romanNumber : string) : integer ;
function ArabicToRoman(N: Integer): string;
function GetWordByNum(const aStr : String; const aNum : Integer) : String;
function UTF8ReverseString(const AText: widestring): widestring;
function UTF8CutNextUseDelimiterNoTrim(var Source: widestring; const Delimiter:string): widestring;
function AddBracketsToNums(const S,Brackets:string):string;
function Search_And_Replace(RichEdit: TRichEdit;
  SearchText, ReplaceText: string): Boolean;
function IsRussianLowerCase(C: Char): Boolean;
function IsRussianUpperCase(C: Char): Boolean;


type
 TCharSet=set of char;
var
 Arr:TIntArr;
 s:string;
implementation

uses sysutils, Math, dateUtils, Windows, clipbrd, calcsimu, StatProcs, variants;

const
cUsedBits=7;
// отрезает символы до точки вначале строки
const
  R: array[1..13] of string[2] =
  ('I', 'IV', 'V', 'IX', 'X', 'XL', 'L', 'XC', 'C', 'CD', 'D', 'CM', 'M');
  A: array[1..13] of Integer =
  (1, 4, 5, 9, 10, 40, 50, 90, 100, 400, 500, 900, 1000);
// обрамляет скобками Brackets[1],Brackets[2] любой номер в строке
// например, для:  Caption:= AddBracketsToNums('Кришна,1Арджуна.113 115','()');
// Caption='Кришна,(1)Арджуна.(113) (115)';

function IsRussianLowerCase(C: Char): Boolean;
begin
  Result := ((C >= 'а') and (C <= 'я')) or (C = 'ё');
end;

function IsRussianUpperCase(C: Char): Boolean;
begin
  Result := ((C >= 'А') and (C <= 'Я')) or (C = 'Ё');
end;

function WSExtractDigits(S:string):string;// извлекает только цифры и дефис
var
 i:integer;
begin
 Result:='';
 for i:=1 to Length(S) do if not(S[i] in ['a'..'z',',']) then Result:=ConCat(Result,S[i]);
 if not (result[Length(result)] in ['0'..'9']) then SetLength(Result,Length(Result)-1);
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
    while FindText(SearchText, startpos, endpos, [stMatchCase])<>-1 do
    begin
      endpos   := Length(RichEdit.Text) - startpos;
      Position := FindText(SearchText, startpos, endpos, [stMatchCase]);
      Inc(startpos, Length(SearchText));
      SetFocus;
      SelStart  := Position;
      SelLength := Length(SearchText);
      richedit.clearselection;
      SelText := ReplaceText;
    end;
    Lines.EndUpdate;
  end;
end;


function AddBracketsToNums(const S,Brackets:string):string;
var
 i:integer;
 SN:string;
 Prev:char;
begin
 i:=0;
 result:='';
 Prev:=#0;
 SN:='';
 repeat
  inc(i);
  if i>Length(S) then break;
  if S[i] in ['0'..'9']
   then SN:=SN+S[i]  // если номер то суммируем
   else
   begin // если не номер
            // предыдущий был номер
    if Prev in ['0'..'9'] then
     begin
      result:=result+Brackets[1]+SN+Brackets[2];
      SN:='';
     end;
           // в любом случае
    result:=result+S[i];
   end;
  Prev:=S[i];
 until False;
 if SN<>'' then result:=result+Brackets[1]+SN+Brackets[2];
end;


  //Поиск слова слева-направо.
function GetWordByNumL(const aStr : String; const aNum : Integer) : String;
const
  //Разделители слов.
  D = ['.', ',', ':', ';', '!', '?', '-', ' ', #9, #10, #13];
var
  i, j, Pos1, Len, LenW : Integer;
begin
  Result := '';
  if aNum < 1 then Exit;

  Len := Length(aStr);
  Pos1 := 0;
  j := 0;
  for i := 1 to Len do begin
    //Пропускаем разделители.
    if aStr[i] in D then Continue;
    //Отслеживаем начало слова.
    if (i = 1) or (aStr[i - 1] in D) then Pos1 := i;
    //Отслеживаем конец слова.
    if (i = Len) or (aStr[i + 1] in D) then begin
      //Порядковый номер слова:
      Inc(j);
      if j = aNum then begin
        //Длина слова.
        LenW := i - Pos1 + 1;
        //Слово.
        Result := Copy(aStr, Pos1, LenW);
        //Завершаем поиск.
        Break;
      end;
    end;
  end;
end;

//Поиск слова справа-налево.
function GetWordByNumR(const aStr : String; const aNum : Integer) : String;
const
  //Разделители слов.
  D = ['.', ',', ':', ';', '!', '?', '-', ' ', #9, #10, #13];
var
  i, j, Pos2, Len, LenW : Integer;
begin
  Result := '';
  if aNum > -1 then Exit;

  Len := Length(aStr);
  Pos2 := 0;
  j := 0;
  for i := Len downto 1 do begin
    //Пропускаем разделители.
    if aStr[i] in D then Continue;
    //Отслеживаем конец слова.
    if (i = Len) or (aStr[i + 1] in D) then Pos2 := i;
    //Отслеживаем начало слова.
    if (i = 1) or (aStr[i - 1] in D) then begin
      //Порядковый номер слова:
      Dec(j);
      if j = aNum then begin
        //Длина слова.
        LenW := Pos2 - i + 1;
        //Слово.
        Result := Copy(aStr, i, LenW);
        //Завершаем поиск.
        Break;
      end;
    end;
  end;
end;

//Поиск слова в любом направлении.
function GetWordByNum(const aStr : String; const aNum : Integer) : String;
begin
  Result := '';
  if aNum > 0 then Result := GetWordByNumL(aStr, aNum)
  else Result := GetWordByNumR(aStr, aNum);
end;

function UTF8ReverseString(const AText: widestring): widestring;
var
 i:integer;
begin
 Result:='';
 for i:=Length(AText) downto 1 do result:=Result+AText[i];
end;

//--------------------------------------------
function ArabicToRoman(N: Integer): string; //???????? ? ???????
var
  i: Integer;
begin
  Result := '';
  i := 13;
  while N > 0 do
  begin
    while A[i] > N do
      Dec(i);
    Result := Result + R[i];
    Dec(N, A[i]);
  end;
end;
function RomanToArabic(
         const romanNumber : string) : integer ;
// Примечание: RomanToArabic вернет -1, если параметр romanNumber написан не латинскими буквами (например, MIXKIX не является римской цифра).
 const
   romanChars = 'IVXLCDMvxlcdm?!#' ;
   decades : array [0..8] of integer = (
         0, 1, 10, 100, 1000, 10000, 100000,
         1000000, 10000000) ;
   OneFive : array [boolean] of byte = (1, 5) ;
 var
   newValue, oldValue : integer ;
   cIdx, P : byte ;
 begin
   result := 0;
   oldValue := 0 ;
   for cIdx := Length(romanNumber) downto 1 do
   begin
     P := Succ(Pos(romanNumber[cIdx], romanChars)) ;
     newValue := OneFive[Odd(P)] * decades[P div 2] ;
     if newValue = 0 then
     begin
       result := -1;
       Exit;
     end ;
     if newValue < oldValue then newValue := - newValue ;
     Inc(result, newValue) ;
     oldValue := newValue
   end ;
 end;

// отрезает символы до точки вначале строки
Function IntToStrNils(Num:integer;NilsCount:byte):string;
var
 AddNum,i:integer;
begin
 Result:=IntToStr(Abs(Num));
 if Num>=0 then
 begin
  AddNum:=NilsCount-Length(Result);
  for i:=1 to AddNum do Result:=concat('0',result);
 end else
 begin
  AddNum:=NilsCount-Length(Result)-1;
  for i:=1 to AddNum do Result:=concat('0',result);
  Result:=concat('-',result);
 end
end;

function VarArrToStr(const V:variant):string;
 var
  i:integer;
begin
 Result:=VarToStr(V[0]);
 for i:=2 to 3 do
  Result:=Result+#9+VarToStr(V[i-1]);
end;
function GetOnlyLetters(S:string;UseCase:boolean):string;
var
 i:integer;
begin
 if not UseCAse then S:=AnsiLowerCase(S);
 S:=StringReplace(S,'і','и',[rfReplaceAll]);
 S:=StringReplace(S,'є','е',[rfReplaceAll]);
 result:='';
 for i:=1 to Length(S) do
  if Ord(S[i]) in [168,170,175,178,179,184,186,191..255] then result:=Result+S[i] ;//else result:=Result+' ';
end;
Function GetMaxCommonLettersSubStr(S1,S2:string;UseCase:boolean):String;
begin
 S1:=GetOnlyLetters(S1,UseCase);
 S2:=GetOnlyLetters(S2,UseCase);
 Result:=GetMaxCommonSubStr(S1,S2);
end;

function GetOnlyDigits(S:string):string;
var
 i:integer;
begin
 result:='';
 for i:=1 to Length(S) do
  if Ord(S[i]) in [48..57] then result:=Result+S[i] ;//else result:=Result+' ';
end;

Function GetMaxCommonDigitsSubStr(S1,S2:string):String;
begin
 S1:=GetOnlyDigits(S1);
 S2:=GetOnlyDigits(S2);
 Result:=GetMaxCommonSubStr(S1,S2);
end;

Function GetMaxCommonSubStr(S1,S2:string):String;
var
 s:string;
 i,j,mx:integer;
begin
  mx:=0;
  for i:=1 to length(s1) do
  for j:=i to length(s1) do
  if (pos(copy(s1,i,j-i+1),s2)>0)and(j-i+1>mx) then
   begin
    mx:=j-i+1;
    s:=copy(s1,i,j-i+1);
   end;
  if mx=0 then Result:=''
  else result:=S;
end;

function DateToFirstDateOfMonth(const DateTime: TDateTime): TDateTime;
var
  Year, Month, Day: Word;
begin
  DecodeDate(DateTime, Year, Month, Day);
  Result := EncodeDate(Year, Month, 1);
  ReplaceTime(Result, DateTime);
end;

function DecMonth(const DateTime: TDateTime): TDateTime;
var
  Year, Month, Day: Word;
begin
  DecodeDate(DateTime, Year, Month, Day);
  Dec(Month);
  if Month=0 then  begin Month:=12; Dec(Year); end;
  Result := EncodeDate(Year, Month, Day);
  ReplaceTime(Result, DateTime);
end;


function CompareStrDigits(Str1,Str2:string;ValueIfNoDigits:boolean):boolean;//сравнивает только числа в строках
var
 S1,S2:string;
begin
 S1:=ExtractDigits(Str1);
 S2:=ExtractDigits(Str2);
 Result:=(S1=S2);
 if Result and (s1='') then Result:=ValueIfNoDigits;
end;
function ExtractDigits(S:string):string;// извлекает только цифры
var
 i:integer;
begin
 Result:='';
 for i:=1 to Length(S) do if (S[i] in ['0'..'9']) then Result:=ConCat(Result,S[i]);
end;
function NumEqDigits(Str1,Str2:string):integer;
var
 i:integer;
 b1,b2:array [0..9] of boolean;
begin
 FillChar(B1,10,0);
 FillChar(B2,10,0);
 result:=0;
 for i:=1 to Length(Str1) do if (Str1[i] in ['0'..'9']) then b1[StrToInt(Str1[i])]:=True;
 for i:=1 to Length(Str2) do if (Str2[i] in ['0'..'9']) then b2[StrToInt(Str2[i])]:=True;
 for i:=0 to 9 do if b1[i] and b2[i] then inc(result);
end;
function FormatCity (City:string):string;
begin
 if (Pos('.',City)>0) and (Pos('.',City)<5)
  then Result:=Copy(City,Pos('.',City)+1,Length(City))
  else Result:=City;
end;

Function SetDateTo01MMYYYY(Date:TDateTime):TDateTime;
var
 Year,Month,Day:word;
begin
 DecodeDate(Date,Year, Month, Day);
 Result:=EncodeDate(Year,Month,1);
end;

function SentenceCase (S:string):string;
var
 i:integer;
 nNextUpperCase:boolean;
begin
 nNextUpperCase:=True;
 for i:=1 to Length(S) do
 begin
  if nNextUpperCase
   then Result:= Concat(Result,ANSIUpperCase(S[i]))
   else Result:= Concat(Result,ANSILowerCase(S[i]));
  nNextUpperCase:=(S[i]='.') or (S[i]=' ');
 end;
end;
function FirstLetterUpperCase (S:string):string;
begin
 if Length(S)>0 then
 begin
  Result:=ANSIUpperCase(S[1])+ANSILowerCase(Copy(S,2,Length(S)));
 end;
end;

Function BytesArrToStr(const Arr:TByteArr):String;
var
 S:string absolute Arr;
begin
 Result:=S;
end;

procedure ListBoxToStringList(var LB:TListBox; var List:TStringList);
var
 i:integer;
begin
 List.Clear;
 List.Sorted:=True;
 for i:=1 to LB.Count do
 if LB.Selected[i-1] then 
 begin
  List.Add(Lb.Items[i-1])
 end;
end;

function GetLevenshteinDistance(const Str1, Str2: String): Integer;
var
  LenStr1, LenStr2: Integer;
  I, J, T, Cost, Minimum: Integer;
  pStr1, pStr2, S1, S2: PChar;
  D, RowPrv2, RowPrv1, RowCur, Temp: PIntegerArray;
begin
  LenStr1 := Length(Str1);
  LenStr2 := Length(Str2);
  // to save some space, make sure the second index points to the shorter string
  if LenStr1 < LenStr2 then
  begin
    T := LenStr1;
    LenStr1 := LenStr2;
    LenStr2 := T;
    pStr1 := PChar(Str2);
    pStr2 := PChar(Str1);
  end
  else
  begin
    pStr1 := PChar(Str1);
    pStr2 := PChar(Str2);
  end;
  // to save some time and space, look for exact match
  while (LenStr2 <> 0) and (pStr1^ = pStr2^) do
  begin
    Inc(pStr1);
    Inc(pStr2);
    Dec(LenStr1);
    Dec(LenStr2);
  end;
  // when one string is empty, length of the other is the distance
  if LenStr2 = 0 then
  begin
    Result := LenStr1;
    Exit;
  end;
  // calculate the edit distance
  T := LenStr2 + 1;
  GetMem(D, 3 * T * SizeOf(Integer));
  FillChar(D^, 2 * T * SizeOf(Integer), 0);
  RowCur := D;
  RowPrv1 := @D[T];
  RowPrv2 := @D[2 * T];
  S1 := pStr1;
  for I := 1 to LenStr1 do
  begin
    Temp := RowPrv2;
    RowPrv2 := RowPrv1;
    RowPrv1 := RowCur;
    RowCur := Temp;
    RowCur[0] := I;
    S2 := pStr2;
    for J := 1 to LenStr2 do
    begin
      Cost := Ord(S1^ <> S2^);
      Minimum := RowPrv1[J - 1] + Cost;      // substitution
      T := RowCur[J - 1] + 1;                // insertion
      if T < Minimum then
        Minimum := T;
      T := RowPrv1[J] + 1;                   // deletion
      if T < Minimum then
        Minimum := T;
      if (I <> 1) and (J <> 1) and (S1^ = (S2 - 1)^) and (S2^ = (S1 - 1)^) then
      begin
        T := RowPrv2[J - 2] + Cost;          // transposition
        if T < Minimum then
          Minimum := T;
      end;
      RowCur[J] := Minimum;
      Inc(S2);
    end;
    Inc(S1);
  end;
  Result := RowCur[LenStr2];
  FreeMem(D);
end;

function StringSimilarityRatio(const Str1, Str2: String; IgnoreCase: Boolean): Double;
var
  MaxLen: Integer;
  Distance: Integer;
begin
  Result := 1.0;
  if Length(Str1) > Length(Str2) then
    MaxLen := Length(Str1)
  else
    MaxLen := Length(Str2);
  if MaxLen <> 0 then
  begin
    if IgnoreCase then
      Distance := GetLevenshteinDistance(LowerCase(Str1), LowerCase(Str2))
    else
      Distance := GetLevenshteinDistance(Str1, Str2);
    Result := Result - (Distance / MaxLen);
  end;
end;

function EditDistance(s, t: string): integer;
var
  d : array of array of integer;
  i,j,cost : integer;
begin
  {
  Compute the edit-distance between two strings.
  Algorithm and description may be found at either of these two links:
  http://en.wikipedia.org/wiki/Levenshtein_distance
  http://www.google.com/search?q=Levenshtein+distance
  }

  try
    //initialize our cost array
    SetLength(d,Length(s)+1);
    for i := Low(d) to High(d) do begin
      SetLength(d[i],Length(t)+1);
    end;

    for i := Low(d) to High(d) do begin
      d[i,0] := i;
      for j := Low(d[i]) to High(d[i]) do begin
        d[0,j] := j;
      end;
    end;

    //store our costs in a 2-d grid
    for i := Low(d)+1 to High(d) do begin
      for j := Low(d[i])+1 to High(d[i]) do begin
        if s[i] = t[j] then begin
          cost := 0;
        end
        else begin
          cost := 1;
        end;

        //to use "Min", add "Math" to your uses clause!
        d[i,j] := Min(Min(
                   d[i-1,j]+1,      //deletion
                   d[i,j-1]+1),     //insertion
                   d[i-1,j-1]+cost  //substitution
                   );
      end;  //for j
    end;  //for i

    //now that we've stored the costs, return the final one
    Result := d[Length(s),Length(t)];
  finally
    //cleanup
    for i := Low(d) to High(d) do begin
      for j := Low(d[i]) to High(d[i]) do begin
        SetLength(d[i],0);
      end;  //for j
    end;  //for i
    SetLength(d,0);
  end;  //try-finally
end;



Procedure StrToBytesArr(const S:string; var Arr:TByteArr);
var
 i:integer;
begin
 SetLength(Arr,Length(S));
 for i:=1 to Length(S) do Arr[i-1]:=ord(S[i]);
end;

procedure BoolArrToPackedByteArr(const BoolArr: TBoolArr;
  var PackedArr: TByteArr);
var
 i:integer;
 BitNum:byte;
 ElmNum:integer;
 Len:integer;
begin
 if Length(BoolArr) mod cUsedBits = 0
  then Len:=Length(BoolArr) div cUsedBits
  else Len:=Length(BoolArr) div cUsedBits+1;
 SetLength(PackedArr, Len);
 for i:=0 to Length(BoolArr)-1 do
 begin
  BitNum:=i mod cUsedBits;
  ElmNum:=i div cUsedBits;
  SetByteBit(PackedArr[ElmNum],BitNum,BoolArr[i]);
  SetByteBit(PackedArr[ElmNum],7,True); // Для того, чтобы строка не = #0
 end;
end;

procedure PackedByteArrToBoolArr(const PackedArr: TByteArr; var BoolArr: TBoolArr);
var
 i,j:integer;
begin
 SetLength(BoolArr,Length(PackedArr)*cUsedBits);
 for i:=1 to length(PackedArr) do
 for j:=1 to cUsedBits do
  BoolArr[(i-1)*cUsedBits+j-1]:=isBit(PackedArr[i-1],j-1);
end;

function BoolArrToPackedStr(const BA: TBoolArr): string;
var
 PBA:TByteArr;
begin
 BoolArrToPackedByteArr(BA,PBA);
 result:=BytesArrToStr(PBA);
end;

procedure PackedStrToBoolArr(const S: string; BA: TBoolArr);
var
 PBA:TByteArr;
begin
 StrToBytesArr(S,PBA);
 PackedByteArrToBoolArr(PBA,BA);
end;


procedure CopyStringToClipboard(const Value: String);
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

function IsDate(str: string): Boolean;
var
  dt: TDateTime;
begin
  Result := True;
  try
    dt := StrToDate(str);
  except
    Result := False;
  end;
end;

function IsTime(str: string): Boolean;
var
  dt: TDateTime;
begin
  Result := True;
  try
    dt := StrToTime(str);
  except
    Result := False;
  end;
end; // return number of digits 0..9 in the string
Function NumDigits(const S:String):Integer;
var
 i:integer;
begin
 result:=0;
 for i:=1 to Length(S) do
  if S[i] in ['0'..'9'] then inc(result);
end;

Function NumCapsRus(const S:String):Integer;
var
 i:integer;
begin
 result:=0;
 for i:=1 to Length(S) do
  if S[i] in ['А'..'Я'] then inc(result);
end;

Function FormatPhones(const PhoneNums:string;Prefics,DefCode:string):string;
var
 S:String;
 PhoneNum:string;
 n:integer;
begin
 result:='';
 if PhoneNums='' then exit;
 S:=PhoneNums;
 S:=StringReplace(S,'.',';',[rfReplaceAll, rfIgnoreCase]);
 S:=StringReplace(S,',',';',[rfReplaceAll, rfIgnoreCase]);
 S:=StringReplace(S,' и ',';',[rfReplaceAll, rfIgnoreCase]);
 while S<>'' do
 begin
  PhoneNum:=CutNextUseDelimiter(S,';');
  n:=NumDigits(PhoneNum);
  if n<5 then continue else
  if N=5 then PhoneNum:=Copy (Defcode,1,7)+PhoneNum else
  if N=6 then PhoneNum:=Copy (Defcode,1,6)+PhoneNum else
  if N=7 then PhoneNum:=Copy (Defcode,1,5)+PhoneNum;
  PhoneNum:=FormatPhone(PhoneNum);
  result:=ConCat(result,Prefics,PhoneNum,';')
 end;
end;
Function FormatPhone(const PhoneNum:string):string;
//phone sample +38(048)2363045
var
 S:String[15];
 i,j:integer;
begin
 j:=0;
 for i:=Length(PhoneNum) downto 1 do
  if PhoneNum[i] in ['0'..'9'] then inc(j);
  if j<5 then begin result:=''; exit; end;
 j:=15;
 S:='+38(           ';
 for i:=Length(PhoneNum) downto 1 do
  if PhoneNum[i] in ['0'..'9'] then
 begin
  S[j]:=PhoneNum[i];
  dec(j);
  if j=8 then begin S[j]:=')'; dec(j); end;
  if j=4 then begin S[j]:='('; dec(j); end;
 end;
 for i:=j downto 5 do S[i]:='0';
 result:=s;
end;

function InvertStr(const S:string):String;
var
 i:integer;
begin
 result:='';
 for i:=1 to Length(S) do result:=ConCat(result,S[Length(S)-i+1]);
end;
function GetInitials(const FullName: String): String;
var
 S:string;
begin
 if FullName='' then begin result:='---'; exit; end;
 S:=FullName;
 result:=CutNext(S);
 result:=Concat(result,' ',S[1],'.');
 CutNext(S);
 result:=Concat(result,S[1],'.');
end;
function DayOfWeekStr(const aDate:TDateTime):string;
var
 ADayOfWeek:word;
begin
 ADayOfWeek:=DayOfTheWeek(aDate);
 Case ADayOfWeek of
  DayMonday: result:= 'Понедельник';
  DayTuesday: result := 'Вторник';
  DayWednesday: result := 'Среда';
  DayThursday: result := 'Четверг';
  DayFriday: result := 'Пятница';
  DaySaturday: result := 'Суббота';
  DaySunday: result  := 'Воскресенье';
  else result  := 'Это не день недели!';
 end
end;
function SortStringElms(const Source,Delimeter:string):string;
var
 List:TStringList;
 S:string;
 i:integer;
begin
 S:=Source;
 List:=TStringList.Create;
 List.Sorted:=True;
 While S<>'' do
 begin
   List.Add(CutNextUseDelimiter(S,Delimeter))
 end;
 Result:='';
 if List.Count>0 then Result:=List[0];
 for i:=2 to List.Count do result:=Concat(result,Delimeter,List[i-1]);
 List.Free;
end;
procedure StringToList(const Source,Delimeter:string; var List:TStringList;bClear:boolean);
var
 S:string;
begin
 if bClear then List.Clear;
 S:=Source;
 While S<>'' do
   List.Add(CutNextUseDelimiter(S,Delimeter));
end;
procedure StringToStrArr(const Source,Delimeter:string; var StringArr:TStringArr);
var
 List:TStringList;
 S:string;
 i:integer;
begin
 S:=Source;
 List:=TStringList.Create;
 List.Sorted:=True;
 While S<>'' do
 begin
   List.Add(CutNextUseDelimiter(S,Delimeter));
 end;
 SetLength(StringArr,List.Count);
 for i:=1 to List.Count do StringArr[i-1]:=List[i-1];
 List.Free;
end;

function CalcSymbolsCount(const S:string;Symbol:char):integer;
var
 i:integer;
begin
 result:=0;
 for i:=1 to Length(S) do
 if S[i]=Symbol then inc(result);
end;
function StrToCode(const S:string):double;
var
 i:integer;
begin
 result:=0;
 for i:=1 to Length(S) do
  result:=result+(100-Ord(S[i]))*IntPower(100,100-i);
end;

Function CheckSubStr(const Substr,Str:string;bWholeWord:boolean):boolean;
begin
 if bWholeWord then Result:=Substr=Str else
  Result:=Pos(SubStr,Str)>0;
end;

Function IntToStrArrUseInterval( const Arr:TIntArr):string;
var
 i:integer;
 s:string;
begin
 result:='';
 if Length(Arr)=0 then exit;
 result:=IntToStr(Arr[0]);
 s:=',';
 for i:=3 to Length(Arr) do
 begin
  if Arr[i-1]-Arr[i-2]<>1
   then Result:=Result+s+IntToStr(Arr[i-1])
   else
   begin
    if i=Length(Arr)
     then Result:=Result+s+IntToStr(Arr[i-1])
     else
      if Arr[i-2]-Arr[i-3]<>1
       then s:= '-'
       else begin Result:=Result+s+IntToStr(Arr[i-1]);s:= ',' end;
   end;
 end;

end;
procedure StrToList(Source:string;var List:TStringList;Delimiter:string);
var
 i:integer;
 S:string;
begin
 List.Clear;
  repeat
   S:=CutNextUseDelimiterNoTrim(Source,Delimiter);
   List.Add(S);
  until Source='';
end;

function ListToStr(const List:TStrings;Delimiter:string):string;
var i:integer;
begin
  result:='';
  for i:=1 to List.Count do
  result:=result+List[i-1]+Delimiter;
  SetLength(result,Length(result)-Length(Delimiter));
end;
procedure ExcludeSpaces(var S:string);
var
 i:integer;
begin
 repeat
  i:=Pos(' ',S);
  if i=0 then exit else Delete(S,i,1);
 until false;
end;
Function StrToIntArrUseInterval( const S:string;var Arr:TIntArr):boolean;
var
 i:integer;
 S2,S1:string;
//----------------------------------------
 procedure AddIntValue(AVAlue:integer);
 begin
   SetLength(Arr,Length(Arr)+1);
   Arr[Length(Arr)-1]:=AValue;
 end;
//----------------------------------------
begin
 if s='' then begin result:=False; exit; end; 
 result:=True;
 try
 S1:=Trim(S);
 ExcludeSpaces(S1);
 if S='' then exit;
 repeat
  S2:=CutNextUseDelimiter(S1,',');
  if S2='' then exit;
  if Pos('-',S2)=0
   then AddIntValue(StrToINt(S2))
   else
    begin
     S2[Pos('-',S2)]:=' ';
     for i:=StrToINt(CutNext(S2)) to StrToINt(CutNext(S2)) do AddIntValue(i);
    end;
 until S1='';
 except
  SetLength(Arr,0);
  result:=false;
 end;
end;

procedure StrToIntArr( const S:string; var Arr:TIntArr);
var
 Value,i:integer;
 S1:string;
 Tmp:Char;
begin
 Tmp:=DecimalSeparator;
 DecimalSeparator:=',';
 S1:=Trim(S);
 if S='' then exit;
 i:=0;
 repeat
  try
  Value:=Round(StrToFloat(CutNext(S1)));
  except
   DecimalSeparator:=Tmp;
   exit;
  end;
   inc(i);
   SetLength(Arr,i);
   Arr[i-1]:=Value;
 until S1='';
 DecimalSeparator:=Tmp;
end;

Function BoolArrToStr(const Arr:TBoolArr):string;
var
 i:integer;
begin
  Result:='';
 for i:=1 to Length(Arr) do
  if Arr[i-1] then Result:=Result+intToStr(i)+', ';
 SetLength(Result,Length(Result)-2);
end;

Function IntArrToStr(const Arr:TIntArr):string;
var
 i:integer;
begin
  Result:='';
 for i:=1 to Length(Arr) do
  Result:=Result+intToStr(Arr[i-1])+', ';
 SetLength(Result,Length(Result)-2);
end;

function ChangeSymbols(Var S:string; Symb,ToCh:char):string;
var
 i:integer;
begin
 for i:=1 to Length(S) do if s[i]=Symb then s[i]:=ToCh;
 result:=s;
end;

function CutNextFromEnd(var Source: string): string;
var
 S:string;
 PosSpace:byte;
begin
 S:=InvertStr(Source);
 S:=Trim(S);
 S:=S+' ';
 PosSpace:=Pos(' ',s);
 result:=InvertStr(Trim(Copy(S,1,PosSpace)));
 Delete(S,1,PosSpace);
 Source:=InvertStr(Trim(S));
end;
function CutNext(var Source: string): string;
var
 S:string;
 PosSpace:integer;
begin
 S:=Trim(Source);
 S:=S+' ';
 PosSpace:=Pos(' ',s);
 result:=Trim(Copy(S,1,PosSpace));
 Delete(S,1,PosSpace);
 Source:=Trim(S);
end;

function UTF8CutNextUseDelimiterNoTrim(var Source: widestring; const Delimiter:string): widestring;
var
 S,wDelimiter:widestring;
 PosSpace:integer;
begin
 wDelimiter:=AnsiToUtf8(Delimiter);
 S:=Source;
 PosSpace:=Pos(Delimiter,s);
 if PosSpace=0 then
 begin
  result:=S;
  Source:='';
  exit;
 end;
 result:=Trim(Copy(S,1,PosSpace-1));
 Delete(S,1,PosSpace+Length(wDelimiter)-1);
 Source:=S;
end;

function CutNextUseDelimiterNoTrim(var Source: string;Delimiter:string): string;
var
 S:string;
 PosSpace:integer;
begin
 S:=Source;
 PosSpace:=Pos(Delimiter,s);
 if PosSpace=0 then
 begin
  result:=S;
  Source:='';
  exit;
 end;
 result:=Trim(Copy(S,1,PosSpace-1));
 Delete(S,1,PosSpace+Length(Delimiter)-1);
 Source:=S;
end;

function WSCutNextUseDelimiterNoTrim(var Source: widestring;Delimiter:string): widestring;
var
 S:string;
 PosSpace:integer;
begin
 S:=Source;
 PosSpace:=Pos(Delimiter,s);
 if PosSpace=0 then
 begin
  result:=S;
  Source:='';
  exit;
 end;
 result:=Trim(Copy(S,1,PosSpace-1));
 Delete(S,1,PosSpace+Length(Delimiter)-1);
 Source:=S;
end;

function GetFirstPartsUseDelimiter(const S: string;Delimiter:string; PartsCount:byte): string;
var
 i:integer;
 S2:String;
begin
 S2:=S;
 Result:='';
 for i:=1 to PartsCount do
 Result:=Result+CutNextUseDelimiter(S2,Delimiter)+' ;';
 if Length(Result)<>0 then  SetLength(Result,Length(Result)-2);
end;

function CutNextUseDelimiter(var Source: string;Delimiter:string): string;
var
 S:string;
 PosSpace:integer;
begin
 S:=Trim(Source);
 PosSpace:=Pos(Delimiter,s);
 if PosSpace=0 then
 begin
  result:=S;
  Source:='';
  exit;
 end;
 result:=Trim(Copy(S,1,PosSpace-1));
 Delete(S,1,PosSpace+Length(Delimiter)-1);
 Source:=Trim(S);
end;


function UpCaseStr(S:string):string;
var i:integer;
begin
 for i:=1 to Length(s) do s[i]:=UpCase(s[i]);
 UpCaseStr:=s;
end;
Function MyStrS ( a : single ; n1 , n2 : longint ) : string ;
  var
    s : string ;
  begin
    str ( a : n1 : n2 , s ) ;
    MyStrS := s ;
  end ;

{============================================================================}
Function FullStr ( s : string ; l : byte ; N : PositionStr ) : string ;
  var
    i : byte ;
  begin
    case N of
      LeftFull :
        begin
          s := Space ( l ) + s ;
          FullStr := Copy ( s , Length(S) - l + 1 , l )
        end ;
      RightFull :
        begin
          s := s + Space ( l ) ;
          FullStr := Copy ( s , 1 , l )
        end ;
      CenterFull :      { ЌҐ®Ўе®¤Ё¬  ¤®а Ў®вЄ  }
        begin
          i := ( l - Length(S) ) div 2 ;
          s := space ( i ) + s + Space ( i ) ;
          if Length(S) < l then s := s + ' ' ;
          FullStr := s
        end
    end
  end ;

Function CenterStr ( s : string ; max : byte ) : string ;
  var
    i : byte ;
    sl : byte absolute s ;
  begin
    i := ( max - sl ) div 2 ;
    s := space ( i ) + s + Space ( i ) ;
  end ;

{==========================================================================}

Function MyStr ( a : longint ) : string ;
  var
    s : string ;
  begin
    Str ( a , s ) ;
    MyStr := s ;
  end ;

{==========================================================================}

Function MyStrI ( a , n : longint ) : string ;
  var
    s : string ;
  begin
    str ( a : n , s ) ;
    MyStrI := s ;
  end ;

{==========================================================================}

Function MyStrR ( a : real ; n1 , n2 : longint ) : string ;
  var
    s : string ;
  begin
    str ( a : n1 : n2 , s ) ;
    MyStrR := s ;
  end ;

{==========================================================================}
Function MyStrR1 ( a : real ; n1  : longint ) : string ;
  var
    s : string ;
  begin
    str ( a : n1 , s ) ;
    MyStrR1 := s ;
  end ;

{==========================================================================}

Function MyStrE ( a : real ) : string ;
  var
    s : string ;
  begin
    str ( a , s ) ;
    MyStrE := s ;
  end ;

Procedure ValErr ( c : integer ) ;
  begin

  end ;

{==========================================================================}

Function MyVal ( s : string ) : longint ;
  var
    res  : longint ;
    code : integer ;

  begin
    Val ( s , res , code ) ;
    if code <> 0 then ValErr ( code ) ;
    MyVal := res ;
  end ;

{==========================================================================}

Function MyValR ( s : string ) : real ;
  var
    res  : real ;
    code : integer ;
  begin
    Val ( s , res , code ) ;
    if code <> 0 then ValErr ( code ) ;
    MyValR := res ;
  end ;

{==========================================================================}

Function CharStr ( l : byte ; c : char ) : string ;
  var
    s : string ;
    i:byte;
  begin
    s:='';
    for i:=1 to l do S:=S + C;
    CharStr := s ;
  end ;

{==========================================================================}

Function ByteStr ( l , c : byte ) : string ;
  begin
    ByteStr := CharStr ( l , Chr ( c)) ;
  end ;

{==========================================================================}

Function Space ( l : integer ) : string ;
  begin
    Space := CharStr ( l , ' ' ) ;
  end ;

{==========================================================================}
Function GetStrCoreCoef(S1,S2:string):double;
var
 List:TStringList;
 i,j:integer;
 Arr1,Arr2:array of single;
begin
 List:=TStringList.Create;
 List.Sorted:=True;
 S1:=Trim(S1);
 S2:=Trim(S2);
 if (S1='')and(S2='') then begin Result:=1 ; exit; end;
 if (S1='')or(S2='') then begin Result:=0; exit; end;
 for i:=1 to Length(S1) do if not List.Find(S1[i],j) then List.Add(S1[i]);
 for i:=1 to Length(S2) do if not List.Find(S2[i],j) then List.Add(S2[i]);
 SetLength(arr1,0);
 SetLength(arr1,List.Count);
 SetLength(arr2,0);
 SetLength(arr2,List.Count);
 for i:=1 to Length(S1) do if List.Find(S1[i],j) then Arr1[j]:=Arr1[j]+1;
 for i:=1 to Length(S2) do if List.Find(S2[i],j) then Arr2[j]:=Arr2[j]+1;
 Result:=CoreRankRank(Arr1,Arr2,List.Count,kendal);
 List.Free;
end;
{==========================================================================}
Function GetNilsBefore(const S:string; strlength:integer; nonils:boolean):string;
var
 NilSstr:string;
 i:integer;
begin
  result:=S;
  if nonils then exit;
  for i:=1 to strlength-Length(S) do NilsStr:=NilsStr+'0';
  result:=Nilsstr+S;
end;
{==========================================================================}

procedure CBListToList(const CBList:TCheckListBox; var List: TStringList);
var
 i:integer;
begin
 List.Clear;
 for i:=1 to CBList.Items.Count do
 if CBList.Checked[i-1] then List.Add(CBList.Items[i-1])
end;
Function MyStr16 (a:longint):string;
var
 Mod16:longint;
 S:string;
 n:byte;
begin
 S:=space(20);
 n:=20;
 repeat
 Mod16:=a mod 16;
  a:=a div 16;
  case mod16 of
  0:S[n]:='0';
  1:S[n]:='1';
  2:S[n]:='2';
  3:S[n]:='3';
  4:S[n]:='4';
  5:S[n]:='5';
  6:S[n]:='6';
  7:S[n]:='7';
  8:S[n]:='8';
  9:S[n]:='9';
  10:S[n]:='A';
  11:S[n]:='B';
  12:S[n]:='C';
  13:S[n]:='D';
  14:S[n]:='E';
  15:S[n]:='F';
  end;
  dec(n);
 until a=0;
 S[n]:='$';
end;
{============================================================================}
initialization
 SetLength(Arr,10);
 arr[0]:=1;
 arr[1]:=2;
 arr[2]:=3;
 arr[3]:=5;
 arr[4]:=6;
 arr[5]:=7;
 arr[6]:=0;
 arr[7]:=11;
 arr[8]:=12;
 arr[9]:=14;
S:=IntToStrArrUseInterval(Arr)


End.



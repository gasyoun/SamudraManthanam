unit uSort;

interface
 uses uTypes, ArtMath;

 type
 TSortArrClass=class (TSortClass)
  public
   Arr:TDoubleArr;
   ArrIds:TIntArr;
   ArrLength:integer;
   function GetValue(I: integer): double;override;
   procedure RunSort;override;
   procedure RunSlowlySort;
   property Value[I:Integer]:double read GetValue ;//write SetValue;
   procedure ExchangeValues(Item1,Item2:integer);override;
 end;


procedure RangeByUniqueValues(Values:TDoubleArr; var NewIds:TIntArr; var MaxRank:integer);
procedure RangeByValues(Values:TDoubleArr; var NewIds:TIntArr);
procedure RangeByValuesSlowly(Values:TDoubleArr; var NewIds:TIntArr);
procedure SortIntArr(var Values:TIntArr);
procedure SortLongWordArr(var Values:array of LongWord);
procedure SortByteArr(const Values:TByteArr; var SortValues:TByteArr);

implementation
 uses Math;

procedure RangeByValuesSlowly(Values:TDoubleArr; var NewIds:TIntArr);
var
 i:integer;
 SortArrClass:TSortArrClass;
begin
  SortArrClass:=TSortArrClass.Create;
  SortArrClass.ArrLength:=Length(Values);
  SetLength(SortArrClass.ArrIds,SortArrClass.ArrLength);
  for i:=1 to Length(Values) do SortArrClass.ArrIds[i-1]:=i;
  CopyDoubleArr(Values,SortArrClass.Arr,SortArrClass.ArrLength);
  SortArrClass.RunSlowlySort;
  CopyIntArr(SortArrClass.ArrIds,NewIds,SortArrClass.ArrLength);
  SortArrClass.Free;
end;

procedure RangeByUniqueValues(Values:TDoubleArr; var NewIds:TIntArr; var MaxRank:integer);
var
 i,ind,j:integer;
 PrevValue:double;
 SortArrClass:TSortArrClass;
begin
  SortArrClass:=TSortArrClass.Create;
  SortArrClass.ArrLength:=Length(Values);
  SetLength(SortArrClass.ArrIds,SortArrClass.ArrLength);
  for i:=1 to Length(Values) do SortArrClass.ArrIds[i-1]:=i;
  CopyDoubleArr(Values,SortArrClass.Arr,SortArrClass.ArrLength);
  SortArrClass.RunSort;
  SetLength(NewIds,Length(Values));
  ind:=0;
  PrevValue:=MinDouble;
  for i:=1 to Length(Values) do
  begin
    if SortArrClass.Arr[i-1]<>PrevValue then
    begin
     inc(ind);
      for j:=1 to Length(Values) do
      begin
       if SortArrClass.Arr[i-1]=Values[j-1] then NewIds[j-1]:=ind;
      end;
    end;
    PrevValue:=SortArrClass.Arr[i-1];
  end;
  MaxRank:=Ind;
  SortArrClass.Free;

end;

procedure RangeByValues(Values:TDoubleArr; var NewIds:TIntArr);
var
 i:integer;
 SortArrClass:TSortArrClass;
begin
  if Length(Values)=0 then exit;
  SortArrClass:=TSortArrClass.Create;
  SortArrClass.ArrLength:=Length(Values);
  SetLength(SortArrClass.ArrIds,SortArrClass.ArrLength);
  for i:=1 to Length(Values) do SortArrClass.ArrIds[i-1]:=i;
  CopyDoubleArr(Values,SortArrClass.Arr,SortArrClass.ArrLength);
  SortArrClass.RunSort;
  CopyIntArr(SortArrClass.ArrIds,NewIds,SortArrClass.ArrLength);
  SortArrClass.Free;
end;

{ TSortArrClass }

procedure TSortArrClass.ExchangeValues(Item1, Item2: integer);
var
 IntTmp:integer;
 ValueTmp:double;
begin
 ValueTmp:=Arr[Item1-1];
 Arr[Item1-1]:=Arr[Item2-1];
 Arr[Item2-1]:=ValueTmp;
 IntTmp:=ArrIds[Item1-1];
 ArrIds[Item1-1]:=ArrIds[Item2-1];
 ArrIds[Item2-1]:=IntTmp;
end;

function TSortArrClass.GetValue(I: integer): double;
begin
 Result:=Arr[i-1];
 if UseAbs then Result:=Abs(Result);
end;

procedure TSortArrClass.RunSlowlySort;
begin
 SlowlySort(1,ArrLength);
end;

procedure TSortArrClass.RunSort;
begin
 QuickSort(1,ArrLength);
end;
{ TSortVarClass }


procedure SortIntArr(var Values:TIntArr);
var
 i:integer;
begin
 with TSortArrClass.Create do
 begin
  ArrLength:=Length(Values);
  SetLength(ArrIds,ArrLength);
  SetLength(Arr,ArrLength);
  for i:=1 to Length(Values) do Arr[i-1]:=Values[i-1];
  RunSort;
  for i:=1 to Length(Values) do Values[i-1]:=Round(Arr[i-1]);
  Free;
 end;
end;

procedure SortLongWordArr(var Values:array of LongWord);
var
 i:integer;
begin
 with TSortArrClass.Create do
 begin                               
  ArrLength:=Length(Values);
  SetLength(ArrIds,ArrLength);
  SetLength(Arr,ArrLength);
  for i:=1 to Length(Values) do Arr[i-1]:=Values[i-1];
  RunSort;
  for i:=1 to Length(Values) do Values[i-1]:=Round(Arr[i-1]);
  Free;
 end;
end;

procedure SortByteArr(const Values:TByteArr; var SortValues:TByteArr);
var
 i:integer;
begin
 if Length(Values)=0 then begin SetLength(SortValues,0); exit; end;
 with TSortArrClass.Create do
 begin
  ArrLength:=Length(Values);
  SetLength(ArrIds,ArrLength);
  SetLength(Arr,ArrLength);
  SetLength(SortValues,ArrLength);
  for i:=1 to Length(Values) do Arr[i-1]:=Values[i-1];
  RunSort;
  for i:=1 to Length(Values) do SortValues[i-1]:=Round(Arr[i-1]);
  Free;
 end;
end;

end.

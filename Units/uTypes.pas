unit uTypes;

interface
type
 TWordPoint=record
 X,Y:Word;
 end;
 T0IntArr=array [1..1000] of integer;
 PIntArr=^T0IntArr;
 TIntArr=array of integer;
 TDoubleArr=array of double;
 TByteArr=array of Byte;
 T2DByteArr=array of TByteArr;
 TBoolArr=array of boolean;
 T2DBoolArr=array of TBoolArr;
 T2DDoubleArr=array of TDoubleArr;
 T3DDoubleArr=array of T2DDoubleArr;
 T2DSingleArr=array of array of single;
 T2DIntArr=array of TIntArr;
 T3DIntArr=array of T2DIntArr;
 TStringArr=array of string;
 TWideStringArr=array of widestring; { H2430: promoted from builder dcu/uTypes (H2429 master) }
 T2DStringArr=array of TStringArr;
 TPointArr=Array of tWordPoint;

procedure CopyIntArr(const Arr1:TIntArr; var Arr2:TIntArr);
procedure Copy2DIntArr(const Arr1:T2DIntArr; var Arr2:T2DIntArr);
procedure Copy2DDoubleArr(const Arr1:T2DDoubleArr; var Arr2:T2DDoubleArr);

implementation
 uses SysUtils;

procedure CopyIntArr(const Arr1:TIntArr; var Arr2:TIntArr);
var
 i:integer;
begin
 SetLength(Arr2,Length(arr1));
 for i:=1 to Length(arr1) do
 begin
   Arr2[i-1]:=Arr1[i-1];
 end;
end;
procedure Copy2DIntArr(const Arr1:T2DIntArr; var Arr2:T2DIntArr);
var
 i,j:integer;
begin
 SetLength(Arr2,Length(arr1));
 for i:=1 to Length(arr1) do
 begin
  SetLength(Arr2[i-1],Length(arr1[i-1]));
  for j:=1 to Length(arr1[i-1]) do
   Arr2[i-1,j-1]:=Arr1[i-1,j-1];
 end;
end;
procedure Copy2DDoubleArr(const Arr1:T2DDoubleArr; var Arr2:T2DDoubleArr);
var
 i,j:integer;
begin
 SetLength(Arr2,Length(arr1));
 for i:=1 to Length(arr1) do
 begin
  SetLength(Arr2[i-1],Length(arr1[i-1]));
  for j:=1 to Length(arr1[i-1]) do
   Arr2[i-1,j-1]:=Arr1[i-1,j-1];
 end;
end;

initialization
 DecimalSeparator:='.';
 DateSeparator:='.';

end.







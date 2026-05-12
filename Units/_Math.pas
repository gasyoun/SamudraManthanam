Unit _math ;

{$MODE Delphi}

  {$N+}
interface
type
  TDoubleDynArray = array of Double;

procedure MeanStdDevWithoutOutliers(
  var Arr: TDoubleDynArray;
  out MeanVal, StdVal: Double;
  out OutlierCount: Integer;
  k: Double = 2.0);

implementation

uses
  Math, SysUtils;


procedure MeanStdDevWithoutOutliers(
  var Arr: TDoubleDynArray;
  out MeanVal, StdVal: Double;
  out OutlierCount: Integer;
  k: Double = 2.0);
var
  Cleaned: TDoubleDynArray;
  i, n: Integer;
  Sum, SumSq, Val: Double;
begin
  OutlierCount := 0;

  if Length(Arr) < 2 then
  begin
    MeanVal := NaN;
    StdVal := NaN;
    OutlierCount := 0;
    Exit;
  end;

  // 1. Первичный расчёт среднего и σ
  Sum := 0;
  for i := 0 to High(Arr) do
    Sum := Sum + Arr[i];
  MeanVal := Sum / Length(Arr);

  SumSq := 0;
  for i := 0 to High(Arr) do
    SumSq := SumSq + Sqr(Arr[i] - MeanVal);
  StdVal := Sqrt(SumSq / (Length(Arr)-1));

  // 2. Удаление выбросов
  SetLength(Cleaned, 0);
  for i := 0 to High(Arr) do
  begin
    Val := Arr[i];
    if Abs(Val - MeanVal) <= k * StdVal then
    begin
      n := Length(Cleaned);
      SetLength(Cleaned, n + 1);
      Cleaned[n] := Val;
    end else
      Inc(OutlierCount);
  end;

  if Length(Cleaned) < 2 then
  begin
    MeanVal := NaN;
    StdVal := NaN;
    SetLength(Arr, 0);
    Exit;
  end;

  // 3. Пересчёт среднего и σ по очищенному массиву
  Sum := 0;
  for i := 0 to High(Cleaned) do
    Sum := Sum + Cleaned[i];
  MeanVal := Sum / Length(Cleaned);

  SumSq := 0;
  for i := 0 to High(Cleaned) do
    SumSq := SumSq + Sqr(Cleaned[i] - MeanVal);
  StdVal := Sqrt(SumSq / (Length(Cleaned)-1));

  // 4. Перезапишем исходный массив очищенными данными
  Arr := Cleaned;
end;

End.



unit _winutils;

{$mode objfpc}{$H+}

interface


uses
  LCLIntf, LCLType,
  Windows,Classes, SysUtils, DateUtils, Grids, Graphics, StdCtrls;

procedure DeleteFilesFromDir(ADir:string;Mask:string);
procedure GetFilesByMask(const SourceDir,mask:string;var Files:TStringList);
Function CleanFileName (AFileName:string):string;
Function GetUniqueFileName(const FileName: string):string;
Function GetValidFileName(const FileName: string): string;
function GetProcessorCount: Integer;
procedure CreateEmptyFile(const FileName: string);
function DownloadFile(const url, filename: string): Boolean;
{Обе функции работают корректно. Первая версия проще и быстрее, вторая использует встроенные функции работы с датами и может быть более надежной для сложных случаев.}
function FormatDateToMonthYear(const Date: TDate): string;
function FormatDateToMonthYear2(const Date: TDate): string;
//function CheckForUpdates(const serverUrl: string; const currentVersion: string): Boolean;
procedure SortMonthYearStringList(var StringList: TStringList);
procedure AutoSizeGridColumns(Grid: TStringGrid);
function FormatCurrencyEx(Value: Currency; DecimalPlaces: Integer = 2;
                         ThousandSeparator: Char = ' '; DecimalSeparator: Char = ','): string;
function GetListBoxNeededWidth(ALB: TListBox): Integer;
procedure AdjustAllRowHeights(Grid: TStringGrid);
Procedure CleanStringGrid(Grid: TStringGrid);

implementation

Uses fphttpclient;
procedure CreateEmptyFile(const FileName: string);
var
  F: File;
begin
  AssignFile(F, FileName);
  Rewrite(F);
  CloseFile(F);
end;
function GetProcessorCount: Integer;
var
  SystemInfo: SYSTEM_INFO;
begin
  GetSystemInfo(SystemInfo);
  Result := SystemInfo.dwNumberOfProcessors;
end;
function GetValidFileName(const FileName: string): string;
const
  InvalidChars: set of Char = ['/', '\', ':', '*', '?', '"', '<', '>', '|'];
var
  i: Integer;
begin
  Result := FileName;
  for i := 1 to Length(Result) do
    if CharInSet(Result[i], InvalidChars) then
      Result[i] := '_'; // заменяем недопустимый символ на символ подчеркивания
  Result:=StringReplace(Result,' ','_',[rfReplaceAll]);// заменяем пробел на подчеркивание
  Result:=StringReplace(Result,'__','_',[rfReplaceAll]);// заменяем два подчеркивания на одно
end;

Function GetUniqueFileName(const FileName: string):string;
var
  NewFileName: string;
  Counter: integer;
begin
  if FileExists(FileName) then
  begin
    Counter := 1;
    repeat
      NewFileName := ChangeFileExt(FileName, '') + '('+IntToStr(Counter) + ')'+ExtractFileExt(FileName);
      Inc(Counter);
    until not FileExists(NewFileName);
  end
  else
    NewFileName := FileName;
  Result:=NewFileName;
end;
procedure DeleteFilesFromDir(ADir:string;Mask:string);
var
  SearchRec: TSearchRec;
  result:integer;
begin
  Result := FindFirst(ADir+Mask, faAnyFile, SearchRec);
  while Result = 0 do
  begin
    DeleteFile(Adir+SearchRec.Name);
    Result := FindNext(SearchRec);
  end;
  FindClose(SearchRec);
end;

procedure GetFilesByMask(const SourceDir,mask:string;var Files:TStringList);
var
  SearchRec: TSearchRec;
  result:integer;
begin
  Result := FindFirst(SourceDir+mask, faArchive, SearchRec);
  while Result = 0 do
  begin
   Files.Add(SourceDir+SearchRec.Name);
   Result := FindNext(SearchRec);
  end;
  FindClose(SearchRec);
end;

function CleanFileName(AFileName: string): string;
var
  Path:string;
begin
{Какие символы не могут использоваться в имени файла?
Ответы1. В Windows система не позволит использовать в именах файлов следущие символы, так как они являются служебными:
\ / : * ? " < > | + Пробел и точка также не допускаются в конце имени файла.}
  Path:=ExtractFilePath(AFileName);
  Result:= ExtractFileName(AFileName);
  Result:= StringReplace(Result, '\', '_', [rfReplaceAll]);
  Result:= StringReplace(Result, '/', '_', [rfReplaceAll]);
  Result:= StringReplace(Result, ':', '_', [rfReplaceAll]);
  Result:= StringReplace(Result, '*', '_', [rfReplaceAll]);
  Result:= StringReplace(Result, '?', '_', [rfReplaceAll]);
  Result:= StringReplace(Result, '"', '_', [rfReplaceAll]);
  Result:= StringReplace(Result, '<', '_', [rfReplaceAll]);
  Result:= StringReplace(Result, '>', '_', [rfReplaceAll]);
  Result:= StringReplace(Result, ':', '_', [rfReplaceAll]);
  Result:= StringReplace(Result, '|', '_', [rfReplaceAll]);
  Result:= StringReplace(Result, '+', '_', [rfReplaceAll]);
  Result:= Path+Result;
end;

function DownloadFile(const url, filename: string): Boolean;
var
  http: TFPHTTPClient;
begin
  http := TFPHTTPClient.Create(nil);
  try
    http.AllowRedirect := True;
    http.Get(url, filename);
    Result := True;
  except
    Result := False;
  end;
  http.Free;
end;

function FormatDateToMonthYear2(const Date: TDate): string;
var
  Day, Month, Year: Integer;
  RussianMonths: array[1..12] of string;
  DateStr:string;
begin
  DateStr:=DateToStr(Date);
  // Массив с названиями месяцев на русском
  RussianMonths[1] := 'январь';
  RussianMonths[2] := 'февраль';
  RussianMonths[3] := 'март';
  RussianMonths[4] := 'апрель';
  RussianMonths[5] := 'май';
  RussianMonths[6] := 'июнь';
  RussianMonths[7] := 'июль';
  RussianMonths[8] := 'август';
  RussianMonths[9] := 'сентябрь';
  RussianMonths[10] := 'октябрь';
  RussianMonths[11] := 'ноябрь';
  RussianMonths[12] := 'декабрь';

  try
    // Парсим дату из строки
    Day := StrToInt(Copy(DateStr, 1, 2));
    Month := StrToInt(Copy(DateStr, 4, 2));
    Year := StrToInt(Copy(DateStr, 7, 4));

    // Проверяем корректность месяца
    if (Month < 1) or (Month > 12) then
      raise Exception.Create('Неверный номер месяца');

    // Формируем результат
    Result := RussianMonths[Month] + ' ' + IntToStr(Year);

  except
    on E: Exception do
    begin
      // Обработка ошибок парсинга
      Result := 'Ошибка: Неверный формат даты';
      // Можно также использовать: raise Exception.Create('Неверный формат даты');
    end;
  end;
end;

function FormatDateToMonthYear(const Date: TDate): string;
var
  RussianMonths: array[1..12] of string;
  ADate: TDateTime;
  Year, Month, Day: Word;
  DateStr:string;
begin
  DateStr:=DateToStr(Date);
  RussianMonths[1] := 'январь';
  RussianMonths[2] := 'февраль';
  RussianMonths[3] := 'март';
  RussianMonths[4] := 'апрель';
  RussianMonths[5] := 'май';
  RussianMonths[6] := 'июнь';
  RussianMonths[7] := 'июль';
  RussianMonths[8] := 'август';
  RussianMonths[9] := 'сентябрь';
  RussianMonths[10] := 'октябрь';
  RussianMonths[11] := 'ноябрь';
  RussianMonths[12] := 'декабрь';

  try
    // Преобразуем строку в дату
    ADate := StrToDate(DateStr, 'dd.mm.yyyy', '.');
    DecodeDate(ADate, Year, Month, Day);

    Result := RussianMonths[Month] + ' ' + IntToStr(Year);

  except
    on E: Exception do
      Result := 'Ошибка: Неверный формат даты';
  end;
end;


// Объявляем функцию сравнения отдельно
function MonthYearCompare(List: TStringList; Index1, Index2: Integer): Integer;
var
  RussianMonths: TStringList;

  function MonthNameToNumber(const MonthName: string): Integer;
  begin
    Result := RussianMonths.IndexOf(MonthName) + 1;
    if Result = 0 then
      Result := 13; // Для некорректных значений ставим в конец
  end;

var
  Parts1, Parts2: TStringList;
  Month1, Month2, Year1, Year2: Integer;
begin
  // Создаем список месяцев в правильном порядке
  RussianMonths := TStringList.Create;
  try
    RussianMonths.Add('январь');
    RussianMonths.Add('февраль');
    RussianMonths.Add('март');
    RussianMonths.Add('апрель');
    RussianMonths.Add('май');
    RussianMonths.Add('июнь');
    RussianMonths.Add('июль');
    RussianMonths.Add('август');
    RussianMonths.Add('сентябрь');
    RussianMonths.Add('октябрь');
    RussianMonths.Add('ноябрь');
    RussianMonths.Add('декабрь');

    Parts1 := TStringList.Create;
    Parts2 := TStringList.Create;
    try
      // Разбиваем строки на части: "месяц" и "год"
      Parts1.Delimiter := ' ';
      Parts1.DelimitedText := List[Index1];

      Parts2.Delimiter := ' ';
      Parts2.DelimitedText := List[Index2];

      // Если формат некорректный, ставим в конец
      if (Parts1.Count < 2) or (Parts2.Count < 2) then
      begin
        Result := CompareStr(List[Index1], List[Index2]);
        Exit;
      end;

      // Получаем числовые значения месяцев и годов
      Month1 := MonthNameToNumber(Parts1[0]);
      Month2 := MonthNameToNumber(Parts2[0]);
      Year1 := StrToIntDef(Parts1[1], 0);
      Year2 := StrToIntDef(Parts2[1], 0);

      // Сначала сравниваем годы
      if Year1 < Year2 then
        Result := -1
      else if Year1 > Year2 then
        Result := 1
      else
      begin
        // Если годы равны, сравниваем месяцы
        if Month1 < Month2 then
          Result := -1
        else if Month1 > Month2 then
          Result := 1
        else
          Result := 0;
      end;

    finally
      Parts1.Free;
      Parts2.Free;
    end;

  finally
    RussianMonths.Free;
  end;
end;

procedure SortMonthYearStringList(var StringList: TStringList);
begin
  // Используем отдельную функцию сравнения
  StringList.Sorted:=False;
  StringList.CustomSort(@MonthYearCompare);
end;

procedure AutoSizeGridColumns(Grid: TStringGrid);
var
  i, j, MaxWidth, TempWidth: Integer;
  TempCanvas: TCanvas;
  Lines: TStringList;
  Part, Value: String;
  TagStart, TagEnd: Integer;
  k: Integer;
begin
  TempCanvas := Grid.Canvas;
  TempCanvas.Font.Assign(Grid.Font); // используем шрифт грида

  Lines := TStringList.Create;
  try
    for i := 0 to Grid.ColCount - 1 do
    begin
      MaxWidth := 0;

      // Проверяем заголовок
      if Grid.FixedRows > 0 then
      begin
        TempWidth := TempCanvas.TextWidth(Grid.Cells[i, 0]) + 20;
        if TempWidth > MaxWidth then
          MaxWidth := TempWidth;
      end;

      // Проверяем все ячейки
      for j := Grid.FixedRows to Grid.RowCount - 1 do
      begin
        Lines.Clear;
        Lines.StrictDelimiter := True;
        Lines.Delimiter := ';';
        Lines.DelimitedText := Grid.Cells[i, j];

        for k := 0 to Lines.Count - 1 do
        begin
          Part := Lines[k];

          // Ищем тег вида <...>
          TagStart := Pos('<', Part);
          TagEnd := Pos('>', Part);
          Value := Part;
          if (TagStart > 0) and (TagEnd > TagStart) then
            Delete(Value, TagStart, TagEnd - TagStart + 1);

          // измеряем ширину текста без тега
          TempWidth := TempCanvas.TextWidth(Value) + 20;
          if TempWidth > MaxWidth then
            MaxWidth := TempWidth;
        end;
      end;

      // ограничение минимальной и максимальной ширины
      if MaxWidth < 30 then MaxWidth := 30;
      if MaxWidth > 500 then MaxWidth := 500;

      Grid.ColWidths[i] := MaxWidth;
    end;
  finally
    Lines.Free;
  end;
end;

function FormatCurrencyEx(Value: Currency; DecimalPlaces: Integer = 2;
                         ThousandSeparator: Char = ' '; DecimalSeparator: Char = ','): string;
var
  FormatSettings: TFormatSettings;
begin
  // Получаем системные настройки формата
  FormatSettings := DefaultFormatSettings;

  // Меняем разделители по желанию
  FormatSettings.ThousandSeparator := ThousandSeparator;
  FormatSettings.DecimalSeparator := DecimalSeparator;

  // Форматируем с нужным количеством знаков после запятой
  case DecimalPlaces of
    0: Result := FormatFloat('#,##0', Value, FormatSettings);
    1: Result := FormatFloat('#,##0.0', Value, FormatSettings);
    2: Result := FormatFloat('#,##0.00', Value, FormatSettings);
    3: Result := FormatFloat('#,##0.000', Value, FormatSettings);
    else Result := FormatFloat('#,##0.00', Value, FormatSettings);
  end;
end;

function GetListBoxNeededWidth(ALB: TListBox): Integer;
var
  i, w: Integer;
  sbWidth: Integer;
begin
  Result := 0;
  ALB.Canvas.Font.Assign(ALB.Font);

  for i := 0 to ALB.Items.Count - 1 do
  begin
    w := ALB.Canvas.TextWidth(ALB.Items[i]);
    if w > Result then
      Result := w;
  end;

  // Добавляем ширину вертикального скролбара (если он будет)
  sbWidth := GetSystemMetrics(SM_CXVSCROLL);

  // + небольшой отступ для красоты
  Inc(Result, sbWidth + 10);
end;

procedure AdjustAllRowHeights(Grid: TStringGrid);
var
  Row, Col: Integer;
  R: TRect;
  S, Part, Value: String;
  Lines: TStringList;
  MaxHeight, W, H, TotalHeight: Integer;
  TagStart, TagEnd: Integer;
  k: Integer;
begin
  Grid.Canvas.Font.Assign(Grid.Font);
  Lines := TStringList.Create;
  try
    for Row := 0 to Grid.RowCount - 1 do
    begin
      MaxHeight := Grid.DefaultRowHeight;

      for Col := 0 to Grid.ColCount - 1 do
      begin
        S := Grid.Cells[Col, Row];

        // разбиваем строку на части по ;
        Lines.Clear;
        Lines.StrictDelimiter := True;
        Lines.Delimiter := ';';
        Lines.DelimitedText := S;

        TotalHeight := 0;

        for k := 0 to Lines.Count - 1 do
        begin
          Part := Lines[k];

          // удаляем тег <...>
          TagStart := Pos('<', Part);
          TagEnd := Pos('>', Part);
          Value := Part;
          if (TagStart > 0) and (TagEnd > TagStart) then
            Delete(Value, TagStart, TagEnd - TagStart + 1);

          // ширина ячейки (минус небольшой отступ)
          W := Grid.ColWidths[Col] - 4;
          if W < 1 then Continue;

          R := Rect(0, 0, W, 0);

          // рассчитываем высоту текста с переносом
          DrawText(Grid.Canvas.Handle, PChar(Value), Length(Value), R,
            DT_WORDBREAK or DT_RIGHT or DT_NOPREFIX or DT_CALCRECT);

          H := R.Bottom - R.Top + 2; // небольшой запас сверху/снизу
          Inc(TotalHeight, H);
        end;

        if TotalHeight > MaxHeight then
          MaxHeight := TotalHeight;
      end;

      Grid.RowHeights[Row] := MaxHeight;
    end;
  finally
    Lines.Free;
  end;
end;
Procedure CleanStringGrid(Grid: TStringGrid);
var
  i,j:integer;
begin
  for i:=1 to Grid.ColCount do
  for j:=1 to Grid.RowCount do
   Grid.Cells[i-1,j-1]:='';
end;

end.


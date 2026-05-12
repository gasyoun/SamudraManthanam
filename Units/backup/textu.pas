unit textu;

{$mode objfpc}{$H+}

interface


uses
  Classes, SysUtils;
function CutNextFromEnd(var Source: string): string;
function CutNextUseDelimiterNoTrim(var Source: string;Delimiter:string): string;
function IsUtf8CharInLimits(const p, left, right: PChar): boolean;

implementation


{------------------------------------------------------------------------------}
{function IsUtf8CharRus(const p: PChar): boolean;
  begin
    // Кириллица упорядочена в таблице Unicode по алфавиту, при этом сначала
    //   идут заглавные буквы, а потом строчные, т.е. [А...Я, а..я]
    // Таким образом заглавная "А" и строчная "я" являются левой и правой
    //   границами диапазона
    Result := IsUtf8CharInLimits(p, 'А', 'я');
  end;}
function IsUtf8CharInLimits(const p, left, right: PChar): boolean;
  var
    CharLen: integer; // длина UTF в байтах, здесь не нужна, просто требуется в функции
    U: integer; // Юникод символа
  begin
    U := UTF8CharacterToUnicode(p, CharLen);
    if U = 0 then
      begin
        Result := false;
        exit;
      end;
    Result := (
      (U >= UTF8CharacterToUnicode(left, CharLen)) and
      (U <= UTF8CharacterToUnicode(right, CharLen)));
  end;

function InvertStr(const S:string):String;
var
 i:integer;
begin
 result:='';
 for i:=1 to Length(S) do result:=ConCat(result,S[Length(S)-i+1]);
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

end.


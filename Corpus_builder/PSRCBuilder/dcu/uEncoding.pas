unit uEncoding;
{$MODE Delphi}
{$H+}
{ Corpus_builder unified encoding layer (H2428).

  Call sites use ToUTF8 / FromUTF8 instead of raw AnsiToUTF8 / UTF8ToAnsi.
  Character-safe helpers re-export LazUTF8 (UTF8Length / UTF8Copy) — same stack
  as Index.

  Under Lazarus 4 / FPC 3.2.2 with UTF8_RTL the process string type is UTF-8.
  ToUTF8/FromUTF8 (string) are intentional identities that document I/O
  direction and keep one retarget point. WideString overload uses UTF8Encode.

  Measured: LazUTF8.SysToUTF8/UTF8ToSys are also identity under UTF8_RTL, so
  they are equivalent here. Golden case01 was rebaselined this pass because the
  H2427 expected files still carried CP-1251 Err.txt bytes from the pre-layer
  binary path; pure UTF-8 I/O changes those bytes. }

interface

uses
  SysUtils;

{ Emit / store as UTF-8 process string (replaces AnsiToUTF8 at call sites). }
function ToUTF8(const S: string): string; overload;
function ToUTF8(const S: WideString): string; overload;

{ Bridge from UTF-8 process string (replaces UTF8ToAnsi at call sites). }
function FromUTF8(const S: string): string;

{ UTF-8 character-safe length/copy (LazUTF8). }
function EncUTF8Length(const S: string): PtrInt;
function EncUTF8Copy(const S: string; StartCharIndex, CharCount: PtrInt): string;

implementation

uses
  LazUTF8;

function ToUTF8(const S: string): string;
begin
  Result := S;
end;

function ToUTF8(const S: WideString): string;
begin
  Result := UTF8Encode(S);
end;

function FromUTF8(const S: string): string;
begin
  Result := S;
end;

function EncUTF8Length(const S: string): PtrInt;
begin
  Result := UTF8Length(S);
end;

function EncUTF8Copy(const S: string; StartCharIndex, CharCount: PtrInt): string;
begin
  Result := UTF8Copy(S, StartCharIndex, CharCount);
end;

end.

Unit CalcSimU;
{$MODE Delphi}
{ Delphi}
interface
uses math, uTypes;
type
 t3dPoint=array [1..3] of single;
procedure inc_double(var A:double; const B:double); 
Function Angle2D ( x1,y1,x2,y2:real ):real;{in radians}
Function Angle3D ( x1,y1,z1,x2,y2,z2,SignMark:real):real;{in gradus}
Function GetWordByte (W:word ; b:byte ):byte;
Function Dist (x1,x2,y1,y2,z1,z2:real):Real;
Function Dist2D (x1,x2,y1,y2:real):Real;
Function Log (osn:real;X:real ):real;
Function Lb ( X:real ):real;
Function isBit  ( Value :longint; bit :byte ):boolean;
Function ByteToBitStr(b:byte):string;
procedure SetByteBit( var Value:byte;bit:byte;State:Boolean);
procedure SetWordBit( var Value:word;bit:byte;State:Boolean);
function GetRad (grd:real):real;
procedure GetDecart (fi,t,R:real ;var  x,y,z:real );
Function GetScalMult (a1,a2,a3,B1,b2,b3:real):real;
Function GetSin (a1,a2,a3,B1,b2,b3:real):real;
Function GetCos (a1,a2,a3,B1,b2,b3:real):real;
Function CalcCNK (n,k:integer):Int64	;
{function Min (x,y:integer):integer;
function Max (x,y:integer):integer;}
function Sign (Value:double):shortint;
function tanh (Value:double):double;
procedure Rotate3DCoord (var co1,co2,co3:single; RotX,RotY,RotZ:single);
procedure GetPlaneEquation(x1,y1,z1,x2,y2,z2,x3,y3,z3:double; var A,B,C,D:double);
Function VectMult ( Pc1,Pc2,Pc3:t3dPoint  ):single;
function Probability(const Energies:TDoubleArr; ElmPos:integer; UseEnergies:boolean):double;
function GetBoolCount(const BoolArr:array of boolean; CurBool:boolean):integer;
procedure RotateAlongVector(var RotX,RotY,RotZ:single; const vx,vy,vz:single);
function GetPointDistanceFromEllipse(const Axes,T_Arr:TDoubleArr;AxesCoef:double):double;
implementation

function GetPointDistanceFromEllipse(const Axes,T_Arr:TDoubleArr;AxesCoef:double):double;
var
 i:integer;
begin
 result:=-1;
 for i:=1 to length(Axes) do
  result:=result+sqr(T_Arr[i-1])/sqr(AxesCoef*Axes[i-1]);
end;

function GetBoolCount(const BoolArr:array of boolean; CurBool:boolean):integer;
var
 i:integer;
begin
 result:=0;
 for i:=0 to Length(BoolArr)-1 do
  if BoolArr[i]=CurBool then inc(result);
end;

function Probability(const Energies:TDoubleArr; ElmPos:integer;UseEnergies:boolean):double;
const
 T=298.15;
 R=1.987*1E-3;// kcal/(mol *K)
 RT=R*T;
var
 i:byte;
 under_exp:double;
 ArrLength:integer;
begin
 result:=1;
 ArrLength:=Length(Energies);
 if not UseEnergies then begin Result:=Result/ArrLength; exit; end;
 for i:=1 to ArrLength do
 if i <> ElmPos then
  begin
    under_exp:=  ( Energies[ElmPos-1] - Energies[i-1]) /RT;
    if   under_exp > 5E4
    then  begin  result:=0; exit;  end;
    if under_exp > -5E5 then
    result:= result +  Exp   ( under_exp )  ;
  end;
 result:=1/result;
end;

Function VectMult ( Pc1,Pc2,Pc3:t3dPoint  ):single;
var Sl1,Sl2,Sl3:real;
begin
 Sl1:=  Pc1[1] * ( Pc2[2] * Pc3 [3]  - Pc3[2] * Pc2 [3] );
 Sl2:=  Pc1[2] * ( Pc2[1] * Pc3 [3]  - Pc3[1] * Pc2 [3] );
 Sl3:=  Pc1[3] * ( Pc2[1] * Pc3 [2]  - Pc3[1] * Pc2 [2] );
 result:= Sl1 - Sl2 + Sl3;
end;

function Sign (Value:double):shortint;
begin
 if Value<0 then result:=-1 else
 if Value>0 then result:=1 else
 result:=0;
end;
{function Min (x,y:integer):integer;
begin
 if x<=y then Min:=x else min:=y;
end;
function Max (x,y:integer):integer;
begin
 if x>=y then Max:=x else max:=y;
end;}
function Fact (N:longint):Extended;
var P:Extended;
    i:longint;
begin
 P:=1;
 for i:=1 to n do P:=P*i;
 Fact:=p;
end;

Function CalcProduction(nFrom,nTo:integer):extended;
var
 i:integer;
begin
 result:=1;
 for i:=nFrom to nTo do result:=result*i;
end;

Function CalcCNK (n,k:integer):Int64	;
var
 a,b:extended;
begin
 if n<k then result:=0 else
 if n>k then
 begin
  a:=CalcProduction(n-k+1,n);
  b:=Fact(k);
  result:=Round(a/b);
 end else result :=1;
end;

Function Angle3D ( x1,y1,z1,x2,y2,z2,SignMark:real):real;{in gradus}
var an:double;
 cos_:double;
begin
 cos_:=GetCos(x1,y1,z1,x2,y2,z2);
 an:=arccos(Cos_) ;
 if isNan(an) then an:=0;
 result:=An*180/pi;
 if SignMark<0 then result:=-result;
end;
procedure inc_double(var A:double; const B:double); 
begin
 A:=A+B;
end;

Function Angle2D ( x1,y1,x2,y2:real ):real;{in radians}
var an:real;
begin
 an:=arccos ( GetCos (x1,y1,0,x2,y2,0) ) ;
 if y1 < 0 then an:=2 * Pi - an;
 Angle2D:=An;
end;

{function arcSin (x:real ):real;
begin
if x<>1 then ArcSin := ArcTan (x/sqrt (1-sqr (x))) else ArcSin:=Pi/2;
end;
function arcCos (x:real ):real;
begin
 if x<0 then ArcCos := Pi+ArcTan (sqrt (1-sqr (x)) /x) else
 if x>0 then ArcCos := ArcTan (sqrt (1-sqr (x)) /x) else
 ArcCos:=Pi/2;
end;}
procedure GetDecart (fi,t,R:real ;var  x,y,z:real );
begin
 x:=sin( GetRad ( fi ) );
 y:=Sin( GetRad ( t ) );
 z:=Cos( GetRad ( fi ) );
end;
Function GetScalMult (a1,a2,a3,B1,b2,b3:real):real;
begin
 GetScalMult:=a1*b1+a2*b2+a3*b3;
end;
Function GetSin (a1,a2,a3,B1,b2,b3:real):real;
// через векторное произведение векторов
var
 AbsA,AbsB,AbsAB:single;
begin
 // модуль вект произв
 AbsAB:=sqr(a2*b3-a3*b2)+sqr(a3*b1-a1*b3)+sqr(a1*b2-a2*b1);
 AbsAB:=sqrt(AbsAB);
 AbsA:=sqrt(sqr(a1)+sqr(a2)+sqr(a3));
 AbsB:=sqrt(sqr(b1)+sqr(b2)+sqr(b3));
 if (AbsA=0) or (AbsB=0)
  then result:=0
  else result:=AbsAB/AbsA/AbsB;
end;

Function GetCos (a1,a2,a3,B1,b2,b3:real):real;
var d1,d2:real;
    sp:real;
begin
 d1:=Dist (a1,0,a2,0,a3,0);
 d2:=Dist (b1,0,b2,0,b3,0) ;
 sp:=GetScalMult (a1,a2,a3,B1,b2,b3);
 if (d1<1E-6) or (d2<1E-6) then
   GetCos:=0;
 if sp=0 then GetCos:=sp else GetCos:=sp/d1/d2;
end;

function GetRad (grd:real):real;
begin
 GetRad:=grd/180*Pi;
end;
Function GetWordByte (W:word ; b:byte ):byte;
var a:array [1..2] of byte absolute w;
begin
result:=a[b]
end;
procedure SetWordBit( var Value:word;bit:byte;State:Boolean);
var
 v2:word;
begin
 v2:=round( IntPower(2,bit));
 Value :=Value or v2;
 if not State then  Value :=Value xor v2;
end;
procedure SetByteBit( var Value:byte;bit:byte;State:Boolean);
var
 v2:byte;
begin
 v2:=round( IntPower(2,bit));
 Value :=Value or v2;
 if not State then  Value :=Value xor v2;
end;

Function isBit  ( Value :longint; bit :byte ):boolean;
begin
 isBit:= odd( Value shr bit ) ;
end;
Function ByteToBitStr(b:byte):string;
var
 i:integer;
 c:char;
begin
 result:='';
 for i:=1 to 8 do
 begin
  if isBit(b,i) then c:='1' else c:='0';
  result:=concat(result,C);
 end;
end;
Function Lb ( X:real ):real;
begin
 lb :=ln ( x )/ ln ( 2 )
end;

Function Log (osn:real;X:real ):real;
begin
 log :=ln (x )/ ln (osn )
end;
Function Dist2D (x1,x2,y1,y2:real):Real;
begin
result:= Sqrt  ( Sqr (X1-x2) +Sqr (Y1-Y2)  ) ;
end;

Function Dist (x1,x2,y1,y2,z1,z2:real):Real;
begin
Dist:= Sqrt  ( Sqr (X1-x2) +Sqr (Y1-Y2) +Sqr (Z1-Z2) ) ;
end;
Function DegR (X,Y:real ):real;
begin
 if x<>0 then  DegR:= Exp  (  Y * Ln  ( X ) ) else  degr:=0;
end;
Function DegI (X:real;Y:byte ):real;
begin
 if x<>0 then  Degi:= Exp  (  Y * Ln  ( X ) ) else  degi:=0;
end;
function tanh (Value:double):double;
begin
 result:=(exp(Value)-exp(-Value))/(exp(Value)+exp(-Value));
end;

procedure RotateAlongVector(var RotX,RotY,RotZ:single; const vx,vy,vz:single);
var
 VectorLength:double;
 Angle:single;
 px,py,pz:single;
begin
 Rotate3DCoord(px,py,pz,RotX,RotY,RotZ);
 // помещаем ось Х координат в вектор
 VectorLength:=sqrt(sqr(vx)+sqr(vy)+sqr(vz));
 Angle:=Angle3d(vx,vy,vz,1,0,0,vx);
 Rotate3DCoord(px,py,pz,0,0,Angle);
 Rotate3DCoord(px,py,pz,VectorLength,0,0);
 Rotate3DCoord(px,py,pz,0,0,-Angle);
 RotX:=Angle3D(px,py,pz,0,1,1,px);
 RotY:=Angle3D(px,py,pz,1,0,1,py);
 RotZ:=Angle3D(px,py,pz,1,1,0,pz);
end;
procedure Rotate3DCoord(var co1,co2,co3:single; RotX,RotY,RotZ:single);
var x1,y1,z1:double;
begin
 RotX:=GetRad (RotX);
 Roty:=GetRad (Roty);
 Rotz:=GetRad (Rotz);
  {по оси y}
 x1:= Co1 * Cos( RotY ) + Co3 * sin( RotY );
 z1:=-Co1 * Sin( RotY ) + Co3 * cos( RotY );
 y1:=Co2;
  {по оси z}
 Co1:=x1; Co3:=z1; Co2:=y1;
 y1:= Co2 * Cos( RotZ ) + Co1 * sin( RotZ );
 x1:=-Co2 * Sin( RotZ ) + Co1 * cos( RotZ );
 z1:=Co3;
  {по оси x}
 Co1:=x1; Co3:=z1; Co2:=y1;
 z1:= Co3 * Cos( RotX ) + Co2 * sin( RotX );
 y1:=-Co3 * Sin( RotX ) + Co2 * cos( RotX );
 x1:=Co1;
 co1:=x1;
 co2:=y1;
 co3:=z1;
end;
procedure GetPlaneEquation(x1,y1,z1,x2,y2,z2,x3,y3,z3:double; var A,B,C,D:double);
begin
 A:=(y2-y1)*(z3-z1)-(z2-z1)*(y3-y1);
 B:=-(x2-x1)*(z3-z1)+(z2-z1)*(x3-x1);
 C:=(x2-x1)*(y3-y1)-(y2-y1)*(x3-x1);
 D:=-X1*A+(Y1*B)-Z1*C;
end;

end.

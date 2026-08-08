unit statprocs;
{$MODE Delphi}
{ Delphi}
interface
 uses uTypes;
const
{types of descriptors}
 dt_real=1;
 dt_rank=2;
 dt_sign=3;

type TCoefType=( kendal,spirman);
{ Function MultyDist(var A1,b1,a2,b2:array of single ;Qelm:integer):single;}
 Function DistND(var A1,a2:array of single ;Qelm:integer):single;
 procedure MinMaxNorm(var Arr:array of single ;Qelm:word);
 procedure SumNorm2(var Arr:TDoubleArr;Qelm:integer);
 function GetTStudent(ASignLevel:single; AQ:byte):single;
// Procedure ArrToRankArr(var arr,RankArr:array of single);
 Function GetRank  ( var Arr:array of single ;Qelm:word; Cur:word):single;
 function GetMedium ( var Arr:array of single ;Qelm:word ):single;
 function MyStdDev(const Arr: array of Double): Extended;
 Procedure GetSigma ( Const Arr:array of single ;Qelm:word; var mid,sigma:single );
 Procedure GetSigmaD ( Const Arr:array of double ;Qelm:integer; var mid,sigma:double );
 function GetMiddle (var Arr:array of single ;Qelm:word ):single;
 Procedure NormArr ( var Arr:array of single ;Qelm:word);
 Function GetTrValue (var Arr,Act:array of single;Qelm:word;trvType:byte):single;
{ линейная }
 Function CoreLinear ( var X,Y:array of single;Qelm:word):single;
 Function CoreLinearDouble ( var X,Y:TDoubleArr;Qelm:integer):double;
 Function CalcQ2 ( var X,Y:TDoubleArr;Qelm:integer):Double;
{ полузнаковая }
 Function CoreHalfSign ( var As_,Ap:array of single;Qelm:word):single;
{ знаковая }
 Function CoreSign ( var A1,A2:array of single;Qelm:word):single;
{ ранговая }
 Function CoreRankRank ( var A1,A2:array of single;Qelm:word;ct:TCoefType):single;
// Function CoreRankRankFromNotRankArr ( var A1,A2:array of single;Qelm:word;ct:TCoefType):single;
// Procedure GetRanksArr(var Arr,RanksArr:array of single);
 { полуранговая }
 function CoreHalfRank  ( var Ar{ранг},Av{число}:array of single;Qelm:word):single;
 procedure GetUT (var A:array of single;Qelm:word;ct:TCoefType;Var QSv:double);
 function CamberrDist( var X,Y:array of single;Qelm:word):single;
 function GetStudentDistrPoint(ASignLevel:single; NumFreedomDeg:byte):single;
 function GetFDistrPoint(f1,f2:integer;SignLevel:single):single;
 function GetNormDistrPoint(SignLevel:single):single;
implementation
 uSes Math, uSort;
Function DistND(var A1,a2:array of single ;Qelm:integer):single;
var
 i:integer;
 sa2:single;
begin
 sa2:=0;
 for i:=low (a1) to low (a1)+qelm-1 do
 begin
   if IsNAN (A1[i]) or IsNAN (A2[i]) then continue;
   sa2:=sa2+sqr(a1[i]-a2[i]);
 end;
 Result:=sqrt(sa2);
end;

function MyStdDev(const Arr: array of Double): Extended;
var
 i:integer;
 qelm:integer;
 mid_,sigma_:double;
begin
 qelm:=Length(Arr);
 if qelm<2 then begin result:=0; exit; end;
 mid_:=0;
 for i:=low (arr) to low (arr)+qelm-1 do mid_:=mid_+arr[i];
 mid_:=mid_ / qelm;
 sigma_:=0;
 for i:=low (arr) to low (arr)+qelm-1 do sigma_:=sigma_ + sqr( arr[i] - mid_ );
 sigma_:=sqrt ( sigma_ / ( qelm - 1 ) );
// if sigma_<1E-6 then sigma_:=0;
 Result:=sigma_;
end;
{Function MultyDist(var A1,b1,a2,b2:array of single ;Qelm:integer):single;
var
 i:integer;
 sa2,sb2:single;
begin
 sa2:=0;
 sb2:=0;
 for i:=low (a1) to low (a1)+qelm-1 do
 begin
  sa2:=sa2+sqr(a1[i]-a2[i]);
  sb2:=sb2+sqr(b1[i]-b2[i]);
 end;
 Result:=sqrt(sa2+sb2);
end;}
{-------------------------------------------------------------}
 function sign (R:real):shortint;
 begin
  sign:=0;
  if r<0 then sign:=-1;
  if r>0 then sign:=+1;
 end;
 function binarysign (R:real):shortint;
 begin
  binarysign:=0;
  if r<=0 then binarysign:=-1;
  if r>0 then binarysign:=+1;
 end;
{-------------------------------------------------------------}
Function GetTrValue (var Arr,Act:array of single;Qelm:word;trvType:byte):single;
var
 i:integer;
begin
{ Sum:=0;
  for i:=low (arr) to low (arr)+qelm-1 do
 Sum:=Sum+ Arr[i]*Act[i];
 GetTrValue:=sum/qelm;}
 if TRVType=0
   then Result:=CoreHalfRank(Act,Arr,QElm)
   else Result:=CoreHalfSign(Act,Arr,QElm);
 end;
{-------------------------------------------------------------}
Function GetSum( a1,a2 : word):single;
var i:word;
   Sum:single;
begin
 sum:=0;
 for i:=a1 to a2 do sum:=sum+i;
 GetSum:=sum;
end;
{-------------------------------------------------------------}
Procedure GetSigma;
 var i:word;
 mid_,sigma_:double;
begin
 mid_:=0;
 for i:=low (arr) to low (arr)+qelm-1 do mid_:=mid_+arr[i];
 mid_:=mid_ / qelm;
 sigma_:=0;
 for i:=low (arr) to low (arr)+qelm-1 do sigma_:=sigma_ + sqr( arr[i] - mid_ );
 sigma_:=sqrt ( sigma_ / ( qelm - 1 ) );
// if sigma_<1E-6 then sigma_:=0;
 mid:=mid_;
 sigma:=sigma_;
end;
{-------------------------------------------------------------}
Procedure GetSigmaD;
 var i:word;
 mid_,sigma_:double;
begin
 mid_:=0;
 for i:=low (arr) to low (arr)+qelm-1 do mid_:=mid_+arr[i];
 mid_:=mid_ / qelm;
 sigma_:=0;
 for i:=low (arr) to low (arr)+qelm-1 do sigma_:=sigma_ + sqr( arr[i] - mid_ );
 sigma_:=sqrt ( sigma_ / ( qelm - 1 ) );
// if sigma_<1E-6 then sigma_:=0;
 mid:=mid_;
 sigma:=sigma_;
end;
{-------------------------------------------------------------}
function GetMiddle (var Arr:array of single ;Qelm:word ):single;
var i:word;
begin
 result:=0;
 for i:=low (arr) to low (arr)+qelm-1 do result:=result+arr[i];
 GetMiddle:=result / qelm;
end;
{-------------------------------------------------------------}
Procedure NormArr ;
 var i:word;
 var sigma,mid:single;
begin
 GetSigma ( Arr , qelm, mid  , sigma );
 for i:=low (arr) to low (arr)+qelm-1 do
 if Abs(sigma) > 1E-7 then
 arr[i]:= ( Arr[i] -mid ) / sigma
               else arr[i]:=0;
end;
{-------------------------------------------------------------}
 Function GetRank  ( var Arr:array of single ;Qelm:word; Cur:word):single;
var
 qequal:word;
 Qm:word;
 i:word;
begin
 qequal:=0;
 qm:=0;
 for i:=low (arr) to low (arr)+qelm-1 do
 begin
  if arr[low (arr)+Cur-1]=arr[i] then inc (qEqual);
  if arr[low (arr)+Cur-1]> arr[i] then inc (qm);
{  if arr[low (arr)+Cur-1]-arr[i]<=1E-6 then inc (qEqual);
  if arr[low (arr)+Cur-1]-arr[i]>1E-6 then inc (qm);}
 end;
 GetRank:= GetSum ( qm+1 , qm+Qequal )/qequal;
end;
{-------------------------------------------------------------}
{Procedure GetRanksArr(var Arr,RanksArr:array of single);
var
 NewIds:TIntArr;
 Values:TDoubleArr;
 i:integer;
begin
 for i:=1 to Length(Arr) do Values[i-1]:=Arr[i-1];
 RangeByValues(Values, NewIds);
 for i:=1 to
end;}
{-------------------------------------------------------------}

{Function CoreRankRankFromNotRankArr ( var A1,A2:array of single;Qelm:word;ct:TCoefType):single;
 var
  RanksArr1,RanksArr2:array of single;
begin
 GetRanksArr(A1,RanksArr1);
 GetRanksArr(A2,RanksArr2);
 result:=CoreRankRank(A1,A2,QElm,Ct);
end;}
{-------------------------------------------------------------}
Function CoreRankRank ( var A1,A2:array of single;Qelm:word;ct:TCoefType):single;
var i,j : word;
    Ro:double;
    n,U,T:double;
begin
 CoreRankRank:=0;
 GetUT (A1,qelm,ct,U);
 GetUT (A2,qelm,ct,T);
 Ro := 0;
 case ct of
 spirman:
 begin
    for i:=low (A1) to low (A1)+qelm-1 do
      Ro := Ro + Sqr ( A1[i] -  A2[i] ) ;
    n:=(qElm*qElm*qElm - qElm )/6;
    if (n-2*T=0) or (n-2*U=0) then begin CoreRankRank:=0; exit end;
    Ro:=(n-T-U-Ro)/sqrt (n-2*T)/sqrt (n-2*U);
    CoreRankRank:=Ro;
 end;
 kendal:
 begin
    for i:=low (A1) to low (A1)+qelm-2 do
    for j:=i to low (A1)+qelm-1 do
      Ro := Ro + ( Sign ( A1[i] -  A1[j] ) )*( Sign ( A2[i] -  A2[j] ) );
    n:=( qElm*( qElm -1 ) ) /2;
    if (n-t=0) or (n-u=0) then begin CoreRankRank:=0; exit end;
    Ro :=Ro/sqrt(n-t)/sqrt(n-u);
    CoreRankRank:=Ro;
 end;
 end;
 if result>1 then result:=1;//эр ёыєўрщ эръюяыхэш  ю°шсъш 
end;
{-------------------------------------------------------------}
procedure GetUT (var A:array of single;Qelm:word;ct:TCoefType;Var QSv:double);
type
 BoolArr=array of boolean;
var
 state:BoolArr;
 i,j:word;
 S:word;
begin
 SetLength(state,QElm);
 QSv:=0;
 for i:=low (A) to low (A)+qelm-2 do if not State[i] then
 begin
     s:=0;
     for j:=i to low (A)+qelm-1 do if not State[j]  then
      begin
       if a[i]=A[j] then begin inc(s) ; state[j]:=true; end;
      end;
     case ct of
      kendal: QSv:=QSv +  s * (S-1);
      spirman:QSv:=QSv +  s * s * s - s;
     end;
 end;
 case ct of
  kendal: QSv:=QSv /2;
  spirman:QSv:=QSv /12;
 end;
end;
{-------------------------------------------------------}
   {--- мод. оценка сp.кв. отклонения ----}
function AbsEstimMedSqDer( var Ap:array of single;Qelm:word) :single;
var
 i:word;
 mid:single;
begin
 result:=0;
 for i:=low (Ap) to low (Ap)+qelm-1 do
 result:=result+Ap[i];
 mid:=result/qElm;
 result:=0;
 for i:=low (Ap) to low (Ap)+qelm-1 do
 result:=result+Abs(Ap[i]-mid);
 result:=result/qElm;
 AbsEstimMedSqDer:=result;
end;
{-------------------полузнаковой------------------------------------}
 Function CoreHalfSign ( var As_,Ap:array of single;Qelm:word):single;
 var
   i:word;
   sigma:single;
   midAs:single;
   midAp:single;
 begin
  sigma:= AbsEstimMedSqDer( Ap , qElm );
  midAs:=GetMiddle (As_ , qElm );
  midAp:=GetMiddle (Ap , qElm );
  result:=0;
 for i:=low ( Ap ) to low ( Ap )+qelm-1 do
 result:= result + (Ap[i]-midAp)*sign(As_[i]-midAs);
 if result=0 then begin CoreHalfSign:=0; exit; end;
 result:= result/qElm/sigma;
 CoreHalfSign:=result;
 end;
{------------------знаковый коэф.ассоциации-------------------------------------------}
 Function CoreSign ( var A1,A2:array of single;Qelm:word):single;
 var
   i:word;
   n11,n22,n12,n21:single;
   s1,s2:shortint;
 begin
   n11:=0;
   n22:=0;
   n12:=0;
   n21:=0;
   for i:=low ( A1 ) to low ( A1 )+qelm-1 do
   begin
      if IsNAN (A1[i]) or IsNAN (A2[i]) then continue;
      s1:=binarysign( a1[i] );
      s2:=binarysign( a2[i] );
      if ( s1=s2 ) and (s1>0) then n11:=n11+1;
      if ( s1=s2 ) and (s1<0) then n22:=n22+1;
      if ( s1>0 ) and (s2<0) then n12:=n12+1;
      if ( s1<0 ) and (s2>0) then n21:=n21+1;
   end;
   result:=n11*n22-n12*n21;
   if result=0 then begin CoreSign:=0; exit; end;
   result:=result/sqrt( (n11+n12)*(n21+n22)*(n11+n21)*(n12+n22)  );
   CoreSign:=result;
 end;
{-------------------------------------------------------------}
{ полуранговая }
function CoreHalfRank  ( var Ar{ранг},Av{число}:array of single;Qelm:word):single;
var
 sigma,middle:single;
 i:word;
 S:single;
begin
 GetSigma (Av,QElm,middle,sigma);
 S:=0;
   for i:=low ( Ar ) to low ( Ar )+qelm-1 do
   begin
    S:=S+Ar[i]*(Av[i]-middle);
   end;
 if sigma>1E-4 then  CoreHalfRank:=S/Sigma/QElm/sqrt (1/12*(QElm*QElm-1))
             else CoreHalfRank:=0;
end;
Function CalcQ2 ( var X,Y:TDoubleArr;Qelm:integer):Double;
Var
 Press,SS:double;
begin
 if SS=0 then result:=0 else result:=1-Press/SS;
end;

Function CoreLinearDouble ( var X,Y:TDoubleArr;Qelm:integer):double;
var
 i:word;
 Sx,Sy,Sxy,Sx2,Sy2:double;
 Sqrt1,Sqrt2:double;
 qNAN:integer;
begin
  Sx:=0;
  Sy:=0;
  Sxy:=0;
  Sx2:=0;
  Sy2:=0;
  qNAN:=0;
  for i:=low ( X ) to low ( X )+qelm-1 do
   begin
    if IsNAN (X[i]) or IsNAN (Y[i]) then begin inc(qNAN); continue; end;
    Sx:=Sx+X[i];
    Sy:=Sy+Y[i];
    Sxy:=Sxy+X[i]*Y[i];
    Sx2:=Sx2+sqr(X[i]);
    Sy2:=Sy2+sqr(Y[i]);
   end;
 Dec(qElm,qNAN);
 if  ( Sx2<>0 ) and ( Sy2<>0 ) then
  begin
   if (QElm*Sy2 -sqr (Sy)>0 ) and (QElm*Sx2 -sqr (Sx)>0) then
   begin
    sqrt1:=sqrt(QElm*Sx2 -sqr (Sx));
    sqrt2:=sqrt(QElm*Sy2 -sqr (Sy));
   end
   else
   begin
    result:=0;
    exit;
   end;
   Result:= (QElm*Sxy -Sx*Sy)/sqrt1  /sqrt2 ;
  end
                               else
 Result:=0;
end;
{-------------------------------------------------------------}
Function CoreLinear ( var X,Y:array of single;Qelm:word):single;
var
 i:word;
 Sx,Sy,Sxy,Sx2,Sy2:double;
 Sqrt1,Sqrt2:double;
 qNAN:integer;
begin
  Sx:=0;
  Sy:=0;
  Sxy:=0;
  Sx2:=0;
  Sy2:=0;
  qNAN:=0;
  for i:=low ( X ) to low ( X )+qelm-1 do
   begin
    if IsNAN (X[i]) or IsNAN (Y[i]) then begin inc(qNAN); continue; end;
    Sx:=Sx+X[i];
    Sy:=Sy+Y[i];
    Sxy:=Sxy+X[i]*Y[i];
    Sx2:=Sx2+sqr(X[i]);
    Sy2:=Sy2+sqr(Y[i]);
   end;
 Dec(qElm,qNAN);
 if  ( Sx2<>0 ) and ( Sy2<>0 ) then
  begin
   if (QElm*Sy2 -sqr (Sy)>0 ) and (QElm*Sx2 -sqr (Sx)>0) then
   begin
    sqrt1:=sqrt(QElm*Sx2 -sqr (Sx));
    sqrt2:=sqrt(QElm*Sy2 -sqr (Sy));
   end
   else
   begin
    CoreLinear:=0;
    exit;
   end;
   CoreLinear:= (QElm*Sxy -Sx*Sy)/sqrt1  /sqrt2 ;
  end
                               else
 CoreLinear:=0;
end;
{-------------------------------------------------------------}
 function GetMedium ( var Arr:array of single ;Qelm:word ):single;
 var i:word;
 mid:single;
begin
 mid:=0;
 for i:=low (arr) to low (arr)+qelm-1 do mid:=mid+arr[i];
 mid:=mid / qelm;
 GetMedium:=mid;
end;
{-------------------------------------------------------------}
function GetStudentDistrPoint(ASignLevel:single; NumFreedomDeg:byte):single;
begin
  result:=0;
  if abs(ASignLevel-0.95)<0.01 then
  case NumFreedomDeg of
  1:result:=12.71;
  2:result:=4.30;
  3:result:=3.18;
  4:result:=2.78;
  5:result:=2.57;
  6:result:=2.45;
  7:result:=2.36;
  8:result:=2.31;
  9:result:=2.26;
 10:result:=2.23;
 11:result:=2.20;
 12:result:=2.18;
 13:result:=2.16;
 14:result:=2.14;
 15:result:=2.13;
 16:result:=2.12;
 17:result:=2.11;
 18:result:=2.10;
 19..20:result:=2.09;
 21:result:=2.08;
 22..23:result:=2.07;
 24..26:result:=2.06;
 27..29:result:=2.05;
 30:result:=2.04;
 31..40:result:=2.02;
 41..60:result:=2.00;
 61..120:result:=1.98
  else if  NumFreedomDeg>120 then result:=1.96;
 end;
  if abs(ASignLevel-0.99)<0.01 then
  case NumFreedomDeg of
  1:result:=63.70;
  2:result:=9.92;
  3:result:=5.84;
  4:result:=4.60;
  5:result:=4.03;
  6:result:=3.71;
  7:result:=3.50;
  8:result:=3.36;
  9:result:=3.25;
 10:result:=3.17;
 11:result:=3.11;
 12:result:=3.05;
 13:result:=3.01;
 14:result:=2.98;
 15:result:=2.95;
 16:result:=2.92;
 17:result:=2.90;
 18:result:=2.88;
 19:result:=2.86;
 20:result:=2.85;
 21:result:=2.83;
 22:result:=2.82;
 23:result:=2.81;
 24:result:=2.80;
 25:result:=2.79;
 26:result:=2.78;
 27:result:=2.77;
 28..29:result:=2.76;
 30:result:=2.75;
 31..40:result:=2.70;
 41..60:result:=2.66;
 61..120:result:=2.62
  else if  NumFreedomDeg>120 then result:=2.58;
 end;
end;
function GetTStudent(ASignLevel:single; AQ:byte):single;
begin
  GetTStudent:=0;
  if abs(ASignLevel-0.95)<0.01 then
  case AQ of
  10:GetTStudent:=1.8125;
  20:GetTStudent:=1.7247;
  30:GetTStudent:=1.6973;
 end;
  if abs(ASignLevel-0.99)<0.01 then
  case AQ   of
  10:GetTStudent:=2.7638;
  20:GetTStudent:=2.5280;
  30:GetTStudent:=2.4573;
 end;
end;
{-------------------------------------------------------------}
procedure MinMaxNorm(var Arr:array of single ;Qelm:word);
var
 i:word;
 min,Max:single;
begin
 Min:=arr[low (arr)];
 Max:=arr[low (arr)];
 for i:=low (arr) to low (arr)+qelm-1 do
  begin
   if Arr[i]<Min then Min:=Arr[i];
   if Arr[i]>Max then Max:=Arr[i];
  end;
 if Min=Max then
  begin
   for i:=low (arr) to low (arr)+qelm-1 do Arr[i]:=0;
   exit;
 end;
 for i:=low (arr) to low (arr)+qelm-1 do
 begin
  Arr[i]:=(Arr[i]-min)/(Max-Min);
 end;
end;
procedure SumNorm2(var Arr:TDoubleArr;Qelm:integer);
var
 i:integer;
 Sum:single;
begin
 Sum:=0;
 for i:=low (arr) to low (arr)+qelm-1 do
 sum:=Sum+Abs(Arr[i]);
 if sum=0 then exit;
 for i:=low (arr) to low (arr)+qelm-1 do
 begin
  Arr[i]:=Arr[i]*QElm/Sum;
 end;
end;
{-----------------------------------------------------}
function CamberrDist( var X,Y:array of single;Qelm:word):single;
var
 i:integer;
 Abs1,Abs2:single;
begin
 result:=0;
 for i:=low (x) to low (x)+qelm-1 do
 begin
  Abs1:=Abs(X[i]-Y[i]);
  Abs2:=Abs(X[i])+Abs(Y[i]);
  if Abs2=0 then continue;
  result:=result+Abs1/Abs2;
 end;
end;
{-----------------------------------------------------}
 function GetFDistrPoint(f1,f2:integer;SignLevel:single):single;
begin
result:=0;
end;
{-----------------------------------------------------}
function GetNormDistrPoint(SignLevel:single):single;
begin
 if abs(SignLevel-0.95)<0.01 then result:=1.96;
 if abs(SignLevel-0.99)<0.01 then result:=2.60;
end;

end.


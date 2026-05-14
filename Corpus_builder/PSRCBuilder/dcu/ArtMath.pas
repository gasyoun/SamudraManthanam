unit ArtMath;

interface
 uses uTypes;
type TRankCoefType=( kendal,spirman);
 function DIV_UP( d,q:integer):integer;
 function GetStudentDistrPoint(ASignLevel:double; NumFreedomDeg:byte):double;
 function CoreLinear ( var X,Y:TDoubleArr;Qelm:word):double;
 function GetNormDistrPoint(SignLevel:single):double;
 Function GetTrValue (var Arr,Act:TDoubleArr;Qelm:integer):double;
 Function GetRank  ( var Arr:TDoubleArr;Qelm,Cur:integer):double;
 Function SumIntegersFromA1ToA2( a1,a2 : integer):double;
 Function CoreRankRank ( var A1,A2:TDoubleArr;Qelm:integer;ct:TRankCoefType):double;
 procedure MakeRankArr( var ArrSource,ArrDest:TDoubleArr;QElm:integer);
 procedure CopyDoubleArr( var ArrSource,ArrDest:TDoubleArr;QElm:integer);
 procedure CopyIntArr( var ArrSource,ArrDest:TIntArr;QElm:integer);
 function GetTStudent(ASignLevel:single; AQ:byte):single;
 procedure MixDoubleArr(const ArrSource:TDoubleArr; var ArrDest:TDoubleArr);
 procedure MixIntArr(const ArrSource:TIntArr; var ArrDest:TIntArr);
 function GetNumValueInArr(Value:integer;var Arr:TIntArr):integer;
 function CoreHalfRank  ( var Ar{ранг},Av{число}:TDoubleArr;Qelm:word):double;
 function CoreHalfSign ( var As_,Ap:TDoubleArr;Qelm:integer):double;
 procedure AutoScaleArr (var Arr:TDoubleArr);
 procedure ScaleArrToNormOne (var Arr:TDoubleArr);
 function CalcCountInArr(const Arr:TDoubleArr;ALength:integer;Number:double):integer;
 function CoreSign ( var A1,A2:TDoubleArr;Qelm:Integer):double;
 procedure MinVertDist(var c:T2DIntArr);
 function ArrMin(const Arr:TDoubleArr):double;
 function ArrMax(const Arr:TDoubleArr):double;
 procedure CreateRandomIntArr(Var arr:TIntArr;Min,Max,ALength,ExcludedValue:integer);
const
 MaxVertDistValue=High(integer);

type
 TSortClass=class
   UseAbs:boolean;
   function GetValue(I: integer): double;virtual;abstract;
   procedure QuickSort(iLo, iHi: Integer);
   procedure SlowlySort(iLo, iHi: Integer);
   procedure RunSort;virtual;abstract;
   property Value[I:Integer]:double read GetValue ;//write SetValue;
   procedure ExchangeValues(Item1,Item2:integer);virtual;abstract;
 end;

implementation
 uses Math;

// создает массив случайных чисел от мин до мах, причем в массив не входит число ExcludedValue
procedure CreateRandomIntArr(Var arr:TIntArr;Min,Max,ALength,ExcludedValue:integer);
var
 i,j:integer;
 Value:integer;
 MaxLength:integer;
 ArrDest:TIntArr;
begin
 MaxLength:=Max-Min+1;
 SetLength(Arr,MaxLength);
 SetLength(ArrDest,MaxLength);
 for i:=1 to MaxLength do Arr[i-1]:=Min+i-1;
 MixIntArr(Arr,ArrDest);
 j:=0;
 for i:=1 to ALength+1 do if ArrDest[i-1]<>ExcludedValue then
 begin
  inc(j);
  Arr[j-1]:=ArrDest[i-1];
 end;
 SetLength(Arr,ALength);
end;
function ArrMin(const Arr:TDoubleArr):double;
var
  i:integer;
begin
 result:=MaxDouble;
 for i:=1 to Length(Arr) do
  if arr[i-1]<result then result:=arr[i-1];
end;
function ArrMax(const Arr:TDoubleArr):double;
var
  i:integer;
begin
 result:=-MaxDouble;
 for i:=1 to Length(Arr) do
  if arr[i-1]>result then result:=arr[i-1];
end;

function DIV_UP( d,q:integer):integer;
begin
 result:=((d+q-1)div q);
end;
function binarysign (R:double):shortint;
begin
 Result:=0;
 if r<=0 then Result:=-1;
 if r>0 then Result:=+1;
end;

Function CoreSign ( var A1,A2:TDoubleArr;Qelm:Integer):double;
var
 i:integer;
 n11,n22,n12,n21:double;
 s1,s2:shortint;
begin
 n11:=0;
 n22:=0;
 n12:=0;
 n21:=0;
 for i:=low ( A1 ) to low ( A1 )+qelm-1 do
 begin
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

 function CalcCountInArr(const Arr:TDoubleArr;ALength:integer;Number:double):integer;
var
 i:integer;
begin
 result:=0;
 for i:=0 to ALength-1 do
  if Arr[i]=Number then inc(result);
end;

procedure ScaleArrToNormOne (var Arr:TDoubleArr);
var
 i:integer;
 Norm_:extended;
begin
 Norm_:=Norm(arr);  if Norm_=0 then exit;
 for i:=Low(Arr) to High(Arr) do
  Arr[i]:=(Arr[i])/Norm_;
end;
procedure AutoScaleArr (var Arr:TDoubleArr);
var
 i:integer;
 Mean,StdDev:extended;
begin
 MeanAndStdDev(arr,Mean,StdDev);
 for i:=Low(Arr) to High(Arr) do
  Arr[i]:=(Arr[i]-Mean)/StdDev;
end;
function GetMean (var Arr:TDoubleArr;Qelm:Integer):double;
var
 i:integer;
begin
 result:=0;
 for i:=low (arr) to low (arr)+qelm-1 do result:=result+arr[i];
 Result:=result / qelm;
end;


function AbsMeanDev( var Ap:TDoubleArr;Qelm:integer) :double;
var
 i:integer;
 mid:double;
begin
 result:=0;
 for i:=low (Ap) to low (Ap)+qelm-1 do
 result:=result+Ap[i];
 mid:=result/qElm;
 result:=0;
 for i:=low (Ap) to low (Ap)+qelm-1 do
 result:=result+Abs(Ap[i]-mid);
 result:=result/qElm;
end;
{-------------------полузнаковой------------------------------------}
function Sign (Value:double):shortint;
begin
 if Value<0 then result:=-1 else
 if Value>0 then result:=1 else
 result:=0;
end;

Function CoreHalfSign ( var As_,Ap:TDoubleArr;Qelm:integer):double;
var
 i:integer;
 sigma:double;
 midAs:double;
 midAp:double;
 begin
  sigma:= AbsMeanDev( Ap , qElm );
  midAs:=GetMean (As_ , qElm );
  midAp:=GetMean (Ap , qElm );
  result:=0;
 for i:=low ( Ap ) to low ( Ap )+qelm-1 do
 result:= result + (Ap[i]-midAp)*sign(As_[i]-midAs);
 if result=0 then begin CoreHalfSign:=0; exit; end;
 result:= result/qElm/sigma;
 CoreHalfSign:=result;
 end;
function CoreHalfRank  ( var Ar{ранг},Av{число}:TDoubleArr;Qelm:word):double;
var
 sigma,middle:extended;
 i:integer;
 S:double;
begin
 MeanAndStdDev(Av,middle,sigma);
 S:=0;
   for i:=low ( Ar ) to low ( Ar )+qelm-1 do
   begin
    S:=S+Ar[i]*(Av[i]-middle);
   end;
 if sigma>1E-6 then  CoreHalfRank:=S/Sigma/QElm/sqrt (1/12*(QElm*QElm-1))
             else CoreHalfRank:=0;
end;

function GetNumValueInArr(Value:integer;var Arr:TIntArr):integer;
var
 i:integer;
begin
 result:=0;
 for i:=1 to Length(Arr) do
  if Arr[i-1]=Value then
  begin
   result:=i;
   exit;
  end;
end;
{Procedure GetSigma;
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
end;}
procedure MixDoubleArr(const ArrSource:TDoubleArr; var ArrDest:TDoubleArr);
var
 i:integer;
 ArrInt:TIntArr;
 RandomInt,ArrLenght:integer;
 bPosArr:array of boolean;
begin
 Randomize;
 ArrLenght:=Length(ArrSource);
 SetLength(ArrInt,ArrLenght);
 SetLength(bPosArr,ArrLenght);
 for i:=1 to ArrLenght do
 begin
  repeat
   RandomInt:=Random(ArrLenght);
   if bPosArr[RandomInt]=false then
   begin
    bPosArr[RandomInt]:=True;
    ArrInt[i-1]:=RandomInt;
    break;
   end;
  until False;
 end;
 for i:=1 to ArrLenght do
 ArrDest[i-1]:=ArrSource[ArrInt[i-1]];
end;

procedure MixIntArr(const ArrSource:TIntArr; var ArrDest:TIntArr);
var
 i:integer;
 ArrInt:TIntArr;
 RandomInt,ArrLenght:integer;
 bPosArr:array of boolean;
begin
 ArrLenght:=Length(ArrSource);
 SetLength(ArrInt,ArrLenght);
 SetLength(bPosArr,ArrLenght);
 for i:=1 to ArrLenght do
 begin
  repeat
   RandomInt:=Random(ArrLenght);
   if bPosArr[RandomInt]=false then
   begin
    bPosArr[RandomInt]:=True;
    ArrInt[i-1]:=RandomInt;
    break;
   end;
  until False;
 end;
 for i:=1 to ArrLenght do
 ArrDest[i-1]:=ArrSource[ArrInt[i-1]];
end;

function GetTStudent(ASignLevel:single; AQ:byte):single;
begin
  GetTStudent:=0;
  if abs(ASignLevel-0.95)<0.01 then
  case AQ of
    1	:GetTStudent:=	6.3138	;
    2	:GetTStudent:=	2.92	;
    3	:GetTStudent:=	2.3534	;
    4	:GetTStudent:=	2.1318	;
    5	:GetTStudent:=	2.015	;
    6	:GetTStudent:=	1.9432	;
    7	:GetTStudent:=	1.8946	;
    8	:GetTStudent:=	1.8595	;
    9	:GetTStudent:=	1.8331	;
    10	:GetTStudent:=	1.8125	;
    11	:GetTStudent:=	1.7959	;
    12	:GetTStudent:=	1.7823	;
    13	:GetTStudent:=	1.7709	;
    14	:GetTStudent:=	1.7613	;
    15	:GetTStudent:=	1.7531	;
    16	:GetTStudent:=	1.7459	;
    17	:GetTStudent:=	1.7396	;
    18	:GetTStudent:=	1.7341	;
    19	:GetTStudent:=	1.7291	;
    20	:GetTStudent:=	1.7247	;
    21	:GetTStudent:=	1.7207	;
    22	:GetTStudent:=	1.7171	;
    23	:GetTStudent:=	1.7139	;
    24	:GetTStudent:=	1.7109	;
    25	:GetTStudent:=	1.7081	;
    26	:GetTStudent:=	1.7056	;
    27	:GetTStudent:=	1.7033	;
    28	:GetTStudent:=	1.7011	;
    29	:GetTStudent:=	1.6991	;
    30	:GetTStudent:=	1.6973	;
    31..32	:GetTStudent:=	1.6939	;
    33..34	:GetTStudent:=	1.6909	;
    35..36	:GetTStudent:=	1.6883	;
    37..38	:GetTStudent:=	1.686	;
    39..40	:GetTStudent:=	1.6839	;
    41..42	:GetTStudent:=	1.682	;
    43..44	:GetTStudent:=	1.6802	;
    45..46	:GetTStudent:=	1.6787	;
    47..48	:GetTStudent:=	1.6772	;
    49..50	:GetTStudent:=	1.6759	;
    51..55	:GetTStudent:=	1.673	;
    56..60	:GetTStudent:=	1.6706	;
    61..70	:GetTStudent:=	1.6669	;
    71..80	:GetTStudent:=	1.6641	;
    81..100	:GetTStudent:=	1.6602	;
     else GetTStudent:=	1.6449	;

 end;
  if abs(ASignLevel-0.99)<0.01 then
  case AQ   of
    1	:GetTStudent:=	31.821	;
    2	:GetTStudent:=	6.9646	;
    3	:GetTStudent:=	4.5407	;
    4	:GetTStudent:=	3.7469	;
    5	:GetTStudent:=	3.3649	;
    6	:GetTStudent:=	3.1427	;
    7	:GetTStudent:=	2.998	;
    8	:GetTStudent:=	2.8965	;
    9	:GetTStudent:=	2.8214	;
    10	:GetTStudent:=	2.7638	;
    11	:GetTStudent:=	2.7181	;
    12	:GetTStudent:=	2.681	;
    13	:GetTStudent:=	2.6503	;
    14	:GetTStudent:=	2.6245	;
    15	:GetTStudent:=	2.6025	;
    16	:GetTStudent:=	2.5835	;
    17	:GetTStudent:=	2.5669	;
    18	:GetTStudent:=	2.5524	;
    19	:GetTStudent:=	2.5395	;
    20	:GetTStudent:=	2.528	;
    21	:GetTStudent:=	2.5176	;
    22	:GetTStudent:=	2.5083	;
    23	:GetTStudent:=	2.4999	;
    24	:GetTStudent:=	2.4922	;
    25	:GetTStudent:=	2.4851	;
    26	:GetTStudent:=	2.4786	;
    27	:GetTStudent:=	2.4727	;
    28	:GetTStudent:=	2.4671	;
    29	:GetTStudent:=	2.462	;
    30	:GetTStudent:=	2.4573	;
    31..32	:GetTStudent:=	2.4487	;
    33..34	:GetTStudent:=	2.4411	;
    35..36	:GetTStudent:=	2.4345	;
    37..38	:GetTStudent:=	2.4286	;
    39..40	:GetTStudent:=	2.4233	;
    41..42	:GetTStudent:=	2.4185	;
    43..44	:GetTStudent:=	2.4141	;
    45..46	:GetTStudent:=	2.4102	;
    47..48	:GetTStudent:=	2.4066	;
    49..50	:GetTStudent:=	2.4033	;
    51..55	:GetTStudent:=	2.3961	;
    56..60	:GetTStudent:=	2.3901	;
    61..70	:GetTStudent:=	2.3808	;
    71..80	:GetTStudent:=	2.3739	;
    81..100	:GetTStudent:=	2.3642	;
     else GetTStudent:=	2.3263	;
 end;
end;
procedure CopyIntArr( var ArrSource,ArrDest:TIntArr;QElm:integer);
begin
 ArrDest:=Copy(ArrSource,Low(ArrSource),QElm);
end;

procedure CopyDoubleArr( var ArrSource,ArrDest:TDoubleArr;QElm:integer);
begin
 ArrDest:=Copy(ArrSource,Low(ArrSource),QElm);
end;

procedure MakeRankArr( var ArrSource,ArrDest:TDoubleArr;QElm:integer);
var
 i:integer;
begin
 for i:=1 to QElm do
  ArrDest[i-1]:=GetRank(ArrSource,QElm,i);
end;

procedure GetUT (var A:TDoubleArr;Qelm:integer;ct:TRankCoefType;Var QSv:double);
var
 state:array of boolean;
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

Function CoreRankRank ( var A1,A2:TDoubleArr;Qelm:integer;ct:TRankCoefType):double;
var i,j : integer;
    Ro:double;
    n,U,T:double;
begin
 result:=0;
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
    result:=Ro;
 end;
 kendal:
 begin
    for i:=low (A1) to low (A1)+qelm-2 do
    for j:=i to low (A1)+qelm-1 do
      Ro := Ro + ( Sign ( A1[i] -  A1[j] ) )*( Sign ( A2[i] -  A2[j] ) );
    n:=( qElm*( qElm -1 ) ) /2;
    if (n-t=0) or (n-u=0) then begin CoreRankRank:=0; exit end;
    Ro :=Ro/sqrt(n-t)/sqrt(n-u);
    result:=Ro;
 end;
 end;
// if result>1 then ;//на случай накопления ошибки
end;

Function SumIntegersFromA1ToA2( a1,a2 : integer):double;
var
 i:integer;
begin
 result:=0;
 for i:=a1 to a2 do result:=result+i;
end;

Function GetRank ( var Arr:TDoubleArr;Qelm,Cur:integer):double;
var
 i:integer;
 qequal,Qm:integer;
begin
 qequal:=0;
 qm:=0;
 for i:=low (arr) to low (arr)+qelm-1 do
 begin
  if arr[low (arr)+Cur-1]=arr[i] then inc (qEqual);
  if arr[low (arr)+Cur-1]> arr[i] then inc (qm);
 end;
 GetRank:= SumIntegersFromA1ToA2 ( qm+1 , qm+Qequal )/qequal;
end;

Function GetTrValue (var Arr,Act:TDoubleArr;Qelm:integer):double;
var
 i:integer;
begin
 result:=0;
  for i:=low (arr) to low (arr)+qelm-1 do
 result:=result+ Arr[i]*Act[i];
 result:=result/qelm;
end;

function GetNormDistrPoint(SignLevel:single):double;
begin
 if abs(SignLevel-0.95)<0.01 then result:=1.96;
 if abs(SignLevel-0.99)<0.01 then result:=2.60;
end;

function CoreLinear ( var X,Y:TDoubleArr;Qelm:word):double;
var
 i:integer;
 Sx,Sy,Sxy,Sx2,Sy2:double;
 Sqrt1,Sqrt2:double;
begin
  Sx:=0;
  Sy:=0;
  Sxy:=0;
  Sx2:=0;
  Sy2:=0;
  for i:=low ( X ) to low ( X )+qelm-1 do
   begin
    Sx:=Sx+X[i];
    Sy:=Sy+Y[i];
    Sxy:=Sxy+X[i]*Y[i];
    Sx2:=Sx2+sqr(X[i]);
    Sy2:=Sy2+sqr(Y[i]);
   end;
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

function GetStudentDistrPoint(ASignLevel:double; NumFreedomDeg:byte):double;
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

procedure MinVertDist(var c:T2DIntArr);
var
 k,i,j,n:integer;
 c1,c2,c3:integer;
begin
 k:=0;
 n:=Length(c);
 while k<n do // было k<n+1, но работало с ошибкой 
 begin
  inc(k);
  for i:=1 to n do if c[i-1,k-1]<MaxVertDistValue then
  for j:=1 to n do if c[j-1,k-1]<MaxVertDistValue then
  if i<>j then
   begin
    c1:=c[i-1,j-1];
    c2:=c[i-1,k-1];
    c3:=c[j-1,k-1];
    c[i-1,j-1]:=min(c[i-1,j-1],c[i-1,k-1]+c[j-1,k-1]);
    if c[i-1,j-1]<0 then
       c[i-1,j-1]:=0;
   end;
 end;
end;

{ TSortClass }

procedure TSortClass.QuickSort(iLo, iHi: Integer);
  var
    Lo, Hi: Integer;
    Mid:double;
  begin
    Lo := iLo;
    Hi := iHi;
    Mid := Value[(Lo + Hi) div 2];
    repeat
      while Value[Lo] > Mid do Inc(Lo);
      while Value[Hi] < Mid do Dec(Hi);
      if Lo <= Hi then
      begin
        ExchangeValues(Hi,Lo);
        Inc(Lo);
        Dec(Hi);
      end;
    until Lo > Hi;
    if Hi > iLo then QuickSort( iLo, Hi);
    if Lo < iHi then QuickSort( Lo, iHi);
  end;

procedure TSortClass.SlowlySort(iLo, iHi: Integer);
var
 i,j:integer;
begin
 for i:=iLo to iHi-1 do
  for j:=i+1 to iHi do
   if Value[i]<=Value[j] then ExchangeValues(i,j);
end;

end.

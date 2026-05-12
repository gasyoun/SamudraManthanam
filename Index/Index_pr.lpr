program Index_pr;

{$MODE Delphi}

uses
  Forms, Interfaces,
  u_Index in 'u_Index.pas' {MainForm},
  fSources in 'fSources.pas' {SourcesForm};

{$R *.res}

begin
  Application.Initialize;
  Application.CreateForm(TMainForm, MainForm);
  Application.Run;
end.

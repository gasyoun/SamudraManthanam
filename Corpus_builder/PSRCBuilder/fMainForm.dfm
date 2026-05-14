object Form1: TForm1
  Left = 229
  Top = 161
  Width = 559
  Height = 381
  Caption = #1050#1086#1084#1087#1086#1085#1086#1074#1097#1080#1082' '#1087#1072#1088#1072#1083#1083#1077#1083#1100#1085#1086#1075#1086' '#1089#1072#1085#1089#1082#1088#1080#1090#1089#1082#1086'-'#1088#1091#1089#1089#1082#1086#1075#1086' '#1082#1086#1088#1087#1091#1089#1072
  Color = clBtnFace
  Font.Charset = DEFAULT_CHARSET
  Font.Color = clWindowText
  Font.Height = -11
  Font.Name = 'MS Sans Serif'
  Font.Style = []
  Menu = MainMenu1
  OldCreateOrder = False
  OnCreate = FormCreate
  PixelsPerInch = 96
  TextHeight = 13
  object Label1: TLabel
    Left = 0
    Top = 1
    Width = 543
    Height = 13
    Align = alBottom
    Caption = 'Memo2'
    Visible = False
  end
  object Label2: TLabel
    Left = 0
    Top = 0
    Width = 543
    Height = 13
    Align = alTop
    Caption = 'Memo1'
    Visible = False
  end
  object StatusBar1: TStatusBar
    Left = 0
    Top = 303
    Width = 543
    Height = 19
    Panels = <
      item
        Width = 200
      end
      item
        Width = 50
      end>
  end
  object Memo2: TMemo
    Left = 0
    Top = 14
    Width = 543
    Height = 289
    Align = alBottom
    ScrollBars = ssBoth
    TabOrder = 1
    Visible = False
    WordWrap = False
  end
  object Memo1: TMemo
    Left = 0
    Top = 13
    Width = 543
    Height = 289
    Align = alClient
    TabOrder = 2
    WordWrap = False
  end
  object MainMenu1: TMainMenu
    Left = 360
    Top = 96
    object N19: TMenuItem
      Caption = #1057#1086#1073#1088#1072#1090#1100' '#1076#1086#1082#1091#1084#1077#1085#1090' '#1082#1086#1088#1087#1091#1089#1072
      object HTML1: TMenuItem
        Caption = #1057#1086#1073#1088#1072#1090#1100' '#1086#1076#1085#1086#1082#1085#1080#1078#1085#1099#1081' '#1076#1086#1082#1091#1084#1077#1085#1090
        OnClick = HTML1Click
      end
      object CorpushtmlbuildManyBooks1: TMenuItem
        Caption = #1057#1086#1073#1088#1072#1090#1100' '#1084#1085#1086#1075#1086#1082#1085#1080#1078#1085#1099#1081' '#1076#1086#1082#1091#1084#1077#1085#1090
        OnClick = CorpushtmlbuildManyBooks1Click
      end
      object CorpushtmlbuildManyBooks2: TMenuItem
        Caption = #1057#1086#1073#1088#1072#1090#1100' '#1084#1085#1086#1075#1086#1082#1085#1080#1078#1085#1099#1081' '#1076#1086#1082#1091#1084#1077#1085#1090' '#1074' '#1086#1076#1085#1086#1084' '#1092#1072#1081#1083#1077' (Ex. ChUp)'
        ShortCut = 16504
        OnClick = CorpushtmlbuildManyBooks2Click
      end
      object N2: TMenuItem
        Caption = #1055#1088#1086#1074#1077#1088#1082#1072'_'#1055#1077#1088#1077#1074#1086#1076#1072
        OnClick = N2Click
      end
      object IAST3: TMenuItem
        Caption = #1057#1075#1077#1085#1077#1088#1080#1088#1086#1074#1072#1090#1100' '#1087#1091#1089#1090#1091#1102' '#1082#1085#1080#1075#1091' '#1085#1072' '#1086#1089#1085#1086#1074#1077' IAST'
        OnClick = IAST3Click
      end
    end
  end
  object OpenDialog1: TOpenDialog
    Filter = 'Text files|*.txt|HTML|*.htm*'
    Left = 152
    Top = 8
  end
  object SaveDialog1: TSaveDialog
    DefaultExt = 'txt'
    Filter = 'Text Files|*.txt'
    Left = 208
    Top = 8
  end
end

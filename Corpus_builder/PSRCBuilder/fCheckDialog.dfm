object OKBottomDlg: TOKBottomDlg
  Left = 245
  Top = 108
  BorderStyle = bsDialog
  Caption = 'Dialog'
  ClientHeight = 268
  ClientWidth = 313
  Color = clBtnFace
  ParentFont = True
  OldCreateOrder = True
  Position = poScreenCenter
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  PixelsPerInch = 96
  TextHeight = 13
  object Label1: TLabel
    Left = 16
    Top = 16
    Width = 78
    Height = 13
    Caption = #1055#1088#1080#1079#1085#1072#1082' '#1075#1083#1072#1074#1099
  end
  object Label2: TLabel
    Left = 16
    Top = 64
    Width = 120
    Height = 13
    Caption = #1055#1088#1080#1079#1085#1072#1082' '#1085#1086#1084#1077#1088#1072' '#1096#1083#1086#1082#1080
  end
  object Label3: TLabel
    Left = 16
    Top = 112
    Width = 116
    Height = 13
    Caption = #1055#1088#1080#1079#1085#1072#1082' '#1082#1086#1084#1084#1077#1085#1090#1072#1088#1080#1103
  end
  object Label4: TLabel
    Left = 16
    Top = 160
    Width = 137
    Height = 13
    Caption = #1055#1088#1080#1079#1085#1072#1082' '#1085#1086#1084#1077#1088#1072' '#1089#1090#1088#1072#1085#1080#1094#1099
  end
  object Bevel1: TBevel
    Left = 8
    Top = 8
    Width = 297
    Height = 209
    Shape = bsFrame
  end
  object OKBtn: TButton
    Left = 71
    Top = 236
    Width = 75
    Height = 25
    Caption = 'OK'
    Default = True
    ModalResult = 1
    TabOrder = 0
  end
  object CancelBtn: TButton
    Left = 167
    Top = 236
    Width = 75
    Height = 25
    Cancel = True
    Caption = 'Cancel'
    ModalResult = 2
    TabOrder = 1
  end
  object E_Chapter: TEdit
    Left = 32
    Top = 32
    Width = 121
    Height = 21
    TabOrder = 2
    Text = #1043#1083#1072#1074#1072
  end
  object E_Shloka: TEdit
    Left = 32
    Top = 80
    Width = 121
    Height = 21
    TabOrder = 3
    Text = '[1]'
  end
  object E_Comment: TEdit
    Left = 32
    Top = 128
    Width = 121
    Height = 21
    TabOrder = 4
    Text = '(1)'
  end
  object E_Page: TEdit
    Left = 32
    Top = 176
    Width = 121
    Height = 21
    TabOrder = 5
    Text = '-1-'
  end
end

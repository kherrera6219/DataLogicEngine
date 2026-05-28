; NSIS customization hooks for DataLogicEngine installer.
; Keep this file tracked so electron-builder include resolution is stable.

!macro customHeader
  ; Explicit completion copy in wizard mode.
  !define MUI_FINISHPAGE_TITLE "DataLogicEngine Installation Complete"
  !define MUI_FINISHPAGE_TEXT "DataLogicEngine was installed successfully. Click Finish to launch the application."
!macroend

!macro customInstall
  DetailPrint "DataLogicEngine custom install hook"
  DetailPrint "Bundled Java runtime is installed under resources\\backend\\databases\\jre when present"
  WriteRegStr SHELL_CONTEXT "${UNINSTALL_REGISTRY_KEY}" "InstallLocation" "$INSTDIR"
!macroend

!macro customUnInstall
  DetailPrint "DataLogicEngine custom uninstall hook"
!macroend

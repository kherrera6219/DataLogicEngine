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

  ; --- Make the uninstaller easy to find -------------------------------------
  ; electron-builder writes the uninstaller as "Uninstall ${PRODUCT_FILENAME}.exe"
  ; in $INSTDIR. Create user-friendly shortcuts so the user does not have to dig
  ; through Program Files to find it.

  ; Start Menu uninstall shortcut (next to the app shortcut)
  CreateShortCut "$SMPROGRAMS\Uninstall DataLogicEngine.lnk" "$INSTDIR\Uninstall ${PRODUCT_FILENAME}.exe"

  ; Desktop uninstall shortcut
  CreateShortCut "$DESKTOP\Uninstall DataLogicEngine.lnk" "$INSTDIR\Uninstall ${PRODUCT_FILENAME}.exe"
!macroend

!macro customUnInstall
  DetailPrint "DataLogicEngine custom uninstall hook"
  ; Clean up the convenience uninstall shortcuts we created at install time.
  Delete "$SMPROGRAMS\Uninstall DataLogicEngine.lnk"
  Delete "$DESKTOP\Uninstall DataLogicEngine.lnk"
!macroend

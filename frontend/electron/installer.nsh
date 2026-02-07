; Minimal NSIS include hooks for DataLogicEngine installer.
; Keep this file tracked so electron-builder include resolution is stable.

!macro customInstall
  DetailPrint "DataLogicEngine custom install hook: no-op"
!macroend

!macro customUnInstall
  DetailPrint "DataLogicEngine custom uninstall hook: no-op"
!macroend

!macro customInstall
  DetailPrint "Installing Microsoft Visual C++ Runtime for BMO..."
  IfFileExists "$INSTDIR\resources\vc_redist.x64.exe" 0 vc_done
    ExecWait '"$INSTDIR\resources\vc_redist.x64.exe" /install /quiet /norestart'
  vc_done:
!macroend

!macro customUnInstall
  DetailPrint "Removing BMO user data..."
  RMDir /r "$LOCALAPPDATA\BMO"
!macroend

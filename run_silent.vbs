Set WshShell = CreateObject("WScript.Shell")
' Run the batch file in the background (0 hides the window)
WshShell.Run chr(34) & WshShell.CurrentDirectory & "\run_app.bat" & chr(34), 0
Set WshShell = Nothing

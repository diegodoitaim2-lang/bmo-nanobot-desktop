Set shell = CreateObject("WScript.Shell")
project = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = project
shell.Environment("PROCESS")("BMO_ELECTRON_LOAD_DIST") = "1"
shell.Run """" & project & "\node_modules\electron\dist\electron.exe"" .", 1, False

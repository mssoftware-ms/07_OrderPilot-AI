Set objShell = CreateObject("WScript.Shell")
appPath = WScript.ScriptFullName
Set fso = CreateObject("Scripting.FileSystemObject")
projDir = fso.GetParentFolderName(appPath)
cmd = "pythonw """ & projDir & "\main.py"""
objShell.Run cmd, 0, False

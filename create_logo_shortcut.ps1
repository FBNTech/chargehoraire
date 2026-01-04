# Script pour créer un raccourci vers ACHLogo.png

$SourcePath = "d:\chargehoraire\static\images\ACHLogo.png"
$ShortcutPath = "$env:USERPROFILE\Desktop\ACHLogo.lnk"

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $SourcePath
$Shortcut.Description = "Raccourci vers le logo ACH"
$Shortcut.Save()

Write-Host "Raccourci créé sur le Bureau : $ShortcutPath" -ForegroundColor Green

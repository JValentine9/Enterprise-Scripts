$Drives = Get-PSDrive -PSProvider 'FileSystem'
Write-Host ($Drives | Format-Table | Out-String)

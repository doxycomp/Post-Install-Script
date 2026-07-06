$var = "Hallo Welt"
$name = read-host "Wie lautet dein Name?"
$name
$ordnerinhalt = Get-ChildItem 
$ordnerinhalt

Write-Host "Hallo Powershell"
Write-Host "Hallo $name"

Get-Member -InputObject $var

$boolean = $true
[int]$zahl = 5

[int]$input = Read-Host "Gib eine Zahl ein"
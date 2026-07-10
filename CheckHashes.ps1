$Checks = @(
    @{ Path = ".\InstallPythonRunFile.bat"; ExpectedHash = "94E7E308AEB3EA1BBB8AEC6442E023CA5266F92AB2E4D2F6692359079EAF33BB" }
    @{ Path = ".\PostInstall.py"; ExpectedHash = "03205AFFB3F5F89D9A8A2755FD866E9C73EDA3CC9EBD7F9FA7851015F11AB3CE" }
    @{ Path = ".\backend.py"; ExpectedHash = "3927DAD6F1FE72F2859226FE7A9894FF7BADD3BD3C109C19A5E1F8B877C93236" }
    @{ Path = ".\gui.py"; ExpectedHash = "EDC4D1A2527AD8665EBBEC00B4E0FEE1324E7065023A909E9F7B32922A4EF8F9" }
    @{ Path = ".\config.json"; ExpectedHash = "3716B06DF4EA4E33068FDF4488E982CA164E32934ECFEC1FBDC91FD0615F2E58" }
    @{ Path = ".\README.md"; ExpectedHash = "76112C618412C31F64A810FFF0CC6F5360FFC00569980C3AB93AE655CD714CBC" }
)
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "      Starte Datei-Integritätsprüfung     " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
$FailedChecks = 0
foreach ($Check in $Checks) {
    $FilePath = $Check.Path
    $ExpectedHash = $Check.ExpectedHash
    if (-not (Test-Path $FilePath)) {
        Write-Host "[-] Fehler: Die Datei '$FilePath' wurde nicht gefunden!" -ForegroundColor Red
        $FailedChecks++
        continue
    }
    if ($ExpectedHash -eq "HIER_DEN_ERWARTETEN_SHA256_HASH_EINTRAGEN") {
        Write-Host "[-] Kein erwarteter Hash für '$FilePath' gesetzt. Bitte ersetze den Platzhalter." -ForegroundColor Yellow
        $FailedChecks++
        continue
    }
    Write-Host "[i] Berechne SHA-256 Hash für: $FilePath..." -ForegroundColor Yellow
    $ComputedHash = (Get-FileHash -Path $FilePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $ExpectedHashNormalized = $ExpectedHash.ToLowerInvariant()
    Write-Host "[i] Berechneter Hash: $ComputedHash" -ForegroundColor Gray
    Write-Host "[i] Erwarteter Hash:  $ExpectedHashNormalized" -ForegroundColor Gray
    if ($ComputedHash -eq $ExpectedHashNormalized) {
        Write-Host "[+] ERFOLG: Der Hash stimmt überein!" -ForegroundColor Green
    } else {
        Write-Host "[X] WARNUNG: Der Hash stimmt NICHT überein!" -ForegroundColor Red
        Write-Host "    Die Datei wurde möglicherweise manipuliert oder ist beschädigt." -ForegroundColor Red
        $FailedChecks++
    }
    Write-Host ""
}
if ($FailedChecks -eq 0) {
    Write-Host "[+] Alle Hash-Prüfungen waren erfolgreich." -ForegroundColor Green
    Exit 0
} else {
    Write-Host "[-] $FailedChecks Hash-Prüfung(en) fehlgeschlagen." -ForegroundColor Red
    Exit 1
}
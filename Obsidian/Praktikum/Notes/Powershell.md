`$Variable` -> erstellt eine Variable mit dem Namen "Variable". Speichert nur momentaufnahmen von Servicen
`$Variable = "Hallo"` -> weist der Variable "Variable" den String "Hallo" zu
`[int]%Variable = "1234"` -> erzwingt einen bestimmten Variablentyp
`$Boolean = $true` -> weißst der Variablen den Boolean "True" zu
### cmdlets: 
`Read-Host` -> vergleichbar mit python `input()`
`Write-Host` -> vergleichbar mit python `print()`
`Get-Process (-Name)` -> Durchsucht alle aktiven Processe 
`Get-Service (-Name)` -> Durchsucht alle aktiven Service
`Get-Member (-InputObject {Variable})` -> Ruft Objecttypen ab (z.B. Boolean, String, int, oder auch service)
`Get-Childitem` Zeigt alle Unterordner des aktiven Ordners an

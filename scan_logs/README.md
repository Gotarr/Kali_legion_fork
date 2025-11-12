# Scan Logs Directory

Diese Verzeichnis enthält die Event-Logs für alle Scans im **JSONL Format** (JSON Lines).

## Format

Jede Scan-Session wird in einer eigenen Datei gespeichert:
- **Dateiname**: `{scan-uuid}.json`
- **Format**: JSONL (eine JSON-Zeile pro Event)
- **Encoding**: UTF-8

## Events

Jeder Scan durchläuft folgende Events:

1. **queued** - Scan wurde zur Queue hinzugefügt
2. **started** - Scan wurde gestartet (nmap läuft)
3. **finished** - Scan beendet (Status: completed/failed/cancelled)
4. **cancelled** - Scan wurde abgebrochen (optional, falls manuell cancelled)

## JSON Struktur

```json
{
  "id": "1c30a667-4d93-409c-8098-0f68522f610b",
  "target": "127.0.0.1",
  "scan_type": "quick",
  "options": {
    "timing": "4"
  },
  "status": "running",
  "created_at": "2025-11-12T15:05:12.962000",
  "started_at": "2025-11-12T15:05:12.963000",
  "completed_at": null,
  "error": null,
  "hosts_found": 0,
  "ports_found": 0,
  "duration": null,
  "event": "started",
  "timestamp": "2025-11-12T15:05:12.963000"
}
```

## Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | string | UUID des Scan-Jobs |
| `target` | string | Ziel IP/Hostname/CIDR |
| `scan_type` | string | quick, full, stealth, custom, etc. |
| `options` | object | Scan-Optionen (timing, ports, scripts, etc.) |
| `status` | string | queued, running, completed, failed, cancelled |
| `created_at` | string (ISO) | Zeitstempel: Job erstellt |
| `started_at` | string (ISO) | Zeitstempel: Scan gestartet |
| `completed_at` | string (ISO) | Zeitstempel: Scan beendet |
| `error` | string/null | Fehlermeldung (falls failed) |
| `hosts_found` | int | Anzahl gefundener Hosts |
| `ports_found` | int | Anzahl gefundener offener Ports |
| `duration` | float/null | Dauer in Sekunden |
| `event` | string | Event-Typ (queued/started/finished/cancelled) |
| `timestamp` | string (ISO) | Event-Zeitstempel |

## Verwendung

### Log-Datei lesen

```python
import json

scan_id = "1c30a667-4d93-409c-8098-0f68522f610b"
log_file = f"scan_logs/{scan_id}.json"

with open(log_file, 'r', encoding='utf-8') as f:
    events = [json.loads(line) for line in f]

print(f"Scan durchlief {len(events)} Events")
for event in events:
    print(f"{event['timestamp']}: {event['event']} - {event['status']}")
```

### Scan nachvollziehen

Jede Zeile repräsentiert den **Zustand des Jobs zu einem bestimmten Zeitpunkt**.

**Beispiel-Log:**

```jsonl
{"id": "abc123", "target": "192.168.1.1", "status": "queued", "event": "queued", "timestamp": "2025-11-12T10:00:00"}
{"id": "abc123", "target": "192.168.1.1", "status": "running", "event": "started", "timestamp": "2025-11-12T10:00:05"}
{"id": "abc123", "target": "192.168.1.1", "status": "completed", "hosts_found": 1, "ports_found": 4, "duration": 5.2, "event": "finished", "timestamp": "2025-11-12T10:00:10"}
```

## Aufbewahrung

- Logs werden **automatisch** bei jedem Scan erstellt
- Logs werden **nie automatisch gelöscht**
- Manuelle Bereinigung empfohlen (z.B. Logs älter als 30 Tage löschen)

## Troubleshooting

### Scan hat keine Log-Datei?
→ Prüfen ob `scan_logs/` Verzeichnis existiert und beschreibbar ist

### Log-Datei ist leer?
→ Scan wurde möglicherweise vor dem ersten Event abgebrochen

### Mehrere Finish-Events?
→ Sollte nicht passieren - Bug melden!

### Event fehlt?
→ Scan könnte crashed sein - siehe Error-Logs

## Tools

### Alle Scans auflisten

```bash
# PowerShell
Get-ChildItem scan_logs\*.json | ForEach-Object {
    $events = Get-Content $_.FullName | ConvertFrom-Json
    $last = $events[-1]
    Write-Host "$($_.BaseName): $($last.target) - $($last.status)"
}
```

### Fehlgeschlagene Scans finden

```bash
# PowerShell
Get-ChildItem scan_logs\*.json | ForEach-Object {
    $events = Get-Content $_.FullName | ConvertFrom-Json
    $failed = $events | Where-Object { $_.status -eq "failed" }
    if ($failed) {
        Write-Host "$($_.BaseName): $($failed[-1].error)"
    }
}
```

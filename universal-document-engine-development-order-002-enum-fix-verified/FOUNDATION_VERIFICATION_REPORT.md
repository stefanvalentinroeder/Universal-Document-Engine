# Foundation Verification Report

## 1. Berichtskontext

- Projekt: Universal Document Engine
- Entwicklungsauftrag: Development Order 001A – Foundation Closure
- Prüfdatum: 2026-08-05 (Europe/Berlin)
- geprüfter Stand: lokaler Repository-Arbeitsstand nach Umsetzung von 001A
- Development Order 002: nicht begonnen

## 2. Gesamtstatus

**Implementierung abgeschlossen, Live-Infrastruktur-Verifikation offen.**

Alle in dieser Laufzeit ohne Docker ausführbaren Prüfungen waren erfolgreich:

- reproduzierbare JavaScript-Installation aus `pnpm-lock.yaml`;
- reproduzierbare Python-Installation aus `uv.lock` mit Python 3.13.14;
- Prettier- und Ruff-Formatprüfung;
- ESLint, Ruff und mypy strict;
- TypeScript- und Python-Unit-Tests;
- beide Next.js-Produktionsbuilds;
- TypeScript-Library-Builds;
- Python-Wheel und Source Distribution;
- FastAPI-Factory- und OpenAPI-Prüfung;
- Secret-Scan;
- realer API-Start mit negativem Readiness-Fall;
- realer Start und gemeinsamer Shutdown von Web, Admin und API über `pnpm dev`,
  wobei nur der nicht verfügbare Docker-Aufruf durch einen lokalen Teststub ersetzt
  wurde;
- zweimaliger Setup-Kontrollfluss mit unveränderter `.env` beim zweiten Lauf,
  wobei Docker und Migration durch klar gekennzeichnete Teststubs ersetzt wurden.

`pnpm verify:foundation` ist **nicht erfolgreich abgeschlossen**. Der Befehl lief
bis einschließlich Secret-Scan erfolgreich und stoppte anschließend erwartungsgemäß
bei der Docker-Compose-Prüfung, weil in der Ausführungsumgebung keine Docker Engine,
kein Docker-CLI und keine alternative Container-Engine vorhanden waren.

Deshalb werden PostgreSQL, MinIO, der gepinnte MinIO-Healthcheck, die Live-Migration,
die markierten Infrastrukturtests, der positive Live-Fall von `/ready` und der
GitHub-Actions-Integration-Job ausdrücklich **nicht** als erfolgreich behauptet.

## 3. Umgesetzte Änderungen

### 3.1 Nx

- Der zweite top-level `analytics`-Eintrag wurde aus `nx.json` entfernt.
- Die Datei enthält nach JSON-Parsing genau einen `analytics`-Schlüssel mit dem
  Wert `false`.

### 3.2 API-Readiness

`GET /ready` prüft PostgreSQL und Object Storage parallel.

- HTTP `200` nur, wenn beide Checks erfolgreich sind;
- HTTP `503`, wenn eine oder beide Abhängigkeiten nicht verfügbar sind;
- getrennte Checks `database` und `object_storage`;
- keine URLs, Credentials, Connection Strings, Exceptions oder internen Details
  im Response;
- interner MinIO-HTTP-Check ignoriert Host-Proxyvariablen, damit lokale bzw.
  interne Storage-Readiness nicht über einen externen Proxy läuft.

Erfolgreich real geprüfter negativer Response:

```json
{
  "status": "not_ready",
  "checks": {
    "database": { "status": "down" },
    "object_storage": { "status": "down" }
  }
}
```

### 3.3 Tests

Explizite Unit-Tests decken ab:

1. Datenbank und Object Storage verfügbar;
2. nur Datenbank nicht verfügbar;
3. nur Object Storage nicht verfügbar;
4. beide nicht verfügbar.

Ein zusätzlicher Regressionstest prüft, dass der Object-Storage-Adapter Host-
Proxyvariablen ignoriert und einen Verbindungsfehler sicher als `False` meldet.

Die markierten Infrastrukturtests prüfen bei aktiviertem Live-Workflow:

- PostgreSQL über `SELECT 1`;
- MinIO über den Object-Storage-Readiness-Adapter.

### 3.4 Infrastruktur-Workflow

`pnpm test:infra` führt in `tools/scripts/test-infra.mjs` folgenden echten Ablauf
aus, sobald Docker verfügbar ist:

1. Docker Compose verfügbar machen und Konfiguration validieren;
2. freie Host-Ports dynamisch reservieren;
3. ein eindeutig benanntes Compose-Projekt erzeugen;
4. PostgreSQL und MinIO mit isolierten Projekt-Volumes starten;
5. über `docker compose up --wait --wait-timeout 120` auf gesunde Container warten;
6. Alembic bis `head` migrieren;
7. markierte Infrastrukturtests ausführen;
8. Uvicorn als realen API-Prozess starten;
9. `/health`, `/ready` und `/openapi.json` gegen den laufenden Prozess prüfen;
10. bei einem Fehler Containerstatus, Containerlogs und API-Log ausgeben;
11. API, Container, Netzwerk und ausschließlich die isolierten Volumes bei Erfolg,
    Fehler oder Signal bereinigen.

Normale Entwicklungsdaten werden nicht adressiert. Der Workflow verwendet ein
separates Compose-Projekt, projektbezogene Volumes und dynamische Ports. Der zuvor
global benannte Compose-Netzwerkname wurde entfernt, damit auch das Netzwerk
projektbezogen isoliert bleibt.

### 3.5 Root-Kommandos

Hinzugefügt:

```bash
pnpm test:infra
pnpm verify:foundation
```

`pnpm verify:foundation` umfasst in dieser Reihenfolge:

1. Formatierung;
2. Linting;
3. Unit-Tests;
4. Builds;
5. OpenAPI-Prüfung;
6. Secret-Scan;
7. Docker-Compose-Prüfung;
8. Live-Infrastruktur, Migration, Infrastrukturtests und API-Smoke-Test.

### 3.6 GitHub Actions

Die bestehende Quality-Job-Struktur bleibt erhalten. Zusätzlich wurde ein eigener
Job `integration` ergänzt. Er installiert die eingefrorenen Abhängigkeiten und
führt `pnpm test:infra` aus. Damit enthält der Job den realen Start von PostgreSQL
und MinIO, Health-Wait, Migration, Infrastrukturtests, API-Smoke-Test,
Fehlerdiagnostik und Cleanup über das gemeinsame, lokal ebenfalls ausführbare
Script.

Der Workflow wurde syntaktisch als YAML geparst, aber nicht auf GitHub Actions
ausgeführt.

### 3.7 MinIO-Healthcheck

Das Compose-Image bleibt auf
`minio/minio:RELEASE.2025-04-22T22-12-26Z` gepinnt; `latest` wird nicht verwendet.
Der bisherige Check `mc ready local` setzte einen nicht im Projekt konfigurierten
Alias voraus. Er wurde auf MinIOs lokalen HTTP-Readiness-Endpunkt über `curl`
umgestellt.

Ob genau das gepinnte Image die verwendete `curl`-Binary enthält und der Check im
Container erfolgreich wird, konnte ohne Container-Engine nicht praktisch geprüft
werden. Dieses Akzeptanzkriterium bleibt offen, bis `pnpm test:infra` auf einem
Docker-Host erfolgreich durchläuft.

### 3.8 Setup und Development Lifecycle

`pnpm setup` bleibt wiederholbar:

- `.env` wird nur angelegt, wenn sie fehlt;
- `uv sync --frozen` ist deklarativ;
- `docker compose up -d --wait` ist deklarativ;
- `alembic upgrade head` ist wiederholbar;
- ein explizites Wait-Timeout von 120 Sekunden wurde ergänzt.

Der Kontrollfluss wurde mit lokalen Teststubs zweimal ausgeführt. Beim ersten Lauf
wurde `.env` erzeugt, beim zweiten Lauf nicht überschrieben; beide SHA-256-Werte
waren identisch. Eine Live-Wiederholung mit PostgreSQL und MinIO war nicht möglich.
Die erzeugte lokale `.env` wurde nach dem Test wieder entfernt.

`pnpm dev` startet Web, Admin und API als drei überwachte Prozessgruppen. Bei
`SIGINT` oder `SIGTERM` erhalten alle drei zunächst Zeit für einen sauberen
Shutdown; verbleibende Prozesse werden nach fünf Sekunden gruppenweise beendet.
Der echte Root-Befehl wurde mit einem Docker-Teststub ausgeführt:

- Web antwortete mit HTTP `200`;
- Admin antwortete mit HTTP `200`;
- API `/health` antwortete mit HTTP `200`;
- nach `SIGINT` waren alle drei Ports geschlossen.

Die Infrastruktur war bei diesem Lifecycle-Test nicht real.

### 3.9 Dokumentation

Aktualisiert wurden:

- `README.md`;
- `docs/engineering-handbook/ENGINEERING_HANDBOOK.md`;
- `docs/api/README.md`.

Dokumentiert sind Readiness-Vertrag, neue Root-Kommandos, isolierter
Infrastrukturablauf, Cleanup, Definition of Done, CI-Integration und die Pflicht,
nicht ausgeführte Live-Prüfungen nicht als erfolgreich darzustellen.

## 4. Tatsächlich ausgeführte Kommandos und Ergebnisse

### 4.1 Abhängigkeiten

Erster Lauf in der eingeschränkten Laufzeit:

```bash
pnpm install --frozen-lockfile
uv sync --frozen
```

Ergebnis: beide Aufrufe scheiterten ausschließlich an schreibgeschützten globalen
Cache-/Installationspfaden unter `/root`; dies war kein Lockfile- oder
Repositoryfehler.

Wiederholung mit taskbezogenen temporären Caches:

```bash
pnpm install --frozen-lockfile --store-dir /tmp/ude-001a-pnpm-store
UV_CACHE_DIR=/tmp/ude-001a-uv-cache \
UV_PYTHON_INSTALL_DIR=/tmp/ude-001a-uv-python \
uv sync --frozen
```

Ergebnis:

- pnpm: erfolgreich, 283 Pakete installiert, Lockfile gegen die integrierten
  Supply-Chain-Regeln geprüft;
- uv: erfolgreich, CPython 3.13.14 und 39 Pakete aus `uv.lock` installiert;
- Lockfiles wurden nicht verändert.

### 4.2 Finaler Foundation-Gesamtlauf

```bash
UV_CACHE_DIR=/tmp/ude-001a-uv-cache \
UV_PYTHON_INSTALL_DIR=/tmp/ude-001a-uv-python \
pnpm verify:foundation
```

Tatsächliches Ergebnis:

| Prüfschritt              | Ergebnis                                               |
| ------------------------ | ------------------------------------------------------ |
| Prettier                 | erfolgreich; alle Dateien formatiert                   |
| Ruff format check        | erfolgreich; 23 Dateien geprüft                        |
| ESLint                   | erfolgreich; 5 Nx-Projekte                             |
| Ruff lint                | erfolgreich                                            |
| mypy strict              | erfolgreich; 22 Python-Quelldateien                    |
| TypeScript-Tests         | erfolgreich; 6 Tests                                   |
| Python-Unit-Tests        | erfolgreich; 10 Tests, 2 Infrastrukturtests abgewählt  |
| Frontend-/Library-Builds | erfolgreich; Web, Admin und beide TypeScript-Libraries |
| Tool-Syntaxbuild         | erfolgreich                                            |
| Python-Build             | erfolgreich; Wheel und Source Distribution             |
| FastAPI/OpenAPI          | erfolgreich                                            |
| Secret-Scan              | erfolgreich                                            |
| Docker Compose           | nicht ausgeführt; `docker` nicht vorhanden             |
| Live-Infrastruktur       | nicht ausgeführt                                       |
| Migration                | nicht ausgeführt                                       |
| Infrastrukturtests       | nicht ausgeführt                                       |
| positiver API-Smoke-Test | nicht ausgeführt                                       |
| Gesamtbefehl             | Exit `1` bei Docker-Compose-Prüfung                    |

### 4.3 Isolierter Infrastruktur-Befehl

```bash
pnpm test:infra
```

Tatsächliches Ergebnis: Exit `1` vor dem Start von Containern mit
`docker compose version` nicht verfügbar. Es wurden keine Container, Netzwerke oder
Volumes angelegt.

### 4.4 Compose- und CI-Prüfung

```bash
pnpm compose:validate
```

Tatsächliches Ergebnis: nicht ausführbar, weil das Docker-CLI fehlt.

Zusätzliche statische Prüfung:

```bash
uv run python -c "import yaml; ..."
```

Tatsächliches Ergebnis: `docker-compose.yml` und `.github/workflows/ci.yml` wurden
erfolgreich als YAML geparst. Das ist ausdrücklich kein Ersatz für
`docker compose config` oder einen GitHub-Actions-Lauf.

### 4.5 Realer API-Prozess ohne Infrastruktur

Uvicorn wurde mit absichtlich nicht erreichbaren lokalen Dependency-Ports gestartet.

| Endpoint        | Tatsächliches Ergebnis                               |
| --------------- | ---------------------------------------------------- |
| `/health`       | HTTP `200`, `healthy`                                |
| `/ready`        | HTTP `503`, beide getrennten Checks `down`           |
| `/openapi.json` | HTTP `200`, erwarteter API-Titel und Operationspfade |

Dieser Lauf deckte zunächst eine unerwünschte Host-SOCKS-Proxyvererbung im
MinIO-Adapter auf. Nach der Korrektur und dem Regressionstest war der reale
negative Readiness-Smoke-Test erfolgreich.

### 4.6 Setup- und Dev-Prüfung

Realer Aufruf ohne Teststubs:

```bash
pnpm setup
pnpm dev
```

Beide Befehle stoppten vor Infrastruktur-/Anwendungsstart, weil Docker nicht
installiert ist. `pnpm dev` meldet den fehlenden Docker-Aufruf explizit.

Zusätzliche klar begrenzte Kontrolltests:

- `pnpm setup` zweimal mit Docker-/uv-Teststubs: beide Läufe Exit `0`, `.env`
  unverändert;
- echter `pnpm dev` mit ausschließlich dem Docker-Aufruf als Teststub: Web, Admin
  und API gestartet, alle drei HTTP-Checks `200`, gemeinsamer Shutdown erfolgreich.

## 5. Status der Akzeptanzkriterien

| Nr. | Akzeptanzkriterium                                                                      | Status                                                      | Nachweis / Einschränkung                                                                         |
| --: | --------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
|   1 | doppelten `analytics`-Eintrag entfernen                                                 | umgesetzt und geprüft                                       | genau ein JSON-Schlüssel vorhanden                                                               |
|   2 | `/ready` prüft PostgreSQL und Object Storage, 200/503-Vertrag, getrennte sichere Checks | umgesetzt; Unit- und negativer Realtest erfolgreich         | positiver Live-Fall ohne Docker offen                                                            |
|   3 | vier Dependency-Kombinationen als Unit-Tests                                            | umgesetzt und erfolgreich                                   | alle vier Fälle in `test_health.py`; gesamter Python-Unitlauf 10/10                              |
|   4 | echter Infrastruktur-Workflow inklusive Migration, Tests und API-Smoke                  | implementiert, nicht live ausgeführt                        | `pnpm test:infra`; Docker fehlt                                                                  |
|   5 | Root-Kommandos `test:infra` und `verify:foundation`                                     | umgesetzt                                                   | beide aufrufbar; Live-Anteil stoppt korrekt wegen Docker                                         |
|   6 | vollständiger Inhalt von `verify:foundation`                                            | umgesetzt; teilweise ausgeführt                             | statische Schritte erfolgreich, Live-Schritte offen                                              |
|   7 | isolierte Volumes / separates Compose-Projekt                                           | umgesetzt                                                   | eindeutiger Projektname, dynamische Ports, projektbezogene Volumes/Netzwerk; Live-Nachweis offen |
|   8 | GitHub-Actions-Integration-Job                                                          | umgesetzt, nicht ausgeführt                                 | YAML erfolgreich geparst; GitHub-Lauf offen                                                      |
|   9 | gepinnten MinIO-Healthcheck praktisch prüfen und ggf. korrigieren                       | korrigiert, praktische Prüfung offen                        | HTTP-Readiness statt unkonfiguriertem `mc`-Alias; Docker fehlt                                   |
|  10 | `pnpm setup` idempotent und `pnpm dev` sauber starten/beenden                           | Scriptlogik und Prozess-Lifecycle geprüft; Live-Setup offen | Setup zweimal mit Stubs; echter App-Start/Stop mit Docker-Stub erfolgreich                       |
|  11 | README, Engineering Handbook und API-Dokumentation                                      | umgesetzt                                                   | alle drei Dokumente aktualisiert                                                                 |
|  12 | `FOUNDATION_VERIFICATION_REPORT.md`                                                     | umgesetzt                                                   | diese Datei                                                                                      |

## 6. Infrastruktur- und Migrationsstatus

| Komponente                           | Status in dieser Prüfung                                          |
| ------------------------------------ | ----------------------------------------------------------------- |
| Docker Engine / CLI                  | nicht vorhanden                                                   |
| Docker Compose                       | nicht vorhanden                                                   |
| PostgreSQL-Container                 | nicht gestartet                                                   |
| MinIO-Container                      | nicht gestartet                                                   |
| PostgreSQL Healthcheck               | nicht live geprüft                                                |
| MinIO Healthcheck im gepinnten Image | nicht live geprüft                                                |
| isolierte Volumes                    | vom Workflow implementiert, nicht angelegt                        |
| Alembic `upgrade head`               | nicht gegen Live-PostgreSQL ausgeführt                            |
| Infrastrukturtests                   | 2 vorhanden, im Unitlauf korrekt abgewählt, live nicht ausgeführt |
| API-Smoke mit beiden Dependencies up | nicht ausgeführt                                                  |

## 7. Warnungen und technische Restpunkte

1. Die Laufzeit setzt gleichzeitig `NO_COLOR` und `FORCE_COLOR`; Node meldet dies
   kosmetisch bei Nx-Unterprozessen.
2. Nx gab beim parallelen Build eine `MaxListenersExceededWarning` für 14 statt 13
   Exit-Listener aus. Alle Targets liefen dennoch erfolgreich. Die Warnung sollte
   bei einem künftigen Nx-Update erneut beobachtet werden.
3. uv konnte zwischen temporärem Cache und Workspace nicht hardlinken und fiel auf
   Kopieren zurück. Dies beeinflusste nur die Installationsgeschwindigkeit.
4. Die aktuelle Umgebung hat schreibgeschützte globale Cachepfade; die erfolgreiche
   Prüfung verwendete deshalb taskbezogene Pfade unter `/tmp`.
5. Das MinIO-Image und sein `curl`-Healthcheck benötigen zwingend einen echten
   Docker-Lauf vor Abnahme.
6. CI ist konfiguriert, aber weder `CI / quality` noch `CI / integration` wurde in
   diesem Auftrag auf GitHub ausgeführt.

## 8. Offene Eigentümeraufgaben

1. Auf einem Rechner mit Docker Engine und Docker Compose v2 im Repository
   ausführen:

   ```bash
   pnpm install --frozen-lockfile
   uv sync --frozen
   pnpm verify:foundation
   ```

2. Falls der gepinnte MinIO-Container den `curl`-Healthcheck nicht ausführen kann,
   den Check anhand der tatsächlich im **gepinnten** Image verfügbaren Binary
   korrigieren; `latest` darf nicht verwendet werden.
3. Nach erfolgreichem Live-Lauf prüfen, dass Alembic `head`, beide
   Infrastrukturtests und `/ready` mit beiden Checks `up` bestätigt werden.
4. Den Stand in das private GitHub-Repository pushen und die Jobs `CI / quality`
   und `CI / integration` real ausführen.
5. Bei einem CI-Fehler die vom Integration-Script ausgegebenen Containerstatus-,
   Containerlog- und API-Logdaten prüfen.
6. Branch Protection so aktualisieren, dass neben `CI / quality` auch
   `CI / integration` erforderlich ist.
7. Die bereits aus Development Order 001 offenen `CODEOWNERS`-, Rechtsinhaber-,
   Jahres- und privaten Security-Kontakt-Platzhalter durch die realen Eigentümerdaten
   ersetzen.

## 9. Geänderte oder ergänzte Projektdateien

- `.github/workflows/ci.yml`
- `README.md`
- `apps/api/project.json`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_storage_health.py`
- `apps/api/ude_api/routes/health.py`
- `docker-compose.yml`
- `docs/api/README.md`
- `docs/engineering-handbook/ENGINEERING_HANDBOOK.md`
- `libs/backend/core/src/ude_backend_core/storage.py`
- `nx.json`
- `package.json`
- `tests/integration/test_database_readiness.py`
- `tools/project.json`
- `tools/scripts/dev.mjs`
- `tools/scripts/setup.mjs`
- `tools/scripts/test-infra.mjs`
- `tools/scripts/validate-compose.mjs`
- `tools/scripts/verify-foundation.mjs`
- `FOUNDATION_VERIFICATION_REPORT.md`

## 10. Abnahmehinweis

Development Order 001A ist code-seitig umgesetzt. Die Foundation darf erst nach
einem erfolgreichen `pnpm verify:foundation` auf einem Docker-fähigen System und
einem real erfolgreichen GitHub-Integration-Job als vollständig verifiziert oder
„CI grün“ bezeichnet werden. Development Order 002 wurde nicht begonnen.

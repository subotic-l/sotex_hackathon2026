# Sotex Solutions Hackathon 2026

Dobrodošli u Sotex Solutions Hackathon Starter repozitorijum.

## Setup

Da bismo vam pružili maksimalnu iskorišćenost vremena za rešavanje problema pripremili smo hackathon starter kit.

Jedini alat koji vam je neophodan da iskoristite starter kit je **Docker**.

Za Windows: [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/)
Za Linux: [Docker Engine](https://docs.docker.com/engine/install/)

(Samo za Windows) Komande:
```powershell
git config core.autocrlf false
git rm --cached -r .
git reset --hard
```
podešavaju kako rade line endings da bi Linux kontejneri mogli da pravilno pročitaju fajl.

Komanda:
```bash
docker compose up -d --build
```
će automatski podesiti SQL Server bazu podataka i importovati hackathon bazu podataka.

Komanda:
```bash
docker logs -f sotex_hackathon_db_init
```
će vam prikazati status import-a.

SQL Client konfiguracija (SSMS, DataGrip, Beekeeper Studio) 

| Setting | Value |
| --- | --- |
| Connection host | localhost |
| Connection port | 1433 |
| Connection user | sa |
| Connection password | SotexSolutions123! |
| Default database | SotexHackathon |
| Trust server certificate | ✓ |

## Ostalo

Napravite svoj timski repozitorijum i dodajte za collaborator mentore:
- nedeljkovignjevic
- AleksaBajat
- matija-mg
- sotex-halid-pasanovic
- sdragan15-00

Unutar assets foldera nalaze se prezentacije i dodatan materijal.
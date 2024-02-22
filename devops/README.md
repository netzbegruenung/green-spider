# DevOps

Die Skripte in diesem Verzeichnis erlauben das weitgehend automatisierte
Provisionieren eines Hetzner Cloud Servers, Ausführen von Spider Jobs und Entfernen des Servers nach Fertigstellung.

**Warnung**: Die Scripte sind aktuell so einfach, dass die erzeugten Server nur nach erfolgreicher
Ausführung des Jobs entfernt werden. Im Fall eines Fehlers muss der provisionierte
Server unbedingt manuell entfernt werden, um unnötige Kosten zu vermeiden.

## Voraussetzungen

- SSH Public Key ist bei Hetzner hinterlegt und in den Scripten eingetragen (siehe 'ssh_keys')
- API Token für Hetzner in Datei `secrets/hetzner-api-token.sh` im Format `export API_TOKEN=<token>`
- Service Account mit Schreibrechten für Google Cloud Datenbank als JSON-Datei in `secrets/datastore-writer.json`
- curl
- [jq](https://jqlang.github.io/jq/)
- ssh

## Generelles

- Die Skripte müssen aus dem root-Verzeichnis des lokalen clone dieses git Repositories ausgeführt werden.
- Der Terminal muss bis zum Ende der Ausführung geöffnet bleiben.
- Es sollte immer das Container Image verwendet werden, welches das letzte Release abbildet. TODO: Erklären, wie man das am einfachsten findet, und wo die Version angepasst werden muss.

## Spider starten

```nohighlight
devops/run-job.sh spider
```

## Webapp deployen

```nohighlight
devops/deploy-webapp.sh
```

## Einloggen per SSH

```nohighlight
devops/ssh.sh
```

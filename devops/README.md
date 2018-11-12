# DevOps

Die Skripte in diesem Verzeichnis erlauben das weitgehend automatisierte
Provisionieren eines Servers, Ausführen von Jobs wie Spider und Screenshotter
und Entfernen des Servers.

**Warnung**: Die Scripte sind aktuell so einfach, dass die erzeugten Server nur nach erfolgreicher
Ausführung des Jobs entfernt werden. Im Fall eines Fehlers muss der provisionierte
Server unbedingt manuell entfernt werden, um unnötige Kosten zu vermeiden.

## Voraussetzungen

- SSH Public Key ist bei Hetzner hinterlegt und in den scripten eingetragen (siehe 'ssh_keys')
- API Token für Hetzner in Datei 'secrets/hetzner-api-token.sh' im Format 'export API_TOKEN=<token>'
- Service account JSON Datei mit Schreibrechten in 'secrets/datastore-writer.json'
- curl
- jq (https://stedolan.github.io/jq/)
- ssh

## Generelles

- Die Skripte müssen aus dem root-Verzeichnis des git repositories ausgeführt werden
- Der Terminal muss bis zum Ende der Ausführung geöffnet bleiben.

## Spider starten

```nohighlight
devops/run-job.sh spider
```

## Screenshots erstellen

```nohighlight
devops/run-job.sh screenshotter
```

## Webapp deployen

```nohighlight
devops/deploy-webapp.sh
```

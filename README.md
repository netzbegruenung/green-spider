# Green Spider

Green Spider prüft Websites von Bündnis 90/Die Grünen Gliederungen auf Einhaltung ausgewählter Standards. Die Ergebnisse sind unter [green-spider.netzbegruenung.de](https://green-spider.netzbegruenung.de/) einsehbar.

Dieses Repository beinhaltet Code für den _Spider_, der Websites besucht und prüft.

Green Spider ist ein Projekt von [netzbegrünung e. V.](https://blog.netzbegruenung.de/).

## Übersicht aller Green Spider Repositories

- **Spider:** Dieses Repository
- **Webapp:** Darstellung der Spider-Ergebnisse. Siehe [netzbegruenung/green-spider-webapp](https://github.com/netzbegruenung/green-spider-webapp/). Dazu gehören
  - **API**: [netzbegruenung/green-spider-api](https://github.com/netzbegruenung/green-spider-api)
  - **Elasticsearch**
  - **Indexer:** Lädt Ergebnisdaten in Elasticsearch. Siehe [netzbegruenung/green-spider-indexer](https://github.com/netzbegruenung/green-spider-indexer)
- **Auswertung**: R Projekt zur Auswertung der Ergebnisse. Siehe [netzbegruenung/green-spider-analysis](https://github.com/netzbegruenung/green-spider-analysis)

## Green Spider verbessern

Du kannst über den Chatbegrünung-Kanal [#green-spider](https://chatbegruenung.de/channel/green-spider) Probleme melden, Fragen stellen und Verbesserungsvorschläge machen. Wenn Du möchtest, kannst Du auch die [Issues](https://github.com/netzbegruenung/green-spider/issues) hier in diesem Repository einsehen ud kommentieren oder selbst ein Issue anlegen.

## Betrieb

Alle Informationen zum Betrieb befinden sich im Verzeichnis [devops](https://github.com/netzbegruenung/green-spider/tree/master/devops).

## Entwicklung

Green Spider ist in Python 3 geschrieben und wird aktuell unter 3.6 getestet und ausgeführt.

Aufgrund zahlreicher Abhängigkeiten empfiehlt es sich, den Spider Code lokal in Docker
auszuführen.

Das Image wird über den folgenden Befehl erzeugt:

```nohighlight
make
```

Das dauert beim ersten Ausführen einige Zeit, wiel einige Python-Module das Kompilieren diverser Libraries erfordern.
Nach dem ersten erfolgreichen Durchlauf dauert ein neuer Aufruf von `make` nur noch wenige Sekunden.

### Tests ausführen

In aller Kürze: `make test`

### Spider testweise ausführen (Debugging)

Der Spider kann einzelne URLs verarbeiten, ohne die Ergebnisse in eine Datenbank zu schreiben.
Am einfachsten geht das über den `make spider` Befehl, so:

```nohighlight
make spider ARGS="--url http://www.example.com/"
```

Ohne `ARGS` aufgerufen, arbeitet der Spider eine Jobliste ab. Dies erfordert Zugriff auf die entsprechende Datenbank.

Wenn nur eine einzelne Site gespidert werden soll, die Ergebnisse aber in die Datenbank geschrieben werden sollen, kann der Spider so mit `--job` und einem JSON-Object aufgerufen werden (Beispiel):

```nohighlight
docker run --rm -ti \
  -v $(pwd)/volumes/dev-shm:/dev/shm \
  -v $(pwd)/secrets:/secrets \
  -v $(pwd)/screenshots:/screenshots \
  -v $(pwd)/volumes/chrome-userdir:/opt/chrome-userdir \
  --shm-size=2g \
  ghcr.io/netzbegruenung/green-spider:latest python3 cli.py \
    --credentials-path /secrets/datastore-writer.json \
    --loglevel debug \
    spider --job '{"url": "https://gruene-porta-westfalica.de/home/", "city": "Porta Westfalica", "country": "DE", "district": "Minden-Lübbecke", "level": "DE:ORTSVERBAND", "state":" Nordrhein-Westfalen", "type": "REGIONAL_CHAPTER"}'
```

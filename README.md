# Green Spider

Initiative und Tools zur Förderung eines benutzer*innenfreundlichen Auftritts von Bündnis 90/Die Grünen im Web.

Zur Auswertung: [https://green-spider.netzbegruenung.de/](https://green-spider.netzbegruenung.de/)

## Tools

- **Spider:** Sammelt Informationen über Websites von B90/GRÜNE Gliederungen
- **Screenshotter:** Erstellt Seiten-Screenshots. Siehe [netzbegruenung/green-spider-screenshotter](https://github.com/netzbegruenung/green-spider-screenshotter/)
- **Webapp:** Darstellung der Spider-Ergebnisse. Siehe [netzbegruenung/green-spider-webapp](https://github.com/netzbegruenung/green-spider-webapp/). Dazu gehören
  - **API**: [netzbegruenung/green-spider-api](https://github.com/netzbegruenung/green-spider-api)
  - **Elasticsearch**
  - **Indexer:** Lädt Ergebnisdaten in Elasticsearch. Siehe [netzbegruenung/green-spider-indexer](https://github.com/netzbegruenung/green-spider-indexer)
- **Auswertung**: R Projekt zur Auswertung der Ergebnisse. Siehe [netzbegruenung/green-spider-analysis](https://github.com/netzbegruenung/green-spider-analysis)

## Aktivitäten

Es ist geplant, auf Basis der gesammelten Informationen (siehe Spider) Informationen an die Betreiber*innen der Websites zu versenden. Hierzu müssen Prozesse erarbeitet und vermutlich weitere Tools geschaffen werden.

## Community

Green Spider ist ein Projekt des [netzbegrünung](https://blog.netzbegruenung.de/) e. V. -- Mitwirkung ist herzlich willkommen.

Zur Kommunikation dient der Chatbegrünung-Kanal [#green-spider](https://chatbegruenung.de/channel/green-spider) sowie die [Issues](https://github.com/netzbegruenung/green-spider/issues) hier in diesem Repository.

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
  quay.io/netzbegruenung/green-spider:latest python cli.py \
    --credentials-path /secrets/datastore-writer.json \
    --loglevel debug \
    spider --job '{"url": "https://xn--grne-porta-westfalica-9hc.de/", "city": "Porta Westfalica", "country": "DE", "district": "Minden-Lübbecke", "level": "DE:ORTSVERBAND", "state":" Nordrhein-Westfalen", "type": "REGIONAL_CHAPTER"}'
```

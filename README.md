# Green Spider

Initiative und Tools zur Förderung eines benutzer*innenfreundlichen Auftritts von BÜNDNIS 90/DIE GRÜNEN im Web.

Zur Auswertung: [https://green-spider.netzbegruenung.de/](https://green-spider.netzbegruenung.de/)

## Tools

- **Spider:** Sammelt Informationen über Websites von B90/GRÜNE Gliederungen
- **Webapp:** Darstellung der Spider-Ergebnisse. Siehe [Netzbegruenung/green-spider-webapp](https://git.verdigado.com/Netzbegruenung/green-spider-webapp/). Dazu gehören
  - **API**: [NB-Public/green-spider-api](https://git.verdigado.com/NB-Public/green-spider-api)
  - **Elasticsearch**
  - **Indexer:** Lädt Ergebnisdaten in Elasticsearch. Siehe [NB-Public/green-spider-indexer](https://git.verdigado.com/NB-Public/green-spider-indexer)
- **Auswertung**: R Projekt zur Auswertung der Ergebnisse. Siehe [NB-Public/green-spider-analysis](https://git.verdigado.com/NB-Public/green-spider-analysis)

## Aktivitäten

Es ist geplant, auf Basis der gesammelten Informationen (siehe Spider) Informationen an die Betreiber*innen der Websites zu versenden. Hierzu müssen Prozesse erarbeitet und vermutlich weitere Tools geschaffen werden.

## Community

Green Spider ist ein Projekt des [netzbegrünung](https://blog.netzbegruenung.de/) e. V. -- Mitwirkung ist herzlich willkommen.

Zur Kommunikation dient der Chatbegrünung-Kanal [#green-spider](https://chatbegruenung.de/channel/green-spider) sowie die [Issues](https://github.com/netzbegruenung/green-spider/issues) hier in diesem Repository.

## Betrieb

Alle Informationen zum Betrieb befinden sich im Verzeichnis [devops](https://github.com/netzbegruenung/green-spider/tree/main/devops).

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
  quay.io/netzbegruenung/green-spider:latest python3 cli.py \
    --credentials-path /secrets/datastore-writer.json \
    --loglevel debug \
    spider --job '{"url": "https://gruene-porta-westfalica.de/", "city": "Porta Westfalica", "country": "DE", "district": "Minden-Lübbecke", "level": "DE:ORTSVERBAND", "state":" Nordrhein-Westfalen", "type": "REGIONAL_CHAPTER"}'
```

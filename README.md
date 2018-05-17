# Green Spider

Initiative und Tools zur Förderung eines benutzer*innenfreundlichen Auftritts von Bündnis 90/Die Grünen im Web

## Tools

- Spider: Sammelt Informationen über Websites von B90/GRÜNE Gliederungen

- Webapp: Darstellung der Spider-Ergebnisse unter [green-spider.netzbegruenung.de](http://green-spider.netzbegruenung.de/)

## Aktivitäten

Es ist geplant, auf Basis der gesammelten Informationen (siehe Spider) Informationen an die Betreiber*innen der Websites zu versenden. Hierzu müssen Prozesse erarbeitet und vermutlich weitere Tools geschaffen werden.

## Community

Green Spider ist ein Projekt des [netzbegrünung](https://blog.netzbegruenung.de/) e. V. -- Mitwirkung ist herzlich willkommen.

Zur Kommunikation dient der Chatbegrünung-Kanal [#green-spider](https://chatbegruenung.de/channel/green-spider) sowie die [Issues](https://github.com/netzbegruenung/green-spider/issues) hier in diesem Repository.

## Anleitung

### Spider ausführen

Damit werden alle bekannten WWW-Adressen aus [netzbegruenung/green-directory](https://github.com/netzbegruenung/green-directory) geprüft und Daten dazu gesammelt.

Voraussetzungen:

- GNU make
- Python 3
- virtualenv

Starte den Vorgang mit diesem Befehl:

```nohighlight
make spider
```

Das Ergebnis ist die Datei `webapp/dist/data/spider_result.json`. Wenn Du die neuen Daten ins Repository einspielen möchtest, erstelle bitte einen Pull Request.

### Screenshots erstellen

Achtung: Dieser Vorgang kann viele Stunden dauern.

Voraussetzungen:

- Docker
- Zugangsdaten für den Google Cloud Storage bucket (derzeit über [marians](https://github.com/marians))

Befehl:

```
make screenshots
```

Damit werden neue Screenshots für alle Sites (jeweils die erste kanonische URL einer Site) erstellt und die Datei `webapp/dist/data/screenshots.json` aktualisiert. Screenshots werden vorübergehend in `./temp` abgelegt, wo sie jedoch danach gelöscht werden können.

### Webapp aktualisieren

Die unter https://netzbegruenung.github.io/green-spider/ veröffentlichte Webapp zeigt den Inhalt des [docs](https://github.com/netzbegruenung/green-spider/tree/master/docs) Verzeichnisses für den `master` Branch dieses repositories an. Dieser kann automatisch neu erzeugt werden.

Voraussetzungen:

- npm

Um den Inhalt des docs-Verzeichnisses zu aktualisieren, gibt es im Makefile dieses Kommando:

```nohighlight
make webapp
```

Das Ergebniss sollte als Pull Request beigesteuert werden.

# Green Spider

Initiative und Tools zur Förderung eines benutzer*innenfreundlichen Auftritts von Bündnis 90/Die Grünen im Web.

Zur Auswertung: [https://green-spider.netzbegruenung.de/](https://green-spider.netzbegruenung.de/)

## Tools

- Spider: Sammelt Informationen über Websites von B90/GRÜNE Gliederungen

- Screenshotter: Erstellt Seiten-Screenshots. Siehe [netzbegruenung/green-spider-screenshotter](https://github.com/netzbegruenung/green-spider-screenshotter/)

- Webapp: Darstellung der Spider-Ergebnisse unter [green-spider.netzbegruenung.de](https://green-spider.netzbegruenung.de/)

## Aktivitäten

Es ist geplant, auf Basis der gesammelten Informationen (siehe Spider) Informationen an die Betreiber*innen der Websites zu versenden. Hierzu müssen Prozesse erarbeitet und vermutlich weitere Tools geschaffen werden.

## Community

Green Spider ist ein Projekt des [netzbegrünung](https://blog.netzbegruenung.de/) e. V. -- Mitwirkung ist herzlich willkommen.

Zur Kommunikation dient der Chatbegrünung-Kanal [#green-spider](https://chatbegruenung.de/channel/green-spider) sowie die [Issues](https://github.com/netzbegruenung/green-spider/issues) hier in diesem Repository.

## Anleitung

### Spider ausführen

Voraussetzungen:

- Docker
- Schlüssel mit Schreibrecht für die Ergebnis-Datenbank

Um alle Sites aus aus [netzbegruenung/green-directory](https://github.com/netzbegruenung/green-directory) zu spidern:

```nohighlight
make spiderjobs
make spider
```

Alternativ kann wie im nachfolgenden Beispiel gezeogt das Spidern einer einzelnen URL angestoßen werden. Diese muss nicht zwingend Teil des `green-directory` sein.

```nohighlight
docker run --rm -ti \
  -v $PWD/secrets:/secrets spider \
  spider.py --credentials-path /secrets/datastore-writer.json \
  jobs --url https://www.trittin.de/

make spider
```

### Screenshots erstellen

Siehe [green-spider-screenshotter](https://github.com/netzbegruenung/green-spider-screenshotter)

### Webapp aktualisieren

Voraussetzungen:

- npm
- Docker
- Schlüssel mit Leserecht für Screenshot- und Ergebnis-Datenbank

Die beiden nachfolgenden Kommandos erzeugen die JSON-Exporte der Spider-Ergebnisse
und Screenshots und aktualisieren die Webapp.

```nohighlight
make export
make webapp
```

Das Ergebniss sollte in einen neuen Branch gepusht und als Pull Request hinzugefügt werden.

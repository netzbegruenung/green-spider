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

Green Spider ist in Python geschrieben. Der Code ist darauf ausgelegt, in einem Docker Container ausführbar zu sein. Darüber hinaus _kann_ er möglicherweise in einer lokalen Python-Umgebung funktionieren. Für reproduzierbare Bedingungen beim Ausführen des headless Browsers (chromium, chromedriver) empfielt es sich jedoch, in einer Container-Umgebung zu testen.

Das aktuellste Container Image steht unter `ghcr.io/netzbegruenung/green-spider:latest` zur Verfügung. Alternative Versionen und Tags sind unter [Packages](https://github.com/netzbegruenung/green-spider/pkgs/container/green-spider) auffindbar.

Lokal kann das Image mit diesem Befehl gebaut werden:

```nohighlight
make dockerimage
```

### Unittests ausführen

Nach dem Bauen des Container Image (siehe oben) werden die Unit Tests im Container über `make test` ausgeführt.

### Spider testweise ausführen (Debugging)

Der Spider kann einzelne URLs verarbeiten, ohne die Ergebnisse in eine Datenbank zu schreiben.
Am einfachsten geht das über den `make dryrun` Befehl, so:

```nohighlight
make dryrun ARGS="http://www.example.com/"
```

### Warteschlange und Worker

Für einen kompletten Durchlauf wird die Warteschlange gefüllt und dann abgearbeitet. Das passiert im Betrieb über das Script [devops/run-job.sh](https://github.com/netzbegruenung/green-spider/blob/main/devops/run-job.sh).

Lokal kann das über die folgenden Befehle getestet werden:

```nohighlight
make jobs
make spider
```

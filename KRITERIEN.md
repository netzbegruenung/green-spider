# Qualitätskriterien

Wir prüfen Sites nach den folgenden Kriterien:

- `DNS_RESOLVABLE_IPV4`: Der Hostname der URL ist in eine IPv4 Adresse auflösbar

- `SITE_REACHABLE`: Die Site ist per HTTP(S) erreichbar (Status-Code 200)

- `HTTPS`: Die Site ist über HTTPS erreichbar. Das Server-Zertifikat ist gültig und stammt von einer vertrauenswürdigen CA.

- `WWW_OPTIONAL`: Die Verwendung von `www.` zu Beginn der Startseiten-URL ist optional. Die Site ist sowohl mit als auch ohne dieses Präfix im Hostnamen erreichbar.

- `CANONICAL_URL`: Bei mehreren möglichen URLs, über die auf die Site zugegriffen werden kann, wird auf eine kanonische URL weiter geleitet bzw. per `rel=canonical` Link verwiesen.

- `FAVICON`: Die Site hat ein Favoriten-Icon.

- `FEEDS`: Die Site verweist auf RSS oder Atom Feeds via `rel=alternate` Link Tag.

- `HTTP_RESPONSE_DURATION`: Zeit, die vom Absenden des HTTP-Request bis zum Empfang der Response-Header vergangen ist.

- `RESPONSIVE`: Die Seite besitzt ein `viewport` Meta-Tag und die Breite der Inhalte passt sich an verschiedene Fenster- bzw. Gerätegrößen an.

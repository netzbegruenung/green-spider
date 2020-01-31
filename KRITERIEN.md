# Qualitätskriterien

Wir prüfen Sites nach den folgenden Kriterien:

- `DNS_RESOLVABLE_IPV4`: Der Hostname der URL ist in eine IPv4 Adresse auflösbar

- `SITE_REACHABLE`: Die Site ist per HTTP(S) erreichbar (Status-Code 200)

- `CANONICAL_URL`: Bei mehreren möglichen URLs, über die auf die Site zugegriffen werden kann, wird auf eine kanonische URL weiter geleitet bzw. per `rel=canonical` Link verwiesen.

- `HTTPS`: Die Site ist über HTTPS erreichbar. Das Server-Zertifikat ist gültig und stammt von einer vertrauenswürdigen CA.

- `WWW_OPTIONAL`: Die Verwendung von `www.` zu Beginn der Startseiten-URL ist optional. Die Site ist sowohl mit als auch ohne dieses Präfix im Hostnamen erreichbar.

- `FAVICON`: Die Site hat ein Favoriten-Icon.

- `RESPONSIVE`: Die Seite besitzt ein `viewport` Meta-Tag und die Breite der Inhalte passt sich an verschiedene Fenster- bzw. Gerätegrößen an.

- `SOCIAL_MEDIA_LINKS`: Die Site verlinkt auf Social Media Profile

- `CONTACT_LINK`: Die Site hat einen Link "Kontakt"

- `USE_SPECIFIC_FONTS`: Die Site verwendet die Schriftart Arvo

- `FEEDS`: Die Site verweist auf RSS oder Atom Feeds via `rel=alternate` Link Tag.

- `NO_THIRD_PARTY_COOKIES`: Es werden keine Third Party Cookies gesetzt

- `NO_SCRIPT_ERRORS`: Es wurden keine JavaScript-Fehler festgestellt

- `NO_NETWORK_ERRORS`: Es wurden keine Probleme beim Laden verknüpfter Ressourcen festgestellt

- `HTTP_RESPONSE_DURATION`: Zeit, die vom Absenden des HTTP-Request bis zum Empfang der Response-Header vergangen ist.

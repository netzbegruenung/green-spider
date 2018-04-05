# green-spider

Collects data on green websites and checks for things like SEO, performance, TLS.

Written and tested in Python3

Results published at https://netzbegruenung.github.io/green-spider/

### Usage

Run the spider:

```nohighlight
make spider
```

The result will be in `webapp/dist/data`.

Build the webapp:

```nohighlight
make webapp
```

### Ideas

- If the URL does not start with `www.`, will entering `www.<url>` also work?
- If the URL is HTTP, is it possible to access the site via HTTPS (recommended)?
- If the URL is HTTPS, is it possible to access the sire via HTTP (recommended: redirect to HTTPS)
- Check which cookies are set and with what settings (expiry, domain)
- submit the URL against a service like Google Page Speed and retrieve the score
- Check against our own webpagetest.org instance
- Detect which one of the well-known CMS is used
- Certificate expiry warning
- Favourite icon availability check

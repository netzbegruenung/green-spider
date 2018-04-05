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

- Check which cookies are set and with what settings (expiry, domain)
- submit the URL against a service like Google Page Speed and retrieve the score (see https://github.com/addyosmani/psi/)
- Check against our own webpagetest.org instance
- Detect which one of the well-known CMS is used
- Warn in case a certificate will expire soon
- Favourite icon availability check

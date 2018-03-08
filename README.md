# Automated Scraper

This is a bot setup that utilizes google's puppeteer to provide a framework for easy scraping of websites that require user interaction.

### Setup

Setup is simple, write scripts you need and save them in the `/scripts` folder, then run them with node from the root folder.

Scripts are meant to be run as below, but may be modified:

```bash
node scripts/repl.js example.config.json
```

You may find you need to extend `scraper.js` and `scraping_utility.js` to meet your needs.

### Chrome

You will need an instance of chrome running with certain parameters enabled:
```
chrome --remote-debugging-port=9222 [ --headless --disable-gpu --proxy-server=127.0.0.1 ]
```

Most servers will require headless and disable-gpu, if you're running a proxy make sure you've enabled access from the server you're running on and add the proxy-server parameter. The remote-debugging-port parameter is required, the port can be anything (typically above 3000).
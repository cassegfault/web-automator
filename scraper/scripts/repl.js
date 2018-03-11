const { Scraper, ScrapingUtility } = require('../scraper');
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

/*
    This is a simple REPL for use with the automated scraper.
    Once in the repl, any commands can be run in the same context as the callback

    This can be very useful when writing and debugging new scripts

    Here are some example commands for use in the repl:
    scraper.go_to('http://google.com')
    scraper.page.screenshot({ path: 'image.jpg' })
    scraper.page.url
*/

const scraper = new Scraper(process.argv[2], async function(scraper) {
    function rep() {
        rl.question('ready for input\n', (res) => {
            try {
                console.log(eval(res));
            } catch (e) {
                console.log(e);
            }

            if (res != '.quit') {
                rep();
            } else {
                scraper.quit();
            }
        });
    }
    rep();
    return Promise.resolve();
}, true);
(async() => {
    await scraper.run();
})();
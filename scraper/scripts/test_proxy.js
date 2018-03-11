const fs = require('fs');
const { Scraper, ScrapingUtility } = require('../scraper');
 
/*
	This is a script to verify the chrome proxy setup is working
*/
const scraper = new Scraper(process.argv[2], async function(scraper) {
    await scraper.go_to('http://bot.whatismyipaddress.com/');

    var result = await scraper.page.evaluate(function(){ return Promise.resolve(document.body.innerText); });
    scraper.log(result);
    return Promise.resolve();
});
(async() => {
    await scraper.run();
})();

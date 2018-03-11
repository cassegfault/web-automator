const puppeteer = require('puppeteer');
const fs = require('fs');
const http = require('http');
const { generateFilename, random, sleep, extend } = require('./utils');
const { ScrapingUtility } = require('./scraping_utility')


exports.ScrapingUtility = ScrapingUtility;

exports.Scraper = class {
    /**
        Usage:
            const autoscraper = new Scraper(async function(){
                // Do Stuff...

                // Output the result
                fs.writeFileSync('/dev/stdout',JSON.stringify(await autoscraper.build_result()));
            });
            await autoscraper.run();
    **/
    constructor(config_filename, callback, dont_quit = false) {
        if (typeof config_filename != "string" && !callback) {
            callback = config_filename;
        }
        this.callback = callback;
        this.CONIFG_FILE = config_filename || 'config.json';
        this.config = {};
        this.logs = [];
        this.has_quit = false;
        this.is_logged_in = false;
        this.dont_quit_after_callback = dont_quit;

        // Gracefully handle interrupts
        process.on('SIGINT', () => { this.quit(); });

        /* 
            This is called when there is an issue with the script running the scraper has a syntax error
            or does not properly handle promises. For the stacktrace check {botname}.err.log
        */
        process.on('unhandledRejection', (err) => {
            console.error(err);
            this.quit('Scripting Error');
        });
    }

    save_config() {
        var config_json = JSON.stringify(this.config);
        fs.writeFileSync(this.CONIFG_FILE, config_json);
    }

    /*
        This provides easy access to the sleep function for the
        scripts utilizing the scraper via this.sleep
    */
    async sleep(...args) {
        return sleep(...args);
    }

    /*
        This should be run after the page is created so we can load in cookies
    */
    async load_config() {
        var data = fs.readFileSync(this.CONIFG_FILE),
            config = {};
        try {
            config = JSON.parse(data);
        } catch (e) {
            this.quit('Error parsing config data');
        }

        this.config = config;
    }


    async get_endpoint() {
        return new Promise((resolve, reject) => {
            /*
                The default for chrome is 9222, but it is an option for when that port is disabled and
                when custom chrome setups are required (like proxies)
            */
            http.get(this.config['chrome_location'] || "http://localhost:9222/json/version", function(resp) {
                let data = '';
                resp.on('data', str => { data += str; });
                resp.on('end', () => {
                    let obj = JSON.parse(data);
                    resolve(obj["webSocketDebuggerUrl"]);
                });
            });
        });
    }

    /*
        It'd be awesome if we could do this stuff in the constructor, but much of it is asynchronous.
        This adds event handlers for logging and error checking navigation,
        sets up the emulated device, runs the main program set by the constructor,
        and properly exits
    */
    async run() {
        await this.load_config();

        /*
            Chrome can either be instantiated or connected to,
            it's easier when running chrome visually to just launch it here.
            When running headlessly, we need to grab the remote control endpoint
        */
        if (this.config['run_visual']) {

            this.browser = await puppeteer.launch({
                ignoreHTTPSErrors: true,
                headless: false
            });

        } else {

            let endpoint = await this.get_endpoint();

            if (!endpoint) {
                this.quit("Could not connect to chrome headless!");
            }

            this.browser = await puppeteer.connect({
                ignoreHTTPSErrors: true,
                browserWSEndpoint: endpoint
            });
        }

        // In the future I'd like to be able to load back pages already running
        this.page = await this.browser.newPage();

        // For persisting sessions and such
        if (this.config.hasOwnProperty('cookies')) {
            await this.page.setCookie(...this.config.cookies);
        }

        // Block video and audio requests
        await this.page.setRequestInterception(true);
        this.page.on('request', function(request) {
            if (request.resourceType === 'media') {
                request.abort();
            } else {
                request.continue();
            }
        });

        this.page.on('response', response => {
            const status = response.status;
            if ((status >= 300) && (status <= 399)) {
                // Not always necessary, but sometimes good to know
                this.log(`Redirect from ${response.url} to ${response.headers['location']}`, 'navigation')
            }
        });

        /* Log every navigation change, store the current set of cookies */
        this.page.on('framenavigated', async function frameNavigated(frame) {
            this.log(frame.url(), 'navigation');
            this.config.cookies = await this.page.cookies(this.page.url());
            /*
                This is also a good spot to catch captchas and that sort of thing
            */
            return Promise.resolve();
        }.bind(this));

        /* This is designed to look like a chrome window running on a mac */
        await this.page.emulate({
            'name': 'Browser',
            'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
            'viewport': {
                'width': 1413,
                'height': 967,
                'deviceScaleFactor': 1,
                'isMobile': false,
                'hasTouch': false,
                'isLandscape': true
            }
        });

        /* Run the user script, catch any exceptions */
        await this.safe_execute(async function callbackRunner() {
            await this.callback(this);
        }, this);

        /*
            In most cases it is desirable for a script to exit after the callback,
            however some asynchronous scripts such as a REPL or those using websockets
            may want to leave the process running until a different method of exit
        */
        if (!this.dont_quit_after_callback) {
            this.quit();
        }
        return Promise.resolve();
    }

    /* 
        These get stored until getting dumped at the end with the result
        'debug' logs are not stored unless the debug flag is set in the config
    */
    log(data, type = 'info') {
        if (type === 'debug' && !this.config.debug)
            return;

        this.logs.push({
            type: type,
            data: data,
            timestamp: Math.round(Date.now() / 1000)
        });
    }

    /* What gets printed at the end of the run */
    build_result() {
        /*
            The idea is for the script to build up everything it scrapes
            to a property which will be output with the data here
        */
        return {
            output: {
                /*
                    'notifications': this.notifications,
                    'messages': this.messages
                */
            },
            logs: this.logs
        };
    }

    /* Abstracted navigation handling */
    async go_to(url, options = {}) {
        options = extend({}, options);
        try {
            await this.page.goto(url, options);
            await sleep(1000, 3000); 
            // waiting for JS to do its thing as waitUntil doesn't seem to work (as of 0.13)
            this.log(`Expected: ${url}, Current: ${this.page.url()}`, 'info');
            return Promise.resolve();
        } catch (e) {
            this.log(`Error while navigating: ${JSON.stringify(e)}`, 'error');
            return Promise.reject();
        }
    }

    async click(selector) {
        try {
            await this.page.waitForSelector(selector);
        } catch (e) {
            this.log(`Click Selector Not Found: ${selector}`, 'info');
            this.quit(`Broken click selector sent: ${selector}`);
            return Promise.resolve();
        }
        await this.page.click(selector, { delay: 45 });
        return Promise.resolve();
    }

    /*
        Certain css3 selectors do not work with the basic click on puppeteer
        in these cases we must send the page code to click them
    */
    async css3_click(selector) {
        try {
            await this.page.evaluate(async(selector) => {
                try {
                    var el = document.querySelector(selector);
                    if (el) {
                        el.click();
                    } else {
                        return Promise.reject();
                    }
                } catch (e) {
                    return Promise.reject();
                }

                return Promise.resolve();
            }, selector);
        } catch (e) {
            this.log(`Special Click Selector Not Found: ${selector}`, 'info');
            this.quit(`Broken Special click selector sent: ${selector}`);
            return Promise.resolve();
        }
    }

    async type(selector, text) {
        // Puppeteer behaves this way, best to keep it the same
        if (!text) {
            text = selector;
            selector = null
        }

        var options = { delay: random(270, 400) };
        /*
            If we have an element to type in, we can make sure to type in it 
            directly, otherwise assume we are focused and just type
        */
        if (selector) {
            try {
                await this.page.waitForSelector(selector);
            } catch (e) {
                this.quit(`Broken type selector sent: ${selector}`);
                return Promise.resolve();
            }
            await this.page.type(selector, text, options)
        } else {
            await this.page.keyboard.type(text, options);
        }
        return Promise.resolve();
    }

    /* 
        Catch errors and throw them in the logs rather than stopping the program entirely
    */
    async safe_execute(func, thisObject) {
        try {
            if (thisObject) {
                await func.bind(thisObject)();
            } else {
                await func();
            }
        } catch (e) {
            this.log(`Error while executing function: ${func.name} - ${JSON.stringify(e)}`, 'error');
        }
    }

    /* 
        Login function, in this case for Github
    */
    async log_in(try_again = true) {
        const EMAIL_FIELD = "#login_field",
            PASSWORD_FIELD = "#password";
        try {
            this.log('Going to login page', 'debug');
            await this.go_to('https://github.com/login');
            try {
                await this.page.waitForSelector(EMAIL_FIELD);
                await this.page.waitForSelector(PASSWORD_FIELD);
            } catch (e) {
                // This can happen when we have logged in previously and saved the cookies
                this.log('No login fields were found, assuming we are logged in', 'info');
                this.is_logged_in = true;
                return Promise.resolve();
            }

            this.log('typing credentials', 'debug');
            // Send the user/pass to log in
            try {
                await this.type(EMAIL_FIELD, this.config.github_email, { delay: 100 });
                await sleep(150, 300);
                await this.type(PASSWORD_FIELD, this.config.github_password, { delay: 100 });
            } catch (e) {
                this.quit(`Error typing in credentials: ${e}`);
            }

            // The login button requires a bit more specificity
            await this.page.click(".auth-form-body input.btn-primary");
            // Sleeps can be good for waiting for navigation or SPA actions
            await sleep(1500, 3000);

            this.is_logged_in = true;
            return Promise.resolve();
        } catch (e) {
            if (try_again && this.config.hasOwnProperty('cookies')) {
                /*
                    This is a safety precaution for sites that redirect or behave undesirably
                    when certain cookies are encountered
                */
                this.page.deleteCookie(...this.config.cookies);
                this.log('attempting login with blank cookies', 'info');
                this.config.cookies = [];
                log_in(false);
            }
        }
    }


    /* 
        Primarily for debug purposes, dumps logs out into a file
    */
    dump_logs() {
        const filename = generateFilename('logs', '.json');
        fs.writeFileSync(filename, JSON.stringify(this.logs));
    }

    /*
        Dumps the result into stdout, shuts down chrome, kills the process as a safety precaution
    */
    quit(sendError) {
        sendError = sendError || false;

        // This is a precaution to not return twice
        if (this.has_quit)
            return;

        if (sendError)
            this.log(sendError, 'error');

        const output = this.build_result();
        if (sendError) {
            output.error = sendError;
        } else {
            // if we've encountered an error, we don't want to save the changes to the configuration file
            this.save_config(this.config);
        }

        this.has_quit = true;

        // print the results (to be handled by a subprocess or saved via a pipe)
        process.stdout.write(JSON.stringify(output), () => {
            if (this.config.debug) {
                // Debug mode also dumps to a file (in case you forget to pipe)
                this.dump_logs();
            }
            if (this.page) {
                // Kill the page so chrome doesn't eat massive amounts of resources
                this.page.close();
            }
            process.exit(sendError ? 1 : null);
        });
    }
}
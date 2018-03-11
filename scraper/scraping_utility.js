/*
    This is a separate file to contain the functions that are meant to be
    run in the page context and potentially used by many scripts / functions

    The functions here are extremely simple, but scraping functions can become very
    complex and return values through the promise
*/
module.exports.ScrapingUtility = {
    view_notifications: function(){
        var el = document.querySelector("#user-links a.notification-indicator");
        if(el)
            el.click();
        return Promise.resolve();
    },

    click_logo: function(){
        var el = document.querySelector(".header-logo-invertocat");
        if(el)
            el.click();
        return Promise.resolve();
    },

    profile_info: function(){
        // Grab any elements to scrape
        var name_el = document.querySelector('.vcard-fullname'),
            handle_el = document.querySelector('.vcard-username'),
            org_el = document.querySelector('.vcard-detail .p-org');

        /* 
            Return the values of each of the elements
            Writing safe code is very important here as if anything throws an error
            you will get nothing back and the promise will fail
        */
        return Promise.resolve({
            'name': name_el && name_el.innerText,
            'handle': handle_el && handle_el.innerText,
            'company': org_el && org_el.innerText
        });
    }
};
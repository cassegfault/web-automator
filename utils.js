/*
    This is similar to any download function, adds an iterator to
    the filename to avoid filename overlap
*/
export function generateFilename (filename,extension) {
    var iterator = 0,
        fileNameDoesExist = fs.existsSync(`${filename}${extension}`);
    extension = extension || '.json';
    while (fileNameDoesExist) {
        iterator++;
        var testFilename = `${filename}-${iterator}`;
        fileNameDoesExist = fs.existsSync(`${testFilename}${extension}`);
        if (!fileNameDoesExist) {
            filename = testFilename;
        }
    }

    return `${filename}${extension}`;
}

/**
    Helper Functions
**/
function sleep(ms, rand_to) {
    if (rand_to)
        ms = random(ms,rand_to)
    return new Promise(resolve => setTimeout(resolve, ms));
}

function random(from, to) {
    from = from || 0;
    to = to || 6;
    return Math.floor(Math.random() * to) + from;
}


// Similar to the funciton popularized by jQuery
function extend() {
    for(var i=1; i<arguments.length; i++){
        for(var key in arguments[i]){
            if(arguments[i].hasOwnProperty(key)){
                arguments[0][key] = arguments[i][key];
            }
        }
    }
    return arguments[0];
}
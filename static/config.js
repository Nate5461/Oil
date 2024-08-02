// config.js
const config = {
    minDate: '1993-06-25',
    maxDate: '2015-12-11',
    spreadMargin: 0.075,
    contractMargin: 0.25,
    depositDelay: 3,
    capitalReserve: 0.1,
    marginWarning: 0.1
};

// Function to load config from local storage or use default
function loadConfig() {
    const storedConfig = localStorage.getItem('config');
    if (storedConfig) {
        return JSON.parse(storedConfig);
    }
    return config;
}

// Function to save config to local storage
function saveConfig(newConfig) {
    localStorage.setItem('config', JSON.stringify(newConfig));
}
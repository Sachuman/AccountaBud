const RECORD_INTERVAL_MIN = 0.5;   // 30 seconds
const REPORT_INTERVAL_MIN = 1;     // 1 minutes

const TIMES_KEY = 'activeTimes';

// On install/startup, schedule our 30-second alarm
chrome.runtime.onInstalled.addListener(init);
chrome.runtime.onStartup.addListener(init);

function init() {
    // Record every 30 s
    chrome.alarms.create('recordActiveTime', {
        periodInMinutes: RECORD_INTERVAL_MIN
    });
    // Report every 5 min
    chrome.alarms.create('sendUsage', {
        periodInMinutes: REPORT_INTERVAL_MIN
    });
    chrome.storage.local.set({ [TIMES_KEY]: {} });
}

chrome.alarms.onAlarm.addListener(async alarm => {
    if (alarm.name === 'recordActiveTime') recordActiveTime();
    else if (alarm.name === 'sendUsage') sendUsageReport();
});

async function recordActiveTime() {
    console.log('Recording active time...');
    const [tab] = await chrome.tabs.query({
        active: true,
        lastFocusedWindow: true
    });
    if (!tab?.url) return;

    let domain;
    try {
        domain = new URL(tab.url).hostname;
    } catch {
        return; // skip invalid URLs
    }

    const times = await getTimes();
    times[domain] = (times[domain] || 0) + (RECORD_INTERVAL_MIN * 60);
    await chrome.storage.local.set({ [TIMES_KEY]: times });
}

async function sendUsageReport() {
    const times = await getTimes();
    if (times.length === 0) return;

    const date = new Date().toLocaleDateString();
    const email = (await chrome.identity.getProfileUserInfo()).email;
    const records = Object.entries(times).map(
        ([domain, active_sec]) => ({ date, email, domain, active_sec })
    );

    console.log('Sending usage alert...', records);

    await fetch('http://localhost:8000/browser-usage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(records)
    });

}

async function getTimes() {
    const data = await chrome.storage.local.get(TIMES_KEY);
    const times = data[TIMES_KEY] || {};
    return times;
}

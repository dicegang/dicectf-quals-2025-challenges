#!/usr/bin/env node
// admin bot simulator
// run: docker run -i --init --rm ghcr.io/puppeteer/puppeteer:latest node -e "$(cat adminbot.js)" "" "$(cat flag.txt)" "https://your-url-here"
import puppeteer from 'puppeteer';

const browser = await puppeteer.launch({
    pipe: true,
    args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--js-flags=--jitless',
        '--incognito'
    ],
    //dumpio: true,
    headless: 'new'
});

const [flag, url] = process.argv.slice(2);

if (!url.startsWith('http://') && !url.startsWith('https://')) {
    console.error('Invalid URL');
    process.exit(1);
}

try {
    const page = await browser.newPage();
    await page.goto('https://safestnote.dicec.tf/');
    await page.waitForSelector('input[name="note"]');
    await page.type('input[name="note"]', flag);
    await page.click('input[type="submit"]');
    await new Promise(res => setTimeout(res, 1000));
    console.log(`visiting ${url}`);
    await page.goto(url);
    await new Promise(res => setTimeout(res, 10000));
    await page.close();
} catch (e) {
    console.error(e);
};

await browser.close();
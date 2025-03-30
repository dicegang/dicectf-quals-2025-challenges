import flag from './flag.txt';

function sleep(time) {
  return new Promise(resolve => {
    setTimeout(resolve, time)
  })
}

export default {
  name: 'safestnote admin bot',
  timeout: 15_000,
  handler: async (url, ctx) => {
    const page = await ctx.newPage();
    await page.goto('https://safestnote.dicec.tf/', { timeout: 5000, waitUntil: 'domcontentloaded' });
    await page.waitForSelector('input[name="note"]');
    await page.type('input[name="note"]', flag);
    await page.click('input[type="submit"]');
    await sleep(1000);
    await page.goto(url, { timeout: 5000, waitUntil: 'domcontentloaded' });
    await sleep(10000);
  }
}
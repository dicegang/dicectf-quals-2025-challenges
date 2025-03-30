import flag from './flag.txt';

function sleep(time) {
  return new Promise(resolve => {
    setTimeout(resolve, time)
  })
}

export default {
  name: 'bcu admin bot',
  timeout: 15_000,
  handler: async (url, ctx) => {
    await ctx.setCookie({
      name: "flag",
      value: flag,
      httpOnly: false,
      secure: true,
      sameSite: "Lax",
      domain: "bcu.dicec.tf",
      path: "/",
    })
    const page = await ctx.newPage();
    await page.goto(url, { timeout: 5000, waitUntil: 'domcontentloaded' });
    await sleep(10000);
  }
}

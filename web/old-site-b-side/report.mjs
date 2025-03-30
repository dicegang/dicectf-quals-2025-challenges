import { sealData } from "iron-session"
import puppeteer from "puppeteer"

import { SESSION_PASSWORD } from "@/users.mjs"

const sleep = ms => new Promise(r => setTimeout(r, ms))

export async function visit(url) {
  let browser
  try {
    browser = await puppeteer.launch({
      pipe: true,
      dumpio: true,
      headless: "new",
      args: ["--js-flags=--noexpose_wasm,--jitless", "--no-sandbox"],
    })
    
    const context = await browser.createBrowserContext()
    await context.setCookie({
      name: "session",
      value: await sealData({ name: "admin" }, { password: SESSION_PASSWORD, ttl: 10 }),
      httpOnly: true,
      secure: true,
      sameSite: "Lax",
      domain: "localhost",
      path: "/",
    })

    const page = await context.newPage()
    await page.goto(url, { timeout: 3000, waitUntil: "domcontentloaded" })
    await sleep(3000)
  
    await browser.close()
    browser = null
  } catch (err) {
    console.log(err)
  } finally {
    if (browser) await browser.close()
  }
}

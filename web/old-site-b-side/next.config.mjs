/** @type {import('next').NextConfig} */
export default {
  reactStrictMode: true,
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: `
              default-src 'none';
              script-src 'none';
              script-src-elem 'sha256-w9vLPbknkHXU0PY1At/IHHdfXLMMOZrbGyc2CpajOSU=';
              style-src 'none';
              style-src-attr 'unsafe-hashes' 'sha256-CH72YuKr0tyLNPzLF7Cv8fm6VzXQRI4klsDNHNZlfQw=' 'sha256-E4pemp/PNLS1erNI4P4iTqoxIS53DEAC9FNagTvBqt8=' 'sha256-CA/eh4+2R0J7cEQ14gBMtx834RIOjzMUqCM+evtrkp4=' 'sha256-/8OYnPaegsrQ1UnDZISUhWTMuVGidXurAhrhnM/WfkU=' 'sha256-e+Z0n8P0IwqIce2RMye3/p5TaNb2k/QdJT4urKCsrwk=' 'sha256-KpSV7LuPYEu58+3u9LJr9v5Drm0uIKEv0h3u/+NVNm8=' 'sha256-nKF2XuR2Pq9Go/SZcVF04Lgn++L3raImP3nbrOYUL6E=';
              img-src 'self';
              font-src 'none';
              object-src 'none';
              base-uri 'self';
              form-action 'self';
              frame-src 'self';
              frame-ancestors 'self';
              media-src http://assets.burturt.com/cursedctf-2023-music-keygen-boosted-lowbitrate.mp3;
              require-trusted-types-for 'script';
              trusted-types 'none';
            `.replaceAll(/\s+/g, " "),
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          }
        ],
      },
    ]
  },
  async redirects() {
    return [{ source: "/", destination: "/index.html", permanent: true }]
  }
}

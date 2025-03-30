FROM oven/bun AS app
RUN apt-get update && apt-get install -y build-essential

FROM pwn.red/jail
COPY --from=app / /srv
COPY challenge/challenge.js /srv/app/run
COPY challenge/gleam /srv/app/gleam
COPY challenge/gleam.mjs /srv/app/gleam.mjs
COPY challenge/package.json /srv/app/package.json
COPY flag.txt /srv/app/flag.txt

ENV JAIL_MEM=0 JAIL_PIDS=100 JAIL_ENV_PATH="/usr/local/bin:$PATH"

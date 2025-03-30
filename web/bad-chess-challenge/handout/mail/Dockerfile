FROM oven/bun:alpine
RUN apk add --no-cache openssl
WORKDIR /opt
COPY package.json ./
RUN bun install
COPY smtp-server ./smtp-server
RUN cd smtp-server && bun install
COPY server.ts cert.ts ./
RUN openssl genrsa -out priv.pem 2048
RUN openssl req -x509 -new -nodes -key priv.pem -sha256 -days 365 -out ca.pem -subj '/CN=DiceGang CA/C=US/ST=NY/L=New York/O=bad-chess-challenge'
CMD ["bun", "run", "server.ts"]
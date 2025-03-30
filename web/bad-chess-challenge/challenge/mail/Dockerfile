FROM oven/bun:alpine
RUN apk add --no-cache openssl
WORKDIR /opt
COPY package.json ./
RUN bun install
COPY smtp-server ./smtp-server
RUN cd smtp-server && bun install
COPY server.ts cert.ts ./
COPY ca.pem priv.pem ./
CMD ["bun", "run", "server.ts"]
FROM node:20.18

COPY index.js package.json package-lock.json /app/
WORKDIR /app

RUN npm install
CMD ["node", "index.js"]

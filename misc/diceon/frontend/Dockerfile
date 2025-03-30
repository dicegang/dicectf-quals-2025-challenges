FROM node:14-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

RUN npm run build

# Install serve to run the application
RUN npm install -g serve

EXPOSE 80

CMD ["serve", "-s", "build", "-l", "80"] 
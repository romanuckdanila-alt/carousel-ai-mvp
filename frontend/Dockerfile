FROM node:20-alpine

WORKDIR /app

COPY package.json /app/package.json
RUN npm install

COPY . /app
RUN npm run build

CMD ["sh", "-c", "NITRO_HOST=0.0.0.0 NITRO_PORT=3000 npm run start"]

FROM node:24.16.0-trixie-slim AS base

WORKDIR /app

CMD ["npm", "run", "start"]

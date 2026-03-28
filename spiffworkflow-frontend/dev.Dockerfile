FROM node:22.22.2-bookworm-slim AS base

WORKDIR /app

CMD ["npm", "run", "start"]

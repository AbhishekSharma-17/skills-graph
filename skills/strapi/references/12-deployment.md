# Strapi — Deployment

> Source: https://docs.strapi.io/cms/deployment

## Production Build Process

### Build & Start

```bash
# Build the admin panel
NODE_ENV=production npm run build

# Start the production server
NODE_ENV=production npm start
```

Never use `npm run develop` in production — it enables hot-reloading, the Content-Type Builder, and the GraphQL playground.

### Hardware Requirements

| Resource | Recommended | Minimum |
|----------|-------------|---------|
| CPU | 2+ cores | 1 core |
| RAM | 4 GB+ | 2 GB |
| Storage | 32 GB+ | 8 GB |

## Environment Variables

### Essential Production Variables

```bash
# .env.production
NODE_ENV=production
HOST=0.0.0.0
PORT=1337
PUBLIC_URL=https://api.myapp.com

# Security keys (generate unique values)
APP_KEYS=key1,key2,key3,key4
API_TOKEN_SALT=<random-string>
ADMIN_JWT_SECRET=<random-string>
JWT_SECRET=<random-string>
TRANSFER_TOKEN_SALT=<random-string>

# Database (PostgreSQL recommended for production)
DATABASE_CLIENT=postgres
DATABASE_HOST=db.example.com
DATABASE_PORT=5432
DATABASE_NAME=strapi_production
DATABASE_USERNAME=strapi
DATABASE_PASSWORD=<secure-password>
DATABASE_SSL=true
```

### Generating Secure Keys

```bash
# Generate random keys
openssl rand -base64 32
# or
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

## Database Selection

SQLite is fine for development but **not recommended for production**. Use PostgreSQL (preferred) or MySQL.

### PostgreSQL Production Config

```javascript
// config/env/production/database.js
module.exports = ({ env }) => ({
  connection: {
    client: 'postgres',
    connection: {
      connectionString: env('DATABASE_URL'),
      ssl: {
        rejectUnauthorized: env.bool('DATABASE_SSL_REJECT', true),
      },
    },
    pool: {
      min: 2,
      max: 20,
    },
  },
});
```

## Process Management with PM2

### Install PM2

```bash
npm install pm2 -g
```

### Ecosystem File

```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'strapi',
      cwd: '/home/app/strapi',
      script: 'npm',
      args: 'start',
      env: {
        NODE_ENV: 'production',
      },
      instances: 1,           // Strapi doesn't support clustering
      exec_mode: 'fork',
      autorestart: true,
      max_memory_restart: '1G',
    },
  ],
};
```

### PM2 Commands

```bash
pm2 start ecosystem.config.js
pm2 status
pm2 logs strapi
pm2 restart strapi
pm2 stop strapi
pm2 save      # persist across reboots
pm2 startup   # auto-start on system boot
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app
COPY --from=build /app ./
ENV NODE_ENV=production
EXPOSE 1337
CMD ["npm", "start"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  strapi:
    build: .
    ports:
      - '1337:1337'
    environment:
      NODE_ENV: production
      DATABASE_CLIENT: postgres
      DATABASE_HOST: postgres
      DATABASE_PORT: 5432
      DATABASE_NAME: strapi
      DATABASE_USERNAME: strapi
      DATABASE_PASSWORD: ${DATABASE_PASSWORD}
    depends_on:
      - postgres
    volumes:
      - strapi-uploads:/app/public/uploads

  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: strapi
      POSTGRES_USER: strapi
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  strapi-uploads:
  postgres-data:
```

### Docker Pool Settings

Set pool min to 0 for container environments:

```javascript
pool: { min: 0, max: 10 }
```

## Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name api.myapp.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.myapp.com;

    ssl_certificate /etc/letsencrypt/live/api.myapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.myapp.com/privkey.pem;

    client_max_body_size 250M;

    location / {
        proxy_pass http://127.0.0.1:1337;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Server $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_pass_request_headers on;
    }
}
```

Enable proxy in Strapi:

```javascript
// config/env/production/server.js
module.exports = ({ env }) => ({
  url: env('PUBLIC_URL', 'https://api.myapp.com'),
  proxy: { enabled: true },
});
```

## Health Check

Strapi exposes a health endpoint:

```bash
GET /_health
# Returns HTTP 204 when the server is ready
```

Use this for Kubernetes readiness/liveness probes, load balancer health checks, and monitoring.

## Cloud Hosting Options

### Strapi Cloud

Official managed hosting platform:

```bash
# Deploy from a GitHub repository
# Configure at https://cloud.strapi.io
```

### Other Supported Platforms

| Platform | Notes |
|----------|-------|
| AWS (EC2, ECS) | Full control, self-managed |
| DigitalOcean | App Platform or Droplets |
| Heroku | Via buildpacks |
| Azure | App Service or VMs |
| Railway | Simplified deployment |
| Render | Docker-based |

## Production Checklist

- [ ] Set `NODE_ENV=production`
- [ ] Use PostgreSQL or MySQL (not SQLite)
- [ ] Generate unique values for all security keys (APP_KEYS, JWT_SECRET, etc.)
- [ ] Set `PUBLIC_URL` to your actual domain
- [ ] Enable SSL on the database connection
- [ ] Configure a reverse proxy with SSL termination
- [ ] Use an external storage provider (S3, Cloudinary) for media files
- [ ] Set up process management (PM2 or Docker)
- [ ] Configure CORS for your frontend domain
- [ ] Set appropriate file upload size limits
- [ ] Enable rate limiting on auth endpoints
- [ ] Set up health check monitoring
- [ ] Configure database connection pooling
- [ ] Run `npm run build` before `npm start`

## Common Pitfalls

- **Never run `npm run develop` in production** — it enables the Content-Type Builder and hot-reloading
- **Strapi doesn't support Node.js clustering** — use `instances: 1` in PM2, scale via multiple containers behind a load balancer
- **SQLite in production** will cause data loss with multiple server instances and doesn't handle concurrent writes well
- **Media files on local filesystem** will be lost on container redeploy — use S3 or Cloudinary
- **`PUBLIC_URL` must match the actual serving URL** — mismatches break admin panel asset loading and file URLs
- **For Kubernetes, prefer npm over pnpm** to avoid native module compilation conflicts
- **Database secrets should never be committed** — use environment variables or secret management

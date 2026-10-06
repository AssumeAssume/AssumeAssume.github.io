# visitmap

A small, cookie-free visitor map for the website, running on Cloudflare Workers with a D1 database (both free tier).

- `assets/visits.js` on the website sends one record per page view to `POST /hit`.
- The Worker stores the time, page, external referrer host, Cloudflare's approximate location
  (country, region, city) and network owner, and only the /24 (IPv4) or /48 (IPv6) part of the IP.
  A daily cron trigger clears networks from records older than `RETENTION_DAYS` (30 days).
- `GET /` is a password-protected dashboard: map, totals, rankings and the latest visits.

## One-time setup

```sh
cd visitmap
npm install
npx wrangler login                      # authorise in the browser
npx wrangler d1 create visitmap         # copy the printed database_id into wrangler.toml
npm run db:init                         # create the table in the remote database
openssl rand -hex 32 | npx wrangler secret put IP_SALT
npx wrangler secret put DASHBOARD_PASSWORD
npm run deploy                          # prints https://visitmap.<subdomain>.workers.dev
```

Then set `"visits": {"endpoint": "https://visitmap.<subdomain>.workers.dev/hit", ...}` in
`content/profile.json` and rebuild the website. Open the Worker URL to see the dashboard
(any user name, the dashboard password).

## Everyday use

- Stop counting your own browser: open any page of the website once with `?notrack`; `?track` undoes it.
- Browsers that send Global Privacy Control or Do Not Track are not counted.
- `*.workers.dev` is blocked in mainland China. To count visitors there, add a custom domain to the
  Worker in the Cloudflare dashboard and update the endpoint in `content/profile.json`.

## Local development

```sh
printf 'DASHBOARD_PASSWORD=local-preview\nIP_SALT=local-salt\n' > .dev.vars
npm run db:init:local
npm run dev                             # http://localhost:8788
```

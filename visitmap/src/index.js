// visitmap: a small, cookie-free visitor map for a static website.
//   POST /hit         records one page view (sent by assets/visits.js on the website)
//   GET  /            private dashboard, protected by HTTP Basic auth (DASHBOARD_PASSWORD)
//   GET  /api/points  aggregated statistics for the dashboard
//   GET  /api/feed    most recent page views
// A daily cron trigger clears truncated IP networks older than RETENTION_DAYS.
import { dashboard } from './dashboard.js';

const DAY = 86400000;
const BOT = /bot|crawl|spider|slurp|headless|lighthouse|preview|facebookexternalhit|curl|wget|python|java\/|httpclient|okhttp/i;
const PRIVATE = { 'cache-control': 'no-store', 'x-robots-tag': 'noindex, nofollow', 'referrer-policy': 'no-referrer' };

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    try {
      if (url.pathname === '/hit') return await hit(request, env);
      if (request.method !== 'GET' && request.method !== 'HEAD') return text('Method not allowed', 405);
      const denied = await authorize(request, env);
      if (denied) return denied;
      const site = pickSite(url, env);
      if (!site) return text('Unknown site', 404);
      if (url.pathname === '/') {
        return new Response(dashboard(site), { headers: { 'content-type': 'text/html; charset=utf-8', ...PRIVATE } });
      }
      if (url.pathname === '/api/points') return json(await points(env, site));
      if (url.pathname === '/api/feed') return json(await feed(env, site, url.searchParams.get('limit')));
      return text('Not found', 404);
    } catch (error) {
      console.error(error);
      return text('Internal error', 500);
    }
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(expire(env));
  },
};

async function hit(request, env) {
  const origin = request.headers.get('origin') || '';
  const cors = list(env.ALLOWED_ORIGINS).includes(origin) ? { 'access-control-allow-origin': origin, vary: 'Origin' } : null;
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: { ...cors, 'access-control-allow-methods': 'POST', 'access-control-allow-headers': 'content-type', 'access-control-max-age': '86400' },
    });
  }
  if (request.method !== 'POST') return text('Method not allowed', 405);
  if (!cors) return text('Origin not allowed', 403);

  const agent = request.headers.get('user-agent') || '';
  const accepted = new Response(null, { status: 204, headers: cors });
  if (!agent || BOT.test(agent)) return accepted;

  const body = await request.text();
  if (body.length > 2048) return text('Payload too large', 413, cors);
  let data;
  try {
    data = JSON.parse(body);
  } catch {
    return text('Bad request', 400, cors);
  }
  if (!list(env.SITES).includes(data.site)) return text('Unknown site', 400, cors);

  const cf = request.cf || {};
  const address = request.headers.get('cf-connecting-ip') || '';
  const now = new Date();
  const page = typeof data.page === 'string' && data.page.startsWith('/') ? data.page.slice(0, 200) : '/';
  await env.DB.prepare(
    `INSERT INTO visits (site, ts, day, visitor, ip, org, country, region, city, lat, lon, page, referrer)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
  ).bind(
    data.site,
    now.getTime(),
    dayIn(env.TIMEZONE, now),
    await digest(`${env.IP_SALT || ''}|${data.site}|${address}|${agent}`),
    network(address),
    clip(cf.asOrganization),
    clip(cf.country, 2),
    clip(cf.region),
    clip(cf.city),
    coordinate(cf.latitude),
    coordinate(cf.longitude),
    page,
    referrerHost(data.ref, origin),
  ).run();
  return accepted;
}

async function points(env, site) {
  const today = dayIn(env.TIMEZONE, new Date());
  const days = lastDays(today, 30);
  const query = (sql, ...values) => env.DB.prepare(sql).bind(site, ...values);
  const [totals, daily, week, month, countries, networks, pages, sources, places] = await env.DB.batch([
    query(`SELECT COUNT(*) AS views, COUNT(DISTINCT visitor) AS visitors, COUNT(DISTINCT country) AS countries,
             COUNT(DISTINCT country || '/' || city) AS cities, MIN(day) AS since FROM visits WHERE site = ?`),
    query('SELECT day, COUNT(DISTINCT visitor) AS visitors FROM visits WHERE site = ? AND day >= ? GROUP BY day', days[16]),
    query('SELECT COUNT(DISTINCT visitor) AS visitors FROM visits WHERE site = ? AND day >= ?', days[23]),
    query('SELECT COUNT(DISTINCT visitor) AS visitors FROM visits WHERE site = ? AND day >= ?', days[0]),
    query(`SELECT country, COUNT(DISTINCT visitor) AS visitors FROM visits WHERE site = ? AND country IS NOT NULL
             GROUP BY country ORDER BY visitors DESC LIMIT 8`),
    query(`SELECT org, COUNT(DISTINCT visitor) AS visitors FROM visits WHERE site = ? AND org IS NOT NULL
             GROUP BY org ORDER BY visitors DESC LIMIT 8`),
    query('SELECT page, COUNT(*) AS views FROM visits WHERE site = ? GROUP BY page ORDER BY views DESC LIMIT 8'),
    query(`SELECT referrer, COUNT(*) AS views FROM visits WHERE site = ? AND referrer IS NOT NULL
             GROUP BY referrer ORDER BY views DESC LIMIT 8`),
    query(`SELECT country, region, city, AVG(lat) AS lat, AVG(lon) AS lon, COUNT(DISTINCT visitor) AS visitors
             FROM visits WHERE site = ? AND lat IS NOT NULL GROUP BY country, region, city ORDER BY visitors DESC LIMIT 1000`),
  ]);
  const byDay = Object.fromEntries(daily.results.map((row) => [row.day, row.visitors]));
  return {
    site,
    timeZone: env.TIMEZONE || 'UTC',
    totals: totals.results[0],
    recent: {
      today: byDay[days[29]] || 0,
      yesterday: byDay[days[28]] || 0,
      last7: week.results[0].visitors,
      last30: month.results[0].visitors,
      series: days.slice(16).map((day) => ({ day, visitors: byDay[day] || 0 })),
    },
    top: { countries: countries.results, networks: networks.results, pages: pages.results, sources: sources.results },
    places: places.results,
  };
}

async function feed(env, site, limit) {
  const count = Math.min(Math.max(parseInt(limit, 10) || 30, 1), 100);
  const { results } = await env.DB.prepare(
    'SELECT ts, ip, org, country, region, city, page, referrer FROM visits WHERE site = ? ORDER BY ts DESC LIMIT ?',
  ).bind(site, count).all();
  return { site, visits: results };
}

async function expire(env) {
  const cutoff = Date.now() - Number(env.RETENTION_DAYS || 365) * DAY;
  await env.DB.prepare('UPDATE visits SET ip = NULL WHERE ts < ? AND ip IS NOT NULL').bind(cutoff).run();
}

async function authorize(request, env) {
  if (!env.DASHBOARD_PASSWORD) return text('Set the DASHBOARD_PASSWORD secret first.', 503);
  const [scheme, encoded] = (request.headers.get('authorization') || '').split(' ');
  if (scheme === 'Basic' && encoded) {
    let password = '';
    try {
      const bytes = Uint8Array.from(atob(encoded), (character) => character.charCodeAt(0));
      password = new TextDecoder().decode(bytes).split(':').slice(1).join(':');
    } catch {
      // A malformed header falls through to a fresh password prompt.
    }
    if (await same(password, env.DASHBOARD_PASSWORD)) return null;
  }
  return text('Password required', 401, { 'www-authenticate': 'Basic realm="visitmap", charset="UTF-8"', ...PRIVATE });
}

// Hashing both sides first gives equal-length inputs for the constant-time comparison.
async function same(a, b) {
  const encoder = new TextEncoder();
  const [x, y] = await Promise.all([a, b].map((value) => crypto.subtle.digest('SHA-256', encoder.encode(value))));
  return crypto.subtle.timingSafeEqual(x, y);
}

async function digest(value) {
  const bytes = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)));
  return [...bytes.slice(0, 8)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

// Keep only the network part of an address: /24 for IPv4, /48 for IPv6.
function network(address) {
  const v4 = address.match(/(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.\d{1,3}$/);
  if (v4) return `${v4[1]}.${v4[2]}.${v4[3]}.*`;
  if (!address.includes(':')) return null;
  const [head, tail = ''] = address.split('::');
  const left = head ? head.split(':') : [];
  const right = tail ? tail.split(':') : [];
  const groups = [...left, ...Array(Math.max(0, 8 - left.length - right.length)).fill('0'), ...right];
  return `${groups.slice(0, 3).map((group) => parseInt(group || '0', 16).toString(16)).join(':')}:*`;
}

function referrerHost(value, origin) {
  try {
    const ref = new URL(value);
    if (!/^https?:$/.test(ref.protocol) || ref.origin === origin) return null;
    return ref.hostname.slice(0, 100);
  } catch {
    return null;
  }
}

function dayIn(timeZone, date) {
  return new Intl.DateTimeFormat('en-CA', { timeZone: timeZone || 'UTC', year: 'numeric', month: '2-digit', day: '2-digit' }).format(date);
}

// Calendar arithmetic on the date itself, so daylight-saving changes never skip or repeat a day.
function lastDays(today, count) {
  const [year, month, day] = today.split('-').map(Number);
  return Array.from({ length: count }, (_, index) => new Date(Date.UTC(year, month - 1, day - (count - 1 - index))).toISOString().slice(0, 10));
}

function coordinate(value) {
  const number = parseFloat(value);
  return Number.isFinite(number) ? Math.round(number * 1000) / 1000 : null;
}

function clip(value, length = 100) {
  return typeof value === 'string' && value ? value.slice(0, length) : null;
}

function pickSite(url, env) {
  const sites = list(env.SITES);
  const site = url.searchParams.get('site') || sites[0];
  return sites.includes(site) ? site : null;
}

function list(value) {
  return (value || '').split(',').map((item) => item.trim()).filter(Boolean);
}

function text(body, status = 200, headers = {}) {
  return new Response(body, { status, headers: { 'content-type': 'text/plain; charset=utf-8', ...headers } });
}

function json(data) {
  return new Response(JSON.stringify(data), { headers: { 'content-type': 'application/json; charset=utf-8', ...PRIVATE } });
}

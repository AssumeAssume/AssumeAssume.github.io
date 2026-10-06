// The private dashboard page. Data arrives from /api/points and /api/feed on the same origin,
// so the browser reuses the Basic auth credentials it was given for this page.
export function dashboard(site) {
  const siteJson = JSON.stringify(site).replace(/</g, '\\u003c');
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>访客地图 · ${escapeHtml(site)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css" integrity="sha384-sHL9NAb7lN7rfvG5lfHpm643Xkcjzp4jFvuavGOndn6pjVqS6ny56CAt3nsEVT4H" crossorigin="anonymous">
<style>
:root{--paper:#F6F4EE;--ink:#202722;--muted:#536057;--accent:#1B675A;--line:#d9ddd1;--soft:#e9eee5;
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--paper);color:var(--ink);font:14px/1.6 var(--sans)}
#map{position:fixed;inset:0;background:#e3e9e6}
.panel{position:fixed;z-index:1000;background:rgba(246,244,238,.97);border:1px solid var(--line);box-shadow:0 6px 24px rgba(32,39,34,.12);overflow:auto}
.stats{top:16px;right:16px;width:320px;max-height:calc(100% - 32px);padding:18px 20px}
.feed{left:16px;bottom:16px;width:400px;max-height:42%;padding:16px 18px}
h1{margin:0;font:600 15px/1.4 var(--sans)}
h2{margin:18px 0 8px;font:400 12px/1.6 var(--mono);color:var(--muted)}
.meta,.note{font:400 12px/1.7 var(--mono);color:var(--muted)}
.big{margin-top:14px;font:600 34px/1 var(--sans);color:var(--accent);font-variant-numeric:tabular-nums}
.big small{margin-left:6px;font:400 13px var(--sans);color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:14px}
.grid div{background:var(--soft);padding:8px 4px;text-align:center}
.grid b{display:block;font-size:17px;font-variant-numeric:tabular-nums}
.grid span{font-size:12px;color:var(--muted)}
.recent{display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:14px;font-size:12px;color:var(--muted)}
.recent b{color:var(--ink);font-variant-numeric:tabular-nums}
.spark{margin-top:8px}
ol{list-style:none;margin:0;padding:0}
.rank li{display:grid;grid-template-columns:minmax(0,1fr) 72px 34px;align-items:center;gap:8px;margin:4px 0;font-size:12px}
.rank .name{overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.rank .bar{height:6px;background:var(--soft)}
.rank .bar i{display:block;height:100%;background:var(--accent)}
.rank .count{text-align:right;font-variant-numeric:tabular-nums;color:var(--muted)}
.visits li{display:grid;grid-template-columns:76px minmax(0,1fr) auto;gap:10px;padding:8px 0;border-top:1px solid var(--line);font-size:12px}
.visits li:first-child{border-top:0}
.visits .when,.visits .ip{font-family:var(--mono);color:var(--muted)}
.visits .where{display:block;font-weight:600}
.visits .org,.visits .path{display:block;color:var(--muted);overflow-wrap:anywhere}
.empty{color:var(--muted);font-size:12px}
.leaflet-popup-content{font:13px/1.5 var(--sans)}
@media(max-width:760px){
  #map{position:relative;height:48vh}
  .panel{position:static;width:auto;max-height:none;margin:12px;box-shadow:none}
}
</style>
</head>
<body>
<div id="map" role="img" aria-label="访客分布地图"></div>
<aside class="panel stats">
  <h1>访客地图 · <span id="site"></span></h1>
  <div class="meta" id="since">正在读取…</div>
  <div class="big"><span id="visitors">–</span><small>位访客</small></div>
  <div class="grid">
    <div><b id="countries">–</b><span>国家/地区</span></div>
    <div><b id="cities">–</b><span>城市</span></div>
    <div><b id="views">–</b><span>次浏览</span></div>
  </div>
  <div class="recent">
    <span>今天 <b id="today">–</b></span><span>昨天 <b id="yesterday">–</b></span>
    <span>近 7 天 <b id="last7">–</b></span><span>近 30 天 <b id="last30">–</b></span>
  </div>
  <div class="spark" id="spark" title="近 14 天每日访客"></div>
  <h2>来源国家/地区</h2><ol class="rank" id="top-countries"></ol>
  <h2>所属网络/机构</h2><ol class="rank" id="top-networks"></ol>
  <h2>热门页面</h2><ol class="rank" id="top-pages"></ol>
  <h2>外部来源</h2><ol class="rank" id="top-sources"></ol>
</aside>
<aside class="panel feed">
  <h1>最近访问</h1>
  <div class="note">IP 只保留到 /24 网段 · 每 30 秒刷新</div>
  <ol class="visits" id="visits"></ol>
</aside>
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js" integrity="sha384-cxOPjt7s7Iz04uaHJceBmS+qpjv2JkIHNVcuOrM+YHwZOmJGBXI00mdUXEq65HTH" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3.1.0/dist/topojson-client.min.js" integrity="sha384-Ukv1p/xTma6P4/2bY5KzWBw+ydSpXmhCMtyciIQVDJ1RmOxtCYNMF1uXT9T63H67" crossorigin="anonymous"></script>
<script>
const SITE = ${siteJson};
const QUERY = 'site=' + encodeURIComponent(SITE);
// location.origin never carries user:password, which fetch() would refuse.
const API = location.origin + '/api/';
const regions = new Intl.DisplayNames(['zh-CN'], { type: 'region' });
const $ = (id) => document.getElementById(id);

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}
function countryName(code) {
  if (!code || code === 'XX' || code === 'T1') return '未知';
  try { return regions.of(code) || code; } catch { return code; }
}
function place(row) {
  const parts = [row.city, row.region, countryName(row.country)].filter(Boolean);
  return parts.filter((part, index) => part !== parts[index - 1]).join(', ');
}
function when(ms) {
  const seconds = (Date.now() - ms) / 1000;
  if (seconds < 60) return '刚刚';
  if (seconds < 3600) return Math.floor(seconds / 60) + ' 分钟前';
  const date = new Date(ms);
  const clock = date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false });
  return date.toDateString() === new Date().toDateString() ? clock : (date.getMonth() + 1) + '/' + date.getDate() + ' ' + clock;
}
function ranking(id, rows, label, value) {
  if (!rows.length) { $(id).innerHTML = '<li class="empty">暂无数据</li>'; return; }
  const max = Math.max(...rows.map(value), 1);
  $(id).innerHTML = rows.map((row) => '<li><span class="name" title="' + esc(label(row)) + '">' + esc(label(row)) + '</span>' +
    '<span class="bar"><i style="width:' + Math.round(value(row) / max * 100) + '%"></i></span>' +
    '<span class="count">' + value(row) + '</span></li>').join('');
}
function sparkline(series) {
  const width = 280, height = 40, max = Math.max(1, ...series.map((d) => d.visitors));
  const points = series.map((d, i) => [i / (series.length - 1) * width, height - 3 - d.visitors / max * (height - 8)]);
  const line = points.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
  return '<svg width="100%" height="' + height + '" viewBox="0 0 ' + width + ' ' + height + '" preserveAspectRatio="none" aria-hidden="true">' +
    '<path d="' + line + ' L' + width + ' ' + height + ' L0 ' + height + ' Z" fill="rgba(27,103,90,.12)"/>' +
    '<path d="' + line + '" fill="none" stroke="#1B675A" stroke-width="1.5"/></svg>';
}
function number(value) { return Number(value || 0).toLocaleString('zh-CN'); }

// Country outlines drawn from Natural Earth data: no tile service, API key or usage quota.
const map = L.map('map', { minZoom: 1, maxZoom: 7, zoomSnap: 0.5, preferCanvas: true, maxBounds: [[-75, -200], [85, 200]] }).setView([30, 10], 2);
map.attributionControl.addAttribution('Map data: Natural Earth');
map.createPane('land').style.zIndex = 350;
fetch('https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-50m.json', {
  integrity: 'sha384-Aw4s9pX1PTPntIYkZ/qV9IYiF5Gv8eTl6Dd/TT56zfO1Wwd+owFwYUuuXNUMrWkc',
}).then((response) => response.json()).then((world) => {
  L.geoJSON(topojson.feature(world, world.objects.countries), {
    pane: 'land', interactive: false,
    style: { color: '#c9cfc3', weight: 0.7, fillColor: '#fbfaf6', fillOpacity: 1 },
  }).addTo(map);
}).catch(report);
const markers = L.layerGroup().addTo(map);
let framed = false;

async function loadPoints() {
  const response = await fetch(API + 'points?' + QUERY);
  if (!response.ok) throw new Error('points ' + response.status);
  const data = await response.json();
  $('site').textContent = data.site;
  $('since').textContent = data.totals.since ? '自 ' + data.totals.since + ' 起统计 · ' + data.timeZone : '还没有访问记录';
  $('visitors').textContent = number(data.totals.visitors);
  $('countries').textContent = number(data.totals.countries);
  $('cities').textContent = number(data.totals.cities);
  $('views').textContent = number(data.totals.views);
  for (const key of ['today', 'yesterday', 'last7', 'last30']) $(key).textContent = number(data.recent[key]);
  $('spark').innerHTML = sparkline(data.recent.series);
  ranking('top-countries', data.top.countries, (r) => countryName(r.country), (r) => r.visitors);
  ranking('top-networks', data.top.networks, (r) => r.org, (r) => r.visitors);
  ranking('top-pages', data.top.pages, (r) => r.page, (r) => r.views);
  ranking('top-sources', data.top.sources, (r) => r.referrer, (r) => r.views);
  markers.clearLayers();
  for (const row of data.places) {
    L.circleMarker([row.lat, row.lon], {
      radius: Math.min(4 + 2.2 * Math.sqrt(row.visitors), 22), color: '#14514a', weight: 1, fillColor: '#1B675A', fillOpacity: 0.45,
    }).bindPopup('<b>' + esc(place(row)) + '</b><br>' + row.visitors + ' 位访客').addTo(markers);
  }
  // Frame all visitors once, keeping them clear of the floating panels on wide screens.
  if (!framed && data.places.length) {
    framed = true;
    const wide = window.innerWidth > 760;
    map.fitBounds(data.places.map((row) => [row.lat, row.lon]), {
      maxZoom: 4, paddingTopLeft: [40, 40], paddingBottomRight: wide ? [380, 220] : [40, 40],
    });
  }
}

async function loadFeed() {
  const response = await fetch(API + 'feed?limit=30&' + QUERY);
  if (!response.ok) throw new Error('feed ' + response.status);
  const { visits } = await response.json();
  $('visits').innerHTML = visits.length ? visits.map((v) => '<li><span class="when">' + esc(when(v.ts)) + '</span><div>' +
    '<span class="where">' + esc(place(v)) + '</span>' +
    (v.org ? '<span class="org">' + esc(v.org) + '</span>' : '') +
    '<span class="path">' + esc(v.page || '/') + (v.referrer ? ' ← ' + esc(v.referrer) : '') + '</span></div>' +
    '<span class="ip">' + esc(v.ip || '—') + '</span></li>').join('')
    : '<li class="empty">还没有访问记录。网站接入后，新的访问会出现在这里。</li>';
}

function report(error) {
  console.error(error);
  $('since').textContent = '数据读取失败，请刷新页面重试';
}
loadPoints().catch(report);
loadFeed().catch(report);
setInterval(() => loadFeed().catch(report), 30000);
setInterval(() => loadPoints().catch(report), 300000);
</script>
</body>
</html>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

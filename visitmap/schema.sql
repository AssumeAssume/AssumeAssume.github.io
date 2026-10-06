-- One row per page view. Location fields come from Cloudflare's request metadata;
-- `ip` keeps only the /24 (IPv4) or /48 (IPv6) network and is cleared after RETENTION_DAYS.
CREATE TABLE IF NOT EXISTS visits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  site TEXT NOT NULL,
  ts INTEGER NOT NULL,      -- milliseconds since the Unix epoch
  day TEXT NOT NULL,        -- YYYY-MM-DD in TIMEZONE
  visitor TEXT NOT NULL,    -- salted hash of IP and browser, used only to count unique visitors
  ip TEXT,
  org TEXT,                 -- network owner, e.g. a university or internet provider
  country TEXT,             -- ISO 3166-1 alpha-2 code
  region TEXT,
  city TEXT,
  lat REAL,
  lon REAL,
  page TEXT,
  referrer TEXT             -- host name of an external referring page
);

CREATE INDEX IF NOT EXISTS visits_site_ts ON visits (site, ts);
CREATE INDEX IF NOT EXISTS visits_site_day ON visits (site, day);

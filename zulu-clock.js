  // ─────────────────────────────────────────────────────────────
  //  LOADER
  // ─────────────────────────────────────────────────────────────
  (function() {
    const LOAD_MAX_MS = 20000; // hard ceiling — 20 s gives slow connections time to finish
    const done = { wx: false, news: false, sa: false };
    let triggered = false;

    // .zulu-center excluded — clock stays at full opacity and shines through as loader fades
    const POWER_ON_SELS = '.topbar, .zulu-flank, .tz-row, .rule, .wx-section, .press-section, .missions-section, .ticker';

    function triggerOut() {
      if (triggered) return;
      triggered = true;

      const loaderEl  = document.getElementById('loader');
      const loaderMsg = document.getElementById('loader-msg');
      const loaderClk = document.getElementById('loader-clock');
      const realClk   = document.getElementById('local-time');

      if (!loaderEl || !loaderClk || !realClk) { loaderEl && loaderEl.remove(); return; }

      const powerEls = [...document.querySelectorAll(POWER_ON_SELS)];

      // T=0: fade "Loading..." text
      if (loaderMsg) {
        loaderMsg.style.transition = 'opacity 0.35s';
        loaderMsg.style.opacity = '0';
      }

      // T=0: pre-hide non-clock elements (still under the solid loader — user can't see this)
      powerEls.forEach(el => { el.style.transition = 'none'; el.style.opacity = '0'; });

      // Step 1: pin loader clock at its current absolute pixel position (leave flex flow)
      const lcRect = loaderClk.getBoundingClientRect();
      loaderClk.style.position  = 'fixed';
      loaderClk.style.left      = lcRect.left + 'px';
      loaderClk.style.top       = lcRect.top  + 'px';
      loaderClk.style.transform = 'none';
      loaderClk.style.margin    = '0';

      void loaderClk.offsetWidth; // commit position as animation start-state

      // Step 2: center-to-center translation — no scale.
      // #local-time is display:block and inherits .zulu-center's full width (set by
      // the wider label text), so rRect.width >> lcRect.width. Scaling by that ratio
      // horizontally smears the loader clock. Both clocks render identical glyphs at
      // the same font-size; aligning their visual glyph-centers is all that's needed.
      const rRect = realClk.getBoundingClientRect();
      const dx = (rRect.left + rRect.width  / 2) - (lcRect.left + lcRect.width  / 2);
      const dy = (rRect.top  + rRect.height / 2) - (lcRect.top  + lcRect.height / 2);

      loaderClk.style.transition = 'transform 0.65s cubic-bezier(0.4, 0, 0.2, 1)';
      loaderClk.style.transform  = `translate(${dx}px,${dy}px)`;

      // T=0.65s: animation lands.
      //   Do NOT remove loaderClk here. Removing it before the loader fade commits
      //   leaves 1-2 solid-black frames where no clock is visible.
      //   Instead let the loader clock ride inside the loader as it fades.
      //   Compositing math: loader_clock×X + real_clock×(1-X) = real_clock_color
      //   at every opacity value (both are identical), so the clock stays at full
      //   brightness throughout. loaderEl.remove() at the end cleans up both.
      setTimeout(() => {
        loaderEl.style.transition = 'opacity 1.2s ease';
        loaderEl.style.opacity    = '0';

        powerEls.forEach(el => {
          el.style.transition = 'opacity 4s ease';
          el.style.opacity    = '1';
        });

        setTimeout(() => loaderEl.remove(), 1300);
      }, 650);
    }

    window._loaderMark = function(key) {
      done[key] = true;
      if (done.wx && done.news && done.sa) triggerOut();
    };

    const clockEl = document.getElementById('loader-clock');
    function tick() {
      if (!clockEl) return;
      const n = new Date();
      // same as the big clock's first paint; pad isn't defined yet here
      clockEl.textContent = document.documentElement.dataset.mode === 'pink' ? n.toLocaleTimeString('en-GB') : n.toISOString().slice(11, 19);
      setTimeout(tick, 1000 - n.getUTCMilliseconds() % 1000);
    }
    tick();

    setTimeout(triggerOut, LOAD_MAX_MS);
  })();

  // ─────────────────────────────────────────────────────────────
  //  CONFIG
  // ─────────────────────────────────────────────────────────────
  const ZONES = [
    { city:'LOS ANGELES', zone:'America/Los_Angeles', lat:34.0522, lon:-118.2437 },
    { city:'DENVER',      zone:'America/Denver',      lat:39.7392, lon:-104.9903 },
    { city:'CHICAGO',     zone:'America/Chicago',     lat:41.8781, lon:-87.6298  },
    { city:'NEW YORK',    zone:'America/New_York',    lat:40.7128, lon:-74.0060  },
    { city:'LONDON',      zone:'Europe/London',       lat:51.5074, lon:-0.1278   },
  ];

  const WX_LOCS = [
    { id:'berkeley',    label:'BERKELEY',    lat:37.8716, lon:-122.2727, metar:'KOAK' },
    { id:'turlock',     label:'TURLOCK',     lat:37.4947, lon:-120.8466, metar:'KMOD' },
    { id:'fresno',      label:'FRESNO',      lat:36.7378, lon:-119.7871, metar:'KFAT' },
    { id:'tulare',      label:'TULARE',      lat:36.2077, lon:-119.3473, metar:'KTLR' },
    { id:'bakersfield', label:'BAKERSFIELD', lat:35.3733, lon:-119.0187, metar:'KBFL' },
    { id:'la',          label:'LOS ANGELES', lat:34.0522, lon:-118.2437, metar:'KLAX' },
    { id:'chino',       label:'CHINO',       lat:34.0122, lon:-117.6889, metar:'KCNO' },
    { id:'sandiego',    label:'SAN DIEGO',   lat:32.7157, lon:-117.1611, metar:'KSAN' },
  ];

  // Google News RSS, read through server.py (browsers can't read it directly)
  const RSS_FEEDS = [
    { tag:'WORLD', cls:'ntag-world', source:'news-world', query:'hl=en&gl=US&ceid=US:en' },
    { tag:'US',    cls:'ntag-us',    source:'news-us',    query:'hl=en&gl=US&ceid=US:en' },
    { tag:'CA',    cls:'ntag-ca',    source:'news-ca',    query:'q=california+news&hl=en&gl=US&ceid=US:en' },
  ];
  const WX_REFRESH_MS   = 20 * 60 * 1000;
  const NEWS_REFRESH_MS = 5  * 60 * 1000;
  const SA_REFRESH_MS   = 4  * 60 * 1000;  // sit-aware: 4 min
  const SA_DWELL_MS     = 3500;             // ms per alert card before cycling
  const STATUS_REFRESH_MS = 60 * 1000;
  const PRESS_REFRESH_MS = 60 * 1000;
  const MISSIONS_REFRESH_MS = 2 * 60 * 1000;
  const TICKER_PX_PER_FRAME = 1.3;
  let   nextNewsRefreshAt = null;
  let   fetchCount       = 0;
  let   wxDegraded       = false;
  let   intelFeedDegraded = false;
  let   sunsetDegraded   = false;
  let   wxAlerts         = [];
  let   currentHeadlines = [];
  let   saDegraded       = false;
  let   saAlerts         = [];
  let   saIdx            = 0;
  let   saCycleTmr       = null;
  let   statusData       = null;   // server.py's /status: how each source's latest calls went

  // Every outside call goes through server.py, which records how it went for /status.
  function src(name, query = '') { return `/source/${name}${query ? '?' + query : ''}`; }

  // ─────────────────────────────────────────────────────────────
  //  STATUS — every status word on the clock comes from /status, naming its source
  // ─────────────────────────────────────────────────────────────
  const SA_SOURCES = ['usgs', 'nws', 'nhc', 'eonet', 'nifc', 'who', 'swpc'];
  function statusOf(name) { return statusData?.sources.find(s => s.name === name) || null; }
  function utcHM(iso) { const d = new Date(iso); return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}Z`; }
  // One source's status as a line: "NIFC FAILING: HTTP 503", "OPEN-METEO 9/9 ANSWERED 17:10Z".
  function statusLine(s) {
    const name = s.label.toUpperCase();
    if (s.state === 'answering') return `${name} ${s.answered}/${s.calls} ANSWERED ${utcHM(s.last_call_at)}`;
    if (s.state === 'partial')   return `${name} ${s.answered}/${s.calls} ANSWERED: ${s.error.toUpperCase()}`;
    if (s.state === 'failing')   return `${name} FAILING: ${s.error.toUpperCase()}`;
    if (s.state === 'offline')   return `${name} OFFLINE`;
    return `${name} NOT CALLED YET`;
  }
  const amber = html => `<span style="color:var(--amber)">${html}</span>`;

  async function loadStatus() {
    try {
      const r = await fetchT('/status', 5000);
      if (!r.ok) throw new Error('HTTP ' + r.status);
      statusData = await r.json();
    } catch { statusData = null; }
    renderStatus();
  }

  function renderStatus() {
    const sys = document.getElementById('sys-status');
    let allGood = false;
    if (!statusData) {
      sys.innerHTML = amber('STATUS UNKNOWN: SERVER.PY NOT ANSWERING');
    } else {
      const called = statusData.sources.filter(s => s.state !== 'not called');
      const bad    = called.filter(s => s.state !== 'answering');
      allGood = !bad.length;
      sys.innerHTML = `${called.length - bad.length} OF ${called.length} SOURCES` + (allGood ? '' :
        ' &middot; ' + amber(bad.slice(0, 2).map(s => `${s.label.toUpperCase()} ${s.state.toUpperCase()}`).join(' &middot; ') +
          (bad.length > 2 ? ` +${bad.length - 2}` : '')));
    }
    document.getElementById('sys-dot').classList.toggle('amber', !allGood);
    const om = statusOf('open-meteo');
    const wx = document.getElementById('wx-status');
    wx.innerHTML = om ? (om.state === 'answering' ? statusLine(om) : amber(statusLine(om))) : 'OPEN-METEO';
    renderFeedStatus();
    rebuildTicker();
    if (!saAlerts.length) saRenderItem(null);
    if (!missionsData) missionsRender();
  }

  // ─────────────────────────────────────────────────────────────
  //  DOM BUILD
  // ─────────────────────────────────────────────────────────────
  const tzRow = document.getElementById('tz-row');
  ZONES.forEach((z, i) => {
    tzRow.insertAdjacentHTML('beforeend', `
      <div class="tz-card">
        <div class="tz-city">${z.city}</div>
        <div class="tz-hm"  id="tz${i}-hm">--:--</div>
        <div class="tz-meta" id="tz${i}-meta">--- -- --</div>
        <div class="tz-sun"  id="tz${i}-sun"></div>
      </div>`);
  });

  const wxGrid = document.getElementById('wx-grid');
  WX_LOCS.forEach(loc => {
    wxGrid.insertAdjacentHTML('beforeend', `
      <div class="wx-card">
        <div class="wx-city">${loc.label}</div>
        <div id="wx-${loc.id}"><span class="wx-pend">FETCHING&#9646;</span></div>
      </div>`);
  });

  // ─────────────────────────────────────────────────────────────
  //  HELPERS
  // ─────────────────────────────────────────────────────────────
  const pad   = n => String(n).padStart(2,'0');
  const DAYS  = ['SUN','MON','TUE','WED','THU','FRI','SAT'];
  const MONS  = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];

  // Date and time parts of `now` in `zone` (undefined = this device's zone).
  function zoneParts(now, zone) {
    const f = new Intl.DateTimeFormat('en-US', { timeZone: zone, hourCycle: 'h23', timeZoneName: 'short',
      year: 'numeric', month: 'numeric', day: 'numeric', weekday: 'short', hour: 'numeric', minute: 'numeric', second: 'numeric' });
    const p = Object.fromEntries(f.formatToParts(now).map(x => [x.type, x.value]));
    return { y: +p.year, mo: +p.month - 1, d: +p.day, wd: p.weekday.toUpperCase(), h: +p.hour, mi: +p.minute, s: +p.second, tz: p.timeZoneName };
  }

  // One zone row: 12-hour time and the date line, read straight from that zone's parts.
  function zoneRow(now, zone) {
    const t = zoneParts(now, zone);
    return { hm: `${pad(t.h % 12 || 12)}:${pad(t.mi)} ${t.h >= 12 ? 'PM' : 'AM'}`, meta: `${t.wd} ${MONS[t.mo]} ${pad(t.d)}` };
  }

  // The big clock: this device's time, 24-hour, with its zone on the date line.
  function localClock(now, zone) {
    const t = zoneParts(now, zone);
    return { time: `${pad(t.h)}:${pad(t.mi)}:${pad(t.s)}`, date: `${t.wd}   ${pad(t.d)} ${MONS[t.mo]} ${t.y}   ${t.tz}` };
  }

  function zuluTime(now) {
    return `${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}Z`;
  }

  // What the clock block shows. Pink: this device's time big, Zulu small. Green and blue: Zulu big, local small.
  function clockFace(now, pink, zone) {
    const local = localClock(now, zone);
    if (pink) {
      const zoneName = new Intl.DateTimeFormat('en-US', { timeZone: zone, timeZoneName: 'long' })
        .formatToParts(now).find(x => x.type === 'timeZoneName').value.toUpperCase();
      return { label: `\u25C4 LOCAL TIME \u00A0\u2022\u00A0 ${zoneName} \u25BA`, big: local.time, date: local.date,
               smallLbl: 'ZULU', small: zuluTime(now) };
    }
    const z = zuluTime(now), d = now;
    return { label: '\u25C4 ZULU TIME \u00A0\u2022\u00A0 COORDINATED UNIVERSAL TIME \u25BA', big: z.slice(0, -1),
             date: `${DAYS[d.getUTCDay()]}   ${pad(d.getUTCDate())} ${MONS[d.getUTCMonth()]} ${d.getUTCFullYear()}   Z`,
             smallLbl: 'LOCAL', small: local.time };
  }

  // Whole days from today in `zone` to the next 25 December (0 on the day).
  function daysUntilChristmas(now, zone) {
    const t = zoneParts(now, zone);
    const today = Date.UTC(t.y, t.mo, t.d);
    let xmas = Date.UTC(t.y, 11, 25);
    if (xmas < today) xmas = Date.UTC(t.y + 1, 11, 25);
    return Math.round((xmas - today) / 86400000);
  }

  // Pink mode's card in the alert panel.
  function christmasItem(now, zone) {
    const n = daysUntilChristmas(now, zone), t = zoneParts(now, zone);
    const x = new Date(Date.UTC(t.y, t.mo, t.d) + n * 86400000);
    return { cat: 'DAYS UNTIL CHRISTMAS', headline: n === 0 ? 'CHRISTMAS DAY' : n === 1 ? '1 DAY' : `${n} DAYS`,
             detail: `${DAYS[x.getUTCDay()]}   ${pad(x.getUTCDate())} ${MONS[x.getUTCMonth()]} ${x.getUTCFullYear()}` };
  }

  function formatSunTime(iso) {
    const t = iso.split('T')[1];
    if (!t) return null;
    let [h, m] = t.split(':').map(Number);
    const ampm = h >= 12 ? 'PM' : 'AM';
    h = h % 12 || 12;
    return `${h}:${pad(m)} ${ampm}`;
  }

  function parseSunMin(iso) {
    const t = iso.split('T')[1];
    if (!t) return 0;
    const [h, m] = t.split(':').map(Number);
    return h * 60 + m;
  }

  // Cache sunrise/sunset data per zone so display can update without re-fetching
  const solarCache = {};

  function updateSolarDisplay() {
    ZONES.forEach((z, i) => {
      const cache = solarCache[z.zone];
      const el    = document.getElementById(`tz${i}-sun`);
      if (!el || !cache) return;
      const t      = zoneParts(new Date(), z.zone);
      const nowMin = t.h * 60 + t.mi;
      let arrow, label, timeStr;
      if (nowMin < cache.riseMin) {
        arrow = '▲'; label = 'SUNRISE'; timeStr = cache.riseStr;
      } else if (nowMin < cache.setMin) {
        arrow = '▼'; label = 'SUNSET';  timeStr = cache.setStr;
      } else {
        arrow = '▲'; label = 'SUNRISE'; timeStr = cache.rise2Str || cache.riseStr;
      }
      el.textContent = `${arrow} ${label} ${timeStr}`;
    });
  }

  function getMoonPhaseData() {
    const now   = new Date();
    const ref   = new Date(Date.UTC(2000, 0, 6, 18, 14));
    const CYCLE = 29.53058867;
    const phase = (((now - ref) / 86400000) % CYCLE + CYCLE) % CYCLE;
    const illum = Math.round((1 - Math.cos(2 * Math.PI * phase / CYCLE)) / 2 * 100);
    let name;
    if      (phase <  1.85) name = 'NEW MOON';
    else if (phase <  7.38) name = 'WAXING CRESCENT';
    else if (phase <  9.22) name = 'FIRST QUARTER';
    else if (phase < 14.77) name = 'WAXING GIBBOUS';
    else if (phase < 16.61) name = 'FULL MOON';
    else if (phase < 22.15) name = 'WANING GIBBOUS';
    else if (phase < 23.99) name = 'LAST QUARTER';
    else                    name = 'WANING CRESCENT';
    return { phase, name, illum };
  }

  // Returns SVG path `d` for the lit portion of the moon.
  // t = phase / CYCLE (0=new, 0.5=full, 1=new again)
  function moonPathD(cx, cy, R, t) {
    const angle = 2 * Math.PI * t;
    const waning = t > 0.5;
    const f = v => v.toFixed(3);
    if (!waning) {
      const tx = Math.cos(angle) * R;
      if (tx >= 0) {
        // Waxing crescent: right limb + left-curving terminator
        return `M ${cx} ${cy-R} A ${R} ${R} 0 0 1 ${cx} ${cy+R} A ${f(tx)} ${R} 0 0 0 ${cx} ${cy-R} Z`;
      } else {
        // Waxing gibbous: right limb + right-curving terminator
        return `M ${cx} ${cy-R} A ${R} ${R} 0 0 1 ${cx} ${cy+R} A ${f(-tx)} ${R} 0 0 1 ${cx} ${cy-R} Z`;
      }
    } else {
      const tl = t - 0.5;
      const tx = Math.cos(2 * Math.PI * tl) * R;
      if (tx >= 0) {
        // Waning gibbous: left limb + right-curving terminator
        return `M ${cx} ${cy-R} A ${R} ${R} 0 0 0 ${cx} ${cy+R} A ${f(tx)} ${R} 0 0 1 ${cx} ${cy-R} Z`;
      } else {
        // Waning crescent: left limb + left-curving terminator
        return `M ${cx} ${cy-R} A ${R} ${R} 0 0 0 ${cx} ${cy+R} A ${f(-tx)} ${R} 0 0 0 ${cx} ${cy-R} Z`;
      }
    }
  }

  function drawMoon() {
    const { phase, name, illum } = getMoonPhaseData();
    const CYCLE = 29.53058867;
    const t = phase / CYCLE;
    const litEl  = document.getElementById('moon-lit');
    const lblEl  = document.getElementById('moon-lbl');
    if (!litEl) return;
    const cx = 50, cy = 50, R = 45;
    // Near new moon: essentially nothing lit
    const d = (t < 0.005 || t > 0.995) ? '' : moonPathD(cx, cy, R, t);
    litEl.setAttribute('d', d);
    if (lblEl) lblEl.textContent = `${name}  ${illum}%`;
  }

  async function fetchAllSunsets() {
    const results = await Promise.all(ZONES.map(async (z) => {
      try {
        const url = src('open-meteo', `latitude=${z.lat}&longitude=${z.lon}` +
          `&daily=sunrise,sunset&forecast_days=2&timezone=${encodeURIComponent(z.zone)}`);
        const r    = await fetchT(url, 15000);
        if (!r.ok) return false;
        const data = await r.json();
        const rises = data.daily?.sunrise;
        const sets  = data.daily?.sunset;
        if (!rises?.length || !sets?.length) return false;
        solarCache[z.zone] = {
          riseMin:  parseSunMin(rises[0]),
          setMin:   parseSunMin(sets[0]),
          riseStr:  formatSunTime(rises[0]),
          setStr:   formatSunTime(sets[0]),
          rise2Str: rises[1] ? formatSunTime(rises[1]) : null,
        };
        return true;
      } catch { return false; }
    }));
    sunsetDegraded = results.some(r => r === false);
    updateSolarDisplay();
  }

  function wxDesc(c) {
    if (c===0)   return 'CLEAR SKY';
    if (c===1)   return 'MOSTLY CLEAR';
    if (c===2)   return 'PARTLY CLOUDY';
    if (c===3)   return 'OVERCAST';
    if (c<=48)   return 'FOG';
    if (c<=55)   return 'DRIZZLE';
    if (c<=65)   return 'RAIN';
    if (c<=75)   return 'SNOW';
    if (c<=77)   return 'SNOW GRAINS';
    if (c<=82)   return 'SHOWERS';
    if (c<=86)   return 'SNOW SHOWERS';
    if (c<=99)   return 'THUNDERSTORM';
    return 'UNKNOWN';
  }

  // Fetch with hard timeout — prevents hung API calls blocking indefinitely
  async function fetchT(url, ms = 9000) {
    const ctrl = new AbortController();
    const tid  = setTimeout(() => ctrl.abort(), ms);
    try {
      const r = await fetch(url, { signal: ctrl.signal });
      clearTimeout(tid);
      return r;
    } catch(e) {
      clearTimeout(tid);
      throw e.name === 'AbortError' ? new Error(`timeout after ${ms}ms`) : e;
    }
  }

  // Strip HTML entities and tags from RSS titles
  // Feed text goes into the page as text: every character that could open a tag or leave an attribute is escaped.
  function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }

  function sanitize(s) {
    return s
      .replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>')
      .replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&#x27;/g,"'")
      .replace(/&apos;/g,"'").replace(/&nbsp;/g,' ')
      .replace(/<[^>]+>/g,'')
      .trim().replace(/\s+/g,' ');
  }

  // ─────────────────────────────────────────────────────────────
  //  CLOCK TICK
  // ─────────────────────────────────────────────────────────────
  function tick() {
    const now = new Date();

    // Pink: this device's time big, Zulu small. Green and blue: Zulu big, local small.
    const face = clockFace(now, isPink());
    document.getElementById('clock-label').textContent = face.label;
    document.getElementById('local-time').textContent  = face.big;
    document.getElementById('local-date').textContent  = face.date;
    document.getElementById('small-lbl').textContent   = face.smallLbl;
    document.getElementById('small-time').textContent  = face.small;

    // Pink mode's Christmas countdown turns over at local midnight
    if (now.getSeconds() === 0 && isPink()) saRenderItem(null);

    // Zones
    ZONES.forEach((z, i) => {
      const row = zoneRow(now, z.zone);
      document.getElementById(`tz${i}-hm`).textContent   = row.hm;
      document.getElementById(`tz${i}-meta`).textContent = row.meta;
    });

    // Solar display flips when sunrise/sunset passes — check once per minute
    if (now.getUTCSeconds() === 0) updateSolarDisplay();

    // News refresh countdown
    const cdEl = document.getElementById('feed-countdown');
    if (cdEl && nextNewsRefreshAt) {
      const rem = nextNewsRefreshAt - Date.now();
      if (rem > 0) {
        const m = Math.floor(rem / 60000);
        const s = Math.floor((rem % 60000) / 1000);
        cdEl.textContent = ` · NEXT ↻ ${m}:${pad(s)}`;
      } else {
        cdEl.textContent = ' · NEXT ↻ NOW';
      }
    }
  }

  // ─────────────────────────────────────────────────────────────
  //  WEATHER
  // ─────────────────────────────────────────────────────────────
  async function fetchMetar() {
    try {
      const ids = WX_LOCS.map(l => l.metar).join(',');
      const r   = await fetchT(src('metar', `ids=${ids}&format=json`), 15000);
      const arr = await r.json();
      const map = {};
      arr.forEach(m => { map[m.icaoId] = m; });
      return map;
    } catch {
      return {};
    }
  }

  async function fetchWx(loc, metarMap) {
    const el = document.getElementById(`wx-${loc.id}`);
    try {
      const url = src('open-meteo', `latitude=${loc.lat}&longitude=${loc.lon}` +
        `&current=temperature_2m,weather_code,wind_speed_10m,precipitation` +
        `&hourly=temperature_2m,wind_speed_10m,precipitation` +
        `&temperature_unit=fahrenheit&wind_speed_unit=mph` +
        `&forecast_days=2&timezone=America%2FLos_Angeles`);
      const r    = await fetchT(url, 15000);
      const data = await r.json();
      const c    = data.current;
      const temp = Math.round(c.temperature_2m);
      const cond = wxDesc(c.weather_code);
      const tc   = temp >= 90 ? 'var(--amber)' : temp <= 45 ? 'var(--cyan)' : 'var(--green)';

      // METAR visibility: statute miles → metres. 0/missing = null.
      const metar     = (metarMap || {})[loc.metar] || {};
      const metarVisM = (metar.visib > 0) ? metar.visib * 1609.34 : null;
      const metarLow  = metarVisM !== null && metarVisM < 4828;

      // Find current hour slot in Open-Meteo hourly array
      const hTimes = data.hourly.time;
      const now    = new Date();
      const nowMs  = new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours()).getTime();
      let startIdx = 0;
      for (let i = 0; i < hTimes.length; i++) {
        const [dp, tp]     = hTimes[i].split('T');
        const [yr, mo, dy] = dp.split('-').map(Number);
        const [hr]         = tp.split(':').map(Number);
        if (new Date(yr, mo - 1, dy, hr).getTime() >= nowMs) { startIdx = i; break; }
      }
      const endIdx = Math.min(startIdx + 12, hTimes.length);

      // Find first consecutive run above threshold in an hourly array slice.
      // Returns { onset: hours from now, duration: consecutive hours in run, peak: max value in run }
      function firstRun(arr, thresh) {
        for (let i = startIdx; i < endIdx; i++) {
          const v = arr[i] || 0;
          if (v > thresh) {
            let j = i, pk = v;
            while (j < endIdx && (arr[j] || 0) > thresh) { pk = Math.max(pk, arr[j] || 0); j++; }
            return { onset: i - startIdx, duration: j - i, peak: pk };
          }
        }
        return null;
      }

      function hrLabel(n) { return n === 1 ? '1 HOUR' : `${n} HOURS`; }

      const windRun   = firstRun(data.hourly.wind_speed_10m, 10);
      const heatRun   = firstRun(data.hourly.temperature_2m, 98);
      const precipRun = firstRun(data.hourly.precipitation,   0);

      const curWind  = Math.round(c.wind_speed_10m || 0);
      const curPrec  = c.precipitation || 0;

      // Build card badges + alert objects for ticker
      const sigs   = [];
      const alerts = [];

      // HEAT
      if (heatRun || temp > 98) {
        let val, tl;
        if (heatRun && heatRun.onset === 0) {
          val = Math.round(Math.max(temp, heatRun.peak));
          tl  = `FOR ${hrLabel(heatRun.duration)}`;
        } else if (temp > 98) {
          val = temp; tl = 'NOW';
        } else {
          val = Math.round(heatRun.peak);
          tl  = `IN ${hrLabel(heatRun.onset)}`;
        }
        sigs.push(`<span class="wx-sig-heat"><svg xmlns="http://www.w3.org/2000/svg" width="8" height="16" viewBox="0 0 8 16" style="display:inline-block;vertical-align:-3px;margin-right:2px"><rect x="2.5" y="0" width="3" height="10" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.2"/><rect x="3.2" y="2" width="1.6" height="8" fill="currentColor"/><circle cx="4" cy="13" r="2.8" fill="currentColor"/></svg>HEAT ${val}&deg;</span>`);
        alerts.push({ type:'HEAT', value:`${val}°F`, timeLabel: tl });
      }

      // WIND
      if (windRun || curWind > 10) {
        let val, tl;
        if (windRun && windRun.onset === 0) {
          val = Math.round(Math.max(curWind, windRun.peak));
          tl  = `FOR ${hrLabel(windRun.duration)}`;
        } else if (curWind > 10) {
          val = curWind; tl = 'NOW';
        } else {
          val = Math.round(windRun.peak);
          tl  = `IN ${hrLabel(windRun.onset)}`;
        }
        sigs.push(`<span class="wx-sig-warn">WIND ${val}MPH</span>`);
        alerts.push({ type:'WIND', value:`${val}MPH`, timeLabel: tl });
      }

      // PRECIP
      if (precipRun || curPrec > 0) {
        let tl;
        if (precipRun && precipRun.onset === 0) {
          tl = `FOR ${hrLabel(precipRun.duration)}`;
        } else if (curPrec > 0) {
          tl = 'NOW';
        } else {
          tl = `IN ${hrLabel(precipRun.onset)}`;
        }
        sigs.push(`<span class="wx-sig-precip">PRECIP</span>`);
        alerts.push({ type:'PRECIP', value:'', timeLabel: tl });
      }

      // VIS — METAR only, observed value, no forecast duration
      if (metarLow) {
        const visMi = (metarVisM / 1609.34).toFixed(1);
        sigs.push(`<span class="wx-sig-warn">VIS ${visMi}MI</span>`);
        alerts.push({ type:'VIS', value:`${visMi}MI`, timeLabel: 'OBSERVED' });
      }

      const sigHtml = sigs.length
        ? `<div class="wx-sig">${sigs.join('<span class="wx-sig-sep"> &middot; </span>')}</div>`
        : '';

      el.innerHTML = `
        <div class="wx-temp" style="color:${tc};text-shadow:0 0 10px ${tc}55">
          ${temp}<span class="wx-unit">&deg;F</span>
        </div>
        <div class="wx-cond">${cond}</div>
        ${sigHtml}`;

      return { ok: true, alerts: alerts.map(a => ({ city: loc.label, ...a })) };
    } catch {
      el.innerHTML = `<span class="wx-err">NO SIGNAL</span>`;
      return { ok: false, alerts: [] };
    }
  }

  async function loadAllWx() {
    const metarMap = await fetchMetar();
    const results  = await Promise.all(WX_LOCS.map(loc => fetchWx(loc, metarMap)));
    wxDegraded     = results.some(r => !r.ok);
    wxAlerts       = results.flatMap(r => r.alerts);
    rebuildTicker();
    window._loaderMark && window._loaderMark('wx');
  }

  // ─────────────────────────────────────────────────────────────
  //  TICKER (rAF-driven, no CSS animation so content can update)
  // ─────────────────────────────────────────────────────────────
  const tickerEl   = document.getElementById('ticker-inner');
  const tickerWrap = document.querySelector('.ticker');
  let   tickerX        = window.innerWidth;
  let   tickerPaused   = false;
  let   tickerVelocity = 0;              // eases from 0 → TICKER_PX_PER_FRAME on resume
  let   tickerResumeTimer = null;

  function buildSysHTML(all) {
    const lines = statusData
      ? statusData.sources.filter(s => all || (s.state !== 'answering' && s.state !== 'not called')).map(statusLine)
      : ['STATUS UNKNOWN: SERVER.PY NOT ANSWERING'];
    return lines.map(s =>
      `<span class="ntag ntag-sys">[SYS]</span>&nbsp;${s}&nbsp;&nbsp;<span class="nsep">◆</span>&nbsp;&nbsp;`
    ).join('');
  }

  function buildNewsHTML(items) {
    return items.map(h => {
      const title = h.url
        ? `<a class="news-link" href="${esc(h.url)}" target="_blank" rel="noopener noreferrer">${esc(h.title)}</a>`
        : esc(h.title);
      return `<span class="ntag ${h.cls}">[${h.tag}]</span>&nbsp;${title}&nbsp;&nbsp;<span class="nsep">◆</span>&nbsp;&nbsp;`;
    }).join('');
  }

  function buildWxAlertHTML(alerts) {
    if (!alerts.length) return '';
    const seen = [], byCity = {};
    alerts.forEach(a => {
      if (!byCity[a.city]) { byCity[a.city] = []; seen.push(a.city); }
      byCity[a.city].push(a);
    });
    return seen.map(city => {
      const parts = byCity[city].map(a => {
        const val = a.value     ? ` ${a.value}`     : '';
        const tl  = a.timeLabel ? ` ${a.timeLabel}` : '';
        return `${a.type}${val}${tl}`;
      }).join(' &middot; ');
      return `<span class="ntag ntag-wx">[WX]</span>&nbsp;${city}: ${parts}&nbsp;&nbsp;<span class="nsep">◆</span>&nbsp;&nbsp;`;
    }).join('');
  }

  function buildSaTickerHTML(alerts) {
    if (!alerts.length) return '';
    return alerts.map(a => {
      return `<span class="ntag" style="color:var(--green)">[SA]</span>&nbsp;${esc(a.cat)}: ${esc(a.headline)}&nbsp;&nbsp;<span class="nsep">◆</span>&nbsp;&nbsp;`;
    }).join('');
  }

  function rebuildTicker() {
    const saHtml   = buildSaTickerHTML(saAlerts);
    const wxHtml   = buildWxAlertHTML(wxAlerts);
    const newsHtml = currentHeadlines.length
      ? buildNewsHTML(currentHeadlines) + buildSysHTML(false)
      : buildSysHTML(true);
    tickerEl.innerHTML = saHtml + wxHtml + newsHtml;
  }

  tickerWrap.addEventListener('wheel', e => {
    e.preventDefault();
    const delta = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY;
    tickerX -= delta * 2.5;
    tickerX  = Math.min(window.innerWidth, tickerX);
    tickerPaused = true;
    clearTimeout(tickerResumeTimer);
    tickerResumeTimer = setTimeout(() => { tickerPaused = false; }, 1500);
  }, { passive: false });

  rebuildTicker();

  // rAF loop — velocity lerps from 0 → full speed on resume (acute ease-in)
  (function animateTicker() {
    if (!tickerPaused) {
      tickerVelocity += (TICKER_PX_PER_FRAME - tickerVelocity) * 0.1;
      tickerX -= tickerVelocity;
      if (tickerX < -tickerEl.scrollWidth) tickerX = window.innerWidth;
    } else {
      tickerVelocity = 0;
    }
    tickerEl.style.transform = `translateX(${Math.round(tickerX)}px)`;
    requestAnimationFrame(animateTicker);
  })();

  // ─────────────────────────────────────────────────────────────
  //  LIVE NEWS — dual-proxy fetch with full error surfacing
  // ─────────────────────────────────────────────────────────────

  // Shared XML parser for raw RSS responses
  // A feed's link is kept only when it is a web address, never javascript: or data:.
  function httpOnly(u) { u = (u || '').trim(); return /^https?:\/\//i.test(u) ? u : ''; }

  function parseRssXml(xml) {
    const doc   = new DOMParser().parseFromString(xml, 'text/xml');
    // Guard against parse errors (DOMParser returns <parsererror> element)
    if (doc.querySelector('parsererror')) throw new Error('XML parse failed');
    const nodes = [...doc.querySelectorAll('item')].slice(0, 10);
    if (!nodes.length) throw new Error('no <item> elements in feed');
    return nodes.map(el => ({
      title: sanitize((el.querySelector('title')?.textContent || '').replace(/ - [^-]+$/, '')),
      url:   httpOnly(el.querySelector('link')?.textContent),
    })).filter(h => h.title);
  }

  async function fetchFeed(feed) {
    const r = await fetchT(src(feed.source, feed.query), 15000);
    if (!r.ok) throw new Error(`server.py ${r.status}`);
    return parseRssXml(await r.text()).map(i => ({ tag: feed.tag, cls: feed.cls, title: i.title, url: i.url }));
  }

  function setFeedStatus(html) {
    // innerHTML wrapper — all content is either our own strings or sanitized RSS titles
    document.getElementById('feed-status').innerHTML = html;
  }

  // The headline count; a failing news feed is named in the sources line, not here.
  function renderFeedStatus() {
    if (!nextNewsRefreshAt) return;   // first load not finished
    setFeedStatus(currentHeadlines.length ? `${currentHeadlines.length} HEADLINES` : amber('NO HEADLINES'));
  }

  async function loadHeadlines() {
    fetchCount++;

    const results = await Promise.allSettled(RSS_FEEDS.map(fetchFeed));
    const items   = results.filter(r => r.status === 'fulfilled').flatMap(r => r.value);
    const failed  = results.filter(r => r.status === 'rejected');

    // Log per-feed failures with correct feed tag (by index, not indexOf)
    results.forEach((r, i) => {
      if (r.status === 'rejected')
        console.error(`Feed [${RSS_FEEDS[i].tag}] failed:`, r.reason?.message);
    });

    nextNewsRefreshAt   = Date.now() + NEWS_REFRESH_MS;
    intelFeedDegraded   = (items.length === 0);

    if (items.length > 0) {
      currentHeadlines = items;
      rebuildTicker();
      if (failed.length) console.warn(`${failed.length} feeds degraded — see console.`);
    } else {
      console.error('All news feeds failed:', results.map((r,i) =>
        `[${RSS_FEEDS[i].tag}] ${r.reason?.message}`).join(' | '));
    }
    renderFeedStatus();
    window._loaderMark && window._loaderMark('news');
  }

  // ─────────────────────────────────────────────────────────────
  //  SITUATIONAL AWARENESS
  // ─────────────────────────────────────────────────────────────
  // CA bounding box for quake filtering
  const CA_LAT = [32.4, 42.1], CA_LON = [-124.6, -114.0];

  function saHrLabel(n) { return n === 1 ? '1 HOUR' : `${n} HOURS`; }

  // Tactical thermometer — tube + bilateral scale marks + mercury fill + bulb
  const THERMO_SA_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 100" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="2"><path d="M19,72 L19,11 A6,6,0,0,0,31,11 L31,72"/><rect x="21" y="35" width="8" height="37" fill="currentColor" stroke="none"/><line x1="13" y1="35" x2="37" y2="35" stroke-width="1.5"/><line x1="19" y1="15" x2="10" y2="15"/><line x1="19" y1="35" x2="10" y2="35"/><line x1="19" y1="55" x2="10" y2="55"/><line x1="19" y1="25" x2="14" y2="25" stroke-width="1.2"/><line x1="19" y1="45" x2="14" y2="45" stroke-width="1.2"/><line x1="19" y1="65" x2="14" y2="65" stroke-width="1.2"/><line x1="31" y1="15" x2="40" y2="15"/><line x1="31" y1="35" x2="40" y2="35"/><line x1="31" y1="55" x2="40" y2="55"/><line x1="31" y1="25" x2="36" y2="25" stroke-width="1.2"/><line x1="31" y1="45" x2="36" y2="45" stroke-width="1.2"/><line x1="31" y1="65" x2="36" y2="65" stroke-width="1.2"/><circle cx="25" cy="85" r="13"/><circle cx="25" cy="85" r="9" fill="currentColor" stroke="none"/></svg>`;

  // 2-armed hurricane spiral — filled tapered shapes.
  // Each arm: thick root where it meets the eye (r≈10), tapering to a sharp tip at the outer
  // edge (r≈42). Arms sweep 270° CCW. Width = 18 at root, 0 at tip.
  // Outer edge: spiral from r=28 (top) outward to tip. Inner edge: r=10 to same tip.
  // Bezier CPs: 0.552 × avg-radius × tangent-direction at each quarter-turn node.
  // Arm 2 is (x,y)→(100-x,100-y) symmetric — thick at bottom, tip at left.
  const SPIRAL_SA_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="currentColor" stroke="none"><path d="M50,28 C36,28 21,36 21,50 C21,68 32,86 50,86 C70,86 92,73 92,50 C92,70 70,79 50,79 C38,79 35,62 35,50 C35,43 43,40 50,40 C60,40 60,28 50,28 Z"/><path d="M50,72 C64,72 79,64 79,50 C79,32 68,14 50,14 C30,14 8,27 8,50 C8,30 30,21 50,21 C62,21 65,38 65,50 C65,57 57,60 50,60 C40,60 40,72 50,72 Z"/></svg>`;

  // Six-armed snowflake — spokes with V branches, for pink mode's Christmas countdown
  const SNOWFLAKE_SA_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="5">${
    [0, 60, 120, 180, 240, 300].map(a => `<g transform="rotate(${a} 50 50)"><line x1="50" y1="50" x2="50" y2="6"/><polyline points="38,16 50,28 62,16"/><polyline points="42,32 50,40 58,32"/></g>`).join('')
  }<circle cx="50" cy="50" r="5" fill="currentColor" stroke="none"/></svg>`;

  // Bootstrap Icons bi-fire (MIT) — outer flame body + dimmed inner core
  const FLAME_SA_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor"><path d="M8 16c3.314 0 6-2 6-5.5 0-1.5-.5-4-2.5-6 .25 1.5-1.25 2-1.25 2C11 4 9 .5 6 0c.357 2 .5 4-2 6-1.25 1-2 2.729-2 4.5C2 14 4.686 16 8 16"/><path opacity=".45" d="M8 15c-1.657 0-3-1-3-2.75 0-.75.25-2 1.25-3C6.125 10 7 10.5 7 10.5c-.375-1.25.5-3.25 2-3.5-.179 1-.25 2 1 3 .625.5 1 1.364 1 2.25C11 14 9.657 15 8 15"/></svg>`;


  // A source that fails is told apart from one that answered with no alerts: the failure is an empty list marked
  // failed, so merging the lists is unchanged and loadSitAware can count the failures.
  async function saFetchT(url, ms) {
    const r = await fetchT(url, ms);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r;
  }
  function saFailed() { return Object.assign([], { failed: true }); }
  function saIsFailed(r) { return r.status === 'rejected' || !!(r.value && r.value.failed); }
  // Degraded when more than half of the sources failed.
  function saIsDegraded(results, total) { return results.filter(saIsFailed).length > total / 2; }

  async function saFetchSeismic() {
    try {
      const r    = await saFetchT(src('usgs'), 15000);
      const data = await r.json();
      const ca   = data.features.filter(f => {
        const [lon, lat] = f.geometry.coordinates;
        return lat >= CA_LAT[0] && lat <= CA_LAT[1] && lon >= CA_LON[0] && lon <= CA_LON[1];
      });
      if (!ca.length) return [];
      ca.sort((a, b) => b.properties.mag - a.properties.mag);
      const q   = ca[0];
      const mag = q.properties.mag;
      if (mag < 3.5) return [];
      const place   = (q.properties.place || 'CALIFORNIA').toUpperCase().replace(/^\d+KM \w+ OF /,'');
      const minsAgo = Math.round((Date.now() - q.properties.time) / 60000);
      const depth   = Math.round(q.geometry.coordinates[2]);
      const timeStr = minsAgo < 60 ? `${minsAgo}MIN AGO` : `${Math.round(minsAgo/60)}HR AGO`;
      const sev     = mag >= 6.5 ? 4 : mag >= 5.5 ? 3 : mag >= 4.5 ? 2 : 1;
      return [{ symbol:'≈', cat:'SEISMIC', headline:`M${mag.toFixed(1)} · ${place}`, detail:`${timeStr} · DEPTH ${depth}KM`, sev }];
    } catch { return saFailed(); }
  }

  async function saFetchNwsAlerts() {
    try {
      const r    = await saFetchT(src('nws', 'area=CA'), 15000);
      const data = await r.json();
      const hits  = (data.features || []).filter(f =>
        f.properties.severity === 'Extreme' || f.properties.severity === 'Severe');
      if (!hits.length) return [];
      const types   = [...new Set(hits.map(f => f.properties.event))];
      const sev     = hits.some(f => f.properties.severity === 'Extreme') ? 4 : 3;
      const count   = hits.length;
      const isHeat  = types.some(t => /heat/i.test(t));
      const sym     = isHeat ? THERMO_SA_SVG : '⚑';
      const rawArea = hits[0].properties.areaDesc || '';
      const area    = rawArea.split(';')[0].replace(/ County$/i,'').replace(/ counties$/i,'').trim().toUpperCase().substring(0, 22) || 'CA';
      return [{ symbol: sym, cat:'CA ALERT', headline: types[0].toUpperCase(), detail:`${area} · ${count} ALERT${count > 1 ? 'S' : ''} · NWS`, sev }];
    } catch { return saFailed(); }
  }

  async function saFetchStorms() {
    try {
      const r     = await saFetchT(src('nhc'), 15000);
      const data  = await r.json();
      const storms = data.activeStorms || [];
      if (!storms.length) return [];
      return storms.map(s => {
        const kt      = parseInt(s.intensity) || 0;
        const type    = kt >= 137 ? 'CAT 5 HURRICANE' : kt >= 113 ? 'CAT 4 HURRICANE' : kt >= 96 ? 'CAT 3 HURRICANE' : kt >= 83 ? 'CAT 2 HURRICANE' : kt >= 64 ? 'CAT 1 HURRICANE' : kt >= 34 ? 'TROPICAL STORM' : 'TROPICAL DEPRESSION';
        const sev     = kt >= 96 ? 4 : kt >= 64 ? 3 : 2;
        const latStr  = s.latitude || s.lat || '';
        const lonStr  = s.longitude || s.lon || '';
        const lat     = parseFloat(latStr) * (String(latStr).endsWith('S') ? -1 : 1);
        const lon     = parseFloat(lonStr) * (String(lonStr).endsWith('W') ? -1 : 1);
        let region    = (s.basin || '').toUpperCase() === 'EP' ? 'E PACIFIC' : 'ATLANTIC';
        if (!isNaN(lat) && !isNaN(lon)) {
          if (lat > 20 && lat < 32 && lon > -98 && lon < -82)       region = 'GULF OF MEXICO';
          else if (lat > 8 && lat < 24 && lon > -88 && lon < -60)   region = 'CARIBBEAN';
          else if (lon < -100)                                        region = 'E PACIFIC';
        }
        return { symbol: SPIRAL_SA_SVG, cat:'TROPICAL', headline:`${(s.name||'UNNAMED').toUpperCase()} · ${type}`, detail:`${kt}KT · ${region}`, sev };
      });
    } catch { return saFailed(); }
  }

  async function saFetchEonet() {
    try {
      const r    = await saFetchT(src('eonet', 'status=open&limit=25'), 15000);
      const data = await r.json();
      // Wildfires handled by saFetchCAWildfires (NIFC); EONET covers other global events
      const WANT = { 'Volcanoes':3, 'Severe Storms':2, 'Floods':2 };
      const hits = (data.events || []).filter(e =>
        e.categories.some(c => WANT[c.title] !== undefined)
      );
      if (!hits.length) return [];

      function eonetRegion(e) {
        const geo = (e.geometry || []).slice().reverse().find(g => g.coordinates);
        if (!geo) return null;
        const [lon, lat] = geo.coordinates;
        if (lat > 20 && lat < 32 && lon > -98 && lon < -82) return 'GULF OF MEXICO';
        if (lat > 8  && lat < 24 && lon > -88 && lon < -60) return 'CARIBBEAN';
        if (lat >= 0 && lon < -100)                          return 'E PACIFIC';
        if (lat >= 0 && lon > 100)                           return 'W PACIFIC';
        if (lat >= 0 && lon > 30 && lon <= 100)              return 'INDIAN OCEAN';
        if (lat >= 0 && lon <= 0)                            return 'N ATLANTIC';
        if (lat < 0  && lon > 100)                           return 'S PACIFIC';
        if (lat < 0  && lon <= 0)                            return 'S ATLANTIC';
        return null;
      }

      return hits.slice(0, 3).map(e => {
        const cat    = e.categories[0].title;
        const sev    = WANT[cat] || 2;
        const sym    = cat === 'Volcanoes' ? '▲' : SPIRAL_SA_SVG;
        const region = eonetRegion(e);
        const detail = region ? `EONET · ${region}` : 'NASA EONET';
        return { symbol: sym, cat: cat.toUpperCase(), headline: e.title.toUpperCase(), detail, sev };
      });
    } catch { return saFailed(); }
  }

  async function saFetchCAWildfires() {
    try {
      const where = encodeURIComponent(
        "POOState='US-CA' AND IncidentTypeCategory='WF' AND DiscoveryAcres>=10"
      );
      const url = src('nifc', `where=${where}&outFields=IncidentName,DiscoveryAcres,PercentContained,POOCounty` +
        '&orderByFields=DiscoveryAcres+DESC&resultRecordCount=5&f=json');
      const r    = await saFetchT(url, 15000);
      const data = await r.json();
      if (data.error) return saFailed();
      const fires = (data.features || []).map(f => f.attributes).filter(f => f.IncidentName);
      if (!fires.length) return [];
      return fires.map(f => {
        const name   = (f.IncidentName || 'UNKNOWN').toUpperCase().replace(/ FIRE$/, '').trim();
        const acres  = Math.round(f.DiscoveryAcres || 0);
        const pct    = f.PercentContained;
        const county = (f.POOCounty || '').toUpperCase();
        const sev    = acres >= 10000 ? 3 : 2;
        const tag    = (pct === null || pct === undefined) ? 'ACTIVE' : pct === 0 ? 'UNCONTAINED' : `${pct}% CONTAINED`;
        return { symbol: FLAME_SA_SVG, cat:'CA WILDFIRE', headline:`${name} FIRE`, detail:`${acres.toLocaleString()} AC · ${county} CTY · ${tag}`, sev };
      });
    } catch { return saFailed(); }
  }

  async function saFetchHealth() {
    try {
      // WHO removed the dedicated DON RSS; use general news feed and filter for outbreaks
      const r    = await saFetchT(src('who'), 15000);
      const doc  = new DOMParser().parseFromString(await r.text(), 'text/xml');
      if (doc.querySelector('parsererror')) return saFailed();
      const OUTBREAK_RE = /outbreak|disease|virus|epidemic|influenza|flu|h5n1|h5n2|bird flu|avian flu|mpox|measles|dengue|ebola|filovirus|hantavirus|cholera|typhoid|plague|marburg|avian|zoonot/i;
      const cutoff = Date.now() - 7 * 86400000; // show items up to 7 days old
      const hits = [...doc.querySelectorAll('item')]
        .filter(item => OUTBREAK_RE.test(item.querySelector('title')?.textContent || ''))
        .filter(item => new Date(item.querySelector('pubDate')?.textContent || 0).getTime() > cutoff)
        .slice(0, 3);
      if (!hits.length) return [];
      return hits.map(item => {
        const title   = (item.querySelector('title')?.textContent || '').toUpperCase();
        const ageDays = (Date.now() - new Date(item.querySelector('pubDate')?.textContent || 0)) / 86400000;
        const sev     = /PHEIC|PANDEMIC|EMERGENCY|EBOLA|MARBURG/i.test(title) ? 4 : 2;
        const ageStr  = ageDays < 1 ? `${Math.round(ageDays*24)}H AGO` : `${Math.round(ageDays)}D AGO`;
        return { symbol:'⊕', cat:'HEALTH WATCH', headline: title.substring(0, 38), detail:`WHO · ${ageStr}`, sev };
      });
    } catch { return saFailed(); }
  }

  async function saFetchSpace() {
    try {
      const r    = await saFetchT(src('swpc'), 15000);
      const rows = await r.json();
      // rows[0] is headers; latest is last row
      const latest = rows[rows.length - 1];
      const kp     = parseFloat(latest[1]);
      if (isNaN(kp) || kp < 5) return [];
      const g    = kp >= 9 ? 'G5' : kp >= 8 ? 'G4' : kp >= 7 ? 'G3' : kp >= 6 ? 'G2' : 'G1';
      const sev  = kp >= 8 ? 4 : kp >= 7 ? 3 : 2;
      const hfImpact = kp >= 7 ? 'HF/NVIS DEGRADED' : kp >= 6 ? 'HF WATCH' : 'MINOR IMPACT';
      return [{ symbol:'✦', cat:'SPACE WX', headline:`${g} GEOMAGNETIC STORM`, detail:`Kp=${kp.toFixed(0)} · ${hfImpact}`, sev }];
    } catch { return saFailed(); }
  }


  // With no alerts: only "ALL CLEAR" when every SA source answered; otherwise say which didn't.
  function saClearSources() { return SA_SOURCES.map(statusOf).filter(Boolean); }
  function saClearBad() { return saClearSources().filter(s => s.state !== 'answering'); }
  function saClearCat() {
    if (!statusData) return 'NO ALERTS';
    return saClearBad().length ? amber('NO ALERTS') : 'ALL CLEAR';
  }
  function saClearHeadline() {
    if (!statusData) return 'SOURCE STATUS<br>UNKNOWN';
    const all = saClearSources(), ok = all.length - saClearBad().length;
    return `${ok} OF ${all.length} SOURCES<br>ANSWERING`;
  }
  function saClearDetail() {
    if (!statusData) return 'SERVER.PY NOT ANSWERING';
    const bad = saClearBad();
    return bad.length ? amber(bad.map(s => `${s.label.toUpperCase()} ${s.state.toUpperCase()}`).join(' · '))
                      : saClearSources().map(s => s.label.toUpperCase()).join(' · ');
  }

  // Pink mode shows no alerts: a snowflake and the days until Christmas instead.
  function isPink() { return document.documentElement.dataset.mode === 'pink'; }

  function saRenderItem(alert) {
    const el = document.getElementById('sa-item');
    if (isPink()) {
      const x = christmasItem(new Date());
      el.innerHTML = `
        <div class="sa-symbol" style="color:rgba(var(--fg-rgb),0.28)">${SNOWFLAKE_SA_SVG}</div>
        <div class="sa-cat">${x.cat}</div>
        <div class="sa-headline">${x.headline}</div>
        <div class="sa-detail">${x.detail}</div>`;
      requestAnimationFrame(fitSaPanel);
      return;
    }
    if (!alert) {
      el.innerHTML = `
        <div class="sa-symbol" style="color:rgba(var(--fg-rgb),0.18)">◆</div>
        <div class="sa-cat"    style="color:rgba(var(--fg-rgb),0.28)">${saClearCat()}</div>
        <div class="sa-headline" style="font-size:18px;color:rgba(var(--fg-rgb),0.28)">${saClearHeadline()}</div>
        <div class="sa-detail">${saClearDetail()}</div>`;
      requestAnimationFrame(fitSaPanel);
      return;
    }
    el.innerHTML = `
      <div class="sa-symbol" style="color:rgba(var(--fg-rgb),0.28)">${alert.symbol}</div>
      <div class="sa-cat">${esc(alert.cat)}</div>
      <div class="sa-headline">${esc(alert.headline)}</div>
      <div class="sa-detail">${esc(alert.detail)}</div>`;
    requestAnimationFrame(fitSaPanel);
  }

  function saRenderDots() {
    const el = document.getElementById('sa-dots');
    if (saAlerts.length <= 1 || isPink()) { el.innerHTML = ''; return; }
    el.innerHTML = saAlerts.map((_, i) =>
      `<div class="sa-dot${i === saIdx ? ' active' : ''}"></div>`
    ).join('');
  }

  function saStartCycle() {
    clearInterval(saCycleTmr);
    saRenderItem(saAlerts[saIdx] || null);
    saRenderDots();
    if (saAlerts.length <= 1) return;
    saCycleTmr = setInterval(() => {
      if (isPink()) return;
      const el = document.getElementById('sa-item');
      el.classList.add('fading');
      setTimeout(() => {
        saIdx = (saIdx + 1) % saAlerts.length;
        saRenderItem(saAlerts[saIdx]);
        saRenderDots();
        el.classList.remove('fading');
      }, 340);
    }, SA_DWELL_MS);
  }

  // 48-hour alert persistence via localStorage —
  // alerts detected by any fetcher are kept for 48h even if the live feed
  // no longer returns them (handles gaps between NHC advisories, WHO posts, etc.)
  const SA_STORE_KEY = 'zc_sa_v1';
  const SA_PERSIST_MS = 48 * 3600 * 1000;

  function saLoadStored() {
    try {
      const items = JSON.parse(localStorage.getItem(SA_STORE_KEY) || '[]');
      return items.filter(a => (Date.now() - a._seen) < SA_PERSIST_MS);
    } catch { return []; }
  }

  function saMerge(fresh) {
    const now    = Date.now();
    const stored = saLoadStored();
    const seenAt = new Map(stored.map(a => [`${a.cat}|${a.headline}`, a._seen]));
    // Tag fresh items with first-seen timestamp
    const tagged = fresh.map(a => ({ ...a, _seen: seenAt.get(`${a.cat}|${a.headline}`) || now }));
    const freshKeys = new Set(tagged.map(a => `${a.cat}|${a.headline}`));
    // Retain cached items not in fresh results (still within 48h)
    const persisted = stored.filter(a => !freshKeys.has(`${a.cat}|${a.headline}`));
    const merged = [...tagged, ...persisted];
    try { localStorage.setItem(SA_STORE_KEY, JSON.stringify(merged.slice(0, 60))); } catch {}
    return merged;
  }

  // NHC (cat:'TROPICAL') and EONET (cat:'SEVERE STORMS') both report the same
  // tropical systems. Keep the NHC entry (richer: category, wind speed, region);
  // drop the EONET duplicate if its headline contains the same storm name.
  function saDeduplicateStorms(alerts) {
    const nhcNames = new Set(
      alerts
        .filter(a => a.cat === 'TROPICAL')
        .map(a => a.headline.split(/\s*[·\-]\s*/)[0].trim())
        .filter(n => n.length > 2)
    );
    if (!nhcNames.size) return alerts;
    return alerts.filter(a => {
      if (a.cat !== 'SEVERE STORMS') return true;
      return ![...nhcNames].some(name => a.headline.includes(name));
    });
  }

  async function loadSitAware() {
    const SA_FETCHERS = [saFetchSeismic, saFetchNwsAlerts, saFetchStorms, saFetchEonet, saFetchCAWildfires, saFetchHealth, saFetchSpace];
    const results = await Promise.allSettled(SA_FETCHERS.map(f => f()));
    const fresh   = results.filter(r => r.status === 'fulfilled').flatMap(r => r.value).filter(Boolean);
    saDegraded    = saIsDegraded(results, SA_FETCHERS.length);
    saAlerts      = saDeduplicateStorms(saMerge(fresh)).sort((a, b) => b.sev - a.sev);
    saIdx         = 0;
    saStartCycle();
    rebuildTicker();
    window._loaderMark && window._loaderMark('sa');
  }

  // ─────────────────────────────────────────────────────────────
  //  PRESS — overdue, today and the next countdown, read from the Presser app.
  //  Read only: GET /api/summary every minute. Keeps nothing in localStorage.
  // ─────────────────────────────────────────────────────────────
  let pressData = null;   // last good summary, or null when the app did not answer

  // The live story with the nearest event still ahead, or null (an old-builder story has no date).
  function pressNext(stories) {
    let best = null;
    stories.forEach(st => {
      const t = Date.parse(st.countdown_to);
      if (!(t > Date.now())) return;
      if (!best || t < best.t) best = { t, id: st.id };
    });
    return best;
  }

  const PRESS_DAYS = ['SUN','MON','TUE','WED','THU','FRI','SAT'];
  const PRESS_MONS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
  function pressWhen(t) {
    const d = new Date(t), p = v => String(v).padStart(2, '0');
    return `${PRESS_DAYS[d.getDay()]} ${d.getDate()} ${PRESS_MONS[d.getMonth()]} ${p(d.getHours())}:${p(d.getMinutes())}`;
  }

  // Cards share the weather grid's columns: the whole row, extra columns to the first cards;
  // when they can't all get two columns, two each and they wrap (a whole row each below four columns).
  function pressSpread(cards) {
    const cols = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--wx-cols')) || 8;
    const n = cards.length;
    cards.forEach((c, i) => c.style.setProperty('--span',
      n * 2 > cols ? (cols < 4 ? cols : 2) : Math.floor(cols / n) + (i < cols % n ? 1 : 0)));
  }

  // The stories that get a card: not archived, and not finished (every step done).
  function pressVisible(stories) {
    return stories.filter(st => {
      const [done, total] = st.progress || [];
      return !st.archived && !(total > 0 && done >= total);
    });
  }

  function pressRender() {
    const sec  = document.getElementById('press');
    const head = document.getElementById('press-head');
    const body = document.getElementById('press-body');
    if (!sec || !head || !body) return;
    sec.href = '/go/presser';   // the server sends it on to Presser's home address
    if (!pressData) {
      sec.classList.add('press-off');
      const ps = statusOf('presser');
      head.textContent = 'PRESS: ' + (ps && ps.state !== 'not called' ? statusLine(ps) : 'app not running');
      body.replaceChildren();
      return;
    }
    sec.classList.remove('press-off');
    const stories = pressVisible(pressData.stories);
    const live = stories.filter(st => !st.old_builder);
    const el = (tag, cls, ...kids) => { const e = document.createElement(tag); if (cls) e.className = cls; e.append(...kids); return e; };
    const span = (cls, text) => el('span', cls, text);
    const sep = () => span('wx-sig-sep', ' · ');

    // Head: totals across the live stories, after the rule.
    const tot = pressData.totals || {};
    const totBits = [
      span(tot.overdue ? 'press-od' : '', `${tot.overdue || 0} OVERDUE`), sep(),
      span(tot.today ? 'press-td' : '', `${tot.today || 0} TODAY`)];
    if (tot.messages) totBits.push(sep(), span('', `${tot.messages} TO CHASE`));
    head.replaceChildren('PRESS — PRESSER APP', el('span', 'press-tot', ...totBits));

    // One card per story, the one with the nearest event first: its countdown sits in its own card.
    // Then overdue, then today, then the soonest event, then the rest.
    const nxt = pressNext(live);
    const rank = st => nxt && st.id === nxt.id ? -1 : st.old_builder ? 3 : st.overdue ? 0 : st.today ? 1 : 2;
    const when = st => { const t = Date.parse(st.countdown_to); return t > 0 ? t : Infinity; };
    const shown = stories.slice().sort((a, b) => rank(a) - rank(b) || when(a) - when(b)).slice(0, 4);
    const cards = shown.map(st => {
      const card = el('div', 'wx-card press-card' + (st.overdue ? ' overdue' : st.today ? ' today' : ''),
        el('div', 'wx-city', span('', st.short_name.toUpperCase()), span('', String(st.doc || '').toUpperCase())));
      if (nxt && st.id === nxt.id) {
        const today = new Date(nxt.t).toDateString() === new Date().toDateString();
        const s = Math.max(0, Math.floor((nxt.t - Date.now()) / 1000)), p = v => String(v).padStart(2, '0');
        const d = Math.floor(s / 86400);
        const hms = `${p(Math.floor(s % 86400 / 3600))}:${p(Math.floor(s % 3600 / 60))}:${p(s % 60)}`;
        const cd = el('div', 'wx-temp press-cd' + (today ? ' today' : ''), span('wx-unit', 'T-'));
        if (d) cd.append(String(d), span('wx-unit', 'D'));
        cd.append(hms);
        card.append(el('div', 'press-cdrow', cd, span('', pressWhen(nxt.t))));
      }
      if (st.old_builder) {
        card.append(el('div', 'press-line', 'OLD BUILDER'));
        return card;
      }
      const [done, total] = st.progress || [];
      if (total) {
        const track = el('div', '', el('i'));
        track.style.setProperty('--seg', total);
        track.firstChild.style.width = `${100 * done / total}%`;
        card.append(el('div', 'press-bar', track, span('', `${done}/${total}`)));
      }
      const counts = [];
      if (st.overdue) counts.push(span('press-od', `${st.overdue} OVERDUE`));
      if (st.today)   counts.push(counts.length ? sep() : '', span('press-td', `${st.today} TODAY`));
      if (!counts.length) counts.push(st.upcoming ? `${st.upcoming} UPCOMING` : 'NOTHING DUE');
      card.append(el('div', 'press-line', ...counts));
      const send = (st.sends_open || [])[0];
      if (st.next && st.next.text) {
        card.append(el('div', 'press-line' + (st.next.state === 'late' ? ' press-late' : ''), '▸ ' + st.next.text.toUpperCase()));
      } else if (send) {
        card.append(el('div', 'press-line', '▸ ' + send.label.toUpperCase() + (Date.parse(send.due) ? ' · ' + pressWhen(Date.parse(send.due)) : '')));
      }
      return card;
    });
    pressSpread(cards);
    if (stories.length > shown.length) head.lastChild.append(sep(), span('', `+${stories.length - shown.length} MORE`));
    body.replaceChildren(el('div', 'press-grid', ...cards));
  }

  // ─────────────────────────────────────────────────────────────
  //  MISSIONS — upcoming FS missions, from cmd fs's mmGetMissions via server.py /missions.
  //  First names, dates, types and facilities. Read only, keeps nothing.
  // ─────────────────────────────────────────────────────────────
  let missionsData = null;     // last good mmGetMissions answer
  let missionsNote = '';       // why there is none, for the head

  function missionsRender() {
    const head = document.getElementById('missions-head');
    const body = document.getElementById('missions-body');
    if (!head || !body) return;
    if (!missionsData) {
      const ms = statusOf('mission-cmd');
      head.textContent = 'MISSIONS: ' + (ms && ms.state !== 'not called' ? statusLine(ms) : missionsNote);
      body.replaceChildren();
      return;
    }
    const el = (tag, cls, ...kids) => { const e = document.createElement(tag); if (cls) e.className = cls; e.append(...kids); return e; };
    const span = (cls, text) => el('span', cls, text);
    const sep = () => span('wx-sig-sep', ' · ');
    const now = Date.now();
    const up = missionsData.missions.filter(m => !m.cancelled && m.days_out >= 0)
      .sort((a, b) => a.days_out - b.days_out);
    const planLate = m => !m.approved && !m.planReceived && Date.parse(m.planDue) < now;

    // Head: this week, plans late, and missions near with no approved plan.
    const gates = up.filter(m => m.gate_warning).length;
    const late  = up.filter(planLate).length;
    const tot = [span('', `${up.filter(m => m.days_out <= 7).length} THIS WEEK`)];
    if (late)  tot.push(sep(), span('press-td', `${late} PLAN${late > 1 ? 'S' : ''} LATE`));
    if (gates) tot.push(sep(), span('press-od', `${gates} NO PLAN, ≤2 DAYS`));
    head.replaceChildren('MISSIONS — CMD FS', el('span', 'press-tot', ...tot));

    const cards = up.slice(0, 4).map(m => {
      const near = m.days_out <= 2;
      const card = el('div', 'wx-card press-card' + (m.gate_warning ? ' overdue' : near || planLate(m) ? ' today' : ''),
        el('div', 'wx-city', span('', m.label.toUpperCase()),
          span('', m.types.map(t => t.replace(/_/g, ' ')).join(' + ').toUpperCase() || 'NO TYPE')));
      const cd = el('div', 'wx-temp press-cd' + (near ? ' today' : ''));
      if (m.days_out === 0) cd.append('TODAY');
      else cd.append(span('wx-unit', 'T-'), String(m.days_out), span('wx-unit ms-days', m.days_out === 1 ? 'DAY' : 'DAYS'));
      card.append(el('div', 'press-cdrow', cd, span('', m.members.map(n => n.split(' ')[0]).join(' + ').toUpperCase())));
      const tick = (on, word) => span(on ? 'done' : '', (on ? '■ ' : '□ ') + word);
      card.append(el('div', 'ms-ticks',
        tick(m.confirmed, 'CONFIRMED'), tick(m.briefingSent, 'BRIEFING'),
        m.approved || !m.gate_warning ? tick(m.approved, 'PLAN OK') : span('need', '□ PLAN OK')));
      let plan;
      if (m.approved)          plan = el('div', 'press-line', 'PLAN APPROVED');
      else if (m.planReceived) plan = el('div', 'press-line', 'PLAN IN' + (Date.parse(m.planReceived.review_by) ? ' · REVIEW BY ' + pressWhen(Date.parse(m.planReceived.review_by)) : ''));
      else if (Date.parse(m.planDue)) plan = el('div', 'press-line' + (planLate(m) ? ' press-td' : ''), (planLate(m) ? 'PLAN LATE · WAS DUE ' : 'PLAN DUE ') + pressWhen(Date.parse(m.planDue)));
      if (plan) card.append(plan);
      if (m.facilities.length) card.append(el('div', 'press-line', '▸ ' + m.facilities.join(' + ').toUpperCase()));
      return card;
    });
    pressSpread(cards);
    if (up.length > cards.length) head.lastChild.append(sep(), span('', `+${up.length - cards.length} MORE`));
    body.replaceChildren(el('div', 'press-grid', ...cards));
  }

  async function loadMissions() {
    const ctl = new AbortController();
    const to  = setTimeout(() => ctl.abort(), 20000);
    try {
      if (!location.protocol.startsWith('http')) throw new Error('opened as a file');
      const r = await fetch('/missions', { signal: ctl.signal, cache: 'no-store' });
      if (!r.ok) throw new Error('cmd fs did not answer');
      const d = await r.json();
      if (!Array.isArray(d.missions)) throw new Error('cmd fs did not answer');
      missionsData = d;
    } catch (e) {
      missionsData = null;
      missionsNote = e.name === 'AbortError' ? 'cmd fs did not answer' : e.message;
    } finally {
      clearTimeout(to);
    }
    try { missionsRender(); } catch { missionsData = null; missionsNote = 'could not read the answer'; missionsRender(); }
  }

  async function loadPress() {
    const ctl = new AbortController();
    const to  = setTimeout(() => ctl.abort(), 5000);
    try {
      const r = await fetch(src('presser'), { signal: ctl.signal, cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const d = await r.json();
      if (!Array.isArray(d.stories)) throw new Error('not a summary');
      pressData = d;
    } catch {
      pressData = null;
    } finally {
      clearTimeout(to);
    }
    try { pressRender(); } catch { pressData = null; pressRender(); }
  }

  // ─────────────────────────────────────────────────────────────
  //  MODES — green, pink, blue. Click the moon or press M for the next one.
  // ─────────────────────────────────────────────────────────────
  const MODES = ['green', 'pink', 'blue'];
  function nextMode() {
    const now  = document.documentElement.dataset.mode || 'green';
    const mode = MODES[(MODES.indexOf(now) + 1) % MODES.length];
    if (mode === 'green') delete document.documentElement.dataset.mode;
    else document.documentElement.dataset.mode = mode;
    try { localStorage.setItem('zulu-mode', mode); } catch {}
    saRenderItem(saAlerts[saIdx] || null);   // pink swaps alerts for the Christmas countdown
    saRenderDots();
  }
  document.getElementById('moon-panel').addEventListener('click', nextMode);
  document.addEventListener('keydown', e => {
    if (e.key.toLowerCase() !== 'm' || e.metaKey || e.ctrlKey || e.altKey || e.repeat) return;
    if (e.target.closest && e.target.closest('input, textarea, [contenteditable]')) return;
    nextMode();
  });

  // ─────────────────────────────────────────────────────────────
  //  START
  // ─────────────────────────────────────────────────────────────
  tick();
  setInterval(() => { tick(); if (pressData) pressRender(); }, 1000);

  drawMoon();
  setInterval(drawMoon, 60 * 60 * 1000); // moon phase changes slowly, hourly is plenty

  // Fit SA panel: symbol height = center height minus the text rows below it.
  // Called after every saRenderItem() and on resize.
  function fitSaPanel() {
    const center  = document.querySelector('.zulu-center');
    const saBlock = document.querySelector('.sa-block');
    const symEl   = saBlock && saBlock.querySelector('.sa-symbol');
    if (!center || !saBlock || !symEl) return;
    const centerH = center.offsetHeight;
    saBlock.style.maxHeight = centerH + 'px';
    // Sum actual rendered heights of text rows below the symbol
    let textH = 0;
    ['.sa-cat', '.sa-headline', '.sa-detail'].forEach(sel => {
      const el = saBlock.querySelector(sel);
      if (el) textH += el.offsetHeight + 5; // +5 for margin-top
    });
    if (textH === 0) textH = 52; // fallback before content renders
    const symH = Math.max(24, centerH - textH - 4);
    symEl.style.height    = symH + 'px';
    symEl.style.fontSize  = symH + 'px'; // scales text symbols; SVG fills height via CSS
  }
  fitSaPanel();
  new ResizeObserver(fitSaPanel).observe(document.querySelector('.zulu-center'));
  window.addEventListener('resize', fitSaPanel);
  window.addEventListener('resize', () => { if (missionsData) missionsRender(); });   // press redraws every second anyway

  // launchWithRetry: fires fn immediately (after initialDelayMs), then backs off
  // through RETRY_MS if still degraded, finally handing off to setInterval at normalMs.
  function launchWithRetry(fn, isStillDegraded, normalMs, initialDelayMs) {
    const RETRY_MS = [6000, 18000, 45000, 120000];
    const run = async () => { await fn(); loadStatus(); };
    async function attempt(idx) {
      await run();
      if (isStillDegraded() && idx < RETRY_MS.length) {
        setTimeout(() => attempt(idx + 1), RETRY_MS[idx]);
      } else {
        setInterval(run, normalMs);
      }
    }
    if (initialDelayMs) setTimeout(() => attempt(0), initialDelayMs);
    else attempt(0);
  }

  launchWithRetry(loadAllWx,      () => wxDegraded,         WX_REFRESH_MS);
  launchWithRetry(fetchAllSunsets,() => false,               6 * 60 * 60 * 1000);
  launchWithRetry(loadHeadlines,  () => intelFeedDegraded,   NEWS_REFRESH_MS,  800);
  launchWithRetry(loadSitAware,   () => saDegraded,          SA_REFRESH_MS,    1200);
  launchWithRetry(loadPress,      () => false,               PRESS_REFRESH_MS, 1500);
  launchWithRetry(loadMissions,   () => false,               MISSIONS_REFRESH_MS, 1700);
  setInterval(loadStatus, STATUS_REFRESH_MS);


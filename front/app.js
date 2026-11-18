(function () {
  "use strict";
  /* ============ helpers ============ */
  const $ = (s) => document.querySelector(s);
  const esc = (s) =>
    String(s == null ? "" : s).replace(
      /[&<>"']/g,
      (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
    );
  const pad = (n) => String(n).padStart(2, "0");
  const hh = (h) => pad(h) + ":00";
  const ymd = (d) => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
  const addDays = (d, n) => {
    const x = new Date(d);
    x.setDate(x.getDate() + n);
    return x;
  };
  const MONTHS = ["січ", "лют", "бер", "кві", "тра", "чер", "лип", "сер", "вер", "жов", "лис", "гру"];
  const DOW = ["Нд", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];
  function dateLabel(s) {
    const d = new Date(s + "T00:00");
    const base = d.getDate() + " " + MONTHS[d.getMonth()];
    if (s === ymd(new Date())) return "Сьогодні, " + base;
    if (s === ymd(addDays(new Date(), 1))) return "Завтра, " + base;
    return DOW[d.getDay()] + ", " + base;
  }
  const money = (n) => Number(n).toLocaleString("uk-UA") + " ₴";
  const h32 = (s) => {
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  };
  const ICON = {
    bolt: '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    window: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M12 3v18M4 12h16"/>',
    monitor: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    wifi: '<path d="M2 9a15 15 0 0 1 20 0M5 12.5a10 10 0 0 1 14 0M8.5 16a5 5 0 0 1 7 0M12 19.5h.01"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    book: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h4"/>',
    lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    check: '<path d="M5 12l5 5 9-10"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    pin: '<path d="M12 21s7-6.2 7-11a7 7 0 0 0-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    lib: '<path d="M3 21h18M5 21V10l7-5 7 5v11M9 21v-6h6v6M9 10h6"/>',
    back: '<path d="M15 6l-6 6 6 6"/>',
    temp: '<path d="M14 14.8V5a2 2 0 0 0-4 0v9.8a4 4 0 1 0 4 0z"/>',
    shield: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    card: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18"/>',
    palette:
      '<circle cx="12" cy="12" r="9"/><circle cx="9" cy="9" r="1.2" fill="currentColor" stroke="none"/><circle cx="15" cy="9" r="1.2" fill="currentColor" stroke="none"/><circle cx="9.5" cy="15" r="1.2" fill="currentColor" stroke="none"/><circle cx="15" cy="15" r="1.2" fill="currentColor" stroke="none"/>',
  };
  const ic = (n, s = 16) =>
    `<svg class="ic" width="${(s / 14).toFixed(2)}em" height="${(s / 14).toFixed(2)}em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[n] || ""}</svg>`;

  /* ============ themes ============ */
  const THEMES = {
    default: {
      name: "Океан",
      swatch: "linear-gradient(145deg,#43d6ff,#1f8fe6)",
      vars: {},
    },
    forest: {
      name: "Ліс",
      swatch: "linear-gradient(145deg,#4cf7a0,#1fb878)",
      vars: {
        "--bg": "#0e2318",
        "--panel": "#143021",
        "--panel-2": "#1b3f2c",
        "--plan-bg": "#13291c",
        "--grid": "rgba(130,240,180,.17)",
        "--line": "#24503a",
        "--line-2": "#37785a",
        "--fg": "#f3fff8",
        "--muted": "#b7d9c4",
        "--dim": "#86aa92",
        "--accent": "#4cf7a0",
        "--accent-2": "#1fb878",
        "--accent-ink": "#021a0f",
        "--free": "#5cf0b0",
        "--busy": "#ff7a8a",
        "--mine": "#ffd24a",
        "--closed": "#88a894",
        "--warn": "#ffbe3d",
      },
    },
    sunset: {
      name: "Захід",
      swatch: "linear-gradient(145deg,#c88cff,#8b4fdc)",
      vars: {
        "--bg": "#1a0f2e",
        "--panel": "#26163f",
        "--panel-2": "#341d52",
        "--plan-bg": "#221336",
        "--grid": "rgba(200,160,255,.18)",
        "--line": "#43285c",
        "--line-2": "#5f3a82",
        "--fg": "#fbf7ff",
        "--muted": "#cbb9e3",
        "--dim": "#a48fc0",
        "--accent": "#c88cff",
        "--accent-2": "#8b4fdc",
        "--accent-ink": "#1a0628",
        "--free": "#5ef2c1",
        "--busy": "#ff7288",
        "--mine": "#ffd24a",
        "--closed": "#9a8bb0",
        "--warn": "#ffbe3d",
      },
    },
    light: {
      name: "Світла",
      swatch: "linear-gradient(145deg,#ffffff,#c9d9f5)",
      vars: {
        "color-scheme": "light",
        "--bg": "#eef2fb",
        "--panel": "#ffffff",
        "--panel-2": "#f2f6ff",
        "--plan-bg": "#f5f8ff",
        "--grid": "rgba(30,80,160,.12)",
        "--line": "#cdd9f0",
        "--line-2": "#a8bde0",
        "--fg": "#0f1c3f",
        "--muted": "#4a5a7a",
        "--dim": "#7a88a8",
        "--accent": "#1f7ad1",
        "--accent-2": "#1466b8",
        "--accent-ink": "#ffffff",
        "--free": "#0ea573",
        "--busy": "#e03e5c",
        "--mine": "#d69a00",
        "--closed": "#8896b8",
        "--warn": "#c98600",
      },
    },
  };
  const THEME_KEY = "cospace.theme";
  function currentTheme() {
    try {
      return localStorage.getItem(THEME_KEY) || "default";
    } catch (e) {
      return "default";
    }
  }
  function applyTheme(key) {
    const t = THEMES[key] || THEMES.default;
    const root = document.documentElement;
    const allKeys = new Set();
    Object.values(THEMES).forEach((th) => Object.keys(th.vars).forEach((k) => allKeys.add(k)));
    allKeys.forEach((k) => root.style.removeProperty(k));
    Object.entries(t.vars).forEach(([k, v]) => root.style.setProperty(k, v));
    try {
      localStorage.setItem(THEME_KEY, key);
    } catch (e) {}
    ui.theme = key;
    ui.themeMenu = false;
    renderTop();
  }

  /* ============ catalogue (з БД) ============ */
  const CONTACT = { email: "admin@cospace.ua", phone: "+380 44 123 45 67", tg: "@cospace_admin" };
  const AMEN = {
    wifi: "Wi-Fi",
    kitchen: "Кухня",
    meeting: "Переговорні",
    coffee: "Кава",
    parking: "Паркінг",
    printer: "Принтер",
  };
  const FEAT = { s: "Розетка 220V", w: "Біля вікна", p: "ПК місце" };
  const MAX_DUR = 3;
  const TPL = {
    open: {
      zone: "Зона A: відкритий простір · природне освітлення",
      zone2: "Кухня · кава-пойнт",
      win: 1,
      seats: [
        ["A01", 14, 27, "sw"],
        ["A02", 38, 27, "sw"],
        ["A03", 62, 27, "sw"],
        ["A04", 86, 27, "sw"],
        ["B01", 14, 64, "s"],
        ["B02", 38, 64, "sp"],
        ["B03", 62, 64, "s"],
        ["B04", 86, 64, "sp"],
      ],
    },
    quiet: {
      zone: "Зона B: тиха зона · без розмов",
      zone2: "Вихід до терас",
      win: 1,
      seats: [
        ["A01", 20, 29, "sw"],
        ["A02", 50, 29, "sw"],
        ["A03", 80, 29, "sw"],
        ["B01", 16, 66, "s"],
        ["B02", 42, 66, "s"],
        ["M01", 80, 68, "sp", "room", 6],
      ],
    },
    it: {
      zone: "Зона C: ІТ-зал · робочі станції",
      zone2: "Серверна шафа · обмежений доступ",
      win: 0,
      seats: [
        ["P01", 20, 30, "sp"],
        ["P02", 50, 30, "sp"],
        ["P03", 80, 30, "sp"],
        ["P04", 20, 68, "sp"],
        ["P05", 50, 68, "sp"],
        ["P06", 80, 68, "sp"],
      ],
    },
    meet: {
      zone: "Зона D: переговорні · скляні кімнати",
      zone2: "Рецепція",
      win: 1,
      seats: [
        ["M01", 25, 33, "sp", "room", 6],
        ["M02", 62, 33, "sp", "room", 4],
        ["A01", 22, 72, "sw"],
        ["A02", 50, 72, "s"],
        ["A03", 78, 72, "sw"],
      ],
    },
  };

  let COS = [];
  const CO = {};
  const SEATS = {};
  let CITIES = [];
  let db = {
    users: [],
    bookings: [],
    closed: {},
    requests: [],
    log: [],
    session: null,
  };

  // zone_type из бэкенда: open_space | silent_zone | meeting_room | lecture_hall
  function isRoomType(zone) {
    return zone === "meeting_room" || zone === "lecture_hall";
  }
  const ZONE_PREFIX = { open_space: "A", silent_zone: "S", meeting_room: "M", lecture_hall: "L" };
  function featFrom(w) {
    const t = (String(w.name || "") + " " + String(w.description || "")).toLowerCase();
    return (/розет/.test(t) ? "s" : "") + (/вікн/.test(t) ? "w" : "") + (/монітор|\bпк\b/.test(t) ? "p" : "");
  }
  function capFrom(w) {
    const m = /на\s+(\d+)\s*(осіб|місць)/i.exec(String(w.description || ""));
    return m ? Number(m[1]) : w.zone_type === "lecture_hall" ? 40 : 6;
  }
  // На бэкенде нет списка удобств — выводим из описаний мест
  function deriveAmen(wss) {
    const t = wss.map((w) => (w.name || "") + " " + (w.description || "")).join(" ").toLowerCase();
    const a = [];
    if (/wi-?fi/.test(t)) a.push("wifi");
    if (/кав/.test(t)) a.push("coffee");
    if (wss.some((w) => isRoomType(w.zone_type))) a.push("meeting");
    return a;
  }
  function guessCity(address) {
    const parts = String(address || "")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    return parts.length > 1 ? parts[parts.length - 1] : parts[0] || "Україна";
  }
  function parseAmen(s) {
    const t = (Array.isArray(s) ? s.join(",") : String(s || "")).toLowerCase();
    return Object.keys(AMEN).filter((k) => t.includes(k) || t.includes(AMEN[k].toLowerCase()));
  }

  function buildCatalogue(raw) {
    Object.keys(SEATS).forEach((k) => delete SEATS[k]);
    COS = (raw || []).map((c) => {
      const halls = (c.halls || []).map((h, hi) => ({
        tpl: h.tpl || "open",
        name: h.name,
        seats: (h.seats || []).map((item) => {
          const tuple = Array.isArray(item);
          const s = tuple
            ? {
                id: String(c.id) + ":" + hi + ":" + item[0],
                code: item[0],
                x: item[1],
                y: item[2],
                f: item[3],
                type: item[4] || "desk",
                cap: item[5] || 1,
                co: c.id,
                hall: hi,
              }
            : {
                id: String(item.id),
                code: item.code,
                x: item.x,
                y: item.y,
                f: item.f != null ? item.f : "s",
                type: item.type || "desk",
                cap: item.cap || 1,
                co: c.id,
                hall: hi,
                price: item.price,
                name: item.name,
                zone: item.zone,
              };
          SEATS[s.id] = s;
          if (!tuple && item.open === false) db.closed[s.id] = true;
          else delete db.closed[s.id];
          return s;
        }),
      }));
      return Object.assign({}, c, { halls });
    });
    Object.keys(CO).forEach((k) => delete CO[k]);
    COS.forEach((c) => (CO[c.id] = c));
    CITIES = [...new Set(COS.map((c) => c.city).filter(Boolean))].sort((a, b) =>
      a.localeCompare(b, "uk"),
    );
  }

  // Бэкенд -> модель фронта. Залы строятся по полю floor у рабочих мест.
  function mapCoworkings(list, workspacesByCo) {
    return (list || []).map((c) => {
      const wss = workspacesByCo[c.id] || [];
      const prices = wss.map((w) => Number(w.price_per_hour)).filter((n) => !isNaN(n) && n > 0);
      const groups = {};
      wss.forEach((w) => {
        const k = w.floor || 1;
        (groups[k] = groups[k] || []).push(w);
      });
      const halls = (Object.keys(groups).length ? Object.entries(groups) : [["1", []]])
        .sort((a, b) => Number(a[0]) - Number(b[0]))
        .map(([floor, items]) => {
          const tpl =
            items.length && items.every((w) => isRoomType(w.zone_type))
              ? "meet"
              : items.length && items.every((w) => w.zone_type === "silent_zone")
                ? "quiet"
                : "open";
          const seats = items.map((w, i) => ({
            id: w.id,
            code: (ZONE_PREFIX[w.zone_type] || "W") + w.id,
            name: w.name,
            zone: w.zone_type,
            x: 12 + (i % 5) * 19,
            y: 22 + Math.floor(i / 5) * 22,
            f: featFrom(w),
            type: isRoomType(w.zone_type) ? "room" : "desk",
            cap: isRoomType(w.zone_type) ? capFrom(w) : 1,
            price: Number(w.price_per_hour),
            open: w.is_available !== false,
          }));
          return { tpl, name: "Поверх " + floor, seats };
        });
      const seed = h32(String(c.id) + c.name);
      return {
        id: String(c.id),
        name: c.name,
        address: (c.location && c.location.address) || c.address || "",
        city: guessCity((c.location && c.location.address) || c.address),
        lat: c.location && c.location.latitude,
        lng: c.location && c.location.longitude,
        amen: deriveAmen(wss),
        manager_id: c.manager_id,
        price: prices.length ? Math.min.apply(null, prices) : 80,
        rating: c.rating != null ? Number(c.rating).toFixed(1) : ((40 + (seed % 10)) / 10).toFixed(1),
        reviews: 12 + (seed % 80),
        open: 10,
        close: 22,
        wifi: ["CoSpace-" + c.id, String(10000000 + (seed % 90000000))],
        halls,
      };
    });
  }

  /* ============ persistence (FastAPI backend) ============ */
  const API_BASE = "http://127.0.0.1:8000";
  const API = {
    login: "/auth/login",
    me: "/auth/me",
    coworkings: "/coworkings",
    bookings: "/bookings",
    pay: "/payments/process",
    // На бэкенде пока нет эндпоинтов для: списка броней, отмены/редактирования,
    // закрытия столов, заявок менеджеров, списка пользователей, журнала.
    // Эти функции работают локально, в памяти страницы.
  };
  const TOKEN_KEY = "cospace.token";
  const PROFILE_KEY = "cospace.profiles";
  const ROLE_IN = { Client: "client", SpaceManager: "manager", PlatformAdmin: "admin" };

  function getToken() {
    try {
      return localStorage.getItem(TOKEN_KEY) || "";
    } catch (e) {
      return "";
    }
  }
  function setToken(t) {
    try {
      if (t) localStorage.setItem(TOKEN_KEY, t);
      else localStorage.removeItem(TOKEN_KEY);
    } catch (e) {}
  }
  function profiles() {
    try {
      return JSON.parse(localStorage.getItem(PROFILE_KEY) || "{}");
    } catch (e) {
      return {};
    }
  }
  function errDetail(data, status) {
    const d = data && data.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) return d.map((x) => x.msg || JSON.stringify(x)).join("; ");
    return "Помилка запиту (" + status + ")";
  }
  async function api(path, opts) {
    if (!path) throw new Error("no endpoint");
    const headers = Object.assign({}, opts && opts.headers);
    if (opts && opts.body != null && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
    const tok = getToken();
    if (tok) headers.Authorization = "Bearer " + tok;
    return fetch(API_BASE + path, Object.assign({}, opts, { headers }));
  }
  async function apiJson(path, opts) {
    const r = await api(path, opts);
    if (r.status === 204) return null;
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      const err = new Error(errDetail(data, r.status));
      err.status = r.status;
      err.data = data;
      throw err;
    }
    return data;
  }
  function isoFrom(date, hour) {
    return date + "T" + pad(hour) + ":00:00";
  }
  function mapUser(u) {
    if (!u) return null;
    const extra = profiles()[u.id] || {};
    const email = u.email || u.username || "";
    const managed = COS.find((c) => c.manager_id === u.id);
    return {
      id: u.id,
      email,
      name: extra.name || u.full_name || u.name || (email || "user").split("@")[0],
      phone: extra.phone || u.phone_number || u.phone || "—",
      role: ROLE_IN[u.role] || "client",
      coId: extra.coId || (managed ? managed.id : null),
      is_blocked: !!u.is_blocked,
      is_email_verified: true,
    };
  }
  async function hydrateMe() {
    return mapUser(await apiJson(API.me));
  }
  async function loadRoleData() {}
  function mapStatus(s) {
    const m = { Pending: "pending", Confirmed: "confirmed", Completed: "completed", Cancelled: "cancelled" };
    return m[s] || String(s || "pending").toLowerCase();
  }
  // hint.dur: бэкенд может вернуть end_time == start_time, поэтому длительность передаём явно
  function mapBooking(b, hint) {
    hint = hint || {};
    const start = new Date(b.start_time);
    const seat = SEATS[String(b.workspace_id)];
    const dur =
      hint.dur || Math.max(1, Math.round((new Date(b.end_time) - start) / 3600000) || 1);
    const price = seat ? seatPrice(seat, dur) : Number(b.total_price) || 0;
    return {
      id: String(b.id),
      code: "CS-" + b.id,
      coId: seat ? seat.co : b.coworking_id != null ? String(b.coworking_id) : null,
      seatId: String(b.workspace_id),
      userId: b.user_id,
      email: (me() || {}).email,
      date: ymd(start),
      start: start.getHours(),
      dur,
      price,
      status: mapStatus(b.status),
      cancelRequested: false,
      refundPct: null,
      guest: null,
    };
  }
  function upsertUser(u) {
    const i = db.users.findIndex((x) => x.id === u.id);
    if (i >= 0) db.users[i] = Object.assign({}, db.users[i], u);
    else db.users.push(u);
    return db.users.find((x) => x.id === u.id);
  }

  function save() {}

  /* ============ ui state ============ */
  const ui = {
    view: "map",
    coId: null,
    hall: 0,
    date: null,
    start: 10,
    dur: 2,
    f: { q: "", city: "", type: "", price: 120, amen: [] },
    attr: [],
    manage: false,
    menu: false,
    theme: currentTheme(),
    themeMenu: false,
    filtersOpen: false,
    drawer: null,
    modal: null,
    cabTab: "now",
    mgrTab: "bookings",
    admTab: "users",
    mgrFilter: "all",
    tempCache: {},
  };
  const def = (() => {
    const n = new Date();
    let date = ymd(n),
      start = n.getHours() + 1;
    if (start < 10) start = 10;
    if (start > 19) {
      date = ymd(addDays(n, 1));
      start = 10;
    }
    return { date, start };
  })();
  ui.date = def.date;
  ui.start = def.start;

  const me = () => db.users.find((u) => u.id === db.session) || null;
  const userById = (id) => db.users.find((u) => String(u.id) === String(id));
  const ROLE = { client: "Клієнт", manager: "Менеджер", admin: "Адміністратор" };
  const curCo = () => CO[ui.coId];
  const typeLabel = (s) =>
    s.zone === "lecture_hall" ? "Івент-зал" : s.type === "room" ? "Переговорна" : "Робоче місце";
  const hourPrice = (seat) =>
    seat.price != null && !isNaN(seat.price)
      ? Number(seat.price)
      : (CO[seat.co] ? CO[seat.co].price : 80) * (seat.type === "room" ? 4 : 1);
  const seatPrice = (seat, dur) => hourPrice(seat) * dur;

  /* ============ domain logic ============ */
  const startTs = (b) => new Date(b.date + "T" + pad(b.start) + ":00").getTime();
  const endTs = (b) => startTs(b) + b.dur * 3600000;
  const stOf = (b) => (b.status === "confirmed" && endTs(b) < Date.now() ? "completed" : b.status);
  const STATUS = {
    pending: "Очікує оплати",
    confirmed: "Підтверджено",
    completed: "Завершено",
    cancelled: "Скасовано",
  };
  const isActive = (b) =>
    b.status === "confirmed" || (b.status === "pending" && b.expiresAt > Date.now());

  function sweep() {
    let ch = false;
    db.bookings.forEach((b) => {
      if (b.status === "pending" && b.expiresAt <= Date.now()) {
        b.status = "cancelled";
        b.reason = "Минув час на оплату";
        ch = true;
      }
    });
    if (ch) save();
  }

  const overlap = (a0, ad, b0, bd) => a0 < b0 + bd && b0 < a0 + ad;

  function bookedBy(seatId, date, start, dur, excludeId) {
    return db.bookings.find(
      (b) =>
        b.id !== excludeId &&
        b.seatId === seatId &&
        b.date === date &&
        isActive(b) &&
        overlap(start, dur, b.start, b.dur),
    );
  }

  function conflict(seat, date, start, dur, excludeId) {
    if (db.closed[seat.id]) return "closed";
    if (bookedBy(seat.id, date, start, dur, excludeId)) return "busy";
    return null;
  }

  function seatState(seat) {
    const co = CO[seat.co];
    if (db.closed[seat.id]) return "closed";
    if (!slotOk(co)) return "busy";
    const u = me();
    if (u) {
      const mine = bookedBy(seat.id, ui.date, ui.start, ui.dur);
      if (mine && mine.userId === u.id) return "mine";
    }
    return conflict(seat, ui.date, ui.start, ui.dur) ? "busy" : "free";
  }

  function minStart(co, date) {
    const n = new Date();
    return date === ymd(n) ? Math.max(co.open, n.getHours() + 1) : co.open;
  }

  function slotOk(co) {
    return ui.start >= minStart(co, ui.date) && ui.start + ui.dur <= co.close;
  }

  function fixSlot() {
    const co = curCo();
    if (!co) return;
    let min = minStart(co, ui.date),
      max = co.close - ui.dur;
    if (min > max && ui.date === ymd(new Date())) {
      ui.date = ymd(addDays(new Date(), 1));
      min = co.open;
    }
    ui.start = Math.min(Math.max(ui.start, min), max);
  }

  function freeIn(co) {
    return co.halls
      .flatMap((h) => h.seats)
      .filter((s) => (!ui.f.type || s.type === ui.f.type) && seatState(s) === "free").length;
  }

  function refundPct(b) {
    if (b.status !== "confirmed") return 0;
    const h = (startTs(b) - Date.now()) / 3600000;
    return h >= 24 ? 100 : h >= 2 ? 50 : 0;
  }

  function logAct(text) {
    const u = me();
    if (!u || u.role === "client") return;
    db.log.unshift({ ts: Date.now(), actor: u.name, role: u.role, text });
    db.log = db.log.slice(0, 200);
  }

  const bkName = (b) => {
    if (b.userId) {
      const u = userById(b.userId);
      if (u && u.name) return u.name;
      if (b.email) return b.email.split("@")[0];
    }
    return (b.guest && b.guest.name) || "—";
  };
  const bkPhone = (b) =>
    b.userId ? (userById(b.userId) || {}).phone || "" : (b.guest && b.guest.phone) || "";

  const myActive = () => {
    const u = me();
    return u
      ? db.bookings.filter(
          (b) =>
            b.userId === u.id &&
            ((stOf(b) === "pending" && isActive(b)) || stOf(b) === "confirmed"),
        ).length
      : 0;
  };

  // Отмена на бэкенде пока не реализована — меняем только локальное состояние
  function cancelBooking(b, note) {
    const pct = refundPct(b);
    const paid = b.status === "confirmed";
    b.status = "cancelled";
    b.refundPct = paid ? pct : null;
    b.cancelRequested = false;
    if (note) b.reason = note;
    save();
    return pct;
  }

  /* ============ toasts ============ */
  function toast(msg, kind) {
    const el = document.createElement("div");
    el.className = "toast " + (kind || "");
    el.textContent = msg;
    $("#toasts").appendChild(el);
    setTimeout(() => el.remove(), 3800);
  }

  /* ============ temperature API ============ */
  async function fetchTemperature(coId) {
    const now = Date.now();
    const c = ui.tempCache[coId];
    if (c && now - c.ts < 60000) return c.value;
    const v = 20 + (h32(String(coId) + ymd(new Date())) % 7);
    ui.tempCache[coId] = { value: v, ts: now };
    return v;
  }

  /* ============ render: top / side / status ============ */
  function renderTop() {
    const u = me();
    let total = 0,
      free = 0;
    COS.forEach((c) => {
      c.halls.forEach((h) =>
        h.seats.forEach((s) => {
          total++;
          if (seatState(s) === "free") free++;
        }),
      );
    });
    const n = myActive();
    const themeMenu = ui.themeMenu
      ? `<div class="theme-menu" role="menu">${Object.entries(THEMES)
          .map(
            ([k, v]) =>
              `<button type="button" data-act="theme-set" data-k="${k}" class="${ui.theme === k ? "on" : ""}" role="menuitem"><span class="theme-swatch" style="background:${v.swatch}"></span>${v.name}</button>`,
          )
          .join("")}</div>`
      : "";
    $("#top").innerHTML = `
   <button class="brand" data-act="home" aria-label="CoSpace — до карти"><span class="brand-mark">${ic("lib", 24)}</span><span><b>CoSpace</b><small>Сервіс бронювання коворкінгів</small></span></button>
   <span class="stat hide-m"><span class="dot"></span>Онлайн-оплата</span>
   <span class="stat keep" title="${dateLabel(ui.date)}, ${hh(ui.start)}–${hh(ui.start + ui.dur)}">Вільні місця: <b>${free} / ${total}</b></span>
   <div class="theme-wrap">
     <button class="theme-btn" data-act="theme-toggle" title="Тема оформлення" aria-haspopup="true" aria-expanded="${ui.themeMenu}">${ic("palette", 18)}</button>
     ${themeMenu}
   </div>
   <button class="mybook" data-act="cabinet">${ic("book")}<span>Мої бронювання</span><span class="badge-n">${n}</span></button>
   ${
     u
       ? `<div class="acct"><button class="acct-btn" data-act="menu" aria-haspopup="true" aria-expanded="${ui.menu}">
        <span class="avatar">${esc(
          u.name
            .split(" ")
            .map((w) => w[0])
            .slice(0, 2)
            .join("")
            .toUpperCase(),
        )}</span>
        <span><b>${esc(u.name)}</b><small>${ROLE[u.role]} · ${esc(u.email)}</small></span></button>
        ${
          ui.menu
            ? `<div class="menu" role="menu">
          <button data-act="cabinet">${ic("book")} Мої бронювання</button>
          ${u.role === "manager" ? `<button data-act="manager">${ic("pin")} Панель менеджера</button>` : ""}
          ${u.role === "admin" ? `<button data-act="admin">${ic("shield")} Панель адміністратора</button>` : ""}
          <hr><button data-act="logout">${ic("x")} Вийти</button></div>`
            : ""
        }</div>`
       : `<button class="btn primary" data-act="login">${ic("user")} Увійти</button>`
   }`;
  }

  function filtered() {
    const f = ui.f;
    return COS.filter(
      (c) =>
        (!f.city || c.city === f.city) &&
        (!f.q || (c.name + " " + c.city + " " + c.address).toLowerCase().includes(f.q)) &&
        c.price <= f.price &&
        f.amen.every((a) => c.amen.includes(a)) &&
        (!f.type || c.halls.some((h) => h.seats.some((s) => s.type === f.type))),
    );
  }

  function renderSide() {
    const list = filtered();
    if (list.length && !list.find((c) => c.id === ui.coId)) {
      ui.coId = list[0].id;
      ui.hall = 0;
      fixSlot();
      if (ui.coId) fetchTemperature(ui.coId).then(() => renderStatus());
    }
    const countEl = $("#count");
    if (countEl) countEl.textContent = list.length + " з " + COS.length;
    $("#list").innerHTML = list.length
      ? list
          .map((c) => {
            const fr = freeIn(c),
              ok = slotOk(c);
            return `<button class="co ${c.id === ui.coId ? "sel" : ""}" data-act="pick-co" data-id="${c.id}">
      <span class="co-top"><b>${esc(c.name)}</b><span class="free ${!ok ? "off" : fr ? "" : "none"}">${!ok ? "зачинено" : fr ? fr + " вільно" : "немає місць"}</span></span>
      <span class="co-meta"><span>${ic("pin", 12)} ${esc(c.city)}, ${esc(c.address)}</span></span>
      <span class="co-foot"><span>від ${c.price} ₴/год</span><span>★ ${c.rating} (${c.reviews})</span></span></button>`;
          })
          .join("")
      : `<div class="empty"><b>Нічого не знайдено</b><span>Змініть місто, ціну або зручності.</span><button class="btn sm" data-act="reset-filters">Скинути фільтри</button></div>`;
    const co = curCo();
    const halls = $("#halls");
    if (halls) {
      halls.innerHTML =
        list.length && co
          ? `<span>Зали</span>` +
            co.halls
              .map(
                (h, i) =>
                  `<button class="hall-btn ${i === ui.hall ? "on" : ""}" data-act="hall" data-i="${i}">${esc(h.name)}</button>`,
              )
              .join("")
          : "";
      halls.style.display = list.length ? "" : "none";
    }
    const amenEl = $("#f-amen");
    if (amenEl)
      amenEl.innerHTML = Object.keys(AMEN)
        .map(
          (k) =>
            `<button class="chip ${ui.f.amen.includes(k) ? "on" : ""}" data-act="amen" data-k="${k}">${AMEN[k]}</button>`,
        )
        .join("");
    const priceV = $("#f-price-v");
    if (priceV) priceV.textContent = ui.f.price >= 120 ? "будь-яка" : ui.f.price + " ₴/год";
  }

  function renderStatus() {
    const co = curCo();
    if (!co) return;
    const sockets = co.halls.flatMap((h) => h.seats).filter((s) => s.f.includes("s"));
    const act = sockets.length
      ? Math.round((sockets.filter((s) => !db.closed[s.id]).length / sockets.length) * 100)
      : 100;
    const temp = ui.tempCache[co.id] ? ui.tempCache[co.id].value : null;
    const tempTxt = temp == null ? "—" : temp + "°C";
    $("#status").innerHTML =
      `<span>${ic("wifi", 14)} Wi-Fi: <b>${esc(co.wifi[0])} (${esc(co.wifi[1])})</b></span>
   <span class="ok">${ic("bolt", 14)} Статус розеток: <b>${act}% активні</b></span>
   <span>${ic("temp", 14)} Температура: <b>${tempTxt}</b></span>
   <span>${ic("clock", 14)} Години роботи: <b>${hh(co.open)}–${hh(co.close)}</b></span>
   <span class="r">Максимальний слот: <b>${MAX_DUR} години</b></span>`;
  }

  /* ============ render: map ============ */
  function slotControls(prefix) {
    const co = curCo();
    if (!co) return "";
    const dates = [];
    for (let i = 0; i < 14; i++) dates.push(ymd(addDays(new Date(), i)));
    const min = minStart(co, ui.date),
      max = co.close - ui.dur;
    const starts = [];
    for (let h = min; h <= max; h++) starts.push(h);
    return `<div class="f"><label for="${prefix}date">Дата</label><select id="${prefix}date" data-bind="date">${dates.map((d) => `<option value="${d}" ${d === ui.date ? "selected" : ""}>${dateLabel(d)}</option>`).join("")}</select></div>
   <div class="f"><label for="${prefix}start">Початок</label><select id="${prefix}start" data-bind="start">${starts.length ? starts.map((h) => `<option value="${h}" ${h === ui.start ? "selected" : ""}>${hh(h)}</option>`).join("") : "<option>—</option>"}</select></div>
   <div class="f"><label for="${prefix}dur">Тривалість</label><select id="${prefix}dur" data-bind="dur">${[1, 2, 3].map((d) => `<option value="${d}" ${d === ui.dur ? "selected" : ""}>${d} год</option>`).join("")}</select></div>`;
  }

  function renderMap() {
    const co = curCo();
    if (!co || !filtered().length) {
      return `<div class="main-scroll"><div class="empty" style="padding-top:5.0rem"><b>Немає коворкінгів за вибраними фільтрами</b><span>Скиньте фільтри, щоб побачити всі локації.</span><button class="btn primary" data-act="reset-filters">Скинути фільтри</button></div></div>`;
    }
    const hall = co.halls[ui.hall] || co.halls[0],
      tpl = TPL[hall.tpl],
      u = me();
    const canManage = u && (u.role === "admin" || (u.role === "manager" && u.coId === co.id));
    const rooms = hall.seats.filter((s) => s.type === "room").length,
      desks = hall.seats.length - rooms;
    const seatsHtml = hall.seats
      .map((s) => {
        const st = seatState(s);
        const dim = ui.attr.length && !ui.attr.every((a) => s.f.includes(a));
        const status =
          st === "free"
            ? "Вільне"
            : st === "mine"
              ? "Ваше бронювання"
              : st === "closed"
                ? "Запис закрито менеджером"
                : "Зайняте";
        const b = [..."wsp"]
          .filter((k) => s.f.includes(k))
          .map(
            (k) =>
              `<i class="b ${k}" title="${FEAT[k]}">${ic(k === "s" ? "bolt" : k === "w" ? "window" : "monitor", 10)}</i>`,
          )
          .join("");
        const lock = st === "closed" ? `<i class="lk">${ic("lock", 10)}</i>` : "";
        return `<button class="seat ${s.type === "room" ? "room" : ""} ${st} ${dim ? "dim" : ""}" style="left:${s.x}%;top:${s.y}%" data-act="seat" data-id="${s.id}" aria-label="${typeLabel(s)} ${s.code}: ${status}">
      <span>${s.code}${s.type === "room" ? `<small>${s.cap} осіб</small>` : ""}</span>${b}${lock}
      <span class="tip"><b>${s.code} · ${typeLabel(s)}</b><br>${s.name ? esc(s.name) + "<br>" : ""}${status}${st === "free" || st === "mine" ? ` · ${money(seatPrice(s, ui.dur))}` : ""}<br>${[
        ..."swp",
      ]
        .filter((k) => s.f.includes(k))
        .map((k) => FEAT[k])
        .join(", ")}</span></button>`;
      })
      .join("");
    const slotTxt = slotOk(co)
      ? `<b>${dateLabel(ui.date)}</b>, ${hh(ui.start)}–${hh(ui.start + ui.dur)}`
      : "<b>Немає вільних годин на цю дату</b>";
    return `<div class="main-scroll">
   <div class="main-head">
     <div><h1>${esc(co.name)}: ${esc(hall.name)} <span class="zone-badge">${desks ? desks + " " + (desks === 1 ? "робоче місце" : "робочих місць") : ""}${desks && rooms ? " · " : ""}${rooms ? rooms + " " + (rooms === 1 ? "переговорна" : "переговорні") : ""}</span></h1>
       <p>${esc(co.city)}, ${esc(co.address)} · ★ ${co.rating} · оберіть зручний стіл на плані зали для бронювання слота</p></div>
     <div class="legend">
       ${Object.keys(FEAT)
         .map(
           (k) =>
             `<button class="chip ${ui.attr.includes(k) ? "on" : ""}" data-act="attr" data-k="${k}">${ic(k === "s" ? "bolt" : k === "w" ? "window" : "monitor", 14)} ${FEAT[k]}</button>`,
         )
         .join("")}
       <span><i style="background:var(--free)"></i>Вільне</span><span><i style="background:var(--busy)"></i>Зайнято</span><span><i style="background:var(--mine)"></i>Ваше</span></div>
   </div>
   <div class="slotbar">${slotControls("m-")}<div class="sum">${slotTxt}${slotOk(co) ? ` · <b>${freeIn(co)}</b> вільно в коворкінгу` : ""}</div>
     ${canManage ? `<button class="btn ${ui.manage ? "primary" : ""}" data-act="manage">${ic("lock", 14)} ${ui.manage ? "Завершити керування" : "Керувати столами"}</button>` : ""}</div>
   ${ui.manage ? `<div class="manage-note">${ic("lock")} Режим керування: натисніть на стіл, щоб закрити або відкрити запис на нього.</div>` : ""}
   <div class="plan ${ui.manage ? "managing" : ""}">
     ${tpl.win ? '<div class="win"></div>' : ""}
     <div class="zl tl">[ ${esc(tpl.zone)} ]</div><div class="zl br">[ ${esc(tpl.zone2)} ]</div><div class="zl bl">[ вхід ]</div>
     ${seatsHtml}
   </div></div>`;
  }

  /* ============ render: cabinet / manager / admin ============ */
  function bkCard(b, mode) {
    const co = CO[b.coId],
      seat = SEATS[b.seatId],
      st = stOf(b);
    const left = b.expiresAt ? Math.max(0, Math.ceil((b.expiresAt - Date.now()) / 60000)) : 0;
    let acts = "";
    if (mode === "client") {
      if (st === "pending")
        acts = `<button class="btn primary sm" data-act="pay-bk" data-id="${b.id}">${ic("card", 14)} Оплатити</button><button class="btn danger sm" data-act="cancel-pending" data-id="${b.id}">Скасувати</button>`;
      else if (st === "confirmed" && !b.cancelRequested)
        acts = `<button class="btn sm" data-act="req-cancel" data-id="${b.id}">Запит на скасування</button>`;
      else if (st === "confirmed" && b.cancelRequested)
        acts = `<span class="pill req">Запит надіслано · менеджер зателефонує вам</span>`;
    }
    const coName = co ? co.name : "Коворкінг";
    const seatCode = seat ? seat.code : "місце";
    return `<div class="bk"><div><h4>${esc(coName)} · ${esc(seatCode)}</h4>
     <div class="meta"><span>${ic("clock", 13)} <b>${dateLabel(b.date)}, ${hh(b.start)}–${hh(b.start + b.dur)}</b></span><span>${esc(co ? co.city : "")}${co ? ", " + esc(co.address) : ""}</span><span>${seat ? typeLabel(seat) : ""}</span><span class="code">${b.code}</span></div>
     ${st === "pending" ? `<div class="meta"><span style="color:var(--warn)">Місце утримується ще ~${left} хв</span></div>` : ""}
     ${st === "cancelled" ? `<div class="meta"><span>${b.reason ? esc(b.reason) + ". " : ""}${b.refundPct != null ? "Повернення коштів: <b>" + b.refundPct + "%</b>" : ""}</span></div>` : ""}</div>
     <div style="text-align:right;display:grid;gap:0.375rem;justify-items:end"><span class="pill ${st}">${STATUS[st]}</span><b class="mono">${money(b.price)}</b></div>
     ${acts ? `<div class="act">${acts}</div>` : ""}</div>`;
  }

  function renderCabinet() {
    const u = me();
    if (!u) return "";
    const mine = db.bookings.filter((b) => b.userId === u.id);
    const now = mine
      .filter((b) => {
        const s = stOf(b);
        return s === "confirmed" || s === "pending";
      })
      .sort((a, b) => startTs(a) - startTs(b));
    const hist = mine
      .filter((b) => {
        const s = stOf(b);
        return s === "completed" || s === "cancelled";
      })
      .sort((a, b) => startTs(b) - startTs(a));
    const list = ui.cabTab === "now" ? now : hist;
    const req = db.requests.find((r) => r.userId === u.id && r.status === "new");
    return `<div class="main-scroll"><div class="page-head"><button class="btn sm" data-act="home">${ic("back", 14)} До карти</button><h1>Мої бронювання</h1></div>
   <div class="cols"><div style="display:grid;gap:0.875rem"><div class="card"><h3>Акаунт</h3><div class="kv">
      <div><span>ПІБ</span>${esc(u.name)}</div><div><span>Телефон</span>${esc(u.phone)}</div><div><span>Пошта</span>${esc(u.email)}</div>
      <div><span>Роль</span><span class="pill role" style="width:fit-content;color:var(--accent)">${ROLE[u.role]}</span></div></div></div>
      ${req ? `<div class="note"><b>Заявка власника коворкінгу на розгляді.</b><br>«${esc(req.coName)}». Права менеджера надає адміністратор платформи. Напишіть або зателефонуйте йому: ${esc(CONTACT.email)}, ${esc(CONTACT.phone)}, ${esc(CONTACT.tg)}.</div>` : ""}
      <div class="note"><b>Правила скасування.</b> Скасувати підтверджену броню можна через запит. Менеджер зателефонує вам. Повернення коштів: 100% за 24 год і більше, 50% за 2–24 год, 0% пізніше.</div></div>
    <div><div class="tabs"><button class="tab ${ui.cabTab === "now" ? "on" : ""}" data-act="cab-tab" data-t="now">Поточні (${now.length})</button><button class="tab ${ui.cabTab === "hist" ? "on" : ""}" data-act="cab-tab" data-t="hist">Історія замовлень (${hist.length})</button></div>
      ${list.length ? list.map((b) => bkCard(b, "client")).join("") : `<div class="empty card"><b>${ui.cabTab === "now" ? "Поточних бронювань немає" : "Історія порожня"}</b><span>${ui.cabTab === "now" ? "Оберіть коворкінг зліва та вільний стіл на плані." : "Завершені й скасовані бронювання з’являться тут."}</span><button class="btn primary" data-act="home">Знайти місце</button></div>`}</div></div></div>`;
  }

  function renderManager() {
    const u = me();
    if (!u || u.role !== "manager") return "";
    const co = CO[u.coId] || COS[0];
    if (!co) return "";
    const all = db.bookings.filter((b) => b.coId === co.id).sort((a, b) => startTs(b) - startTs(a));
    const reqs = all.filter((b) => b.cancelRequested && b.status === "confirmed");
    const upcoming = all.filter((b) => stOf(b) === "confirmed").length;
    const today = all.filter((b) => b.date === ymd(new Date()) && isActive(b)).length;
    const rows = ui.mgrFilter === "req" ? reqs : all;
    const closedN = co ? co.halls.flatMap((h) => h.seats).filter((s) => db.closed[s.id]).length : 0;
    return `<div class="main-scroll"><div class="page-head"><button class="btn sm" data-act="home">${ic("back", 14)} До карти</button><h1>Панель менеджера · ${esc(co ? co.name : "")}</h1>
     <button class="btn" data-act="go-manage">${ic("lock", 14)} Керувати столами</button><button class="btn primary" data-act="manual-bk">Зафіксувати бронювання</button></div>
   <div class="kpis"><div class="kpi"><span>Підтверджені попереду</span><b>${upcoming}</b></div><div class="kpi"><span>Сьогодні</span><b>${today}</b></div><div class="kpi"><span>Запити на скасування</span><b>${reqs.length}</b></div><div class="kpi"><span>Закриті столи</span><b>${closedN}</b></div></div>
   <div class="tabs"><button class="tab ${ui.mgrFilter === "all" ? "on" : ""}" data-act="mgr-filter" data-t="all">Усі бронювання (${all.length})</button><button class="tab ${ui.mgrFilter === "req" ? "on" : ""}" data-act="mgr-filter" data-t="req">Запити на скасування${reqs.length ? `<span class="badge-n">${reqs.length}</span>` : ""}</button></div>
   ${
     rows.length
       ? `<div class="tw"><table><thead><tr><th>Код</th><th>Місце</th><th>Клієнт</th><th>Дата і час</th><th>Статус</th><th>Сума</th><th></th></tr></thead><tbody>${rows
           .map((b) => {
             const st = stOf(b),
               seat = SEATS[b.seatId];
             const canEdit = st === "confirmed" || st === "pending";
             const canCancel = st === "confirmed" && (b.cancelRequested || !b.userId);
             return `<tr><td class="mono">${b.code}</td><td>${seat ? seat.code : "—"}<span class="sub">${seat && co ? esc(co.halls[seat.hall].name) : ""}</span></td>
      <td>${esc(bkName(b))}<span class="sub">${esc(bkPhone(b))}</span></td><td>${dateLabel(b.date)}<span class="sub">${hh(b.start)}–${hh(b.start + b.dur)}</span></td>
      <td><span class="pill ${st}">${STATUS[st]}</span>${b.cancelRequested && st === "confirmed" ? `<br><span class="pill req" style="margin-top:0.25rem">Запит на скасування</span>` : ""}</td><td class="mono">${money(b.price)}</td>
      <td class="acts">${canEdit ? `<button class="btn sm" data-act="edit-bk" data-id="${b.id}">Редагувати</button>` : ""}${canCancel ? `<button class="btn sm danger" data-act="mgr-cancel" data-id="${b.id}">Скасувати</button>` : st === "confirmed" ? `<button class="btn sm" disabled title="Скасування можливе після запиту клієнта">Скасувати</button>` : ""}</td></tr>`;
           })
           .join("")}</tbody></table></div>`
       : `<div class="empty card"><b>Запитів на скасування немає</b><span>Коли клієнт попросить скасувати броню, вона з’явиться тут.</span></div>`
   }
   <p class="hint" style="margin-top:0.625rem">Скасувати підтверджену броню клієнта можна лише після його запиту в сервісі та дзвінка для уточнення.</p></div>`;
  }

  function renderAdmin() {
    const u = me();
    if (!u || u.role !== "admin") return "";
    const reqs = db.requests.filter((r) => r.status === "new");
    const tabs = [
      ["users", "Користувачі (" + db.users.length + ")"],
      [
        "reqs",
        "Заявки менеджерів" + (reqs.length ? `<span class="badge-n">${reqs.length}</span>` : ""),
      ],
      ["all", "Усі бронювання (" + db.bookings.length + ")"],
      ["log", "Журнал дій"],
    ];
    let body = "";
    if (ui.admTab === "users") {
      body = `<div class="tw"><table><thead><tr><th>Користувач</th><th>Телефон</th><th>Роль</th><th>Коворкінг</th></tr></thead><tbody>${db.users
        .map(
          (x) =>
            `<tr><td>${esc(x.name)}<span class="sub">${esc(x.email)}</span></td><td>${esc(x.phone)}</td>
      <td>${x.role === "admin" ? `<span class="pill role">${ROLE.admin}</span>` : `<select data-role="${x.id}" aria-label="Роль ${esc(x.name)}" style="width:auto"><option value="client" ${x.role === "client" ? "selected" : ""}>Клієнт</option><option value="manager" ${x.role === "manager" ? "selected" : ""}>Менеджер</option></select>`}</td>
      <td>${x.role === "admin" ? "—" : `<select data-co="${x.id}" aria-label="Коворкінг ${esc(x.name)}" style="width:auto" ${x.role !== "manager" ? "disabled" : ""}><option value="">—</option>${COS.map((c) => `<option value="${c.id}" ${x.coId === c.id ? "selected" : ""}>${esc(c.name)}</option>`).join("")}</select>`}</td></tr>`,
        )
        .join("")}</tbody></table></div>`;
    }
    if (ui.admTab === "reqs") {
      const all = db.requests.slice().sort((a, b) => b.ts - a.ts);
      body = all.length
        ? all
            .map((r) => {
              const x = userById(r.userId);
              return `<div class="bk"><div><h4>${esc(r.coName)}${r.city ? `, ${esc(r.city)}` : ""}</h4><div class="meta"><span>Заявник: <b>${esc(x ? x.name : "—")}</b></span><span>${esc(x ? x.email : "")}</span><span>${esc(x ? x.phone : "")}</span></div></div>
      <div><span class="pill ${r.status === "new" ? "req" : r.status === "approved" ? "confirmed" : "cancelled"}">${r.status === "new" ? "Очікує" : r.status === "approved" ? "Схвалено" : "Відхилено"}</span></div>
      ${r.status === "new" ? `<div class="act"><label class="hint" for="rc-${r.id}">Призначити коворкінг</label><select id="rc-${r.id}" style="width:auto">${COS.map((c) => `<option value="${c.id}">${esc(c.name)} (${esc(c.city)})</option>`).join("")}</select><button class="btn primary sm" data-act="approve" data-id="${r.id}">Надати права менеджера</button><button class="btn danger sm" data-act="reject" data-id="${r.id}">Відхилити</button></div>` : ""}</div>`;
            })
            .join("")
        : `<div class="empty card"><b>Заявок немає</b><span>Власники коворкінгів реєструються як клієнти й залишають заявку.</span></div>`;
    }
    if (ui.admTab === "all") {
      const rows = db.bookings.slice().sort((a, b) => startTs(b) - startTs(a));
      body = `<div class="tw"><table><thead><tr><th>Код</th><th>Коворкінг</th><th>Клієнт</th><th>Дата і час</th><th>Статус</th><th></th></tr></thead><tbody>${rows
        .map((b) => {
          const st = stOf(b);
          const co = CO[b.coId];
          const seat = SEATS[b.seatId];
          return `<tr><td class="mono">${b.code}</td><td>${co ? esc(co.name) : "—"}<span class="sub">${seat ? seat.code : ""}</span></td><td>${esc(bkName(b))}</td><td>${dateLabel(b.date)}<span class="sub">${hh(b.start)}–${hh(b.start + b.dur)}</span></td><td><span class="pill ${st}">${STATUS[st]}</span></td>
      <td class="acts">${st === "confirmed" || st === "pending" ? `<button class="btn sm" data-act="edit-bk" data-id="${b.id}">Редагувати</button><button class="btn sm danger" data-act="adm-cancel" data-id="${b.id}">Скасувати</button>` : ""}</td></tr>`;
        })
        .join("")}</tbody></table></div>`;
    }
    if (ui.admTab === "log") {
      body = db.log.length
        ? `<div class="tw"><table><thead><tr><th>Час</th><th>Хто</th><th>Дія</th></tr></thead><tbody>${db.log
            .map((l) => {
              const d = new Date(l.ts);
              return `<tr><td class="mono" style="white-space:nowrap">${pad(d.getDate())}.${pad(d.getMonth() + 1)} ${pad(d.getHours())}:${pad(d.getMinutes())}</td><td>${esc(l.actor)}<span class="sub">${ROLE[l.role]}</span></td><td>${esc(l.text)}</td></tr>`;
            })
            .join("")}</tbody></table></div>`
        : `<div class="empty card"><b>Журнал порожній</b></div>`;
    }
    return `<div class="main-scroll"><div class="page-head"><button class="btn sm" data-act="home">${ic("back", 14)} До карти</button><h1>Панель адміністратора</h1></div>
   <div class="tabs">${tabs.map(([k, l]) => `<button class="tab ${ui.admTab === k ? "on" : ""}" data-act="adm-tab" data-t="${k}">${l}</button>`).join("")}</div>${body}</div>`;
  }

  function renderMain() {
    const wide = ui.view !== "map";
    $("#shell").classList.toggle("wide", wide);
    $("#main").innerHTML =
      ui.view === "cabinet"
        ? renderCabinet()
        : ui.view === "manager"
          ? renderManager()
          : ui.view === "admin"
            ? renderAdmin()
            : renderMap();
  }

  function renderAll() {
    sweep();
    renderTop();
    renderSide();
    renderMain();
    renderStatus();
  }

  /* ============ drawer: booking flow (4 кроки) ============ */
  let holdTimer = null;
  function closeDrawer() {
    clearInterval(holdTimer);
    ui.drawer = null;
    $("#drawer-root").innerHTML = "";
    renderAll();
  }

  function openDrawer(seatId) {
    if (!me()) {
      openAuth("login", {
        after: () => openDrawer(seatId),
        note: "Увійдіть, щоб забронювати місце.",
      });
      return;
    }
    ui.drawer = { step: 1, seatId, bookingId: null, err: "", busy: false };
    renderDrawer();
  }

  function renderDrawer() {
    const d = ui.drawer;
    clearInterval(holdTimer);
    if (!d) {
      $("#drawer-root").innerHTML = "";
      return;
    }
    const seat = SEATS[d.seatId],
      co = CO[seat.co],
      u = me();
    const b = d.bookingId ? db.bookings.find((x) => x.id === d.bookingId) : null;
    const date = b ? b.date : ui.date,
      start = b ? b.start : ui.start,
      dur = b ? b.dur : ui.dur;
    const price = seatPrice(seat, dur);
    const labels = ["Місце і час", "Підтвердження", "Оплата", "Готово"];
    let body = "",
      foot = "";
    const card = `<div class="seatcard ${seat.type === "room" ? "room" : ""}"><div class="big">${seat.code}</div><div><b>${esc(co.name)} · ${esc(co.halls[seat.hall].name)}</b><span>${typeLabel(seat)}${seat.type === "room" ? ", до " + seat.cap + " осіб" : ""} · ${[
      ..."swp",
    ]
      .filter((k) => seat.f.includes(k))
      .map((k) => FEAT[k])
      .join(", ")}</span></div></div>`;
    const sum = `<div class="sumtable"><div><span>Дата</span><b>${dateLabel(date)}</b></div><div><span>Час</span><b>${hh(start)}–${hh(start + dur)} (${dur} год)</b></div><div><span>Тариф</span><b>${money(hourPrice(seat))}/год</b></div><div class="tot"><span>До сплати</span><b>${money(price)}</b></div></div>`;

    if (d.step === 1) {
      const bad = !slotOk(co) || conflict(seat, date, start, dur);
      body =
        card +
        `<div class="form">
      <div class="slotbar" style="margin:0;display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5rem">${slotControls("d-")}</div>
      ${bad ? `<div class="err">Це місце недоступне на обраний час. Змініть час або оберіть інший стіл.</div>` : ""}${sum}</div>`;
      foot = `<button class="btn" data-act="d-close">Скасувати</button><button class="btn primary" data-act="d-next1" ${bad ? "disabled" : ""}>Далі</button>`;
    }
    if (d.step === 2) {
      body =
        card +
        sum +
        `<div class="card" style="padding:0.75rem 0.875rem"><div class="kv"><div><span>Клієнт</span>${esc(u.name)}</div><div><span>Телефон</span>${esc(u.phone)}</div><div><span>Пошта для підтвердження</span>${esc(u.email)}</div></div></div>
     ${d.err ? `<div class="err">${esc(d.err)}</div>` : ""}
     <label class="checks" for="d-agree"><input type="checkbox" id="d-agree"><span>Погоджуюся з правилами: повернення коштів 100% за 24 год і більше до початку, 50% за 2–24 год, 0% пізніше.</span></label>`;
      foot = `<button class="btn" data-act="d-back">Назад</button><button class="btn primary" data-act="d-next2">Перейти до оплати</button>`;
    }
    if (d.step === 3) {
      const left = b ? Math.max(0, b.expiresAt - Date.now()) : 0;
      body =
        card +
        sum +
        `<div class="hold"><span>Місце утримується для вас</span><b id="hold">${pad(Math.floor(left / 60000))}:${pad(Math.floor(left / 1000) % 60)}</b></div>
     <div class="form"><div class="note">${ic("shield", 14)} Оплата карткою. Дані передаються платіжному провайдеру; ми не зберігаємо номер картки.</div>
     <div class="field"><label for="p-num">Номер картки</label><input id="p-num" type="text" inputmode="numeric" autocomplete="off" placeholder="4242 4242 4242 4242" maxlength="19" value="${esc((d.card || {}).num || "")}"></div>
     <div class="two"><div class="field"><label for="p-exp">Термін дії</label><input id="p-exp" type="text" inputmode="numeric" placeholder="MM/YY" maxlength="5" autocomplete="off" value="${esc((d.card || {}).exp || "")}"></div><div class="field"><label for="p-cvc">CVC</label><input id="p-cvc" type="password" inputmode="numeric" maxlength="3" placeholder="•••" autocomplete="off"></div></div>
     ${d.err ? `<div class="err" id="p-err">${esc(d.err)}</div>` : ""}</div>`;
      foot = `<button class="btn" data-act="d-close">Оплатити пізніше</button><button class="btn primary" data-act="d-pay" ${d.busy ? "disabled" : ""}>${d.busy ? "Обробка платежу…" : "Сплатити " + money(price)}</button>`;
      holdTimer = setInterval(() => {
        const bb = db.bookings.find((x) => x.id === d.bookingId);
        const el = $("#hold");
        if (!bb || bb.status !== "pending") {
          clearInterval(holdTimer);
          return;
        }
        const l = bb.expiresAt - Date.now();
        if (l <= 0) {
          sweep();
          clearInterval(holdTimer);
          toast("Час на оплату минув. Місце знову вільне.", "bad");
          closeDrawer();
          return;
        }
        if (el) el.textContent = pad(Math.floor(l / 60000)) + ":" + pad(Math.floor(l / 1000) % 60);
      }, 1000);
    }
    if (d.step === 4) {
      body = `<div class="done"><div class="ok">${ic("check", 32)}</div><h2>Бронювання підтверджено</h2><div class="code">${b ? b.code : ""}</div><p class="hint">Підтвердження надіслано на ${esc(u.email)}</p></div>${card}${sum}`;
      foot = `<button class="btn" data-act="d-close">Закрити</button><button class="btn primary" data-act="d-cab">Мої бронювання</button>`;
    }
    $("#drawer-root").innerHTML =
      `<div class="drawer-wrap" data-act="d-scrim"><aside class="drawer" role="dialog" aria-modal="true" aria-label="Бронювання місця">
    <div class="drawer-h"><h2>Бронювання місця</h2><button class="x" data-act="d-close" aria-label="Закрити">${ic("x", 20)}</button></div>
    <div class="steps">${labels.map((_, i) => `<i class="${i < d.step ? "on" : ""}"></i>`).join("")}</div>
    <div class="steps-l">Крок ${d.step} з 4 · ${labels[d.step - 1]}</div>
    <div class="drawer-b">${body}</div><div class="drawer-f">${foot}</div></aside></div>`;
  }

  function drawerNext1() {
    const d = ui.drawer,
      seat = SEATS[d.seatId];
    if (!slotOk(CO[seat.co]) || conflict(seat, ui.date, ui.start, ui.dur)) {
      renderDrawer();
      return;
    }
    d.step = 2;
    d.err = "";
    renderDrawer();
  }

  async function drawerNext2() {
    const d = ui.drawer,
      seat = SEATS[d.seatId];
    if (!$("#d-agree").checked) {
      d.err = "Підтвердьте, що ви ознайомилися з правилами.";
      renderDrawer();
      return;
    }
    if (!slotOk(CO[seat.co]) || conflict(seat, ui.date, ui.start, ui.dur)) {
      d.step = 1;
      toast("409: місце щойно зайняли. Оберіть інший час або стіл.", "bad");
      renderAll();
      renderDrawer();
      return;
    }
    let b;
    try {
      const created = await apiJson(API.bookings, {
        method: "POST",
        body: JSON.stringify({
          workspace_id: Number(seat.id),
          booking_type: "hourly",
          start_time: isoFrom(ui.date, ui.start),
          duration: ui.dur,
        }),
      });
      b = mapBooking(created, { dur: ui.dur });
      // бэкенд сразу отдаёт "confirmed", а UI требует шага оплаты
      b.status = "pending";
      b.expiresAt = Date.now() + 10 * 60000;
    } catch (e) {
      d.step = 1;
      d.err = "";
      toast(e.message || "Місце щойно зайняли. Оберіть інший час або стіл.", "bad");
      renderAll();
      renderDrawer();
      return;
    }
    if (!db.bookings.find((x) => x.id === b.id)) db.bookings.push(b);
    d.bookingId = b.id;
    d.step = 3;
    d.err = "";
    renderAll();
    renderDrawer();
  }

  async function drawerPay() {
    const d = ui.drawer;
    const b = db.bookings.find((x) => x.id === d.bookingId);
    const num = $("#p-num").value.replace(/\s/g, ""),
      exp = $("#p-exp").value,
      cvc = $("#p-cvc").value;
    d.card = { num: $("#p-num").value, exp };
    const fail = (m) => {
      d.err = m;
      d.busy = false;
      renderDrawer();
    };
    if (!b || b.status !== "pending" || b.expiresAt <= Date.now())
      return fail("Час на оплату минув. Створіть бронювання знову.");
    if (!/^\d{16}$/.test(num)) return fail("Введіть 16 цифр номера картки.");
    const m = /^(\d{2})\/(\d{2})$/.exec(exp);
    if (!m || +m[1] < 1 || +m[1] > 12) return fail("Вкажіть термін дії у форматі MM/YY.");
    const y = 2000 + +m[2];
    if (
      y < new Date().getFullYear() ||
      (y === new Date().getFullYear() && +m[1] < new Date().getMonth() + 1)
    )
      return fail("Термін дії картки минув.");
    if (!/^\d{3}$/.test(cvc)) return fail("CVC складається з трьох цифр.");
    d.busy = true;
    d.err = "";
    renderDrawer();
    try {
      // данные карты на бэкенд не отправляются
      const r = await api(API.pay, {
        method: "POST",
        body: JSON.stringify({
          booking_id: Number(b.id),
          amount: b.price,
          payment_method: "credit_card",
        }),
      });
      if (!r.ok) {
        const data = await r.json().catch(() => ({}));
        return fail(errDetail(data, r.status));
      }
      const rec = await r.json().catch(() => ({}));
      b.status = "confirmed";
      b.paidAt = Date.now();
      if (rec.pdf_url) b.receiptUrl = rec.pdf_url;
      delete b.expiresAt;
      d.busy = false;
      d.step = 4;
      renderAll();
      renderDrawer();
      toast("Оплату прийнято. Бронювання підтверджено.", "ok");
    } catch (e) {
      fail("Мережа недоступна. Спробуйте ще раз.");
    }
  }

  /* ============ modals ============ */
  function closeModal() {
    ui.modal = null;
    $("#modal-root").innerHTML = "";
  }

  function frame(title, body, wide) {
    $("#modal-root").innerHTML =
      `<div class="scrim" data-act="m-scrim"><div class="modal ${wide ? "wide" : ""}" role="dialog" aria-modal="true" aria-label="${esc(title)}"><div class="modal-h"><h2>${esc(title)}</h2><button class="x" data-act="m-close" aria-label="Закрити">${ic("x", 20)}</button></div>${body}</div></div>`;
  }

  function openAuth(step, extra) {
    const prev = ui.modal && ui.modal.kind === "auth" ? ui.modal : null;
    ui.modal = Object.assign(
      {
        kind: "auth",
        step,
        err: "",
        after: prev ? prev.after : null,
      },
      extra || {},
    );
    renderAuth();
  }

  // Бэкенд поддерживает только логин (регистрации, 2FA и сброса пароля нет)
  function renderAuth() {
    const m = ui.modal;
    const err = m.err ? `<div class="err" role="alert">${esc(m.err)}</div>` : "";
    const body = `<p class="hint" style="margin-bottom:.7rem">${m.note ? esc(m.note) : "Увійдіть, щоб бронювати місця, бачити поточні броні та історію замовлень."}</p><form class="form" data-form="login" novalidate>
     <div class="field"><label for="a-email">Логін</label><input id="a-email" name="email" type="text" autocomplete="username" value="${esc(m.email || "")}"></div>
     <div class="field"><label for="a-pw">Пароль</label><input id="a-pw" name="pw" type="password" autocomplete="current-password"></div>${err}
     <button class="btn primary" type="submit">Увійти</button></form>`;
    frame("Вхід у CoSpace", body);
    const first = $("#modal-root input:not([type=checkbox]):not([hidden])");
    if (first) first.focus();
  }

  async function finishLogin(user, view) {
    db.session = user.id;
    upsertUser(user);
    try {
      await loadRoleData(user);
    } catch (e) {}
    const after = ui.modal && ui.modal.after;
    closeModal();
    ui.menu = false;
    ui.manage = false;
    if (!after)
      ui.view =
        view || (user.role === "manager" ? "manager" : user.role === "admin" ? "admin" : "map");
    renderAll();
    toast("Вітаємо, " + (user.name.split(" ")[1] || user.name) + "!", "ok");
    if (after) after();
  }

  const formHandlers = {
    async login(f) {
      const m = ui.modal,
        email = f.get("email").trim(),
        pw = f.get("pw");
      m.email = email;
      try {
        // OAuth2PasswordRequestForm ждёт form-urlencoded с полями username/password
        const r = await api(API.login, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({ username: email, password: pw }).toString(),
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) {
          m.err =
            r.status === 400 || r.status === 401
              ? "Невірний логін або пароль."
              : errDetail(data, r.status);
          renderAuth();
          return;
        }
        setToken(data.access_token);
        const u = await hydrateMe();
        await finishLogin(u);
      } catch (e) {
        m.err = "Мережа недоступна. Перевірте з’єднання.";
        renderAuth();
      }
    },
    // На бэкенде нет PUT/cancel для броней — правка только локальная
    async editbk(f) {
      const m = ui.modal,
        b = db.bookings.find((x) => x.id === m.id),
        seat = SEATS[f.get("seat")],
        date = f.get("date"),
        start = +f.get("start"),
        dur = +f.get("dur"),
        co = CO[b.coId];
      if (start < co.open || start + dur > co.close) {
        m.err = "Час виходить за години роботи (" + hh(co.open) + "–" + hh(co.close) + ").";
        renderEdit();
        return;
      }
      if (conflict(seat, date, start, dur, b.id)) {
        m.err = "409: це місце зайняте або закрите на обраний час.";
        renderEdit();
        return;
      }
      const oldSeat = SEATS[b.seatId];
      const old = `${oldSeat ? oldSeat.code : ""}, ${b.date} ${hh(b.start)}`;
      Object.assign(b, {
        seatId: seat.id,
        date,
        start,
        dur,
        price: seatPrice(seat, dur),
        hall: seat.hall,
      });
      logAct(
        `Змінено бронь ${b.code}: було ${old}, стало ${seat.code}, ${date} ${hh(start)}–${hh(start + dur)}`,
      );
      closeModal();
      renderAll();
      toast("Бронювання оновлено.", "ok");
    },
    async manual(f) {
      const m = ui.modal,
        co = CO[m.coId],
        seat = SEATS[f.get("seat")],
        date = f.get("date"),
        start = +f.get("start"),
        dur = +f.get("dur"),
        name = f.get("name").trim(),
        phone = f.get("phone").trim();
      if (name.length < 2) {
        m.err = "Вкажіть ім’я гостя.";
        renderManual();
        return;
      }
      if (start < co.open || start + dur > co.close) {
        m.err = "Час виходить за години роботи (" + hh(co.open) + "–" + hh(co.close) + ").";
        renderManual();
        return;
      }
      if (conflict(seat, date, start, dur)) {
        m.err = "409: це місце зайняте або закрите на обраний час.";
        renderManual();
        return;
      }
      const guest = { name, phone: phone || "—" };
      let b;
      try {
        const created = await apiJson(API.bookings, {
          method: "POST",
          body: JSON.stringify({
            workspace_id: Number(seat.id),
            booking_type: "hourly",
            start_time: isoFrom(date, start),
            duration: dur,
          }),
        });
        b = Object.assign(mapBooking(created, { dur }), {
          userId: null,
          guest,
          status: "confirmed",
        });
      } catch (e) {
        m.err = e.message || "Не вдалося зафіксувати бронювання.";
        renderManual();
        return;
      }
      if (!db.bookings.find((x) => x.id === b.id)) db.bookings.push(b);
      logAct(
        `Зафіксовано бронь ${b.code} для гостя «${name}»: ${seat.code}, ${date} ${hh(start)}–${hh(start + dur)}`,
      );
      closeModal();
      renderAll();
      toast("Бронювання зафіксовано.", "ok");
    },
  };

  function slotSelects(b, co) {
    const dates = [];
    for (let i = 0; i < 14; i++) dates.push(ymd(addDays(new Date(), i)));
    if (b && !dates.includes(b.date)) dates.unshift(b.date);
    const sts = [];
    for (let h = co.open; h < co.close; h++) sts.push(h);
    const sel = (id, opts, v) =>
      `<select id="${id}" name="${id.slice(2)}">${opts.map((o) => `<option value="${o[0]}" ${String(o[0]) === String(v) ? "selected" : ""}>${o[1]}</option>`).join("")}</select>`;
    return `<div class="field"><label for="e-date">Дата</label>${sel(
      "e-date",
      dates.map((d) => [d, dateLabel(d)]),
      b ? b.date : ui.date,
    )}</div>
   <div class="two"><div class="field"><label for="e-start">Початок</label>${sel(
     "e-start",
     sts.map((h) => [h, hh(h)]),
     b ? b.start : ui.start,
   )}</div><div class="field"><label for="e-dur">Тривалість</label>${sel(
     "e-dur",
     [1, 2, 3].map((d) => [d, d + " год"]),
     b ? b.dur : ui.dur,
   )}</div></div>`;
  }

  function seatOptions(co, cur) {
    return co.halls
      .map(
        (h) =>
          `<optgroup label="${esc(h.name)}">${h.seats.map((s) => `<option value="${s.id}" ${s.id === cur ? "selected" : ""}>${s.code} · ${typeLabel(s)}${db.closed[s.id] ? " (закрито)" : ""}</option>`).join("")}</optgroup>`,
      )
      .join("");
  }

  function renderEdit() {
    const m = ui.modal,
      b = db.bookings.find((x) => x.id === m.id),
      co = CO[b.coId];
    frame(
      "Редагування " + b.code,
      `<form class="form" data-form="editbk" novalidate><div class="note"><b>${esc(bkName(b))}</b> · ${esc(bkPhone(b))}</div>
   <div class="field"><label for="e-seat">Місце</label><select id="e-seat" name="seat">${seatOptions(co, b.seatId)}</select></div>${slotSelects(b, co)}${m.err ? `<div class="err">${esc(m.err)}</div>` : ""}
   <div style="display:flex;gap:0.5rem;justify-content:flex-end"><button type="button" class="btn" data-act="m-close">Скасувати</button><button class="btn primary" type="submit">Зберегти зміни</button></div></form>`,
    );
  }

  function renderManual() {
    const m = ui.modal,
      co = CO[m.coId];
    frame(
      "Фіксація бронювання",
      `<form class="form" data-form="manual" novalidate><p class="hint">Для гостя без акаунта, який звернувся напряму. Бронь одразу стає підтвердженою.</p>
   <div class="two"><div class="field"><label for="g-name">Ім’я гостя</label><input id="g-name" name="name" type="text"></div><div class="field"><label for="g-phone">Телефон</label><input id="g-phone" name="phone" type="tel"></div></div>
   <div class="field"><label for="e-seat">Місце</label><select id="e-seat" name="seat">${seatOptions(co, "")}</select></div>${slotSelects(null, co)}${m.err ? `<div class="err">${esc(m.err)}</div>` : ""}
   <div style="display:flex;gap:0.5rem;justify-content:flex-end"><button type="button" class="btn" data-act="m-close">Скасувати</button><button class="btn primary" type="submit">Зафіксувати</button></div></form>`,
    );
  }

  function renderConfirm() {
    const m = ui.modal;
    frame(
      m.title,
      `<div class="form"><p>${m.text}</p>${m.check ? `<label class="checks" for="c-check"><input type="checkbox" id="c-check"><span>${m.check}</span></label>` : ""}${m.err ? `<div class="err">${esc(m.err)}</div>` : ""}
   <div style="display:flex;gap:0.5rem;justify-content:flex-end"><button class="btn" data-act="m-close">Назад</button><button class="btn ${m.danger ? "danger" : "primary"}" data-act="m-ok">${esc(m.ok)}</button></div></div>`,
    );
  }

  function openConfirm(o) {
    ui.modal = Object.assign({ kind: "confirm" }, o);
    renderConfirm();
  }

  /* ============ events ============ */
  const A = {
    home() {
      ui.view = "map";
      ui.manage = false;
      ui.menu = false;
      renderAll();
    },
    cabinet() {
      ui.menu = false;
      if (!me()) {
        openAuth("login", {
          after: () => {
            ui.view = "cabinet";
            renderAll();
          },
          note: "Увійдіть, щоб побачити свої бронювання.",
        });
        return;
      }
      ui.view = "cabinet";
      ui.manage = false;
      renderAll();
    },
    manager() {
      ui.menu = false;
      ui.view = "manager";
      ui.manage = false;
      renderAll();
    },
    admin() {
      ui.menu = false;
      ui.view = "admin";
      ui.manage = false;
      renderAll();
    },
    login() {
      openAuth("login", { note: "", after: null });
    },
    logout() {
      setToken("");
      db.session = null;
      ui.view = "map";
      ui.manage = false;
      ui.menu = false;
      renderAll();
      toast("Ви вийшли з акаунта.");
    },
    menu() {
      ui.menu = !ui.menu;
      renderTop();
    },
    "theme-toggle"() {
      ui.themeMenu = !ui.themeMenu;
      renderTop();
    },
    "theme-set"(t) {
      applyTheme(t.dataset.k);
      toast("Тему змінено.", "ok");
    },
    "pick-co"(t) {
      ui.coId = t.dataset.id;
      ui.hall = 0;
      ui.manage = false;
      ui.view = "map";
      fixSlot();
      fetchTemperature(ui.coId).then(() => renderStatus());
      renderAll();
    },
    hall(t) {
      ui.hall = +t.dataset.i;
      renderAll();
    },
    amen(t) {
      const k = t.dataset.k,
        i = ui.f.amen.indexOf(k);
      i < 0 ? ui.f.amen.push(k) : ui.f.amen.splice(i, 1);
      renderAll();
    },
    attr(t) {
      const k = t.dataset.k,
        i = ui.attr.indexOf(k);
      i < 0 ? ui.attr.push(k) : ui.attr.splice(i, 1);
      renderMain();
    },
    "reset-filters"() {
      ui.f = { q: "", city: "", type: "", price: 120, amen: [] };
      $("#f-q").value = "";
      $("#f-city").value = "";
      $("#f-type").value = "";
      $("#f-price").value = 120;
      renderAll();
    },
    "toggle-filters"() {
      ui.filtersOpen = !ui.filtersOpen;
      $("#filters").classList.toggle("open", ui.filtersOpen);
    },
    seat(t) {
      const s = SEATS[t.dataset.id];
      if (ui.manage) {
        const was = db.closed[s.id];
        if (was) delete db.closed[s.id];
        else db.closed[s.id] = true;
        logAct(`${was ? "Відкрито" : "Закрито"} запис на місце ${s.code} (${CO[s.co].name})`);
        renderAll();
        toast(`Місце ${s.code}: запис ${was ? "відкрито" : "закрито"}.`, "ok");
        return;
      }
      const st = seatState(s);
      if (!slotOk(CO[s.co])) {
        toast("На цю дату немає вільних годин. Оберіть іншу дату.", "bad");
        return;
      }
      if (st === "free") openDrawer(s.id);
      else if (st === "mine") {
        const b = bookedBy(s.id, ui.date, ui.start, ui.dur);
        toast("Це ваше місце на цей час. Бронювання " + (b ? b.code : "") + ".", "ok");
      } else if (st === "closed") toast("Запис на це місце закрито менеджером.", "bad");
      else toast("Це місце зайняте на обраний час. Спробуйте інший час або стіл.", "bad");
    },
    manage() {
      ui.manage = !ui.manage;
      renderMain();
    },
    "go-manage"() {
      const u = me();
      ui.coId = u.coId;
      ui.hall = 0;
      ui.view = "map";
      ui.manage = true;
      fixSlot();
      renderAll();
    },
    "cab-tab"(t) {
      ui.cabTab = t.dataset.t;
      renderMain();
    },
    "mgr-filter"(t) {
      ui.mgrFilter = t.dataset.t;
      renderMain();
    },
    "adm-tab"(t) {
      ui.admTab = t.dataset.t;
      renderMain();
    },
    "m-close"() {
      closeModal();
    },
    "m-scrim"(t, e) {
      if (e.target === t) closeModal();
    },
    "m-ok"() {
      const m = ui.modal;
      if (m.check && !$("#c-check").checked) {
        m.err = "Підтвердіть, що виконали умову.";
        renderConfirm();
        return;
      }
      const fn = m.onOk;
      closeModal();
      fn();
    },
    "d-close"() {
      closeDrawer();
    },
    "d-scrim"(t, e) {
      if (e.target === t) closeDrawer();
    },
    "d-next1"() {
      drawerNext1();
    },
    "d-next2"() {
      drawerNext2();
    },
    "d-back"() {
      ui.drawer.step = 1;
      ui.drawer.err = "";
      renderDrawer();
    },
    "d-pay"() {
      drawerPay();
    },
    "d-cab"() {
      closeDrawer();
      ui.view = "cabinet";
      ui.cabTab = "now";
      renderAll();
    },
    "pay-bk"(t) {
      const b = db.bookings.find((x) => x.id === t.dataset.id);
      if (!b || b.status !== "pending" || b.expiresAt <= Date.now()) {
        toast("Час на оплату минув.", "bad");
        renderAll();
        return;
      }
      ui.drawer = { step: 3, seatId: b.seatId, bookingId: b.id, err: "", busy: false };
      renderDrawer();
    },
    "cancel-pending"(t) {
      const b = db.bookings.find((x) => x.id === t.dataset.id);
      openConfirm({
        title: "Скасувати бронювання?",
        text: `Бронь ${b.code} ще не оплачена, місце буде звільнено.`,
        ok: "Скасувати бронь",
        danger: true,
        onOk() {
          cancelBooking(b, "Скасовано клієнтом до оплати");
          renderAll();
          toast("Бронювання скасовано.");
        },
      });
    },
    "req-cancel"(t) {
      const b = db.bookings.find((x) => x.id === t.dataset.id),
        pct = refundPct(b);
      openConfirm({
        title: "Запит на скасування",
        text: `Менеджер коворкінгу зателефонує вам за номером <b>${esc(me().phone)}</b>, щоб узгодити скасування броні ${b.code}. Якщо скасувати зараз, повернемо <b>${pct}%</b> (${money(Math.round((b.price * pct) / 100))}).`,
        ok: "Надіслати запит",
        onOk() {
          b.cancelRequested = true;
          save();
          renderAll();
          toast("Запит надіслано. Очікуйте дзвінка менеджера.", "ok");
        },
      });
    },
    "edit-bk"(t) {
      ui.modal = { kind: "edit", id: t.dataset.id, err: "" };
      renderEdit();
    },
    "manual-bk"() {
      ui.modal = { kind: "manual", coId: me().coId, err: "" };
      renderManual();
    },
    "mgr-cancel"(t) {
      const b = db.bookings.find((x) => x.id === t.dataset.id),
        pct = refundPct(b);
      openConfirm({
        title: "Скасувати бронювання " + b.code,
        text: `Клієнт: <b>${esc(bkName(b))}</b>, ${esc(bkPhone(b))}. Повернення коштів: <b>${pct}%</b> (${money(Math.round((b.price * pct) / 100))}).`,
        check: b.userId ? "Я зателефонував клієнтові, і він погодився на скасування" : "",
        ok: "Скасувати бронь",
        danger: true,
        onOk() {
          const p = cancelBooking(b, "Скасовано менеджером за погодженням із клієнтом");
          logAct(`Скасовано бронь ${b.code} (${bkName(b)}), повернення ${p}%`);
          renderAll();
          toast("Бронювання скасовано.", "ok");
        },
      });
    },
    "adm-cancel"(t) {
      const b = db.bookings.find((x) => x.id === t.dataset.id),
        pct = refundPct(b);
      openConfirm({
        title: "Скасувати бронювання " + b.code,
        text: `Клієнт: <b>${esc(bkName(b))}</b>. Повернення коштів: <b>${pct}%</b>.`,
        ok: "Скасувати бронь",
        danger: true,
        onOk() {
          const p = cancelBooking(b, "Скасовано адміністратором платформи");
          logAct(`Адміністратор скасував бронь ${b.code}, повернення ${p}%`);
          renderAll();
          toast("Бронювання скасовано.", "ok");
        },
      });
    },
    approve(t) {
      const r = db.requests.find((x) => x.id === t.dataset.id),
        coId = $("#rc-" + r.id).value,
        u = userById(r.userId);
      if (u) {
        u.role = "manager";
        u.coId = coId;
      }
      r.status = "approved";
      save();
      logAct(`Надано права менеджера «${u ? u.name : "Користувач"}» для коворкінгу «${CO[coId] ? CO[coId].name : ""}»`);
      renderAll();
      toast("Права менеджера надано.", "ok");
    },
    reject(t) {
      const r = db.requests.find((x) => x.id === t.dataset.id),
        u = userById(r.userId);
      r.status = "rejected";
      save();
      logAct(`Відхилено заявку менеджера від «${u ? u.name : "Користувач"}»`);
      renderAll();
      toast("Заявку відхилено.");
    },
  };

  document.addEventListener("click", (e) => {
    if (ui.menu && !e.target.closest(".acct")) {
      ui.menu = false;
      renderTop();
    }
    if (ui.themeMenu && !e.target.closest(".theme-wrap")) {
      ui.themeMenu = false;
      renderTop();
    }
    const t = e.target.closest("[data-act]");
    if (!t) return;
    const fn = A[t.dataset.act];
    if (fn) fn(t, e);
  });

  document.addEventListener("submit", (e) => {
    e.preventDefault();
    const k = e.target.dataset.form;
    if (k && formHandlers[k]) formHandlers[k](new FormData(e.target));
  });

  document.addEventListener("change", (e) => {
    const t = e.target;
    if (t.dataset && t.dataset.bind) {
      const k = t.dataset.bind;
      ui[k] = k === "date" ? t.value : Number(t.value);
      fixSlot();
      renderAll();
      if (ui.drawer && ui.drawer.step === 1) renderDrawer();
      return;
    }
    if (t.id === "f-city") {
      ui.f.city = t.value;
      renderAll();
    } else if (t.id === "f-type") {
      ui.f.type = t.value;
      renderAll();
    } else if (t.dataset && t.dataset.role) {
      const u = userById(t.dataset.role);
      if (u) {
        u.role = t.value;
        u.coId = t.value === "manager" ? u.coId || (COS[0] && COS[0].id) : null;
        save();
        logAct(`Змінено роль «${u.name}» на «${ROLE[u.role]}»`);
        renderAll();
        toast("Роль оновлено.", "ok");
      }
    } else if (t.dataset && t.dataset.co) {
      const u = userById(t.dataset.co);
      if (u) {
        u.coId = t.value || (COS[0] && COS[0].id);
        save();
        logAct(`Призначено «${u.name}» до коворкінгу «${CO[u.coId] ? CO[u.coId].name : ""}»`);
        renderAll();
        toast("Коворкінг призначено.", "ok");
      }
    }
  });

  document.addEventListener("input", (e) => {
    const t = e.target;
    if (t.id === "f-q") {
      ui.f.q = t.value.trim().toLowerCase();
      renderSide();
      renderMain();
      renderTop();
    } else if (t.id === "f-price") {
      ui.f.price = +t.value;
      renderSide();
      renderMain();
      renderTop();
    } else if (t.id === "p-num") {
      const v = t.value.replace(/\D/g, "").slice(0, 16);
      t.value = v.replace(/(\d{4})(?=\d)/g, "$1 ");
    } else if (t.id === "p-exp") {
      let v = t.value.replace(/\D/g, "").slice(0, 4);
      if (v.length > 2) v = v.slice(0, 2) + "/" + v.slice(2);
      t.value = v;
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (ui.modal) closeModal();
      else if (ui.drawer) closeDrawer();
      else if (ui.menu) {
        ui.menu = false;
        renderTop();
      } else if (ui.themeMenu) {
        ui.themeMenu = false;
        renderTop();
      }
    }
  });

  /* ============ init: завантаження з бекенду ============ */
  async function loadInitialData() {
    // 1) каталог: коворкинги + рабочие места
    try {
      const r = await api(API.coworkings);
      const list = r.ok ? await r.json() : [];
      const byCo = {};
      await Promise.all(
        list.map(async (c) => {
          if (Array.isArray(c.workspaces)) {
            byCo[c.id] = c.workspaces;
            return;
          }
          try {
            const rr = await api(API.coworkings + "/" + c.id + "/workspaces");
            byCo[c.id] = rr.ok ? await rr.json() : [];
          } catch (e) {
            byCo[c.id] = [];
          }
        }),
      );
      buildCatalogue(mapCoworkings(list, byCo));
    } catch (e) {
      buildCatalogue([]);
    }

    // 2) текущий пользователь (после каталога — mapUser смотрит на COS)
    if (getToken()) {
      try {
        const u = await hydrateMe();
        db.users.push(u);
        db.session = u.id;
      } catch (e) {
        setToken("");
      }
    }
  }

  async function initApp() {
    applyTheme(currentTheme());
    await loadInitialData();

    const citySel = $("#f-city");
    if (citySel)
      citySel.innerHTML =
        '<option value="">Усі міста</option>' +
        CITIES.map((c) => `<option>${esc(c)}</option>`).join("");

    if (COS.length) {
      if (!ui.coId) ui.coId = COS[0].id;
      fixSlot();
      fetchTemperature(ui.coId).then(() => renderStatus());
    }
    renderAll();

    setInterval(() => {
      if (ui.view === "map" && !ui.drawer) {
        const before = db.bookings.filter((b) => b.status === "pending").length;
        sweep();
        if (before !== db.bookings.filter((b) => b.status === "pending").length) renderAll();
      }
    }, 20000);
    setInterval(() => {
      if (ui.coId) fetchTemperature(ui.coId).then(() => renderStatus());
    }, 60000);
  }

  initApp();
})();
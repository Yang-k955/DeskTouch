(function () {
  'use strict';

  var $ = function (id) { return document.getElementById(id); };
  var NS = 'http://www.w3.org/2000/svg';
  var ICONS = {
    grid: ['M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z'],
    apps: ['M4 4h6v6H4z M14 4h6v6h-6z M4 14h6v6H4z M14 14h6v6h-6z'],
    monitor: ['M3 4h18v13H3z M8 21h8 M12 17v4'],
    cpu: ['M6 6h12v12H6z M9 9h6v6H9z M9 2v4 M15 2v4 M9 18v4 M15 18v4 M2 9h4 M2 15h4 M18 9h4 M18 15h4'],
    memory: ['M3 6h18v12H3z M7 10v4 M11 10v4 M15 10v4 M19 10v4 M6 18v3 M10 18v3 M14 18v3 M18 18v3'],
    network: ['M12 3v6 M5 15v-4h14v4 M12 11v4 M2 16h6v5H2z M9 16h6v5H9z M16 16h6v5h-6z M9 3h6v5H9z'],
    volume: ['M4 9h4l5-4v14l-5-4H4z M17 8a6 6 0 0 1 0 8 M20 5a10 10 0 0 1 0 14'],
    muted: ['M4 9h4l5-4v14l-5-4H4z M17 9l5 6 M22 9l-5 6'],
    music: ['M9 18V5l11-2v13 M9 7l11-2 M9 18a3 3 0 1 1-3-3h3 M20 16a3 3 0 1 1-3-3h3'],
    play: ['M9 5l11 7-11 7z'], pause: ['M8 5v14 M16 5v14'],
    previous: ['M6 5v14 M18 5L8 12l10 7z'], next: ['M18 5v14 M6 5l10 7-10 7z'],
    disk: ['M5 3h14l3 12v6H2v-6z M2 15h20 M17 18h2 M13 18h1'],
    power: ['M12 2v10 M6 5a9 9 0 1 0 12 0'],
    lock: ['M6 10h12v11H6z M8 10V6a4 4 0 0 1 8 0v4 M12 14v3'],
    display_off: ['M3 4h18v13H3z M8 21h8 M12 17v4 M8 8l8 5 M16 8l-8 5'],
    sleep: ['M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11z'],
    restart: ['M20 11a8 8 0 1 0-2 6 M20 4v7h-7'], shutdown: ['M12 2v10 M6 5a9 9 0 1 0 12 0'],
    settings: ['M10 3h4l1 3 3 1 3-1 2 4-2 2v3l2 2-2 4-3-1-3 1-1 3h-4l-1-3-3-1-3 1-2-4 2-2v-3l-2-2 2-4 3 1 3-1z', 'M15 13a3 3 0 1 1-6 0 3 3 0 0 1 6 0'],
    fullscreen: ['M8 3H3v5 M16 3h5v5 M3 16v5h5 M21 16v5h-5'],
    moon: ['M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11z'],
    sun: ['M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0 M12 2v2 M12 20v2 M2 12h2 M20 12h2 M5 5l2 2 M17 17l2 2 M5 19l2-2 M17 7l2-2'],
    shield: ['M12 2l9 4v6c0 6-9 10-9 10S3 18 3 12V6z M8 12l3 3 5-6'],
    wifi: ['M2 8a16 16 0 0 1 20 0 M5 12a11 11 0 0 1 14 0 M8 16a6 6 0 0 1 8 0 M12 20h.01'],
    plus: ['M12 5v14 M5 12h14'], search: ['M16 10a6 6 0 1 1-12 0 6 6 0 0 1 12 0 M15 15l6 6'],
    edit: ['M4 16L16 4l4 4L8 20H4z M13 7l4 4'],
    image: ['M3 4h18v16H3z M3 17l5-4 4 3 3-2 6 5', 'M9 10a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0'],
    folder: ['M3 6h6l2 2h10v11H3z'], file: ['M6 3h8l5 5v13H6z M14 3v5h5'],
    'arrow-right': ['M4 12h16 M14 6l6 6-6 6'], 'arrow-left': ['M20 12H4 M10 6l-6 6 6 6'],
    up: ['M12 20V4 M6 10l6-6 6 6'], down: ['M12 4v16 M6 14l6 6 6-6'],
    close: ['M6 6l12 12 M18 6L6 18'], trash: ['M3 6h18 M8 6V3h8v3 M5 6l1 15h12l1-15 M10 10v7 M14 10v7'],
    check: ['M4 12l5 5L20 6'], refresh: ['M20 10a8 8 0 0 0-14-4 M4 14a8 8 0 0 0 14 4 M20 3v7h-7 M4 21v-7h7'],
    clock: ['M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0 M12 6v6l4 2'],
    battery: ['M2 7h18v10H2z M22 10v4 M5 10h10v4H5z'],
    window: ['M3 4h18v16H3z M3 8h18 M6 6h.01 M9 6h.01']
  };
  var POWER = { lock: '锁定电脑', display_off: '关闭显示器', sleep: '睡眠', restart: '重新启动', shutdown: '关机' };
  var SHORT_POWER = { lock: '锁屏', display_off: '息屏', sleep: '睡眠', restart: '重启', shutdown: '关机' };
  var SOURCES = { startmenu: '开始菜单', uwp: '商店应用', steam: 'Steam', running: '运行中' };
  var METRICS = { cpu: 'CPU 负载', memory: '内存', network: '网络速率', disk: '磁盘空间', uptime: '运行时间', battery: '电池状态', foreground: '前台窗口' };
  var state = {
    token: '', epoch: 0, connected: false, demo: false, layout: null, apps: [], groups: [], pageId: '',
    system: null, audio: null, media: null, snapshotAt: 0, revision: 0, renderers: [], socket: null,
    reconnectAttempt: 0, reconnectTimer: null, heartbeat: null, authTimer: null, bootBusy: false, lastCloseCode: 0,
    edit: false, draft: null, configDirty: false, saving: false, configTimer: null, modal: null,
    scan: null, scanBusy: false, scanVersion: 0, scanSelected: new Set(), appSearch: '', appGroup: '',
    appBusy: new Set(), highlights: new Set(), icons: new Map(), iconGeneration: 0,
    volumeTimer: null, volumeSending: false, volumeDesired: null, volumeEditing: false, volumeLast: 0,
    wake: null, wakeMessage: '', expectedPower: '', configVersion: 0,
    retryAt: 0, offlineVisible: false, offlineTimer: null, offlineHideTimer: null
  };

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = String(text);
    return node;
  }
  function svgIcon(name) {
    var svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('class', 'icon');
    svg.setAttribute('fill', 'none'); svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '1.65'); svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round'); svg.setAttribute('aria-hidden', 'true');
    (ICONS[name] || ICONS.grid).forEach(function (d) { var p = document.createElementNS(NS, 'path'); p.setAttribute('d', d); svg.appendChild(p); });
    return svg;
  }
  function setIcon(node, name) { clear(node); node.appendChild(svgIcon(name)); }
  function hydrateIcons(root) { Array.prototype.forEach.call(root.querySelectorAll('[data-icon]'), function (n) { setIcon(n, n.getAttribute('data-icon')); }); }
  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }
  function button(text, cls, icon, handler) {
    var b = el('button', cls || 'btn subtle'); b.type = 'button';
    if (icon) b.appendChild(svgIcon(icon));
    if (text) b.appendChild(el('span', '', text));
    if (handler) b.addEventListener('click', handler);
    return b;
  }
  function iconButton(name, label, handler) {
    var b = button('', 'icon-button', name, handler); b.title = label; b.setAttribute('aria-label', label); return b;
  }
  function control(node, kind) { node.setAttribute('data-control', kind || 'remote'); return node; }
  function controlsAvailable() { return state.connected && !state.demo && !state.edit; }
  function syncControls() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-control]'), function (n) {
      var kind = n.getAttribute('data-control');
      var allowed = state.connected && !state.demo;
      if (kind === 'config') allowed = state.connected && !state.edit;
      else if (kind === 'audio') allowed = controlsAvailable() && state.audio && state.audio.available === true;
      else if (kind === 'media') allowed = controlsAvailable() && state.media && state.media.available === true && state.media.active;
      else if (kind === 'remote') allowed = controlsAvailable();
      n.disabled = !allowed || n.getAttribute('data-busy') === 'true';
      if (state.demo) n.title = '演示模式，不控制电脑';
      else if (!state.connected) n.title = '连接恢复后可操作';
    });
    $('scan-open').disabled = !state.connected || state.edit;
    if (state.modal && state.modal.sync) state.modal.sync();
    $('edit-toggle').disabled = !state.layout || !state.connected || state.saving;
    $('page-add').disabled = !state.layout || !state.connected || state.edit;
    $('edit-save').disabled = !state.connected || state.saving;
    if (!state.connected) cancelVolume();
  }
  function num(v) { return typeof v === 'number' && isFinite(v) ? v : 0; }
  function percent(v) { return Math.max(0, Math.min(100, num(v))); }
  function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
  function bytes(v) {
    v = Math.max(0, num(v));
    if (v >= 1073741824) return (v / 1073741824).toFixed(v >= 10737418240 ? 0 : 1) + ' GB';
    if (v >= 1048576) return (v / 1048576).toFixed(0) + ' MB';
    if (v >= 1024) return (v / 1024).toFixed(0) + ' KB';
    return Math.round(v) + ' B';
  }
  function rate(v) {
    v = Math.max(0, num(v));
    if (v >= 1048576) return [(v / 1048576).toFixed(1), 'MB/s'];
    if (v >= 1024) return [(v / 1024).toFixed(0), 'KB/s'];
    return [Math.round(v).toString(), 'B/s'];
  }
  function duration(v) { v = Math.max(0, Math.floor(num(v))); return Math.floor(v / 60) + ':' + ('0' + v % 60).slice(-2); }
  function uptime(v) {
    v = Math.max(0, Math.floor(num(v))); var d = Math.floor(v / 86400), h = Math.floor(v % 86400 / 3600), m = Math.floor(v % 3600 / 60);
    return (d ? d + ' 天 ' : '') + h + ' 小时 ' + m + ' 分钟';
  }
  function toast(message, error) {
    var t = el('div', 'toast' + (error ? ' error' : ''), message); $('toasts').appendChild(t);
    while ($('toasts').children.length > 4) $('toasts').removeChild($('toasts').firstChild);
    setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, error ? 6500 : 4200);
  }
  function storageWarning(message) {
    $('storage-warning').textContent = message; $('storage-warning').hidden = false;
  }
  function readStorage(key) {
    try { return localStorage.getItem(key) || ''; }
    catch (e) { storageWarning('当前浏览器无法永久记住配对；关闭页面后需要重新配对。请使用非无痕窗口并允许本地存储。'); return ''; }
  }
  function saveToken(value) {
    try {
      if (value) localStorage.setItem('dt_token', value); else localStorage.removeItem('dt_token');
      if ((localStorage.getItem('dt_token') || '') !== value) throw new Error('本地存储未生效');
      $('storage-warning').hidden = true; return true;
    } catch (e) {
      storageWarning(value ? '当前浏览器无法永久记住配对；本次页面仍可连接，但关闭后需要重新配对。请使用非无痕窗口并允许本地存储。' : '无法清除浏览器中保存的配对。请在浏览器设置中手动清除此地址的网站数据。');
      return false;
    }
  }
  function setDemo(value) {
    state.demo = value === true; $('demo-banner').hidden = !state.demo; document.body.classList.toggle('demo-mode', state.demo);
    $('pair-health').textContent = state.demo ? '演示服务 · 所有电脑控制已禁用' : '服务可用 · 等待安全配对'; syncControls();
  }
  async function api(path, method, data, options) {
    options = options || {}; var epoch = state.epoch;
    var headers = {}; if (!options.public && state.token) headers.Authorization = 'Bearer ' + state.token;
    if (data !== undefined) headers['Content-Type'] = 'application/json';
    var controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
    var timer = controller ? setTimeout(function () { controller.abort(); }, options.timeout || 15000) : null;
    try {
      var res = await fetch(path, { method: method || 'GET', headers: headers, body: data === undefined ? undefined : JSON.stringify(data), credentials: 'same-origin', cache: 'no-store', signal: controller ? controller.signal : undefined });
      var json = {}; try { json = await res.json(); } catch (e) { if (res.ok) throw new Error('服务返回了无效的 JSON'); }
      if (epoch !== state.epoch) throw new Error('连接会话已更换，请重试');
      if (!res.ok || json.ok === false) {
        var err = new Error(json.message || (json.detail && typeof json.detail === 'string' ? json.detail : '请求失败（' + res.status + '）'));
        err.status = res.status; err.code = json.error;
        if (res.status === 401 && !options.public) showPair('配对已失效，请重新输入电脑端配对码。');
        throw err;
      }
      return json;
    } catch (e) {
      if (e.name === 'AbortError') throw new Error('服务响应超时，请检查电脑与局域网连接。');
      if (e instanceof TypeError) throw new Error('无法连接电脑，请检查服务和 Wi-Fi。');
      throw e;
    } finally { if (timer) clearTimeout(timer); }
  }
  function requireRemote() {
    if (!controlsAvailable()) { toast(state.demo ? '演示模式 · 不控制电脑' : '连接尚未恢复，控制暂不可用。'); return false; }
    return true;
  }
  async function remote(path, body) {
    if (!requireRemote()) return null;
    try { return await api(path, 'POST', body); } catch (e) { toast(e.message, true); return null; }
  }

  function releaseIcons() {
    state.iconGeneration += 1;
    state.icons.forEach(function (entry) { if (entry.url) URL.revokeObjectURL(entry.url); }); state.icons.clear();
  }
  function safeImagePath(path) {
    if (typeof path !== 'string' || !path || path.length > 1000) return '';
    try {
      var u = new URL(path, location.href);
      if (u.origin !== location.origin || u.search || u.hash) return '';
      if (!/^\/api\/(icons\/|scan\/icon\/|media\/)/.test(u.pathname) && !/^\/api\/icon-library\/[^/]+\.svg$/.test(u.pathname)) return '';
      return u.pathname;
    } catch (e) { return ''; }
  }
  async function imageURL(path) {
    path = safeImagePath(path); if (!path || !state.token) return '';
    if (state.icons.has(path)) return state.icons.get(path).promise;
    var generation = state.iconGeneration;
    var entry = { url: '', promise: null };
    entry.promise = (async function () {
      try {
        var response = await fetch(path, { headers: { Authorization: 'Bearer ' + state.token }, cache: 'no-store', credentials: 'same-origin' });
        if (response.status === 401 && generation === state.iconGeneration) showPair('配对已失效，请重新连接。');
        if (!response.ok || !/^image\//i.test(response.headers.get('Content-Type') || '')) return '';
        var blob = await response.blob(); if (generation !== state.iconGeneration || state.icons.get(path) !== entry || blob.size > 5 * 1024 * 1024) return '';
        entry.url = URL.createObjectURL(blob); return entry.url;
      } catch (e) { return ''; }
    }());
    state.icons.set(path, entry);
    if (state.icons.size > 160) {
      var first = state.icons.keys().next().value; var old = state.icons.get(first);
      state.icons.delete(first);
      old.promise.then(function (url) { if (url) URL.revokeObjectURL(url); });
    }
    entry.promise.then(function (url) { if (!url && state.icons.get(path) === entry) state.icons.delete(path); });
    return entry.promise;
  }
  function appIcon(name, path, cls) {
    var box = el('span', cls || 'app-icon'); box.textContent = Array.from(String(name || '?').trim())[0] || '?';
    if (path) imageURL(path).then(function (url) {
      if (!url || !document.documentElement.contains(box)) return;
      var img = el('img'); img.alt = ''; img.src = url;
      img.addEventListener('load', function () { clear(box); box.appendChild(img); });
    });
    return box;
  }

  async function health() {
    $('pair-host').textContent = '正在检测电脑服务…'; $('pair-health-dot').className = 'dot offline';
    $('health-retry').disabled = true;
    $('lan-address').textContent = location.protocol === 'file:' ? '请通过电脑服务的局域网地址打开此网页。' : location.origin;
    try {
      var h = await api('/api/health', 'GET', undefined, { public: true, timeout: 8000 });
      $('pair-host').textContent = h.hostname || 'DeskTouch 电脑'; setDemo(h.demo);
      $('pair-health-dot').className = 'dot'; $('side-version').textContent = h.version || '—';
      if (/^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname)) $('lan-address').textContent = '当前是电脑本机地址。请在平板上使用电脑托盘连接窗口显示的局域网地址。';
    } catch (e) { $('pair-host').textContent = '暂时无法连接电脑'; $('pair-health').textContent = e.message; }
    finally { $('health-retry').disabled = false; }
  }
  function stopConnection() {
    clearTimeout(state.reconnectTimer); clearTimeout(state.authTimer); clearInterval(state.heartbeat);
    state.reconnectTimer = null; state.authTimer = null; state.heartbeat = null; state.retryAt = 0;
    if (state.socket) { var ws = state.socket; state.socket = null; ws.onclose = null; ws.onmessage = null; ws.onopen = null; ws.close(); }
    setConnected(false);
  }
  function showPair(message) {
    state.epoch += 1; state.configVersion += 1; clearTimeout(state.configTimer); state.expectedPower = ''; stopConnection(); state.token = ''; var removed = saveToken(''); releaseIcons(); cancelVolume();
    state.appBusy.clear(); state.scanSelected.clear(); state.scan = null; state.scanVersion += 1; state.scanBusy = false;
    state.system = null; state.audio = null; state.media = null; state.snapshotAt = 0;
    state.layout = null; state.apps = []; state.groups = []; state.edit = false; state.draft = null; state.renderers = []; state.lastCloseCode = 0;
    clear($('card-grid')); $('hostname').textContent = '我的电脑';
    if (state.modal) state.modal.busy = false;
    closeModal(); releaseWake(); $('workspace').hidden = true; $('pair-screen').hidden = false; updateOffline();
    $('pair-error').textContent = removed ? message || '' : '当前页面已断开，但未能清除保存的配对。请手动清除此地址的网站数据。'; $('pair-code').value = ''; $('pair-submit').disabled = false;
    if (message) $('pair-code').focus();
  }
  async function pair(event) {
    event.preventDefault();
    var code = $('pair-code').value.trim(), name = $('device-name').value.trim();
    if (!/^[0-9]{6}$/.test(code)) { $('pair-error').textContent = '请输入 6 位数字配对码。'; return; }
    if (!name) { $('pair-error').textContent = '为这台平板填写一个名称。'; return; }
    $('pair-submit').disabled = true; $('pair-error').textContent = '';
    try {
      var result = await api('/api/pair', 'POST', { code: code, device_name: name }, { public: true });
      if (!result.token || typeof result.token !== 'string') throw new Error('服务未返回配对令牌。');
      state.epoch += 1; state.token = result.token;
      saveToken(result.token);
      $('pair-code').value = ''; await boot();
    } catch (e) { $('pair-error').textContent = e.message; }
    finally { $('pair-submit').disabled = false; }
  }
  function setConnected(value, message) {
    state.connected = value;
    $('connection-label').textContent = value ? (state.demo ? '演示连接' : '已连接 · 实时同步') : '连接未就绪';
    $('connection-dot').className = 'dot' + (value ? '' : ' offline');
    $('connection-banner').hidden = value;
    $('connection-message').textContent = message || (state.expectedPower ? '已发送「' + state.expectedPower + '」，电脑可能正在休眠或关闭；等待恢复连接。' : '连接已断开，正在重新连接。控制已暂时禁用。');
    if (!value && state.modal && state.modal.cancelHold) state.modal.cancelHold();
    syncControls(); updateOffline();
  }
  function offlineWanted() { return !!state.token && state.connected !== true && $('workspace').hidden === false; }
  function updateOffline() {
    var overlay = $('offline-overlay'); if (!overlay) return;
    clearTimeout(state.offlineTimer); state.offlineTimer = null;
    if (offlineWanted()) {
      if (state.offlineVisible) { renderOffline(); return; }
      state.offlineTimer = setTimeout(function () {
        state.offlineTimer = null; if (!offlineWanted()) return;
        state.offlineVisible = true; clearTimeout(state.offlineHideTimer); state.offlineHideTimer = null;
        overlay.hidden = false; overlay.getBoundingClientRect(); overlay.classList.add('is-visible'); renderOffline();
      }, 320);
      return;
    }
    if (!state.offlineVisible) { overlay.hidden = true; overlay.classList.remove('is-visible'); return; }
    state.offlineVisible = false; overlay.classList.remove('is-visible');
    clearTimeout(state.offlineHideTimer);
    state.offlineHideTimer = setTimeout(function () { state.offlineHideTimer = null; if (!state.offlineVisible) overlay.hidden = true; }, 320);
  }
  function renderOffline() {
    var note = $('offline-note'), status = $('offline-status'); if (!note || !status) return;
    var noteText = (state.expectedPower ? '若刚发送电源指令，电脑可能正在关机、休眠或重启。' : '') + '电脑可能已休眠、关机，或平板与电脑的网络暂时断开。恢复连接后会自动继续，不需要重新配对。';
    var parts = [], left = state.retryAt ? Math.max(0, Math.ceil((state.retryAt - Date.now()) / 1000)) : 0;
    if (state.reconnectAttempt > 0) parts.push('第 ' + state.reconnectAttempt + ' 次重连');
    if (state.retryAt) parts.push(left > 0 ? left + ' 秒后自动重试' : '即将自动重试');
    else parts.push('正在尝试重新连接…');
    var statusText = parts.join(' · ');
    if (note.textContent !== noteText) note.textContent = noteText;
    if (status.textContent !== statusText) status.textContent = statusText;
  }
  async function moduleSnapshot(path) {
    try { return await api(path); } catch (e) { if (e.status === 503) return { available: false, message: e.message }; throw e; }
  }
  async function snapshot() {
    var revision = state.revision;
    var data = await Promise.all([api('/api/system'), moduleSnapshot('/api/audio'), moduleSnapshot('/api/media')]);
    if (revision === state.revision) { state.system = data[0]; state.audio = data[1]; state.media = data[2]; state.snapshotAt = Date.now(); updateCards(); }
  }
  function applyLayout(layout, apps) {
    if (!layout || !Array.isArray(layout.pages) || !layout.pages.length) throw new Error('电脑尚未提供有效的页面布局。');
    state.layout = layout; state.apps = Array.isArray(apps.apps) ? apps.apps : []; state.groups = Array.isArray(apps.groups) ? apps.groups : [];
    if (!layout.pages.some(function (p) { return p.id === state.pageId; })) state.pageId = layout.pages[0].id;
    $('hostname').textContent = layout.hostname || (state.system && state.system.hostname) || '我的电脑';
    $('side-version').textContent = layout.version || '—'; setDemo(layout.demo); applyUI(layout.ui || {}); renderPage();
  }
  async function refreshConfig() {
    var version = ++state.configVersion;
    var values = await Promise.all([api('/api/layout'), api('/api/apps')]);
    if (version !== state.configVersion) return;
    if (state.edit) {
      state.apps = Array.isArray(values[1].apps) ? values[1].apps : state.apps;
      state.configDirty = true; toast('电脑端布局已更新。请取消当前编辑后重试，避免覆盖新配置。'); return;
    }
    releaseIcons(); applyLayout(values[0], values[1]);
  }
  async function boot() {
    if (state.bootBusy || !state.token) return;
    state.bootBusy = true; var epoch = state.epoch;
    $('pair-screen').hidden = true; $('workspace').hidden = false;
    setConnected(false, '正在读取电脑配置与实时状态…');
    try {
      var config = await Promise.all([api('/api/layout'), api('/api/apps')]);
      if (epoch !== state.epoch) return;
      applyLayout(config[0], config[1]); await snapshot();
      if (epoch === state.epoch) connect();
    } catch (e) {
      if (epoch !== state.epoch) return;
      setConnected(false, e.message + ' 控制已禁用，稍后自动重试。'); scheduleReconnect(true);
    } finally { state.bootBusy = false; }
  }
  function scheduleReconnect(fullBoot) {
    if (!state.token || state.reconnectTimer) return;
    var wait = Math.min(10000, Math.pow(2, state.reconnectAttempt) * 1000); state.reconnectAttempt += 1;
    state.retryAt = Date.now() + wait; updateOffline();
    state.reconnectTimer = setTimeout(function () { state.reconnectTimer = null; state.retryAt = 0; if (fullBoot || !state.layout) boot(); else connect(); }, wait);
  }
  function connect() {
    if (!state.token) return;
    stopConnection();
    state.retryAt = 0;
    if (state.lastCloseCode === 1013) setConnected(false, '连接数量已达上限，请断开其他平板；正在等待可用连接。');
    var epoch = state.epoch;
    var ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws');
    state.socket = ws; var ready = false, fresh = false, lastMessage = Date.now();
    state.authTimer = setTimeout(function () { if (state.socket === ws) ws.close(4000, 'timeout'); }, 10000);
    ws.onopen = function () { if (state.socket !== ws) return; ws.send(JSON.stringify({ type: 'auth', token: state.token })); };
    ws.onmessage = function (event) {
      if (state.socket !== ws || epoch !== state.epoch) return;
      var msg; try { msg = JSON.parse(event.data); } catch (e) { return; }
      lastMessage = Date.now();
      if (msg.type === 'ready') {
        if (ready) return; ready = true; clearTimeout(state.authTimer);
        refreshConfig().then(snapshot).then(function () {
          if (state.socket !== ws || ws.readyState !== WebSocket.OPEN || epoch !== state.epoch) return;
          fresh = true; state.reconnectAttempt = 0; state.expectedPower = ''; state.lastCloseCode = 0; setConnected(true);
          if (state.layout.ui && state.layout.ui.keep_awake) requestWake(false);
        }).catch(function (e) { if (state.socket === ws) { setConnected(false, '状态读取失败：' + e.message); ws.close(4001, 'snapshot failed'); } });
        state.heartbeat = setInterval(function () {
          if (state.socket !== ws || ws.readyState !== WebSocket.OPEN) return;
          if (Date.now() - lastMessage > 35000 || (fresh && Date.now() - state.snapshotAt > 15000)) { ws.close(4000, 'stale state'); return; }
          ws.send(JSON.stringify({ type: 'ping' }));
        }, 5000);
      } else if (msg.type === 'ping' && ready) { ws.send(JSON.stringify({ type: 'pong' })); }
      else if (msg.type === 'state' && ready) {
        if (!msg.system || !msg.system.cpu || !msg.system.memory || !msg.system.network) return;
        state.revision += 1; state.system = msg.system;
        if (msg.audio) state.audio = msg.audio;
        if (msg.media) state.media = msg.media;
        if (msg.apps && typeof msg.apps === 'object') state.apps.forEach(function (app) { if (Object.prototype.hasOwnProperty.call(msg.apps, app.id)) app.running = msg.apps[app.id] === true; });
        state.snapshotAt = Date.now(); updateCards();
      } else if (msg.type === 'config_updated' && ready) {
        clearTimeout(state.configTimer);
        state.configTimer = setTimeout(function () { refreshConfig().catch(function (e) { toast(e.message, true); }); }, 120);
      }
    };
    ws.onerror = function () { if (state.socket === ws) setConnected(false, '无法连接实时服务，正在重试；控制已禁用。'); };
    ws.onclose = function (event) {
      if (state.socket !== ws || epoch !== state.epoch) return;
      state.socket = null; state.lastCloseCode = event.code; clearInterval(state.heartbeat); clearTimeout(state.authTimer);
      setConnected(false, event.code === 1013 ? '连接数量已达上限，请断开其他平板；正在等待可用连接。' : undefined);
      if (event.code === 1008) {
        setConnected(false, '实时连接中断，正在验证已保存的配对；不会仅因掉线解除配对。');
        api('/api/layout', 'GET', undefined, { timeout: 8000 }).catch(function (e) {
          if (epoch === state.epoch && !state.socket) setConnected(false, e.message + ' 已保留配对，等待自动恢复。');
        }).then(function () {
          if (epoch === state.epoch && !state.socket) scheduleReconnect(true);
        });
        return;
      }
      scheduleReconnect(false);
    };
  }
  function reconnectNow() { clearTimeout(state.reconnectTimer); state.reconnectTimer = null; state.reconnectAttempt = 0; state.retryAt = 0; updateOffline(); if (!state.layout) boot(); else connect(); }

  function applyTheme(theme) {
    theme = theme === 'dark' ? 'dark' : 'light'; document.documentElement.setAttribute('data-theme', theme);
    document.querySelector('meta[name="theme-color"]').setAttribute('content', theme === 'dark' ? '#131821' : '#f4f6fb');
    setIcon($('theme-toggle'), theme === 'dark' ? 'sun' : 'moon');
    $('theme-toggle').setAttribute('aria-label', theme === 'dark' ? '切换浅色主题' : '切换深色主题');
  }
  function applyUI(ui) {
    applyTheme(ui.theme); var accent = /^#[0-9a-fA-F]{6}$/.test(ui.accent || '') ? ui.accent : '#3465d9';
    document.documentElement.style.setProperty('--accent', accent);
    $('card-grid').style.gridTemplateColumns = 'repeat(' + clamp(parseInt(ui.columns, 10) || 4, 1, 8) + ', minmax(0, 1fr))';
    var available = Math.max(420, window.innerHeight - 322);
    $('card-grid').style.setProperty('--card-height', Math.max(154, Math.floor((available - 16 * ((ui.rows || 3) - 1)) / clamp(parseInt(ui.rows, 10) || 3, 1, 10))) + 'px');
    if (!ui.keep_awake) releaseWake();
  }
  function activePages() { return state.edit ? state.draft : (state.layout ? state.layout.pages : []); }
  function activePage() { return activePages().filter(function (p) { return p.id === state.pageId; })[0]; }
  function isAppPage(page) { return page && (page.id === 'apps' || /快捷应用|应用/.test(page.name || '') || (page.items.length && page.items.every(function (i) { return i.type === 'app'; }))); }
  function switchPage(id) {
    if (state.edit) { toast('请先保存或取消布局编辑。'); return; }
    state.pageId = id; state.appSearch = ''; state.appGroup = ''; $('app-search').value = ''; renderPage();
  }
  function renderPage() {
    var page = activePage(); if (!page) return;
    clear($('page-tabs')); clear($('card-grid')); state.renderers = [];
    activePages().forEach(function (p) {
      var tab = button(p.name || '未命名页面', 'page-tab' + (p.id === state.pageId ? ' active' : ''), null, function () { switchPage(p.id); });
      tab.setAttribute('aria-pressed', String(p.id === state.pageId));
      tab.appendChild(el('span', 'tab-count', p.items.length)); $('page-tabs').appendChild(tab);
    });
    var appsPage = isAppPage(page);
    $('nav-overview').classList.toggle('active', !appsPage); $('nav-apps').classList.toggle('active', !!appsPage);
    $('page-title').textContent = page.name || '工作台'; $('page-eyebrow').textContent = appsPage ? 'QUICK LAUNCH' : 'DESK OVERVIEW';
    $('page-description').textContent = appsPage ? '常用的应用，一触即达。' : '掌握此刻，保持专注。';
    $('app-tools').hidden = !appsPage || state.edit; $('edit-toolbar').hidden = !state.edit;
    $('edit-label').textContent = state.edit ? '编辑中' : '编辑布局'; $('edit-toggle').setAttribute('aria-pressed', String(state.edit));
    if (appsPage) renderAppGroups();
    var items = page.items.slice();
    if (appsPage && !state.edit && !items.length && state.apps.length) items = state.apps.map(function (a) { return { type: 'app', app_id: a.id, span: 1 }; });
    var visibleCount = 0;
    items.forEach(function (item, index) {
      var app = item.type === 'app' ? state.apps.filter(function (a) { return a.id === item.app_id; })[0] : null;
      if (appsPage && !state.edit && app && ((state.appSearch && String(app.name).toLowerCase().indexOf(state.appSearch.toLowerCase()) < 0) || (state.appGroup && app.group !== state.appGroup))) return;
      var card = makeCard(item, app); visibleCount += 1;
      var columns = clamp(parseInt((state.layout.ui || {}).columns, 10) || 4, 1, 8);
      var span = clamp(parseInt(item.span, 10) || 1, 1, columns);
      card.style.gridColumn = 'span ' + span;
      if (num(item.row_span) > 1) card.style.gridRow = 'span ' + clamp(item.row_span, 1, 3);
      if (span >= 2) card.classList.add('wide-card');
      if (state.edit) card.appendChild(editControls(index, item));
      $('card-grid').appendChild(card);
    });
    if (!visibleCount) {
      var empty = el('div', 'empty-state'); var symbol = el('span'); symbol.appendChild(svgIcon(appsPage ? 'apps' : 'grid')); empty.appendChild(symbol);
      empty.appendChild(el('h3', '', state.appSearch || state.appGroup ? '没有匹配的应用' : (appsPage ? '把常用应用放在手边' : '为这个页面添加第一张卡片')));
      empty.appendChild(el('p', '', state.appSearch || state.appGroup ? '换个关键词或分组试试。' : (appsPage ? '扫描本机软件，多选后一键添加到面板。' : '进入编辑模式，添加系统状态、媒体或控制卡片。')));
      empty.appendChild(button(appsPage ? '扫描并添加应用' : '添加状态卡片', 'btn primary', 'plus', function () { if (appsPage) openScan(); else { if (!state.edit) startEdit(); openCardPicker(); } }));
      $('card-grid').appendChild(empty);
    }
    updateCards(); syncControls();
  }
  function renderAppGroups() {
    clear($('app-group-filters'));
    var groups = []; state.apps.forEach(function (a) { if (a.group && groups.indexOf(a.group) < 0) groups.push(a.group); });
    var all = button('全部', 'chip' + (!state.appGroup ? ' active' : ''), null, function () { state.appGroup = ''; renderPage(); }); $('app-group-filters').appendChild(all);
    groups.forEach(function (id) {
      var g = state.groups.filter(function (x) { return typeof x === 'object' && x.id === id; })[0];
      $('app-group-filters').appendChild(button(g ? g.name : id, 'chip' + (state.appGroup === id ? ' active' : ''), null, function () { state.appGroup = id; renderPage(); }));
    });
  }
  function cardHead(card, title, icon, kicker) {
    var head = el('div', 'card-head'), label = el('div', 'card-heading'); label.appendChild(svgIcon(icon)); label.appendChild(el('span', '', title));
    head.appendChild(label); var right = el('span', 'card-kicker', kicker || ''); head.appendChild(right); card.appendChild(head); return right;
  }
  function meter(parent) { var wrap = el('div', 'meter'), fill = el('div', 'meter-fill'); wrap.appendChild(fill); parent.appendChild(wrap); return fill; }
  function makeCard(item, app) {
    var card = el('article', 'card');
    if (item.type === 'app') { makeAppCard(card, app, item.app_id); return card; }
    if (item.type === 'volume') { makeVolumeCard(card); return card; }
    if (item.type === 'media') { makeMediaCard(card); return card; }
    if (item.type === 'power') { makePowerCard(card, item.actions); return card; }
    var metric = item.metric;
    if (metric === 'cpu') makeCPU(card);
    else if (metric === 'memory') makeMemory(card);
    else if (metric === 'network') makeNetwork(card);
    else if (metric === 'disk') makeDisks(card);
    else makeSimpleStat(card, metric);
    return card;
  }
  function makeCPU(card) {
    var kicker = cardHead(card, 'CPU 负载', 'cpu', 'LIVE · 60 SEC');
    var body = el('div', 'cpu-body'), left = el('div', 'cpu-number'), value = el('div', 'metric-value', '—'), pill = el('span', 'status-pill', '等待采样');
    left.appendChild(value); left.appendChild(pill); body.appendChild(left);
    var canvas = el('canvas', 'cpu-chart'); canvas.setAttribute('aria-label', 'CPU 最近 60 个采样点曲线'); canvas.setAttribute('role', 'img'); body.appendChild(canvas); card.appendChild(body);
    var meta = el('div', 'metric-meta'), cores = el('span', '', '— 核心'), legend = el('span', '', '实时使用率'); meta.appendChild(cores); meta.appendChild(legend); card.appendChild(meta);
    state.renderers.push(function () {
      var cpu = state.system && state.system.cpu; if (!cpu) return;
      var p = percent(cpu.percent); clear(value); value.appendChild(document.createTextNode(p.toFixed(1))); value.appendChild(el('small', '', '%'));
      cores.textContent = num(cpu.cores) + ' 逻辑核心'; pill.textContent = p > 95 ? '高负载' : (p > 80 ? '负载较高' : '运行平稳');
      pill.className = 'status-pill' + (p > 95 ? ' danger' : (p > 80 ? ' warning' : '')); kicker.textContent = state.connected ? 'LIVE · 60 SEC' : '最后一次采样';
      drawCPU(canvas, Array.isArray(cpu.history) ? cpu.history : [p]);
    });
  }
  function drawCPU(canvas, history) {
    var rect = canvas.getBoundingClientRect(), w = Math.max(50, rect.width), h = 70, dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); }
    var c = canvas.getContext('2d'); if (!c) return; c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, w, h);
    var style = getComputedStyle(document.documentElement), line = style.getPropertyValue('--line').trim(), accent = style.getPropertyValue('--accent').trim();
    c.strokeStyle = line; c.lineWidth = 1;
    [12, 34, 56].forEach(function (y) { c.beginPath(); c.moveTo(0, y); c.lineTo(w, y); c.stroke(); });
    var data = history.slice(-60); if (!data.length) return;
    var points = data.map(function (v, i) { return [data.length === 1 ? w : i * w / (data.length - 1), 65 - percent(v) * .58]; });
    var gradient = c.createLinearGradient(0, 0, 0, h); gradient.addColorStop(0, accent); gradient.addColorStop(1, style.getPropertyValue('--surface').trim());
    c.beginPath(); c.moveTo(points[0][0], h); points.forEach(function (p) { c.lineTo(p[0], p[1]); }); c.lineTo(points[points.length - 1][0], h); c.closePath(); c.globalAlpha = .12; c.fillStyle = gradient; c.fill(); c.globalAlpha = 1;
    c.beginPath(); points.forEach(function (p, i) { if (!i) c.moveTo(p[0], p[1]); else c.lineTo(p[0], p[1]); }); c.strokeStyle = accent; c.lineWidth = 2; c.lineJoin = 'round'; c.stroke();
  }
  function makeMemory(card) {
    cardHead(card, '内存', 'memory', 'RAM'); var value = el('div', 'metric-value', '—'); card.appendChild(value); var fill = meter(card);
    var detail = el('div', 'memory-detail'), used = el('span', '', '— 已用'), total = el('span', '', '— 总量'); detail.appendChild(used); detail.appendChild(total); card.appendChild(detail);
    state.renderers.push(function () { var m = state.system && state.system.memory; if (!m) return; clear(value); value.appendChild(document.createTextNode(percent(m.percent).toFixed(0))); value.appendChild(el('small', '', '%')); fill.style.width = percent(m.percent) + '%'; used.textContent = bytes(m.used) + ' 已用'; total.textContent = '/ ' + bytes(m.total); });
  }
  function makeNetwork(card) {
    cardHead(card, '网络速率', 'network', '实时'); var body = el('div', 'network-body');
    function stat(icon, title) { var block = el('div', 'network-stat'), label = el('small'); label.appendChild(svgIcon(icon)); label.appendChild(document.createTextNode(title)); var value = el('strong', '', '—'), unit = el('em', '', 'KB/s'); block.appendChild(label); block.appendChild(value); block.appendChild(unit); body.appendChild(block); return [value, unit]; }
    var down = stat('down', '下载'); body.appendChild(el('div', 'network-divider')); var up = stat('up', '上传'); card.appendChild(body);
    state.renderers.push(function () { var n = state.system && state.system.network; if (!n) return; var d = rate(n.down), u = rate(n.up); down[0].textContent = d[0]; down[1].textContent = d[1]; up[0].textContent = u[0]; up[1].textContent = u[1]; });
  }
  function makeDisks(card) {
    var kicker = cardHead(card, '磁盘空间', 'disk', 'STORAGE'); var list = el('div', 'disk-scroll'); card.appendChild(list); var signature = '', rows = [];
    state.renderers.push(function () {
      var disks = state.system && state.system.disks; if (!Array.isArray(disks)) return;
      var sig = disks.map(function (d) { return d.mount; }).join('|');
      if (sig !== signature || !rows.length) {
        signature = sig; clear(list); rows = [];
        disks.forEach(function (disk) {
          var row = el('div', 'disk-row'), sym = el('span', 'disk-icon'); sym.appendChild(svgIcon('disk')); row.appendChild(sym);
          var info = el('div', 'disk-info'), heading = el('div', 'disk-name'), title = el('strong', '', disk.mount || '磁盘'), detail = el('small'); heading.appendChild(title); heading.appendChild(detail); info.appendChild(heading); var fill = meter(info); row.appendChild(info); list.appendChild(row); rows.push([detail, fill]);
        });
        if (!disks.length) list.appendChild(el('p', 'module-note', '未检测到磁盘信息'));
      }
      disks.forEach(function (d, i) { rows[i][0].textContent = bytes(d.used) + ' / ' + bytes(d.total) + ' · ' + Math.round(percent(d.percent)) + '%'; rows[i][1].style.width = percent(d.percent) + '%'; rows[i][1].style.background = percent(d.percent) > 90 ? 'var(--amber)' : 'var(--green)'; }); kicker.textContent = disks.length + ' 个分区';
    });
  }
  function makeSimpleStat(card, metric) {
    card.classList.add('simple-stat'); cardHead(card, METRICS[metric] || '状态', metric === 'uptime' ? 'clock' : (metric === 'battery' ? 'battery' : 'window'));
    var value = el('div', metric === 'foreground' ? 'foreground-text' : 'metric-value', '—'), note = el('p', 'module-note', '等待电脑状态'); card.appendChild(value); card.appendChild(note);
    state.renderers.push(function () {
      var s = state.system; if (!s) return;
      if (metric === 'uptime') { value.textContent = Math.floor(num(s.uptime) / 3600) + 'h'; note.textContent = uptime(s.uptime); }
      else if (metric === 'battery') { value.textContent = s.battery ? Math.round(percent(s.battery.percent)) + '%' : '无电池'; note.textContent = s.battery ? (s.battery.charging ? '已接电源 · 充电中' : '正在使用电池') : '台式电脑或电池信息不可用'; }
      else if (metric === 'foreground') { value.textContent = s.foreground ? s.foreground.process || '桌面' : '桌面'; note.textContent = s.foreground ? s.foreground.title || '没有前台窗口标题' : '没有前台窗口'; note.title = note.textContent; }
      else { value.textContent = '暂不支持'; note.textContent = '请编辑卡片选择状态指标'; }
    });
  }
  function makeVolumeCard(card) {
    cardHead(card, '主音量', 'volume', 'AUDIO'); var top = el('div', 'volume-top'), value = el('div', 'metric-value', '—'); top.appendChild(value); card.appendChild(top);
    var controls = el('div', 'volume-controls'), mute = control(button('', 'mute-button', 'volume', function () {
      if (!state.audio || state.audio.available !== true || !requireRemote()) return;
      mute.setAttribute('data-busy', 'true'); syncControls(); remote('/api/audio/mute', { muted: !state.audio.muted }).then(function (r) { if (r && typeof r.muted === 'boolean') state.audio.muted = r.muted; mute.removeAttribute('data-busy'); updateCards(); });
    }), 'audio'); mute.setAttribute('aria-label', '静音或取消静音');
    var range = control(el('input'), 'audio'); range.type = 'range'; range.min = '0'; range.max = '100'; range.step = '1'; range.value = '0'; range.setAttribute('aria-label', '主音量');
    range.addEventListener('input', function () { if (!requireRemote()) return; state.volumeEditing = true; state.volumeDesired = Number(range.value); showVolume(value, range, state.volumeDesired); queueVolume(); });
    range.addEventListener('change', function () { state.volumeEditing = false; queueVolume(); });
    range.addEventListener('blur', function () { state.volumeEditing = false; });
    controls.appendChild(mute); controls.appendChild(range); card.appendChild(controls); var note = el('p', 'module-note', '正在读取音频设备'); card.appendChild(note);
    state.renderers.push(function () {
      var a = state.audio; if (!a) return;
      if (!state.volumeEditing && state.volumeDesired === null && !state.volumeSending) showVolume(value, range, percent(a.volume));
      mute.classList.toggle('is-muted', !!a.muted); setIcon(mute, a.muted ? 'muted' : 'volume'); mute.setAttribute('aria-pressed', String(!!a.muted));
      mute.setAttribute('aria-label', a.muted ? '取消静音' : '静音');
      note.textContent = a.available !== true ? a.message || '电脑端音频模块不可用' : (a.muted ? '已静音 · ' : '') + (a.device || '默认音频设备'); note.title = note.textContent;
    });
  }
  function showVolume(value, range, v) { clear(value); value.appendChild(document.createTextNode(Math.round(v))); value.appendChild(el('small', '', '%')); range.value = v; range.style.backgroundImage = 'linear-gradient(to right,var(--accent) 0%,var(--accent) ' + v + '%,var(--line) ' + v + '%,var(--line) 100%)'; range.setAttribute('aria-valuetext', Math.round(v) + '%'); }
  function cancelVolume() { clearTimeout(state.volumeTimer); state.volumeTimer = null; state.volumeDesired = null; state.volumeEditing = false; }
  function queueVolume() {
    if (state.volumeDesired === null || state.volumeSending || state.volumeTimer) return;
    if (!controlsAvailable() || !state.audio || state.audio.available !== true) { cancelVolume(); return; }
    state.volumeTimer = setTimeout(sendVolume, Math.max(0, 50 - (Date.now() - state.volumeLast)));
  }
  async function sendVolume() {
    state.volumeTimer = null; if (state.volumeDesired === null || !controlsAvailable() || !state.audio || state.audio.available !== true) { cancelVolume(); return; }
    var v = state.volumeDesired, epoch = state.epoch; state.volumeDesired = null; state.volumeSending = true; state.volumeLast = Date.now();
    try { var a = await api('/api/audio/volume', 'POST', { value: v }); if (epoch === state.epoch && state.audio) state.audio.volume = typeof a.volume === 'number' ? a.volume : v; }
    catch (e) { if (epoch === state.epoch) { toast(e.message, true); cancelVolume(); } }
    finally { state.volumeSending = false; if (state.volumeDesired !== null) queueVolume(); else updateCards(); }
  }
  function makeMediaCard(card) {
    var kicker = cardHead(card, '正在播放', 'music', 'MEDIA'); var body = el('div', 'media-body'), cover = el('div', 'media-cover'); cover.appendChild(svgIcon('music')); body.appendChild(cover);
    var info = el('div', 'media-info'), title = el('strong', 'media-title', '没有正在播放的媒体'), artist = el('span', 'media-artist', '在电脑上打开音乐或视频播放器'); info.appendChild(title); info.appendChild(artist); body.appendChild(info);
    var actions = el('div', 'media-actions'), play;
    [['previous', 'previous', '上一首'], ['play_pause', 'play', '播放或暂停'], ['next', 'next', '下一首']].forEach(function (entry) {
      var b = control(iconButton(entry[1], entry[2], function () {
        if (!state.media || state.media.available !== true || !state.media.active || !requireRemote()) return;
        b.setAttribute('data-busy', 'true'); syncControls(); remote('/api/media/control', { action: entry[0] }).then(function () { b.removeAttribute('data-busy'); syncControls(); });
      }), 'media'); if (entry[0] === 'play_pause') { b.classList.add('play-button'); play = b; } actions.appendChild(b);
    }); body.appendChild(actions); card.appendChild(body);
    var progress = el('div', 'media-progress'), fill = el('span'); progress.appendChild(fill); card.appendChild(progress); var times = el('div', 'media-times'), position = el('span', '', '0:00'), end = el('span', '', '0:00'); times.appendChild(position); times.appendChild(end); card.appendChild(times); var coverKey = '';
    state.renderers.push(function () {
      var m = state.media; if (!m) return;
      title.textContent = m.available !== true ? '媒体模块不可用' : (m.active ? m.title || '未命名媒体' : '没有正在播放的媒体'); title.title = title.textContent;
      artist.textContent = m.available !== true ? m.message || '请检查电脑端媒体服务' : (m.active ? [m.artist, m.album].filter(Boolean).join(' · ') || '未知艺术家' : '在电脑上打开音乐或视频播放器');
      kicker.textContent = m.player || 'MEDIA'; setIcon(play, m.playing ? 'pause' : 'play'); play.setAttribute('aria-label', m.playing ? '暂停' : '播放');
      fill.style.width = (num(m.duration) > 0 ? clamp(num(m.position) / m.duration * 100, 0, 100) : 0) + '%'; position.textContent = duration(m.position); end.textContent = duration(m.duration);
      var key = m.active ? safeImagePath(m.cover) : '';
      if (key !== coverKey) { coverKey = key; clear(cover); cover.appendChild(svgIcon('music')); if (key) imageURL(key).then(function (url) { if (url && key === coverKey && document.documentElement.contains(cover)) { var img = el('img'); img.alt = '当前媒体封面'; img.src = url; img.addEventListener('load', function () { if (key === coverKey) { clear(cover); cover.appendChild(img); } }); } }); }
    });
  }
  function makePowerCard(card, actions) {
    cardHead(card, '电源与会话', 'power', '谨慎操作'); var row = el('div', 'power-actions');
    (Array.isArray(actions) ? actions : Object.keys(POWER)).forEach(function (action) {
      if (!POWER[action]) return;
      var b = control(button('', 'power-action' + (/restart|shutdown/.test(action) ? ' risky' : ''), action, function () { openPower(action); })); b.appendChild(el('small', '', SHORT_POWER[action])); b.setAttribute('aria-label', POWER[action]); row.appendChild(b);
    }); card.appendChild(row); card.appendChild(el('p', 'power-note', '所有操作均需确认并长按 1.5 秒'));
  }
  function makeAppCard(card, app, id) {
    card.classList.add('app-card'); if (state.highlights.has(id)) card.classList.add('highlight');
    if (!app) { card.appendChild(el('p', 'muted', '应用已从配置中移除')); return; }
    var launch = control(button('', 'app-launch', null, function () { launchApp(app, card, launch, status); }));
    launch.appendChild(appIcon(app.name, app.icon)); launch.appendChild(el('strong', '', app.name || '未命名应用')); var status = el('span', 'app-status'); launch.appendChild(status); card.appendChild(launch);
    var tools = el('div', 'app-actions');
    var changeIcon = control(iconButton('image', '更换图标', function (event) { event.stopPropagation(); openIconPicker(app); }), 'config'); changeIcon.classList.add('app-change-icon');
    var editPath = control(iconButton('edit', '修改启动地址', function (event) { event.stopPropagation(); openAppPath(app); }), 'config'); editPath.classList.add('app-edit-path');
    var remove = iconButton('trash', '从面板移除 ' + app.name, function (event) { event.stopPropagation(); confirmRemove(app); }); remove.classList.add('app-remove');
    tools.appendChild(changeIcon); tools.appendChild(editPath); tools.appendChild(remove); card.appendChild(tools);
    state.renderers.push(function () {
      if (state.appBusy.has(app.id)) { clear(status); status.appendChild(el('span', 'spinner')); status.appendChild(document.createTextNode('启动中…')); launch.setAttribute('data-busy', 'true'); card.classList.add('busy'); }
      else { launch.removeAttribute('data-busy'); card.classList.remove('busy'); clear(status); if (app.running) status.appendChild(el('span', 'dot')); status.appendChild(document.createTextNode(app.running ? '正在运行 · 触碰切换' : '触碰启动')); status.className = 'app-status' + (app.running ? ' running' : ''); }
      remove.disabled = !state.connected || state.demo || state.edit;
    });
  }
  async function launchApp(app, card, launch, status) {
    if (!requireRemote() || state.appBusy.has(app.id)) return;
    state.appBusy.add(app.id); card.classList.remove('error'); updateCards();
    try {
      var r = await api('/api/apps/' + encodeURIComponent(app.id) + '/launch', 'POST');
      var messages = { started: '已启动', focused: '已切换到前台', already_running: '已在运行', dispatched: '启动指令已发送' };
      toast(app.name + ' · ' + (r.message || messages[r.action] || '操作完成'));
      if (r.action !== 'dispatched') app.running = true;
    } catch (e) { card.classList.add('error'); toast(e.message, true); }
    finally { state.appBusy.delete(app.id); updateCards(); }
  }
  function updateCards() {
    state.renderers.forEach(function (render) { try { render(); } catch (e) { /* 单张卡片异常不影响其他模块。 */ } });
    var s = state.system;
    if (s) { $('foreground-summary').textContent = '前台窗口 · ' + (s.foreground ? s.foreground.title || s.foreground.process || '桌面' : '桌面'); $('foreground-summary').title = $('foreground-summary').textContent; $('uptime-summary').textContent = '运行时间 · ' + uptime(s.uptime); }
    syncControls();
  }

  function openModal(title, drawer, subtitle) {
    closeModal(); var lastFocus = document.activeElement, root = $('modal-root'); clear(root); root.hidden = false;
    var backdrop = el('div', 'modal-backdrop' + (drawer ? ' drawer-backdrop' : '')), box = el('section', 'modal' + (drawer ? ' drawer' : ''));
    box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.setAttribute('aria-labelledby', 'modal-title'); box.tabIndex = -1;
    var head = el('div', 'modal-header'), heading = el('div'); if (subtitle) heading.appendChild(el('span', 'eyebrow', subtitle)); var h = el('h2', '', title); h.id = 'modal-title'; heading.appendChild(h); head.appendChild(heading);
    head.appendChild(iconButton('close', '关闭弹窗', closeModal)); box.appendChild(head); var content = el('div', 'modal-content'), footer = el('div', 'modal-footer'); box.appendChild(content); box.appendChild(footer); backdrop.appendChild(box); root.appendChild(backdrop);
    var previousOverflow = document.body.style.overflow; document.body.style.overflow = 'hidden';
    var modal = { box: box, content: content, footer: footer, cleanup: [], lastFocus: lastFocus, overflow: previousOverflow, busy: false };
    state.modal = modal;
    backdrop.addEventListener('click', function (e) { if (e.target === backdrop) closeModal(); });
    box.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { e.preventDefault(); closeModal(); return; }
      if (e.key !== 'Tab') return;
      var nodes = Array.prototype.filter.call(box.querySelectorAll('button,input,select,[tabindex="0"]'), function (n) { return !n.disabled && n.offsetParent !== null; });
      if (!nodes.length) { e.preventDefault(); box.focus(); return; }
      var first = nodes[0], last = nodes[nodes.length - 1];
      if (e.shiftKey && (document.activeElement === first || document.activeElement === box)) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
    setTimeout(function () { if (state.modal === modal) { var input = box.querySelector('input:not([type=checkbox]),select'); if (input && !drawer) input.focus(); else box.focus(); } }, 0);
    return modal;
  }
  function closeModal() {
    var m = state.modal; if (!m) return;
    if (m.busy) { toast('请求正在处理，请稍候。'); return; }
    state.modal = null; m.cleanup.forEach(function (f) { f(); }); document.body.style.overflow = m.overflow;
    clear($('modal-root')); $('modal-root').hidden = true;
    if (m.lastFocus && document.documentElement.contains(m.lastFocus)) m.lastFocus.focus();
  }
  async function iconLibrary() {
    var result = await api('/api/icon-library');
    if (!Array.isArray(result.icons)) throw new Error('服务返回的图标库无效。');
    var seen = new Set();
    return result.icons.filter(function (item) {
      if (!item || typeof item.id !== 'string' || !item.id || typeof item.name !== 'string' || !/^\/api\/icon-library\//.test(safeImagePath(item.url)) || seen.has(item.id)) return false;
      seen.add(item.id); return true;
    });
  }
  function parentPath(value) {
    var p = String(value || '').replace(/[\\/]+$/, '');
    if (!p) return '';
    var index = Math.max(p.lastIndexOf('\\'), p.lastIndexOf('/'));
    if (index < 0) return '';
    var parent = p.slice(0, index);
    return /^[A-Za-z]:$/.test(parent) ? parent + '\\' : parent;
  }
  function openBrowse(onPick) {
    var host = state.modal, lastFocus = document.activeElement;
    var layer = el('div', 'browse-layer'), backdrop = el('div', 'browse-backdrop'), panel = el('section', 'browse-panel');
    panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-modal', 'true'); panel.setAttribute('aria-labelledby', 'browse-title'); panel.tabIndex = -1;
    var head = el('div', 'modal-header'), heading = el('div'); heading.appendChild(el('span', 'eyebrow', 'BROWSE THIS PC'));
    var title = el('h2', '', '选择启动文件'); title.id = 'browse-title'; heading.appendChild(title); head.appendChild(heading);
    head.appendChild(iconButton('close', '关闭目录浏览', closeBrowse)); panel.appendChild(head);
    var bar = el('div', 'browse-bar'), up = iconButton('up', '上一级', function () { if (upTarget) load(upTarget); }), pathText = el('p', 'browse-path', '此电脑');
    up.classList.add('browse-up'); up.disabled = true; bar.appendChild(up); bar.appendChild(pathText); panel.appendChild(bar);
    var driveBar = el('div', 'browse-drives'); driveBar.setAttribute('role', 'group'); driveBar.setAttribute('aria-label', '驱动器'); panel.appendChild(driveBar);
    var status = el('p', 'browse-status', '正在读取目录…'); status.setAttribute('role', 'status'); panel.appendChild(status);
    var list = el('div', 'browse-list'); panel.appendChild(list);
    var foot = el('div', 'modal-footer'); foot.appendChild(button('取消', 'btn subtle', null, closeBrowse)); panel.appendChild(foot);
    backdrop.addEventListener('click', function () { closeBrowse(); });
    layer.appendChild(backdrop); layer.appendChild(panel); document.body.appendChild(layer);
    var current = '', upTarget = '', loading = false, disposed = false;
    if (host && host.cleanup) host.cleanup.push(closeBrowse);
    function closeBrowse() {
      if (disposed) return;
      disposed = true; if (layer.parentNode) layer.parentNode.removeChild(layer);
      if (lastFocus && document.documentElement.contains(lastFocus)) lastFocus.focus();
    }
    function pick(path) { if (disposed) return; closeBrowse(); if (typeof onPick === 'function') onPick(path); }
    function renderEntries(entries, truncated) {
      clear(list);
      var usable = entries.filter(function (entry) { return entry && typeof entry.path === 'string' && typeof entry.name === 'string'; });
      if (!usable.length) { list.appendChild(el('p', 'module-note', '此目录没有可显示的项目。')); return; }
      usable.forEach(function (entry) {
        var isDir = entry.type === 'dir';
        var row = button('', 'browse-entry' + (isDir ? ' is-dir' : ''), isDir ? 'folder' : 'file', function () { if (isDir) load(entry.path); else pick(entry.path); });
        row.appendChild(el('span', 'browse-entry-name', entry.name));
        row.appendChild(el('span', 'browse-entry-type', isDir ? '文件夹' : '文件')); list.appendChild(row);
      });
      if (truncated) list.appendChild(el('p', 'module-note', '条目较多，仅显示前 ' + usable.length + ' 项。'));
    }
    async function load(target) {
      if (loading || disposed) return;
      loading = true; up.disabled = true; status.className = 'browse-status'; status.textContent = '正在读取目录…'; clear(list);
      try {
        var result = await api('/api/browse?path=' + encodeURIComponent(target || ''));
        if (disposed) return;
        current = typeof result.path === 'string' ? result.path : (target || '');
        upTarget = typeof result.parent === 'string' ? result.parent : '';
        pathText.textContent = current || '此电脑'; pathText.title = pathText.textContent; up.disabled = !upTarget;
        var entries = Array.isArray(result.entries) ? result.entries : [];
        renderEntries(entries, result.truncated === true);
        status.textContent = entries.length ? '共 ' + entries.length + ' 项' : '';
      } catch (e) {
        if (disposed) return;
        current = target || ''; upTarget = current ? parentPath(current) : '';
        pathText.textContent = current || '此电脑'; pathText.title = pathText.textContent; up.disabled = !upTarget;
        status.className = 'browse-status error';
        status.textContent = (target ? '无法打开这个位置：' : '无法读取驱动器：') + e.message;
        clear(list); list.appendChild(button('重新加载', 'btn subtle', 'refresh', function () { load(current); }));
      } finally { loading = false; }
    }
    async function loadDrives() {
      try {
        var result = await api('/api/drives'); if (disposed) return;
        var items = Array.isArray(result.drives) ? result.drives : []; clear(driveBar);
        items.forEach(function (drive) {
          if (!drive || typeof drive.path !== 'string') return;
          var chip = button(drive.name || drive.path, 'chip browse-drive', 'disk', function () { load(drive.path); });
          chip.title = drive.path; driveBar.appendChild(chip);
        });
      } catch (e) { if (!disposed) { clear(driveBar); driveBar.appendChild(el('span', 'module-note', '驱动器列表不可用')); } }
    }
    panel.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') { event.preventDefault(); closeBrowse(); return; }
      if (event.key !== 'Tab') return;
      var nodes = Array.prototype.filter.call(panel.querySelectorAll('button,input'), function (n) { return !n.disabled && n.offsetParent !== null; });
      if (!nodes.length) { event.preventDefault(); panel.focus(); return; }
      var first = nodes[0], last = nodes[nodes.length - 1];
      if (event.shiftKey && (document.activeElement === first || document.activeElement === panel)) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    });
    loadDrives(); load('');
    setTimeout(function () { if (!disposed) panel.focus(); }, 0);
  }
  function openAppPath(app) {
    if (!state.connected || state.edit) return;
    var m = openModal('修改启动地址', false, 'LAUNCH PATH');
    m.content.appendChild(el('p', 'modal-message', '为「' + app.name + '」指定可执行文件的完整路径。路径只在电脑端使用。'));
    var form = el('div', 'path-form'), label = el('label', '', '启动地址'), row = el('div', 'path-field');
    var input = el('input'); input.placeholder = '例如 F:\\software\\KOOK\\KOOK.exe'; input.maxLength = 512; input.autocomplete = 'off'; input.spellcheck = false;
    var browse = button('浏览电脑…', 'btn subtle path-browse', 'folder', function () { openBrowse(function (value) { input.value = value; input.focus(); }); });
    row.appendChild(input); row.appendChild(browse); label.appendChild(row); form.appendChild(label); m.content.appendChild(form);
    var error = el('p', 'form-error path-error'); error.setAttribute('role', 'alert'); m.content.appendChild(error);
    m.content.appendChild(el('p', 'module-note', '保存后仅更新这台电脑上的快捷配置，不会移动或修改文件。'));
    var cancel = button('取消', 'btn subtle', null, closeModal), save = button('保存地址', 'btn primary', 'check', submit);
    m.footer.appendChild(cancel); m.footer.appendChild(save);
    m.sync = function () { var unavailable = !state.connected || state.edit || m.busy; input.disabled = unavailable; browse.disabled = unavailable; cancel.disabled = m.busy; save.disabled = unavailable; };
    async function submit() {
      if (!state.connected || state.edit || m.busy) return;
      var value = input.value.trim();
      if (!value) { error.textContent = '请填写完整的启动地址，或点击「浏览电脑…」选择文件。'; input.focus(); return; }
      m.busy = true; error.textContent = ''; m.sync();
      try {
        await api('/api/apps/' + encodeURIComponent(app.id), 'PUT', { path: value });
        m.busy = false; closeModal(); await refreshConfig(); toast('启动地址已更新。');
      } catch (e) {
        m.busy = false;
        if (state.modal === m) {
          error.textContent = e.message + (e.status === 404 ? ' 请确认该文件仍然存在。' : (e.status === 400 ? ' 请填写完整的可执行文件路径。' : ''));
          m.sync();
        }
      }
    }
    syncControls();
  }
  function openManualAdd() {
    if (!state.connected || state.edit) { toast('连接恢复并退出编辑后可以添加应用。'); return; }
    var pageId = state.pageId, m = openModal('手动添加应用', false, 'ADD MANUALLY');
    m.content.appendChild(el('p', 'modal-message', '扫描找不到的软件，可以直接指定它的启动文件。'));
    var form = el('div', 'manual-form'), nameLabel = el('label', '', '应用名称'), name = el('input');
    name.placeholder = '例如：KOOK'; name.maxLength = 64; name.autocomplete = 'off'; nameLabel.appendChild(name); form.appendChild(nameLabel);
    var pathLabel = el('label', '', '启动地址'), row = el('div', 'path-field'), pathInput = el('input');
    pathInput.placeholder = '例如 F:\\software\\KOOK\\KOOK.exe'; pathInput.maxLength = 512; pathInput.autocomplete = 'off'; pathInput.spellcheck = false;
    var browse = button('浏览电脑…', 'btn subtle path-browse', 'folder', function () { openBrowse(function (value) { pathInput.value = value; pathInput.focus(); }); });
    row.appendChild(pathInput); row.appendChild(browse); pathLabel.appendChild(row); form.appendChild(pathLabel); m.content.appendChild(form);
    var error = el('p', 'form-error path-error'); error.setAttribute('role', 'alert'); m.content.appendChild(error);
    var iconBox = el('div', 'manual-icons'), grid = el('div', 'icon-library-grid manual-icon-grid');
    iconBox.appendChild(el('span', 'mini-label', '可选图标 · 默认使用系统图标')); iconBox.appendChild(grid); m.content.appendChild(iconBox);
    grid.setAttribute('role', 'group'); grid.setAttribute('aria-label', '可选应用图标');
    var icons = [], selected = null, loading = true;
    var cancel = button('取消', 'btn subtle', null, closeModal), save = button('保存应用', 'btn primary', 'check', submit);
    m.footer.appendChild(cancel); m.footer.appendChild(save);
    m.sync = function () {
      var unavailable = !state.connected || state.edit || m.busy;
      name.disabled = unavailable; pathInput.disabled = unavailable; browse.disabled = unavailable; cancel.disabled = m.busy; save.disabled = unavailable;
      Array.prototype.forEach.call(grid.querySelectorAll('button'), function (b) { b.disabled = unavailable || loading; });
    };
    function renderIcons() {
      if (state.modal !== m) return; clear(grid);
      if (loading) { grid.appendChild(el('p', 'module-note', '正在读取图标库…')); return; }
      if (!icons.length) { grid.appendChild(el('p', 'module-note', '暂时没有可选图标，将使用系统图标。')); return; }
      icons.forEach(function (item) {
        var choice = button('', 'icon-choice' + (item.id === selected ? ' selected' : ''), null, function () {
          selected = selected === item.id ? null : item.id; renderIcons();
          var focused = Array.prototype.filter.call(grid.querySelectorAll('button'), function (b) { return b.getAttribute('data-icon-id') === selected; })[0];
          if (focused) focused.focus(); else name.focus();
        });
        choice.setAttribute('data-icon-id', item.id); choice.setAttribute('aria-pressed', String(item.id === selected));
        choice.appendChild(appIcon(item.name, item.url, 'app-icon icon-preview')); choice.appendChild(el('span', 'icon-choice-name', item.name)); grid.appendChild(choice);
      });
    }
    async function loadIcons() {
      loading = true; renderIcons();
      try { icons = await iconLibrary(); }
      catch (e) { icons = []; if (state.modal === m) error.textContent = '图标库加载失败：' + e.message; }
      finally { loading = false; if (state.modal === m) { renderIcons(); m.sync(); } }
    }
    async function submit() {
      if (!state.connected || state.edit || m.busy) return;
      var nameValue = name.value.trim(), pathValue = pathInput.value.trim();
      if (!nameValue) { error.textContent = '请填写应用名称。'; name.focus(); return; }
      if (!pathValue) { error.textContent = '请填写启动地址，或点击「浏览电脑…」选择文件。'; pathInput.focus(); return; }
      m.busy = true; error.textContent = ''; m.sync();
      try {
        await api('/api/apps/custom', 'POST', { name: nameValue, path: pathValue, icon_id: selected, page_id: pageId, group: '常用' });
        m.busy = false; closeModal(); await refreshConfig(); toast('已添加到面板');
      } catch (e) {
        m.busy = false;
        if (state.modal === m) { error.textContent = e.message; m.sync(); }
      }
    }
    m.sync(); loadIcons();
  }
  function openIconPicker(app) {
    if (!state.connected || state.edit) return;
    var m = openModal('更换应用图标', false, 'APP ICONS'); m.box.classList.add('icon-picker');
    m.content.appendChild(el('p', 'modal-message', '为「' + app.name + '」选择高清图标。保存到电脑后，刷新或重新打开页面仍会保留。'));
    var error = el('p', 'form-error icon-error'); error.setAttribute('role', 'alert'); m.content.appendChild(error);
    var grid = el('div', 'icon-library-grid'); grid.setAttribute('role', 'group'); grid.setAttribute('aria-label', '可选应用图标'); m.content.appendChild(grid);
    var icons = [], selected = typeof app.icon_id === 'string' ? app.icon_id : null, loading = false;
    var restore = button('恢复系统图标', 'btn subtle icon-restore', 'refresh', function () { submit(null); });
    var cancel = button('取消', 'btn subtle', null, closeModal);
    var save = button('保存图标', 'btn primary icon-save', 'check', function () { submit(selected); });
    m.footer.appendChild(restore); m.footer.appendChild(cancel); m.footer.appendChild(save);
    m.sync = function () {
      var unavailable = !state.connected || state.edit || m.busy;
      restore.disabled = unavailable; cancel.disabled = m.busy;
      save.disabled = unavailable || loading || !icons.some(function (i) { return i.id === selected; });
      Array.prototype.forEach.call(grid.querySelectorAll('button'), function (b) { b.disabled = unavailable || loading; });
    };
    function render() {
      if (state.modal !== m) return; clear(grid);
      if (loading) grid.appendChild(el('p', 'module-note', '正在读取图标库…'));
      else icons.forEach(function (item) {
        var choice = button('', 'icon-choice' + (item.id === selected ? ' selected' : ''), null, function () {
          selected = item.id; render();
          var focused = Array.prototype.filter.call(grid.querySelectorAll('button'), function (b) { return b.getAttribute('data-icon-id') === selected; })[0];
          if (focused) focused.focus();
        });
        choice.setAttribute('data-icon-id', item.id); choice.setAttribute('aria-pressed', String(item.id === selected));
        choice.appendChild(appIcon(item.name, item.url, 'app-icon icon-preview')); choice.appendChild(el('span', 'icon-choice-name', item.name)); grid.appendChild(choice);
      });
      m.sync();
    }
    async function load() {
      if (loading || !state.connected) return; loading = true; error.textContent = ''; render();
      try {
        icons = await iconLibrary();
        if (state.modal !== m) return;
        if (!icons.length) throw new Error('暂无可选图标，仍可恢复系统图标。');
      } catch (e) {
        if (state.modal === m) {
          error.textContent = '图标库加载失败：' + e.message;
        }
      } finally {
        loading = false;
        if (state.modal === m) { if (icons.length) render(); else { clear(grid); grid.appendChild(button('重新加载图标库', 'btn subtle', 'refresh', load)); m.sync(); } }
      }
    }
    async function submit(iconId) {
      if (!state.connected || state.edit || m.busy) return;
      m.busy = true; error.textContent = ''; m.sync(); var saved = false;
      try {
        await api('/api/apps/' + encodeURIComponent(app.id) + '/icon', 'PUT', { icon_id: iconId }); saved = true;
        releaseIcons(); await refreshConfig();
        m.busy = false; if (state.modal === m) closeModal();
        toast(iconId === null ? '已恢复系统图标并保存到电脑。' : '图标已保存到电脑。');
      } catch (e) {
        m.busy = false;
        if (state.modal === m) { error.textContent = (saved ? '图标已保存，但刷新失败，请重试：' : '保存失败：') + e.message; m.sync(); }
      }
    }
    load();
  }
  function confirmRemove(app) {
    if (!requireRemote()) return;
    var m = openModal('移除快捷应用', false, 'REMOVE SHORTCUT');
    m.content.appendChild(el('p', 'modal-message', '确定从所有面板移除「' + app.name + '」吗？\n这只删除 DeskTouch 快捷配置，不会卸载或关闭电脑上的软件。'));
    m.footer.appendChild(button('取消', 'btn subtle', null, closeModal));
    var ok = control(button('确认移除', 'btn danger', 'trash', async function () {
      if (!requireRemote()) return; m.busy = true; ok.disabled = true;
      try { await api('/api/apps/' + encodeURIComponent(app.id), 'DELETE'); m.busy = false; closeModal(); await refreshConfig(); state.scan = null; toast('已移除快捷入口，电脑软件未卸载。'); }
      catch (e) { m.busy = false; toast(e.message, true); if (state.modal === m) ok.disabled = false; }
    })); m.footer.appendChild(ok); syncControls();
  }
  function openScan() {
    if (!state.connected || state.edit) { toast('连接恢复并退出编辑后可以添加应用。'); return; }
    var m = openModal('添加应用', true, 'DISCOVER YOUR APPS'); state.scanSelected.clear();
    m.content.appendChild(el('p', 'scan-description', '扫描仅发现软件。选中并添加到面板后，才能通过快捷卡片启动。'));
    var searchBox = el('label', 'search-field scan-search'); searchBox.appendChild(svgIcon('search')); var search = el('input'); search.placeholder = '搜索电脑上的应用…'; search.setAttribute('aria-label', '搜索扫描结果'); searchBox.appendChild(search); m.content.appendChild(searchBox);
    var filters = el('div', 'chip-list'), meta = el('p', 'scan-meta'), warnings = el('div', 'scan-warnings'), list = el('div', 'scan-list'); warnings.hidden = true;
    m.content.appendChild(filters); m.content.appendChild(meta); m.content.appendChild(warnings); m.content.appendChild(list);
    var targets = el('div', 'scan-targets'), pageLabel = el('label', '', '添加到页面'), target = el('select');
    state.layout.pages.forEach(function (p) { var opt = el('option', '', p.name); opt.value = p.id; target.appendChild(opt); });
    var appPage = state.layout.pages.filter(isAppPage)[0]; target.value = appPage ? appPage.id : state.pageId; pageLabel.appendChild(target); targets.appendChild(pageLabel);
    var groupLabel = el('label', '', '应用分组'), group = el('input'); group.value = '常用'; group.maxLength = 48; group.setAttribute('aria-label', '应用分组'); groupLabel.appendChild(group); targets.appendChild(groupLabel); m.content.appendChild(targets);
    var selection = el('span', 'scan-selection', '已选 0 项'), refresh = button('重新扫描', 'btn subtle', 'refresh', function () { load(true); });
    var add = button('添加到面板', 'btn primary', 'plus', submit); add.disabled = true; m.footer.classList.add('scan-footer'); m.footer.appendChild(selection); m.footer.appendChild(add);
    var manual = button('手动添加', 'btn subtle scan-manual', 'plus', function () { openManualAdd(); }), headerTools = el('div', 'modal-header-tools');
    headerTools.appendChild(manual); headerTools.appendChild(refresh); m.box.querySelector('.modal-header').insertBefore(headerTools, m.box.querySelector('.modal-header').lastChild);
    var source = '', loading = false, failure = '', disposed = false;
    m.cleanup.push(function () { disposed = true; });
    m.sync = function () { selectionCount(); refresh.disabled = loading || m.busy || !state.connected; manual.disabled = m.busy || !state.connected; target.disabled = !state.connected || m.busy; group.disabled = !state.connected || m.busy; };
    search.addEventListener('input', renderList);
    function renderFilters() {
      clear(filters); var counts = state.scan ? state.scan.counts || {} : {};
      [['', '全部']].concat(Object.keys(SOURCES).map(function (key) { return [key, SOURCES[key]]; })).forEach(function (entry) {
        var count = entry[0] ? (counts[entry[0]] !== undefined ? counts[entry[0]] : (state.scan ? state.scan.items.filter(function (i) { return i.source === entry[0]; }).length : 0)) : (state.scan ? state.scan.items.length : 0);
        filters.appendChild(button(entry[1] + ' ' + count, 'chip' + (source === entry[0] ? ' active' : ''), null, function () { source = entry[0]; renderFilters(); renderList(); }));
      });
    }
    function selectionCount() { selection.textContent = '已选 ' + state.scanSelected.size + ' 项'; add.disabled = loading || !state.connected || !state.scanSelected.size || m.busy; }
    function renderList() {
      if (disposed) return; clear(list); selectionCount();
      if (loading && !state.scan) { var loadText = el('div', 'scan-loading'); loadText.appendChild(el('span', 'spinner')); loadText.appendChild(document.createTextNode('正在扫描本机软件…')); list.appendChild(loadText); for (var k = 0; k < 5; k += 1) list.appendChild(el('div', 'skeleton-row')); return; }
      if (failure) { var error = el('div', 'scan-error'); error.appendChild(el('p', '', '扫描出错：' + failure)); error.appendChild(button('点此重试', 'btn primary', 'refresh', function () { load(true); })); list.appendChild(error); if (!state.scan) return; }
      var scan = state.scan; if (!scan) return;
      var query = search.value.trim().toLowerCase();
      var items = scan.items.filter(function (i) { return (!source || source === i.source) && (!query || String(i.name || '').toLowerCase().indexOf(query) >= 0); });
      if (!items.length) { var empty = el('div', 'scan-error'); empty.appendChild(el('p', 'muted', scan.items.length ? '没有匹配的应用，试试其他名称或来源。' : '没有找到可添加的软件，请重新扫描或在电脑端检查扫描源。')); list.appendChild(empty); return; }
      items.forEach(function (item) {
        var row = el('label', 'scan-item' + (item.added ? ' added' : '') + (state.scanSelected.has(item.key) ? ' selected' : '')), checkbox = el('input'); checkbox.type = 'checkbox'; checkbox.checked = !!item.added || state.scanSelected.has(item.key); checkbox.disabled = !!item.added || loading || m.busy; checkbox.setAttribute('aria-label', (item.added ? '已添加 ' : '选择 ') + item.name); row.appendChild(checkbox); row.appendChild(appIcon(item.name, item.icon));
        var name = el('span', 'scan-name'); name.appendChild(el('strong', '', item.name || '未命名应用')); name.appendChild(el('small', '', (SOURCES[item.source] || item.source || '其他来源') + (item.suggested_type ? ' · ' + item.suggested_type : ''))); row.appendChild(name);
        if (item.added) row.appendChild(el('span', 'scan-added', '✓ 已添加'));
        checkbox.addEventListener('change', function () { if (item.added) return; if (checkbox.checked) state.scanSelected.add(item.key); else state.scanSelected.delete(item.key); row.classList.toggle('selected', checkbox.checked); selectionCount(); }); list.appendChild(row);
      });
    }
    function renderMeta() {
      if (disposed) return;
      var scan = state.scan;
      meta.textContent = loading ? '正在扫描… 结果就绪后自动更新' : (scan ? (scan.cached ? '已读取扫描缓存' : '本次扫描完成') + ' · ' + scan.items.length + ' 项 · ' + new Date(scan.scanned_at).toLocaleString('zh-CN') : '准备扫描');
      warnings.hidden = !scan || !Array.isArray(scan.warnings) || !scan.warnings.length;
      if (!warnings.hidden) warnings.textContent = scan.warnings.map(function (w) { return typeof w === 'string' ? w : (w.message || '部分扫描来源不可用'); }).join('\n');
      refresh.disabled = loading || m.busy || !state.connected; renderFilters(); renderList();
    }
    async function load(force) {
      if (loading || !state.connected) return; loading = true; failure = ''; renderMeta();
      var version = ++state.scanVersion;
      try {
        var result = await api('/api/scan?refresh=' + (force ? 'true' : 'false'), 'GET', undefined, { timeout: 60000 });
        if (version !== state.scanVersion) return;
        if (!Array.isArray(result.items)) throw new Error('服务返回的扫描列表无效');
        state.scan = result;
        state.scanSelected.forEach(function (key) { if (!result.items.some(function (i) { return i.key === key && !i.added; })) state.scanSelected.delete(key); });
      } catch (e) { failure = e.message; }
      finally { loading = false; if (!disposed) renderMeta(); }
    }
    async function submit() {
      if (!state.connected || !state.scanSelected.size || loading || m.busy) return;
      if (!group.value.trim()) { toast('请填写应用分组。', true); group.focus(); return; }
      var keys = Array.from(state.scanSelected), pageId = target.value;
      m.busy = true; add.disabled = true; refresh.disabled = true; renderList();
      try {
        var result = await api('/api/apps/batch', 'POST', { keys: keys, page_id: pageId, group: group.value.trim() });
        if (!Array.isArray(result.results)) throw new Error('服务返回的添加结果无效');
        var added = 0; result.results.forEach(function (r) { if (r.added) { added += 1; state.highlights.add(r.app_id); } if (state.scan) state.scan.items.forEach(function (i) { if (i.key === r.key) i.added = true; }); });
        state.pageId = pageId; m.busy = false; closeModal(); await refreshConfig();
        toast('已添加 ' + added + ' 个应用' + (result.results.length > added ? '，其余已在面板中。' : '。'));
        setTimeout(function () { state.highlights.clear(); Array.prototype.forEach.call(document.querySelectorAll('.highlight'), function (n) { n.classList.remove('highlight'); }); }, 1200);
      } catch (e) {
        m.busy = false; toast(e.message, true);
        if (e.status === 409) { state.scanSelected.clear(); await load(false); }
        if (!disposed) renderMeta();
      }
    }
    renderMeta(); load(false);
  }

  function startEdit() {
    if (!state.layout || !state.connected || state.edit) return;
    state.edit = true; state.configDirty = false; state.draft = JSON.parse(JSON.stringify(state.layout.pages)); renderPage();
  }
  async function cancelEdit() {
    var dirty = state.configDirty; state.edit = false; state.draft = null; state.configDirty = false; renderPage();
    if (dirty) try { await refreshConfig(); } catch (e) { toast(e.message, true); }
  }
  function editControls(index, item) {
    var tools = el('div', 'card-edit-controls');
    var left = iconButton('arrow-left', '向前移动卡片', function () { move(-1); }), right = iconButton('arrow-right', '向后移动卡片', function () { move(1); }); left.disabled = index === 0; right.disabled = index === activePage().items.length - 1; tools.appendChild(left); tools.appendChild(right);
    var width = el('select'); width.setAttribute('aria-label', '卡片跨列宽度');
    for (var i = 1; i <= clamp(parseInt((state.layout.ui || {}).columns, 10) || 4, 1, 8); i += 1) { var option = el('option', '', i + ' 列宽'); option.value = i; width.appendChild(option); }
    width.value = item.span || 1; width.addEventListener('change', function () { item.span = Number(width.value); renderPage(); }); tools.appendChild(width);
    var remove = iconButton('trash', '从当前页面移除卡片', function () { activePage().items.splice(index, 1); renderPage(); }); remove.classList.add('remove-card'); tools.appendChild(remove);
    function move(delta) { var items = activePage().items, target = index + delta; if (target < 0 || target >= items.length) return; var current = items[index]; items[index] = items[target]; items[target] = current; renderPage(); }
    return tools;
  }
  async function savePages(pages) {
    if (!state.connected || state.saving) { toast('连接未就绪或正在保存。'); return false; }
    state.saving = true; syncControls(); $('edit-save').disabled = true;
    try { await api('/api/layout', 'PUT', { pages: pages }); state.edit = false; state.draft = null; state.configDirty = false; await refreshConfig(); toast('布局已保存到电脑。'); return true; }
    catch (e) { toast(e.message, true); return false; }
    finally { state.saving = false; $('edit-save').disabled = false; syncControls(); }
  }
  async function saveEdit() {
    if (state.configDirty) { toast('电脑端配置已变化，请取消编辑再重新调整。', true); return; }
    await savePages(state.draft);
  }
  function openPageForm() {
    if (!state.connected || state.edit) return;
    var m = openModal('新建页面', false, 'MAKE IT YOURS'), form = el('div', 'page-form'), label = el('label', '', '页面名称'), name = el('input'); name.maxLength = 32; name.placeholder = '例如：专注、影音、游戏'; label.appendChild(name); form.appendChild(label); m.content.appendChild(form);
    m.content.appendChild(el('p', 'modal-message', '页面创建后，可以在编辑模式中添加状态卡片，或从扫描面板添加应用。'));
    m.footer.appendChild(button('取消', 'btn subtle', null, closeModal)); var ok = button('创建页面', 'btn primary', 'plus', async function () {
      if (!name.value.trim()) { name.focus(); return; }
      var pages = JSON.parse(JSON.stringify(state.layout.pages)), id = 'page_' + Date.now().toString(36); pages.push({ id: id, name: name.value.trim(), items: [] });
      m.busy = true; ok.disabled = true;
      if (await savePages(pages)) { state.pageId = id; m.busy = false; closeModal(); renderPage(); }
      else { m.busy = false; ok.disabled = false; }
    }); m.footer.appendChild(ok);
    m.sync = function () { ok.disabled = !state.connected || m.busy; };
  }
  function openCardPicker() {
    if (!state.edit) return;
    var m = openModal('添加工作台卡片', false, 'BUILD YOUR PANEL'), form = el('div', 'card-form'), label = el('label', '', '卡片类型'), type = el('select');
    var choices = Object.keys(METRICS).map(function (key) { return ['stat:' + key, METRICS[key]]; }).concat([['volume', '主音量控制'], ['media', '媒体播放'], ['power', '电源与会话']]);
    choices.forEach(function (entry) { var o = el('option', '', entry[1]); o.value = entry[0]; type.appendChild(o); }); label.appendChild(type); form.appendChild(label); m.content.appendChild(form);
    m.footer.appendChild(button('取消', 'btn subtle', null, closeModal)); m.footer.appendChild(button('添加卡片', 'btn primary', 'plus', function () {
      var item; if (type.value.indexOf('stat:') === 0) item = { type: 'stat', metric: type.value.slice(5), span: type.value === 'stat:cpu' || type.value === 'stat:disk' ? 2 : 1 };
      else item = { type: type.value, span: 2 };
      if (item.type === 'power') item.actions = Object.keys(POWER);
      activePage().items.push(item); closeModal(); renderPage(); toast('卡片已加入草稿，保存布局后生效。');
    }));
  }
  function openSettings() {
    var m = openModal('工作台设置', false, 'DESKTOUCH SETTINGS'), ui = (state.layout && state.layout.ui) || { theme: 'light', columns: 4, rows: 3, keep_awake: false, accent: '#3465d9' };
    var grid = el('div', 'settings-grid');
    function select(labelText, values, selected) { var label = el('label', '', labelText), field = el('select'); values.forEach(function (entry) { var o = el('option', '', entry[1]); o.value = entry[0]; field.appendChild(o); }); field.value = selected; label.appendChild(field); grid.appendChild(label); return field; }
    var theme = select('外观主题', [['light', '浅色 · 日间工作台'], ['dark', '深色 · 夜间工作台']], ui.theme || 'light');
    var accentLabel = el('label', '', '强调色'), accent = el('input'); accent.type = 'color'; accent.value = /^#[0-9a-fA-F]{6}$/.test(ui.accent || '') ? ui.accent : '#3465d9'; accentLabel.appendChild(accent); grid.appendChild(accentLabel);
    var cols = select('横屏列数', Array.from({ length: 8 }, function (_, i) { return [i + 1, i + 1 + ' 列']; }), ui.columns || 4);
    var rows = select('目标行数', Array.from({ length: 10 }, function (_, i) { return [i + 1, i + 1 + ' 行']; }), ui.rows || 3);
    var checkLabel = el('label', 'check-line settings-wide'), awake = el('input'); awake.type = 'checkbox'; awake.checked = !!ui.keep_awake; checkLabel.appendChild(awake); checkLabel.appendChild(document.createTextNode('屏幕常亮（浏览器支持时）')); grid.appendChild(checkLabel); m.content.appendChild(grid);
    var note = el('p', 'wake-note', wakeInfo()); m.content.appendChild(note);
    awake.addEventListener('change', function () { note.textContent = awake.checked ? wakeInfo() : '保存后关闭浏览器屏幕常亮。'; });
    m.content.appendChild(el('p', 'modal-message', '窄屏自动调整为 2 列。行数决定卡片基础高度，内容超出时仍可滚动。\n可在浏览器菜单将 DeskTouch 添加到主屏幕；离线只能打开静态页面，不能控制电脑。'));
    var links = el('div', 'settings-links'); links.appendChild(button('进入全屏', 'btn subtle', 'fullscreen', toggleFullscreen));
    var reload = button('重新加载配置', 'btn subtle', 'refresh', async function () {
      if (!state.connected || state.edit) { toast('请先连接并退出编辑模式。'); return; } reload.disabled = true; m.busy = true;
      try { await api('/api/layout/reload', 'POST'); await refreshConfig(); m.busy = false; closeModal(); toast('电脑配置已重新加载。'); }
      catch (e) { m.busy = false; reload.disabled = false; toast(e.message, true); }
    }); reload.disabled = !state.connected; links.appendChild(reload);
    links.appendChild(button('解除本机配对', 'btn subtle', 'lock', function () { confirmLogout(); })); m.content.appendChild(links);
    m.footer.appendChild(button('取消', 'btn subtle', null, closeModal)); var save = button('保存设置', 'btn primary', 'check', async function () {
      if (!state.connected || state.edit) { toast('请连接电脑并退出布局编辑后保存设置。'); return; }
      save.disabled = true; m.busy = true;
      var newUI = { theme: theme.value, columns: Number(cols.value), rows: Number(rows.value), keep_awake: awake.checked, accent: accent.value };
      try { await api('/api/layout', 'PUT', { ui: newUI }); await refreshConfig(); if (newUI.keep_awake) await requestWake(true); m.busy = false; closeModal(); toast('设置已保存到电脑。'); }
      catch (e) { m.busy = false; save.disabled = false; toast(e.message, true); }
    }); save.disabled = !state.connected || state.edit; m.footer.appendChild(save);
    m.sync = function () { save.disabled = !state.connected || state.edit || m.busy; reload.disabled = !state.connected || state.edit || m.busy; };
  }
  function confirmLogout() {
    var m = openModal('解除这台平板的配对', false, 'LOCAL DEVICE'); m.content.appendChild(el('p', 'modal-message', '将删除本机浏览器保存的令牌并断开连接。再次访问需要重新输入配对码。其他设备与电脑配置不受影响。'));
    m.footer.appendChild(button('取消', 'btn subtle', null, closeModal)); m.footer.appendChild(button('解除配对', 'btn danger', null, function () { showPair('已解除本机配对。'); health(); }));
  }
  async function toggleTheme() {
    if (!state.connected || !state.layout || state.edit) { toast('请连接电脑并退出编辑模式后切换主题。'); return; }
    $('theme-toggle').disabled = true;
    try { await api('/api/layout', 'PUT', { ui: { theme: document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark' } }); await refreshConfig(); }
    catch (e) { toast(e.message, true); } finally { $('theme-toggle').disabled = false; }
  }
  function wakeInfo() {
    if (!window.isSecureContext) return '当前 HTTP 局域网页面不是安全上下文，浏览器常亮不可用。请在平板系统设置中关闭自动锁屏或设置屏幕常亮。';
    if (!navigator.wakeLock || !navigator.wakeLock.request) return '此浏览器不支持 Wake Lock，请在平板系统设置中延长自动锁屏时间。';
    return state.wake ? '浏览器屏幕常亮已启用；切到后台时会自动释放，回到页面后重新申请。' : (state.wakeMessage || '支持屏幕常亮。保存设置后将向浏览器申请，系统节电策略可能拒绝。');
  }
  async function requestWake(notify) {
    if (!window.isSecureContext || !navigator.wakeLock || !navigator.wakeLock.request) { if (notify) toast(wakeInfo()); return false; }
    if (state.wake || document.visibilityState !== 'visible') return !!state.wake;
    try {
      var lock = await navigator.wakeLock.request('screen');
      if (!state.token || !state.layout || !state.layout.ui.keep_awake) { lock.release(); return false; }
      state.wake = lock; state.wakeMessage = ''; lock.addEventListener('release', function () { if (state.wake === lock) state.wake = null; });
      if (notify) toast('浏览器屏幕常亮已启用。'); return true;
    } catch (e) { state.wakeMessage = '浏览器未允许屏幕常亮，请使用平板系统常亮设置。'; if (notify) toast(state.wakeMessage); return false; }
  }
  function releaseWake() { if (state.wake) { var lock = state.wake; state.wake = null; lock.release().catch(function () {}); } }
  async function toggleFullscreen() {
    var root = document.documentElement;
    try {
      if (document.fullscreenElement || document.webkitFullscreenElement) { var exit = document.exitFullscreen || document.webkitExitFullscreen; if (exit) await exit.call(document); }
      else { var enter = root.requestFullscreen || root.webkitRequestFullscreen; if (!enter) { toast('此浏览器不支持页面全屏；可尝试添加到主屏幕。'); return; } await enter.call(root); }
    } catch (e) { toast('未进入全屏，请直接触碰全屏按钮，或添加到主屏幕。'); }
  }

  function openPower(action) {
    if (!POWER[action] || !requireRemote()) return;
    var m = openModal('确认' + POWER[action], false, 'POWER & SESSION');
    m.content.appendChild(el('div', 'power-warning', '请先保存电脑上所有未保存的文件。\n即将执行「' + POWER[action] + '」，可能中断当前工作或连接。'));
    m.content.appendChild(el('p', 'power-detail', '按住下方按钮至少 1.5 秒。提前松手、移开、切到后台或取消弹窗都会中止；普通点击不会执行。键盘可按住空格或 Enter。'));
    var hold = control(button('', 'hold-button', null, null)), progress = el('span', 'hold-progress'), label = el('span', '', '准备安全确认…'); hold.appendChild(progress); hold.appendChild(label); hold.setAttribute('aria-label', '长按至少 1.5 秒确认' + POWER[action]); hold.setAttribute('aria-describedby', 'hold-hint'); hold.disabled = true; m.content.appendChild(hold);
    var hint = el('div', 'hold-hint', '正在向电脑申请一次性确认凭证…'); hint.id = 'hold-hint'; m.content.appendChild(hint); m.footer.appendChild(button('取消操作', 'btn subtle', null, closeModal));
    var nonce = '', expires = 0, minHold = 1500, held = false, timer = null, frame = null, startAt = 0, sending = false, touchId = null;
    var epoch = state.epoch;
    function stopHold(message) {
      if (sending) return; held = false; clearTimeout(timer); cancelAnimationFrame(frame); timer = null; frame = null; progress.style.width = '0%';
      if (nonce) label.textContent = '长按确认 · ' + POWER[action];
      if (message) hint.textContent = message;
    }
    m.cancelHold = function () { stopHold('连接已断开，操作已取消。请恢复连接后重新确认。'); nonce = ''; hold.setAttribute('data-busy', 'true'); };
    function animate() { if (!held) return; progress.style.width = Math.min(100, (performance.now() - startAt) / minHold * 100) + '%'; frame = requestAnimationFrame(animate); }
    async function prepare() {
      hold.setAttribute('data-busy', 'true'); syncControls();
      try {
        var r = await api('/api/power/confirm', 'POST', { action: action });
        if (state.modal !== m || epoch !== state.epoch) return;
        if (typeof r.nonce !== 'string' || !r.nonce || num(r.expires_in) <= 0) throw new Error('电脑返回的确认凭证无效');
        nonce = r.nonce; expires = Date.now() + num(r.expires_in) * 1000; minHold = Math.max(1500, num(r.min_hold_ms));
        hold.removeAttribute('data-busy'); syncControls(); label.textContent = '长按确认 · ' + POWER[action]; hint.textContent = '安全确认已就绪 · 凭证 ' + r.expires_in + ' 秒内有效';
      } catch (e) { if (state.modal !== m) return; label.textContent = '无法准备确认'; hint.textContent = e.message; m.footer.appendChild(button('重试确认', 'btn subtle', 'refresh', prepare)); }
    }
    function startHold(e) {
      if (held || sending || hold.disabled || !nonce || !requireRemote()) return;
      if (Date.now() + minHold >= expires) { stopHold('确认凭证已过期，正在重新申请；请再次长按。'); nonce = ''; prepare(); return; }
      if (e) e.preventDefault(); held = true; startAt = performance.now(); hint.textContent = '保持按住，松手即取消…'; label.textContent = '正在确认 · ' + POWER[action];
      animate(); timer = setTimeout(execute, minHold + 20);
    }
    async function execute() {
      if (!held || sending || state.modal !== m || epoch !== state.epoch || !controlsAvailable() || !nonce || Date.now() >= expires || performance.now() - startAt < minHold) { stopHold('操作未完成，请重新长按。'); return; }
      sending = true; held = false; cancelAnimationFrame(frame); progress.style.width = '100%'; hold.setAttribute('data-busy', 'true'); syncControls(); m.busy = true; label.textContent = '正在发送「' + POWER[action] + '」…';
      var currentNonce = nonce; nonce = '';
      state.expectedPower = POWER[action];
      hint.textContent = '指令发送后，睡眠、关机或重启可能导致预期的连接中断。';
      try {
        await api('/api/power', 'POST', { action: action, nonce: currentNonce });
        toast('「' + POWER[action] + '」指令已发送。' + (/sleep|shutdown|restart/.test(action) ? '连接可能暂时中断。' : ''));
        m.busy = false; closeModal();
        if (/sleep|shutdown|restart/.test(action)) { setConnected(false); if (state.socket) state.socket.close(4002, 'expected power disconnect'); }
      } catch (e) {
        m.busy = false; sending = false;
        if (!state.connected) { hint.textContent = '连接已断开，执行结果无法确认。请在电脑恢复后检查，不会自动重发。'; toast('电源请求结果无法确认，不会自动重复执行。', true); }
        else { hint.textContent = e.message + ' 请重新打开确认弹窗。'; toast(e.message, true); state.expectedPower = ''; }
        label.textContent = '请关闭后重新确认';
      }
    }
    if (window.PointerEvent) {
      hold.addEventListener('pointerdown', function (e) { if (e.button !== 0 || !e.isPrimary) return; startHold(e); });
      ['pointerup', 'pointercancel', 'pointerleave'].forEach(function (type) { hold.addEventListener(type, function () { if (held) stopHold('已取消；重新长按即可确认。'); }); });
      var pointerEnd = function () { if (held) stopHold('已取消；重新长按即可确认。'); };
      window.addEventListener('pointerup', pointerEnd); window.addEventListener('pointercancel', pointerEnd); m.cleanup.push(function () { window.removeEventListener('pointerup', pointerEnd); window.removeEventListener('pointercancel', pointerEnd); });
    } else {
      hold.addEventListener('mousedown', function (e) { if (e.button === 0) startHold(e); });
      hold.addEventListener('mouseleave', function () { if (held) stopHold('已取消。'); });
      var mouseEnd = function () { if (held) stopHold('已取消。'); }; window.addEventListener('mouseup', mouseEnd); m.cleanup.push(function () { window.removeEventListener('mouseup', mouseEnd); });
      hold.addEventListener('touchstart', function (e) { if (e.touches.length !== 1) { stopHold('多点触控已取消操作。'); return; } touchId = e.touches[0].identifier; startHold(e); }, { passive: false });
      hold.addEventListener('touchmove', function (e) { var touch = Array.prototype.filter.call(e.touches, function (t) { return t.identifier === touchId; })[0], r = hold.getBoundingClientRect(); if (!touch || touch.clientX < r.left || touch.clientX > r.right || touch.clientY < r.top || touch.clientY > r.bottom) stopHold('已移开，操作取消。'); e.preventDefault(); }, { passive: false });
      var touchEnd = function () { if (held) stopHold('已取消。'); }; window.addEventListener('touchend', touchEnd); window.addEventListener('touchcancel', touchEnd); m.cleanup.push(function () { window.removeEventListener('touchend', touchEnd); window.removeEventListener('touchcancel', touchEnd); });
    }
    hold.addEventListener('keydown', function (e) { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); if (!e.repeat) startHold(e); } });
    var keyEnd = function (e) { if ((e.key === ' ' || e.key === 'Enter') && held) { e.preventDefault(); stopHold('已松开按键，操作取消。'); } }; window.addEventListener('keyup', keyEnd);
    hold.addEventListener('blur', function () { if (held) stopHold('焦点已移开，操作取消。'); });
    hold.addEventListener('click', function (e) { e.preventDefault(); });
    hold.addEventListener('contextmenu', function (e) { e.preventDefault(); if (held) stopHold('操作取消。'); });
    var blur = function () { if (held) stopHold('窗口失去焦点，操作取消。'); }, visibility = function () { if (document.visibilityState !== 'visible') blur(); };
    window.addEventListener('blur', blur); document.addEventListener('visibilitychange', visibility);
    m.cleanup.push(function () { stopHold(); nonce = ''; window.removeEventListener('keyup', keyEnd); window.removeEventListener('blur', blur); document.removeEventListener('visibilitychange', visibility); });
    prepare();
  }

  function updateClock() {
    var now = new Date(); $('clock-time').textContent = ('0' + now.getHours()).slice(-2) + ':' + ('0' + now.getMinutes()).slice(-2);
    $('clock-date').textContent = (now.getMonth() + 1) + '月' + now.getDate() + '日 · ' + ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][now.getDay()];
    var age = state.snapshotAt ? Math.floor((Date.now() - state.snapshotAt) / 1000) : 0;
    $('snapshot-age').textContent = state.snapshotAt ? (state.connected ? (age <= 1 ? '实时同步 · 刚刚更新' : age + ' 秒前更新') : '离线 · 最后状态 ' + age + ' 秒前') : '等待电脑状态';
    if (state.connected && age > 15) { setConnected(false, '状态同步已超时，控制已禁用，正在重新连接。'); if (state.socket) state.socket.close(4000, 'stale'); }
    if (state.offlineVisible) renderOffline();
  }
  function navigateApps() {
    if (!state.layout) return;
    var page = state.layout.pages.filter(isAppPage)[0]; if (page) switchPage(page.id); else openPageForm();
  }
  function init() {
    hydrateIcons(document); applyTheme('light'); state.token = readStorage('dt_token');
    $('pair-form').addEventListener('submit', pair); $('pair-code').addEventListener('input', function () { $('pair-code').value = $('pair-code').value.replace(/[^0-9]/g, '').slice(0, 6); });
    $('health-retry').addEventListener('click', health); $('connection-retry').addEventListener('click', reconnectNow);
    $('offline-retry').addEventListener('click', reconnectNow);
    $('scan-open').addEventListener('click', openScan); $('settings-open').addEventListener('click', openSettings);
    $('theme-toggle').addEventListener('click', toggleTheme); $('fullscreen-toggle').addEventListener('click', toggleFullscreen);
    $('nav-apps').addEventListener('click', navigateApps); $('nav-overview').addEventListener('click', function () { if (state.layout) { var page = state.layout.pages.filter(function (p) { return !isAppPage(p); })[0]; if (page) switchPage(page.id); } });
    $('page-add').addEventListener('click', openPageForm); $('edit-toggle').addEventListener('click', function () { if (!state.edit) startEdit(); });
    $('card-add').addEventListener('click', openCardPicker); $('edit-save').addEventListener('click', saveEdit); $('edit-cancel').addEventListener('click', cancelEdit);
    $('app-search').addEventListener('input', function () { state.appSearch = $('app-search').value; renderPage(); });
    window.addEventListener('resize', function () { if (state.layout) { applyUI(state.layout.ui || {}); updateCards(); } });
    window.addEventListener('offline', function () { stopConnection(); setConnected(false, '此平板已离线，请检查 Wi-Fi。控制已禁用。'); scheduleReconnect(false); });
    window.addEventListener('online', reconnectNow);
    document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') { updateClock(); if (state.token && !state.connected) reconnectNow(); if (state.layout && state.layout.ui.keep_awake) requestWake(false); } else { cancelVolume(); releaseWake(); } });
    window.addEventListener('pagehide', function () { stopConnection(); releaseIcons(); releaseWake(); });
    window.addEventListener('pageshow', function (e) { if (e.persisted && state.token) boot(); });
    updateClock(); setInterval(updateClock, 1000); health(); if (state.token) boot();
    if (window.isSecureContext && 'serviceWorker' in navigator && /^https?:$/.test(location.protocol)) navigator.serviceWorker.register('./sw.js').catch(function () { toast('离线资源未注册，不影响在线使用。'); });
  }
  init();
}());

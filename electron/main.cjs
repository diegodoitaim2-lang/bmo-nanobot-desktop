const { app, BrowserWindow, dialog, shell, Tray, Menu, Notification, screen, globalShortcut, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let mainWindow = null;
let backendProcess = null;
let tray = null;
let isQuitting = false;
const notifiedReminders = new Set();
const reminderWindows = new Map();
let registeredHotkey = '';

const isDev = !app.isPackaged;
const useDevServer = isDev && process.env.BMO_ELECTRON_LOAD_DIST !== '1' && process.env.BMO_USE_DEV_SERVER === '1';
const gotSingleInstanceLock = app.requestSingleInstanceLock();

function mainLog(message) {
  try {
    const dir = app.getPath('userData');
    fs.mkdirSync(dir, { recursive: true });
    fs.appendFileSync(path.join(dir, 'main.log'), `${new Date().toISOString()} ${message}\n`, 'utf8');
  } catch {
    // Logging must never block startup.
  }
}

if (!gotSingleInstanceLock) {
  mainLog('second instance detected; quitting duplicate');
  app.exit(0);
}

function projectRoot() {
  return path.join(__dirname, '..');
}

function resourcesRoot() {
  return isDev ? projectRoot() : process.resourcesPath;
}

function resolveResource(...segments) {
  return path.join(resourcesRoot(), ...segments);
}

function localBmoConfigPath() {
  return path.join(app.getPath('home'), '.bmo', 'config', 'app_config.json');
}

function readSavedHotkey() {
  try {
    const data = JSON.parse(fs.readFileSync(localBmoConfigPath(), 'utf8'));
    return data.hotkey || 'Ctrl+Alt+B';
  } catch (error) {
    mainLog(`read hotkey fallback: ${error.message}`);
    return 'Ctrl+Alt+B';
  }
}

function registerOpenHotkey() {
  const next = readSavedHotkey();
  if (next === registeredHotkey) return;
  if (registeredHotkey) globalShortcut.unregister(registeredHotkey);
  registeredHotkey = '';
  try {
    if (globalShortcut.register(next, () => showMainWindow(true))) {
      registeredHotkey = next;
      mainLog(`registered hotkey ${next}`);
    }
  } catch (error) {
    mainLog(`hotkey register failed ${next}: ${error.message}`);
  }
}

function backendExecutable() {
  if (isDev) return null;

  const packagedBackendDir = resolveResource('bmo_backend', 'bmo_backend.exe');
  if (fs.existsSync(packagedBackendDir)) return packagedBackendDir;

  const packagedBackend = resolveResource('bmo_backend.exe');
  if (fs.existsSync(packagedBackend)) return packagedBackend;

  const localBackendDir = path.join(projectRoot(), 'backend-dist', 'bmo_backend', 'bmo_backend.exe');
  if (fs.existsSync(localBackendDir)) return localBackendDir;

  const localBackend = path.join(projectRoot(), 'backend-dist', 'bmo_backend.exe');
  if (fs.existsSync(localBackend)) return localBackend;

  return null;
}

function startBackend() {
  const exe = backendExecutable();
  if (exe) {
    mainLog(`starting packaged backend: ${exe}`);
    // Capturar stdout com buffer para chunks parciais
    let stdoutBuf = '';
    backendProcess = spawn(exe, {
      cwd: path.dirname(exe),
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe'],
      detached: false,
    });
    backendProcess.stdout.on('data', (data) => {
      stdoutBuf += data.toString('utf8');
      const match = stdoutBuf.match(/BMO_TOKEN=([a-f0-9]{64})/);
      if (match) {
        bmoApiToken = match[1];
        mainLog('BMO API token captured from backend');
      }
    });
    return;
  }

  const script = path.join(projectRoot(), 'backend', 'bmo_backend.py');
  if (!fs.existsSync(script)) {
    dialog.showErrorBox('BMO', `Backend nao encontrado:\n${script}`);
    return;
  }

  const pythonCommand = process.platform === 'win32' ? 'pythonw' : 'python';
  mainLog(`starting dev backend: ${pythonCommand} ${script}`);
  const spawnOptions = {
    cwd: projectRoot(),
    windowsHide: true,
    stdio: ['ignore', 'pipe', 'pipe'],
    detached: false,
  };
  backendProcess = spawn(pythonCommand, [script], spawnOptions);
  let stdoutBuf = '';
  backendProcess.stdout.on('data', (data) => {
    stdoutBuf += data.toString('utf8');
    const match = stdoutBuf.match(/BMO_TOKEN=([a-f0-9]{64})/);
    if (match) {
      bmoApiToken = match[1];
      mainLog('BMO API token captured from dev backend');
    }
  });
  backendProcess.once('error', (error) => {
    dialog.showErrorBox('BMO', `Nao consegui iniciar o backend invisivel com pythonw.\n${error.message}`);
  });
}

function stopBackend() {
  if (backendProcess && !backendProcess.killed) {
    try {
      backendProcess.kill();
    } catch {
      // Best effort shutdown.
    }
  }
  backendProcess = null;
}

function iconPath() {
  const candidates = [
    resolveResource('icon.ico'),
    path.join(projectRoot(), 'build-support', 'icon.ico'),
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || '';
}

function showMainWindow(forceTop = false) {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  ensureWindowVisible();
  mainWindow.show();
  if (mainWindow.isMinimized()) mainWindow.restore();
  if (forceTop) {
    mainWindow.setAlwaysOnTop(true, 'screen-saver');
    mainWindow.flashFrame(true);
    setTimeout(() => {
      if (!mainWindow || mainWindow.isDestroyed()) return;
      mainWindow.setAlwaysOnTop(false);
      mainWindow.flashFrame(false);
    }, 5000);
  }
  mainWindow.focus();
}

function ensureWindowVisible() {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  const bounds = mainWindow.getBounds();
  const displays = screen.getAllDisplays();
  const isVisibleOnDisplay = displays.some(({ workArea }) => {
    const right = bounds.x + bounds.width;
    const bottom = bounds.y + bounds.height;
    return right > workArea.x && bounds.x < workArea.x + workArea.width && bottom > workArea.y && bounds.y < workArea.y + workArea.height;
  });
  if (isVisibleOnDisplay) return;
  const { workArea } = screen.getPrimaryDisplay();
  const width = Math.min(Math.max(bounds.width || 1280, 980), workArea.width);
  const height = Math.min(Math.max(bounds.height || 820, 680), workArea.height);
  mainWindow.setBounds({
    width,
    height,
    x: Math.round(workArea.x + (workArea.width - width) / 2),
    y: Math.round(workArea.y + (workArea.height - height) / 2),
  });
}

async function backendFetch(pathname, options = {}, timeoutMs = 8000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(`http://127.0.0.1:8787${pathname}`, {
      ...options,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

async function backendPost(pathname, payload) {
  try {
    await backendFetch(pathname, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    }, 10000);
  } catch (error) {
    mainLog(`backend post failed ${pathname}: ${error.message}`);
  }
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function handleReminderPopupAction(action, item, popup) {
  if (action === 'complete') await backendPost('/api/reminders', { action: 'complete', id: item.id });
  if (action === 'snooze5') await backendPost('/api/reminders', { action: 'snooze', id: item.id, minutes: 5 });
  if (action === 'snooze10') await backendPost('/api/reminders', { action: 'snooze', id: item.id, minutes: 10 });
  reminderWindows.delete(item.id);
  if (popup && !popup.isDestroyed()) popup.close();
  showMainWindow(true);
}

function showReminderPopup(item) {
  if (!item.id || reminderWindows.has(item.id)) return;
  const { workArea } = screen.getPrimaryDisplay();
  const width = 420;
  const height = 230;
  const popup = new BrowserWindow({
    width,
    height,
    x: Math.round(workArea.x + workArea.width - width - 22),
    y: Math.round(workArea.y + workArea.height - height - 22),
    title: 'Lembrete do BMO',
    icon: iconPath() || undefined,
    resizable: false,
    minimizable: false,
    maximizable: false,
    alwaysOnTop: true,
    skipTaskbar: false,
    autoHideMenuBar: true,
    backgroundColor: '#031411',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  reminderWindows.set(item.id, popup);
  const body = escapeHtml(item.text || 'Voce tem um lembrete.');
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>
    body{margin:0;font-family:Segoe UI,Arial,sans-serif;background:linear-gradient(135deg,#031411,#063d35);color:#ecfff4}
    main{padding:22px;display:grid;gap:14px}
    h1{font-size:22px;margin:0;color:#50ff9a} p{font-size:18px;line-height:1.35;margin:0}
    .buttons{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}
    button{border:1px solid rgba(100,255,170,.28);background:rgba(0,40,30,.72);color:#ecfff4;border-radius:14px;padding:11px 13px;font-weight:700;cursor:pointer}
    button.primary{background:#39d98a;color:#03201a}
  </style></head><body><main>
    <h1>BMO lembrou!</h1>
    <p>${body}</p>
    <div class="buttons">
      <button class="primary" onclick="location.href='bmo-reminder://complete'">Concluir</button>
      <button onclick="location.href='bmo-reminder://snooze5'">Adiar 5 min</button>
      <button onclick="location.href='bmo-reminder://snooze10'">Adiar 10 min</button>
    </div>
  </main></body></html>`;
  popup.webContents.on('will-navigate', (event, url) => {
    event.preventDefault();
    const action = String(url).replace('bmo-reminder://', '');
    handleReminderPopupAction(action, item, popup);
  });
  popup.on('closed', () => reminderWindows.delete(item.id));
  popup.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);
  popup.show();
  popup.focus();
}

async function pollReminders() {
  try {
    if (mainWindow && !mainWindow.isDestroyed() && mainWindow.isVisible() && mainWindow.isFocused()) return;
    const response = await backendFetch('/api/reminders?due=1', {}, 8000);
    if (!response.ok) return;
    const data = await response.json();
    if (data.busy) return;
    for (const item of data.items || []) {
      if (!item.id || notifiedReminders.has(item.id)) continue;
      notifiedReminders.add(item.id);
      await backendPost('/api/reminders', { action: 'notify', id: item.id });
      await backendPost('/api/sound', { type: 'ack' });
      if (!item.backendFired) backendPost('/api/speak', { text: `Ei. Lembrete: ${item.text}` });
      showReminderPopup(item);

      const notification = new Notification({
        title: 'Lembrete do BMO',
        body: item.text || 'Voce tem um lembrete.',
        icon: iconPath(),
        silent: false,
        actions: [
          { type: 'button', text: 'Concluir' },
          { type: 'button', text: 'Adiar 5 min' },
          { type: 'button', text: 'Adiar 10 min' },
        ],
      });
      notification.on('click', showMainWindow);
      notification.on('action', (_event, index) => {
        if (index === 0) backendPost('/api/reminders', { action: 'complete', id: item.id });
        if (index === 1) backendPost('/api/reminders', { action: 'snooze', id: item.id, minutes: 5 });
        if (index === 2) backendPost('/api/reminders', { action: 'snooze', id: item.id, minutes: 10 });
        showMainWindow();
      });
      notification.show();
      showMainWindow(true);
    }
  } catch (error) {
    mainLog(`poll reminders skipped: ${error.message}`);
  }
}

function notifiedSubagentsPath() {
  return path.join(app.getPath('userData'), 'notified-subagents.json');
}

function loadNotifiedSubagentIds() {
  try {
    const raw = fs.readFileSync(notifiedSubagentsPath(), 'utf8');
    const data = JSON.parse(raw);
    return new Set(Array.isArray(data.ids) ? data.ids : []);
  } catch {
    return new Set();
  }
}

function persistNotifiedSubagentIds(ids) {
  try {
    fs.writeFileSync(notifiedSubagentsPath(), JSON.stringify({ ids: [...ids].slice(-500) }), 'utf8');
  } catch (error) {
    mainLog(`persist notified subagents failed: ${error.message}`);
  }
}

async function pollSubagents() {
  try {
    if (mainWindow && !mainWindow.isDestroyed() && mainWindow.isVisible() && mainWindow.isFocused()) return;
    const response = await backendFetch('/api/subagents', {}, 8000);
    if (!response.ok) return;
    const data = await response.json();
    if (data.busy) return;
    const locallyNotified = loadNotifiedSubagentIds();
    let changed = false;
    for (const item of data.items || []) {
      const finished = item.status === 'concluido' || item.status === 'erro';
      if (!finished || !item.id) continue;
      const key = `agent-${item.id}`;
      if (item.notified || locallyNotified.has(key)) {
        // Ja notificado (backend ou localmente), ignora
        if (!locallyNotified.has(key)) {
          locallyNotified.add(key);
          changed = true;
        }
        continue;
      }
      // Nunca foi notificado: dispara notificacao
      locallyNotified.add(key);
      changed = true;
      await backendPost('/api/subagents', { action: 'mark_notified', id: item.id });
      await backendPost('/api/sound', { type: 'ack' });
      const ok = item.status === 'concluido';
      const text = ok
        ? `Agente ${item.id} terminou. Resultado salvo em ${item.outputPath || item.outputFile || 'arquivo de resultado'}.`
        : `Agente ${item.id} encontrou um problema.`;
      backendPost('/api/speak', { text });
      new Notification({
        title: ok ? 'Subagente do BMO concluido' : 'Subagente do BMO com erro',
        body: text,
        icon: iconPath(),
        silent: true,
      }).show();
      showMainWindow(true);
    }
    if (changed) persistNotifiedSubagentIds(locallyNotified);
  } catch (error) {
    mainLog(`poll subagents skipped: ${error.message}`);
  }
}

function createTray() {
  if (tray) return;
  const icon = iconPath();
  if (!icon) {
    mainLog('tray skipped: icon not found');
    return;
  }
  mainLog(`creating tray with icon: ${icon}`);
  tray = new Tray(icon);
  tray.setToolTip('BMO');
  tray.setContextMenu(
    Menu.buildFromTemplate([
      { label: 'Abrir BMO', click: showMainWindow },
      { type: 'separator' },
      {
        label: 'Sair completamente',
        click: () => {
          isQuitting = true;
          app.quit();
        },
      },
    ]),
  );
  tray.on('click', showMainWindow);
}

function createWindow() {
  const icon = iconPath();
  mainLog(`creating window packaged=${app.isPackaged} icon=${icon || 'none'} projectRoot=${projectRoot()} resources=${resourcesRoot()}`);
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 980,
    minHeight: 680,
    title: 'BMO',
    icon: icon || undefined,
    backgroundColor: '#020b09',
    autoHideMenuBar: true,
    show: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      preload: path.join(__dirname, 'preload.cjs'),
      backgroundThrottling: false,
    },
  });

  const revealWindow = () => {
    if (!mainWindow || mainWindow.isDestroyed()) return;
    ensureWindowVisible();
    mainWindow.show();
    mainWindow.restore();
    mainWindow.focus();
  };

  revealWindow();

  mainWindow.once('ready-to-show', revealWindow);

  setTimeout(revealWindow, 2500);

  mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL) => {
    const logLine = `[WINDOW] did-fail-load ${errorCode} ${errorDescription} ${validatedURL}\n`;
    fs.appendFileSync(path.join(app.getPath('userData'), 'window.log'), logLine, 'utf8');
    revealWindow();
  });

  mainWindow.webContents.on('render-process-gone', (_event, details) => {
    const logLine = `[WINDOW] render-process-gone ${details.reason} exitCode=${details.exitCode}\n`;
    fs.appendFileSync(path.join(app.getPath('userData'), 'window.log'), logLine, 'utf8');
    revealWindow();
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('close', (event) => {
    if (isQuitting) return;
    event.preventDefault();
    mainWindow.hide();
    const flagPath = path.join(app.getPath('userData'), 'tray-info-shown.json');
    if (!fs.existsSync(flagPath)) {
      fs.writeFileSync(flagPath, JSON.stringify({ shownAt: Date.now() }), 'utf8');
      new Notification({
        title: 'BMO continua acordado',
        body: 'Quando voce fecha no X, eu fico na bandeja para lembrar voce das coisas. Use o menu da bandeja para sair completamente.',
        icon: iconPath(),
      }).show();
    }
  });

  if (useDevServer) {
    mainLog('loading dev server http://127.0.0.1:5173');
    mainWindow.loadURL('http://127.0.0.1:5173');
  } else {
    const indexFile = path.join(projectRoot(), 'dist', 'index.html');
    mainLog(`loading file ${indexFile}`);
    mainWindow.loadFile(indexFile).catch((error) => {
      mainLog(`loadFile failed: ${error.message}`);
      dialog.showErrorBox('BMO', `Nao consegui carregar a interface:\n${indexFile}\n\n${error.message}`);
      showMainWindow(true);
    });
  }
}

if (gotSingleInstanceLock) {
  ipcMain.handle('bmo:get-token', async () => bmoApiToken);

  ipcMain.handle('bmo:save-file', async (_event, options) => {
    try {
      const result = await dialog.showSaveDialog({
        title: 'Exportar conversa do BMO',
        defaultPath: options.defaultPath || 'BMO_conversa.txt',
        filters: options.filters || [{ name: 'Texto', extensions: ['txt'] }],
      });
      if (result.canceled || !result.filePath) return { ok: false };
      fs.writeFileSync(result.filePath, String(options.content || ''), 'utf8');
      return { ok: true, path: result.filePath };
    } catch (error) {
      return { ok: false, error: error.message };
    }
  });

  app.whenReady().then(() => {
    mainLog('app ready');
    createWindow();
    createTray();
    startBackend();
    registerOpenHotkey();
    setInterval(pollReminders, 15000);
    setInterval(pollSubagents, 30000);
    setInterval(registerOpenHotkey, 5000);

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });

  app.on('second-instance', () => {
    showMainWindow(true);
    if (Notification.isSupported()) {
      new Notification({
        title: 'BMO ja esta aberto',
        body: 'Eu ja estou rodando. Trouxe minha janela pra frente pra voce.',
        icon: iconPath(),
      }).show();
    }
  });
}

app.on('before-quit', stopBackend);
app.on('before-quit', () => {
  isQuitting = true;
  globalShortcut.unregisterAll();
});

app.on('window-all-closed', () => {
  if (process.platform === 'darwin') return;
});

const { app, BrowserWindow, shell, Menu } = require("electron");
const { spawn, execSync } = require("child_process");
const http = require("http");
const path = require("path");

const SERVER_PORT = 3800;
const SERVER_HOST = "zudopd.localhost";
const SERVER_URL = `http://${SERVER_HOST}:${SERVER_PORT}/pj/zudo-pd/`;
const DOC_DIR = path.join(__dirname, "..", "doc");

let serverProcess = null;
let mainWindow = null;

// --- Shell environment for nodenv/anyenv ---

function getShellEnv() {
  const userShell = process.env.SHELL || "/bin/bash";
  const rcFile = userShell.includes("zsh") ? "~/.zshrc" : "~/.bashrc";

  return new Promise((resolve) => {
    const child = spawn(userShell, ["-c", `source ${rcFile} && env`], {
      env: process.env,
    });

    let output = "";
    child.stdout.on("data", (data) => (output += data));
    child.on("close", () => {
      const env = {};
      output.split("\n").forEach((line) => {
        const [key, ...value] = line.split("=");
        if (key) env[key] = value.join("=");
      });
      resolve(env);
    });
  });
}

// --- Kill stale process on port ---

function killProcessOnPort(port) {
  try {
    const output = execSync(`lsof -ti tcp:${port}`, { encoding: "utf-8" });
    const pids = output.trim().split("\n").filter(Boolean);
    for (const pid of pids) {
      process.kill(Number(pid), "SIGKILL");
    }
  } catch {
    // No process on port - fine
  }
}

// --- Health check ---

function isServerReady(url) {
  return new Promise((resolve) => {
    const urlObj = new URL(url);
    const req = http.request(
      {
        hostname: urlObj.hostname,
        port: urlObj.port || 80,
        path: "/",
        method: "HEAD",
        timeout: 2000,
      },
      (res) => resolve(res.statusCode > 0)
    );
    req.on("error", () => resolve(false));
    req.on("timeout", () => {
      req.destroy();
      resolve(false);
    });
    req.end();
  });
}

function waitForServer(url, maxAttempts = 60, interval = 1000) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const check = async () => {
      attempts++;
      if (await isServerReady(url)) {
        resolve();
      } else if (attempts >= maxAttempts) {
        reject(new Error(`Server not ready after ${maxAttempts} attempts`));
      } else {
        setTimeout(check, interval);
      }
    };
    check();
  });
}

// --- Dev server ---

async function startDevServer() {
  const env = await getShellEnv();

  killProcessOnPort(SERVER_PORT);

  serverProcess = spawn("pnpm", ["start"], {
    cwd: DOC_DIR,
    env,
    shell: true,
    detached: true,
  });

  serverProcess.stdout.on("data", (data) => {
    process.stdout.write(data);
  });

  serverProcess.stderr.on("data", (data) => {
    process.stderr.write(data);
  });

  await waitForServer(SERVER_URL);
}

function stopDevServer() {
  if (serverProcess && !serverProcess.killed) {
    try {
      process.kill(-serverProcess.pid, "SIGTERM");
    } catch (e) {
      serverProcess.kill("SIGTERM");
    }
    serverProcess = null;
  }
}

// --- Windows ---

function createSplashWindow() {
  const splash = new BrowserWindow({
    width: 300,
    height: 300,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });
  splash.loadFile(path.join(__dirname, "splash.html"));
  return splash;
}

function createMainWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    title: "zudo-PD",
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  win.loadURL(SERVER_URL);
  win.once("ready-to-show", () => win.show());

  // Open external links in default browser
  const devServerOrigin = new URL(SERVER_URL).origin;
  win.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const parsed = new URL(url);
      if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
        return { action: "deny" };
      }
      if (parsed.origin !== devServerOrigin) {
        shell.openExternal(url);
        return { action: "deny" };
      }
    } catch {
      // Invalid URL
    }
    return { action: "deny" };
  });

  return win;
}

// --- Menu ---

const menuTemplate = [
  {
    label: "View",
    submenu: [
      { role: "reload" },
      { role: "forceReload" },
      { role: "toggleDevTools" },
    ],
  },
  {
    label: "Edit",
    submenu: [
      { role: "undo" },
      { role: "redo" },
      { type: "separator" },
      { role: "cut" },
      { role: "copy" },
      { role: "paste" },
      { role: "selectAll" },
    ],
  },
  {
    label: "Window",
    submenu: [{ role: "minimize" }, { role: "close" }],
  },
];

// --- App lifecycle ---

app.whenReady().then(async () => {
  Menu.setApplicationMenu(Menu.buildFromTemplate(menuTemplate));

  const splash = createSplashWindow();

  try {
    await startDevServer();
  } catch (e) {
    console.error("Failed to start dev server:", e);
  }

  splash.close();
  mainWindow = createMainWindow();
});

app.on("activate", async () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    if (serverProcess) {
      mainWindow = createMainWindow();
    } else {
      const splash = createSplashWindow();
      try {
        await startDevServer();
      } catch (e) {
        console.error("Failed to start dev server:", e);
      }
      splash.close();
      mainWindow = createMainWindow();
    }
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("will-quit", stopDevServer);
process.on("SIGINT", () => {
  stopDevServer();
  app.quit();
});
process.on("SIGTERM", () => {
  stopDevServer();
  app.quit();
});

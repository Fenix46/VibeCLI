import fs from "fs-extra";
import path from "path";
import net from "net";
import { spawn } from "child_process";
import { fetch } from "undici";
import { getLogsDir, getStateDir } from "../config/dirs.js";
import { AppConfig } from "../config/schema.js";
import { confirm } from "../utils/confirm.js";
import { execa } from "execa";
import { logInfo, logWarn } from "../utils/logger.js";
import { withFileLock } from "../utils/fs.js";

export type ServerState = {
  pid: number;
  port: number;
  modelPath: string;
  startedAt: string;
};

const PID_FILE = "llama-server.pid";
const STATE_FILE = "llama-server.json";
const LAST_USED_FILE = "llama-server.lastused";
const LOCK_FILE = "llama-server.lock";

function getPidPath(): string {
  return path.join(getStateDir(), PID_FILE);
}

function getStatePath(): string {
  return path.join(getStateDir(), STATE_FILE);
}

function getLastUsedPath(): string {
  return path.join(getStateDir(), LAST_USED_FILE);
}

function getLockPath(): string {
  return path.join(getStateDir(), LOCK_FILE);
}

export function getServerBaseUrl(port: number): string {
  return `http://127.0.0.1:${port}`;
}

export function readState(): ServerState | null {
  const file = getStatePath();
  if (!fs.existsSync(file)) return null;
  return fs.readJsonSync(file) as ServerState;
}

export function writeState(state: ServerState): void {
  fs.ensureDirSync(getStateDir());
  fs.writeJsonSync(getStatePath(), state, { spaces: 2 });
}

export function isPidRunning(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

export async function isPortFree(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once("error", () => resolve(false));
    server.once("listening", () => server.close(() => resolve(true)));
    server.listen(port, "127.0.0.1");
  });
}

export async function findFreePort(start: number, maxTries = 20): Promise<number> {
  let port = start;
  for (let i = 0; i < maxTries; i++) {
    if (await isPortFree(port)) return port;
    port += 1;
  }
  throw new Error("No free port found");
}

export async function startServer(config: AppConfig, modelPath: string): Promise<ServerState> {
  fs.ensureDirSync(getStateDir());
  fs.ensureDirSync(getLogsDir());
  const logPath = path.join(getLogsDir(), "llama-server.log");
  const port = await findFreePort(config.serverPort);
  const exe = config.llamaServerPath ?? "llama-server";

  const args = ["-m", modelPath, "-c", String(config.ctxSize), "--port", String(port)];
  if (config.gpuLayers > 0) {
    args.push("-ngl", String(config.gpuLayers));
  }

  const out = fs.openSync(logPath, "a");
  const child = spawn(exe, args, {
    detached: true,
    stdio: ["ignore", out, out],
    windowsHide: true
  });
  child.unref();

  // Close file descriptor after spawn to prevent leak
  fs.closeSync(out);

  if (!child.pid) {
    throw new Error("Failed to start llama-server");
  }

  fs.writeFileSync(getPidPath(), String(child.pid), "utf8");
  const state: ServerState = {
    pid: child.pid,
    port,
    modelPath,
    startedAt: new Date().toISOString()
  };
  writeState(state);
  logInfo("llama-server started", state);
  await waitForHealthy(port);
  return state;
}

export async function stopServer(): Promise<void> {
  const pidPath = getPidPath();
  const state = readState();
  if (!state || !fs.existsSync(pidPath)) return;
  const pid = Number(fs.readFileSync(pidPath, "utf8"));
  if (!isPidRunning(pid)) {
    fs.removeSync(pidPath);
    return;
  }
  if (process.platform === "win32") {
    await execa("taskkill", ["/PID", String(pid), "/T", "/F"]);
  } else {
    process.kill(pid, "SIGTERM");
  }
  fs.removeSync(pidPath);
}

export async function getStatus(): Promise<{ running: boolean; state?: ServerState }>
{
  const state = readState();
  if (!state) return { running: false };
  if (!isPidRunning(state.pid)) return { running: false };
  return { running: true, state };
}

export async function ensureServer(config: AppConfig, modelPath: string): Promise<ServerState> {
  // Use lock to prevent race conditions when multiple processes try to start server
  return withFileLock(getLockPath(), async () => {
    const status = await getStatus();
    if (status.running && status.state) {
      if (status.state.modelPath !== modelPath) {
        const ok = await confirm("llama-server is running with a different model. Restart?", true);
        if (!ok) throw new Error("Model mismatch; aborting.");
        await stopServer();
        return startServer(config, modelPath);
      }
      return status.state;
    }
    return startServer(config, modelPath);
  });
}

export async function waitForHealthy(port: number, timeoutMs = 60000): Promise<void> {
  const url = getServerBaseUrl(port);
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const health = await fetch(`${url}/health`);
      if (health.ok) return;
    } catch {
      // ignore
    }
    try {
      const models = await fetch(`${url}/v1/models`);
      if (models.ok) return;
    } catch {
      // ignore
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  logWarn("llama-server health check timed out", { port });
  throw new Error("llama-server not healthy within timeout");
}

export function markServerUsed(): void {
  fs.ensureDirSync(getStateDir());
  fs.writeFileSync(getLastUsedPath(), String(Date.now()), "utf8");
}

export async function stopIfIdle(idleMinutes: number): Promise<boolean> {
  if (idleMinutes <= 0) return false;
  const file = getLastUsedPath();
  if (!fs.existsSync(file)) return false;
  const last = Number(fs.readFileSync(file, "utf8"));
  const now = Date.now();
  if (Number.isNaN(last)) return false;
  const idleMs = idleMinutes * 60 * 1000;
  if (now - last >= idleMs) {
    await stopServer();
    return true;
  }
  return false;
}

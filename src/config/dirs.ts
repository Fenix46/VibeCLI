import os from "os";
import path from "path";
import fs from "fs-extra";

let cachedBase: string | null = null;

export function getConfigDir(): string {
  if (cachedBase) return cachedBase;
  const platform = process.platform;
  if (platform === "win32") {
    const appData = process.env.APPDATA ?? path.join(os.homedir(), "AppData", "Roaming");
    cachedBase = path.join(appData, "local");
  } else if (platform === "darwin") {
    cachedBase = path.join(os.homedir(), "Library", "Application Support", "local");
  } else {
    const xdg = process.env.XDG_CONFIG_HOME ?? path.join(os.homedir(), ".config");
    cachedBase = path.join(xdg, "local");
  }
  return cachedBase;
}

export function getModelsDir(): string {
  return path.join(getConfigDir(), "models");
}

export function getSessionsDir(): string {
  return path.join(getConfigDir(), "sessions");
}

export function getLogsDir(): string {
  return path.join(getConfigDir(), "logs");
}

export function getStateDir(): string {
  return path.join(getConfigDir(), "state");
}

export function ensureAppDirs(): void {
  fs.ensureDirSync(getConfigDir());
  fs.ensureDirSync(getModelsDir());
  fs.ensureDirSync(getSessionsDir());
  fs.ensureDirSync(getLogsDir());
  fs.ensureDirSync(getStateDir());
}

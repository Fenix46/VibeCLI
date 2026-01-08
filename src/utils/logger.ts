import fs from "fs-extra";
import path from "path";
import { getLogsDir } from "../config/dirs.js";

export type LogLevel = "info" | "warn" | "error";

let logPath: string | null = null;

function ensureLogPath(): string {
  if (!logPath) {
    const dir = getLogsDir();
    fs.ensureDirSync(dir);
    logPath = path.join(dir, "cli.log");
  }
  return logPath;
}

export function log(level: LogLevel, message: string, meta?: Record<string, unknown>): void {
  const entry = {
    ts: new Date().toISOString(),
    level,
    message,
    meta: meta ?? null
  };
  const line = JSON.stringify(entry);
  try {
    fs.appendFileSync(ensureLogPath(), line + "\n", "utf8");
  } catch {
    // Ignore logging failures.
  }
}

export function logInfo(message: string, meta?: Record<string, unknown>): void {
  log("info", message, meta);
}

export function logWarn(message: string, meta?: Record<string, unknown>): void {
  log("warn", message, meta);
}

export function logError(message: string, meta?: Record<string, unknown>): void {
  log("error", message, meta);
}

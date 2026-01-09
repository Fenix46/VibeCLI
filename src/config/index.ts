import fs from "fs-extra";
import path from "path";
import { ensureAppDirs, getConfigDir } from "./dirs.js";
import { AppConfig, configSchema, defaultConfig } from "./schema.js";
import { logWarn } from "../utils/logger.js";
import { writeJsonWithBackupSync } from "../utils/fs.js";

const CONFIG_FILE = "config.json";

export function getConfigPath(): string {
  return path.join(getConfigDir(), CONFIG_FILE);
}

export function loadConfig(): AppConfig {
  ensureAppDirs();
  const file = getConfigPath();
  if (!fs.existsSync(file)) {
    const defaults = defaultConfig();
    fs.writeJsonSync(file, defaults, { spaces: 2 });
    return defaults;
  }
  try {
    const data = fs.readJsonSync(file);
    return configSchema.parse({ ...defaultConfig(), ...data });
  } catch (err) {
    logWarn("Failed to load config.json, using defaults", { error: String(err) });
    const defaults = defaultConfig();
    writeJsonWithBackupSync(file, defaults);
    return defaults;
  }
}

export function saveConfig(config: AppConfig): void {
  ensureAppDirs();
  const file = getConfigPath();
  writeJsonWithBackupSync(file, configSchema.parse(config));
}

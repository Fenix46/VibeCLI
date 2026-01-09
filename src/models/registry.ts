import fs from "fs-extra";
import path from "path";
import { ensureAppDirs, getConfigDir } from "../config/dirs.js";
import { loadConfig, saveConfig } from "../config/index.js";
import { writeJsonWithBackupSync } from "../utils/fs.js";

export type ModelRecord = {
  id: string;
  repoId: string;
  filename: string;
  localPath: string;
  size: number;
  quant?: string;
  parameters?: string;
  sha256?: string;
  dateInstalled: string;
};

export type ModelsRegistry = {
  models: ModelRecord[];
};

const REGISTRY_FILE = "models.json";

export function getRegistryPath(): string {
  return path.join(getConfigDir(), REGISTRY_FILE);
}

export function loadRegistry(): ModelsRegistry {
  ensureAppDirs();
  const file = getRegistryPath();
  if (!fs.existsSync(file)) {
    const data: ModelsRegistry = { models: [] };
    fs.writeJsonSync(file, data, { spaces: 2 });
    return data;
  }
  return fs.readJsonSync(file) as ModelsRegistry;
}

export function saveRegistry(registry: ModelsRegistry): void {
  ensureAppDirs();
  const file = getRegistryPath();
  writeJsonWithBackupSync(file, registry);
}

export function addModel(record: ModelRecord): void {
  const registry = loadRegistry();
  registry.models.push(record);
  saveRegistry(registry);

  // Set as default if no default model is configured
  const config = loadConfig();
  if (!config.defaultModelId) {
    config.defaultModelId = record.id;
    saveConfig(config);
  }
}

export function removeModel(id: string): ModelRecord | null {
  const registry = loadRegistry();
  const index = registry.models.findIndex((m) => m.id === id);
  if (index === -1) return null;

  const [removed] = registry.models.splice(index, 1);
  saveRegistry(registry);

  // Update default if the removed model was default
  const config = loadConfig();
  if (config.defaultModelId === id) {
    config.defaultModelId = registry.models[0]?.id;
    saveConfig(config);
  }

  return removed;
}

export function setDefaultModel(id: string): boolean {
  const registry = loadRegistry();
  if (!registry.models.find((m) => m.id === id)) return false;

  const config = loadConfig();
  config.defaultModelId = id;
  saveConfig(config);
  return true;
}

export function getDefaultModel(): ModelRecord | null {
  const registry = loadRegistry();
  const config = loadConfig();
  const id = config.defaultModelId;
  return registry.models.find((m) => m.id === id) ?? registry.models[0] ?? null;
}

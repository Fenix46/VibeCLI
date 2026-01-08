import fs from "fs-extra";
import path from "path";

export async function withFileLock<T>(lockPath: string, fn: () => Promise<T>, retries = 20): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try {
      await fs.open(lockPath, "wx");
      try {
        return await fn();
      } finally {
        await fs.remove(lockPath);
      }
    } catch {
      await new Promise((r) => setTimeout(r, 250));
    }
  }
  throw new Error(`Failed to acquire lock: ${lockPath}`);
}

export function safeFileName(name: string): string {
  return name.replace(/[^a-zA-Z0-9._-]+/g, "_");
}

export function ensureParent(filePath: string): void {
  fs.ensureDirSync(path.dirname(filePath));
}

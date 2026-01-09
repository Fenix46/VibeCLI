import fs from "fs-extra";
import path from "path";

/**
 * Improved file lock with PID tracking and stale lock detection
 */
export async function withFileLock<T>(lockPath: string, fn: () => Promise<T>, retries = 20): Promise<T> {
  const currentPid = process.pid;

  for (let i = 0; i < retries; i++) {
    try {
      // Try to acquire lock
      await fs.writeFile(lockPath, String(currentPid), { flag: "wx" });
      try {
        return await fn();
      } finally {
        // Only remove lock if we still own it
        try {
          const lockPid = Number(await fs.readFile(lockPath, "utf8"));
          if (lockPid === currentPid) {
            await fs.remove(lockPath);
          }
        } catch {
          // Lock file already removed or unreadable, ignore
        }
      }
    } catch (err: any) {
      // Lock exists, check if stale
      if (err.code === "EEXIST") {
        try {
          const lockPid = Number(await fs.readFile(lockPath, "utf8"));
          if (!isNaN(lockPid) && !isPidRunning(lockPid)) {
            // Stale lock, remove it
            await fs.remove(lockPath);
            continue; // Retry immediately
          }
        } catch {
          // Can't read lock file, try to remove it
          try {
            await fs.remove(lockPath);
            continue;
          } catch {
            // ignore
          }
        }
      }
      await new Promise((r) => setTimeout(r, 250));
    }
  }
  throw new Error(`Failed to acquire lock: ${lockPath}`);
}

function isPidRunning(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

export function safeFileName(name: string): string {
  return name.replace(/[^a-zA-Z0-9._-]+/g, "_");
}

export function ensureParent(filePath: string): void {
  fs.ensureDirSync(path.dirname(filePath));
}

/**
 * Create a timestamped backup of a file before overwriting it
 * Keeps up to maxBackups backup files
 */
export async function createBackup(filePath: string, maxBackups = 5): Promise<void> {
  if (!await fs.pathExists(filePath)) {
    return; // No file to backup
  }

  const dir = path.dirname(filePath);
  const ext = path.extname(filePath);
  const base = path.basename(filePath, ext);
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const backupPath = path.join(dir, `${base}.backup.${timestamp}${ext}`);

  try {
    await fs.copy(filePath, backupPath);

    // Clean up old backups
    const backupPattern = new RegExp(`^${base}\\.backup\\..*\\${ext}$`);
    const files = await fs.readdir(dir);
    const backupFiles = files
      .filter((f) => backupPattern.test(f))
      .map((f) => path.join(dir, f))
      .sort(); // Sort by name (ISO timestamp sorts chronologically)

    // Remove oldest backups if we exceed maxBackups
    while (backupFiles.length > maxBackups) {
      const oldest = backupFiles.shift();
      if (oldest) await fs.remove(oldest);
    }
  } catch (err) {
    // Backup failure should not block the main operation
    console.warn(`Failed to create backup of ${filePath}:`, err);
  }
}

/**
 * Write JSON file with automatic backup (async)
 */
export async function writeJsonWithBackup(
  filePath: string,
  data: any,
  options: { spaces?: number; maxBackups?: number } = {}
): Promise<void> {
  await createBackup(filePath, options.maxBackups ?? 5);
  await fs.writeJson(filePath, data, { spaces: options.spaces ?? 2 });
}

/**
 * Write JSON file with automatic backup (sync)
 */
export function writeJsonWithBackupSync(
  filePath: string,
  data: any,
  options: { spaces?: number; maxBackups?: number } = {}
): void {
  // Sync backup
  if (fs.existsSync(filePath)) {
    try {
      const dir = path.dirname(filePath);
      const ext = path.extname(filePath);
      const base = path.basename(filePath, ext);
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      const backupPath = path.join(dir, `${base}.backup.${timestamp}${ext}`);

      fs.copySync(filePath, backupPath);

      // Clean up old backups
      const maxBackups = options.maxBackups ?? 5;
      const backupPattern = new RegExp(`^${base}\\.backup\\..*\\${ext}$`);
      const files = fs.readdirSync(dir);
      const backupFiles = files
        .filter((f) => backupPattern.test(f))
        .map((f) => path.join(dir, f))
        .sort();

      while (backupFiles.length > maxBackups) {
        const oldest = backupFiles.shift();
        if (oldest) fs.removeSync(oldest);
      }
    } catch (err) {
      console.warn(`Failed to create backup of ${filePath}:`, err);
    }
  }

  fs.writeJsonSync(filePath, data, { spaces: options.spaces ?? 2 });
}

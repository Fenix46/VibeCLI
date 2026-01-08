import path from "path";
import fs from "fs-extra";
import { execa } from "execa";

export async function getRepoRoot(cwd: string): Promise<string | null> {
  try {
    const { stdout } = await execa("git", ["rev-parse", "--show-toplevel"], { cwd });
    return stdout.trim();
  } catch {
    return null;
  }
}

export function isGitRepo(cwd: string): boolean {
  return fs.existsSync(path.join(cwd, ".git"));
}

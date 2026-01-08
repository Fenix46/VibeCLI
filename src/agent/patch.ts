import fs from "fs-extra";
import path from "path";
import { execa } from "execa";
import { applyUnifiedDiff } from "../utils/diff.js";
import { isGitRepo } from "../utils/repo.js";

export async function applyPatch(diff: string, repoRoot: string): Promise<void> {
  if (isGitRepo(repoRoot)) {
    await execa("git", ["apply", "-"], { cwd: repoRoot, input: diff });
    return;
  }
  const fileDiffs = splitDiffByFile(diff);
  const root = path.resolve(repoRoot);
  for (const fileDiff of fileDiffs) {
    const target = path.resolve(repoRoot, fileDiff.path);
    if (!target.startsWith(root)) {
      throw new Error("Patch touches path outside repo root");
    }
    const original = fs.existsSync(target) ? fs.readFileSync(target, "utf8") : "";
    const updated = applyUnifiedDiff(original, fileDiff.diff);
    fs.ensureDirSync(path.dirname(target));
    fs.writeFileSync(target, updated, "utf8");
  }
}

type FileDiff = { path: string; diff: string };

function splitDiffByFile(diff: string): FileDiff[] {
  const lines = diff.split(/\r?\n/);
  const fileDiffs: FileDiff[] = [];
  let currentPath: string | null = null;
  let buffer: string[] = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.startsWith("+++ ")) {
      if (currentPath && buffer.length > 0) {
        fileDiffs.push({ path: currentPath, diff: buffer.join("\n") });
      }
      const pathLine = line.replace(/^\+\+\+\s+/, "");
      currentPath = pathLine.replace(/^b\//, "");
      buffer = [line];
      continue;
    }
    if (currentPath) {
      buffer.push(line);
    }
  }
  if (currentPath && buffer.length > 0) {
    fileDiffs.push({ path: currentPath, diff: buffer.join("\n") });
  }
  return fileDiffs;
}

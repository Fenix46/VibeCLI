import fs from "fs-extra";
import path from "path";
import { execa } from "execa";

export type SearchResult = {
  file: string;
  line: number;
  text: string;
};

export async function hasRg(): Promise<boolean> {
  try {
    await execa("rg", ["--version"]);
    return true;
  } catch {
    return false;
  }
}

export async function searchText(root: string, query: string): Promise<SearchResult[]> {
  if (await hasRg()) {
    const { stdout } = await execa("rg", ["--line-number", "--no-heading", query, root]);
    if (!stdout.trim()) return [];
    return stdout
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => {
        const first = line.indexOf(":");
        const second = line.indexOf(":", first + 1);
        const file = line.slice(0, first);
        const lineNo = Number(line.slice(first + 1, second));
        const text = line.slice(second + 1);
        return { file, line: lineNo, text };
      });
  }

  const results: SearchResult[] = [];
  const files = listFiles(root);
  for (const file of files) {
    const content = fs.readFileSync(file, "utf8");
    const lines = content.split(/\r?\n/);
    lines.forEach((text, idx) => {
      if (text.includes(query)) {
        results.push({ file, line: idx + 1, text });
      }
    });
  }
  return results;
}

function listFiles(root: string): string[] {
  const entries = fs.readdirSync(root, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    const full = path.join(root, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name.startsWith(".")) continue;
      files.push(...listFiles(full));
    } else {
      files.push(full);
    }
  }
  return files;
}

import { fetch } from "undici";
import path from "path";
import fs from "fs-extra";
import cliProgress from "cli-progress";
import { getModelsDir } from "../config/dirs.js";
import { safeFileName, withFileLock, ensureParent } from "../utils/fs.js";
import { logInfo } from "../utils/logger.js";

const HF_API = "https://huggingface.co/api";

export type HfSearchResult = {
  id: string;
  likes?: number;
  downloads?: number;
  ggufFiles: string[];
};

export type HfModelFile = {
  name: string;
  size?: number;
  sha256?: string;
};

function getHeaders(): Record<string, string> {
  const token = process.env.HF_TOKEN;
  if (token) return { Authorization: `Bearer ${token}` };
  return {};
}

export async function searchModels(query: string, limit = 10): Promise<HfSearchResult[]> {
  const url = `${HF_API}/models?search=${encodeURIComponent(query)}&limit=${limit}`;
  const res = await fetch(url, { headers: getHeaders() });
  if (!res.ok) throw new Error(`HF search failed: ${res.status}`);
  const data = (await res.json()) as Array<{ id: string; likes?: number; downloads?: number }>;
  const results: HfSearchResult[] = [];
  for (const item of data) {
    const ggufFiles = await listGgufFiles(item.id);
    if (ggufFiles.length === 0) continue;
    results.push({ id: item.id, likes: item.likes, downloads: item.downloads, ggufFiles });
  }
  return results;
}

export async function listGgufFiles(repoId: string): Promise<string[]> {
  const detail = await fetch(`${HF_API}/models/${repoId}`, { headers: getHeaders() });
  if (!detail.ok) return [];
  const info = (await detail.json()) as { siblings?: Array<{ rfilename: string }> };
  const siblings = info.siblings ?? [];
  return siblings.map((s) => s.rfilename).filter((name) => name.toLowerCase().endsWith(".gguf"));
}

export async function getModelFiles(repoId: string): Promise<HfModelFile[]> {
  const detail = await fetch(`${HF_API}/models/${repoId}`, { headers: getHeaders() });
  if (!detail.ok) throw new Error(`HF model fetch failed: ${detail.status}`);
  const info = (await detail.json()) as {
    siblings?: Array<{ rfilename: string; size?: number; lfs?: { sha256?: string; size?: number } }>;
  };
  return (info.siblings ?? [])
    .filter((s) => s.rfilename.toLowerCase().endsWith(".gguf"))
    .map((s) => ({
      name: s.rfilename,
      size: s.size ?? s.lfs?.size,
      sha256: s.lfs?.sha256
    }));
}

export async function downloadModelFile(repoId: string, filename: string): Promise<{ path: string; size: number; sha256?: string }> {
  const modelsDir = getModelsDir();
  const safeName = safeFileName(`${repoId}__${path.basename(filename)}`);
  const target = path.join(modelsDir, safeName);
  ensureParent(target);
  const lockPath = target + ".lock";

  return withFileLock(lockPath, async () => {
    const url = `https://huggingface.co/${repoId}/resolve/main/${filename}`;
    const headers = getHeaders();
    let start = 0;
    if (fs.existsSync(target)) {
      start = fs.statSync(target).size;
      if (start > 0) headers.Range = `bytes=${start}-`;
    }

    const res = await fetch(url, { headers });
    if (!res.ok && res.status !== 206) {
      throw new Error(`Download failed: ${res.status}`);
    }
    if (start > 0 && res.status === 200) {
      start = 0;
      fs.truncateSync(target, 0);
    }

    const total = Number(res.headers.get("content-length") ?? "0") + start;
    const bar = new cliProgress.SingleBar(
      { format: "Downloading [{bar}] {percentage}% | {value}/{total} bytes" },
      cliProgress.Presets.shades_classic
    );
    if (total > 0) bar.start(total, start);

    const writeStream = fs.createWriteStream(target, { flags: "a" });
    const reader = res.body?.getReader();
    if (!reader) throw new Error("No response body");
    let downloaded = start;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (value) {
        writeStream.write(Buffer.from(value));
        downloaded += value.length;
        if (total > 0) bar.update(downloaded);
      }
    }
    writeStream.close();
    if (total > 0) bar.stop();

    logInfo("Model download complete", { repoId, filename, path: target, size: downloaded });
    return { path: target, size: downloaded };
  });
}

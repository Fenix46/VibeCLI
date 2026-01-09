import inquirer from "inquirer";
import path from "path";
import chalk from "chalk";
import fs from "fs-extra";
import crypto from "crypto";
import { searchModels, getModelFiles, downloadModelFile } from "../hf/client.js";
import { addModel, loadRegistry, removeModel, setDefaultModel } from "./registry.js";
import { loadConfig } from "../config/index.js";
import { safeFileName } from "../utils/fs.js";

export async function modelSearch(query: string): Promise<void> {
  const results = await searchModels(query, 10);
  if (results.length === 0) {
    console.log("No GGUF models found.");
    return;
  }
  for (const res of results) {
    console.log(chalk.cyan(res.id));
    console.log(`  likes: ${res.likes ?? 0} | downloads: ${res.downloads ?? 0}`);
    console.log(`  gguf: ${res.ggufFiles.slice(0, 3).join(", ")}${res.ggufFiles.length > 3 ? "..." : ""}`);
  }
}

export async function modelInstall(repoId: string, filename?: string): Promise<void> {
  const files = await getModelFiles(repoId);
  if (files.length === 0) throw new Error("No GGUF files found in repo.");

  let picked = filename;
  if (!picked) {
    const answer = (await inquirer.prompt([
      { type: "list", name: "file", message: "Select GGUF file", choices: files.map((f) => f.name) }
    ])) as { file: string };
    picked = answer.file;
  }
  if (!picked) throw new Error("No file selected.");

  const fileMeta = files.find((f) => f.name === picked);
  const result = await downloadModelFile(repoId, picked);
  if (fileMeta?.size && fileMeta.size !== result.size) {
    console.log(chalk.yellow(`Warning: expected size ${fileMeta.size}, got ${result.size}`));
  }
  if (fileMeta?.sha256) {
    const hash = await sha256File(result.path);
    if (hash !== fileMeta.sha256) {
      console.log(chalk.yellow(`Warning: SHA256 mismatch. expected ${fileMeta.sha256} got ${hash}`));
    }
  }

  const id = safeFileName(`${repoId}-${path.basename(picked)}`);
  const { parameters, quant } = parseModelMeta(picked);
  addModel({
    id,
    repoId,
    filename: picked,
    localPath: result.path,
    size: result.size,
    quant,
    parameters,
    sha256: fileMeta?.sha256,
    dateInstalled: new Date().toISOString()
  });

  console.log(chalk.green(`Installed ${id}`));
}

export async function modelList(): Promise<void> {
  const registry = loadRegistry();
  if (registry.models.length === 0) {
    console.log("No models installed.");
    return;
  }
  const config = loadConfig();
  for (const model of registry.models) {
    const isDefault = model.id === config.defaultModelId;
    console.log(`${isDefault ? "*" : " "} ${model.id} -> ${model.localPath}`);
  }
}

export async function modelRemove(id: string): Promise<void> {
  const removed = removeModel(id);
  if (!removed) {
    console.log("Model not found.");
    return;
  }
  if (fs.existsSync(removed.localPath)) {
    fs.removeSync(removed.localPath);
  }
  console.log(chalk.green(`Removed ${id}`));
}

export async function modelSetDefault(id: string): Promise<void> {
  const ok = setDefaultModel(id);
  if (!ok) {
    console.log("Model not found.");
    return;
  }
  console.log(chalk.green(`Default model set to ${id}`));
}

function parseModelMeta(filename: string): { parameters?: string; quant?: string } {
  const base = path.basename(filename);
  const quantMatch = base.match(/Q\d[_\w-]*/i);
  const paramMatch = base.match(/(\d+\.?\d*)[bB]/);
  return { quant: quantMatch?.[0], parameters: paramMatch?.[0] };
}

async function sha256File(filePath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash("sha256");
    const stream = fs.createReadStream(filePath);
    stream.on("data", (chunk) => hash.update(chunk));
    stream.on("error", (err) => reject(err));
    stream.on("end", () => resolve(hash.digest("hex")));
  });
}

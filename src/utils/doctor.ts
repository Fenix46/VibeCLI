import fs from "fs-extra";
import os from "os";
import path from "path";
import { execa } from "execa";
import chalk from "chalk";
import { getConfigDir } from "../config/dirs.js";

export async function runDoctor(): Promise<void> {
  console.log(chalk.cyan("local doctor"));

  const checks: Array<{ name: string; ok: boolean; details?: string }> = [];

  const nodeMajor = Number(process.versions.node.split(".")[0]);
  checks.push({ name: "node version", ok: nodeMajor >= 18, details: process.version });

  const llamaOk = await hasCommand(process.platform === "win32" ? "where" : "which", "llama-server");
  checks.push({ name: "llama-server in PATH", ok: llamaOk });

  const rgOk = await hasCommand("rg", "--version");
  checks.push({ name: "ripgrep available", ok: rgOk });

  const configDir = getConfigDir();
  try {
    fs.ensureDirSync(configDir);
    const testPath = path.join(configDir, ".write-test");
    fs.writeFileSync(testPath, "ok", "utf8");
    fs.removeSync(testPath);
    checks.push({ name: "config dir writable", ok: true, details: configDir });
  } catch (err) {
    checks.push({ name: "config dir writable", ok: false, details: String(err) });
  }

  const disk = await getDiskFree(configDir);
  checks.push({ name: "disk free", ok: disk.freeGb > 1, details: `${disk.freeGb.toFixed(2)} GB free` });
  checks.push({ name: "HF_TOKEN set", ok: Boolean(process.env.HF_TOKEN) });

  for (const check of checks) {
    const icon = check.ok ? chalk.green("OK") : chalk.red("FAIL");
    console.log(`${icon} ${check.name}${check.details ? ` - ${check.details}` : ""}`);
  }
}

async function hasCommand(cmd: string, arg: string): Promise<boolean> {
  try {
    await execa(cmd, [arg]);
    return true;
  } catch {
    return false;
  }
}

async function getDiskFree(targetPath: string): Promise<{ freeGb: number }> {
  try {
    const stats = fs.statfsSync(targetPath);
    const freeBytes = stats.bavail * stats.bsize;
    return { freeGb: freeBytes / 1024 / 1024 / 1024 };
  } catch {
    return { freeGb: 0 };
  }
}

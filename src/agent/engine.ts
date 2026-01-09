import path from "path";
import fs from "fs-extra";
import ora from "ora";
import chalk from "chalk";
import { loadConfig } from "../config/index.js";
import { ensureServer, getServerBaseUrl, stopIfIdle, stopManagedServerOnExit } from "../server/manager.js";
import { streamChatCompletion, chatCompletion, ChatMessage } from "../server/llmClient.js";
import { confirm } from "../utils/confirm.js";
import { getRepoRoot } from "../utils/repo.js";
import { searchText } from "../utils/rg.js";
import { applyPatch } from "./patch.js";
import { saveSession } from "../utils/sessions.js";
import { execa } from "execa";

const SYSTEM_PROMPT = `You are a coding agent. Follow the protocol strictly.
Output only a JSON object with one of:
{ "type": "plan", "steps": ["..."] }
{ "type": "tool", "name": "READ_FILE|WRITE_FILE|LIST_TREE|SEARCH|RUN_CMD|APPLY_PATCH|GIT_STATUS|GIT_DIFF", "args": { ... } }
{ "type": "patch", "diff": "...unified diff..." }
{ "type": "final", "summary": "...", "verification": ["..."] }
Rules:
- Use READ_FILE before proposing changes.
- Request APPLY_PATCH only with unified diff.
- Keep steps short.
`;

export type CodeAgentOptions = {
  prompt: string;
  repoPath: string;
  modelPath: string;
  dryRun?: boolean;
};

export async function runCodeAgent(options: CodeAgentOptions): Promise<void> {
  const config = loadConfig();
  const spinner = ora("Preparing agent...").start();
  const repoRoot = (await getRepoRoot(options.repoPath)) ?? options.repoPath;

  const state = await ensureServer(config, options.modelPath, {
    managed: true,
    ownerPid: process.pid
  });
  const baseUrl = getServerBaseUrl(state.port);
  spinner.succeed(`Connected to llama-server on ${baseUrl}`);

  const messages: ChatMessage[] = [
    { role: "system", content: SYSTEM_PROMPT },
    { role: "system", content: `Repo root: ${repoRoot}` },
    { role: "user", content: options.prompt }
  ];

  const planRaw = await chatCompletion(baseUrl, messages);
  const planObj = parseJson(planRaw);
  if (planObj?.type !== "plan") throw new Error("Expected plan response");

  console.log(chalk.cyan("Plan:"));
  for (const step of planObj.steps ?? []) {
    console.log(`- ${step}`);
  }
  const proceed = await confirm("Continue with this plan?", true);
  if (!proceed) return;
  messages.push({ role: "assistant", content: JSON.stringify(planObj) });

  let finished = false;
  while (!finished) {
    const response = await chatCompletion(baseUrl, messages);
    const obj = parseJson(response);
    if (!obj) throw new Error("Model did not return JSON");

    if (obj.type === "tool") {
      const result = await executeTool(obj.name, obj.args ?? {}, repoRoot, options.dryRun ?? false);
      messages.push({ role: "assistant", content: JSON.stringify(obj) });
      messages.push({ role: "user", content: `TOOL_RESULT ${JSON.stringify(result)}` });
      continue;
    }

    if (obj.type === "patch") {
      const diff = String(obj.diff ?? "");
      console.log(chalk.yellow("Proposed diff:\n"));
      console.log(diff);
      if (options.dryRun) {
        messages.push({ role: "assistant", content: JSON.stringify(obj) });
        messages.push({ role: "user", content: "TOOL_RESULT dry-run: patch not applied" });
        continue;
      }
      const ok = await confirm("Apply this patch?", false);
      if (!ok) {
        messages.push({ role: "assistant", content: JSON.stringify(obj) });
        messages.push({ role: "user", content: "TOOL_RESULT patch rejected" });
        continue;
      }
      await applyPatch(diff, repoRoot);
      messages.push({ role: "assistant", content: JSON.stringify(obj) });
      messages.push({ role: "user", content: "TOOL_RESULT patch applied" });
      continue;
    }

    if (obj.type === "final") {
      console.log(chalk.green(obj.summary ?? "Done."));
      if (Array.isArray(obj.verification) && obj.verification.length > 0) {
        console.log(chalk.cyan("Verification:"));
        obj.verification.forEach((v: string) => console.log(`- ${v}`));
      }
      saveSession("code", "code-session", [
        { role: "user", content: options.prompt },
        { role: "assistant", content: JSON.stringify(obj) }
      ]);
      finished = true;
      break;
    }

    throw new Error("Unexpected response type");
  }

  const stopped = await stopManagedServerOnExit();
  if (!stopped) {
    await stopIfIdle(config.idleTimeoutMinutes);
  }
}

async function executeTool(
  name: string,
  args: Record<string, unknown>,
  repoRoot: string,
  dryRun: boolean
): Promise<unknown> {
  switch (name) {
    case "READ_FILE": {
      const file = await resolvePath(repoRoot, String(args.path ?? ""));
      return fs.readFileSync(file, "utf8");
    }
    case "WRITE_FILE": {
      const file = await resolvePath(repoRoot, String(args.path ?? ""));
      if (dryRun) {
        console.log(chalk.yellow(`dry-run: would write ${file}`));
        return { dryRun: true, path: file };
      }
      const allow = await confirm(`Write file ${file}?`, false);
      if (!allow) throw new Error("Write denied");
      fs.ensureDirSync(path.dirname(file));
      fs.writeFileSync(file, String(args.content ?? ""), "utf8");
      return { ok: true };
    }
    case "LIST_TREE": {
      return listTree(repoRoot);
    }
    case "SEARCH": {
      const query = String(args.query ?? "");
      return await searchText(repoRoot, query);
    }
    case "RUN_CMD": {
      const cmd = String(args.command ?? "");
      if (dryRun) {
        console.log(chalk.yellow(`dry-run: would run ${cmd}`));
        return { dryRun: true, command: cmd };
      }

      // Check for dangerous patterns
      if (isRiskyCommand(cmd)) {
        throw new Error(`Dangerous command blocked: ${cmd}`);
      }

      // Parse command and arguments safely
      const parsed = parseCommand(cmd);
      if (!parsed) {
        throw new Error(`Cannot parse command safely: ${cmd}`);
      }

      // Always require confirmation for commands (unless whitelisted)
      if (!isWhitelistedCommand(parsed.command)) {
        const ok = await confirm(`Run command: ${cmd}?`, false);
        if (!ok) throw new Error("Command denied");
      }

      // Execute with argument array (no shell injection possible)
      try {
        const { stdout, stderr } = await execa(parsed.command, parsed.args, {
          cwd: repoRoot,
          shell: false,
          timeout: 30000 // 30 second timeout
        });
        return { stdout, stderr };
      } catch (err: any) {
        return { error: err.message, stdout: err.stdout || "", stderr: err.stderr || "" };
      }
    }
    case "GIT_STATUS": {
      const { stdout } = await execa("git", ["status", "--porcelain"], { cwd: repoRoot });
      return stdout;
    }
    case "GIT_DIFF": {
      const { stdout } = await execa("git", ["diff"], { cwd: repoRoot });
      return stdout;
    }
    case "APPLY_PATCH": {
      const diff = String(args.diff ?? "");
      console.log(chalk.yellow("Proposed diff:\n"));
      console.log(diff);
      if (dryRun) {
        return { dryRun: true };
      }
      const ok = await confirm("Apply this patch?", false);
      if (!ok) throw new Error("Patch rejected");
      await applyPatch(diff, repoRoot);
      return { ok: true };
    }
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

async function resolvePath(repoRoot: string, inputPath: string): Promise<string> {
  const resolved = path.resolve(repoRoot, inputPath);
  const root = path.resolve(repoRoot);
  if (!resolved.startsWith(root)) {
    const ok = await confirm(`Access path outside repo? ${resolved}`, false);
    if (!ok) throw new Error("Path outside repo root");
  }
  return resolved;
}

function listTree(root: string): string[] {
  const entries = fs.readdirSync(root, { withFileTypes: true });
  const result: string[] = [];
  for (const entry of entries) {
    if (entry.name === "node_modules" || entry.name.startsWith(".")) continue;
    const full = path.join(root, entry.name);
    result.push(path.relative(root, full));
  }
  return result;
}

function isRiskyCommand(cmd: string): boolean {
  // Block commands with dangerous patterns
  const dangerousPatterns = [
    /rm\s+(-rf|-r|-f)/i, // rm with recursive/force flags
    /del\s+/i, // Windows delete
    /format\s/i, // Format drives
    /mkfs/i, // Make filesystem
    /dd\s/i, // Disk duplicator
    /shutdown/i,
    /reboot/i,
    /halt/i,
    /:>/,  // Bash redirect that clears files
    />\s*\/dev/i, // Writing to device files
    /chmod\s+777/i, // Dangerous permissions
    /sudo\s/i, // Privilege escalation
    /curl.*\|\s*(bash|sh)/i, // Download and execute
    /wget.*\|\s*(bash|sh)/i, // Download and execute
    /eval\s/i, // Code evaluation
    /powershell.*Remove-Item/i, // PowerShell remove
    /;\s*rm/i, // Chained rm command
    /&&\s*rm/i, // Chained rm command
  ];

  return dangerousPatterns.some((pattern) => pattern.test(cmd));
}

/**
 * Whitelist of safe commands that don't require confirmation
 */
function isWhitelistedCommand(cmd: string): boolean {
  const whitelist = [
    "ls", "dir", "pwd", "cat", "head", "tail", "echo",
    "date", "whoami", "hostname", "uname",
    "npm", "node", "python", "python3", "pip", "pipenv",
    "cargo", "rustc", "go", "java", "javac", "mvn", "gradle",
    "make", "cmake", "gcc", "g++", "clang",
    "git", // git commands are generally safe for read operations
  ];
  return whitelist.includes(cmd.toLowerCase());
}

/**
 * Parse command string into command and arguments array
 * Simple parser that handles basic quoting
 */
function parseCommand(cmdString: string): { command: string; args: string[] } | null {
  cmdString = cmdString.trim();
  if (!cmdString) return null;

  // Block commands with shell operators (pipes, redirects, etc)
  if (/[|&;<>]/.test(cmdString)) {
    return null; // Cannot safely parse shell operators
  }

  // Simple tokenizer that handles quotes
  const tokens: string[] = [];
  let current = "";
  let inQuote = false;
  let quoteChar = "";

  for (let i = 0; i < cmdString.length; i++) {
    const char = cmdString[i];

    if (!inQuote && (char === '"' || char === "'")) {
      inQuote = true;
      quoteChar = char;
    } else if (inQuote && char === quoteChar) {
      inQuote = false;
      quoteChar = "";
    } else if (!inQuote && char === " ") {
      if (current) {
        tokens.push(current);
        current = "";
      }
    } else {
      current += char;
    }
  }

  if (current) tokens.push(current);
  if (tokens.length === 0) return null;

  return {
    command: tokens[0],
    args: tokens.slice(1)
  };
}

function parseJson(text: string): any {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

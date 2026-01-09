import path from "path";
import fs from "fs-extra";
import { chatCompletion, ChatMessage } from "../server/llmClient.js";
import { execa } from "execa";
import { searchText } from "../utils/rg.js";
import { applyPatch } from "../agent/patch.js";

type ToolName =
  | "READ_FILE"
  | "WRITE_FILE"
  | "APPLY_PATCH"
  | "LIST_TREE"
  | "SEARCH"
  | "GIT_STATUS"
  | "GIT_DIFF";

type ToolCall = {
  type: "tool";
  name: ToolName | string;
  args?: Record<string, unknown>;
};

const TOOL_NAMES: ToolName[] = [
  "READ_FILE",
  "WRITE_FILE",
  "APPLY_PATCH",
  "LIST_TREE",
  "SEARCH",
  "GIT_STATUS",
  "GIT_DIFF"
];

export function createChatSystemMessages(repoRoot: string): ChatMessage[] {
  const prompt = `You are a local coding assistant with access to tools for inspecting the local codebase.
You can answer normally or call tools when you need file info.
Do NOT ask the user to paste code or provide file listings; use the tools instead.
When you need a tool, output ONLY a JSON object:
{"type":"tool","name":"TOOL_NAME","args":{...}}
You will receive tool output as: TOOL_RESULT <json>.
Use relative paths within the repo root and avoid paths outside it.

Repo root: ${repoRoot}

Available tools:
- LIST_TREE { "path"?: "relative/dir", "limit"?: number }
- READ_FILE { "path": "relative/file" }
- WRITE_FILE { "path": "relative/file", "content": "..." }
- APPLY_PATCH { "diff": "unified diff" }
- SEARCH { "query": "text" }
- GIT_STATUS {}
- GIT_DIFF {}
`;

  return [{ role: "system", content: prompt }];
}

export async function runToolAwareCompletion(
  baseUrl: string,
  messages: ChatMessage[],
  repoRoot: string,
  maxToolTurns = 8
): Promise<string> {
  let turns = 0;
  while (turns < maxToolTurns) {
    const response = await chatCompletion(baseUrl, messages);
    const obj = parseJson(response) as ToolCall | null;
    if (obj?.type === "tool") {
      const result = await executeChatTool(repoRoot, obj.name, obj.args ?? {});
      messages.push({ role: "assistant", content: JSON.stringify(obj) });
      messages.push({ role: "user", content: `TOOL_RESULT ${JSON.stringify(result)}` });
      turns += 1;
      continue;
    }
    return response;
  }
  return "Tool loop exceeded maximum steps.";
}

async function executeChatTool(
  repoRoot: string,
  name: string,
  args: Record<string, unknown>
): Promise<unknown> {
  if (!TOOL_NAMES.includes(name as ToolName)) {
    return { error: `Tool not available: ${name}` };
  }

  switch (name as ToolName) {
    case "READ_FILE": {
      const file = resolvePath(repoRoot, String(args.path ?? ""));
      if (!fs.existsSync(file)) return { error: `File not found: ${args.path}` };
      return fs.readFileSync(file, "utf8");
    }
    case "WRITE_FILE": {
      const file = resolvePath(repoRoot, String(args.path ?? ""));
      const content = String(args.content ?? "");
      fs.ensureDirSync(path.dirname(file));
      fs.writeFileSync(file, content, "utf8");
      return { ok: true, path: path.relative(repoRoot, file) };
    }
    case "APPLY_PATCH": {
      const diff = String(args.diff ?? "");
      if (!diff.trim()) return { error: "Missing diff" };
      await applyPatch(diff, repoRoot);
      return { ok: true };
    }
    case "LIST_TREE": {
      const dir = resolvePath(repoRoot, String(args.path ?? "."));
      if (!fs.existsSync(dir)) return { error: `Path not found: ${args.path}` };
      const limit = Number(args.limit ?? 200);
      return listTree(dir, repoRoot, Number.isFinite(limit) ? limit : 200);
    }
    case "SEARCH": {
      const query = String(args.query ?? "").trim();
      if (!query) return { error: "Missing query" };
      const results = await searchText(repoRoot, query);
      return results.slice(0, 200);
    }
    case "GIT_STATUS": {
      try {
        const { stdout } = await execa("git", ["status", "--porcelain"], { cwd: repoRoot });
        return stdout.trim();
      } catch (err: any) {
        return { error: `GIT_STATUS failed: ${err.message}` };
      }
    }
    case "GIT_DIFF": {
      try {
        const { stdout } = await execa("git", ["diff"], { cwd: repoRoot });
        return stdout;
      } catch (err: any) {
        return { error: `GIT_DIFF failed: ${err.message}` };
      }
    }
  }
}

function resolvePath(repoRoot: string, inputPath: string): string {
  const root = path.resolve(repoRoot);
  const resolved = path.resolve(repoRoot, inputPath);
  const relative = path.relative(root, resolved);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(`Path outside repo root: ${inputPath}`);
  }
  return resolved;
}

function listTree(dir: string, repoRoot: string, limit: number): string[] {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const result: string[] = [];
  for (const entry of entries) {
    if (entry.name === "node_modules" || entry.name.startsWith(".")) continue;
    const full = path.join(dir, entry.name);
    result.push(path.relative(repoRoot, full));
    if (result.length >= limit) break;
  }
  return result;
}

function parseJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

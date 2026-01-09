import readline from "readline";
import chalk from "chalk";
import { loadConfig } from "../config/index.js";
import { ensureServer, getServerBaseUrl, stopIfIdle, stopManagedServerOnExit } from "../server/manager.js";
import { ChatMessage } from "../server/llmClient.js";
import { getDefaultModel } from "../models/registry.js";
import { saveSession } from "../utils/sessions.js";
import { createChatSystemMessages, runToolAwareCompletion } from "./tooling.js";
import { getRepoRoot } from "../utils/repo.js";

export async function runChatRepl(modelPath?: string): Promise<void> {
  const config = loadConfig();
  const model = modelPath ? { localPath: modelPath } : getDefaultModel();
  if (!model) throw new Error("No model installed. Use `local model install`.");

  const state = await ensureServer(config, model.localPath, {
    managed: true,
    ownerPid: process.pid
  });
  const baseUrl = getServerBaseUrl(state.port);
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const repoRoot = (await getRepoRoot(process.cwd())) ?? process.cwd();
  const messages: ChatMessage[] = [...createChatSystemMessages(repoRoot)];

  const ask = (): void => {
    rl.question(chalk.green("local> "), async (input) => {
      if (input.trim().toLowerCase() === "/exit") {
        rl.close();
        const stopped = await stopManagedServerOnExit();
        if (!stopped) {
          await stopIfIdle(config.idleTimeoutMinutes);
        }
        saveSession("chat", "chat-session", messages);
        return;
      }
      messages.push({ role: "user", content: input });
      process.stdout.write(chalk.cyan("assistant> "));
      const full = await runToolAwareCompletion(baseUrl, messages, repoRoot);
      process.stdout.write(full + "\n");
      messages.push({ role: "assistant", content: full });
      ask();
    });
  };

  console.log(chalk.gray("Type /exit to quit"));
  ask();
}

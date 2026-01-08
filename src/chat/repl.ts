import readline from "readline";
import chalk from "chalk";
import { loadConfig } from "../config/index.js";
import { ensureServer, getServerBaseUrl, stopIfIdle } from "../server/manager.js";
import { streamChatCompletion, ChatMessage } from "../server/llmClient.js";
import { getDefaultModel } from "../models/registry.js";
import { saveSession } from "../utils/sessions.js";

export async function runChatRepl(modelPath?: string): Promise<void> {
  const config = loadConfig();
  const model = modelPath ? { localPath: modelPath } : getDefaultModel();
  if (!model) throw new Error("No model installed. Use `local model install`.");

  const state = await ensureServer(config, model.localPath);
  const baseUrl = getServerBaseUrl(state.port);
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const messages: ChatMessage[] = [{ role: "system", content: "You are a helpful assistant." }];

  const ask = (): void => {
    rl.question(chalk.green("local> "), async (input) => {
      if (input.trim().toLowerCase() === "/exit") {
        rl.close();
        await stopIfIdle(config.idleTimeoutMinutes);
        saveSession("chat", "chat-session", messages);
        return;
      }
      messages.push({ role: "user", content: input });
      process.stdout.write(chalk.cyan("assistant> "));
      const full = await streamChatCompletion(baseUrl, messages, (token) => process.stdout.write(token));
      process.stdout.write("\n");
      messages.push({ role: "assistant", content: full });
      ask();
    });
  };

  console.log(chalk.gray("Type /exit to quit"));
  ask();
}

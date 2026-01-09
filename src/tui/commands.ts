import { loadRegistry, getDefaultModel } from "../models/registry.js";
import { loadConfig } from "../config/index.js";
import { loadTasks } from "../tasks/storage.js";

/**
 * Handle slash commands
 */
export async function handleSlashCommand(
  command: string,
  serverUrl: string,
  modelPath: string
): Promise<string> {
  const parts = command.slice(1).split(/\s+/);
  const cmd = parts[0].toLowerCase();
  const args = parts.slice(1);

  switch (cmd) {
    case "help":
      return `Available commands:
/help - Show this help message
/clear - Clear chat history
/model [list|info] - Show model information
/config - Show configuration
/tasks - List scheduled tasks
/code <prompt> - Run code agent
/server - Show server status
/exit - Exit the application`;

    case "clear":
      return "Chat cleared";

    case "model":
      const subCmd = args[0] || "info";
      if (subCmd === "list") {
        const registry = loadRegistry();
        if (registry.models.length === 0) {
          return "No models installed";
        }
        return `Installed models:\n${registry.models.map((m, i) => `${i + 1}. ${m.id} (${m.filename})`).join("\n")}`;
      } else {
        const model = getDefaultModel();
        if (!model) {
          return "No model configured";
        }
        return `Current model: ${model.id}\nFile: ${model.filename}\nPath: ${model.localPath}`;
      }

    case "config":
      const config = loadConfig();
      return `Configuration:
Server Port: ${config.serverPort}
Context Size: ${config.ctxSize}
GPU Layers: ${config.gpuLayers}
Idle Timeout: ${config.idleTimeoutMinutes} minutes
Default Model: ${config.defaultModelId || "none"}`;

    case "tasks":
      const tasks = loadTasks();
      if (tasks.tasks.length === 0) {
        return "No tasks configured";
      }
      return `Scheduled tasks:\n${tasks.tasks.map((t, i) => `${i + 1}. ${t.name} (${t.type})`).join("\n")}`;

    case "server":
      return `Server URL: ${serverUrl}\nModel: ${modelPath}`;

    case "code":
      if (args.length === 0) {
        return "Usage: /code <prompt>";
      }
      return "Code agent will be implemented in the full version";

    case "exit":
    case "quit":
      process.exit(0);

    default:
      return `Unknown command: ${cmd}\nType /help for available commands`;
  }
}

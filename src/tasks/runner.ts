import { loadConfig } from "../config/index.js";
import { getDefaultModel, loadRegistry } from "../models/registry.js";
import { ensureServer, getServerBaseUrl } from "../server/manager.js";
import { chatCompletion } from "../server/llmClient.js";
import { TaskDefinition, updateTask } from "./storage.js";
import { saveSession } from "../utils/sessions.js";
import { runCodeAgent } from "../agent/engine.js";

export async function runTask(task: TaskDefinition): Promise<void> {
  const config = loadConfig();
  const registry = loadRegistry();
  const model = task.modelId
    ? registry.models.find((m) => m.id === task.modelId) ?? getDefaultModel()
    : getDefaultModel();

  if (!model) throw new Error("No model installed. Use `local model install`.");

  try {
    if (task.type === "chat") {
      const state = await ensureServer(config, model.localPath);
      const baseUrl = getServerBaseUrl(state.port);
      const reply = await chatCompletion(baseUrl, [
        { role: "system", content: "You are a helpful assistant." },
        { role: "user", content: task.prompt }
      ]);
      task.runs.push({
        id: cryptoRandomId(),
        ts: new Date().toISOString(),
        status: "success",
        output: reply
      });
      task.lastRun = new Date().toISOString();
      updateTask(task);
      saveSession("chat", task.name, [{ role: "user", content: task.prompt }, { role: "assistant", content: reply }]);
      return;
    }

    if (task.type === "code") {
      await runCodeAgent({
        prompt: task.prompt,
        repoPath: task.repoPath ?? process.cwd(),
        modelPath: model.localPath
      });
      task.runs.push({
        id: cryptoRandomId(),
        ts: new Date().toISOString(),
        status: "success",
        output: "code session complete"
      });
      task.lastRun = new Date().toISOString();
      updateTask(task);
    }
  } catch (err) {
    task.runs.push({
      id: cryptoRandomId(),
      ts: new Date().toISOString(),
      status: "error",
      output: String(err)
    });
    task.lastRun = new Date().toISOString();
    updateTask(task);
    throw err;
  }
}

export async function tickTasks(): Promise<TaskDefinition[]> {
  const store = await import("./storage.js").then((m) => m.loadTasks());
  const due: TaskDefinition[] = [];
  const now = Date.now();
  for (const task of store.tasks) {
    if (!task.schedule) continue;
    if (task.schedule.type === "interval") {
      const last = task.lastRun ? Date.parse(task.lastRun) : 0;
      if (now - last >= task.schedule.minutes * 60 * 1000) {
        due.push(task);
      }
    }
  }
  return due;
}

function cryptoRandomId(): string {
  return Math.random().toString(36).slice(2, 10);
}

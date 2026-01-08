import inquirer from "inquirer";
import chalk from "chalk";
import { getDefaultModel } from "../models/registry.js";
import { runChatRepl } from "../chat/repl.js";
import { runCodeAgent } from "../agent/engine.js";
import { runTask } from "../tasks/runner.js";
import { loadTasks } from "../tasks/storage.js";
import { getStatus } from "../server/manager.js";
import { modelList } from "../models/commands.js";

export async function runMainReplMenu(options?: { repoPath?: string; dryRun?: boolean }): Promise<void> {
  const repoPath = options?.repoPath ?? process.cwd();
  const dryRun = options?.dryRun ?? false;

  const answer = (await inquirer.prompt([
    {
      type: "list",
      name: "action",
      message: "What do you want to do?",
      choices: [
        { name: "Chat (REPL)", value: "chat" },
        { name: "Code (agentic REPL)", value: "code" },
        { name: "Task runner", value: "task" },
        { name: "Model manager", value: "model" },
        { name: "Server status", value: "server" },
        { name: "Exit", value: "exit" }
      ]
    }
  ])) as { action: string };

  if (answer.action === "exit") return;

  if (answer.action === "chat") {
    const model = getDefaultModel();
    if (!model) {
      printModelHelp();
      return;
    }
    await runChatRepl(model.localPath);
    return;
  }

  if (answer.action === "code") {
    const model = getDefaultModel();
    if (!model) {
      printModelHelp();
      return;
    }
    const promptAnswer = (await inquirer.prompt([
      { type: "input", name: "prompt", message: "What should I do?" }
    ])) as { prompt: string };
    await runCodeAgent({ prompt: promptAnswer.prompt, repoPath, modelPath: model.localPath, dryRun });
    return;
  }

  if (answer.action === "task") {
    const store = loadTasks();
    if (store.tasks.length === 0) {
      console.log("No tasks. Use `local task create`.");
      return;
    }
    const taskPick = (await inquirer.prompt([
      {
        type: "list",
        name: "taskId",
        message: "Select a task to run",
        choices: store.tasks.map((t) => ({ name: `${t.name} [${t.type}]`, value: t.id }))
      }
    ])) as { taskId: string };
    const task = store.tasks.find((t) => t.id === taskPick.taskId);
    if (!task) {
      console.log("Task not found.");
      return;
    }
    await runTask(task);
    return;
  }

  if (answer.action === "model") {
    await modelList();
    console.log("Use `local model search <query>` and `local model install <repo_id>`. ");
    return;
  }

  if (answer.action === "server") {
    const status = await getStatus();
    if (!status.running) {
      console.log("llama-server: not running");
      return;
    }
    console.log(`llama-server: running on port ${status.state?.port}`);
    if (status.state?.modelPath) {
      console.log(`model: ${status.state.modelPath}`);
    }
  }
}

function printModelHelp(): void {
  console.log(chalk.yellow("No default model set."));
  console.log("Next steps:");
  console.log("  local model search <query>");
  console.log("  local model install <repo_id>");
  console.log("  local model set-default <id>");
}

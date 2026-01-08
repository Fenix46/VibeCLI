import { Command } from "commander";
import chalk from "chalk";
import path from "path";
import inquirer from "inquirer";
import { ensureAppDirs } from "./config/dirs.js";
import { loadConfig } from "./config/index.js";
import { modelSearch, modelInstall, modelList, modelRemove, modelSetDefault } from "./models/commands.js";
import { loadRegistry, getDefaultModel } from "./models/registry.js";
import { runChatRepl } from "./chat/repl.js";
import { runCodeAgent } from "./agent/engine.js";
import { runDoctor } from "./utils/doctor.js";
import { getStatus, startServer, stopServer, readState } from "./server/manager.js";
import { getLogsDir } from "./config/dirs.js";
import { addTask, loadTasks, removeTask } from "./tasks/storage.js";
import { runTask, tickTasks } from "./tasks/runner.js";
import { runMainReplMenu } from "./repl/menu.js";

ensureAppDirs();

const program = new Command();
program.showHelpAfterError();
program.showSuggestionAfterError();
program.name("local").description("Local coding assistant CLI").version("0.1.0");

const argv = process.argv.slice(2);
const wantsHelp = argv.includes("-h") || argv.includes("--help");
const wantsVersion = argv.includes("-V") || argv.includes("--version");
const noArgs = argv.length === 0;

program.action(async () => {
  if (noArgs && !wantsHelp && !wantsVersion) {
    await runMainReplMenu({ repoPath: process.cwd() });
  }
});

program
  .command("repl")
  .description("Open the interactive main menu")
  .action(async () => {
    await runMainReplMenu({ repoPath: process.cwd() });
  });

program
  .command("chat")
  .description("Interactive chat REPL")
  .option("-m, --model <id>", "model id")
  .action(async (opts) => {
    const registry = loadRegistry();
    const model = opts.model ? registry.models.find((m) => m.id === opts.model) : getDefaultModel();
    if (!model) throw new Error("Model not found.");
    await runChatRepl(model.localPath);
  });

program
  .command("code")
  .description("Agentic coding REPL in current repo")
  .option("-r, --repo <path>", "repo path")
  .option("-m, --model <id>", "model id")
  .option("--dry-run", "show diffs and commands without applying", false)
  .argument("[prompt]", "task prompt")
  .action(async (promptArg, opts) => {
    const prompt =
      promptArg ??
      ((await inquirer.prompt([
        { type: "input", name: "prompt", message: "What should I do?" }
      ])) as { prompt: string }).prompt;
    const registry = loadRegistry();
    const model = opts.model ? registry.models.find((m) => m.id === opts.model) : getDefaultModel();
    if (!model) throw new Error("Model not found.");
    const repoPath = opts.repo ? path.resolve(opts.repo) : process.cwd();
    await runCodeAgent({ prompt, repoPath, modelPath: model.localPath, dryRun: opts.dryRun });
  });

const modelCmd = program.command("model").description("Manage models");
modelCmd.command("search <query>").action(modelSearch);
modelCmd.command("install <repoId>").option("--file <gguf>").action((repoId, opts) => modelInstall(repoId, opts.file));
modelCmd.command("list").action(modelList);
modelCmd.command("remove <id>").action(modelRemove);
modelCmd.command("set-default <id>").action(modelSetDefault);

const serverCmd = program.command("server").description("Manage llama-server");
serverCmd
  .command("start")
  .option("-m, --model <id>", "model id")
  .action(async (opts) => {
    const config = loadConfig();
    const registry = loadRegistry();
    const model = opts.model ? registry.models.find((m) => m.id === opts.model) : getDefaultModel();
    if (!model) throw new Error("Model not found.");
    const status = await getStatus();
    if (status.running) {
      console.log(`llama-server already running on port ${status.state?.port}`);
      return;
    }
    const state = await startServer(config, model.localPath);
    console.log(chalk.green(`Started llama-server on port ${state.port}`));
  });
serverCmd.command("stop").action(async () => {
  await stopServer();
  console.log("Stopped llama-server");
});
serverCmd.command("status").action(async () => {
  const status = await getStatus();
  if (!status.running) {
    console.log("llama-server: not running");
    return;
  }
  console.log(`llama-server: running on port ${status.state?.port}`);
  if (status.state?.modelPath) {
    console.log(`model: ${status.state.modelPath}`);
  }
});
serverCmd.command("logs").action(() => {
  const state = readState();
  if (!state) {
    console.log("No server logs yet.");
    return;
  }
  console.log("Logs at", path.join(getLogsDir(), "llama-server.log"));
});

const taskCmd = program.command("task").description("Task system");

taskCmd.command("list").action(() => {
  const store = loadTasks();
  if (store.tasks.length === 0) {
    console.log("No tasks.");
    return;
  }
  store.tasks.forEach((task) => {
    console.log(`${task.id} ${task.name} [${task.type}]`);
  });
});

taskCmd.command("create").action(async () => {
  const registry = loadRegistry();
  const modelChoices = [{ name: "default", value: "" }, ...registry.models.map((m) => ({ name: m.id, value: m.id }))];
  const answers = (await inquirer.prompt([
    { type: "input", name: "name", message: "Task name" },
    { type: "input", name: "description", message: "Description" },
    { type: "list", name: "type", message: "Task type", choices: ["chat", "code"] },
    { type: "input", name: "repoPath", message: "Repo path (optional)", default: process.cwd() },
    { type: "input", name: "prompt", message: "Prompt" },
    { type: "list", name: "modelId", message: "Model override", choices: modelChoices },
    { type: "confirm", name: "schedule", message: "Schedule interval?", default: false },
    {
      type: "input",
      name: "interval",
      message: "Interval minutes",
      when: (a: { schedule: boolean }) => a.schedule,
      default: 60,
      filter: (input: string) => Number(input)
    }
  ])) as {
    name: string;
    description: string;
    type: "chat" | "code";
    repoPath: string;
    prompt: string;
    modelId: string;
    schedule: boolean;
    interval: number;
  };

  addTask({
    id: Math.random().toString(36).slice(2, 10),
    name: answers.name,
    description: answers.description,
    type: answers.type,
    repoPath: answers.type === "code" ? answers.repoPath : undefined,
    prompt: answers.prompt,
    modelId: answers.modelId || undefined,
    createdAt: new Date().toISOString(),
    schedule: answers.schedule ? { type: "interval", minutes: answers.interval } : undefined,
    runs: []
  });

  console.log(chalk.green("Task created"));
});

taskCmd.command("run <id>").action(async (id) => {
  const store = loadTasks();
  const task = store.tasks.find((t) => t.id === id);
  if (!task) throw new Error("Task not found");
  await runTask(task);
});

taskCmd.command("delete <id>").action((id) => {
  const removed = removeTask(id);
  if (!removed) {
    console.log("Task not found");
    return;
  }
  console.log(chalk.green("Task deleted"));
});

taskCmd.command("tick").action(async () => {
  const due = await tickTasks();
  for (const task of due) {
    await runTask(task);
  }
  console.log(`Ran ${due.length} due tasks.`);
});

program.command("doctor").description("Diagnostics").action(runDoctor);

program.parseAsync(process.argv).catch((err) => {
  console.error(chalk.red(String(err)));
  process.exit(1);
});

import fs from "fs-extra";
import path from "path";
import { ensureAppDirs, getConfigDir } from "../config/dirs.js";
import { writeJsonWithBackupSync } from "../utils/fs.js";

export type TaskType = "chat" | "code";

export type TaskSchedule = {
  type: "interval";
  minutes: number;
};

export type TaskRun = {
  id: string;
  ts: string;
  status: "success" | "error";
  output?: string;
};

export type TaskDefinition = {
  id: string;
  name: string;
  description?: string;
  type: TaskType;
  repoPath?: string;
  prompt: string;
  modelId?: string;
  schedule?: TaskSchedule;
  createdAt: string;
  lastRun?: string;
  runs: TaskRun[];
};

export type TaskStore = {
  tasks: TaskDefinition[];
};

const TASKS_FILE = "tasks.json";

export function getTasksPath(): string {
  return path.join(getConfigDir(), TASKS_FILE);
}

export function loadTasks(): TaskStore {
  ensureAppDirs();
  const file = getTasksPath();
  if (!fs.existsSync(file)) {
    const data: TaskStore = { tasks: [] };
    fs.writeJsonSync(file, data, { spaces: 2 });
    return data;
  }
  return fs.readJsonSync(file) as TaskStore;
}

export function saveTasks(store: TaskStore): void {
  ensureAppDirs();
  writeJsonWithBackupSync(getTasksPath(), store);
}

export function addTask(task: TaskDefinition): void {
  const store = loadTasks();
  store.tasks.push(task);
  saveTasks(store);
}

export function removeTask(id: string): TaskDefinition | null {
  const store = loadTasks();
  const index = store.tasks.findIndex((t) => t.id === id);
  if (index === -1) return null;
  const [task] = store.tasks.splice(index, 1);
  saveTasks(store);
  return task;
}

export function updateTask(task: TaskDefinition): void {
  const store = loadTasks();
  const index = store.tasks.findIndex((t) => t.id === task.id);
  if (index === -1) throw new Error("Task not found");
  store.tasks[index] = task;
  saveTasks(store);
}

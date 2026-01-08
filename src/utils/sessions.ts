import fs from "fs-extra";
import path from "path";
import { getSessionsDir } from "../config/dirs.js";

export type SessionMessage = { role: string; content: string };

export function saveSession(type: "chat" | "code", title: string, messages: SessionMessage[]): string {
  const dir = getSessionsDir();
  fs.ensureDirSync(dir);
  const fileName = `${type}-${Date.now()}-${sanitize(title)}.json`;
  const filePath = path.join(dir, fileName);
  fs.writeJsonSync(filePath, { title, type, messages }, { spaces: 2 });
  return filePath;
}

function sanitize(input: string): string {
  return input.replace(/[^a-zA-Z0-9._-]+/g, "_").slice(0, 40);
}

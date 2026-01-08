import { fetch } from "undici";
import { markServerUsed } from "./manager.js";

export type ChatMessage = { role: "system" | "user" | "assistant"; content: string };

export async function streamChatCompletion(
  baseUrl: string,
  messages: ChatMessage[],
  onToken: (token: string) => void
): Promise<string> {
  const res = await fetch(`${baseUrl}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: "local", messages, stream: true })
  });
  if (!res.ok || !res.body) {
    throw new Error(`LLM call failed: ${res.status}`);
  }
  const reader = res.body.getReader();
  let buffer = "";
  let full = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += new TextDecoder().decode(value);
    const parts = buffer.split("\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const data = line.replace(/^data:\s*/, "");
      if (data === "[DONE]") break;
      try {
        const json = JSON.parse(data) as { choices?: Array<{ delta?: { content?: string } }> };
        const token = json.choices?.[0]?.delta?.content;
        if (token) {
          full += token;
          onToken(token);
        }
      } catch {
        // ignore
      }
    }
  }
  markServerUsed();
  return full;
}

export async function chatCompletion(baseUrl: string, messages: ChatMessage[]): Promise<string> {
  const res = await fetch(`${baseUrl}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: "local", messages })
  });
  if (!res.ok) throw new Error(`LLM call failed: ${res.status}`);
  const data = (await res.json()) as { choices?: Array<{ message?: { content?: string } }> };
  const content = data.choices?.[0]?.message?.content ?? "";
  markServerUsed();
  return content;
}

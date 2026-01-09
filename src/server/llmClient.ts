import { fetch } from "undici";
import { markServerUsed } from "./manager.js";

export type ChatMessage = { role: "system" | "user" | "assistant"; content: string };

const DEFAULT_TIMEOUT_MS = 120000; // 2 minutes
const STREAM_READ_TIMEOUT_MS = 30000; // 30 seconds per chunk

/**
 * Create an AbortSignal that times out after specified ms
 */
function createTimeoutSignal(timeoutMs: number): AbortSignal {
  const controller = new AbortController();
  setTimeout(() => controller.abort(), timeoutMs);
  return controller.signal;
}

export async function streamChatCompletion(
  baseUrl: string,
  messages: ChatMessage[],
  onToken: (token: string) => void,
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<string> {
  const signal = createTimeoutSignal(timeoutMs);

  const res = await fetch(`${baseUrl}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: "local", messages, stream: true }),
    signal
  });

  if (!res.ok || !res.body) {
    throw new Error(`LLM call failed: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder(); // Reuse decoder
  let buffer = "";
  let full = "";
  let lastChunkTime = Date.now();

  while (true) {
    // Check for read timeout
    if (Date.now() - lastChunkTime > STREAM_READ_TIMEOUT_MS) {
      reader.cancel();
      throw new Error("Stream read timeout: no data received in 30 seconds");
    }

    const { value, done } = await reader.read();
    if (done) break;

    lastChunkTime = Date.now();
    buffer += decoder.decode(value, { stream: true });
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
        // ignore malformed JSON chunks
      }
    }
  }

  markServerUsed();
  return full;
}

export async function chatCompletion(
  baseUrl: string,
  messages: ChatMessage[],
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<string> {
  const signal = createTimeoutSignal(timeoutMs);

  const res = await fetch(`${baseUrl}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: "local", messages }),
    signal
  });

  if (!res.ok) throw new Error(`LLM call failed: ${res.status}`);

  const data = (await res.json()) as { choices?: Array<{ message?: { content?: string } }> };
  const content = data.choices?.[0]?.message?.content ?? "";
  markServerUsed();
  return content;
}

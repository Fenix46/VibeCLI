import React, { useState } from "react";
import { Box, Text, useInput } from "ink";
import TextInput from "ink-text-input";
import { ChatMessage } from "../../server/llmClient.js";
import { handleSlashCommand } from "../commands.js";
import { createChatSystemMessages, runToolAwareCompletion } from "../../chat/tooling.js";

type Message = {
  role: "user" | "assistant" | "system";
  content: string;
};

type Props = {
  serverUrl: string;
  modelPath: string;
  onBack: () => void;
};

export function ChatView({ serverUrl, modelPath, onBack }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [llmMessages, setLlmMessages] = useState<ChatMessage[]>(
    () => createChatSystemMessages(process.cwd())
  );
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [showHelp, setShowHelp] = useState(true);

  useInput((input, key) => {
    if (key.escape) {
      onBack();
    }
  });

  const handleSubmit = async () => {
    if (!input.trim() || isStreaming) return;

    const userInput = input.trim();
    setInput("");
    setShowHelp(false);

    // Check for slash commands
    if (userInput.startsWith("/")) {
      if (userInput === "/clear") {
        setMessages([]);
        setLlmMessages(createChatSystemMessages(process.cwd()));
        return;
      }

      const result = await handleSlashCommand(userInput, serverUrl, modelPath);
      setMessages((prev) => [
        ...prev,
        { role: "user", content: userInput },
        { role: "system", content: result }
      ]);
      return;
    }

    // Add user message
    const userMessage: Message = { role: "user", content: userInput };
    setMessages((prev) => [...prev, userMessage]);

    // Tool-aware response (non-streaming)
    setIsStreaming(true);

    try {
      const nextLlmMessages = [...llmMessages, { role: "user", content: userInput }];
      const fullResponse = await runToolAwareCompletion(serverUrl, nextLlmMessages, process.cwd());
      nextLlmMessages.push({ role: "assistant", content: fullResponse });
      setLlmMessages(nextLlmMessages);
      setMessages((prev) => [...prev, { role: "assistant", content: fullResponse }]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "system", content: `Error: ${err.message}` }
      ]);
    } finally {
      setIsStreaming(false);
    }
  };

  const modelName = modelPath.split(/[\\/]/).pop() || "unknown";

  return (
    <Box flexDirection="column" paddingX={2} height="100%">
      {/* Messages area */}
      <Box flexDirection="column" flexGrow={1} marginBottom={1}>
        {showHelp && messages.length === 0 && (
          <Box flexDirection="column" paddingY={1}>
            <Text dimColor>💬 Chat with {modelName}</Text>
            <Text dimColor></Text>
            <Text dimColor>Slash commands:</Text>
            <Text dimColor> /help - Show commands</Text>
            <Text dimColor> /clear - Clear history</Text>
            <Text dimColor> /model - Model info</Text>
            <Text dimColor></Text>
            <Text dimColor>Press ESC to return to menu</Text>
          </Box>
        )}

        {messages.map((msg, idx) => (
          <Box key={idx} flexDirection="column" marginBottom={1}>
            <Text
              bold
              color={
                msg.role === "user"
                  ? "cyan"
                  : msg.role === "assistant"
                  ? "green"
                  : "yellow"
              }
            >
              {msg.role === "user" ? "You" : msg.role === "assistant" ? "Assistant" : "System"}:
            </Text>
            <Text>{msg.content}</Text>
          </Box>
        ))}

        {isStreaming && (
          <Box flexDirection="column" marginBottom={1}>
            <Text bold color="green">
              Assistant:
            </Text>
            <Text dimColor>Thinking...</Text>
          </Box>
        )}
      </Box>

      {/* Input area */}
      <Box borderStyle="single" borderColor={isStreaming ? "yellow" : "cyan"} paddingX={1}>
        <Text dimColor>{">"} </Text>
        <TextInput
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          placeholder={isStreaming ? "Waiting for response..." : "Type a message..."}
          showCursor={!isStreaming}
        />
      </Box>
    </Box>
  );
}

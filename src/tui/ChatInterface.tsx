import React, { useState, useEffect, useRef } from "react";
import { Box, Text, useInput } from "ink";
import TextInput from "ink-text-input";
import { ChatMessage, streamChatCompletion } from "../server/llmClient.js";
import { handleSlashCommand } from "./commands.js";

type Message = {
  role: "user" | "assistant" | "system";
  content: string;
};

type Props = {
  serverUrl: string;
  modelPath: string;
};

export function ChatInterface({ serverUrl, modelPath }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentResponse, setCurrentResponse] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useInput((input, key) => {
    if (key.ctrl && input === "l") {
      // Clear chat
      setMessages([]);
      setCurrentResponse("");
    }
  });

  const handleSubmit = async () => {
    if (!input.trim()) return;

    const userInput = input.trim();
    setInput("");

    // Check for slash commands
    if (userInput.startsWith("/")) {
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

    // Stream AI response
    setIsStreaming(true);
    setCurrentResponse("");

    try {
      const chatMessages: ChatMessage[] = [
        ...messages.map((m) => ({ role: m.role as any, content: m.content })),
        { role: "user", content: userInput }
      ];

      await streamChatCompletion(
        serverUrl,
        chatMessages,
        (token) => {
          setCurrentResponse((prev) => prev + token);
        }
      );

      // Save final response
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: currentResponse }
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "system", content: `Error: ${err.message}` }
      ]);
    } finally {
      setIsStreaming(false);
      setCurrentResponse("");
    }
  };

  return (
    <Box flexDirection="column" flexGrow={1} paddingX={2}>
      {/* Messages area */}
      <Box flexDirection="column" flexGrow={1} marginBottom={1}>
        {messages.length === 0 && (
          <Box flexDirection="column" paddingY={2}>
            <Text dimColor>Welcome to Local CLI!</Text>
            <Text dimColor>Type a message or use slash commands:</Text>
            <Text dimColor> /help - Show available commands</Text>
            <Text dimColor> /clear - Clear chat history</Text>
            <Text dimColor> /model - Change model</Text>
            <Text dimColor> /code - Run code agent</Text>
            <Text dimColor></Text>
            <Text dimColor>Press Ctrl+L to clear, Ctrl+Q to quit</Text>
          </Box>
        )}

        {messages.map((msg, idx) => (
          <Box key={idx} flexDirection="column" marginBottom={1}>
            <Text bold color={msg.role === "user" ? "cyan" : msg.role === "assistant" ? "green" : "yellow"}>
              {msg.role === "user" ? "You" : msg.role === "assistant" ? "Assistant" : "System"}:
            </Text>
            <Text>{msg.content}</Text>
          </Box>
        ))}

        {isStreaming && currentResponse && (
          <Box flexDirection="column" marginBottom={1}>
            <Text bold color="green">
              Assistant:
            </Text>
            <Text>{currentResponse}</Text>
            <Text dimColor>▊</Text>
          </Box>
        )}
      </Box>

      {/* Input area */}
      <Box borderStyle="single" borderColor="gray" paddingX={1}>
        <Text dimColor>{">"} </Text>
        <TextInput
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          placeholder="Type a message..."
        />
      </Box>
    </Box>
  );
}

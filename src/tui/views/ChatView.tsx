import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import TextInput from "ink-text-input";
import { ChatMessage, streamChatCompletion } from "../../server/llmClient.js";
import { handleSlashCommand } from "../commands.js";

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
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentResponse, setCurrentResponse] = useState("");
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
        setCurrentResponse("");
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
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);

    // Stream AI response
    setIsStreaming(true);
    setCurrentResponse("");

    try {
      const chatMessages: ChatMessage[] = newMessages.map((m) => ({
        role: m.role as any,
        content: m.content
      }));

      let fullResponse = "";
      await streamChatCompletion(
        serverUrl,
        chatMessages,
        (token) => {
          fullResponse += token;
          setCurrentResponse(fullResponse);
        }
      );

      // Save final response
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: fullResponse }
      ]);
      setCurrentResponse("");
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

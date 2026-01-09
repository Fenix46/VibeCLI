import React, { useState } from "react";
import { Box, Text, useInput } from "ink";
import TextInput from "ink-text-input";

type Props = {
  onClose: () => void;
  onCommand: (command: string) => void;
};

export function CommandPalette({ onClose, onCommand }: Props) {
  const [input, setInput] = useState("");

  useInput((_, key) => {
    if (key.escape) {
      onClose();
    }
  });

  const handleSubmit = () => {
    if (input.trim()) {
      onCommand(input.trim());
    } else {
      onClose();
    }
  };

  const commands = [
    "/help - Show available commands",
    "/clear - Clear chat history",
    "/model - Show model info",
    "/config - Show configuration",
    "/tasks - List tasks",
    "/code <prompt> - Run code agent",
    "/server - Server status",
    "/exit - Exit application"
  ];

  return (
    <Box flexDirection="column" padding={2} borderStyle="double" borderColor="cyan">
      <Box marginBottom={1}>
        <Text bold color="cyan">
          Command Palette
        </Text>
      </Box>

      <Box flexDirection="column" marginBottom={1}>
        {commands.map((cmd, idx) => (
          <Text key={idx} dimColor>
            {cmd}
          </Text>
        ))}
      </Box>

      <Box borderStyle="single" borderColor="cyan" paddingX={1}>
        <Text color="cyan">{">"} </Text>
        <TextInput
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          placeholder="Type a command..."
          focus={true}
        />
      </Box>

      <Box marginTop={1}>
        <Text dimColor>Press ESC to close</Text>
      </Box>
    </Box>
  );
}

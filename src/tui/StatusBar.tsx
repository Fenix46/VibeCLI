import React from "react";
import { Box, Text } from "ink";

type Props = {
  status: string;
  modelPath: string;
  serverUrl: string;
};

export function StatusBar({ status, modelPath, serverUrl }: Props) {
  const modelName = modelPath ? modelPath.split(/[\\/]/).pop() || "unknown" : "no model";

  return (
    <Box borderStyle="single" borderColor="gray" paddingX={1}>
      <Box flexGrow={1}>
        <Text dimColor>Status: </Text>
        <Text color={status === "ready" ? "green" : "yellow"}>{status}</Text>
      </Box>
      <Box marginLeft={2}>
        <Text dimColor>Model: </Text>
        <Text>{modelName}</Text>
      </Box>
      <Box marginLeft={2}>
        <Text dimColor>Press </Text>
        <Text bold>Ctrl+Q</Text>
        <Text dimColor> to quit</Text>
      </Box>
    </Box>
  );
}

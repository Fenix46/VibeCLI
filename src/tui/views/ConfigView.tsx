import React from "react";
import { Box, Text, useInput } from "ink";
import { loadConfig } from "../../config/index.js";
import { getDefaultModel } from "../../models/registry.js";

type Props = {
  onBack: () => void;
};

export function ConfigView({ onBack }: Props) {
  const config = loadConfig();
  const defaultModel = getDefaultModel();

  useInput((input, key) => {
    if (key.escape || input === "b") {
      onBack();
    }
  });

  return (
    <Box flexDirection="column" paddingX={2} paddingY={1}>
      <Box marginBottom={1}>
        <Text bold>Configuration</Text>
      </Box>

      <Box flexDirection="column" marginBottom={1}>
        <Box>
          <Text bold color="cyan">Default Model: </Text>
          <Text>{defaultModel?.id || "none"}</Text>
        </Box>

        <Box marginTop={1}>
          <Text bold color="cyan">Server Port: </Text>
          <Text>{config.serverPort}</Text>
        </Box>

        <Box>
          <Text bold color="cyan">Context Size: </Text>
          <Text>{config.ctxSize} tokens</Text>
        </Box>

        <Box>
          <Text bold color="cyan">GPU Layers: </Text>
          <Text>{config.gpuLayers}</Text>
        </Box>

        <Box>
          <Text bold color="cyan">Idle Timeout: </Text>
          <Text>{config.idleTimeoutMinutes} minutes</Text>
        </Box>

        {config.llamaServerPath && (
          <Box>
            <Text bold color="cyan">llama-server Path: </Text>
            <Text>{config.llamaServerPath}</Text>
          </Box>
        )}
      </Box>

      <Box marginTop={2}>
        <Text dimColor>Press ESC to go back</Text>
      </Box>

      <Box marginTop={1}>
        <Text dimColor>
          Tip: Edit config file directly:
        </Text>
        <Text dimColor>  {process.platform === "win32" ? "%APPDATA%" : "~"}/.../config.json</Text>
      </Box>
    </Box>
  );
}

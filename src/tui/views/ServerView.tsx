import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import { getStatus, readState } from "../../server/manager.js";
import { loadConfig } from "../../config/index.js";
import fs from "fs-extra";
import path from "path";
import { getLogsDir } from "../../config/dirs.js";

type Props = {
  onBack: () => void;
};

export function ServerView({ onBack }: Props) {
  const [serverStatus, setServerStatus] = useState<any>(null);
  const [serverState, setServerState] = useState<any>(null);
  const [logTail, setLogTail] = useState<string[]>([]);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    const status = await getStatus();
    setServerStatus(status);

    if (status.state) {
      setServerState(status.state);
    }

    // Read last 10 lines of log
    try {
      const logPath = path.join(getLogsDir(), "llama-server.log");
      if (await fs.pathExists(logPath)) {
        const content = await fs.readFile(logPath, "utf8");
        const lines = content.split("\n").filter((l) => l.trim());
        setLogTail(lines.slice(-10));
      }
    } catch {
      // Ignore log read errors
    }
  };

  useInput((input, key) => {
    if (key.escape || input === "b") {
      onBack();
    }
  });

  return (
    <Box flexDirection="column" paddingX={2} paddingY={1}>
      <Box marginBottom={1}>
        <Text bold>Server Status</Text>
      </Box>

      <Box flexDirection="column" marginBottom={1}>
        <Box>
          <Text bold color="cyan">Status: </Text>
          <Text color={serverStatus?.running ? "green" : "red"}>
            {serverStatus?.running ? "🟢 Running" : "🔴 Stopped"}
          </Text>
        </Box>

        {serverState && (
          <>
            <Box>
              <Text bold color="cyan">PID: </Text>
              <Text>{serverState.pid}</Text>
            </Box>

            <Box>
              <Text bold color="cyan">Port: </Text>
              <Text>{serverState.port}</Text>
            </Box>

            <Box>
              <Text bold color="cyan">URL: </Text>
              <Text>http://127.0.0.1:{serverState.port}</Text>
            </Box>

            <Box>
              <Text bold color="cyan">Model: </Text>
              <Text>{serverState.modelPath.split(/[\\/]/).pop()}</Text>
            </Box>

            <Box>
              <Text bold color="cyan">Started: </Text>
              <Text>{new Date(serverState.startedAt).toLocaleString()}</Text>
            </Box>
          </>
        )}
      </Box>

      {logTail.length > 0 && (
        <>
          <Box marginTop={1} marginBottom={1}>
            <Text bold>Recent Logs (last 10 lines):</Text>
          </Box>
          <Box flexDirection="column" borderStyle="single" paddingX={1} paddingY={1}>
            {logTail.map((line, idx) => (
              <Text key={idx} dimColor>
                {line.substring(0, 120)}
              </Text>
            ))}
          </Box>
        </>
      )}

      <Box marginTop={2}>
        <Text dimColor>Press ESC to go back</Text>
      </Box>

      <Box marginTop={1}>
        <Text dimColor>Auto-refreshing every 2 seconds...</Text>
      </Box>
    </Box>
  );
}

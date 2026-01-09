import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import TextInput from "ink-text-input";
import fs from "fs-extra";
import path from "path";
import { getStatus, startServer, stopServer } from "../../server/manager.js";
import { loadConfig, saveConfig } from "../../config/index.js";
import { getLogsDir } from "../../config/dirs.js";
import { getDefaultModel, loadRegistry } from "../../models/registry.js";
import { AppConfig } from "../../config/schema.js";

type Props = {
  onBack: () => void;
};

type ViewMode = "status" | "model_select" | "config_select" | "config_edit";

type ConfigField = {
  key: keyof AppConfig;
  label: string;
  type: "number" | "string";
  optional?: boolean;
};

const CONFIG_FIELDS: ConfigField[] = [
  { key: "serverPort", label: "Server Port", type: "number" },
  { key: "ctxSize", label: "Context Size", type: "number" },
  { key: "gpuLayers", label: "GPU Layers", type: "number" },
  { key: "idleTimeoutMinutes", label: "Idle Timeout (minutes)", type: "number" },
  { key: "llamaServerPath", label: "llama-server Path", type: "string", optional: true }
];

export function ServerView({ onBack }: Props) {
  const [serverStatus, setServerStatus] = useState<any>(null);
  const [serverState, setServerState] = useState<any>(null);
  const [logTail, setLogTail] = useState<string[]>([]);
  const [mode, setMode] = useState<ViewMode>("status");
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [models, setModels] = useState<any[]>([]);
  const [config, setConfig] = useState<AppConfig>(loadConfig());
  const [editField, setEditField] = useState<ConfigField | null>(null);
  const [editValue, setEditValue] = useState("");

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
    } else {
      setServerState(null);
    }

    // Read last 10 lines of log
    try {
      const logPath = path.join(getLogsDir(), "llama-server.log");
      if (await fs.pathExists(logPath)) {
        const content = await fs.readFile(logPath, "utf8");
        const lines = content.split("\n").filter((l) => l.trim());
        setLogTail(lines.slice(-10));
      } else {
        setLogTail([]);
      }
    } catch {
      // Ignore log read errors
    }
  };

  const startWithModel = async (modelPath: string) => {
    try {
      setError("");
      setStatusMessage("Starting server...");
      const currentConfig = loadConfig();
      const state = await startServer(currentConfig, modelPath, {
        managed: true,
        ownerPid: process.pid
      });
      setStatusMessage(`Server started on port ${state.port}`);
      await loadStatus();
    } catch (err: any) {
      setError(`Failed to start server: ${err.message}`);
    } finally {
      setTimeout(() => setStatusMessage(""), 2000);
    }
  };

  const handleStartDefault = async () => {
    const model = getDefaultModel();
    if (!model) {
      setError("No default model configured.");
      return;
    }
    await startWithModel(model.localPath);
  };

  const handleStop = async () => {
    try {
      setError("");
      setStatusMessage("Stopping server...");
      await stopServer();
      setStatusMessage("Server stopped.");
      await loadStatus();
    } catch (err: any) {
      setError(`Failed to stop server: ${err.message}`);
    } finally {
      setTimeout(() => setStatusMessage(""), 2000);
    }
  };

  const openModelSelect = () => {
    const registry = loadRegistry();
    if (registry.models.length === 0) {
      setError("No models installed.");
      return;
    }
    setModels(registry.models);
    setSelectedIndex(0);
    setMode("model_select");
  };

  const openConfigSelect = () => {
    setConfig(loadConfig());
    setSelectedIndex(0);
    setMode("config_select");
  };

  const submitConfigEdit = () => {
    if (!editField) return;
    const updated = { ...config };
    if (editField.type === "number") {
      const value = Number(editValue.trim());
      if (!Number.isFinite(value)) {
        setError("Please enter a valid number.");
        return;
      }
      (updated as any)[editField.key] = Math.trunc(value);
    } else {
      const value = editValue.trim();
      if (!value && editField.optional) {
        (updated as any)[editField.key] = undefined;
      } else {
        (updated as any)[editField.key] = value;
      }
    }

    try {
      saveConfig(updated);
      setConfig(updated);
      setStatusMessage("Configuration saved.");
      setTimeout(() => setStatusMessage(""), 2000);
      setMode("config_select");
      setEditField(null);
      setEditValue("");
    } catch (err: any) {
      setError(`Invalid config: ${err.message}`);
    }
  };

  useInput(async (input, key) => {
    if (mode === "status") {
      if (key.escape || input === "b") {
        onBack();
        return;
      }
      if (input === "s") {
        if (serverStatus?.running) {
          await handleStop();
        } else {
          await handleStartDefault();
        }
      } else if (input === "r") {
        if (serverStatus?.running) {
          await handleStop();
        }
        await handleStartDefault();
      } else if (input === "m") {
        openModelSelect();
      } else if (input === "c") {
        openConfigSelect();
      }
      return;
    }

    if (mode === "model_select") {
      if (key.escape || input === "b") {
        setMode("status");
        return;
      }
      if (key.upArrow) {
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : models.length - 1));
      } else if (key.downArrow) {
        setSelectedIndex((prev) => (prev < models.length - 1 ? prev + 1 : 0));
      } else if (key.return && models.length > 0) {
        if (serverStatus?.running) {
          await handleStop();
        }
        await startWithModel(models[selectedIndex].localPath);
        setMode("status");
      }
      return;
    }

    if (mode === "config_select") {
      if (key.escape || input === "b") {
        setMode("status");
        return;
      }
      if (key.upArrow) {
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : CONFIG_FIELDS.length - 1));
      } else if (key.downArrow) {
        setSelectedIndex((prev) => (prev < CONFIG_FIELDS.length - 1 ? prev + 1 : 0));
      } else if (key.return) {
        const field = CONFIG_FIELDS[selectedIndex];
        const currentValue = config[field.key];
        setEditField(field);
        setEditValue(currentValue ? String(currentValue) : "");
        setMode("config_edit");
      }
      return;
    }

    if (mode === "config_edit") {
      if (key.escape) {
        setMode("config_select");
        setEditField(null);
        setEditValue("");
      }
    }
  });

  const renderStatus = () => (
    <>
      <Box flexDirection="column" marginBottom={1}>
        <Box>
          <Text bold color="cyan">Status: </Text>
          <Text color={serverStatus?.running ? "green" : "red"}>
            {serverStatus?.running ? "Running" : "Stopped"}
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

      <Box marginTop={2} flexDirection="column">
        <Text dimColor>[s] start/stop  [r] restart  [m] model  [c] config</Text>
        <Text dimColor>Press ESC to go back</Text>
      </Box>
    </>
  );

  const renderModelSelect = () => (
    <>
      <Box marginBottom={1}>
        <Text bold>Select Model</Text>
      </Box>
      <Box flexDirection="column">
        {models.map((model, idx) => {
          const isSelected = idx === selectedIndex;
          return (
            <Box key={model.id}>
              <Text
                bold={isSelected}
                color={isSelected ? "cyan" : undefined}
                backgroundColor={isSelected ? "blue" : undefined}
              >
                {isSelected ? "> " : "  "}
                {model.id}
              </Text>
            </Box>
          );
        })}
      </Box>
      <Box marginTop={1}>
        <Text dimColor>Up/Down to select, Enter to start, ESC to cancel</Text>
      </Box>
    </>
  );

  const renderConfigSelect = () => (
    <>
      <Box marginBottom={1}>
        <Text bold>Server Configuration</Text>
      </Box>
      <Box flexDirection="column">
        {CONFIG_FIELDS.map((field, idx) => {
          const isSelected = idx === selectedIndex;
          const value = config[field.key];
          return (
            <Box key={field.key}>
              <Text
                bold={isSelected}
                color={isSelected ? "cyan" : undefined}
                backgroundColor={isSelected ? "blue" : undefined}
              >
                {isSelected ? "> " : "  "}
                {field.label}: {value ?? "(unset)"}
              </Text>
            </Box>
          );
        })}
      </Box>
      <Box marginTop={1}>
        <Text dimColor>Up/Down to select, Enter to edit, ESC to cancel</Text>
      </Box>
    </>
  );

  const renderConfigEdit = () => (
    <>
      <Box marginBottom={1}>
        <Text bold>Edit {editField?.label}</Text>
      </Box>
      <Box borderStyle="single" paddingX={1}>
        <Text>{">"} </Text>
        <TextInput
          value={editValue}
          onChange={setEditValue}
          onSubmit={submitConfigEdit}
          placeholder={editField?.optional ? "Leave empty to unset" : ""}
        />
      </Box>
      <Box marginTop={1}>
        <Text dimColor>Press Enter to save, ESC to cancel</Text>
      </Box>
    </>
  );

  return (
    <Box flexDirection="column" paddingX={2} paddingY={1}>
      {statusMessage && (
        <Box marginBottom={1}>
          <Text color="green">{statusMessage}</Text>
        </Box>
      )}

      {error && (
        <Box marginBottom={1}>
          <Text color="red">{error}</Text>
        </Box>
      )}

      {mode === "status" && renderStatus()}
      {mode === "model_select" && renderModelSelect()}
      {mode === "config_select" && renderConfigSelect()}
      {mode === "config_edit" && renderConfigEdit()}
    </Box>
  );
}

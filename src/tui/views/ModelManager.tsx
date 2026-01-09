import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import TextInput from "ink-text-input";
import Spinner from "ink-spinner";
import { loadRegistry, removeModel, setDefaultModel, addModel } from "../../models/registry.js";
import { loadConfig } from "../../config/index.js";
import { searchModels, getModelFiles, downloadModelFile } from "../../hf/client.js";
import fs from "fs-extra";
import path from "path";
import os from "os";

type ModelManagerState = "list" | "search" | "results" | "downloading" | "removing" | "local_browse" | "local_path";

type Props = {
  onBack: () => void;
};

type LocalModel = {
  path: string;
  name: string;
  size: number;
};

export function ModelManager({ onBack }: Props) {
  const [state, setState] = useState<ModelManagerState>("list");
  const [models, setModels] = useState<any[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [localModels, setLocalModels] = useState<LocalModel[]>([]);
  const [manualPath, setManualPath] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = () => {
    const registry = loadRegistry();
    setModels(registry.models);
  };

  const scanForLocalModels = async () => {
    const found: LocalModel[] = [];
    const searchDirs = [
      path.join(os.homedir(), "Downloads"),
      path.join(os.homedir(), "Documents"),
      process.cwd(),
    ];

    try {
      for (const dir of searchDirs) {
        if (await fs.pathExists(dir)) {
          const files = await fs.readdir(dir);
          for (const file of files) {
            if (file.endsWith(".gguf")) {
              const fullPath = path.join(dir, file);
              const stats = await fs.stat(fullPath);
              found.push({
                path: fullPath,
                name: file,
                size: stats.size
              });
            }
          }
        }
      }
    } catch (err) {
      // Ignore scan errors
    }

    return found;
  };

  useInput(async (input, key) => {
    if (key.escape || input === "b") {
      if (state === "list") {
        onBack();
      } else {
        setState("list");
        setSearchQuery("");
        setManualPath("");
        setError("");
      }
      return;
    }

    if (state === "list") {
      if (key.upArrow && models.length > 0) {
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : models.length - 1));
      } else if (key.downArrow && models.length > 0) {
        setSelectedIndex((prev) => (prev < models.length - 1 ? prev + 1 : 0));
      } else if (input === "d" && models.length > 0) {
        await handleSetDefault();
      } else if (input === "r" && models.length > 0) {
        await handleRemove();
      } else if (input === "i") {
        setState("search");
      } else if (input === "l") {
        // Load local model
        setStatusMessage("Scanning for local .gguf files...");
        const found = await scanForLocalModels();
        setLocalModels(found);
        setSelectedIndex(0);
        setState("local_browse");
        setStatusMessage("");
      } else if (input === "p") {
        // Manual path input
        setState("local_path");
      }
    }

    if (state === "results") {
      if (key.upArrow) {
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : searchResults.length - 1));
      } else if (key.downArrow) {
        setSelectedIndex((prev) => (prev < searchResults.length - 1 ? prev + 1 : 0));
      } else if (key.return && searchResults.length > 0) {
        await handleInstall(searchResults[selectedIndex]);
      }
    }

    if (state === "local_browse") {
      if (key.upArrow && localModels.length > 0) {
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : localModels.length - 1));
      } else if (key.downArrow && localModels.length > 0) {
        setSelectedIndex((prev) => (prev < localModels.length - 1 ? prev + 1 : 0));
      } else if (key.return && localModels.length > 0) {
        await handleAddLocalModel(localModels[selectedIndex].path);
      } else if (input === "p") {
        setState("local_path");
      }
    }
  });

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    try {
      setState("results");
      setSelectedIndex(0);
      const results = await searchModels(searchQuery, 10);
      setSearchResults(results);
      if (results.length === 0) {
        setError("No models found");
      }
    } catch (err: any) {
      setError(`Search failed: ${err.message}`);
    }
  };

  const handleInstall = async (model: any) => {
    try {
      setState("downloading");
      setStatusMessage("Fetching model files...");

      const files = await getModelFiles(model.id);
      const ggufFiles = files.filter((f: any) => f.name.endsWith(".gguf"));

      if (ggufFiles.length === 0) {
        setError("No GGUF files found");
        setState("results");
        return;
      }

      const fileToDownload = ggufFiles.sort((a: any, b: any) => (a.size || 0) - (b.size || 0))[0];
      setStatusMessage(`Downloading ${fileToDownload.name}...`);

      const downloadResult = await downloadModelFile(model.id, fileToDownload.name);

      const modelId = `${model.id.replace("/", "-")}-${fileToDownload.name}`;
      addModel({
        id: modelId,
        repoId: model.id,
        filename: fileToDownload.name,
        localPath: downloadResult.path,
        size: downloadResult.size,
        sha256: downloadResult.sha256,
        dateInstalled: new Date().toISOString()
      });

      loadModels();
      setState("list");
      setStatusMessage("Model installed successfully!");
      setTimeout(() => setStatusMessage(""), 3000);
    } catch (err: any) {
      setError(`Download failed: ${err.message}`);
      setState("results");
    }
  };

  const handleAddLocalModel = async (modelPath: string) => {
    try {
      // Validate file exists and is .gguf
      if (!await fs.pathExists(modelPath)) {
        setError("File not found");
        return;
      }

      if (!modelPath.endsWith(".gguf")) {
        setError("File must be a .gguf file");
        return;
      }

      const stats = await fs.stat(modelPath);
      const filename = path.basename(modelPath);
      const modelId = `local-${filename.replace(/\.gguf$/, "")}`;

      // Check if already exists
      const registry = loadRegistry();
      if (registry.models.find((m) => m.id === modelId)) {
        setError("Model already in registry");
        setState("list");
        return;
      }

      addModel({
        id: modelId,
        repoId: "local",
        filename: filename,
        localPath: modelPath,
        size: stats.size,
        dateInstalled: new Date().toISOString()
      });

      loadModels();
      setState("list");
      setStatusMessage(`Added local model: ${filename}`);
      setTimeout(() => setStatusMessage(""), 3000);
    } catch (err: any) {
      setError(`Failed to add model: ${err.message}`);
      setState("list");
    }
  };

  const handleManualPathSubmit = async () => {
    if (!manualPath.trim()) {
      setState("list");
      return;
    }

    await handleAddLocalModel(manualPath.trim());
  };

  const handleSetDefault = () => {
    if (models.length === 0) return;
    const model = models[selectedIndex];
    setDefaultModel(model.id);
    setStatusMessage(`Set ${model.id} as default`);
    setTimeout(() => setStatusMessage(""), 2000);
  };

  const handleRemove = async () => {
    if (models.length === 0) return;

    const model = models[selectedIndex];
    setState("removing");

    try {
      // Remove file only if it's in our models directory
      const modelsDir = path.dirname(model.localPath);
      if (await fs.pathExists(model.localPath) && modelsDir.includes("local")) {
        await fs.remove(model.localPath);
      }

      // Remove from registry
      removeModel(model.id);

      loadModels();
      setSelectedIndex(0);
      setState("list");
      setStatusMessage(`Removed ${model.id}`);
      setTimeout(() => setStatusMessage(""), 2000);
    } catch (err: any) {
      setError(`Failed to remove: ${err.message}`);
      setState("list");
    }
  };

  const getDefaultModelId = () => {
    const config = loadConfig();
    return config.defaultModelId;
  };

  return (
    <Box flexDirection="column" paddingX={2} paddingY={1}>
      {statusMessage && (
        <Box marginBottom={1}>
          <Text color="green">✓ {statusMessage}</Text>
        </Box>
      )}

      {error && (
        <Box marginBottom={1}>
          <Text color="red">✗ {error}</Text>
        </Box>
      )}

      {state === "list" && (
        <Box flexDirection="column">
          <Box marginBottom={1}>
            <Text bold>Installed Models ({models.length})</Text>
          </Box>

          {models.length > 0 ? (
            <>
              <Box flexDirection="column" marginBottom={1}>
                {models.map((model, index) => {
                  const isSelected = index === selectedIndex;
                  const isDefault = model.id === getDefaultModelId();
                  const isLocal = model.repoId === "local";
                  return (
                    <Box key={model.id} marginBottom={1}>
                      <Text
                        bold={isSelected}
                        color={isSelected ? "cyan" : undefined}
                        backgroundColor={isSelected ? "blue" : undefined}
                      >
                        {isSelected ? "▶ " : "  "}
                        {isDefault ? "⭐ " : ""}
                        {isLocal ? "💾 " : ""}
                        {model.id}
                      </Text>
                      {isSelected && (
                        <Text dimColor> ({(model.size / 1024 / 1024 / 1024).toFixed(2)} GB)</Text>
                      )}
                    </Box>
                  );
                })}
              </Box>

              <Box marginTop={1} flexDirection="column">
                <Text dimColor>[i] Install from HF  [l] Load local  [p] Enter path</Text>
                <Text dimColor>[d] Set default  [r] Remove  ESC to go back</Text>
              </Box>
            </>
          ) : (
            <>
              <Text color="yellow">No models installed yet.</Text>
              <Box marginTop={1} flexDirection="column">
                <Text dimColor>Press [i] to download from Hugging Face</Text>
                <Text dimColor>Press [l] to load local .gguf file</Text>
                <Text dimColor>Press [p] to enter file path manually</Text>
              </Box>
            </>
          )}
        </Box>
      )}

      {state === "search" && (
        <Box flexDirection="column">
          <Box marginBottom={1}>
            <Text bold>Search Models on Hugging Face</Text>
          </Box>
          <Box borderStyle="single" paddingX={1}>
            <Text>🔍 </Text>
            <TextInput
              value={searchQuery}
              onChange={setSearchQuery}
              onSubmit={handleSearch}
              placeholder="Enter model name..."
            />
          </Box>
          <Box marginTop={1}>
            <Text dimColor>Press ESC to cancel</Text>
          </Box>
        </Box>
      )}

      {state === "results" && (
        <Box flexDirection="column">
          <Box marginBottom={1}>
            <Text bold>Search Results ({searchResults.length})</Text>
          </Box>

          {searchResults.length > 0 ? (
            <>
              <Box flexDirection="column" marginBottom={1}>
                {searchResults.map((model, index) => {
                  const isSelected = index === selectedIndex;
                  return (
                    <Box key={model.id}>
                      <Text
                        bold={isSelected}
                        color={isSelected ? "cyan" : undefined}
                        backgroundColor={isSelected ? "blue" : undefined}
                      >
                        {isSelected ? "▶ " : "  "}
                        {model.id}
                      </Text>
                    </Box>
                  );
                })}
              </Box>
              <Box marginTop={1}>
                <Text dimColor>↑/↓ navigate, Enter to install, ESC to cancel</Text>
              </Box>
            </>
          ) : (
            <Text>No results found. Press ESC to search again.</Text>
          )}
        </Box>
      )}

      {state === "local_browse" && (
        <Box flexDirection="column">
          <Box marginBottom={1}>
            <Text bold>Found Local Models ({localModels.length})</Text>
          </Box>

          {localModels.length > 0 ? (
            <>
              <Box flexDirection="column" marginBottom={1}>
                {localModels.map((model, index) => {
                  const isSelected = index === selectedIndex;
                  return (
                    <Box key={model.path}>
                      <Text
                        bold={isSelected}
                        color={isSelected ? "cyan" : undefined}
                        backgroundColor={isSelected ? "blue" : undefined}
                      >
                        {isSelected ? "▶ " : "  "}
                        {model.name}
                      </Text>
                      {isSelected && (
                        <Text dimColor> ({(model.size / 1024 / 1024 / 1024).toFixed(2)} GB)</Text>
                      )}
                    </Box>
                  );
                })}
              </Box>
              <Box marginTop={1} flexDirection="column">
                <Text dimColor>↑/↓ navigate, Enter to add, [p] manual path, ESC cancel</Text>
              </Box>
            </>
          ) : (
            <>
              <Text color="yellow">No .gguf files found in common directories.</Text>
              <Box marginTop={1}>
                <Text dimColor>Searched: ~/Downloads, ~/Documents, current dir</Text>
                <Text dimColor>Press [p] to enter path manually, ESC to cancel</Text>
              </Box>
            </>
          )}
        </Box>
      )}

      {state === "local_path" && (
        <Box flexDirection="column">
          <Box marginBottom={1}>
            <Text bold>Enter Model Path</Text>
          </Box>
          <Box marginBottom={1}>
            <Text dimColor>Enter full path to .gguf file:</Text>
          </Box>
          <Box borderStyle="single" paddingX={1}>
            <Text>📁 </Text>
            <TextInput
              value={manualPath}
              onChange={setManualPath}
              onSubmit={handleManualPathSubmit}
              placeholder="C:\path\to\model.gguf"
            />
          </Box>
          <Box marginTop={1}>
            <Text dimColor>Press ESC to cancel</Text>
          </Box>
        </Box>
      )}

      {state === "downloading" && (
        <Box>
          <Text>
            <Spinner type="dots" /> {statusMessage}
          </Text>
        </Box>
      )}

      {state === "removing" && (
        <Box>
          <Text>
            <Spinner type="dots" /> Removing model...
          </Text>
        </Box>
      )}
    </Box>
  );
}

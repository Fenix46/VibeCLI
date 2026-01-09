import React, { useState } from "react";
import { Box, Text, useInput } from "ink";
import TextInput from "ink-text-input";
import Spinner from "ink-spinner";
import { searchModels, getModelFiles, downloadModelFile } from "../../hf/client.js";
import { addModel } from "../../models/registry.js";
import fs from "fs-extra";
import path from "path";

type OnboardingState = "welcome" | "choice" | "search" | "results" | "downloading" | "local_path" | "done";

type Props = {
  onComplete: () => void;
};

export function OnboardingView({ onComplete }: Props) {
  const [state, setState] = useState<OnboardingState>("welcome");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [downloadProgress, setDownloadProgress] = useState("");
  const [localPath, setLocalPath] = useState("");
  const [error, setError] = useState("");

  useInput(async (input, key) => {
    if (state === "welcome" && key.return) {
      setState("choice");
    }

    if (state === "choice") {
      if (input === "1") {
        setState("search");
      } else if (input === "2") {
        setState("local_path");
      }
    }

    if (state === "results") {
      if (key.upArrow) {
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : searchResults.length - 1));
      } else if (key.downArrow) {
        setSelectedIndex((prev) => (prev < searchResults.length - 1 ? prev + 1 : 0));
      } else if (key.return) {
        await handleInstall(searchResults[selectedIndex]);
      } else if (input === "b") {
        setState("search");
        setSearchQuery("");
      }
    }

    if (state === "done" && key.return) {
      onComplete();
    }
  });

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    try {
      setState("results");
      const results = await searchModels(searchQuery, 10);
      setSearchResults(results);
      if (results.length === 0) {
        setError("No models found. Try a different search term.");
      }
    } catch (err: any) {
      setError(`Search failed: ${err.message}`);
    }
  };

  const handleInstall = async (model: any) => {
    try {
      setState("downloading");
      setDownloadProgress("Fetching model files...");

      const files = await getModelFiles(model.id);
      const ggufFiles = files.filter((f: any) => f.name.endsWith(".gguf"));

      if (ggufFiles.length === 0) {
        setError("No GGUF files found in this model");
        setState("results");
        return;
      }

      // Download first GGUF file (or smallest one)
      const fileToDownload = ggufFiles.sort((a: any, b: any) => (a.size || 0) - (b.size || 0))[0];

      setDownloadProgress(`Downloading ${fileToDownload.name}...`);

      const downloadResult = await downloadModelFile(model.id, fileToDownload.name);

      // Add to registry
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

      setState("done");
    } catch (err: any) {
      setError(`Download failed: ${err.message}`);
      setState("results");
    }
  };

  const handleLocalPathSubmit = async () => {
    if (!localPath.trim()) {
      setState("choice");
      return;
    }

    try {
      const modelPath = localPath.trim();

      // Validate file exists and is .gguf
      if (!await fs.pathExists(modelPath)) {
        setError("File not found");
        return;
      }

      if (!modelPath.endsWith(".gguf")) {
        setError("File must be a .gguf file");
        return;
      }

      setState("downloading");
      setDownloadProgress("Adding local model...");

      const stats = await fs.stat(modelPath);
      const filename = path.basename(modelPath);
      const modelId = `local-${filename.replace(/\.gguf$/, "")}`;

      addModel({
        id: modelId,
        repoId: "local",
        filename: filename,
        localPath: modelPath,
        size: stats.size,
        dateInstalled: new Date().toISOString()
      });

      setState("done");
    } catch (err: any) {
      setError(`Failed to add model: ${err.message}`);
      setState("local_path");
    }
  };

  return (
    <Box flexDirection="column" paddingX={2} paddingY={1}>
      {state === "welcome" && (
        <Box flexDirection="column">
          <Box marginBottom={1}>
            <Text bold color="cyan">
              🎉 Welcome to Local CLI!
            </Text>
          </Box>
          <Text>
            It looks like you don't have any models installed yet.
          </Text>
          <Text>
            Let's get you set up with a model to start using the CLI!
          </Text>
          <Box marginTop={2}>
            <Text dimColor>
              Press <Text bold>Enter</Text> to continue
            </Text>
          </Box>
        </Box>
      )}

      {state === "choice" && (
        <Box flexDirection="column">
          <Box marginBottom={1}>
            <Text bold>How would you like to add a model?</Text>
          </Box>

          <Box flexDirection="column" marginY={1}>
            <Box marginBottom={1}>
              <Text bold color="cyan">
                [1] Download from Hugging Face
              </Text>
            </Box>
            <Box marginLeft={4} marginBottom={2}>
              <Text dimColor>Search and download models from the Hugging Face hub</Text>
            </Box>

            <Box marginBottom={1}>
              <Text bold color="cyan">
                [2] Use a local .gguf file
              </Text>
            </Box>
            <Box marginLeft={4}>
              <Text dimColor>Add a model you've already downloaded</Text>
            </Box>
          </Box>

          <Box marginTop={1}>
            <Text dimColor>Press [1] or [2] to choose</Text>
          </Box>
        </Box>
      )}

      {state === "search" && (
        <Box flexDirection="column">
          <Box marginBottom={1}>
            <Text bold>Search for a model:</Text>
          </Box>
          <Box marginBottom={1}>
            <Text dimColor>
              Try: "llama", "mistral", "qwen", "phi"
            </Text>
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
        </Box>
      )}

      {state === "results" && (
        <Box flexDirection="column">
          <Box marginBottom={1}>
            <Text bold>
              Search Results ({searchResults.length})
            </Text>
          </Box>

          {searchResults.length > 0 ? (
            <>
              <Box flexDirection="column" marginBottom={1}>
                {searchResults.map((model, index) => {
                  const isSelected = index === selectedIndex;
                  return (
                    <Box key={model.id} marginBottom={1}>
                      <Text
                        bold={isSelected}
                        color={isSelected ? "cyan" : undefined}
                        backgroundColor={isSelected ? "blue" : undefined}
                      >
                        {isSelected ? "▶ " : "  "}
                        {model.id}
                      </Text>
                      {isSelected && (
                        <Text dimColor> ({model.downloads || 0} downloads)</Text>
                      )}
                    </Box>
                  );
                })}
              </Box>
              <Box marginTop={1}>
                <Text dimColor>
                  ↑/↓ to navigate, Enter to install, [b] to search again
                </Text>
              </Box>
            </>
          ) : (
            <Text color="yellow">No models found. Press [b] to search again.</Text>
          )}

          {error && (
            <Box marginTop={1}>
              <Text color="red">{error}</Text>
            </Box>
          )}
        </Box>
      )}

      {state === "local_path" && (
        <Box flexDirection="column">
          <Box marginBottom={1}>
            <Text bold>Enter Model Path</Text>
          </Box>
          <Box marginBottom={1}>
            <Text dimColor>Enter the full path to your .gguf file:</Text>
          </Box>
          <Box borderStyle="single" paddingX={1}>
            <Text>📁 </Text>
            <TextInput
              value={localPath}
              onChange={setLocalPath}
              onSubmit={handleLocalPathSubmit}
              placeholder="C:\path\to\model.gguf"
            />
          </Box>
          {error && (
            <Box marginTop={1}>
              <Text color="red">{error}</Text>
            </Box>
          )}
        </Box>
      )}

      {state === "downloading" && (
        <Box flexDirection="column">
          <Box marginBottom={1}>
            <Text>
              <Spinner type="dots" />
              {" " + downloadProgress}
            </Text>
          </Box>
          <Text dimColor>This may take a moment...</Text>
        </Box>
      )}

      {state === "done" && (
        <Box flexDirection="column">
          <Box marginBottom={1}>
            <Text bold color="green">
              ✅ Model set up successfully!
            </Text>
          </Box>
          <Text>You're all set to start using Local CLI.</Text>
          <Box marginTop={2}>
            <Text dimColor>
              Press <Text bold>Enter</Text> to continue to Main Menu
            </Text>
          </Box>
        </Box>
      )}
    </Box>
  );
}

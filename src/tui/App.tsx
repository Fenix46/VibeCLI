import React, { useState, useEffect } from "react";
import { Box, Text, useApp } from "ink";
import { MainMenu } from "./views/MainMenu.js";
import { ChatView } from "./views/ChatView.js";
import { ModelManager } from "./views/ModelManager.js";
import { TasksView } from "./views/TasksView.js";
import { ConfigView } from "./views/ConfigView.js";
import { ServerView } from "./views/ServerView.js";
import { OnboardingView } from "./views/OnboardingView.js";
import { loadConfig } from "../config/index.js";
import { getDefaultModel, loadRegistry } from "../models/registry.js";
import { ensureServer, getServerBaseUrl, stopServer } from "../server/manager.js";

export type View = "onboarding" | "main_menu" | "chat" | "models" | "tasks" | "config" | "server";

type AppState = {
  currentView: View;
  serverUrl: string;
  modelPath: string;
  error: string;
  isServerReady: boolean;
};

export function App() {
  const { exit } = useApp();
  const [state, setState] = useState<AppState>({
    currentView: "main_menu",
    serverUrl: "",
    modelPath: "",
    error: "",
    isServerReady: false
  });

  useEffect(() => {
    // Check if we need onboarding
    (async () => {
      try {
        const registry = loadRegistry();
        if (registry.models.length === 0) {
          setState((prev) => ({ ...prev, currentView: "onboarding" }));
          return;
        }

        // Models available, go to main menu
        setState((prev) => ({ ...prev, currentView: "main_menu" }));
      } catch (err: any) {
        setState((prev) => ({ ...prev, error: `Startup error: ${err.message}` }));
      }
    })();

    // Cleanup on exit
    return () => {
      stopServer().catch(() => {});
    };
  }, []);

  const ensureServerForChat = async () => {
    try {
      const config = loadConfig();
      const model = getDefaultModel();

      if (!model) {
        setState((prev) => ({ ...prev, error: "No default model configured" }));
        return false;
      }

      const serverState = await ensureServer(config, model.localPath);
      setState((prev) => ({
        ...prev,
        serverUrl: getServerBaseUrl(serverState.port),
        modelPath: model.localPath,
        isServerReady: true,
        error: ""
      }));
      return true;
    } catch (err: any) {
      setState((prev) => ({ ...prev, error: `Failed to start server: ${err.message}` }));
      return false;
    }
  };

  const navigateTo = async (view: View) => {
    if (view === "chat") {
      // Ensure server is ready before navigating to chat
      const ready = await ensureServerForChat();
      if (!ready) return;
    }
    setState((prev) => ({ ...prev, currentView: view }));
  };

  const handleExit = () => {
    exit();
  };

  return (
    <Box flexDirection="column" height="100%">
      {/* Header */}
      <Box borderStyle="round" borderColor="cyan" paddingX={1} marginBottom={1}>
        <Text bold color="cyan">
          🚀 Local CLI - {state.currentView.replace("_", " ").toUpperCase()}
        </Text>
      </Box>

      {/* Error display */}
      {state.error && (
        <Box paddingX={2} paddingY={1} borderStyle="single" borderColor="red" marginBottom={1}>
          <Text color="red">❌ {state.error}</Text>
        </Box>
      )}

      {/* Main content */}
      <Box flexGrow={1}>
        {state.currentView === "onboarding" && (
          <OnboardingView onComplete={() => navigateTo("main_menu")} />
        )}

        {state.currentView === "main_menu" && (
          <MainMenu onNavigate={navigateTo} onExit={handleExit} />
        )}

        {state.currentView === "chat" && (
          <ChatView
            serverUrl={state.serverUrl}
            modelPath={state.modelPath}
            onBack={() => navigateTo("main_menu")}
          />
        )}

        {state.currentView === "models" && (
          <ModelManager onBack={() => navigateTo("main_menu")} />
        )}

        {state.currentView === "tasks" && (
          <TasksView onBack={() => navigateTo("main_menu")} />
        )}

        {state.currentView === "config" && (
          <ConfigView onBack={() => navigateTo("main_menu")} />
        )}

        {state.currentView === "server" && (
          <ServerView onBack={() => navigateTo("main_menu")} />
        )}
      </Box>

      {/* Footer */}
      <Box borderStyle="single" borderColor="gray" paddingX={1}>
        <Box flexGrow={1}>
          <Text dimColor>
            {state.isServerReady ? "🟢 Server Ready" : "⚪ Server Idle"}
          </Text>
        </Box>
        <Box marginLeft={2}>
          <Text dimColor>
            Press <Text bold>Ctrl+Q</Text> to quit
          </Text>
        </Box>
      </Box>
    </Box>
  );
}

import React, { useState } from "react";
import { Box, Text, useInput } from "ink";
import { View } from "../App.js";

type MenuItem = {
  key: string;
  label: string;
  description: string;
  view: View | "exit";
  icon: string;
};

const menuItems: MenuItem[] = [
  { key: "1", label: "Chat", description: "Interactive chat with LLM", view: "chat", icon: "💬" },
  { key: "2", label: "Models", description: "Manage and download models", view: "models", icon: "🤖" },
  { key: "3", label: "Tasks", description: "Scheduled tasks", view: "tasks", icon: "📋" },
  { key: "4", label: "Config", description: "View configuration", view: "config", icon: "⚙️" },
  { key: "5", label: "Server", description: "Server status and logs", view: "server", icon: "🖥️" },
  { key: "q", label: "Exit", description: "Quit application", view: "exit", icon: "🚪" }
];

type Props = {
  onNavigate: (view: View) => void;
  onExit: () => void;
};

export function MainMenu({ onNavigate, onExit }: Props) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  useInput((input, key) => {
    if (key.upArrow) {
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : menuItems.length - 1));
    } else if (key.downArrow) {
      setSelectedIndex((prev) => (prev < menuItems.length - 1 ? prev + 1 : 0));
    } else if (key.return) {
      const selected = menuItems[selectedIndex];
      if (selected.view === "exit") {
        onExit();
      } else {
        onNavigate(selected.view as View);
      }
    } else {
      // Number key navigation
      const item = menuItems.find((m) => m.key === input);
      if (item) {
        if (item.view === "exit") {
          onExit();
        } else {
          onNavigate(item.view as View);
        }
      }
    }
  });

  return (
    <Box flexDirection="column" paddingX={2} paddingY={1}>
      <Box marginBottom={1}>
        <Text bold color="cyan">
          Main Menu
        </Text>
      </Box>

      <Box flexDirection="column">
        {menuItems.map((item, index) => {
          const isSelected = index === selectedIndex;
          return (
            <Box key={item.key} marginBottom={1}>
              <Text
                bold={isSelected}
                color={isSelected ? "cyan" : undefined}
                backgroundColor={isSelected ? "blue" : undefined}
              >
                {isSelected ? "▶ " : "  "}
                {item.icon} [{item.key}] {item.label}
              </Text>
              {isSelected && (
                <Text dimColor> - {item.description}</Text>
              )}
            </Box>
          );
        })}
      </Box>

      <Box marginTop={2} flexDirection="column">
        <Text dimColor>
          Navigation: ↑/↓ or number keys, Enter to select
        </Text>
      </Box>
    </Box>
  );
}

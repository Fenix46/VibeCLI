import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import { loadTasks } from "../../tasks/storage.js";

type Props = {
  onBack: () => void;
};

export function TasksView({ onBack }: Props) {
  const [tasks, setTasks] = useState<any[]>([]);

  useEffect(() => {
    const store = loadTasks();
    setTasks(store.tasks);
  }, []);

  useInput((input, key) => {
    if (key.escape || input === "b") {
      onBack();
    }
  });

  return (
    <Box flexDirection="column" paddingX={2} paddingY={1}>
      <Box marginBottom={1}>
        <Text bold>Scheduled Tasks ({tasks.length})</Text>
      </Box>

      {tasks.length > 0 ? (
        <Box flexDirection="column">
          {tasks.map((task, index) => (
            <Box key={task.id} flexDirection="column" marginBottom={1}>
              <Text bold color="cyan">
                {index + 1}. {task.name}
              </Text>
              <Text dimColor>   Type: {task.type}</Text>
              {task.schedule && (
                <Text dimColor>
                   Schedule: Every {task.schedule.minutes} minutes
                </Text>
              )}
              {task.lastRun && (
                <Text dimColor>   Last run: {new Date(task.lastRun).toLocaleString()}</Text>
              )}
              <Text dimColor>   Runs: {task.runs.length}</Text>
            </Box>
          ))}
        </Box>
      ) : (
        <Box>
          <Text color="yellow">No tasks configured.</Text>
        </Box>
      )}

      <Box marginTop={2}>
        <Text dimColor>Press ESC to go back</Text>
      </Box>

      <Box marginTop={1}>
        <Text dimColor>
          Tip: Use CLI commands to create and manage tasks:
        </Text>
        <Text dimColor>  local task create</Text>
        <Text dimColor>  local task run &lt;name&gt;</Text>
      </Box>
    </Box>
  );
}

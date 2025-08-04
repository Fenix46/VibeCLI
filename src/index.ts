#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import { setupCommand } from './cli/setup';
import { chatCommand } from './cli/chat';
import { contextCommand } from './cli/context';
import { toolsCommand } from './cli/tools';

const program = new Command();

program
  .name('vibe')
  .description('AI agent that lives in your terminal')
  .version('1.0.0');

// Setup command for initial configuration
program
  .command('setup')
  .description('Interactive setup for API keys and models')
  .action(setupCommand);

// Chat command for interacting with the AI
program
  .command('chat')
  .alias('c')
  .description('Start a chat session with the AI agent')
  .option('-m, --message <message>', 'Send a single message')
  .action(chatCommand);

// Context management
program
  .command('context')
  .description('Manage project context and memory')
  .option('-s, --show', 'Show current context')
  .option('-c, --clear', 'Clear context')
  .option('-r, --reset', 'Reset context to default')
  .action(contextCommand);

// Tools integration
program
  .command('tools')
  .description('Access to file, git, and shell tools')
  .option('-l, --list', 'List available tools')
  .action(toolsCommand);

// Default action - show help if no command provided
program.action(() => {
  console.log(chalk.cyan('🤖 VibeCli - Your AI Terminal Agent'));
  console.log(chalk.gray('Run "vibe setup" to get started'));
  program.help();
});

program.parse();

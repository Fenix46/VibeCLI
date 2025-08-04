import chalk from 'chalk';
import { ConfigManager } from '../core/config';
import { FileTools } from '../tools/file-tools';
import { GitTools } from '../tools/git-tools';
import { ShellTools } from '../tools/shell-tools';

export async function toolsCommand(options: { list?: boolean }) {
  const config = new ConfigManager();
  
  // Check if setup is complete
  if (!(await config.isSetupComplete())) {
    console.log(chalk.yellow('⚠️  VibeCli is not set up yet.'));
    console.log(chalk.gray('Run "vibe setup" to configure your AI provider.'));
    return;
  }

  if (options.list) {
    listAvailableTools();
  } else {
    showToolsHelp();
  }
}

function listAvailableTools(): void {
  console.log(chalk.cyan.bold('\n🛠️  Available Tools\n'));
  
  console.log(chalk.yellow('📁 File Tools:'));
  console.log('  • Read files and directories');
  console.log('  • Write and modify files');
  console.log('  • Search file contents');
  console.log('  • File system operations');
  
  console.log(chalk.yellow('\n🔧 Git Tools:'));
  console.log('  • Repository status');
  console.log('  • Commit operations');
  console.log('  • Branch management');
  console.log('  • Diff and log viewing');
  
  console.log(chalk.yellow('\n💻 Shell Tools:'));
  console.log('  • Execute commands');
  console.log('  • Process management');
  console.log('  • Environment variables');
  console.log('  • System information');
  
  console.log(chalk.gray('\nThese tools are automatically available when chatting with VibeCli.'));
  console.log(chalk.gray('Just ask the AI to perform file operations, git commands, or shell tasks!'));
  console.log();
}

function showToolsHelp(): void {
  console.log(chalk.cyan.bold('\n🛠️  VibeCli Tools\n'));
  
  console.log('VibeCli comes with integrated tools for development tasks:');
  console.log();
  
  console.log(chalk.green('File Operations:'));
  console.log('  "Read the package.json file"');
  console.log('  "Create a new component in src/components"');
  console.log('  "Search for TODO comments in the codebase"');
  console.log();
  
  console.log(chalk.green('Git Operations:'));
  console.log('  "Show git status"');
  console.log('  "Create a new branch for feature X"');
  console.log('  "Show the last 5 commits"');
  console.log();
  
  console.log(chalk.green('Shell Commands:'));
  console.log('  "Install dependencies with npm"');
  console.log('  "Run the test suite"');
  console.log('  "Check disk usage"');
  console.log();
  
  console.log(chalk.gray('Simply chat with VibeCli using "vibe chat" and ask for any of these operations!'));
  console.log(chalk.gray('Use "vibe tools --list" to see all available tool categories.'));
  console.log();
}

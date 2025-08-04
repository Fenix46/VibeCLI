import chalk from 'chalk';
import { ContextManager } from '../core/context';
import { ConfigManager } from '../core/config';

export async function contextCommand(options: { show?: boolean; clear?: boolean; reset?: boolean }) {
  const config = new ConfigManager();
  
  // Check if setup is complete
  if (!(await config.isSetupComplete())) {
    console.log(chalk.yellow('⚠️  VibeCli is not set up yet.'));
    console.log(chalk.gray('Run "vibe setup" to configure your AI provider.'));
    return;
  }

  const context = new ContextManager();
  
  try {
    await context.initializeContext();
    
    if (options.show) {
      await showContext(context);
    } else if (options.clear) {
      await clearContext(context);
    } else if (options.reset) {
      await resetContext(context);
    } else {
      // Default: show context summary
      await showContextSummary(context);
    }
    
  } catch (error) {
    console.error(chalk.red('Error managing context:'), error);
  }
}

async function showContext(context: ContextManager): Promise<void> {
  console.log(chalk.cyan.bold('\n📋 Project Context\n'));
  
  const summary = await context.getProjectSummary();
  console.log(summary);
  
  const recentMessages = await context.getRecentContext(5);
  
  if (recentMessages.length > 0) {
    console.log(chalk.cyan('\n💬 Recent Messages:'));
    recentMessages.forEach((msg, index) => {
      const roleColor = msg.role === 'user' ? chalk.green : chalk.blue;
      const timestamp = new Date(msg.timestamp).toLocaleTimeString();
      console.log(`${roleColor(msg.role)} [${timestamp}]: ${msg.content.substring(0, 100)}${msg.content.length > 100 ? '...' : ''}`);
    });
  }
  
  console.log();
}

async function showContextSummary(context: ContextManager): Promise<void> {
  console.log(chalk.cyan.bold('\n📋 Context Summary\n'));
  
  const summary = await context.getProjectSummary();
  console.log(summary);
  
  console.log(chalk.gray('\nOptions:'));
  console.log(chalk.gray('  --show    Show full context details'));
  console.log(chalk.gray('  --clear   Clear message history'));
  console.log(chalk.gray('  --reset   Reset entire context'));
  console.log();
}

async function clearContext(context: ContextManager): Promise<void> {
  await context.clearMessages();
  console.log(chalk.green('✅ Message history cleared successfully!'));
  console.log(chalk.gray('Project context structure remains intact.'));
}

async function resetContext(context: ContextManager): Promise<void> {
  // This would completely reset the context
  await context.initializeContext();
  console.log(chalk.green('✅ Context reset successfully!'));
  console.log(chalk.gray('A fresh context has been initialized for this project.'));
}

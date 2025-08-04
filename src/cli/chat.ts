import inquirer from 'inquirer';
import chalk from 'chalk';
import ora from 'ora';
import { ConfigManager } from '../core/config';
import { ContextManager } from '../core/context';
import { StreamingAIProvider, StreamChunk } from '../providers/streaming-provider';

export async function chatCommand(options: { message?: string }) {
  const config = new ConfigManager();
  const context = new ContextManager();
  
  // Check if setup is complete
  if (!(await config.isSetupComplete())) {
    console.log(chalk.yellow('⚠️  VibeCli is not set up yet.'));
    console.log(chalk.gray('Run "vibe setup" to configure your AI provider.'));
    return;
  }

  const vibeConfig = await config.loadConfig();
  if (!vibeConfig) {
    console.log(chalk.red('❌ Configuration not found. Please run "vibe setup".'));
    return;
  }

  const aiProvider = new StreamingAIProvider(vibeConfig);
  await context.initializeContext();

  // Update last used
  await config.updateLastUsed();

  if (options.message) {
    // Single message mode
    await processSingleMessage(options.message, aiProvider, context);
  } else {
    // Interactive chat mode
    await startInteractiveChat(aiProvider, context);
  }
}

async function processSingleMessage(message: string, aiProvider: StreamingAIProvider, context: ContextManager) {
  const spinner = ora('Thinking...').start();
  
  try {
    // Add user message to context
    await context.addMessage('user', message);
    
    let fullResponse = '';
    let hasStartedStreaming = false;
    
    // Stream AI response
    for await (const chunk of aiProvider.chatStream(message, await context.getRecentContext())) {
      if (!hasStartedStreaming) {
        spinner.stop();
        console.log(chalk.cyan('\n🤖 VibeCli:'));
        hasStartedStreaming = true;
      }
      
      if (chunk.content) {
        process.stdout.write(chunk.content);
        fullResponse += chunk.content;
      }
      
      if (chunk.isComplete) {
        console.log('\n');
        
        // Execute tool calls if any
        if (chunk.toolCalls && chunk.toolCalls.length > 0) {
          console.log(chalk.yellow('🔧 Executing tools...'));
          const toolResults = await aiProvider.executeToolCalls(chunk.toolCalls);
          toolResults.forEach(result => {
            console.log(chalk.gray(`  ${result}`));
          });
          console.log();
        }
        
        break;
      }
    }
    
    // Add AI response to context
    await context.addMessage('assistant', fullResponse);
    
  } catch (error) {
    spinner.fail('Error occurred');
    console.error(chalk.red(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`));
  }
}

async function startInteractiveChat(aiProvider: StreamingAIProvider, context: ContextManager) {
  console.log(chalk.cyan.bold('\n💬 Interactive Chat Mode'));
  console.log(chalk.gray('Type "exit" or "quit" to end the session\n'));

  while (true) {
    try {
      const { message } = await inquirer.prompt([
        {
          type: 'input',
          name: 'message',
          message: chalk.green('You:'),
          validate: (input: string) => {
            if (!input.trim()) {
              return 'Please enter a message';
            }
            return true;
          }
        }
      ]);

      if (message.toLowerCase() === 'exit' || message.toLowerCase() === 'quit') {
        console.log(chalk.yellow('\n👋 Chat session ended.'));
        break;
      }

      const spinner = ora('Thinking...').start();
      
      try {
        // Add user message to context
        await context.addMessage('user', message);
        
        let fullResponse = '';
        let hasStartedStreaming = false;
        
        // Stream AI response
        for await (const chunk of aiProvider.chatStream(message, await context.getRecentContext())) {
          if (!hasStartedStreaming) {
            spinner.stop();
            console.log(chalk.cyan('\n🤖 VibeCli:'));
            hasStartedStreaming = true;
          }
          
          if (chunk.content) {
            process.stdout.write(chunk.content);
            fullResponse += chunk.content;
          }
          
          if (chunk.isComplete) {
            console.log('\n');
            
            // Execute tool calls if any
            if (chunk.toolCalls && chunk.toolCalls.length > 0) {
              console.log(chalk.yellow('🔧 Executing tools...'));
              const toolResults = await aiProvider.executeToolCalls(chunk.toolCalls);
              toolResults.forEach(result => {
                console.log(chalk.gray(`  ${result}`));
              });
              console.log();
            }
            
            break;
          }
        }
        
        // Add AI response to context
        await context.addMessage('assistant', fullResponse);
        
      } catch (error) {
        spinner.fail('Error occurred');
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`));
      }
      
    } catch (error) {
      if (error && typeof error === 'object' && 'isTTYError' in error) {
        // User interrupted with Ctrl+C
        console.log(chalk.yellow('\n\n👋 Chat session ended.'));
        break;
      }
      console.error(chalk.red('An error occurred:'), error);
      break;
    }
  }
}

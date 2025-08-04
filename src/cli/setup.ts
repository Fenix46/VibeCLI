import inquirer from 'inquirer';
import chalk from 'chalk';
import ora from 'ora';
import { ConfigManager } from '../core/config';
import { validateApiKey } from '../providers/validator';

export async function setupCommand() {
  console.log(chalk.cyan.bold('\n🚀 VibeCli Setup Wizard\n'));
  
  try {
    const config = new ConfigManager();
    
    // Provider selection
    const { provider } = await inquirer.prompt([
      {
        type: 'list',
        name: 'provider',
        message: 'Select your AI provider:',
        choices: [
          { name: '🤖 OpenAI (GPT-4, GPT-3.5)', value: 'openai' },
          { name: '🧠 Anthropic (Claude)', value: 'anthropic' },
          { name: '🔍 Google (Gemini)', value: 'google' }
        ]
      }
    ]);

    // API Key input
    const { apiKey } = await inquirer.prompt([
      {
        type: 'password',
        name: 'apiKey',
        message: `Enter your ${provider.toUpperCase()} API key:`,
        mask: '*',
        validate: (input: string) => {
          if (!input.trim()) {
            return 'API key is required';
          }
          return true;
        }
      }
    ]);

    // Validate API key
    const spinner = ora('Validating API key...').start();
    
    try {
      const models = await validateApiKey(provider, apiKey);
      spinner.succeed('API key validated successfully!');
      
      // Model selection
      const { model } = await inquirer.prompt([
        {
          type: 'list',
          name: 'model',
          message: 'Select a model:',
          choices: models.map(model => ({
            name: `${model.name} ${model.description ? `- ${model.description}` : ''}`,
            value: model.id
          }))
        }
      ]);

      // Save configuration
      await config.saveConfig({
        provider,
        apiKey,
        model,
        setupComplete: true,
        createdAt: new Date().toISOString()
      });

      console.log(chalk.green('\n✅ Setup completed successfully!'));
      console.log(chalk.gray('You can now use "vibe chat" to start chatting with your AI agent.'));
      console.log(chalk.gray('Use "vibe context" to manage your project context.'));
      
    } catch (error) {
      spinner.fail('API key validation failed');
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`));
      process.exit(1);
    }
    
  } catch (error) {
    console.error(chalk.red('Setup failed:'), error);
    process.exit(1);
  }
}

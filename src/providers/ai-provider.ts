import { OpenAI } from 'openai';
import { Anthropic } from '@anthropic-ai/sdk';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { VibeConfig } from '../core/config';
import { Message } from '../core/context';

export class AIProvider {
  private config: VibeConfig;
  private openai?: OpenAI;
  private anthropic?: Anthropic;
  private google?: GoogleGenerativeAI;

  constructor(config: VibeConfig) {
    this.config = config;
    this.initializeProvider();
  }

  private initializeProvider(): void {
    switch (this.config.provider) {
      case 'openai':
        this.openai = new OpenAI({ apiKey: this.config.apiKey });
        break;
      case 'anthropic':
        this.anthropic = new Anthropic({ apiKey: this.config.apiKey });
        break;
      case 'google':
        this.google = new GoogleGenerativeAI(this.config.apiKey);
        break;
    }
  }

  async chat(message: string, context: Message[] = []): Promise<string> {
    switch (this.config.provider) {
      case 'openai':
        return this.chatOpenAI(message, context);
      case 'anthropic':
        return this.chatAnthropic(message, context);
      case 'google':
        return this.chatGoogle(message, context);
      default:
        throw new Error(`Unsupported provider: ${this.config.provider}`);
    }
  }

  private async chatOpenAI(message: string, context: Message[]): Promise<string> {
    if (!this.openai) throw new Error('OpenAI not initialized');

    const messages: any[] = [
      {
        role: 'system',
        content: `You are VibeCli, an AI assistant that lives in the terminal. You help developers with their projects by providing code assistance, file operations, git operations, and general development support. Be concise and helpful.

Current working directory: ${process.cwd()}
Project context: You have access to the conversation history and can help with various development tasks.`
      },
      ...context.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      {
        role: 'user',
        content: message
      }
    ];

    const response = await this.openai.chat.completions.create({
      model: this.config.model,
      messages,
      max_tokens: 2000,
      temperature: 0.7
    });

    return response.choices[0]?.message?.content || 'No response generated';
  }

  private async chatAnthropic(message: string, context: Message[]): Promise<string> {
    if (!this.anthropic) throw new Error('Anthropic not initialized');

    const systemMessage = `You are VibeCli, an AI assistant that lives in the terminal. You help developers with their projects by providing code assistance, file operations, git operations, and general development support. Be concise and helpful.

Current working directory: ${process.cwd()}
Project context: You have access to the conversation history and can help with various development tasks.`;

    const messages: any[] = [
      ...context.map(msg => ({
        role: msg.role === 'assistant' ? 'assistant' : 'user',
        content: msg.content
      })),
      {
        role: 'user',
        content: message
      }
    ];

    const response = await this.anthropic.messages.create({
      model: this.config.model,
      max_tokens: 2000,
      system: systemMessage,
      messages
    });

    const content = response.content[0];
    return content.type === 'text' ? content.text : 'No response generated';
  }

  private async chatGoogle(message: string, context: Message[]): Promise<string> {
    if (!this.google) throw new Error('Google not initialized');

    const model = this.google.getGenerativeModel({ model: this.config.model });

    let prompt = `You are VibeCli, an AI assistant that lives in the terminal. You help developers with their projects by providing code assistance, file operations, git operations, and general development support. Be concise and helpful.

Current working directory: ${process.cwd()}
Project context: You have access to the conversation history and can help with various development tasks.

`;

    // Add context
    if (context.length > 0) {
      prompt += 'Recent conversation:\n';
      context.forEach(msg => {
        prompt += `${msg.role}: ${msg.content}\n`;
      });
      prompt += '\n';
    }

    prompt += `User: ${message}\nAssistant:`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    return response.text() || 'No response generated';
  }
}

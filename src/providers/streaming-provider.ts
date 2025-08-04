import { OpenAI } from 'openai';
import { Anthropic } from '@anthropic-ai/sdk';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { VibeConfig } from '../core/config';
import { Message } from '../core/context';
import { ToolRegistry } from '../tools/tool-registry';
import { PromptTemplates } from '../core/prompts';

export interface StreamChunk {
  content: string;
  isComplete: boolean;
  toolCalls?: ToolCall[];
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: any;
}

export class StreamingAIProvider {
  private config: VibeConfig;
  private openai?: OpenAI;
  private anthropic?: Anthropic;
  private google?: GoogleGenerativeAI;
  private toolRegistry: ToolRegistry;

  constructor(config: VibeConfig) {
    this.config = config;
    this.toolRegistry = new ToolRegistry();
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

  async *chatStream(message: string, context: Message[] = []): AsyncGenerator<StreamChunk> {
    switch (this.config.provider) {
      case 'openai':
        yield* this.streamOpenAI(message, context);
        break;
      case 'anthropic':
        yield* this.streamAnthropic(message, context);
        break;
      case 'google':
        yield* this.streamGoogle(message, context);
        break;
      default:
        throw new Error(`Unsupported provider: ${this.config.provider}`);
    }
  }

  private async *streamOpenAI(message: string, context: Message[]): AsyncGenerator<StreamChunk> {
    if (!this.openai) throw new Error('OpenAI not initialized');

    const systemPrompt = this.buildSystemPrompt();
    const tools = this.toolRegistry.getOpenAITools();

    const messages: any[] = [
      { role: 'system', content: systemPrompt },
      ...context.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      { role: 'user', content: message }
    ];

    const stream = await this.openai.chat.completions.create({
      model: this.config.model,
      messages,
      max_tokens: 2000,
      temperature: 0.7,
      stream: true,
      tools: tools.length > 0 ? tools : undefined,
      tool_choice: 'auto'
    });

    let accumulatedContent = '';
    let toolCalls: ToolCall[] = [];

    for await (const chunk of stream) {
      const delta = chunk.choices[0]?.delta;
      
      if (delta?.content) {
        accumulatedContent += delta.content;
        yield {
          content: delta.content,
          isComplete: false
        };
      }

      if (delta?.tool_calls) {
        for (const toolCall of delta.tool_calls) {
          if (toolCall.function) {
            toolCalls.push({
              id: toolCall.id || '',
              name: toolCall.function.name || '',
              arguments: JSON.parse(toolCall.function.arguments || '{}')
            });
          }
        }
      }

      if (chunk.choices[0]?.finish_reason === 'stop' || chunk.choices[0]?.finish_reason === 'tool_calls') {
        yield {
          content: '',
          isComplete: true,
          toolCalls: toolCalls.length > 0 ? toolCalls : undefined
        };
        break;
      }
    }
  }

  private async *streamAnthropic(message: string, context: Message[]): AsyncGenerator<StreamChunk> {
    if (!this.anthropic) throw new Error('Anthropic not initialized');

    const systemPrompt = this.buildSystemPrompt();
    const tools = this.toolRegistry.getAnthropicTools();

    const messages: any[] = [
      ...context.map(msg => ({
        role: msg.role === 'assistant' ? 'assistant' : 'user',
        content: msg.content
      })),
      { role: 'user', content: message }
    ];

    const stream = await this.anthropic.messages.create({
      model: this.config.model,
      max_tokens: 2000,
      system: systemPrompt,
      messages,
      tools: tools.length > 0 ? tools : undefined,
      stream: true
    });

    let accumulatedContent = '';

    for await (const chunk of stream) {
      if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
        accumulatedContent += chunk.delta.text;
        yield {
          content: chunk.delta.text,
          isComplete: false
        };
      }

      if (chunk.type === 'message_stop') {
        yield {
          content: '',
          isComplete: true
        };
        break;
      }
    }
  }

  private async *streamGoogle(message: string, context: Message[]): AsyncGenerator<StreamChunk> {
    if (!this.google) throw new Error('Google not initialized');

    const model = this.google.getGenerativeModel({ model: this.config.model });
    
    let prompt = this.buildSystemPrompt() + '\n\n';
    
    if (context.length > 0) {
      prompt += 'Recent conversation:\n';
      context.forEach(msg => {
        prompt += `${msg.role}: ${msg.content}\n`;
      });
      prompt += '\n';
    }

    prompt += `User: ${message}\nAssistant:`;

    const result = await model.generateContentStream(prompt);
    
    for await (const chunk of result.stream) {
      const chunkText = chunk.text();
      if (chunkText) {
        yield {
          content: chunkText,
          isComplete: false
        };
      }
    }

    yield {
      content: '',
      isComplete: true
    };
  }

  private buildSystemPrompt(): string {
    return PromptTemplates.getSystemPrompt(
      process.cwd(),
      this.toolRegistry.getAvailableTools()
    );
  }

  async executeToolCalls(toolCalls: ToolCall[]): Promise<string[]> {
    const results: string[] = [];
    
    for (const toolCall of toolCalls) {
      try {
        const result = await this.toolRegistry.executeTool(toolCall.name, toolCall.arguments);
        results.push(`Tool ${toolCall.name} executed successfully: ${result}`);
      } catch (error) {
        results.push(`Tool ${toolCall.name} failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
    
    return results;
  }
}

import { OpenAI } from 'openai';
import { Anthropic } from '@anthropic-ai/sdk';
import { GoogleGenerativeAI } from '@google/generative-ai';

export interface ModelInfo {
  id: string;
  name: string;
  description?: string;
}

export async function validateApiKey(provider: string, apiKey: string): Promise<ModelInfo[]> {
  switch (provider) {
    case 'openai':
      return validateOpenAI(apiKey);
    case 'anthropic':
      return validateAnthropic(apiKey);
    case 'google':
      return validateGoogle(apiKey);
    default:
      throw new Error(`Unsupported provider: ${provider}`);
  }
}

async function validateOpenAI(apiKey: string): Promise<ModelInfo[]> {
  try {
    const openai = new OpenAI({ apiKey });
    
    // Test the API key by making a simple request
    const models = await openai.models.list();
    
    // Filter and return relevant models
    const relevantModels = models.data
      .filter(model => 
        model.id.includes('gpt-4') || 
        model.id.includes('gpt-3.5') ||
        model.id.includes('gpt-4o')
      )
      .map(model => ({
        id: model.id,
        name: model.id,
        description: getOpenAIModelDescription(model.id)
      }))
      .sort((a, b) => {
        // Sort GPT-4 models first
        if (a.id.includes('gpt-4') && !b.id.includes('gpt-4')) return -1;
        if (!a.id.includes('gpt-4') && b.id.includes('gpt-4')) return 1;
        return a.id.localeCompare(b.id);
      });

    return relevantModels.length > 0 ? relevantModels : [
      { id: 'gpt-4', name: 'GPT-4', description: 'Most capable model' },
      { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'Fast and efficient' }
    ];
  } catch (error) {
    throw new Error('Invalid OpenAI API key or network error');
  }
}

async function validateAnthropic(apiKey: string): Promise<ModelInfo[]> {
  try {
    const anthropic = new Anthropic({ apiKey });
    
    // Test the API key by making a simple request
    await anthropic.messages.create({
      model: 'claude-3-haiku-20240307',
      max_tokens: 1,
      messages: [{ role: 'user', content: 'Hi' }]
    });

    return [
      { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus', description: 'Most powerful model' },
      { id: 'claude-3-sonnet-20240229', name: 'Claude 3 Sonnet', description: 'Balanced performance' },
      { id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku', description: 'Fastest model' }
    ];
  } catch (error) {
    throw new Error('Invalid Anthropic API key or network error');
  }
}

async function validateGoogle(apiKey: string): Promise<ModelInfo[]> {
  try {
    const genAI = new GoogleGenerativeAI(apiKey);
    
    // Test the API key by getting a model
    const model = genAI.getGenerativeModel({ model: 'gemini-pro' });
    
    // Make a simple test request
    await model.generateContent('Hi');

    return [
      { id: 'gemini-pro', name: 'Gemini Pro', description: 'Most capable model' },
      { id: 'gemini-pro-vision', name: 'Gemini Pro Vision', description: 'Multimodal capabilities' }
    ];
  } catch (error) {
    throw new Error('Invalid Google API key or network error');
  }
}

function getOpenAIModelDescription(modelId: string): string {
  if (modelId.includes('gpt-4o')) return 'Latest multimodal model';
  if (modelId.includes('gpt-4-turbo')) return 'Fast GPT-4 variant';
  if (modelId.includes('gpt-4')) return 'Most capable model';
  if (modelId.includes('gpt-3.5-turbo')) return 'Fast and efficient';
  return '';
}

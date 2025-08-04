import fs from 'fs-extra';
import path from 'path';
import { ConfigManager } from './config';

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface ProjectContext {
  projectName: string;
  projectPath: string;
  messages: Message[];
  files: string[];
  gitInfo?: {
    branch: string;
    lastCommit: string;
  };
  createdAt: string;
  updatedAt: string;
}

export class ContextManager {
  private contextPath: string;
  private configManager: ConfigManager;

  constructor() {
    this.contextPath = path.join(process.cwd(), '.vibe', 'context.json');
    this.configManager = new ConfigManager();
  }

  async initializeContext(): Promise<void> {
    await fs.ensureDir(path.dirname(this.contextPath));
    
    if (!(await fs.pathExists(this.contextPath))) {
      const initialContext: ProjectContext = {
        projectName: path.basename(process.cwd()),
        projectPath: process.cwd(),
        messages: [],
        files: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      await this.saveContext(initialContext);
    }
  }

  async getContext(): Promise<ProjectContext> {
    try {
      if (await fs.pathExists(this.contextPath)) {
        return await fs.readJson(this.contextPath);
      }
      throw new Error('Context not initialized');
    } catch (error) {
      throw new Error('Failed to load context');
    }
  }

  async saveContext(context: ProjectContext): Promise<void> {
    context.updatedAt = new Date().toISOString();
    await fs.writeJson(this.contextPath, context, { spaces: 2 });
  }

  async addMessage(role: 'user' | 'assistant' | 'system', content: string): Promise<void> {
    const context = await this.getContext();
    
    const message: Message = {
      role,
      content,
      timestamp: new Date().toISOString()
    };
    
    context.messages.push(message);
    
    // Keep only last 50 messages to prevent context from growing too large
    if (context.messages.length > 50) {
      context.messages = context.messages.slice(-50);
    }
    
    await this.saveContext(context);
  }

  async getRecentContext(limit: number = 10): Promise<Message[]> {
    const context = await this.getContext();
    return context.messages.slice(-limit);
  }

  async clearMessages(): Promise<void> {
    const context = await this.getContext();
    context.messages = [];
    await this.saveContext(context);
  }

  async addFileToContext(filePath: string): Promise<void> {
    const context = await this.getContext();
    
    if (!context.files.includes(filePath)) {
      context.files.push(filePath);
      await this.saveContext(context);
    }
  }

  async removeFileFromContext(filePath: string): Promise<void> {
    const context = await this.getContext();
    context.files = context.files.filter(f => f !== filePath);
    await this.saveContext(context);
  }

  async updateGitInfo(): Promise<void> {
    try {
      const simpleGit = require('simple-git');
      const git = simpleGit(process.cwd());
      
      const branch = await git.revparse(['--abbrev-ref', 'HEAD']);
      const lastCommit = await git.log(['-1', '--pretty=format:%h %s']);
      
      const context = await this.getContext();
      context.gitInfo = {
        branch: branch.trim(),
        lastCommit: lastCommit.latest?.hash + ' ' + lastCommit.latest?.message || 'No commits'
      };
      
      await this.saveContext(context);
    } catch (error) {
      // Git info is optional, don't fail if git is not available
      console.debug('Could not update git info:', error);
    }
  }

  async getProjectSummary(): Promise<string> {
    const context = await this.getContext();
    
    let summary = `Project: ${context.projectName}\n`;
    summary += `Path: ${context.projectPath}\n`;
    summary += `Messages: ${context.messages.length}\n`;
    summary += `Tracked files: ${context.files.length}\n`;
    
    if (context.gitInfo) {
      summary += `Git branch: ${context.gitInfo.branch}\n`;
      summary += `Last commit: ${context.gitInfo.lastCommit}\n`;
    }
    
    summary += `Created: ${new Date(context.createdAt).toLocaleString()}\n`;
    summary += `Updated: ${new Date(context.updatedAt).toLocaleString()}`;
    
    return summary;
  }
}

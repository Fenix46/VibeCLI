import fs from 'fs-extra';
import path from 'path';
import os from 'os';

export interface VibeConfig {
  provider: 'openai' | 'anthropic' | 'google';
  apiKey: string;
  model: string;
  setupComplete: boolean;
  createdAt: string;
  lastUsed?: string;
}

export class ConfigManager {
  private configDir: string;
  private configPath: string;
  private projectConfigPath: string;

  constructor() {
    // Global config in user home directory
    this.configDir = path.join(os.homedir(), '.vibe');
    this.configPath = path.join(this.configDir, 'config.json');
    
    // Project-specific config in current working directory
    this.projectConfigPath = path.join(process.cwd(), '.vibe', 'project.json');
  }

  async ensureConfigDir(): Promise<void> {
    await fs.ensureDir(this.configDir);
    await fs.ensureDir(path.join(process.cwd(), '.vibe'));
  }

  async saveConfig(config: VibeConfig): Promise<void> {
    await this.ensureConfigDir();
    await fs.writeJson(this.configPath, config, { spaces: 2 });
  }

  async loadConfig(): Promise<VibeConfig | null> {
    try {
      if (await fs.pathExists(this.configPath)) {
        return await fs.readJson(this.configPath);
      }
      return null;
    } catch (error) {
      console.error('Error loading config:', error);
      return null;
    }
  }

  async saveProjectConfig(projectData: any): Promise<void> {
    await this.ensureConfigDir();
    const projectConfig = {
      ...projectData,
      updatedAt: new Date().toISOString()
    };
    await fs.writeJson(this.projectConfigPath, projectConfig, { spaces: 2 });
  }

  async loadProjectConfig(): Promise<any> {
    try {
      if (await fs.pathExists(this.projectConfigPath)) {
        return await fs.readJson(this.projectConfigPath);
      }
      return {};
    } catch (error) {
      console.error('Error loading project config:', error);
      return {};
    }
  }

  async isSetupComplete(): Promise<boolean> {
    const config = await this.loadConfig();
    return config?.setupComplete === true;
  }

  async updateLastUsed(): Promise<void> {
    const config = await this.loadConfig();
    if (config) {
      config.lastUsed = new Date().toISOString();
      await this.saveConfig(config);
    }
  }
}

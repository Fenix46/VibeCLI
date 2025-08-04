import fs from 'fs-extra';
import path from 'path';

export class FileTools {
  static async readFile(filePath: string): Promise<string> {
    try {
      const fullPath = path.resolve(filePath);
      return await fs.readFile(fullPath, 'utf-8');
    } catch (error) {
      throw new Error(`Failed to read file ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  static async writeFile(filePath: string, content: string): Promise<void> {
    try {
      const fullPath = path.resolve(filePath);
      await fs.ensureDir(path.dirname(fullPath));
      await fs.writeFile(fullPath, content, 'utf-8');
    } catch (error) {
      throw new Error(`Failed to write file ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  static async listDirectory(dirPath: string): Promise<string[]> {
    try {
      const fullPath = path.resolve(dirPath);
      const items = await fs.readdir(fullPath);
      return items;
    } catch (error) {
      throw new Error(`Failed to list directory ${dirPath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  static async fileExists(filePath: string): Promise<boolean> {
    try {
      const fullPath = path.resolve(filePath);
      return await fs.pathExists(fullPath);
    } catch (error) {
      return false;
    }
  }

  static async getFileStats(filePath: string): Promise<any> {
    try {
      const fullPath = path.resolve(filePath);
      const stats = await fs.stat(fullPath);
      return {
        size: stats.size,
        isFile: stats.isFile(),
        isDirectory: stats.isDirectory(),
        modified: stats.mtime,
        created: stats.birthtime
      };
    } catch (error) {
      throw new Error(`Failed to get file stats for ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  static async searchInFile(filePath: string, searchTerm: string): Promise<{ line: number; content: string }[]> {
    try {
      const content = await this.readFile(filePath);
      const lines = content.split('\n');
      const matches: { line: number; content: string }[] = [];

      lines.forEach((line, index) => {
        if (line.toLowerCase().includes(searchTerm.toLowerCase())) {
          matches.push({
            line: index + 1,
            content: line.trim()
          });
        }
      });

      return matches;
    } catch (error) {
      throw new Error(`Failed to search in file ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  static async createDirectory(dirPath: string): Promise<void> {
    try {
      const fullPath = path.resolve(dirPath);
      await fs.ensureDir(fullPath);
    } catch (error) {
      throw new Error(`Failed to create directory ${dirPath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  static async deleteFile(filePath: string): Promise<void> {
    try {
      const fullPath = path.resolve(filePath);
      await fs.remove(fullPath);
    } catch (error) {
      throw new Error(`Failed to delete ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  static async copyFile(sourcePath: string, destPath: string): Promise<void> {
    try {
      const fullSourcePath = path.resolve(sourcePath);
      const fullDestPath = path.resolve(destPath);
      await fs.ensureDir(path.dirname(fullDestPath));
      await fs.copy(fullSourcePath, fullDestPath);
    } catch (error) {
      throw new Error(`Failed to copy ${sourcePath} to ${destPath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}

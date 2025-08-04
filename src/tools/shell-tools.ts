import { exec, spawn } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export interface CommandResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

export class ShellTools {
  static async executeCommand(command: string, cwd?: string): Promise<CommandResult> {
    try {
      const options = cwd ? { cwd } : {};
      const { stdout, stderr } = await execAsync(command, options);
      
      return {
        stdout: stdout.toString(),
        stderr: stderr.toString(),
        exitCode: 0
      };
    } catch (error: any) {
      return {
        stdout: error.stdout ? error.stdout.toString() : '',
        stderr: error.stderr ? error.stderr.toString() : error.message,
        exitCode: error.code || 1
      };
    }
  }

  static async executeCommandStream(
    command: string, 
    args: string[] = [], 
    cwd?: string,
    onData?: (data: string) => void
  ): Promise<CommandResult> {
    return new Promise((resolve) => {
      const options = cwd ? { cwd } : {};
      const child = spawn(command, args, options);
      
      let stdout = '';
      let stderr = '';

      child.stdout?.on('data', (data) => {
        const output = data.toString();
        stdout += output;
        if (onData) onData(output);
      });

      child.stderr?.on('data', (data) => {
        const output = data.toString();
        stderr += output;
        if (onData) onData(output);
      });

      child.on('close', (code) => {
        resolve({
          stdout,
          stderr,
          exitCode: code || 0
        });
      });

      child.on('error', (error) => {
        resolve({
          stdout,
          stderr: error.message,
          exitCode: 1
        });
      });
    });
  }

  static async getEnvironmentVariable(name: string): Promise<string | undefined> {
    return process.env[name];
  }

  static async setEnvironmentVariable(name: string, value: string): Promise<void> {
    process.env[name] = value;
  }

  static async getCurrentDirectory(): Promise<string> {
    return process.cwd();
  }

  static async changeDirectory(path: string): Promise<void> {
    try {
      process.chdir(path);
    } catch (error) {
      throw new Error(`Failed to change directory to ${path}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  static async getSystemInfo(): Promise<any> {
    const os = require('os');
    
    return {
      platform: os.platform(),
      arch: os.arch(),
      release: os.release(),
      hostname: os.hostname(),
      uptime: os.uptime(),
      loadavg: os.loadavg(),
      totalmem: os.totalmem(),
      freemem: os.freemem(),
      cpus: os.cpus().length,
      nodeVersion: process.version
    };
  }

  static async findProcess(name: string): Promise<any[]> {
    try {
      const result = await this.executeCommand(`ps aux | grep "${name}" | grep -v grep`);
      
      if (result.exitCode === 0 && result.stdout.trim()) {
        return result.stdout.trim().split('\n').map(line => {
          const parts = line.trim().split(/\s+/);
          return {
            user: parts[0],
            pid: parts[1],
            cpu: parts[2],
            mem: parts[3],
            command: parts.slice(10).join(' ')
          };
        });
      }
      
      return [];
    } catch (error) {
      throw new Error(`Failed to find process ${name}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  static async killProcess(pid: string | number): Promise<void> {
    try {
      const result = await this.executeCommand(`kill ${pid}`);
      if (result.exitCode !== 0) {
        throw new Error(result.stderr || 'Failed to kill process');
      }
    } catch (error) {
      throw new Error(`Failed to kill process ${pid}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  static async checkCommandExists(command: string): Promise<boolean> {
    try {
      const result = await this.executeCommand(`which ${command}`);
      return result.exitCode === 0;
    } catch (error) {
      return false;
    }
  }

  static async getDirectorySize(path: string): Promise<string> {
    try {
      const result = await this.executeCommand(`du -sh "${path}"`);
      if (result.exitCode === 0) {
        return result.stdout.split('\t')[0].trim();
      }
      throw new Error(result.stderr);
    } catch (error) {
      throw new Error(`Failed to get directory size: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}

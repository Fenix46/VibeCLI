import { FileTools } from './file-tools';
import { GitTools } from './git-tools';
import { ShellTools } from './shell-tools';

export interface Tool {
  name: string;
  description: string;
  parameters: any;
  execute: (args: any) => Promise<string>;
}

export class ToolRegistry {
  private tools: Map<string, Tool> = new Map();
  private fileTools: FileTools;
  private gitTools: GitTools;
  private shellTools: ShellTools;

  constructor() {
    this.fileTools = new FileTools();
    this.gitTools = new GitTools();
    this.shellTools = new ShellTools();
    this.registerTools();
  }

  private registerTools(): void {
    // File Tools
    this.registerTool({
      name: 'read_file',
      description: 'Read the contents of a file',
      parameters: {
        type: 'object',
        properties: {
          filePath: {
            type: 'string',
            description: 'Path to the file to read'
          }
        },
        required: ['filePath']
      },
      execute: async (args) => {
        return await FileTools.readFile(args.filePath);
      }
    });

    this.registerTool({
      name: 'write_file',
      description: 'Write content to a file',
      parameters: {
        type: 'object',
        properties: {
          filePath: {
            type: 'string',
            description: 'Path to the file to write'
          },
          content: {
            type: 'string',
            description: 'Content to write to the file'
          }
        },
        required: ['filePath', 'content']
      },
      execute: async (args) => {
        await FileTools.writeFile(args.filePath, args.content);
        return `File ${args.filePath} written successfully`;
      }
    });

    this.registerTool({
      name: 'list_directory',
      description: 'List contents of a directory',
      parameters: {
        type: 'object',
        properties: {
          dirPath: {
            type: 'string',
            description: 'Path to the directory to list'
          }
        },
        required: ['dirPath']
      },
      execute: async (args) => {
        const items = await FileTools.listDirectory(args.dirPath);
        return `Directory contents: ${items.join(', ')}`;
      }
    });

    this.registerTool({
      name: 'search_in_file',
      description: 'Search for a term in a file',
      parameters: {
        type: 'object',
        properties: {
          filePath: {
            type: 'string',
            description: 'Path to the file to search in'
          },
          searchTerm: {
            type: 'string',
            description: 'Term to search for'
          }
        },
        required: ['filePath', 'searchTerm']
      },
      execute: async (args) => {
        const matches = await FileTools.searchInFile(args.filePath, args.searchTerm);
        return `Found ${matches.length} matches: ${JSON.stringify(matches)}`;
      }
    });

    // Git Tools
    this.registerTool({
      name: 'git_status',
      description: 'Get git repository status',
      parameters: {
        type: 'object',
        properties: {}
      },
      execute: async () => {
        const status = await this.gitTools.getStatus();
        return `Git status: ${JSON.stringify(status, null, 2)}`;
      }
    });

    this.registerTool({
      name: 'git_add',
      description: 'Add files to git staging area',
      parameters: {
        type: 'object',
        properties: {
          files: {
            type: 'array',
            items: { type: 'string' },
            description: 'Files to add (default: all files)'
          }
        }
      },
      execute: async (args) => {
        await this.gitTools.addFiles(args.files || ['.']);
        return `Files added to staging area`;
      }
    });

    this.registerTool({
      name: 'git_commit',
      description: 'Commit changes to git repository',
      parameters: {
        type: 'object',
        properties: {
          message: {
            type: 'string',
            description: 'Commit message'
          }
        },
        required: ['message']
      },
      execute: async (args) => {
        const result = await this.gitTools.commit(args.message);
        return `Commit created: ${result.commit}`;
      }
    });

    this.registerTool({
      name: 'git_log',
      description: 'Get git commit history',
      parameters: {
        type: 'object',
        properties: {
          maxCount: {
            type: 'number',
            description: 'Maximum number of commits to show (default: 10)'
          }
        }
      },
      execute: async (args) => {
        const log = await this.gitTools.getLog(args.maxCount || 10);
        return `Recent commits: ${JSON.stringify(log.all.map((c: any) => ({ hash: c.hash, message: c.message, date: c.date })))}`;
      }
    });

    this.registerTool({
      name: 'create_branch',
      description: 'Create and switch to a new git branch',
      parameters: {
        type: 'object',
        properties: {
          branchName: {
            type: 'string',
            description: 'Name of the new branch'
          }
        },
        required: ['branchName']
      },
      execute: async (args) => {
        await this.gitTools.createBranch(args.branchName);
        return `Created and switched to branch: ${args.branchName}`;
      }
    });

    // Shell Tools
    this.registerTool({
      name: 'execute_command',
      description: 'Execute a shell command',
      parameters: {
        type: 'object',
        properties: {
          command: {
            type: 'string',
            description: 'Shell command to execute'
          },
          cwd: {
            type: 'string',
            description: 'Working directory for the command (optional)'
          }
        },
        required: ['command']
      },
      execute: async (args) => {
        const result = await ShellTools.executeCommand(args.command, args.cwd);
        return `Command executed (exit code: ${result.exitCode}):\nSTDOUT: ${result.stdout}\nSTDERR: ${result.stderr}`;
      }
    });

    this.registerTool({
      name: 'get_system_info',
      description: 'Get system information',
      parameters: {
        type: 'object',
        properties: {}
      },
      execute: async () => {
        const info = await ShellTools.getSystemInfo();
        return `System info: ${JSON.stringify(info, null, 2)}`;
      }
    });
  }

  private registerTool(tool: Tool): void {
    this.tools.set(tool.name, tool);
  }

  getAvailableTools(): string[] {
    return Array.from(this.tools.keys());
  }

  getTool(name: string): Tool | undefined {
    return this.tools.get(name);
  }

  async executeTool(name: string, args: any): Promise<string> {
    const tool = this.tools.get(name);
    if (!tool) {
      throw new Error(`Tool ${name} not found`);
    }
    return await tool.execute(args);
  }

  getOpenAITools(): any[] {
    return Array.from(this.tools.values()).map(tool => ({
      type: 'function',
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.parameters
      }
    }));
  }

  getAnthropicTools(): any[] {
    return Array.from(this.tools.values()).map(tool => ({
      name: tool.name,
      description: tool.description,
      input_schema: tool.parameters
    }));
  }
}

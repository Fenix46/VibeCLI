import simpleGit, { SimpleGit } from 'simple-git';

export class GitTools {
  private git: SimpleGit;

  constructor(workingDir: string = process.cwd()) {
    this.git = simpleGit(workingDir);
  }

  async getStatus(): Promise<any> {
    try {
      return await this.git.status();
    } catch (error) {
      throw new Error(`Failed to get git status: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getCurrentBranch(): Promise<string> {
    try {
      const branches = await this.git.branch();
      return branches.current;
    } catch (error) {
      throw new Error(`Failed to get current branch: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async listBranches(): Promise<string[]> {
    try {
      const branches = await this.git.branch();
      return branches.all;
    } catch (error) {
      throw new Error(`Failed to list branches: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async createBranch(branchName: string): Promise<void> {
    try {
      await this.git.checkoutLocalBranch(branchName);
    } catch (error) {
      throw new Error(`Failed to create branch ${branchName}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async switchBranch(branchName: string): Promise<void> {
    try {
      await this.git.checkout(branchName);
    } catch (error) {
      throw new Error(`Failed to switch to branch ${branchName}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async addFiles(files: string[] = ['.']): Promise<void> {
    try {
      await this.git.add(files);
    } catch (error) {
      throw new Error(`Failed to add files: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async commit(message: string): Promise<any> {
    try {
      return await this.git.commit(message);
    } catch (error) {
      throw new Error(`Failed to commit: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getLog(maxCount: number = 10): Promise<any> {
    try {
      return await this.git.log({ maxCount });
    } catch (error) {
      throw new Error(`Failed to get git log: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getDiff(cached: boolean = false): Promise<string> {
    try {
      return await this.git.diff(cached ? ['--cached'] : []);
    } catch (error) {
      throw new Error(`Failed to get diff: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async pull(remote: string = 'origin', branch?: string): Promise<any> {
    try {
      return await this.git.pull(remote, branch);
    } catch (error) {
      throw new Error(`Failed to pull: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async push(remote: string = 'origin', branch?: string): Promise<any> {
    try {
      return await this.git.push(remote, branch);
    } catch (error) {
      throw new Error(`Failed to push: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async isRepo(): Promise<boolean> {
    try {
      await this.git.status();
      return true;
    } catch (error) {
      return false;
    }
  }

  async initRepo(): Promise<void> {
    try {
      await this.git.init();
    } catch (error) {
      throw new Error(`Failed to initialize git repository: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getRemotes(): Promise<any[]> {
    try {
      return await this.git.getRemotes(true);
    } catch (error) {
      throw new Error(`Failed to get remotes: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async addRemote(name: string, url: string): Promise<void> {
    try {
      await this.git.addRemote(name, url);
    } catch (error) {
      throw new Error(`Failed to add remote ${name}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}

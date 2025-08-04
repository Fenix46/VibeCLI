# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Build and Development
- `npm run build` - Compile TypeScript to JavaScript in dist/
- `npm run dev` - Run in development mode with ts-node
- `npm run watch` - Build in watch mode for development
- `npm run clean` - Clean the dist/ directory
- `npm start` - Run the compiled JavaScript version

### Package Management
- `npm run prepare` - Automatically run build before npm operations
- `npm run prepublishOnly` - Run before publishing to npm
- `npm run publish:script` - Execute publishing script

### Version Management
- `npm run version:patch` - Increment patch version
- `npm run version:minor` - Increment minor version  
- `npm run version:major` - Increment major version

### Testing and Quality
- No linting or testing commands currently configured (both return exit 0)

## Project Architecture

### Core Structure
VibeCli is an AI terminal agent built with TypeScript that provides streaming AI interactions with integrated tool execution:

```
src/
├── index.ts              # Main CLI entry point with Commander.js
├── cli/                  # CLI command implementations
│   ├── chat.ts          # Interactive and single-message chat
│   ├── setup.ts         # Initial configuration wizard
│   ├── context.ts       # Project context management
│   └── tools.ts         # Tool listing and help
├── core/                # Core business logic
│   ├── config.ts        # Global and project configuration
│   ├── context.ts       # Project memory and message history
│   └── prompts.ts       # AI prompt templates
├── providers/           # AI provider integrations
│   ├── ai-provider.ts   # Basic AI provider (non-streaming)
│   └── streaming-provider.ts # Advanced streaming provider with tools
└── tools/               # Integrated tool system
    ├── file-tools.ts    # File operations (read, write, list, search)
    ├── git-tools.ts     # Git operations (status, commit, branch)
    ├── shell-tools.ts   # Shell command execution
    └── tool-registry.ts # Unified tool registration and execution
```

### Key Architectural Patterns

#### Dual Provider System
- `AIProvider`: Basic request/response for simple operations
- `StreamingAIProvider`: Advanced streaming with tool integration and real-time feedback

#### Tool Integration
- Function calling support for OpenAI and Anthropic
- Unified tool registry with standardized execution
- Automatic tool result processing and display

#### Context Management
- Global config in `~/.vibe/config.json`
- Per-project context in `.vibe/context.json` and `.vibe/project.json`
- Message history with automatic pruning (50 message limit)
- Git integration for project metadata

#### Multi-Provider Support
Supports OpenAI, Anthropic (Claude), and Google (Gemini) with provider-specific optimizations:
- OpenAI: Full streaming with tool calls
- Anthropic: Streaming with tool support
- Google: Basic streaming (no tool calls)

### Configuration System
- Interactive setup wizard for API keys and model selection
- Validation of API keys during setup
- Project-specific context persistence
- Global configuration management

### CLI Commands
- `vibe setup` - Configure AI provider and API keys
- `vibe chat` - Start interactive chat or send single message (-m flag)
- `vibe context` - Manage project context (--show, --clear, --reset)
- `vibe tools` - List available tools (--list)

### Binary Configuration
The `bin/vibe` script intelligently switches between:
- Production: Uses compiled JavaScript from dist/
- Development: Uses ts-node for TypeScript execution

## Dependencies

### Runtime Dependencies
- `commander` - CLI framework
- `inquirer` - Interactive prompts
- `chalk` - Terminal colors
- `ora` - Loading spinners
- AI SDKs: `openai`, `@anthropic-ai/sdk`, `@google/generative-ai`
- `simple-git` - Git operations
- `fs-extra` - Enhanced file system operations

### Development Dependencies
- `typescript` - TypeScript compiler
- `ts-node` - TypeScript execution for development
- Type definitions for Node.js and dependencies

## Development Notes

### Build Process
- Compiles to CommonJS modules in dist/
- Generates declaration files and source maps
- Excludes test files and node_modules

### Package Publishing
- Configured as scoped package `@vibecli/core`
- Includes only essential files (dist/, bin/, README, LICENSE)
- Public access configured for npm publishing

### Error Handling
- Graceful fallbacks for missing configurations
- Tool execution error containment
- Provider-specific error handling in streaming

### Performance Considerations
- Streaming responses for immediate user feedback
- Message history pruning to prevent context bloat
- Lazy loading of AI provider SDKs
- Async tool execution with parallel processing where possible
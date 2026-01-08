# local

A production-grade, cross-platform CLI to run local llama-server models with chat, coding agent, tasks, and model management.

## Install

```bash
npm install
npm run build
npm link
```

Run:

```bash
local --help
```

## Quick Start

```bash
local model search mistral
local model install TheBloke/Mistral-7B-Instruct-v0.2-GGUF --file mistral-7b-instruct-v0.2.Q4_K_M.gguf
local model list
local chat
```

## Commands

- `local chat` interactive chat REPL
- `local code` agentic coding REPL
- `local model search <query>`
- `local model install <repo_id> [--file <gguf_filename>]`
- `local model list`
- `local model remove <id>`
- `local model set-default <id>`
- `local server start|stop|status|logs`
- `local task create|list|run|delete|tick`
- `local doctor`

## Safety

- Destructive commands require confirmation.
- `local code` only writes inside repo root unless you explicitly approve.
- Use `--dry-run` with `local code` to see diffs and commands without applying.

## Config + State

Stored in OS-appropriate config directories:

- Linux: `~/.config/local`
- macOS: `~/Library/Application Support/local`
- Windows: `%APPDATA%/local`

Files:

- `config.json` default model, server port, ctx size, gpu layers, idle timeout
- `models.json` installed model registry
- `tasks.json` tasks and run history
- `sessions/` chat and code transcripts
- `logs/` structured logs and llama-server logs

## Assumptions

- `llama-server` is installed and available in PATH (or set `llamaServerPath` in `config.json`).
- Hugging Face API is reachable; set `HF_TOKEN` for higher rate limits/private repos.

## Notes

- The coding agent uses a strict JSON tool protocol.
- `local task tick` triggers interval-based schedules without requiring background services.

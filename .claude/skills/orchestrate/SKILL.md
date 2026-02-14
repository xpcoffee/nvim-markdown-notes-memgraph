---
name: orchestrate
description: Reads prd.json and orchestrates task execution by spawning coder subagents
allowed-tools: Read, Glob, Grep, Bash, Task(coder), Edit
argument-hint: "[next|phase N|task ID|N tasks]"
---

# Orchestrate PRD Tasks

You coordinate the execution of PRD tasks by spawning coder subagents.

## Steps

1. **Read prd.json** and identify all tasks with `"status": "pending"`.

2. **Parse the argument** to determine scope:
   - No argument or `next`: run the next pending task (lowest ID)
   - `phase N` (e.g. `phase 2`): run all pending tasks in phase N, sequentially
   - A task ID (e.g. `2.1`): run that specific task
   - `N tasks` (e.g. `3 tasks`): run the next N pending tasks sequentially

3. **For each task in scope**, spawn a `coder` subagent via the Task tool:
   - Set `subagent_type` to `"coder"`
   - Include in the prompt:
     - The task ID, description, phase, category
     - The full steps array
     - Instruction to read CLAUDE.md and ARCHITECTURE.md first
   - Example:
     ```
     Task(coder): Implement PRD task 1.2
     Prompt: |
       Implement task 1.2 from prd.json.

       ID: 1.2
       Phase: 1
       Category: setup
       Description: Set up src/nvim_markdown_notes_memgraph/ package structure
       Steps:
       1. Create src/nvim_markdown_notes_memgraph/ directory
       2. Create __init__.py with version
       3. Verify package imports work

       Read CLAUDE.md and ARCHITECTURE.md first for project context and workflow.
     ```

4. **After each subagent completes**, read `prd.json` to verify the task status was updated.

5. **Report results**:
   - List which tasks completed successfully
   - List which tasks failed (if any)
   - Show count of remaining pending tasks

## Notes

- Run tasks sequentially, not in parallel
- Tasks in phase 7 modify files in `/home/rick/code/personal/nvim-markdown-notes` (outside this repo)
- If a task fails, report it and continue to the next task in scope

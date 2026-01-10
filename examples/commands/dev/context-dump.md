---
description: Dump current project context (git, env, structure)
argument-hint: "[depth:2]"
allowed-tools: [bash]
max-chars: 8000
---

Here's the current project context:

## Git Status
!`git status --short 2>/dev/null || echo "Not a git repo"`

## Recent Commits
!`git log --oneline -5 2>/dev/null || echo "No git history"`

## Current Branch
!`git branch --show-current 2>/dev/null || echo "N/A"`

## Directory Structure
!`find . -maxdepth {{$1 or "2"}} -type f -name "*.py" -o -type f -name "*.md" -o -type f -name "*.yaml" 2>/dev/null | head -30 | sort`

## Python Environment
!`python --version 2>/dev/null && pip list 2>/dev/null | head -10 || echo "No Python env"`

Based on this context, what would you like to know or do?

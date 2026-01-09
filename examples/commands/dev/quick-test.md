---
description: Run tests for a specific file or module and analyze failures
argument-hint: "[test-path]"
---

Run tests for {{$1 or "the current directory"}} and provide analysis.

Steps:
1. Run `pytest {{$1 or "."}} -v --tb=short 2>&1 | head -100`
2. If there are failures:
   - Summarize what failed and why
   - Look at the relevant source code
   - Suggest fixes for failing tests
3. If all tests pass:
   - Report the count of passing tests
   - Note any warnings or slow tests

Keep the output focused on actionable information.

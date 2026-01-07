---
description: Generate comprehensive unit tests
allowed-tools: [read_file, write_file, task]
argument-hint: [file-path]
---

Analyze {{$1 or "the current code"}} and generate comprehensive unit tests covering:

## Test Coverage Areas
1. **Happy Path**: Normal execution scenarios with valid inputs
2. **Edge Cases**: Boundary conditions, empty inputs, null values
3. **Error Conditions**: Invalid inputs, exceptions, error handling
4. **Integration Points**: Mock external dependencies appropriately

## Test Structure
- Use clear, descriptive test names
- Follow Arrange-Act-Assert pattern
- One assertion per test when possible
- Include setup and teardown as needed

## Best Practices
- Test behavior, not implementation details
- Make tests independent and repeatable
- Use fixtures for common setup
- Include docstrings explaining test purpose

Generate tests using the project's testing framework and conventions.

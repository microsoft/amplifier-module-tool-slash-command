---
description: Generate comprehensive documentation
allowed-tools: [read_file, write_file]
argument-hint: [file-or-module]
---

Generate comprehensive documentation for {{$1 or "the code"}}:

## Documentation Requirements

### Module/File Overview
- Purpose and responsibilities
- Key components and their relationships
- Usage examples

### Public API Documentation
For each public function/class/method:
- Clear description of purpose
- Parameters with types and descriptions
- Return value with type and description
- Exceptions that may be raised
- Usage examples
- Notes on thread safety, performance, or other important considerations

### Code Examples
Provide realistic, runnable examples showing:
- Basic usage
- Common use cases
- Error handling
- Integration with other components

### Architecture Decisions
Document why things are implemented the way they are:
- Design choices and trade-offs
- Alternative approaches considered
- Future considerations

## Documentation Format
Use the project's standard documentation format:
- Docstrings for functions/classes
- README.md for modules
- Inline comments for complex logic only

Focus on the "why" and "how to use" rather than "what" (which should be obvious from well-named code).

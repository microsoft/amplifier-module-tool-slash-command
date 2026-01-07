---
description: Analyze code for performance optimization opportunities
allowed-tools: [read_file, grep]
argument-hint: [file-path]
---

Analyze {{$1 or "the code"}} for performance optimization opportunities:

## Performance Analysis Areas

### Algorithmic Efficiency
- Time complexity analysis (Big O notation)
- Space complexity considerations
- Algorithm selection (can we use a better algorithm?)

### Data Structures
- Appropriate data structure usage
- Unnecessary data copying or transformations
- Cache-friendly access patterns

### I/O Operations
- Batch operations where possible
- Async/await usage for I/O-bound work
- Connection pooling and reuse

### Database Queries
- N+1 query problems
- Missing indexes
- Query optimization opportunities
- Unnecessary data fetching

### Resource Management
- Memory leaks or excessive allocations
- File handle/connection management
- Thread/process pool efficiency

### Caching
- Computation result caching
- Database query result caching
- HTTP response caching

Provide specific recommendations with estimated performance impact (High, Medium, Low) and implementation complexity.

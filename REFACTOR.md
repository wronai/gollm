# GoLLM Refactoring Plan

## Overview

This document outlines a comprehensive refactoring plan for the GoLLM project, focusing on:

1. Modularizing large files into smaller, more maintainable components
2. Creating reusable, independent Python packages
3. Reducing code duplication
4. Flattening the project hierarchy
5. Improving performance
6. Enhancing logging and debugging capabilities

## Performance Issues

The main performance bottleneck identified is that direct curl requests to the Ollama API are faster than using the `gollm -v generate` command. This is due to multiple layers of processing:
- Context building
- Prompt formatting
- Validation
- Response processing

## Files Requiring Refactoring (Over 300 Lines)

1. `ollama_adapter.py` (717 lines)
2. `cli.py` (560 lines)
3. `ollama/provider.py` (439 lines)
4. `project_management/todo_manager.py` (368 lines)
5. `ollama/adapter.py` (355 lines)

## Independent Package Structure

We will extract the following independent packages that can be reused across projects:

### 1. `wronai-llm-core`

Core LLM functionality independent of specific providers:

```
wronai-llm-core/
├── pyproject.toml
├── README.md
└── src/
    └── wronai/
        └── llm/
            ├── __init__.py
            ├── base_provider.py
            ├── context_builder.py
            ├── prompt_formatter.py
            ├── response_validator.py
            └── router.py
```

### 2. `wronai-code-quality`

Code validation, quality checking, and improvement tools:

```
wronai-code-quality/
├── pyproject.toml
├── README.md
└── src/
    └── wronai/
        └── code_quality/
            ├── __init__.py
            ├── validators/
            │   ├── __init__.py
            │   ├── python_validator.py
            │   └── generic_validator.py
            ├── fixers/
            │   ├── __init__.py
            │   └── syntax_fixer.py
            └── metrics/
                ├── __init__.py
                └── quality_metrics.py
```

### 3. `wronai-logging`

Advanced logging, monitoring and debugging tools:

```
wronai-logging/
├── pyproject.toml
├── README.md
└── src/
    └── wronai/
        └── logging/
            ├── __init__.py
            ├── formatters.py
            ├── handlers.py
            ├── aggregator.py
            └── execution_capture.py
```

### 4. `wronai-ollama`

Ollama-specific client libraries:

```
wronai-ollama/
├── pyproject.toml
├── README.md
└── src/
    └── wronai/
        └── ollama/
            ├── __init__.py
            ├── client.py
            ├── modules/
            │   ├── __init__.py
            │   ├── generation/
            │   ├── prompt/
            │   ├── model/
            │   ├── health/
            │   └── config/
            └── transport/
                ├── __init__.py
                ├── http.py
                └── grpc.py
```

## Specific Refactoring Tasks

### 1. Ollama Adapter Refactoring

Split `ollama_adapter.py` into modular components:

1. **Prompt Formatting and Processing**
   - Extract prompt formatting logic
   - Create standardized prompt templates
   - Implement context management

2. **Model Management**
   - Model information retrieval
   - Model selection and validation
   - Model configuration handling

3. **Generation Operations**
   - Text generation (completion)
   - Chat generation
   - Streaming support
   - Error handling

4. **Health Check and Status Monitoring**
   - Service availability checks
   - Model availability validation
   - Performance metrics collection
   - Diagnostics

5. **Configuration Handling**
   - Configuration loading and validation
   - Default settings management
   - Environment variable integration

### 2. CLI Refactoring

Split `cli.py` into logical command groups:

1. **Core Commands**
   - Generate
   - Validate
   - Config

2. **Project Management Commands**
   - Todo
   - Status
   - Metrics

3. **Development Commands**
   - Debug
   - Benchmark
   - Test

### 3. Provider Refactoring

Create a consistent provider interface:

1. **Base Provider Interface**
   - Standard methods for all providers
   - Common configuration handling
   - Error standardization

2. **Provider-Specific Implementations**
   - Ollama
   - OpenAI
   - Anthropic
   - Others

### 4. Project Management Refactoring

Improve the todo manager:

1. **Task Management**
   - Task creation and tracking
   - Priority handling
   - Status updates

2. **Integration**
   - Git integration
   - IDE integration
   - Notification system

## Implementation Plan

### Phase 1: Modularization of Existing Code

1. Create the module structure for Ollama adapter components
2. Extract code from large files into appropriate modules
3. Ensure tests pass after refactoring
4. Update documentation

### Phase 2: Independent Package Creation

1. Set up package scaffolding with Poetry
2. Move generic code to independent packages
3. Update dependencies in main project
4. Create comprehensive documentation for each package

### Phase 3: Performance Optimization

1. Identify and eliminate bottlenecks
2. Implement caching where appropriate
3. Optimize API calls and response handling
4. Benchmark before and after to measure improvements

### Phase 4: Integration and Testing

1. Ensure all components work together seamlessly
2. Create integration tests
3. Update user documentation
4. Release new version

## Coding Standards

- Use Black for code formatting
- Maintain comprehensive docstrings
- Follow PEP 8 guidelines
- Implement proper type hints
- Ensure test coverage for all new code

## Logging and Debugging

- Implement consistent logging across all modules
- Add debug levels for development
- Create log aggregation for complex operations
- Ensure errors are properly captured and reported

## Migration Strategy

1. Develop new modules alongside existing code
2. Create adapter patterns to maintain backward compatibility
3. Gradually transition to new architecture
4. Deprecate old modules with clear notices
5. Provide migration guides for users

## Timeline

- Phase 1: 2 weeks
- Phase 2: 3 weeks
- Phase 3: 1 week
- Phase 4: 2 weeks

Total estimated time: 8 weeks

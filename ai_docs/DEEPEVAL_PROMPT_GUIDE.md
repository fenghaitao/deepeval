# DeepEval Prompt Management System - Complete Guide

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Prompt Class](#prompt-class)
4. [Prompt Types](#prompt-types)
5. [Interpolation Methods](#interpolation-methods)
6. [Model Settings](#model-settings)
7. [Output Configuration](#output-configuration)
8. [Pull, Push, Update Operations](#pull-push-update-operations)
9. [Caching System](#caching-system)
10. [Auto-Refresh Polling](#auto-refresh-polling)
11. [Usage Examples](#usage-examples)
12. [Best Practices](#best-practices)

---

## Overview

DeepEval's prompt management system provides a centralized way to manage, version, and deploy prompts for LLM applications. It integrates with Confident AI's cloud platform for:

- **Version control** for prompts
- **Centralized management** across teams
- **A/B testing** with labels
- **Auto-refresh** for dynamic prompt updates
- **Local caching** for offline/fallback support
- **Structured outputs** with Pydantic schemas

---

## Core Concepts

### Prompt Versioning

Every prompt has:
- **Alias**: Unique identifier (e.g., "customer-support-prompt")
- **Version**: Numeric version (e.g., "1", "2", "3", "latest")
- **Label**: Named version for A/B testing (e.g., "production", "experimental")

### Prompt Storage

Prompts can be stored in three places:
1. **Confident AI Cloud** - Central source of truth
2. **Local Cache** - JSON file at `.deepeval/.deepeval-prompt-cache.json`
3. **In-Memory** - Active prompt instance

---

## Prompt Class

The `Prompt` class is the main interface for prompt management.

### Initialization

```python
from deepeval.prompt import Prompt, PromptMessage, ModelSettings, OutputType

# Create a new prompt
prompt = Prompt(
    alias="my-prompt",                    # Unique identifier
    text_template="Hello {name}!",        # For text prompts
    messages_template=[                   # For chat prompts
        PromptMessage(role="system", content="You are a helpful assistant"),
        PromptMessage(role="user", content="Help me with {task}")
    ],
    model_settings=ModelSettings(...),    # Optional LLM settings
    output_type=OutputType.JSON,          # Optional output format
    output_schema=MySchema,                # Optional Pydantic schema
    interpolation_type=PromptInterpolationType.FSTRING  # Variable format
)
```

### Key Properties

- **alias**: Unique prompt identifier
- **version**: Current version (read-only, auto-managed)
- **label**: Current label (if pulled by label)
- **text_template**: String template for text prompts
- **messages_template**: List of messages for chat prompts
- **type**: `PromptType.TEXT` or `PromptType.LIST` (auto-detected)
- **interpolation_type**: How variables are formatted
- **model_settings**: LLM configuration
- **output_type**: Expected output format
- **output_schema**: Pydantic model for structured output

---

## Prompt Types

### Text Prompts

Simple string templates for completion-style prompts.

```python
prompt = Prompt(
    alias="summarizer",
    text_template="Summarize the following text:\n\n{text}\n\nSummary:"
)
```

### Chat Prompts (Messages)

List of messages for chat-style prompts (system, user, assistant).

```python
from deepeval.prompt import PromptMessage

prompt = Prompt(
    alias="customer-support",
    messages_template=[
        PromptMessage(
            role="system",
            content="You are a customer support agent for {company_name}"
        ),
        PromptMessage(
            role="user",
            content="{customer_query}"
        )
    ]
)
```

---

## Interpolation Methods

DeepEval supports multiple variable interpolation formats:

### 1. F-String (Default)

```python
from deepeval.prompt import PromptInterpolationType

prompt = Prompt(
    alias="greeting",
    text_template="Hello {name}, welcome to {place}!",
    interpolation_type=PromptInterpolationType.FSTRING
)

result = prompt.interpolate(name="Alice", place="Wonderland")
# Output: "Hello Alice, welcome to Wonderland!"
```

### 2. Mustache

```python
prompt = Prompt(
    alias="greeting",
    text_template="Hello {{name}}, welcome to {{place}}!",
    interpolation_type=PromptInterpolationType.MUSTACHE
)
```

### 3. Mustache with Space

```python
prompt = Prompt(
    alias="greeting",
    text_template="Hello {{ name }}, welcome to {{ place }}!",
    interpolation_type=PromptInterpolationType.MUSTACHE_WITH_SPACE
)
```

### 4. Dollar Brackets

```python
prompt = Prompt(
    alias="greeting",
    text_template="Hello ${name}, welcome to ${place}!",
    interpolation_type=PromptInterpolationType.DOLLAR_BRACKETS
)
```

### 5. Jinja2

```python
prompt = Prompt(
    alias="greeting",
    text_template="Hello {{ name }}, welcome to {{ place }}!",
    interpolation_type=PromptInterpolationType.JINJA
)
```

Jinja2 supports advanced features like loops and conditionals:

```python
prompt = Prompt(
    alias="list-items",
    text_template="""
    Items:
    {% for item in items %}
    - {{ item }}
    {% endfor %}
    """,
    interpolation_type=PromptInterpolationType.JINJA
)

result = prompt.interpolate(items=["apple", "banana", "cherry"])
```

---

## Model Settings

Configure LLM parameters for your prompts:

```python
from deepeval.prompt import ModelSettings, ModelProvider, ReasoningEffort, Verbosity

settings = ModelSettings(
    provider=ModelProvider.OPEN_AI,      # OPEN_AI, ANTHROPIC, GEMINI, X_AI, DEEPSEEK, BEDROCK
    name="gpt-4",                        # Model name
    temperature=0.7,                     # Randomness (0.0-2.0)
    max_tokens=1000,                     # Max output tokens
    top_p=0.9,                           # Nucleus sampling
    frequency_penalty=0.0,               # Penalize frequent tokens
    presence_penalty=0.0,                # Penalize repeated tokens
    stop_sequence=["END"],               # Stop generation at these strings
    reasoning_effort=ReasoningEffort.HIGH,  # For reasoning models (o1, o3)
    verbosity=Verbosity.MEDIUM           # For some models
)

prompt = Prompt(
    alias="my-prompt",
    text_template="...",
    model_settings=settings
)
```

### Model Providers

- **OPEN_AI**: GPT-4, GPT-3.5, o1, o3
- **ANTHROPIC**: Claude 3 (Opus, Sonnet, Haiku)
- **GEMINI**: Gemini Pro, Gemini Ultra
- **X_AI**: Grok models
- **DEEPSEEK**: DeepSeek models
- **BEDROCK**: AWS Bedrock models

---

## Output Configuration

Control the format and structure of LLM outputs:

### Output Types

```python
from deepeval.prompt import OutputType

# 1. Plain text output (default)
prompt = Prompt(
    alias="text-output",
    text_template="...",
    output_type=OutputType.TEXT
)

# 2. JSON output (unstructured)
prompt = Prompt(
    alias="json-output",
    text_template="...",
    output_type=OutputType.JSON
)

# 3. Structured schema output
from pydantic import BaseModel

class UserInfo(BaseModel):
    name: str
    age: int
    email: str

prompt = Prompt(
    alias="schema-output",
    text_template="Extract user information from: {text}",
    output_type=OutputType.SCHEMA,
    output_schema=UserInfo
)
```

### Nested Schemas

DeepEval supports complex nested Pydantic schemas:

```python
from pydantic import BaseModel
from typing import List

class Address(BaseModel):
    street: str
    city: str
    country: str

class Person(BaseModel):
    name: str
    age: int
    addresses: List[Address]

prompt = Prompt(
    alias="extract-person",
    text_template="Extract person data from: {text}",
    output_type=OutputType.SCHEMA,
    output_schema=Person
)
```

---

## Pull, Push, Update Operations

### Pull: Fetch Prompts from Confident AI

```python
prompt = Prompt(alias="customer-support")

# Pull latest version
prompt.pull()

# Pull specific version
prompt.pull(version="3")

# Pull by label (for A/B testing)
prompt.pull(label="production")

# Pull with fallback to cache if API fails
prompt.pull(fallback_to_cache=True)

# Pull and write to cache
prompt.pull(write_to_cache=True)

# Default to cache first (fastest)
prompt.pull(default_to_cache=True)

# Auto-refresh every 60 seconds
prompt.pull(refresh=60)
```

### Push: Upload Prompts to Confident AI

```python
# Create and push a new prompt
prompt = Prompt(alias="new-prompt")
prompt.push(
    text="Translate {text} to {language}",
    interpolation_type=PromptInterpolationType.FSTRING,
    model_settings=ModelSettings(
        provider=ModelProvider.OPEN_AI,
        name="gpt-4",
        temperature=0.3
    ),
    output_type=OutputType.TEXT
)
# ✅ Prompt successfully pushed to Confident AI! View at https://...

# Push chat prompt
prompt.push(
    messages=[
        PromptMessage(role="system", content="You are a translator"),
        PromptMessage(role="user", content="Translate: {text}")
    ]
)
```

### Update: Modify Existing Versions

```python
prompt = Prompt(alias="existing-prompt")

# Update a specific version
prompt.update(
    version="2",
    text="Updated template: {variable}",
    model_settings=ModelSettings(temperature=0.5)
)
# ✅ Prompt successfully updated on Confident AI!
```

---

## Caching System

DeepEval uses a local JSON cache for offline support and performance.

### Cache Location

```
.deepeval/.deepeval-prompt-cache.json
```

### Cache Structure

```json
{
  "customer-support": {
    "version": {
      "1": { "alias": "...", "template": "...", ... },
      "2": { "alias": "...", "template": "...", ... }
    },
    "label": {
      "production": { "alias": "...", "template": "...", ... },
      "experimental": { "alias": "...", "template": "...", ... }
    }
  }
}
```

### Cache Behavior

**Read Operations** (concurrent reads allowed):
- Uses shared lock (`LOCK_SH`)
- Multiple processes can read simultaneously
- Returns `None` if cache is locked or corrupted

**Write Operations** (exclusive lock):
- Uses exclusive lock (`LOCK_EX`)
- Blocks other reads/writes
- Silently fails if lock cannot be acquired

**Thread Safety**:
- Uses `portalocker` for file locking
- Thread-safe with internal `threading.Lock()`
- Safe for multi-process environments

### Cache Options

```python
# Pull with cache fallback
prompt.pull(fallback_to_cache=True)  # Use cache if API fails

# Pull and update cache
prompt.pull(write_to_cache=True)     # Write to cache after pull

# Pull from cache first (fastest)
prompt.pull(default_to_cache=True)   # Use cache if available, skip API

# Disable caching
prompt.pull(
    fallback_to_cache=False,
    write_to_cache=False,
    default_to_cache=False
)
```

---

## Auto-Refresh Polling

DeepEval can automatically poll Confident AI for prompt updates in the background.

### How It Works

1. **Background Thread**: Creates a daemon thread with its own event loop
2. **Periodic Polling**: Fetches updates at specified intervals
3. **Automatic Updates**: Updates cache and in-memory prompt when changes detected
4. **Thread-Safe**: Uses locks to prevent race conditions

### Usage

```python
prompt = Prompt(alias="dynamic-prompt")

# Auto-refresh every 60 seconds
prompt.pull(refresh=60)

# Now the prompt will automatically update in the background
# Your application continues running with the latest prompt version
```

### Refresh Behavior

- **Initial Pull**: Fetches prompt immediately and bootstraps cache
- **Background Polling**: Polls every `refresh` seconds
- **Silent Updates**: Updates happen in background without blocking
- **Cache Updates**: Automatically writes updates to cache
- **In-Memory Updates**: Updates the prompt instance properties

### Stopping Polling

```python
# Polling stops automatically when prompt instance is destroyed
del prompt

# Or explicitly stop by setting refresh=None
prompt.pull(refresh=None)
```

### Use Cases

**Production Deployments**:
```python
# Long-running service with dynamic prompts
prompt = Prompt(alias="chatbot-prompt")
prompt.pull(refresh=300)  # Refresh every 5 minutes

# Your service continues running
# Prompt updates automatically without restart
```

**A/B Testing**:
```python
# Test different prompt versions in production
prompt_a = Prompt(alias="experiment")
prompt_a.pull(label="variant-a", refresh=60)

prompt_b = Prompt(alias="experiment")
prompt_b.pull(label="variant-b", refresh=60)

# Both variants stay in sync with Confident AI
```

---

## Usage Examples

### Example 1: Simple Text Prompt

```python
from deepeval.prompt import Prompt

# Create and pull prompt
prompt = Prompt(alias="summarizer")
prompt.pull()

# Interpolate variables
text = prompt.interpolate(
    document="Long article about AI...",
    max_words=100
)

# Use with your LLM
response = llm.generate(text)
```

### Example 2: Chat Prompt with Model Settings

```python
from deepeval.prompt import Prompt, PromptMessage, ModelSettings, ModelProvider

# Create chat prompt
prompt = Prompt(alias="code-reviewer")
prompt.push(
    messages=[
        PromptMessage(
            role="system",
            content="You are an expert code reviewer. Review code for bugs and improvements."
        ),
        PromptMessage(
            role="user",
            content="Review this code:\n\n{code}"
        )
    ],
    model_settings=ModelSettings(
        provider=ModelProvider.OPEN_AI,
        name="gpt-4",
        temperature=0.2,
        max_tokens=2000
    )
)

# Pull and use
prompt.pull()
messages = prompt.interpolate(code="def hello(): print('world')")
# Returns: [
#   {"role": "system", "content": "You are an expert..."},
#   {"role": "user", "content": "Review this code:\n\ndef hello(): print('world')"}
# ]
```

### Example 3: Structured Output with Schema

```python
from deepeval.prompt import Prompt, OutputType
from pydantic import BaseModel
from typing import List

# Define output schema
class Sentiment(BaseModel):
    sentiment: str  # "positive", "negative", "neutral"
    confidence: float
    key_phrases: List[str]

# Create prompt with schema
prompt = Prompt(alias="sentiment-analyzer")
prompt.push(
    text="Analyze the sentiment of: {text}",
    output_type=OutputType.SCHEMA,
    output_schema=Sentiment
)

# Use prompt
prompt.pull()
text = prompt.interpolate(text="I love this product!")

# LLM will return structured output matching Sentiment schema
```

### Example 4: Version Management

```python
from deepeval.prompt import Prompt

prompt = Prompt(alias="translator")

# Push version 1
prompt.push(text="Translate to {language}: {text}")

# Push version 2 (improved)
prompt.push(text="Translate the following text to {language}. Maintain tone and style.\n\nText: {text}")

# Push version 3 (with examples)
prompt.push(text="""Translate to {language}. Examples:
English: Hello → Spanish: Hola
English: Goodbye → Spanish: Adiós

Text: {text}""")

# Use specific version
prompt.pull(version="2")

# Or use latest
prompt.pull(version="latest")
```

### Example 5: A/B Testing with Labels

```python
from deepeval.prompt import Prompt

# Create two variants
prompt = Prompt(alias="onboarding-email")

# Push variant A (formal)
prompt.push(text="Dear {name},\n\nWelcome to our platform...")
# Manually label as "formal" in Confident AI UI

# Push variant B (casual)
prompt.push(text="Hey {name}! 👋\n\nWelcome aboard...")
# Manually label as "casual" in Confident AI UI

# Use in production
prompt_formal = Prompt(alias="onboarding-email")
prompt_formal.pull(label="formal")

prompt_casual = Prompt(alias="onboarding-email")
prompt_casual.pull(label="casual")

# Route users to different variants
if user.preference == "formal":
    email = prompt_formal.interpolate(name=user.name)
else:
    email = prompt_casual.interpolate(name=user.name)
```

### Example 6: Auto-Refresh for Production

```python
from deepeval.prompt import Prompt
import time

# Initialize with auto-refresh
prompt = Prompt(alias="production-chatbot")
prompt.pull(
    label="production",
    refresh=60,              # Refresh every 60 seconds
    default_to_cache=True    # Start with cache for instant load
)

# Long-running service
while True:
    user_input = get_user_input()
    
    # Always uses latest prompt version
    messages = prompt.interpolate(user_query=user_input)
    response = llm.chat(messages)
    
    send_response(response)
```

### Example 7: Load from Local File

```python
from deepeval.prompt import Prompt

# Load from JSON file
prompt = Prompt()
prompt.load("prompts/customer-support.json", messages_key="messages")

# Load from text file
prompt = Prompt()
prompt.load("prompts/summarizer.txt")

# Then push to Confident AI
prompt.alias = "customer-support"
prompt.push()
```

---

## Best Practices

### 1. Use Aliases Consistently

```python
# Good: Descriptive, consistent naming
"customer-support-v2"
"email-generator-formal"
"code-reviewer-python"

# Bad: Vague or inconsistent
"prompt1"
"test"
"asdf"
```

### 2. Version Control Strategy

```python
# Use semantic versioning in commit messages
prompt.push(text="...")  # Creates version "1"
# In Confident AI, add commit message: "Initial version"

prompt.push(text="...")  # Creates version "2"
# Commit message: "Added examples for better accuracy"

prompt.push(text="...")  # Creates version "3"
# Commit message: "Fixed formatting issues"
```

### 3. Label Strategy for A/B Testing

```python
# Use clear, descriptive labels
"production"      # Current production version
"staging"         # Testing before production
"experimental"    # Experimental features
"variant-a"       # A/B test variant A
"variant-b"       # A/B test variant B
```

### 4. Cache Management

```python
# For production: Use cache with fallback
prompt.pull(
    default_to_cache=True,    # Fast startup
    fallback_to_cache=True,   # Resilient to API failures
    write_to_cache=True       # Keep cache updated
)

# For development: Skip cache for latest changes
prompt.pull(
    default_to_cache=False,
    write_to_cache=False
)
```

### 5. Auto-Refresh Guidelines

```python
# Production: Longer intervals (5-15 minutes)
prompt.pull(refresh=300)  # 5 minutes

# Staging: Medium intervals (1-5 minutes)
prompt.pull(refresh=60)   # 1 minute

# Development: Shorter intervals or manual refresh
prompt.pull(refresh=30)   # 30 seconds
# Or just pull manually when needed
```

### 6. Error Handling

```python
from deepeval.prompt import Prompt

try:
    prompt = Prompt(alias="my-prompt")
    prompt.pull(fallback_to_cache=True)
except Exception as e:
    # Handle API failures
    print(f"Failed to pull prompt: {e}")
    # Use default prompt or raise error
```

### 7. Model Settings Best Practices

```python
# For deterministic outputs (code generation, data extraction)
ModelSettings(
    temperature=0.0,
    top_p=1.0
)

# For creative outputs (content generation, brainstorming)
ModelSettings(
    temperature=0.9,
    top_p=0.95
)

# For balanced outputs (chatbots, Q&A)
ModelSettings(
    temperature=0.7,
    top_p=0.9
)
```

### 8. Structured Output Best Practices

```python
from pydantic import BaseModel, Field
from typing import List, Optional

# Use descriptive field names and types
class ProductReview(BaseModel):
    rating: int = Field(ge=1, le=5, description="Rating from 1-5")
    sentiment: str = Field(description="positive, negative, or neutral")
    summary: str = Field(max_length=200)
    pros: List[str]
    cons: List[str]
    recommendation: Optional[str] = None

# Use with prompt
prompt = Prompt(
    alias="review-analyzer",
    text_template="Analyze this review: {review_text}",
    output_type=OutputType.SCHEMA,
    output_schema=ProductReview
)
```

---

## Summary

DeepEval's prompt management system provides:

- **Centralized Management**: Store prompts in Confident AI cloud
- **Version Control**: Track changes and rollback when needed
- **A/B Testing**: Use labels to test different prompt variants
- **Auto-Refresh**: Keep prompts updated without redeployment
- **Local Caching**: Fast startup and offline support
- **Structured Outputs**: Type-safe outputs with Pydantic schemas
- **Multiple Interpolation**: Support for various template formats
- **Model Configuration**: Centralize LLM settings with prompts
- **Thread-Safe**: Safe for multi-threaded and multi-process environments

The system is designed for production use with features like automatic caching, background polling, and graceful fallbacks.

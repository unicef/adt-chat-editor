# Code Refactoring Ideas for ADT Chat Editor

## Overview

This document outlines comprehensive refactoring suggestions to improve code quality, PEP compliance, and adherence to software engineering best practices for the ADT Chat Editor project.

## 1. Type Safety and Error Handling

### 1.1 Fix Type Annotations

**Current Issue**: The linter error shows `state.language` can be `str | None` but `load_translated_html_contents` expects `str`.

**Solution**:

```python
# In src/workflows/agents/web_split_agent/actions.py
async def web_split(state: ADTState, config: RunnableConfig) -> ADTState:
    # Add null check before calling the function
    if state.language is None:
        raise ValueError("Language must be set before splitting HTML files")
  
    translated_html_contents = await load_translated_html_contents(
        language=state.language
    )
```

**Alternative**: Update the function signature to accept `Optional[str]`:

```python
# In src/utils/file_utils.py
async def load_translated_html_contents(language: Optional[str]) -> List[Dict[str, Any]]:
    if language is None:
        raise ValueError("Language cannot be None")
    # ... rest of implementation
```

### 1.2 Add Comprehensive Type Hints

- Add return type annotations to all functions
- Use `typing` module for complex types
- Add generic types where appropriate

## 2. Code Organization and Structure

### 2.1 Extract Constants

**Current Issue**: Magic strings and repeated values throughout the code.

**Solution**: Create a dedicated constants module:

```python
# src/constants.py
class FileExtensions:
    HTML = ".html"
    JSON = ".json"

class FileNames:
    NAV_HTML = "nav.html"
    TEXTS_JSON = "texts.json"
    CHECKPOINT_JSON = "checkpoint.json"

class DirectoryNames:
    TRANSLATIONS = "translations"
    HTML_CONTENTS = "html_contents"
    STATE_CHECKPOINTS = "state_checkpoints"
```

### 2.2 Implement Service Layer Pattern

**Current Issue**: Business logic mixed with data access in action functions.

**Solution**: Create service classes:

```python
# src/services/html_service.py
class HTMLService:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
  
    async def get_html_files(self) -> List[str]:
        # Implementation
      
    async def read_html_file(self, file_path: str) -> str:
        # Implementation
      
    async def write_html_file(self, file_path: str, content: str) -> None:
        # Implementation

# src/services/translation_service.py
class TranslationService:
    def __init__(self, translations_dir: str):
        self.translations_dir = translations_dir
  
    async def load_translated_contents(self, language: str) -> List[Dict[str, Any]]:
        # Implementation
```

### 2.3 Implement Repository Pattern

**Current Issue**: Direct file system access scattered throughout the code.

**Solution**: Create repository classes:

```python
# src/repositories/html_repository.py
class HTMLRepository:
    async def find_by_pattern(self, pattern: str) -> List[str]:
        # Implementation
      
    async def save(self, file_path: str, content: str) -> None:
        # Implementation
      
    async def find_by_id(self, file_id: str) -> Optional[str]:
        # Implementation
```

## 3. Error Handling and Logging

### 3.1 Implement Custom Exceptions

```python
# src/exceptions.py
class ADTException(Exception):
    """Base exception for ADT Chat Editor"""
    pass

class HTMLProcessingError(ADTException):
    """Raised when HTML processing fails"""
    pass

class TranslationError(ADTException):
    """Raised when translation operations fail"""
    pass

class StateError(ADTException):
    """Raised when state operations fail"""
    pass
```

### 3.2 Improve Error Handling

**Current Issue**: Generic exception handling without specific error types.

**Solution**: Replace generic exception handling:

```python
# Instead of:
try:
    # operation
except Exception:
    # generic handling

# Use:
try:
    # operation
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    raise HTMLProcessingError(f"Required file not found: {e}")
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON: {e}")
    raise TranslationError(f"Invalid translation file format: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise ADTException(f"Unexpected error during operation: {e}")
```

### 3.3 Structured Logging

```python
# src/utils/logging.py
import structlog

def setup_logging() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
```

## 4. Code Quality Improvements

### 4.1 Reduce Function Complexity

**Current Issue**: The `web_split` function is doing too many things.

**Solution**: Break it down into smaller, focused functions:

```python
async def web_split(state: ADTState, config: RunnableConfig) -> ADTState:
    """Split one HTML file into several and update nav accordingly."""
    current_step = state.steps[state.current_step_index]
  
    # Extract HTML file processing
    html_file = await _get_target_html_file(current_step)
    html_content = await _process_html_content(html_file)
  
    # Extract translation loading
    translated_contents = await _load_translations(state.language, html_file)
  
    # Extract splitting logic
    split_responses = await _split_html_content(
        html_content, translated_contents, state.messages[-1].content, config
    )
  
    # Extract file writing and nav updates
    splitted_file_paths = await _write_split_files_and_update_nav(
        html_file, split_responses
    )
  
    # Update state
    await _update_state(state, splitted_file_paths)
  
    return state

async def _get_target_html_file(current_step) -> str:
    """Get the target HTML file for splitting."""
    html_files = await get_html_files(OUTPUT_DIR)
    html_files = [f for f in html_files if f in current_step.html_files]
    return html_files[-1]

async def _process_html_content(html_file: str) -> str:
    """Process HTML content for splitting."""
    html_content = await read_html_file(html_file)
    html_content, _ = await extract_layout_properties_async(html_content)
    return html_content
```

### 4.2 Implement Dependency Injection

**Current Issue**: Hard-coded dependencies and tight coupling.

**Solution**: Use dependency injection:

```python
# src/di/container.py
from dependency_injector import containers, providers
from src.services.html_service import HTMLService
from src.services.translation_service import TranslationService

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
  
    html_service = providers.Singleton(
        HTMLService,
        output_dir=config.output_dir
    )
  
    translation_service = providers.Singleton(
        TranslationService,
        translations_dir=config.translations_dir
    )

# Usage in actions
async def web_split(
    state: ADTState, 
    config: RunnableConfig,
    html_service: HTMLService = Depends(),
    translation_service: TranslationService = Depends()
) -> ADTState:
    # Use injected services
```

### 4.3 Add Input Validation

```python
# src/validators.py
from pydantic import BaseModel, validator
from typing import List, Optional

class WebSplitRequest(BaseModel):
    html_file: str
    instruction: str
    language: str
  
    @validator('html_file')
    def validate_html_file(cls, v):
        if not v.endswith('.html'):
            raise ValueError('File must be an HTML file')
        return v
  
    @validator('language')
    def validate_language(cls, v):
        if not v or len(v) < 2:
            raise ValueError('Language must be at least 2 characters')
        return v

# Usage
async def web_split(state: ADTState, config: RunnableConfig) -> ADTState:
    request = WebSplitRequest(
        html_file=html_file,
        instruction=state.messages[-1].content,
        language=state.language or "en"
    )
```

## 5. Performance Optimizations

### 5.1 Implement Caching

```python
# src/cache/translation_cache.py
from functools import lru_cache
import asyncio
from typing import Dict, Any

class TranslationCache:
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
  
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            return self._cache.get(key)
  
    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._cache[key] = value
  
    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()

# Usage
translation_cache = TranslationCache()

async def load_translated_html_contents(language: str) -> List[Dict[str, Any]]:
    cache_key = f"translated_html_{language}"
  
    # Check cache first
    cached_result = await translation_cache.get(cache_key)
    if cached_result:
        return cached_result
  
    # Load from file
    result = await _load_from_file(language)
  
    # Cache the result
    await translation_cache.set(cache_key, result)
  
    return result
```

### 5.2 Implement Async Context Managers

```python
# src/utils/async_utils.py
import aiofiles
from contextlib import asynccontextmanager

@asynccontextmanager
async def html_file_context(file_path: str, mode: str = 'r'):
    """Async context manager for HTML file operations."""
    async with aiofiles.open(file_path, mode, encoding='utf-8') as file:
        yield file

# Usage
async def read_html_file(file_path: str) -> str:
    async with html_file_context(file_path) as file:
        return await file.read()
```

## 6. Testing Improvements

### 6.1 Add Unit Tests

```python
# tests/test_web_split_agent.py
import pytest
from unittest.mock import AsyncMock, patch
from src.workflows.agents.web_split_agent.actions import web_split

@pytest.mark.asyncio
async def test_web_split_success():
    # Arrange
    mock_state = AsyncMock()
    mock_config = {}
  
    with patch('src.workflows.agents.web_split_agent.actions.get_html_files') as mock_get_files:
        mock_get_files.return_value = ['test.html']
      
        # Act
        result = await web_split(mock_state, mock_config)
      
        # Assert
        assert result is not None
        mock_get_files.assert_called_once()
```

### 6.2 Add Integration Tests

```python
# tests/integration/test_html_processing.py
import pytest
from src.services.html_service import HTMLService

@pytest.mark.asyncio
async def test_html_file_operations():
    # Arrange
    html_service = HTMLService("/tmp/test_output")
    test_content = "<html><body>Test</body></html>"
  
    # Act
    await html_service.write_html_file("test.html", test_content)
    result = await html_service.read_html_file("test.html")
  
    # Assert
    assert result == test_content
```

## 7. Configuration Management

### 7.1 Environment-based Configuration

```python
# src/config/settings.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    output_dir: str = "data/output"
    translations_dir: str = "data/translations"
    html_contents_dir: str = "data/html_contents"
    state_checkpoints_dir: str = "data/state_checkpoints"
  
    # LLM settings
    llm_api_key: Optional[str] = None
    llm_model: str = "gpt-4"
  
    # Logging
    log_level: str = "INFO"
  
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 7.2 Feature Flags

```python
# src/config/features.py
from dataclasses import dataclass

@dataclass
class FeatureFlags:
    enable_caching: bool = True
    enable_async_processing: bool = True
    enable_validation: bool = True
    enable_metrics: bool = False

feature_flags = FeatureFlags()
```

## 8. Documentation Improvements

### 8.1 Add Comprehensive Docstrings

```python
async def web_split(state: ADTState, config: RunnableConfig) -> ADTState:
    """
    Split one HTML file into several files and update navigation accordingly.
  
    This function processes an HTML file based on user instructions and splits it
    into multiple standalone HTML files. It also updates the navigation file to
    include references to the newly created files.
  
    Args:
        state: The current state of the ADT workflow containing step information
               and user messages.
        config: Configuration object for the LangChain runnable, containing
                settings for LLM calls and other runtime configurations.
  
    Returns:
        ADTState: The updated state object with new messages and step status.
  
    Raises:
        ValueError: If the language is not set or HTML file cannot be found.
        HTMLProcessingError: If HTML processing fails.
        TranslationError: If translation loading fails.
  
    Example:
        >>> state = ADTState(...)
        >>> config = RunnableConfig(...)
        >>> updated_state = await web_split(state, config)
    """
```

### 8.2 Add Type Documentation

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.workflows.state import ADTState
    from langchain_core.runnables import RunnableConfig

async def web_split(
    state: "ADTState", 
    config: "RunnableConfig"
) -> "ADTState":
    """Split HTML file into multiple files."""
```

## 9. Code Style and PEP Compliance

### 9.1 Follow PEP 8 Strictly

- Use 4 spaces for indentation (not tabs)
- Limit line length to 88 characters (Black formatter)
- Use snake_case for functions and variables
- Use PascalCase for classes
- Use UPPER_CASE for constants

### 9.2 Implement Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.10
      
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.270
    hooks:
      - id: ruff
        args: [--fix]
      
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### 9.3 Add Code Quality Tools

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py310']
include = '\.pyi?$'

[tool.ruff]
target-version = "py310"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## 10. Monitoring and Observability

### 10.1 Add Metrics

```python
# src/metrics/metrics.py
import time
from functools import wraps
from typing import Callable, Any

def track_execution_time(func: Callable) -> Callable:
    """Decorator to track function execution time."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            # Log or send to metrics service
            logger.info(f"{func.__name__} executed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
  
    return wrapper

# Usage
@track_execution_time
async def web_split(state: ADTState, config: RunnableConfig) -> ADTState:
    # Implementation
```

### 10.2 Add Health Checks

```python
# src/health/health_check.py
from typing import Dict, Any
import asyncio

class HealthChecker:
    async def check_html_service(self) -> Dict[str, Any]:
        """Check if HTML service is healthy."""
        try:
            # Perform health check
            return {"status": "healthy", "service": "html"}
        except Exception as e:
            return {"status": "unhealthy", "service": "html", "error": str(e)}
  
    async def check_translation_service(self) -> Dict[str, Any]:
        """Check if translation service is healthy."""
        try:
            # Perform health check
            return {"status": "healthy", "service": "translation"}
        except Exception as e:
            return {"status": "unhealthy", "service": "translation", "error": str(e)}
  
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services."""
        checks = await asyncio.gather(
            self.check_html_service(),
            self.check_translation_service()
        )
      
        all_healthy = all(check["status"] == "healthy" for check in checks)
      
        return {
            "overall_status": "healthy" if all_healthy else "unhealthy",
            "services": checks
        }
```

## Implementation Priority

1. **High Priority** (Fix immediately):

   - Type safety fixes (linter errors)
   - Error handling improvements
   - Function complexity reduction
2. **Medium Priority** (Next sprint):

   - Service layer implementation
   - Configuration management
   - Testing improvements
3. **Low Priority** (Future sprints):

   - Performance optimizations
   - Monitoring and observability
   - Advanced patterns (DI, caching)

## Conclusion

These refactoring suggestions will significantly improve the codebase's maintainability, reliability, and adherence to Python best practices. The changes should be implemented incrementally, starting with the high-priority items that address immediate issues like type safety and error handling.

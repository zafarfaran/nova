# Logging Configuration

This document explains how to configure logging per section with verbosity control.

**Note:** Metrics always run and cannot be disabled. Only logging is configurable.

## Environment Variables

Add these to your `.env` file to control logging:

### Enable/Disable Logging Globally

```bash
# Enable/disable structured logging globally (default: true)
LOGGING_ENABLED=true
```

### Configure Logging Sections

```bash
# Enable logging for specific sections (comma-separated)
# Use "all" to enable all sections (default)
# Available sections: document_processing, chat, validation, email, api, client_management, ai
LOGGING_ENABLED_SECTIONS=all
```

### Configure Log Verbosity Per Section

```bash
# Set log levels per section (comma-separated key:value pairs)
# Format: section:level,section:level
# Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
# Default: INFO for all sections if not specified
LOGGING_LEVELS=document_processing:DEBUG,chat:INFO,validation:WARNING
```

## Examples

### Example 1: Enable only document processing and chat logging

```bash
LOGGING_ENABLED=true
LOGGING_ENABLED_SECTIONS=document_processing,chat
```

This will:
- **Metrics**: Always collected for all sections
- **Logging**: Only `document_processing` and `chat` sections (default INFO level)

### Example 2: Different verbosity levels per section

```bash
LOGGING_ENABLED=true
LOGGING_ENABLED_SECTIONS=all
LOGGING_LEVELS=document_processing:DEBUG,chat:INFO,validation:WARNING,email:ERROR
```

This will:
- **Metrics**: Always collected for all sections
- **Logging**: 
  - `document_processing`: DEBUG level (most verbose)
  - `chat`: INFO level (default)
  - `validation`: WARNING level (only warnings and errors)
  - `email`: ERROR level (only errors)
  - Other sections: INFO level (default)

### Example 3: Production setup - minimal logging

```bash
LOGGING_ENABLED=true
LOGGING_ENABLED_SECTIONS=document_processing,chat
LOGGING_LEVELS=document_processing:INFO,chat:WARNING
```

This will:
- **Metrics**: Always collected for all sections
- **Logging**: 
  - Only `document_processing` and `chat` sections
  - `document_processing` at INFO level
  - `chat` at WARNING level (reduces noise)

### Example 4: Debug mode for specific section

```bash
LOGGING_ENABLED=true
LOGGING_ENABLED_SECTIONS=all
LOGGING_LEVELS=document_processing:DEBUG
```

This will:
- **Metrics**: Always collected for all sections
- **Logging**: 
  - `document_processing` at DEBUG level (very verbose, includes all details)
  - All other sections at INFO level (default)

## Available Sections

- `document_processing` - Document extraction and processing operations
- `chat` - AI chat interactions
- `validation` - Document validation operations
- `email` - Email and chaser generation
- `api` - General API endpoints
- `client_management` - Client and engagement management
- `ai` - General AI operations

## How It Works

1. **Metrics**: Always collected for all sections. Metrics cannot be disabled.

2. **Logging**: When a log entry is created, the system:
   - Checks if logging is enabled for that section
   - Checks if the log level meets the configured verbosity for that section
   - If either check fails, the log entry is filtered out (returns empty string)

3. **Section Detection**: Sections are automatically detected from:
   - Module paths (for LLM calls)
   - Endpoint paths (for HTTP requests)
   - Logger names (for general logging)

4. **Log Levels**: 
   - DEBUG: Most verbose, includes all details
   - INFO: Standard information (default)
   - WARNING: Only warnings and errors
   - ERROR: Only errors
   - CRITICAL: Only critical errors

## Performance Impact

- Metrics always run (minimal overhead, essential for monitoring)
- Disabling logging for a section reduces log volume and I/O operations
- Using higher log levels (WARNING, ERROR) reduces log volume significantly
- Settings are cached for performance. Changes to `.env` require application restart.

## Notes

- **Metrics cannot be disabled** - they always run for monitoring purposes
- Settings are cached for performance. Changes to `.env` require application restart.
- Use `"all"` (case-insensitive) to enable all sections for logging
- Empty string disables all logging sections
- Section names are case-insensitive in configuration
- Log levels are case-insensitive (DEBUG, debug, Debug all work)
- If a section is not specified in `LOGGING_LEVELS`, it defaults to INFO

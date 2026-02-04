# AI Provider Configuration Guide

This application supports both **Anthropic (Claude)** and **OpenAI (GPT)** as AI providers. You can easily switch between them using environment variables.

## Configuration

### 1. Choose Your Provider

In your `.env` file, set the `AI_PROVIDER` variable to either:
- `anthropic` - Use Anthropic's Claude models
- `openai` - Use OpenAI's GPT models

```bash
AI_PROVIDER=anthropic
```

### 2. Set API Keys

Add the API key for your chosen provider:

**For Anthropic:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

**For OpenAI:**
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

## Provider Details

### Anthropic (Claude)
- **Model Used**: `claude-sonnet-4-20250514`
- **Features**:
  - Document analysis and extraction
  - Function calling / tool use
  - Streaming responses
  - Vision capabilities for PDFs and images

### OpenAI (GPT)
- **Model Used**: `gpt-4o`
- **Features**:
  - Document analysis and extraction
  - Function calling
  - Streaming responses
  - Vision capabilities for images

## Example Configuration

See `.env.example` for a complete configuration template.

### Using Anthropic (Default)
```bash
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
OPENAI_API_KEY=  # Can be empty
```

### Using OpenAI
```bash
AI_PROVIDER=openai
ANTHROPIC_API_KEY=  # Can be empty
OPENAI_API_KEY=sk-xxxxx
```

## What Gets Switched?

When you change the `AI_PROVIDER` setting, both of these services will use the selected provider:

1. **Document Processing**: Extraction and validation of invoices, credit notes, and other VAT documents
2. **Chat Assistant**: The Nova AI chat assistant for VAT compliance queries

## Notes

- You only need to provide the API key for the provider you're using
- The application will automatically use the correct provider based on the `AI_PROVIDER` setting
- Changes to `.env` require restarting the application to take effect
- Both providers support the same features, so switching should be seamless

# Domain-Based Architecture

This directory follows a **domain-driven design** approach, organizing code by business domain rather than technical layer.

## Structure

Each domain is self-contained with its own:

```
domains/
├── clients/
│   ├── api/          # API client functions
│   ├── components/   # React components
│   ├── hooks/        # React hooks (useClients, etc.)
│   ├── types/        # TypeScript types matching backend schemas
│   └── utils/        # Domain-specific utilities
├── documents/
├── engagements/
└── ...
```

## Benefits

1. **Scalability**: Easy to add new domains without affecting others
2. **Maintainability**: All related code is in one place
3. **Team Collaboration**: Different teams can work on different domains
4. **Type Safety**: Types match backend schemas exactly
5. **Reusability**: Components and hooks can be shared across the app

## Domain Structure

### API Layer (`api/`)
- Direct API calls to backend endpoints
- Error handling with domain-specific error classes
- Matches backend FastAPI routes

### Components (`components/`)
- Reusable React components for the domain
- Self-contained with their own state management
- Export via `index.ts` for clean imports

### Hooks (`hooks/`)
- React hooks for domain operations
- Encapsulate state management and API calls
- Provide loading, error, and data states

### Types (`types/`)
- TypeScript types matching backend Pydantic schemas
- Domain-specific enums and interfaces
- Utility functions for type transformations

### Utils (`utils/`)
- Domain-specific validation
- Helper functions
- Business logic utilities

## Usage Example

```typescript
// Import from domain
import { CreateClientForm, ClientsList } from "~/domains/clients/components";
import { useClients } from "~/domains/clients/hooks/useClients";
import type { ClientResponse } from "~/domains/clients/types";

// Use in component
function MyComponent() {
    const { clients, loading, fetchClients } = useClients();
    
    return <ClientsList clients={clients} />;
}
```

## Adding a New Domain

1. Create domain folder: `domains/[domain-name]/`
2. Add structure: `api/`, `components/`, `hooks/`, `types/`, `utils/`
3. Create types matching backend schemas
4. Create API client functions
5. Create React hooks for state management
6. Build components
7. Export via `index.ts` files

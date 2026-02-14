# Clients Domain

Complete client management domain with API, components, hooks, and types.

## Structure

```
clients/
├── api/
│   └── client.ts          # API functions (create, list, get, update, delete)
├── components/
│   ├── CreateClientForm.tsx
│   ├── ClientsList.tsx
│   └── index.ts
├── hooks/
│   └── useClients.ts      # React hook for client operations
├── types/
│   └── index.ts           # TypeScript types matching backend
└── utils/
    └── validation.ts       # Form validation utilities
```

## Usage

### Using the Hook

```typescript
import { useClients } from "~/domains/clients/hooks/useClients";

function MyComponent() {
    const { clients, total, loading, error, fetchClients, createNewClient } = useClients();
    
    useEffect(() => {
        fetchClients();
    }, []);
    
    // Use clients, loading, error states
}
```

### Using Components

```typescript
import { CreateClientForm, ClientsList } from "~/domains/clients/components";

function MyPage() {
    return (
        <>
            <CreateClientForm 
                onResult={(result) => {
                    if (result.success) {
                        console.log("Client created:", result.clientId);
                    }
                }}
                onCancel={() => {}}
            />
            <ClientsList 
                onClientSelect={(client) => console.log("Selected:", client)}
            />
        </>
    );
}
```

### Direct API Calls

```typescript
import { listClients, createClient } from "~/domains/clients/api/client";
import type { ClientCreatePayload } from "~/domains/clients/types";

// List clients
const response = await listClients(0, 100);
console.log(response.items, response.total);

// Create client
const payload: ClientCreatePayload = {
    name: "Acme Corp",
    contact_email: "contact@acme.com",
    entity_type: "limited_company",
};
const client = await createClient(payload);
```

## API Functions

- `createClient(payload)` - Create a new client
- `listClients(skip, limit)` - List clients with pagination
- `getClient(clientId)` - Get a single client
- `updateClient(clientId, payload)` - Update a client
- `deleteClient(clientId)` - Delete a client

All functions throw `ClientApiError` on failure.

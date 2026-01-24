# Client Onboarding Webhook

## Quick Start

### 1. Apply Database Changes

Run this command to update your database with the new models:

```bash
npm run db:push
```

### 2. Start Development Server

```bash
npm run dev
```

### 3. Test the Webhook

Send a POST request to create a new client onboarding:

```bash
curl -X POST http://localhost:3000/api/client/new \
  -H "Content-Type: application/json" \
  -d @test-payload.json
```

### 4. Visit the Onboarding Link

The API will return a response like:

```json
{
  "success": true,
  "data": {
    "client_id": "clxxx...",
    "onboarding_link": "http://localhost:3000/onboard/clxxx...",
    "email": "client@example.com",
    "client_name": "ABC Joinery Ltd"
  }
}
```

Open the `onboarding_link` in your browser to see the customized client onboarding page.

## API Endpoint

**POST** `/api/client/new`

Accepts a JSON payload with client setup information, checklist items, and auto-chaser configurations.

See `test-payload.json` for the complete payload structure.

## Features

✅ Validates incoming webhook payloads  
✅ Stores client data in PostgreSQL database  
✅ Generates unique onboarding links  
✅ Displays customizable onboarding pages  
✅ Tracks document checklist status  
✅ Supports automated reminder scheduling

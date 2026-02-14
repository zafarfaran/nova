# Prisma Removal Progress

## ✅ Completed

### Client Domain
- ✅ `src/app/accountant/page.tsx` - Now fetches from backend API
- ✅ `src/app/api/clients/[clientId]/route.ts` - DELETE uses backend API
- ✅ `src/app/api/client/new/route.ts` - Creates client via backend API (with engagement and request items)
- ✅ `src/app/api/sync-document/route.ts` - Verifies client via backend API

### Onboarding Domain
- ✅ `src/app/onboard/[clientId]/page.tsx` - Fetches client, engagements, and request items from backend
- ✅ `src/app/api/onboarding/submit/route.ts` - Uses backend API for all data
- ✅ All Prisma type imports replaced with `ChecklistItemCompat` from `~/domains/requests/types`

### Type System
- ✅ Created `src/domains/requests/types/index.ts` with backend-compatible types
- ✅ Removed all `@prisma/client` imports from onboard components

## ⚠️ Still Using Prisma (Needs Backend Endpoints)

### API Routes
- `src/app/api/ai-agent/chat/route.ts` - Uses Prisma for client/document lookups
- `src/app/api/vat-periods/[periodId]/status/route.ts` - Needs backend VAT period endpoint
- `src/app/api/uploadthing/core.ts` - Uses Prisma for checklist items
- `src/app/api/plaid/*` - Bank connection routes (may need backend endpoints)
- `src/app/api/flagged-documents/*` - Document review routes (may need backend endpoints)
- `src/app/api/documents/[clientId]/route.ts` - Document listing (partially uses backend)
- `src/app/api/checklist/*` - Checklist item management (needs backend endpoints)

### Auth
- `src/server/auth/config.ts` - Uses Prisma for user management
  - **Note**: NextAuth may require database for sessions. Consider:
    - Creating backend user endpoints
    - Using NextAuth with backend session storage
    - Or keeping Prisma only for auth (document as exception)

## 📋 Backend Endpoints Needed

### High Priority
1. **VAT Periods/Engagements**
   - `GET /api/v1/engagements/{id}/status` - Get engagement status
   - `PATCH /api/v1/engagements/{id}/status` - Update engagement status

2. **Request Items (Checklist)**
   - `PATCH /api/v1/requests/items/{id}` - Update request item status (already exists, verify usage)
   - `POST /api/v1/requests/items` - Create request item (already exists)

3. **Documents**
   - `GET /api/v1/documents?client_id={id}` - List documents (already exists)
   - Enhanced document review endpoints

### Medium Priority
4. **Bank Connections**
   - Backend endpoints for Plaid integration
   - Or keep Plaid routes as-is if they're frontend-only

5. **UploadThing Integration**
   - Backend endpoint to update request items when files are uploaded
   - Or modify uploadthing core to call backend API

### Low Priority / Optional
6. **User Management** (for auth)
   - `GET /api/v1/users/{id}` - Get user
   - `POST /api/v1/users` - Create user
   - Or keep Prisma for auth only

## 🎯 Next Steps

1. **Replace remaining API routes** that have backend equivalents
2. **Create backend endpoints** for missing functionality
3. **Update auth** to use backend or document Prisma exception
4. **Remove Prisma dependencies** once all routes are migrated
5. **Delete Prisma schema** and `src/server/db.ts` (or keep minimal for auth)

## 📝 Notes

- Backend is now the **single source of truth** for:
  - Clients
  - Engagements (VAT periods)
  - Request Sets and Items (checklist)
  - Documents (via sync endpoint)

- Frontend types match backend schemas in:
  - `src/domains/clients/types/index.ts`
  - `src/domains/requests/types/index.ts`

- All client creation/listing now goes through backend API
- Onboarding flow now uses backend API for all data

# Create Engagement - cURL Request

## Endpoint
`POST /api/v1/engagements`

## Request Body
The `engagement_type` and `status` fields must use **lowercase** values (enum values, not enum names):

- `engagement_type`: `"vat_return"`, `"annual_accounts"`, `"tax_return"`, `"audit"`, `"bookkeeping"`, `"other"`
- `status`: `"draft"`, `"in_progress"`, `"under_review"`, `"ready"`, `"submitted"`, `"locked"`

## Windows Command Prompt (single line)
```cmd
curl -X POST http://localhost:8000/api/v1/engagements -H "Content-Type: application/json" -d "{\"client_id\": 1, \"engagement_type\": \"vat_return\", \"period_start\": \"2026-02-14\", \"period_end\": \"2026-02-14\", \"status\": \"draft\", \"reference\": \"Q1-2026\", \"notes\": \"Test engagement\"}"
```

## PowerShell
```powershell
$body = @{
    client_id = 1
    engagement_type = "vat_return"
    period_start = "2026-02-14"
    period_end = "2026-02-14"
    status = "draft"
    reference = "Q1-2026"
    notes = "Test engagement"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/engagements" -Method POST -Body $body -ContentType "application/json"
```

## Linux/Mac
```bash
curl -X POST http://localhost:8000/api/v1/engagements \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "engagement_type": "vat_return",
    "period_start": "2026-02-14",
    "period_end": "2026-02-14",
    "status": "draft",
    "reference": "Q1-2026",
    "notes": "Test engagement"
  }'
```

## Using a JSON file (recommended for Windows)
Create `engagement.json`:
```json
{
  "client_id": 1,
  "engagement_type": "vat_return",
  "period_start": "2026-02-14",
  "period_end": "2026-02-14",
  "status": "draft",
  "reference": "Q1-2026",
  "notes": "Test engagement"
}
```

Then run:
```cmd
curl -X POST http://localhost:8000/api/v1/engagements -H "Content-Type: application/json" -d @engagement.json
```

## Required Fields
- `client_id` (int): ID of the client
- `period_start` (date): Start date (YYYY-MM-DD)
- `period_end` (date): End date (YYYY-MM-DD)

## Optional Fields
- `engagement_type` (string): Defaults to `"vat_return"` if not provided
- `status` (string): Defaults to `"draft"` if not provided
- `reference` (string | null): Reference code
- `due_date` (date | null): Due date
- `notes` (string | null): Notes

## Example Response
```json
{
  "id": 1,
  "client_id": 1,
  "engagement_type": "vat_return",
  "period_start": "2026-02-14",
  "period_end": "2026-02-14",
  "status": "draft",
  "reference": "Q1-2026",
  "due_date": null,
  "notes": "Test engagement",
  "is_locked": false,
  "created_at": "2026-02-14T12:00:00Z",
  "updated_at": "2026-02-14T12:00:00Z"
}
```

## Common Errors

### Error: `invalid input value for enum engagementtype: "VAT_RETURN"`
**Solution**: Use lowercase enum values. Change `"VAT_RETURN"` to `"vat_return"`.

### Error: `Client not found`
**Solution**: Make sure the `client_id` exists in the database.

### Error: `422 Unprocessable Entity`
**Solution**: Check that all required fields are provided and dates are in `YYYY-MM-DD` format.

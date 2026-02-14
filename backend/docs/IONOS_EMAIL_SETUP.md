# IONOS Email SMTP Configuration

This guide shows you how to configure the email agent with your IONOS domain email server.

## IONOS SMTP Server Details

IONOS provides SMTP servers for sending emails from your custom domain. Here are the settings you need:

### Configuration for .env file

Add these settings to your `.env` file:

**IMPORTANT**: Also set your application URL for email links:

```bash
# Application URL (for email links)
APP_URL=https://yourdomain.com

# IONOS Email/SMTP Configuration
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USERNAME=your-email@yourdomain.com
SMTP_PASSWORD=your-email-password
SMTP_FROM_EMAIL=your-email@yourdomain.com
SMTP_FROM_NAME=Nova VAT Assistant
SMTP_USE_TLS=true
```

### Alternative IONOS SMTP Settings

IONOS supports multiple configurations:

**Option 1: TLS/STARTTLS (Recommended)**
```bash
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

**Option 2: SSL/TLS**
```bash
SMTP_HOST=smtp.ionos.com
SMTP_PORT=465
SMTP_USE_TLS=false  # Port 465 uses implicit SSL
```

**Option 3: No Encryption (Not Recommended)**
```bash
SMTP_HOST=smtp.ionos.com
SMTP_PORT=25
SMTP_USE_TLS=false
```

## Step-by-Step Setup

### 1. Get Your IONOS Email Credentials

You need:
- **Email address**: your-email@yourdomain.com
- **Password**: The password you set when creating the email account

To find or reset your password:
1. Log in to your IONOS account at https://www.ionos.com
2. Go to **Email & Office** → **Email**
3. Click on your email account
4. Reset password if needed

### 2. Update Your .env File

Replace the placeholder values with your actual credentials:

```bash
SMTP_USERNAME=info@yourdomain.com        # Your full email address
SMTP_PASSWORD=YourActualPassword          # Your email password
SMTP_FROM_EMAIL=info@yourdomain.com      # Same as username
SMTP_FROM_NAME=Your Company Name         # Display name for sent emails
```

### 3. Test the Configuration

Start your server and test sending an email:

```bash
# Start the server
uvicorn app.main:app --reload

# Test sending an email (in another terminal)
curl -X POST "http://localhost:8000/api/v1/email/send" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "your-test-email@gmail.com",
    "to_name": "Test User",
    "subject": "Test Email from Nova VAT",
    "body": "This is a test email to verify IONOS SMTP configuration.",
    "purpose": "general",
    "tone": "professional"
  }'
```

## Common Email Addresses for Business

Choose appropriate email addresses based on purpose:

- **info@yourdomain.com** - General inquiries and communications
- **support@yourdomain.com** - Support requests
- **noreply@yourdomain.com** - Automated emails (notifications, reminders)
- **accounts@yourdomain.com** - Accounting and VAT related emails
- **admin@yourdomain.com** - Administrative communications

Set `SMTP_FROM_EMAIL` to whichever email you want to send from.

## Advanced Configuration

### Using Different Reply-To Address

You can set a different reply-to address when sending emails:

```python
response = requests.post("http://localhost:8000/api/v1/email/send", json={
    "to_email": "client@example.com",
    "subject": "VAT Documents Required",
    "body": "...",
    "purpose": "missing_documents",
    "reply_to": "support@yourdomain.com"  # Replies go here
})
```

### Multiple From Addresses

If you have multiple IONOS email accounts, you can only send from the account you authenticate with (`SMTP_USERNAME`). To send from different addresses:

1. **Option A**: Change `SMTP_USERNAME` and `SMTP_PASSWORD` in .env (requires restart)
2. **Option B**: Set up email forwarding/aliases in IONOS
3. **Option C**: Use the same sending address but different `SMTP_FROM_NAME`

## Troubleshooting

### Error: Authentication Failed

**Problem**: Wrong username or password

**Solutions**:
1. Verify your email address is correct (must be full address: user@domain.com)
2. Check password is correct
3. Try resetting the password in IONOS control panel
4. Make sure you're using the IONOS email password, not your IONOS account password

### Error: Connection Timeout

**Problem**: Cannot connect to SMTP server

**Solutions**:
1. Check firewall isn't blocking ports 587 or 465
2. Verify SMTP_HOST is exactly `smtp.ionos.com`
3. Try alternative port (465 instead of 587)
4. Check your internet connection

### Error: TLS/SSL Error

**Problem**: Encryption handshake failed

**Solutions**:
1. For port 587: Set `SMTP_USE_TLS=true`
2. For port 465: Set `SMTP_USE_TLS=false`
3. Update Python SSL certificates: `pip install --upgrade certifi`

### Error: Relay Access Denied

**Problem**: IONOS won't relay your emails

**Solutions**:
1. Make sure `SMTP_FROM_EMAIL` matches `SMTP_USERNAME`
2. Verify your email account is active in IONOS
3. Check you haven't exceeded IONOS sending limits

### Emails Going to Spam

**Solutions**:
1. Configure SPF record in your domain DNS
2. Configure DKIM in IONOS email settings
3. Add DMARC policy to your domain
4. Ensure your domain has proper reverse DNS

## IONOS Email Limits

Be aware of IONOS sending limits:

- **Standard plans**: Typically 500-1000 emails per day
- **Business plans**: Higher limits (check your plan)
- **Rate limiting**: Avoid sending too many emails at once

If you need to send bulk emails, consider:
1. Spacing out emails over time
2. Upgrading your IONOS plan
3. Using a dedicated email service (SendGrid, Mailgun, etc.)

## DNS Configuration (Optional but Recommended)

For better email deliverability, configure these DNS records in your IONOS domain settings:

### SPF Record
```
Type: TXT
Name: @
Value: v=spf1 include:_spf.perfora.net include:_spf.ionos.com ~all
```

### DMARC Record
```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=none; rua=mailto:postmaster@yourdomain.com
```

DKIM is usually configured automatically by IONOS.

## Security Best Practices

1. **Use strong passwords** for your IONOS email accounts
2. **Enable 2FA** on your IONOS account (not the email itself)
3. **Don't commit .env** to version control (it contains passwords)
4. **Rotate passwords** regularly
5. **Monitor sent emails** for unauthorized usage
6. **Use environment-specific emails** (different emails for dev/staging/production)

## Example Complete .env File

```bash
# Database
DATABASE_PATH=postgresql://user:password@host:5432/dbname

# Storage
UPLOADTHING_TOKEN=your_uploadthing_token_here

# AI Provider
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# IONOS Email Configuration
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USERNAME=accounts@yourdomain.com
SMTP_PASSWORD=YourSecurePassword123!
SMTP_FROM_EMAIL=accounts@yourdomain.com
SMTP_FROM_NAME=Nova VAT Assistant
SMTP_USE_TLS=true

# Application
DEBUG=false
```

## Integration Examples

### Chat Agent Sending Email

The chat agent can now send emails automatically:

**User**: "Send a reminder email to john@example.com about missing documents"

**Nova AI**: *Uses send_email tool to compose and send the email*

### Chaser Sending Email

```bash
# Generate and send chaser email
curl -X POST "http://localhost:8000/api/v1/chaser/requests/123/send-email"
```

This will:
1. Generate AI message if not already generated
2. Send email via IONOS SMTP
3. Mark chaser as sent

## Support

If you encounter issues:

1. **Check IONOS Status**: https://status.ionos.com
2. **IONOS Support**: Contact IONOS customer support
3. **Application Logs**: Check your application logs for detailed error messages
4. **Test SMTP**: Use a tool like `telnet smtp.ionos.com 587` to test connectivity

## Further Reading

- IONOS Email Documentation: https://www.ionos.com/help/email/
- SMTP Protocol: https://en.wikipedia.org/wiki/Simple_Mail_Transfer_Protocol
- Email Deliverability Best Practices: https://www.validity.com/blog/email-deliverability-best-practices/

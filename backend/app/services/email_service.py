"""Email service for composing and sending emails with AI assistance."""

import asyncio
import base64
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from sqlalchemy.orm import Session

from app.ai.provider import AIProvider
from app.config import Settings, get_settings
from app.models.client import Client
from app.schemas.email import (
    AIEmailGenerationRequest,
    EmailPurpose,
    EmailRequest,
    EmailResponse,
    EmailTone,
)


class EmailService:
    """Service for composing and sending emails with AI assistance."""

    def __init__(self, db: Session, ai_provider: AIProvider | None = None):
        """Initialize email service.

        Args:
            db: Database session
            ai_provider: AI provider for email composition (optional)
        """
        self.db = db
        self.ai_provider = ai_provider
        self.settings: Settings = get_settings()
        self._logo_base64: str | None = None

    def _get_logo_base64(self) -> str:
        """Get Nova logo as base64 encoded string for email embedding.

        Returns:
            Base64 encoded logo SVG
        """
        if self._logo_base64:
            return self._logo_base64

        # Try to read logo from public folder
        logo_paths = [
            "../public/logo.svg",  # From backend folder
            "../../public/logo.svg",  # Alternative path
            "/app/public/logo.svg",  # Docker path
        ]

        logo_svg = None
        for path in logo_paths:
            try:
                full_path = os.path.join(os.path.dirname(__file__), path)
                if os.path.exists(full_path):
                    with open(full_path, 'rb') as f:
                        logo_svg = f.read()
                    break
            except Exception:
                continue

        # Fallback to hardcoded logo if file not found
        if not logo_svg:
            logo_svg = b'''<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <circle cx="256" cy="256" r="256" fill="#000000"/>
  <path d="M256 96 C170 96 112 158 112 236 V292 C112 320 142 340 176 340 H300 C338 340 368 316 368 284 V236 C368 158 342 96 256 96 Z" fill="#FFFFFF"/>
  <rect x="190" y="210" rx="14" ry="14" width="28" height="56" fill="#000000"/>
  <rect x="252" y="220" rx="14" ry="14" width="28" height="48" fill="#000000"/>
</svg>'''

        self._logo_base64 = base64.b64encode(logo_svg).decode('utf-8')
        return self._logo_base64

    def _wrap_in_html_template(self, body: str, subject: str = "") -> str:
        """Wrap email body in professional HTML template with Nova branding.

        Args:
            body: Email body content (can be plain text or simple HTML)
            subject: Email subject for reference

        Returns:
            Full HTML email with Nova branding
        """
        logo_base64 = self._get_logo_base64()

        # Convert plain text to HTML if needed
        if not ("<p>" in body.lower() or "<div>" in body.lower() or "<html>" in body.lower()):
            # Simple text - convert line breaks to paragraphs
            paragraphs = body.split('\n\n')
            body_html = ''.join(f'<p style="margin: 0 0 16px 0; line-height: 1.6;">{p.replace(chr(10), "<br>")}</p>' for p in paragraphs if p.strip())
        else:
            body_html = body

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #fafafa;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fafafa; padding: 40px 20px;">
        <tr>
            <td align="center">
                <!-- Main Container -->
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border: 1px solid #e8e8e8; border-radius: 4px;">
                    <!-- Header with Logo -->
                    <tr>
                        <td style="padding: 32px 40px; text-align: center; border-bottom: 1px solid #e8e8e8;">
                            <img src="data:image/svg+xml;base64,{logo_base64}" alt="Nova" width="48" height="48" style="display: inline-block; vertical-align: middle;">
                            <span style="font-size: 20px; font-weight: 500; color: #000000; margin-left: 12px; vertical-align: middle;">Nova</span>
                        </td>
                    </tr>

                    <!-- Body Content -->
                    <tr>
                        <td style="padding: 40px; color: #000000cc; font-size: 16px; line-height: 1.6;">
                            {body_html}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; background-color: #fafafa; border-top: 1px solid #e8e8e8; text-align: center;">
                            <p style="margin: 0 0 8px 0; font-size: 14px; color: #9ba1a5;">
                                Powered by Nova - 10x Your Accounting Power
                            </p>
                            <p style="margin: 0; font-size: 12px; color: #9ba1a5;">
                                © 2026 Nova. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''

    def _get_system_prompt(self) -> str:
        """Get system prompt for email generation."""
        return """You are an AI assistant for Nova, the AI-powered platform that helps accountants 10x their productivity.

Your role is to:
- Write clear, professional, and courteous emails
- Maintain appropriate tone based on the email purpose
- Include relevant information from the context provided
- Follow UK business email etiquette
- Be concise but informative and helpful
- Reflect Nova's mission to make accountants unstoppable

Guidelines:
- Use proper email structure (greeting, body, closing)
- Address the recipient by name when available
- Stay focused on the purpose of the email
- Use professional language appropriate for accountancy services
- Include relevant details from the context
- End with a clear call-to-action if needed
- For welcome emails, be warm and welcoming while being professional
- Include clickable links when URLs are provided
- Use bullet points or numbered lists for steps/items when appropriate
- Keep the tone helpful and supportive, not overwhelming
- Emphasize how Nova helps save time and increase efficiency

Email Structure:
1. Warm greeting with recipient's name
2. Brief introduction explaining the purpose
3. Main content with relevant information, steps, or lists
4. Clear call-to-action with any links
5. Professional closing with offer to help

Remember: You're helping accountants save time and work smarter with Nova's AI-powered tools. Be clear, helpful, and encouraging.
"""

    def _build_generation_prompt(
        self,
        purpose: EmailPurpose,
        tone: EmailTone,
        recipient_name: str | None = None,
        client_name: str | None = None,
        context_data: dict | None = None,
    ) -> str:
        """Build prompt for AI email generation.

        Args:
            purpose: Email purpose
            tone: Email tone
            recipient_name: Name of recipient
            client_name: Name of client company
            context_data: Additional context

        Returns:
            Formatted prompt for AI
        """
        prompt_parts = [
            f"Compose an email with the following specifications:",
            f"",
            f"Purpose: {purpose.value}",
            f"Tone: {tone.value}",
        ]

        if recipient_name:
            prompt_parts.append(f"Recipient Name: {recipient_name}")

        if client_name:
            prompt_parts.append(f"Client Company: {client_name}")

        if context_data:
            prompt_parts.append(f"")
            prompt_parts.append(f"Context Information:")
            for key, value in context_data.items():
                prompt_parts.append(f"- {key}: {value}")

        # Add purpose-specific instructions
        purpose_instructions = {
            EmailPurpose.REMINDER: "Remind the client about pending tasks or upcoming deadlines in a polite manner.",
            EmailPurpose.MISSING_DOCUMENTS: "Request missing documents needed for VAT return preparation. Be specific about what's needed.",
            EmailPurpose.VAT_RETURN_READY: "Notify the client that their VAT return is ready for review.",
            EmailPurpose.VALIDATION_ISSUES: "Inform the client about validation issues found in their documents. Be constructive and helpful.",
            EmailPurpose.INVOICE_REQUEST: "Request specific invoices or receipts from the client.",
            EmailPurpose.FOLLOW_UP: "Follow up on a previous communication or request.",
            EmailPurpose.WELCOME: """Welcome a new client to Nova. This is their first interaction with us, so:
- Be warm, welcoming, and enthusiastic
- Explain how Nova helps accountants work smarter and save time
- Include the onboarding URL as a clickable link
- List the clear steps they need to follow (use numbered list from context)
- Mention the required documents they'll need to upload (use list from context)
- Highlight the benefits of using Nova (from context)
- End with support information and encourage them to reach out with questions
- Make them feel confident and excited to get started""",
            EmailPurpose.GENERAL: "General communication with the client.",
        }

        if purpose in purpose_instructions:
            prompt_parts.append(f"")
            prompt_parts.append(f"Specific Instructions: {purpose_instructions[purpose]}")

        prompt_parts.append(f"")
        prompt_parts.append(
            f"Please provide the email in the following JSON format:"
        )
        prompt_parts.append(f'{{"subject": "Email subject here", "body": "Email body here"}}')
        prompt_parts.append(f"")
        prompt_parts.append(f"Keep the subject concise (under 60 characters) and the body professional and to the point.")

        return "\n".join(prompt_parts)

    async def _generate_email_content(
        self,
        purpose: EmailPurpose,
        tone: EmailTone,
        recipient_name: str | None = None,
        client_name: str | None = None,
        context_data: dict | None = None,
    ) -> dict[str, str]:
        """Generate email subject and body using AI.

        Args:
            purpose: Email purpose
            tone: Email tone
            recipient_name: Name of recipient
            client_name: Name of client company
            context_data: Additional context

        Returns:
            Dictionary with 'subject' and 'body' keys
        """
        if not self.ai_provider:
            raise ValueError("AI provider is required for email generation")

        system_prompt = self._get_system_prompt()
        user_prompt = self._build_generation_prompt(
            purpose=purpose,
            tone=tone,
            recipient_name=recipient_name,
            client_name=client_name,
            context_data=context_data,
        )

        # Call AI provider
        response = await self.ai_provider.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        # Parse JSON response
        import json

        try:
            # Try to extract JSON from response
            content = response.strip()
            # Handle potential markdown code blocks
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])
            if content.startswith("json"):
                content = content[4:].strip()

            email_data = json.loads(content)
            return {
                "subject": email_data.get("subject", ""),
                "body": email_data.get("body", ""),
            }
        except json.JSONDecodeError:
            # Fallback: try to extract subject and body manually
            lines = response.split("\n")
            subject = ""
            body_lines = []
            in_body = False

            for line in lines:
                if line.lower().startswith("subject:"):
                    subject = line.split(":", 1)[1].strip()
                elif subject and not in_body:
                    in_body = True
                    body_lines.append(line)
                elif in_body:
                    body_lines.append(line)

            return {
                "subject": subject or "Message from Nova",
                "body": "\n".join(body_lines).strip() or response,
            }

    def _send_smtp_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        to_name: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
    ) -> str:
        """Send email via SMTP.

        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body (HTML or plain text)
            to_name: Recipient name
            cc: CC recipients
            bcc: BCC recipients
            reply_to: Reply-to address

        Returns:
            Message ID

        Raises:
            ValueError: If SMTP settings are not configured
            smtplib.SMTPException: If email sending fails
        """
        if not self.settings.smtp_host or not self.settings.smtp_username:
            raise ValueError(
                "SMTP settings are not configured. Please set SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD in environment variables."
            )

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.settings.smtp_from_name} <{self.settings.smtp_from_email}>"
        msg["To"] = f"{to_name} <{to_email}>" if to_name else to_email

        if cc:
            msg["Cc"] = ", ".join(cc)
        if bcc:
            msg["Bcc"] = ", ".join(bcc)
        if reply_to:
            msg["Reply-To"] = reply_to

        # Add body (support both plain text and HTML)
        # Always wrap in HTML template for brand consistency
        if "<html>" in body.lower() and "<!DOCTYPE" in body:
            # Already a full HTML document
            html_body = body
        else:
            # Wrap in Nova branded HTML template
            html_body = self._wrap_in_html_template(body, subject)

        # Attach both plain text and HTML versions
        plain_body = body if not ("<html>" in body.lower() or "<p>" in body.lower()) else body
        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        # Send email
        try:
            if self.settings.smtp_use_tls:
                # Use STARTTLS
                with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                    server.starttls()
                    server.login(self.settings.smtp_username, self.settings.smtp_password)
                    server.send_message(msg)
            else:
                # Use SSL/TLS directly
                with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port) as server:
                    server.login(self.settings.smtp_username, self.settings.smtp_password)
                    server.send_message(msg)

            return msg["Message-ID"] or f"<{datetime.utcnow().timestamp()}@nova-vat>"

        except smtplib.SMTPAuthenticationError:
            raise ValueError("SMTP authentication failed. Please check your credentials.")
        except smtplib.SMTPException as e:
            raise ValueError(f"Failed to send email: {str(e)}")

    async def send_email(self, request: EmailRequest) -> EmailResponse:
        """Send email with optional AI generation.

        Args:
            request: Email request with recipient and content

        Returns:
            EmailResponse with send status
        """
        subject = request.subject
        body = request.body
        generated_subject = None
        generated_body = None

        # Generate email content if not provided
        if not subject or not body:
            # Get client context if available
            client_name = None
            recipient_name = request.to_name

            if request.client_id:
                client = self.db.get(Client, request.client_id)
                if client:
                    client_name = client.name
                    if not recipient_name:
                        recipient_name = client.contact_name

            # Generate content using AI
            generated = await self._generate_email_content(
                purpose=request.purpose,
                tone=request.tone,
                recipient_name=recipient_name,
                client_name=client_name,
                context_data=request.context_data,
            )

            if not subject:
                subject = generated["subject"]
                generated_subject = subject

            if not body:
                body = generated["body"]
                generated_body = body

        # Send email via SMTP
        try:
            message_id = self._send_smtp_email(
                to_email=request.to_email,
                subject=subject,
                body=body,
                to_name=request.to_name,
                cc=request.cc,
                bcc=request.bcc,
                reply_to=request.reply_to,
            )

            return EmailResponse(
                success=True,
                message="Email sent successfully",
                message_id=message_id,
                generated_subject=generated_subject,
                generated_body=generated_body,
                sent_at=datetime.utcnow(),
            )

        except Exception as e:
            return EmailResponse(
                success=False,
                message=f"Failed to send email: {str(e)}",
                generated_subject=generated_subject,
                generated_body=generated_body,
            )

    async def generate_preview(
        self,
        purpose: EmailPurpose,
        tone: EmailTone,
        recipient_name: str | None = None,
        client_id: int | None = None,
        context_data: dict | None = None,
    ) -> dict[str, str]:
        """Generate email preview without sending.

        Args:
            purpose: Email purpose
            tone: Email tone
            recipient_name: Name of recipient
            client_id: Client ID for context
            context_data: Additional context

        Returns:
            Dictionary with 'subject' and 'body' keys
        """
        client_name = None
        if client_id:
            client = self.db.get(Client, client_id)
            if client:
                client_name = client.name
                if not recipient_name:
                    recipient_name = client.contact_name

        return await self._generate_email_content(
            purpose=purpose,
            tone=tone,
            recipient_name=recipient_name,
            client_name=client_name,
            context_data=context_data,
        )

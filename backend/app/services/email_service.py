"""Email service for composing and sending emails with AI assistance."""

import asyncio
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

    def _get_system_prompt(self) -> str:
        """Get system prompt for email generation."""
        return """You are an AI assistant for Nova VAT Readiness Tool, helping to compose professional emails to clients.

Your role is to:
- Write clear, professional, and courteous emails
- Maintain appropriate tone based on the email purpose
- Include relevant information from the context provided
- Follow UK business email etiquette
- Be concise but informative and helpful

Guidelines:
- Use proper email structure (greeting, body, closing)
- Address the recipient by name when available
- Stay focused on the purpose of the email
- Use professional language appropriate for accountancy/VAT services
- Include relevant details from the context
- End with a clear call-to-action if needed
- For welcome emails, be warm and welcoming while being professional
- Include clickable links when URLs are provided
- Use bullet points or numbered lists for steps/items when appropriate
- Keep the tone helpful and supportive, not overwhelming

Email Structure:
1. Warm greeting with recipient's name
2. Brief introduction explaining the purpose
3. Main content with relevant information, steps, or lists
4. Clear call-to-action with any links
5. Professional closing with offer to help

Remember: You're helping clients navigate VAT compliance, which can be complex. Be clear, helpful, and encouraging.
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
            EmailPurpose.WELCOME: """Welcome a new client to the Nova VAT system. This is their first interaction with us, so:
- Be warm, welcoming, and enthusiastic
- Explain what Nova VAT does and how it will help them
- Include the onboarding URL as a clickable link
- List the clear steps they need to follow (use numbered list from context)
- Mention the required documents they'll need to upload (use list from context)
- Highlight the benefits of using the system (from context)
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
                "subject": subject or "Message from Nova VAT",
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
        if "<html>" in body.lower() or "<p>" in body.lower():
            # HTML email
            msg.attach(MIMEText(body, "html"))
        else:
            # Plain text email
            msg.attach(MIMEText(body, "plain"))

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

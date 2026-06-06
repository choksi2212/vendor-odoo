"""
Async email delivery via Brevo (formerly Sendinblue) HTTP API.

Railway blocks all outbound SMTP; Brevo's API uses plain HTTPS so it always
works. The free tier gives 300 emails/day with no domain required - just verify
a sender email address in the Brevo dashboard.

All send_* functions are fire-and-forget safe - exceptions are caught and
logged so a mail failure never crashes a request.

Call them with FastAPI BackgroundTasks:
    background_tasks.add_task(email.send_verification_email, user.email, raw_token)
"""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_BREVO_URL = "https://api.brevo.com/v3/smtp/email"


async def _send(subject: str, to: str, html: str) -> None:
    """Send an HTML email via Brevo's transactional email API."""
    sender_email = settings.email_from
    sender_name = settings.email_from_name

    if not settings.BREVO_API_KEY or not sender_email:
        logger.warning(
            "Email not configured (BREVO_API_KEY or sender missing) - "
            "skipped delivery to %s (subject=%r)", to, subject
        )
        return

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": html,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                _BREVO_URL,
                headers={"api-key": settings.BREVO_API_KEY, "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            logger.info("Email sent successfully to %s (subject=%r)", to, subject)
    except Exception:
        logger.error("Email delivery failed to %s (subject=%r)", to, subject, exc_info=True)


async def _send_with_attachment(
    subject: str, to: str, html: str, attachment_bytes: bytes, attachment_name: str
) -> None:
    """Send an HTML email with a PDF attachment via Brevo API."""
    import base64

    sender_email = settings.email_from
    sender_name = settings.email_from_name

    if not settings.BREVO_API_KEY or not sender_email:
        logger.warning(
            "Email not configured - skipped delivery to %s (subject=%r)", to, subject
        )
        return

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": html,
        "attachment": [
            {
                "content": base64.b64encode(attachment_bytes).decode(),
                "name": attachment_name,
            }
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                _BREVO_URL,
                headers={"api-key": settings.BREVO_API_KEY, "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            logger.info("Email with attachment sent to %s (subject=%r)", to, subject)
    except Exception:
        logger.error("Email delivery failed to %s (subject=%r)", to, subject, exc_info=True)


# ─── HTML Template Shell ──────────────────────────────────────────────────────


def _wrap(body_html: str) -> str:
    """Wrap email body in VendorBridge branded template."""
    return f"""<!DOCTYPE html>
<html lang="en">
<body style="margin:0;padding:0;background:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:48px 20px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e5e7eb;">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#2563eb 0%,#1d4ed8 100%);padding:28px 40px;">
            <h1 style="color:#ffffff;margin:0;font-size:20px;font-weight:600;letter-spacing:-0.3px;">
              VendorBridge
            </h1>
            <p style="color:#bfdbfe;margin:4px 0 0;font-size:12px;">
              Procurement &amp; Vendor Management System
            </p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:40px;">
            {body_html}
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:20px 40px;border-top:1px solid #f3f4f6;">
            <p style="color:#9ca3af;font-size:12px;margin:0;line-height:1.5;">
              You received this email from VendorBridge.
              If you did not request this action, you can safely ignore this message.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ─── Auth Email Senders ───────────────────────────────────────────────────────


async def send_verification_email(to: str, token: str) -> None:
    """Send email verification link."""
    link = f"{settings.APP_BASE_URL}/verify-email?token={token}"
    body = f"""
<h2 style="margin:0 0 10px;font-size:22px;font-weight:700;color:#0f0f1a;">
  Verify your email address
</h2>
<p style="color:#6b7280;line-height:1.65;margin:0 0 28px;">
  Welcome to VendorBridge! Click the button below to confirm your email address.<br>
  This link is valid for <strong style="color:#0f0f1a;">24 hours</strong>.
</p>
<a href="{link}"
   style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;
          padding:13px 28px;border-radius:8px;font-size:14px;font-weight:500;">
  Verify Email Address
</a>
<p style="color:#9ca3af;font-size:12px;margin:24px 0 0;line-height:1.6;">
  If the button doesn't work, paste this link into your browser:<br>
  <a href="{link}" style="color:#2563eb;word-break:break-all;">{link}</a>
</p>"""
    await _send("Verify your email - VendorBridge", to, _wrap(body))


async def send_reset_email(to: str, token: str) -> None:
    """Send password reset link."""
    link = f"{settings.APP_BASE_URL}/reset-password?token={token}"
    body = f"""
<h2 style="margin:0 0 10px;font-size:22px;font-weight:700;color:#0f0f1a;">
  Reset your password
</h2>
<p style="color:#6b7280;line-height:1.65;margin:0 0 28px;">
  We received a request to reset the password for your VendorBridge account.<br>
  This link expires in <strong style="color:#0f0f1a;">1 hour</strong>.
  If you didn't make this request, no action is needed.
</p>
<a href="{link}"
   style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;
          padding:13px 28px;border-radius:8px;font-size:14px;font-weight:500;">
  Reset Password
</a>
<p style="color:#9ca3af;font-size:12px;margin:24px 0 0;line-height:1.6;">
  Direct link:<br>
  <a href="{link}" style="color:#2563eb;word-break:break-all;">{link}</a>
</p>"""
    await _send("Reset your password - VendorBridge", to, _wrap(body))


async def send_otp_email(to: str, otp: str) -> None:
    """Send 2FA OTP code."""
    body = f"""
<h2 style="margin:0 0 10px;font-size:22px;font-weight:700;color:#0f0f1a;">
  Your verification code
</h2>
<p style="color:#6b7280;line-height:1.65;margin:0 0 24px;">
  Use the code below to complete your sign-in.
  It expires in <strong style="color:#0f0f1a;">5 minutes</strong>.
</p>
<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;
            padding:28px;text-align:center;margin:0 0 24px;">
  <span style="font-size:40px;font-weight:700;letter-spacing:14px;
               color:#0f0f1a;font-family:'Courier New',Courier,monospace;">
    {otp}
  </span>
</div>
<p style="color:#6b7280;font-size:13px;margin:0;line-height:1.6;">
  This code is single-use. Never share it with anyone -
  VendorBridge will <strong>never</strong> ask you for it.
</p>"""
    await _send("Your login OTP - VendorBridge", to, _wrap(body))


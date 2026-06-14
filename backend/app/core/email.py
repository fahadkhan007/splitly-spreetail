# app/core/email.py
#
# Email sending via the Resend API.
# All email templates live here.
#
# DEV MODE: If RESEND_API_KEY is not set (or left as the placeholder),
# emails are NOT sent — the link is printed to the terminal console instead.
# This lets you test the full flow without needing a real Resend account.

import resend

from app.config import settings


def _is_dev_mode() -> bool:
    """Returns True if the Resend API key hasn't been configured yet."""
    return not settings.RESEND_API_KEY or settings.RESEND_API_KEY.startswith("re_your")


def send_verification_email(to_email: str, verification_link: str) -> None:
    """
    Sends an account verification email to a newly registered user.
    The email contains a link they must click to verify their email address.
    """
    if _is_dev_mode():
        # In development: print the link so you can test without Resend
        print("\n" + "="*60)
        print(f"[DEV] Verification email for: {to_email}")
        print(f"[DEV] Click this link to verify: {verification_link}")
        print("="*60 + "\n")
        return

    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send({
        "from": "Splitly <noreply@splitly.app>",
        "to": [to_email],
        "subject": "Verify your Splitly account",
        "html": f"""
        <div style="font-family: sans-serif; max-width: 480px; margin: auto; padding: 24px;">
            <h2 style="color: #1a73e8;">Welcome to Splitly!</h2>
            <p>Click the button below to verify your email address and activate your account.</p>
            <a href="{verification_link}"
               style="background:#1a73e8; color:white; padding:12px 24px;
                      border-radius:6px; text-decoration:none; display:inline-block; margin:16px 0;">
                Verify Email
            </a>
            <p style="color:#888; font-size:13px;">
                This link expires in 24 hours.<br>
                If you didn't create a Splitly account, you can safely ignore this email.
            </p>
        </div>
        """,
    })


def send_group_invitation_email(to_email: str, group_name: str, invited_by: str, invite_link: str) -> None:
    """
    Sends a group invitation email.
    Called when a group admin invites someone to join their group.
    """
    if _is_dev_mode():
        print("\n" + "="*60)
        print(f"[DEV] Group invite email for: {to_email}")
        print(f"[DEV] Group: {group_name} | Invited by: {invited_by}")
        print(f"[DEV] Invite link: {invite_link}")
        print("="*60 + "\n")
        return

    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send({
        "from": "Splitly <noreply@splitly.app>",
        "to": [to_email],
        "subject": f"{invited_by} invited you to join {group_name} on Splitly",
        "html": f"""
        <div style="font-family: sans-serif; max-width: 480px; margin: auto; padding: 24px;">
            <h2 style="color: #1a73e8;">You're invited!</h2>
            <p><strong>{invited_by}</strong> has invited you to join the group
               <strong>{group_name}</strong> on Splitly.</p>
            <a href="{invite_link}"
               style="background:#1a73e8; color:white; padding:12px 24px;
                      border-radius:6px; text-decoration:none; display:inline-block; margin:16px 0;">
                Accept Invitation
            </a>
            <p style="color:#888; font-size:13px;">
                This invitation expires in 7 days.
            </p>
        </div>
        """,
    })

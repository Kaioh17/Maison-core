"""Shared Maison transactional email layout: wordmark header, typography, footer year, CTA button."""
from __future__ import annotations

import html
from datetime import datetime
from typing import Optional

FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
FONT_MONO = (
    "ui-monospace, 'SF Mono', 'Cascadia Code', 'Segoe UI Mono', Menlo, Monaco, "
    "Consolas, monospace"
)
HIGHLIGHT_BG = "#f3f4f6"
HIGHLIGHT_BORDER = "#e5e7eb"
HIGHLIGHT_TEXT = "#374151"
TEXT = "#111827"
MUTED = "#6b7280"
# Lighter slate for booking detail labels (Passenger, Route, …) vs body values
DETAIL_LABEL = "#94a3b8"
BTN_BG = "#111827"
BTN_BORDER = "#6d5f8a"  # muted purple accent

WARN_BOX_BG = "#fef9c3"
WARN_BOX_BORDER = "#eab308"
WARN_BOX_TEXT = "#713f12"

# Outer wrapper matches card (no gray “mat”); inner column max width for readability in clients.
EMAIL_OUTER_BG = "#ffffff"
EMAIL_INNER_MAX_WIDTH = "820px"
# Minimal gutter: shell is mostly full-bleed; content uses almost full card width.
EMAIL_SHELL_PADDING = "12px 0 0 0"
EMAIL_CONTENT_PAD_X = "12px"


def _year() -> int:
    return datetime.now().year


def wordmark_row(operator: str = 'Maison') -> str:
    return f"""
    <tr>
        <td style="padding: 28px {EMAIL_CONTENT_PAD_X} 18px {EMAIL_CONTENT_PAD_X}; border-bottom: 1px solid #e5e7eb;">
            <span style="font-family: {FONT}; font-size: 17px; font-weight: 600; color: {TEXT}; letter-spacing: -0.03em;">{operator}</span>
        </td>
    </tr>
    """


def footer_row(brand_name: str = "Maison", unsubscribe_href: str = "#") -> str:
    y = _year()
    return f"""
    <tr>
        <td style="padding: 28px {EMAIL_CONTENT_PAD_X} 36px {EMAIL_CONTENT_PAD_X}; border-top: 1px solid #e5e7eb;">
            <p style="margin: 0 0 8px 0; font-family: {FONT}; font-size: 13px; line-height: 1.6; color: {MUTED}; text-align: center;">
                {brand_name}
            </p>
            <p style="margin: 0; font-family: {FONT}; font-size: 13px; line-height: 1.6; color: {MUTED}; text-align: center;">
                <a href="{unsubscribe_href}" style="color: {MUTED}; text-decoration: underline;">Unsubscribe</a>
                <span style="color: #d1d5db;"> · </span>
                {y}
            </p>
        </td>
    </tr>
    """


def p(text: str, *, margin_bottom: str = "16px") -> str:
    return f"""<p style="margin: 0 0 {margin_bottom} 0; font-family: {FONT}; font-size: 16px; line-height: 1.65; color: {TEXT};">{text}</p>"""


def muted_p(text: str) -> str:
    return f"""<p style="margin: 16px 0 0 0; font-family: {FONT}; font-size: 16px; line-height: 1.65; color: {MUTED};">{text}</p>"""


def highlight(text: Optional[str]) -> str:
    """Markdown-style inline code look for addresses/routes (safe for HTML body)."""
    safe = html.escape(str(text) if text is not None else "", quote=False)
    return (
        f'<span style="font-family: {FONT_MONO}; font-size: 0.92em; font-weight: 500; '
        f"color: {HIGHLIGHT_TEXT}; background-color: {HIGHLIGHT_BG}; "
        f"border: 1px solid {HIGHLIGHT_BORDER}; border-radius: 4px; padding: 2px 7px; "
        f'word-break: break-word;">{safe}</span>'
    )


def detail_kv(key: str, value_html: str) -> str:
    """Booking-style line: muted label + value (value may contain HTML, e.g. highlight())."""
    k = html.escape(key.strip(), quote=False)
    return (
        f'<span style="color: {DETAIL_LABEL}; font-family: {FONT}; font-size: 16px; '
        f'font-weight: 500; line-height: 1.65;">{k}:</span> '
        f'<span style="font-family: {FONT}; font-size: 16px; line-height: 1.65; color: {TEXT};">'
        f"{value_html}</span>"
    )


def completed_ride_dispute_notice(
    contact_email: Optional[str],
    contact_phone: Optional[str],
    *,
    operator_name: str,
) -> str:
    """Yellow callout if the ride may have been completed in error (tenant contact)."""
    email = (contact_email or "").strip()
    phone = (contact_phone or "").strip()
    if not email and not phone:
        return ""

    op = html.escape(operator_name, quote=False)
    rows: list[str] = []
    if email:
        e_safe = html.escape(email, quote=False)
        e_attr = html.escape(email, quote=True)
        rows.append(
            f'<span style="color: {WARN_BOX_TEXT}; font-weight: 600;">Email:</span> '
            f'<a href="mailto:{e_attr}" style="color: {WARN_BOX_TEXT}; text-decoration: underline;">{e_safe}</a>'
        )
    if phone:
        p_safe = html.escape(phone, quote=False)
        tel = "".join(c for c in phone if c.isdigit() or c == "+")
        if not tel:
            tel = phone.replace(" ", "")
        tel_attr = html.escape(tel, quote=True)
        rows.append(
            f'<span style="color: {WARN_BOX_TEXT}; font-weight: 600;">Phone:</span> '
            f'<a href="tel:{tel_attr}" style="color: {WARN_BOX_TEXT}; text-decoration: underline;">{p_safe}</a>'
        )
    contacts = "<br/>".join(rows)

    return f"""
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 24px;">
        <tr>
            <td style="background-color: {WARN_BOX_BG}; border: 1px solid {WARN_BOX_BORDER}; border-radius: 8px; padding: 16px {EMAIL_CONTENT_PAD_X};">
                <p style="margin: 0 0 10px 0; font-family: {FONT}; font-size: 15px; font-weight: 600; color: {WARN_BOX_TEXT}; line-height: 1.5;">
                    Didn't take this ride?
                </p>
                <p style="margin: 0 0 12px 0; font-family: {FONT}; font-size: 15px; color: {WARN_BOX_TEXT}; line-height: 1.6;">
                    If this trip was marked complete by mistake or you never got in the vehicle,
                    please contact <strong style="color: {WARN_BOX_TEXT};">{op}</strong> right away:
                </p>
                <p style="margin: 0; font-family: {FONT}; font-size: 15px; line-height: 1.75; color: {WARN_BOX_TEXT};">
                    {contacts}
                </p>
            </td>
        </tr>
    </table>
    """


def signoff_maison_team() -> str:
    return p("— The Maison team", margin_bottom="0")


def primary_cta(href: str, label: str) -> str:
    return f"""
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 28px;">
        <tr>
            <td style="padding: 0;">
                <a href="{href}" style="display: block; width: 100%; box-sizing: border-box; padding: 14px 24px; background-color: {BTN_BG}; color: #ffffff; text-decoration: none; font-family: {FONT}; font-size: 16px; font-weight: 500; border-radius: 8px; text-align: center; border: 1px solid {BTN_BORDER};">{label}</a>
            </td>
        </tr>
    </table>
    """


def build_email(body_html: str, *, footer_brand: str = "Maison", unsubscribe_href: str = "#") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: {EMAIL_OUTER_BG}; font-family: {FONT};">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {EMAIL_OUTER_BG};">
        <tr>
            <td align="center" style="padding: {EMAIL_SHELL_PADDING};">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: {EMAIL_INNER_MAX_WIDTH}; width: 100%; background-color: #ffffff; border-radius: 8px; border: 1px solid #e5e7eb;">
                    {wordmark_row(footer_brand)}
                    <tr>
                        <td style="padding: 32px {EMAIL_CONTENT_PAD_X} 40px {EMAIL_CONTENT_PAD_X};">
                            {body_html}
                        </td>
                    </tr>
                    {footer_row(brand_name=footer_brand, unsubscribe_href=unsubscribe_href)}
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def first_name(full_name: Optional[str]) -> str:
    if not full_name or not str(full_name).strip():
        return "there"
    return str(full_name).strip().split()[0]

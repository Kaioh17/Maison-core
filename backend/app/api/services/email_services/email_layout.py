"""Shared Maison transactional email layout: wordmark header, typography, footer year, CTA button."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
TEXT = "#111827"
MUTED = "#6b7280"
BTN_BG = "#111827"
BTN_BORDER = "#6d5f8a"  # muted purple accent


def _year() -> int:
    return datetime.now().year


def wordmark_row(operator: str = 'Maison') -> str:
    return f"""
    <tr>
        <td style="padding: 28px 40px 18px 40px; border-bottom: 1px solid #e5e7eb;">
            <span style="font-family: {FONT}; font-size: 17px; font-weight: 600; color: {TEXT}; letter-spacing: -0.03em;">{operator}</span>
        </td>
    </tr>
    """


def footer_row(brand_name: str = "Maison", unsubscribe_href: str = "#") -> str:
    y = _year()
    return f"""
    <tr>
        <td style="padding: 28px 40px 36px 40px; border-top: 1px solid #e5e7eb;">
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
<body style="margin: 0; padding: 0; background-color: #f4f4f5; font-family: {FONT};">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f4f4f5;">
        <tr>
            <td align="center" style="padding: 40px 16px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);">
                    {wordmark_row(footer_brand)}
                    <tr>
                        <td style="padding: 32px 40px 40px 40px;">
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

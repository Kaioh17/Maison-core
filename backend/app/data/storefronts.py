from app.utils.logging import logger
from app.api.services.helper_service import format_phone, tenant_branding, tenant_table
def get_tenant_storefront(slug,  company_profile = None, tenant: tenant_table =None, db=None):
    """Retrieve tenant storefront configuration based on slug.

    Args:
        slug (str): The tenant slug identifier to determine storefront template.
        company_profile (object, optional): Company profile object containing company details. Defaults to None.
        tenant (object, optional): Tenant object containing contact information. Defaults to None.

    Returns:
        dict: A storefront configuration dictionary with template, branding, CTAs, and footer details.
    """
    logger.info(f'{slug}') 
    ALLOWED_PREMIUM=['bho']

    if slug.lower() in ALLOWED_PREMIUM:
        branding:tenant_branding = db.query(tenant_branding).filter(tenant_branding.tenant_id == tenant.id).first()
        
        logger.info(f'Premium {slug}')
        return {
        "template": "Premium",
        "tenant_name": "BHO Logistics",
        "wordmark": "BHO LOGISTICS",
        "caption": "PRIVATE CHAUFFEURS · CHICAGO",
        "hero": {
            "title": "Chauffeured transportation for Chicago, its airports, and the people who expect their driver to already know the route.",
            "supporting": "Black car service built for travelers who measure quality by what they don't have to think about. Book once, ride well, every time."
        },
        "ctas": {
            "primary": {
                "label": "Book a ride",
                "route": "rider_signup"
            },
            "secondary": {
                "label": "Existing client? Sign in",
                "route": "rider_login"
            }
        },
        "value_props": [
            {
                "title": "24/7 dispatch",
                "description": "Always reachable, always on time."
            },
            {
                "title": "Professional chauffeurs",
                "description": "Vetted, uniformed, route-fluent."
            },
            {
                "title": "Discreet service",
                "description": "Private, quiet, never anonymous."
            }
        ],
        "trust_line": "Trusted by travelers, hotels, and corporate guests across Chicago.",
        "palette": {
            "background": branding.background_color or "#F5EFE0",
            "text": branding.text_color or "#0F0F0E",
            "accent": branding.accent_color or "#0E1B2C",
            "muted": branding.text_muted_color or "#7A6F5C",
            "button_text": branding.button_text_color or "#7A6F5C"

        },
        "footer": {
            "copyright": "© BHO Logistics LLC",
            "links": [
                {"label": "Phone", "value": f"{format_phone(tenant.phone_no)}", "href": f"tel:{tenant.phone_no}"},
                {"label": "Email", "value": f"{tenant.email}", "href": f"mailto:{tenant.email}"}
            ]
        } 
    }
    else:
        ## default 
        logger.info(f'Default {slug}')

        return {
            "template": "default",
            "tenant_name": company_profile.company_name,
            "wordmark": company_profile.company_name,
            "welcome_label": f"WELCOME TO {company_profile.company_name.upper()}",
            "hero_title": "Your ride starts here",
            "hero_description": (
                f"Whether you are booking a trip or driving one, "
                f"{company_profile.company_name} runs this site for you. "
                f"Choose an option below to sign in or get started."
            ),
            "rider_card": {
                "title": "Riders & passengers",
                "description": (
                    f"Book and manage rides with {company_profile.company_name}. "
                    f"Sign in to your rider account or create one, it only takes a minute."
                ),
                "primary_cta": {
                    "label": "Rider sign in",
                    "route": "rider_login"
                },
                "secondary_cta": {
                    "label": "Create rider account",
                    "route": "rider_signup"
                }
            },
            "driver_card": {
                "title": "Drivers",
                "description": (
                    f"Partner with {company_profile.company_name} on the road. "
                    f"Sign in to your driver dashboard to manage trips and availability."
                ),
                "primary_cta": {
                    "label": "Driver sign in",
                    "route": "driver_login"
                }
            },
            "footer": {
                "copyright": f"© {company_profile.company_name}",
                "links": []
            }
        }
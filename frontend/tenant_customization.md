## Tenant Customization - Frontend Implementation Guide

### Overview
Maison supports a multi-tenant white-label architecture. Each tenant has their own **branded portal**, accessible via a unique subdomain:

- https://acme.ourapp.com
- https://uber-clone.ourapp.com

### Architecture Understanding

#### Backend Structure

- **Tenant Isolation**  
  All API routes are scoped using the `tenant_id` field to ensure tenant-specific data separation.

- **Authentication**  
  Uses OAuth2 + `current_user` dependency to ensure only authenticated users access tenant resources.

- **URL Structure**  
  The frontend receives requests from subdomains in the format:

  {slug}.ourapp.com

  The `{slug}` represents the tenant’s unique identifier.

---

### How it works

1. **User visits** `https://acme.ourapp.com`
2. **Frontend** extracts `acme` from the subdomain.
3. **Frontend** sends the slug with login or fetch requests if needed.
4. **Backend**:
 - Resolves the slug to a `tenant_id`
 - Automatically filters all data by this `tenant_id`
 - Ensures all resources and responses belong only to that tenant

---

### Frontend Responsibilities

- Extract tenant slug from `window.location.hostname`
- Use tenant slug to:
- Fetch tenant branding (logo, name, theme)
- Display custom UI elements
- All authenticated routes automatically inherit the tenant context from the login session

---
### Notes
- Tenant slug is only required at login or branding fetch

- Once logged in, all data is scoped via token → no need to resend slug

- Plan to cache tenant settings (logo, colors) locally per session
---

### Future Enhancements (Post-MVP)

- Custom fonts
- Layout modifications
- Feature toggling per tenant
- Advanced theme customization
- Mobile app theming
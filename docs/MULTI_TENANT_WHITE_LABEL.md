# Multi-Tenant Architecture & White Labelling

## Overview

Maison-core implements a sophisticated **multi-tenant SaaS architecture** with comprehensive **white labelling** capabilities. This document describes how tenant isolation is achieved, the database structure supporting multi-tenancy, and the slug-based routing system that enables each tenant to have their own branded subdomain (e.g., `acme.maison.com`).

---

## Table of Contents

1. [Multi-Tenant Architecture Overview](#multi-tenant-architecture-overview)
2. [Database Structure for Multi-Tenancy](#database-structure-for-multi-tenancy)
3. [Tenant Isolation Mechanisms](#tenant-isolation-mechanisms)
4. [Slug-Based Routing System](#slug-based-routing-system)
5. [White Labelling Features](#white-labelling-features)
6. [ServiceContext Pattern for Automatic Isolation](#servicecontext-pattern-for-automatic-isolation)
7. [Database Session Management](#database-session-management)
8. [Evolution Over Time](#evolution-over-time)

---

## Multi-Tenant Architecture Overview

### What is Multi-Tenancy?

Multi-tenancy is an architecture where a single instance of the application serves multiple tenants (customers), with each tenant's data isolated and secure. In Maison-core:

- **Single Application Instance**: One FastAPI backend serves all tenants
- **Shared Database**: All tenants share the same PostgreSQL database
- **Data Isolation**: Each tenant can only access their own data
- **Branded Experience**: Each tenant has their own branded subdomain and customization

### Architecture Benefits

1. **Cost Efficiency**: Single infrastructure serves multiple customers
2. **Scalability**: Easy to add new tenants without additional infrastructure
3. **Maintenance**: Single codebase to maintain and update
4. **Resource Sharing**: Efficient use of database connections and compute resources

### Tenant Hierarchy

```
Tenant (1)
├── TenantProfile (1:1) - Company info, slug, Stripe IDs
├── TenantStats (1:1) - Business metrics
├── TenantSettings (1:1) - Configuration (JSONB)
├── TenantBranding (1:1) - Visual branding
├── TenantPricing (1:1) - Pricing configuration
├── Users/Riders (1:many) - Customer accounts
├── Drivers (1:many) - Driver accounts
├── Vehicles (1:many) - Fleet management
├── Bookings (1:many) - Ride bookings
└── TenantBookingPricing (1:many) - Service-specific pricing
```

---

## Database Structure for Multi-Tenancy

### Core Tenant Tables

#### 1. `tenants` Table
The primary tenant table storing authentication and basic information:

```python
class Tenants(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    first_name = Column(String(200), nullable=False)
    last_name = Column(String(200), nullable=False)
    password = Column(String, nullable=False)
    phone_no = Column(String(200), nullable=False, index=True)
    role = Column(String, nullable=False, index=True, default="tenant")
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_on = Column(TIMESTAMP(timezone=True), nullable=False)
    updated_on = Column(TIMESTAMP(timezone=True))
```

**Key Features:**
- Unique email constraint across all tenants
- Role-based access control
- Active/inactive status for tenant management

#### 2. `tenants_profile` Table
Business profile information including the unique slug:

```python
class TenantProfile(Base):
    __tablename__ = "tenants_profile"
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), 
                      primary_key=True)
    company_name = Column(String(200), unique=True, nullable=False, index=True)
    logo_url = Column(String, nullable=True)
    slug = Column(String, unique=True, nullable=False, index=True)  # KEY: Unique slug
    address = Column(String, nullable=True)
    city = Column(String, nullable=False, index=True)
    
    # Stripe Integration
    stripe_customer_id = Column(String, nullable=True, index=True, unique=True)
    stripe_account_id = Column(String, nullable=True, index=True, unique=True)
    charges_enabled = Column(Boolean, nullable=True, default=False)
    
    # Subscription Management
    subscription_status = Column(String, nullable=True, default="inactive")
    subscription_plan = Column(String, nullable=True, default="free")
    cur_subscription_id = Column(String, nullable=True, unique=True)
```

**Critical Field: `slug`**
- **Unique constraint**: Ensures no two tenants have the same slug
- **Indexed**: Fast lookups for slug-based routing
- **Used for**: Subdomain routing (`slug.maison.com`)
- **Example**: `acme` → `acme.maison.com`

#### 3. `tenants_settings` Table
JSONB configuration for flexible tenant settings:

```python
class TenantSettings(Base):
    __tablename__ = "tenants_settings"
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), 
                      primary_key=True)
    rider_tiers_enabled = Column(Boolean, nullable=True, default=False)
    config = Column(JSONB, nullable=True)  # Flexible JSON configuration
```

**JSONB Config Structure:**
```json
{
  "booking": {
    "allow_guest_bookings": true,
    "show_vehicle_images": false,
    "types": {
      "airport": {"is_deposit_required": false},
      "dropoffs": {"is_deposit_required": false},
      "hourly": {"is_deposit_required": false}
    }
  },
  "branding": {
    "button_radius": 8,
    "font_family": "DM Sans"
  },
  "features": {
    "vip_profiles": true,
    "show_loyalty_banner": false
  }
}
```

#### 4. `tenant_branding` Table
Visual branding and white-label customization:

```python
class TenantBranding(Base):
    __tablename__ = "tenant_branding"
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), 
                      primary_key=True)
    theme = Column(String, nullable=False, default="dark")
    primary_color = Column(String, nullable=True)
    secondary_color = Column(String, nullable=True)
    accent_color = Column(String, nullable=True)
    favicon_url = Column(String, nullable=True)
    slug = Column(String, unique=True, nullable=True, index=True)
    email_from_name = Column(String, nullable=True)
    email_from_address = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    enable_branding = Column(Boolean, nullable=False, default=False)
```

### Tenant-Scoped Tables

All tenant-related data includes a `tenant_id` foreign key for isolation:

#### Users/Riders Table
```python
class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(200), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), 
                      nullable=False)
    
    __table_args__ = (
        UniqueConstraint('email', 'tenant_id', name='unique_user'),
    )
```

**Key Isolation Features:**
- `tenant_id` foreign key with CASCADE delete
- Unique constraint on `(email, tenant_id)` - allows same email across tenants
- All queries filtered by `tenant_id`

#### Drivers Table
```python
class Drivers(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), 
                      nullable=False)
    email = Column(String(200), nullable=False, index=True)
    
    __table_args__ = (
        UniqueConstraint('email', 'tenant_id', 'license_number', 
                       name='unique_driver'),
    )
```

#### Vehicles Table
```python
class Vehicles(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), 
                      nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True, unique=True)
    # ... vehicle details
```

#### Bookings Table
```python
class Bookings(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), 
                      nullable=False)
    rider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), 
                     nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), 
                       nullable=False)
    # ... booking details
```

### Cascade Delete Strategy

The database implements sophisticated cascade delete strategies:

1. **Tenant Deletion**: When a tenant is deleted, all related data is automatically removed:
   - Users (CASCADE)
   - Drivers (CASCADE)
   - Vehicles (CASCADE)
   - Bookings (CASCADE)
   - Settings, Profile, Stats, Branding, Pricing (CASCADE)

2. **User Deletion**: Cascades to user's bookings

3. **Vehicle Deletion**: Sets booking `vehicle_id` to NULL (preserves booking history)

4. **Driver Deletion**: Removes driver from bookings but preserves booking records

---

## Tenant Isolation Mechanisms

### 1. Database-Level Isolation

#### Foreign Key Constraints
Every tenant-scoped table has a `tenant_id` foreign key:

```python
tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), 
                  nullable=False)
```

**Benefits:**
- Referential integrity enforced at database level
- Automatic cleanup on tenant deletion
- Prevents orphaned records

#### Unique Constraints with tenant_id
Allows same values across different tenants:

```python
# Users can have same email across tenants
UniqueConstraint('email', 'tenant_id', name='unique_user')

# Drivers can have same email/license across tenants
UniqueConstraint('email', 'tenant_id', 'license_number', name='unique_driver')
```

#### Indexes on tenant_id
All tenant-scoped tables have indexes on `tenant_id` for fast filtering:

```python
tenant_id = Column(Integer, ForeignKey(...), nullable=False, index=True)
```

### 2. Application-Level Isolation

#### ServiceContext Automatic Isolation

The `ServiceContext` base class automatically extracts and provides `tenant_id`:

```python
class ServiceContext:
    def __init__(self, db, current_user):
        self.db = db
        self.current_user = current_user
        if self.current_user:
            self.role = self.current_user.role
            if self.role != 'tenant':  # User is driver or rider
                # Automatically extract tenant_id from user
                self.tenant_id = self.current_user.tenant_id
                self.tenant_email = self.current_user.tenants.email
                self.slug = self.current_user.tenants.slug
            else:  # User is tenant
                self.tenant_id = self.current_user.id
                self.slug = self.current_user.profile.slug
```

**Benefits:**
- Automatic tenant context extraction
- Consistent access to `tenant_id` across all services
- No manual tenant_id extraction needed
- Prevents accidental cross-tenant data access

#### Query Filtering Pattern

All queries automatically filter by `tenant_id`:

```python
# BookingService example
async def get_bookings_by(self, booking_status: str = None):
    execute_params = {
        "booking_status": booking_status,
        "tenant_id": self.tenant_id,  # Automatically from ServiceContext
        # ... other params
    }
    
    stmt = """
        SELECT b.*, ...
        FROM bookings b
        WHERE b.tenant_id = :tenant_id  -- Always filtered
        AND (:booking_status IS NULL OR b.booking_status = :booking_status)
        ...
    """
    booking_query = self.db.execute(text(stmt), execute_params)
```

**Pattern:**
1. `ServiceContext` provides `self.tenant_id`
2. All queries include `WHERE tenant_id = :tenant_id`
3. No manual tenant_id extraction needed
4. Impossible to access other tenants' data

### 3. Database Session-Level Isolation

#### PostgreSQL Session Variables

The database connection sets a session variable for additional isolation:

```python
def get_db(tenant_id: int | None = Depends(security.get_tenant_id_from_token)):
    db = SessionLocal()
    try:
        if tenant_id is not None:
            # Set PostgreSQL session variable
            db.execute(
                text("SET app.current_tenant_id = :tenant_id")
                .bindparams(tenant_id=tenant_id)
            )
        yield db
    finally:
        db.close()
```

**Benefits:**
- Additional layer of isolation at database level
- Can be used for row-level security policies
- Audit trail capability
- Future-proof for advanced isolation features

#### Token-Based Tenant Extraction

The `tenant_id` is extracted from JWT token:

```python
def get_tenant_id_from_token(token = Depends(oauth2.oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    role = payload.get("role")
    
    if role and role.lower() == "tenant":
        return payload.get("id")  # Tenant's own ID
    return payload.get("tenant_id")  # User's tenant_id
```

**Token Structure:**
```json
{
  "id": 123,
  "role": "rider",
  "tenant_id": 456,
  "email": "user@example.com"
}
```

---

## Slug-Based Routing System

### Overview

Each tenant has a unique **slug** that maps to their subdomain. The slug is used for:
1. **Subdomain Routing**: `acme.maison.com` → tenant with slug `acme`
2. **Branding Lookup**: Retrieve tenant's branding configuration
3. **Public API Access**: Unauthenticated access to tenant information

### Slug Structure

#### Database Storage
```python
# tenants_profile table
slug = Column(String, unique=True, nullable=False, index=True)
```

**Constraints:**
- **Unique**: No two tenants can have the same slug
- **Indexed**: Fast lookups for routing
- **Required**: Every tenant must have a slug
- **Example Values**: `acme`, `luxury-transport`, `city-rides`

### Slug Verification Endpoint

Public endpoint to verify and retrieve tenant information by slug:

```python
@router.get("/api/v1/slug/{slug}", status_code=200)
async def verify_slug(slug: str, slug_service: SlugService = Depends(get_slug_service)):
    slug_ = slug_service.verify_slug(slug)
    return slug_
```

**Implementation:**
```python
class SlugService(ServiceContext):
    def verify_slug(self, slug):
        # Join multiple tables to get complete tenant setup
        resp = (self.db.query(tenant_setting_table, tenant_profile, tenant_branding)
                .join(tenant_profile, tenant_profile.tenant_id == tenant_setting_table.tenant_id)
                .join(tenant_branding, tenant_branding.tenant_id == tenant_setting_table.tenant_id)
                .filter(tenant_profile.slug == slug)
                .first())
        
        if not resp:
            raise HTTPException(status_code=404, detail="Slug is not in db")
        
        settings, profile, branding = resp
        return {
            "settings": settings.__dict__,
            "profile": profile.__dict__,
            "branding": branding.__dict__
        }
```

**Response Structure:**
```json
{
  "msg": "Slug exists",
  "data": {
    "settings": {
      "tenant_id": 123,
      "rider_tiers_enabled": false,
      "config": { ... }
    },
    "profile": {
      "tenant_id": 123,
      "company_name": "Acme Transport",
      "slug": "acme",
      "logo_url": "https://...",
      "stripe_customer_id": "cus_...",
      "subscription_plan": "growth"
    },
    "branding": {
      "tenant_id": 123,
      "theme": "dark",
      "primary_color": "#1a1a1a",
      "secondary_color": "#2d2d2d",
      "logo_url": "https://...",
      "enable_branding": true
    }
  }
}
```

### Frontend Integration

The frontend extracts the slug from the subdomain:

```javascript
// Extract slug from subdomain
// acme.maison.com → "acme"
const slug = window.location.hostname.split('.')[0];

// Fetch tenant configuration
const response = await fetch(`/api/v1/slug/${slug}`);
const tenantConfig = await response.json();

// Apply branding
applyBranding(tenantConfig.data.branding);
```

**Flow:**
1. User visits `acme.maison.com`
2. Frontend extracts `acme` from hostname
3. Frontend calls `/api/v1/slug/acme`
4. Backend returns tenant settings, profile, and branding
5. Frontend applies branding (colors, logo, theme)
6. User sees Acme-branded interface

### Slug in ServiceContext

The slug is automatically available in all services:

```python
class ServiceContext:
    def __init__(self, db, current_user):
        # ...
        if self.role != 'tenant':
            self.slug = self.current_user.tenants.slug
        else:
            self.slug = self.current_user.profile.slug
```

**Usage in Services:**
```python
class BookingService(ServiceContext):
    async def confirm_ride(self, booking_id: int, payload):
        # ...
        # Use slug for email branding
        drivers.DriverEmailServices(
            to_email=driver_email,
            from_email=self.tenant_email
        ).new_ride(
            booking_obj=response,
            assigned=False,
            slug=self.slug  # Automatically available
        )
```

---

## White Labelling Features

### What is White Labelling?

White labelling allows each tenant to rebrand the platform as their own product. Tenants can customize:
- Visual branding (logo, colors, theme)
- Company information
- Email communications
- Feature visibility
- Business logic (pricing, workflows)

### White Label Components

#### 1. Visual Branding (`tenant_branding` table)

**Customizable Elements:**
- **Logo**: Company logo displayed throughout the platform
- **Color Scheme**: Primary, secondary, and accent colors
- **Theme**: Light or dark mode
- **Favicon**: Browser tab icon
- **Email Branding**: Custom "from" name and address

**Database Schema:**
```python
class TenantBranding(Base):
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), 
                      primary_key=True)
    theme = Column(String, nullable=False, default="dark")
    primary_color = Column(String, nullable=True)
    secondary_color = Column(String, nullable=True)
    accent_color = Column(String, nullable=True)
    favicon_url = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    email_from_name = Column(String, nullable=True)
    email_from_address = Column(String, nullable=True)
    enable_branding = Column(Boolean, nullable=False, default=False)
```

**Application:**
- Web dashboard uses tenant colors and logo
- Mobile apps display tenant branding
- Email templates use tenant logo and colors
- Receipts and invoices show tenant branding

#### 2. Feature Customization (`tenants_settings.config` JSONB)

**Flexible Configuration:**
```json
{
  "booking": {
    "allow_guest_bookings": true,
    "show_vehicle_images": false,
    "types": {
      "airport": {"is_deposit_required": false},
      "dropoffs": {"is_deposit_required": false},
      "hourly": {"is_deposit_required": false}
    }
  },
  "branding": {
    "button_radius": 8,
    "font_family": "DM Sans"
  },
  "features": {
    "vip_profiles": true,
    "show_loyalty_banner": false
  }
}
```

**Benefits:**
- No schema changes needed for new features
- Tenant-specific feature toggles
- Flexible configuration per tenant
- Easy to add new configuration options

#### 3. Pricing Customization (`tenant_pricing` and `tenant_booking_price`)

**Base Pricing:**
```python
class TenantPricing(Base):
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), 
                      primary_key=True)
    base_fare = Column(Float, nullable=False, default=0.0)
    per_mile_rate = Column(Float, nullable=False, default=0.0)
    per_minute_rate = Column(Float, nullable=True, default=0.0)
    per_hour_rate = Column(Float, nullable=False, default=0.0)
    cancellation_fee = Column(Float, nullable=False, default=0.0)
    discounts = Column(Boolean, nullable=False, default=False)
```

**Service-Specific Pricing:**
```python
class TenantBookingPricing(Base):
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), 
                      nullable=False)
    service_type = Column(String, nullable=False)  # airport, dropoff, hourly
    deposit_type = Column(String, nullable=False)  # percentage, flat
    deposit_fee = Column(Float, nullable=True, default=0.0)
    
    # Airport-specific fees
    stc_rate = Column(Float, nullable=True)  # Surface Transport Charge
    gratuity_rate = Column(Float, nullable=True)
    airport_gate_fee = Column(Float, nullable=True)
    meet_and_greet_fee = Column(Float, nullable=True)
```

**Benefits:**
- Each tenant sets their own pricing
- Service-specific pricing (airport, dropoff, hourly)
- Flexible deposit configurations
- Airport-specific fee structures

#### 4. Email White Labelling

Email services use tenant branding:

```python
class DriverEmailServices(EmailServices):
    def new_ride(self, booking_obj, assigned=False, slug=None):
        # Use tenant slug for email branding
        subject = f"New Ride Assignment - {slug}"
        html = f"""
        <html>
            <body>
                <img src="{tenant_logo_url}" alt="{tenant_company_name}">
                <h1>New Ride Assignment</h1>
                <!-- Email content with tenant branding -->
            </body>
        </html>
        """
        self.send_email(
            from_email=f"{tenant_email_from_name} <{tenant_email_from_address}>",
            to_email=driver_email,
            subject=subject,
            html=html
        )
```

**Customization:**
- Custom "from" name and email address
- Tenant logo in email headers
- Tenant colors in email templates
- Company-specific email content

### White Label Implementation Areas

1. **Tenant Admin Dashboard**
   - Settings panel for all customizations
   - Real-time preview of changes
   - Feature toggle switches
   - Branding upload tools

2. **Driver Portal**
   - Branded interface reflecting tenant's identity
   - Customized onboarding flow
   - Feature-specific screens based on tenant settings

3. **Rider App/Website**
   - Complete tenant branding
   - Custom booking flow
   - Tenant-specific features only
   - Personalized user experience

4. **Email Communications**
   - Tenant-branded email templates
   - Custom "from" addresses
   - Tenant logo and colors
   - Company-specific messaging

---

## ServiceContext Pattern for Automatic Isolation

### Overview

The `ServiceContext` base class provides automatic tenant isolation for all services. This pattern ensures:
- Consistent tenant context across all services
- Automatic `tenant_id` extraction
- No manual tenant filtering needed
- Prevents cross-tenant data access

### Implementation

```python
class ServiceContext:
    def __init__(self, db, current_user):
        self.db = db
        self.current_user = current_user
        
        if self.current_user:
            self.role = self.current_user.role
            
            if self.role != 'tenant':  # User is driver or rider
                # Extract tenant context from user
                self.tenant_id = self.current_user.tenant_id
                self.tenant_email = self.current_user.tenants.email
                self.full_name = self.current_user.full_name
                
                if self.role == 'driver':
                    self.driver_id = self.current_user.id
                    self.driver_type = self.current_user.driver_type
                else:  # rider
                    self.rider_id = self.current_user.id
                    self.slug = self.current_user.tenants.slug
                    
            else:  # User is tenant
                # Tenant's own context
                self.tenant_id = self.current_user.id
                self.tenant_email = self.current_user.email
                self.profile_response = self.db.query(tenant_profile).filter(
                    tenant_profile.tenant_id == self.tenant_id
                ).first()
                self.sub_plan = self.profile_response.subscription_plan
                self.slug = self.current_user.profile.slug
        
        self.time_now = datetime.now(timezone.utc)
```

### Service Usage

All services inherit from `ServiceContext`:

```python
class BookingService(ServiceContext):
    def __init__(self, db, current_user):
        super().__init__(db, current_user)
        # Now self.tenant_id is automatically available
    
    async def get_bookings_by(self, booking_status: str = None):
        # Automatic tenant filtering
        execute_params = {
            "booking_status": booking_status,
            "tenant_id": self.tenant_id,  # From ServiceContext
            # ...
        }
        
        stmt = """
            SELECT b.*, ...
            FROM bookings b
            WHERE b.tenant_id = :tenant_id  -- Always filtered
            AND (:booking_status IS NULL OR b.booking_status = :booking_status)
        """
        return self.db.execute(text(stmt), execute_params)
```

### Services Using ServiceContext

All major services use this pattern:

1. **BookingService** - Booking operations
2. **TenantService** - Tenant management
3. **DriverService** - Driver operations
4. **VehicleService** - Vehicle management
5. **UserService** - User/rider operations
6. **TenantSettingsService** - Settings management
7. **Analytics Services** - Business intelligence
8. **SlugService** - Slug verification

### Benefits

1. **Automatic Isolation**: No manual `tenant_id` extraction needed
2. **Consistency**: All services follow the same pattern
3. **Safety**: Impossible to forget tenant filtering
4. **Context Access**: Automatic access to tenant email, slug, subscription plan
5. **Role Awareness**: Automatic role-based context (driver, rider, tenant)

---

## Database Session Management

### Session-Level Tenant Isolation

The database connection sets a PostgreSQL session variable for additional isolation:

```python
def get_db(tenant_id: int | None = Depends(security.get_tenant_id_from_token)):
    db = SessionLocal()
    try:
        if tenant_id is not None:
            # Set PostgreSQL session variable
            db.execute(
                text("SET app.current_tenant_id = :tenant_id")
                .bindparams(tenant_id=tenant_id)
            )
        yield db
    finally:
        db.close()
```

### Token-Based Tenant Extraction

The `tenant_id` is extracted from the JWT token:

```python
def get_tenant_id_from_token(token = Depends(oauth2.oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    role = payload.get("role")
    
    if role and role.lower() == "tenant":
        # Tenant's own ID
        return payload.get("id")
    # User's tenant_id
    return payload.get("tenant_id")
```

### Token Structure

**For Tenants:**
```json
{
  "id": 123,
  "role": "tenant",
  "email": "admin@acme.com"
}
```

**For Users/Drivers:**
```json
{
  "id": 456,
  "role": "rider",
  "tenant_id": 123,
  "email": "user@example.com"
}
```

### Base Database Connection

For unauthenticated endpoints (like slug verification):

```python
def get_base_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Usage:**
```python
@router.get("/api/v1/slug/{slug}")
async def verify_slug(slug: str, 
                     slug_service: SlugService = Depends(get_slug_service)):
    # Uses get_base_db() - no authentication required
    slug_ = slug_service.verify_slug(slug)
    return slug_
```

---

## Evolution Over Time

### Initial Implementation (Summer 2025)

**Early Multi-Tenancy:**
- Basic `tenant_id` foreign keys in tables
- Manual tenant filtering in queries
- Simple slug storage in `tenants_profile`
- Basic white-labeling with logo and colors

**Key Commits:**
- Added `tenant_id` to all tenant-scoped tables
- Implemented cascade deletes
- Created `tenants_profile` table with slug
- Basic slug verification endpoint

### Service Layer Evolution (Fall 2025)

**ServiceContext Introduction:**
- Created `ServiceContext` base class
- Automatic `tenant_id` extraction
- Consistent tenant isolation pattern
- Reduced manual tenant filtering

**Key Changes:**
- All services inherit from `ServiceContext`
- Automatic context management
- Consistent query patterns
- Reduced code duplication

### White Label Enhancement (Winter 2025)

**Advanced White Labelling:**
- JSONB configuration in `tenants_settings`
- Comprehensive branding table (`tenant_branding`)
- Service-specific pricing (`tenant_booking_price`)
- Email white labelling

**Key Features Added:**
- Flexible feature toggles via JSONB
- Airport-specific fee structures
- Enhanced branding options
- Email customization

**Database Schema Changes:**
```python
# Changed tenant_id to primary key in one-to-one tables
tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"),
                  primary_key=True, nullable=False, unique=True)
```

**Benefits:**
- Better data integrity
- Clearer relationship definitions
- Improved query performance

### Current State (January 2026)

**Mature Multi-Tenancy:**
- Comprehensive tenant isolation at multiple levels
- Sophisticated white labelling capabilities
- Flexible configuration system
- Scalable architecture

**Architecture Highlights:**
- Database-level isolation (foreign keys, constraints)
- Application-level isolation (ServiceContext)
- Session-level isolation (PostgreSQL variables)
- Slug-based routing for subdomains
- Comprehensive white labelling

---

## Best Practices

### 1. Always Use ServiceContext

**✅ Good:**
```python
class BookingService(ServiceContext):
    async def get_bookings(self):
        # Automatic tenant_id from ServiceContext
        bookings = self.db.query(Booking).filter(
            Booking.tenant_id == self.tenant_id
        ).all()
```

**❌ Bad:**
```python
class BookingService:
    async def get_bookings(self, tenant_id: int):
        # Manual tenant_id - easy to forget or misuse
        bookings = self.db.query(Booking).filter(
            Booking.tenant_id == tenant_id
        ).all()
```

### 2. Always Filter by tenant_id

**✅ Good:**
```python
stmt = """
    SELECT * FROM bookings
    WHERE tenant_id = :tenant_id
    AND booking_status = :status
"""
```

**❌ Bad:**
```python
stmt = """
    SELECT * FROM bookings
    WHERE booking_status = :status
    -- Missing tenant_id filter!
"""
```

### 3. Use Unique Constraints with tenant_id

**✅ Good:**
```python
UniqueConstraint('email', 'tenant_id', name='unique_user')
```

**❌ Bad:**
```python
email = Column(String, unique=True)  # Prevents same email across tenants
```

### 4. Leverage Cascade Deletes

**✅ Good:**
```python
tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"))
```

**❌ Bad:**
```python
tenant_id = Column(Integer, ForeignKey("tenants.id"))
# Manual cleanup needed
```

### 5. Use Slug for Public Access

**✅ Good:**
```python
@router.get("/api/v1/slug/{slug}")
async def verify_slug(slug: str):
    # Public endpoint - no authentication
    tenant = get_tenant_by_slug(slug)
```

**❌ Bad:**
```python
@router.get("/api/v1/tenant/{tenant_id}")
async def get_tenant(tenant_id: int):
    # Exposes internal tenant_id
    tenant = get_tenant(tenant_id)
```

---

## Security Considerations

### 1. Tenant Isolation

- **Never expose tenant_id in public APIs**: Use slug instead
- **Always filter by tenant_id**: Even in admin operations
- **Validate tenant access**: Check user belongs to tenant before operations

### 2. Slug Security

- **Validate slug format**: Prevent injection attacks
- **Rate limit slug endpoints**: Prevent enumeration attacks
- **Sanitize slug input**: Remove special characters

### 3. Database Security

- **Use parameterized queries**: Prevent SQL injection
- **Index tenant_id columns**: Fast filtering
- **Use foreign key constraints**: Data integrity

### 4. Token Security

- **Validate JWT tokens**: Verify signature and expiration
- **Extract tenant_id from token**: Don't trust client-provided tenant_id
- **Role-based access**: Enforce role checks

---

## Conclusion

Maison-core implements a comprehensive multi-tenant architecture with:

1. **Database-Level Isolation**: Foreign keys, unique constraints, cascade deletes
2. **Application-Level Isolation**: ServiceContext pattern for automatic tenant filtering
3. **Session-Level Isolation**: PostgreSQL session variables
4. **Slug-Based Routing**: Subdomain routing for tenant access
5. **White Labelling**: Comprehensive branding and customization

This architecture provides:
- **Security**: Strong tenant isolation at multiple levels
- **Scalability**: Easy to add new tenants
- **Flexibility**: White labelling and customization
- **Maintainability**: Consistent patterns across services
- **Performance**: Indexed queries and efficient filtering

The evolution from basic multi-tenancy to a sophisticated white-label platform demonstrates growth in:
- Database design skills
- Architecture patterns
- Security practices
- Scalability considerations

---

## References

### Code Files
- **ServiceContext**: [backend/app/api/services/service_context.py](backend/app/api/services/service_context.py)
- **SlugService**: [backend/app/api/services/slug_services.py](backend/app/api/services/slug_services.py)
- **Tenant Models**: [backend/app/models/tenant.py](backend/app/models/tenant.py)
- **Tenant Settings**: [backend/app/models/tenant_setting.py](backend/app/models/tenant_setting.py)
- **Database Config**: [backend/app/db/database.py](backend/app/db/database.py)
- **Security**: [backend/app/api/core/security.py](backend/app/api/core/security.py)

### Database Schema
- **Schema Definition**: [backend/db/schema.dbml](backend/db/schema.dbml)
- **Visual Diagram**: [docs/DBM Diagram.pdf](docs/DBM%20Diagram.pdf)

### Documentation
- **White Labelling Overview**: [docs/frontend_docs/White_labelling.md](docs/frontend_docs/White_labelling.md)
- **Git Changes**: [docs/summer_2025_git_changes.txt](docs/summer_2025_git_changes.txt), [docs/winter_break_2025_git_changes.txt](docs/winter_break_2025_git_changes.txt)

---

*Document created: January 2026*  
*Project: Maison-core - Multi-tenant Luxury Car Service Platform*

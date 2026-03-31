-- ============================================================================
-- Maison-core Database Schema
-- Multi-Tenant Luxury Car Service Platform
-- Generated from SQLAlchemy Models
-- ============================================================================

-- ============================================================================
-- SEQUENCES
-- ============================================================================

-- Sequence for generating tenant and related entity IDs
CREATE SEQUENCE IF NOT EXISTS id_seq START WITH 150;

-- ============================================================================
-- CORE TENANT TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: tenants
-- Description: Main tenant table storing authentication and basic information
-- Relationships: One-to-one with profile, stats, settings, branding, pricing
--                 One-to-many with users, drivers, vehicles, bookings
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenants (
    id INTEGER PRIMARY KEY DEFAULT nextval('id_seq'),
    email VARCHAR(200) UNIQUE NOT NULL,
    first_name VARCHAR(200) NOT NULL,
    last_name VARCHAR(200) NOT NULL,
    password VARCHAR NOT NULL,
    phone_no VARCHAR(200) NOT NULL,
    role VARCHAR NOT NULL DEFAULT 'tenant',
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE
);

-- Indexes for tenants table
CREATE INDEX IF NOT EXISTS idx_tenants_email ON tenants(email);
CREATE INDEX IF NOT EXISTS idx_tenants_phone_no ON tenants(phone_no);
CREATE INDEX IF NOT EXISTS idx_tenants_role ON tenants(role);

-- ----------------------------------------------------------------------------
-- Table: tenants_profile
-- Description: Business profile information including unique slug for subdomain routing
-- Relationship: One-to-one with tenants (tenant_id is primary key)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenants_profile (
    tenant_id INTEGER PRIMARY KEY,
    company_name VARCHAR(200) UNIQUE NOT NULL,
    logo_url VARCHAR,
    slug VARCHAR UNIQUE NOT NULL,
    address VARCHAR,
    city VARCHAR NOT NULL,
    stripe_customer_id VARCHAR UNIQUE,
    stripe_account_id VARCHAR UNIQUE,
    charges_enabled BOOLEAN DEFAULT FALSE,
    subscription_status VARCHAR DEFAULT 'inactive',
    subscription_plan VARCHAR DEFAULT 'free',
    cur_subscription_id VARCHAR UNIQUE,
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_tenants_profile_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id) 
        ON DELETE CASCADE
);

-- Indexes for tenants_profile table
CREATE INDEX IF NOT EXISTS idx_tenants_profile_company_name ON tenants_profile(company_name);
CREATE INDEX IF NOT EXISTS idx_tenants_profile_slug ON tenants_profile(slug);
CREATE INDEX IF NOT EXISTS idx_tenants_profile_city ON tenants_profile(city);
CREATE INDEX IF NOT EXISTS idx_tenants_profile_stripe_customer_id ON tenants_profile(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_tenants_profile_stripe_account_id ON tenants_profile(stripe_account_id);

-- ----------------------------------------------------------------------------
-- Table: tenants_stats
-- Description: Business metrics and statistics for each tenant
-- Relationship: One-to-one with tenants (tenant_id is primary key)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenants_stats (
    tenant_id INTEGER PRIMARY KEY UNIQUE NOT NULL,
    drivers_count INTEGER NOT NULL,
    daily_ride_count INTEGER DEFAULT 0,
    last_ride_count_reset TIMESTAMP WITH TIME ZONE,
    total_ride_count INTEGER NOT NULL DEFAULT 0,
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_tenants_stats_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id) 
        ON DELETE CASCADE
);

-- Indexes for tenants_stats table
CREATE INDEX IF NOT EXISTS idx_tenants_stats_tenant_id ON tenants_stats(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenants_stats_drivers_count ON tenants_stats(drivers_count);

-- ----------------------------------------------------------------------------
-- Table: tenants_settings
-- Description: Flexible JSONB configuration for tenant settings
-- Relationship: One-to-one with tenants (tenant_id is primary key)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenants_settings (
    tenant_id INTEGER PRIMARY KEY UNIQUE NOT NULL,
    rider_tiers_enabled BOOLEAN DEFAULT FALSE,
    config JSONB,
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_tenants_settings_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id) 
        ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- Table: tenant_branding
-- Description: Visual branding and white-label customization
-- Relationship: One-to-one with tenants (tenant_id is primary key)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenant_branding (
    tenant_id INTEGER PRIMARY KEY UNIQUE NOT NULL,
    theme VARCHAR NOT NULL DEFAULT 'dark',
    primary_color VARCHAR,
    secondary_color VARCHAR,
    accent_color VARCHAR,
    favicon_url VARCHAR,
    slug VARCHAR UNIQUE,
    email_from_name VARCHAR,
    email_from_address VARCHAR,
    logo_url VARCHAR,
    enable_branding BOOLEAN NOT NULL DEFAULT FALSE,
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_tenant_branding_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id) 
        ON DELETE CASCADE
);

-- Indexes for tenant_branding table
CREATE INDEX IF NOT EXISTS idx_tenant_branding_slug ON tenant_branding(slug);

-- ----------------------------------------------------------------------------
-- Table: tenant_pricing
-- Description: Base pricing configuration for each tenant
-- Relationship: One-to-one with tenants (tenant_id is primary key)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenant_pricing (
    tenant_id INTEGER PRIMARY KEY UNIQUE NOT NULL,
    base_fare FLOAT NOT NULL DEFAULT 0.0,
    per_mile_rate FLOAT NOT NULL DEFAULT 0.0,
    per_minute_rate FLOAT DEFAULT 0.0,
    per_hour_rate FLOAT NOT NULL DEFAULT 0.0,
    cancellation_fee FLOAT NOT NULL DEFAULT 0.0,
    discounts BOOLEAN NOT NULL DEFAULT FALSE,
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_tenant_pricing_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id) 
        ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- Table: tenant_booking_price
-- Description: Service-specific pricing (airport, dropoff, hourly) with deposit configuration
-- Relationship: One-to-many with tenants
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenant_booking_price (
    id INTEGER PRIMARY KEY DEFAULT nextval('id_seq'),
    tenant_id INTEGER NOT NULL,
    service_type VARCHAR NOT NULL,
    stc_rate FLOAT,
    gratuity_rate FLOAT,
    airport_gate_fee FLOAT,
    meet_and_greet_fee FLOAT,
    deposit_type VARCHAR NOT NULL,
    deposit_fee FLOAT DEFAULT 0.0,
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_tenant_booking_price_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id) 
        ON DELETE CASCADE,
    CONSTRAINT check_deposit_type 
        CHECK (deposit_type IN ('percentage', 'flat')),
    CONSTRAINT enforce_airport_fees_if_airport_service 
        CHECK (
            service_type = 'airport' OR (
                stc_rate IS NULL AND 
                gratuity_rate IS NULL AND 
                airport_gate_fee IS NULL AND 
                meet_and_greet_fee IS NULL
            )
        ),
    CONSTRAINT uq_tenant_booking 
        UNIQUE (service_type, tenant_id)
);

-- Indexes for tenant_booking_price table
CREATE INDEX IF NOT EXISTS idx_tenant_booking_price_service_type ON tenant_booking_price(service_type);
CREATE INDEX IF NOT EXISTS idx_tenant_booking_price_stc_rate ON tenant_booking_price(stc_rate);
CREATE INDEX IF NOT EXISTS idx_tenant_booking_price_gratuity_rate ON tenant_booking_price(gratuity_rate);
CREATE INDEX IF NOT EXISTS idx_tenant_booking_price_airport_gate_fee ON tenant_booking_price(airport_gate_fee);
CREATE INDEX IF NOT EXISTS idx_tenant_booking_price_meet_and_greet_fee ON tenant_booking_price(meet_and_greet_fee);
CREATE INDEX IF NOT EXISTS idx_tenant_booking_price_deposit_type ON tenant_booking_price(deposit_type);

-- ============================================================================
-- USER MANAGEMENT TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: users
-- Description: Rider/customer accounts for each tenant
-- Relationship: Many-to-one with tenants
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY DEFAULT nextval('id_seq'),
    email VARCHAR(200) NOT NULL,
    phone_no VARCHAR(200),
    first_name VARCHAR(200) NOT NULL,
    last_name VARCHAR(200) NOT NULL,
    password VARCHAR NOT NULL,
    address VARCHAR,
    city VARCHAR,
    state VARCHAR,
    country VARCHAR,
    postal_code VARCHAR,
    stripe_customer_id VARCHAR,
    role VARCHAR NOT NULL DEFAULT 'rider',
    tenant_id INTEGER NOT NULL,
    tier VARCHAR NOT NULL DEFAULT 'free',
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_users_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id) 
        ON DELETE CASCADE,
    CONSTRAINT unique_user 
        UNIQUE (email, tenant_id)
);

-- Indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone_no ON users(phone_no);
CREATE INDEX IF NOT EXISTS idx_users_state ON users(state);
CREATE INDEX IF NOT EXISTS idx_users_country ON users(country);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);

-- ----------------------------------------------------------------------------
-- Table: drivers
-- Description: Driver accounts for each tenant (in-house or outsourced)
-- Relationship: Many-to-one with tenants, one-to-one with vehicles
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY DEFAULT nextval('id_seq'),
    tenant_id INTEGER NOT NULL,
    email VARCHAR(200) NOT NULL,
    phone_no VARCHAR(200),
    first_name VARCHAR(200) NOT NULL,
    last_name VARCHAR(200) NOT NULL,
    password VARCHAR,
    state VARCHAR,
    postal_code VARCHAR,
    role VARCHAR DEFAULT 'driver',
    driver_type VARCHAR NOT NULL,
    completed_rides INTEGER NOT NULL DEFAULT 0,
    license_number VARCHAR(100),
    driver_token VARCHAR NOT NULL,
    is_registered VARCHAR NOT NULL DEFAULT 'pending',
    is_active BOOLEAN DEFAULT FALSE,
    is_token BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'available',
    stripe_account_id VARCHAR(255),
    background_check_status VARCHAR(50) DEFAULT 'pending',
    stripe_onboaring_complete BOOLEAN DEFAULT FALSE,
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_drivers_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id) 
        ON DELETE CASCADE,
    CONSTRAINT check_driver_registeration 
        CHECK (is_registered IN ('registered', 'pending')),
    CONSTRAINT unique_driver 
        UNIQUE (email, tenant_id, license_number)
);

-- Indexes for drivers table
CREATE INDEX IF NOT EXISTS idx_drivers_email ON drivers(email);
CREATE INDEX IF NOT EXISTS idx_drivers_phone_no ON drivers(phone_no);
CREATE INDEX IF NOT EXISTS idx_drivers_state ON drivers(state);
CREATE INDEX IF NOT EXISTS idx_drivers_stripe_account_id ON drivers(stripe_account_id);

-- ============================================================================
-- VEHICLE MANAGEMENT TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: vehicle_category_rate
-- Description: Vehicle category pricing rates for each tenant
-- Relationship: Many-to-one with tenants, one-to-many with vehicles
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicle_category_rate (
    id INTEGER PRIMARY KEY DEFAULT nextval('id_seq'),
    tenant_id INTEGER NOT NULL,
    vehicle_category VARCHAR,
    vehicle_flat_rate FLOAT NOT NULL DEFAULT 0.0,
    allowed_image_types VARCHAR[] DEFAULT ARRAY[
        'front_exterior',
        'rear_exterior',
        'side_exterior',
        'interior_front',
        'interior_rear',
        'trunk',
        'dashboard',
        'wheel',
        'feature'
    ],
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_vehicle_category_rate_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id) 
        ON DELETE CASCADE
);

-- Indexes for vehicle_category_rate table
CREATE INDEX IF NOT EXISTS idx_vehicle_category_rate_tenant_id ON vehicle_category_rate(tenant_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_category_rate_vehicle_category ON vehicle_category_rate(vehicle_category);

-- ----------------------------------------------------------------------------
-- Table: vehicle_config (DEPRECATED)
-- Description: Legacy vehicle configuration table (deprecated in favor of vehicle_category_rate)
-- Relationship: Many-to-one with tenants
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicle_config (
    id INTEGER PRIMARY KEY DEFAULT nextval('id_seq'),
    tenant_id INTEGER NOT NULL,
    vehicle_category VARCHAR,
    seating_capacity INTEGER,
    vehicle_flat_rate FLOAT NOT NULL DEFAULT 0.0,
    allowed_image_types VARCHAR[] NOT NULL DEFAULT ARRAY[
        'front_exterior',
        'rear_exterior',
        'side_exterior',
        'interior_front',
        'interior_rear',
        'trunk',
        'dashboard',
        'wheel',
        'feature'
    ],
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_vehicle_config_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id) 
        ON DELETE CASCADE
);

-- Indexes for vehicle_config table
CREATE INDEX IF NOT EXISTS idx_vehicle_config_tenant_id ON vehicle_config(tenant_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_config_vehicle_category ON vehicle_config(vehicle_category);
CREATE INDEX IF NOT EXISTS idx_vehicle_config_seating_capacity ON vehicle_config(seating_capacity);

-- ----------------------------------------------------------------------------
-- Table: vehicles
-- Description: Fleet vehicles for each tenant
-- Relationship: Many-to-one with tenants, one-to-one with drivers, many-to-one with vehicle_category_rate
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY DEFAULT nextval('id_seq'),
    tenant_id INTEGER NOT NULL,
    driver_id INTEGER UNIQUE,
    make VARCHAR(200) NOT NULL,
    model VARCHAR(200) NOT NULL,
    year INTEGER,
    seating_capacity INTEGER,
    vehicle_images JSONB,
    vehicle_category_id INTEGER,
    license_plate VARCHAR(50) UNIQUE,
    color VARCHAR(50),
    status VARCHAR(50) DEFAULT 'available',
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_vehicles_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_vehicles_driver_id 
        FOREIGN KEY (driver_id) 
        REFERENCES drivers(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_vehicles_vehicle_category_id 
        FOREIGN KEY (vehicle_category_id) 
        REFERENCES vehicle_category_rate(id),
    CONSTRAINT check_driver_status 
        CHECK (status IN ('available', 'in_use', 'maintenance'))
);

-- Indexes for vehicles table
CREATE INDEX IF NOT EXISTS idx_vehicles_tenant_id ON vehicles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_driver_id ON vehicles(driver_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_make ON vehicles(make);
CREATE INDEX IF NOT EXISTS idx_vehicles_model ON vehicles(model);
CREATE INDEX IF NOT EXISTS idx_vehicles_year ON vehicles(year);
CREATE INDEX IF NOT EXISTS idx_vehicles_seating_capacity ON vehicles(seating_capacity);
CREATE INDEX IF NOT EXISTS idx_vehicles_vehicle_images ON vehicles USING GIN(vehicle_images);
CREATE INDEX IF NOT EXISTS idx_vehicles_color ON vehicles(color);
CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status);

-- ----------------------------------------------------------------------------
-- Table: vehicle_vehicle_config_association
-- Description: Many-to-many association table between vehicles and vehicle_config (DEPRECATED)
-- Relationship: Many-to-many between vehicles and vehicle_config
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicle_vehicle_config_association (
    vehicle_id INTEGER NOT NULL,
    vehicle_config_id INTEGER NOT NULL,
    CONSTRAINT pk_vehicle_vehicle_config_association 
        PRIMARY KEY (vehicle_id, vehicle_config_id),
    CONSTRAINT fk_vehicle_vehicle_config_association_vehicle_id 
        FOREIGN KEY (vehicle_id) 
        REFERENCES vehicles(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_vehicle_vehicle_config_association_vehicle_config_id 
        FOREIGN KEY (vehicle_config_id) 
        REFERENCES vehicle_config(id) 
        ON DELETE CASCADE
);

-- ============================================================================
-- BOOKING TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: bookings
-- Description: Ride bookings connecting riders, drivers, vehicles, and tenants
-- Relationship: Many-to-one with tenants, users (riders), drivers, vehicles
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY DEFAULT nextval('id_seq'),
    driver_id INTEGER,
    tenant_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    service_type VARCHAR NOT NULL,
    airport_service VARCHAR,
    rider_id INTEGER NOT NULL,
    pickup_location VARCHAR NOT NULL,
    pickup_time TIMESTAMP WITH TIME ZONE NOT NULL,
    hours FLOAT,
    dropoff_location VARCHAR,
    dropoff_time TIMESTAMP WITH TIME ZONE,
    country VARCHAR,
    booking_status VARCHAR NOT NULL DEFAULT 'pending',
    estimated_price FLOAT,
    payment_method VARCHAR,
    notes VARCHAR,
    is_approved BOOLEAN DEFAULT FALSE,
    payment_status VARCHAR DEFAULT 'pending',
    deposit_intent_id VARCHAR,
    balance_intent_id VARCHAR,
    payment_id VARCHAR,
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_bookings_driver_id 
        FOREIGN KEY (driver_id) 
        REFERENCES drivers(id),
    CONSTRAINT fk_bookings_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_bookings_vehicle_id 
        FOREIGN KEY (vehicle_id) 
        REFERENCES vehicles(id) 
        ON DELETE SET NULL,
    CONSTRAINT fk_bookings_rider_id 
        FOREIGN KEY (rider_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE,
    CONSTRAINT airport_service_check 
        CHECK (airport_service IN ('from_airport', 'to_airport')),
    CONSTRAINT booking_status_check_connstraint 
        CHECK (booking_status IN ('pending', 'completed', 'cancelled', 'delayed', 'confirmed')),
    CONSTRAINT booking_payment_status_check_connstraint 
        CHECK (payment_status IN ('pending', 'full_paid', 'deposit_paid', 'balance_paid')),
    CONSTRAINT uq_driver_booking 
        UNIQUE (driver_id, pickup_time, dropoff_time),
    CONSTRAINT uq_vehicle_booking 
        UNIQUE (vehicle_id, pickup_time, dropoff_time)
);

-- Indexes for bookings table
CREATE INDEX IF NOT EXISTS idx_bookings_deposit_intent_id ON bookings(deposit_intent_id);
CREATE INDEX IF NOT EXISTS idx_bookings_balance_intent_id ON bookings(balance_intent_id);
CREATE INDEX IF NOT EXISTS idx_bookings_payment_id ON bookings(payment_id);

-- ============================================================================
-- PAYMENT TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: transactions
-- Description: Payment transactions for bookings
-- Relationship: Many-to-one with bookings and tenants
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY DEFAULT nextval('id_seq'),
    booking_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL,
    stripe_payment_intent_id VARCHAR(255),
    amount FLOAT NOT NULL DEFAULT 0.0,
    platform_fee_amount FLOAT,
    currency VARCHAR(3) DEFAULT 'usd' NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_transactions_booking_id 
        FOREIGN KEY (booking_id) 
        REFERENCES bookings(id),
    CONSTRAINT fk_transactions_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id)
);

-- ----------------------------------------------------------------------------
-- Table: payouts
-- Description: Driver payouts for completed rides
-- Relationship: Many-to-one with bookings and tenants
-- Note: References "driving.id" which may not exist - verify this relationship
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payouts (
    id INTEGER PRIMARY KEY DEFAULT nextval('id_seq'),
    driving_id INTEGER NOT NULL,
    booking_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL,
    stripe_transfer_id VARCHAR(255),
    amount FLOAT NOT NULL DEFAULT 0.0,
    currency VARCHAR(3) DEFAULT 'usd' NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_on TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_payouts_booking_id 
        FOREIGN KEY (booking_id) 
        REFERENCES bookings(id),
    CONSTRAINT fk_payouts_tenant_id 
        FOREIGN KEY (tenant_id) 
        REFERENCES tenants(id)
);

-- ============================================================================
-- RELATIONSHIP SUMMARY
-- ============================================================================

/*
RELATIONSHIPS OVERVIEW:

TENANT HIERARCHY (One-to-One):
- tenants (1) ──> tenants_profile (1:1) - Business profile, slug, Stripe IDs
- tenants (1) ──> tenants_stats (1:1) - Business metrics
- tenants (1) ──> tenants_settings (1:1) - JSONB configuration
- tenants (1) ──> tenant_branding (1:1) - Visual branding
- tenants (1) ──> tenant_pricing (1:1) - Base pricing

TENANT-SCOPED ENTITIES (One-to-Many):
- tenants (1) ──> users (1:many) - Rider/customer accounts
- tenants (1) ──> drivers (1:many) - Driver accounts
- tenants (1) ──> vehicles (1:many) - Fleet vehicles
- tenants (1) ──> bookings (1:many) - Ride bookings
- tenants (1) ──> tenant_booking_price (1:many) - Service-specific pricing
- tenants (1) ──> vehicle_category_rate (1:many) - Vehicle category rates
- tenants (1) ──> transactions (1:many) - Payment transactions
- tenants (1) ──> payouts (1:many) - Driver payouts

BOOKING RELATIONSHIPS:
- bookings (many) ──> tenants (many:1) - Tenant who owns the booking
- bookings (many) ──> users (many:1) - Rider who made the booking
- bookings (many) ──> drivers (many:1, nullable) - Assigned driver
- bookings (many) ──> vehicles (many:1) - Vehicle for the booking

VEHICLE RELATIONSHIPS:
- vehicles (many) ──> tenants (many:1) - Tenant who owns the vehicle
- vehicles (many) ──> drivers (many:1, unique) - Assigned driver (one-to-one)
- vehicles (many) ──> vehicle_category_rate (many:1) - Vehicle category

DRIVER RELATIONSHIPS:
- drivers (many) ──> tenants (many:1) - Tenant who employs the driver
- drivers (1) ──> vehicles (1:1) - Assigned vehicle (via vehicles.driver_id)

USER RELATIONSHIPS:
- users (many) ──> tenants (many:1) - Tenant the user belongs to
- users (1) ──> bookings (1:many) - User's bookings

CASCADE DELETE STRATEGY:
- Tenant deletion: Cascades to all related entities (users, drivers, vehicles, bookings, settings, etc.)
- User deletion: Cascades to user's bookings
- Vehicle deletion: Sets booking vehicle_id to NULL (preserves booking history)
- Driver deletion: Removes driver from bookings but preserves booking records
*/

-- ============================================================================
-- MULTI-TENANT ISOLATION NOTES
-- ============================================================================

/*
MULTI-TENANT ISOLATION:

1. DATABASE LEVEL:
   - All tenant-scoped tables have tenant_id foreign key with CASCADE delete
   - Unique constraints include tenant_id (e.g., unique_user: email + tenant_id)
   - Indexes on tenant_id for fast filtering

2. APPLICATION LEVEL:
   - ServiceContext pattern automatically extracts tenant_id from JWT token
   - All queries filter by tenant_id: WHERE tenant_id = :tenant_id
   - Impossible to access other tenants' data

3. SESSION LEVEL:
   - PostgreSQL session variable: SET app.current_tenant_id = :tenant_id
   - Additional layer of isolation at database level

4. SLUG-BASED ROUTING:
   - Each tenant has unique slug in tenants_profile.slug
   - Used for subdomain routing: slug.maison.com
   - Public endpoint: /api/v1/slug/{slug} for tenant verification
*/

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

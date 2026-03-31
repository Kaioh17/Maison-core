# Maison-core: A Multi-Tenant Luxury Car Service Platform

## Overview

**Maison-core** is a comprehensive backend system for managing luxury car service companies. Think of it like Uber or Lyft, but designed specifically for high-end transportation services where multiple companies (tenants) can operate their own branded platforms on the same infrastructure. It's built using **FastAPI** (Python) and follows a **multi-tenant architecture**, meaning one codebase serves multiple independent companies, each with their own drivers, vehicles, customers, and branding.

## Core Concept: Multi-Tenancy

The fundamental idea behind this project is **multi-tenancy** - a single application instance serves multiple "tenants" (transportation companies). Each tenant operates completely independently:

- **Data Isolation**: Each tenant can only see and manage their own data (drivers, vehicles, bookings, customers)
- **White-Labeling**: Each tenant can customize branding (colors, logos, email templates)
- **Independent Operations**: Each tenant manages their own pricing, vehicle categories, and business rules
- **Subdomain Routing**: Each tenant gets a unique subdomain (e.g., `company1.maison.com`, `company2.maison.com`)

## System Architecture

### High-Level Flow

```
Client Request → FastAPI Router → Service Layer → Database Models → PostgreSQL
                     ↓
              Authentication (JWT)
                     ↓
              Tenant Context Extraction
                     ↓
              Business Logic Processing
                     ↓
              Response (JSON)
```

### Three-Layer Architecture

1. **API Layer (Routers)**: Handles HTTP requests, validates input, manages authentication
2. **Service Layer**: Contains all business logic, orchestrates operations, integrates with third-party services
3. **Data Layer (Models)**: SQLAlchemy ORM models that map to PostgreSQL database tables

## Key Components

### 1. Authentication & Authorization

The system uses **OAuth2 with JWT tokens** for authentication. There are three distinct user roles:

- **Tenants**: Company administrators who manage their business
- **Drivers**: Service providers (can be in-house employees or outsourced contractors)
- **Riders/Users**: End customers who book rides

Each role has different permissions and access levels. When a user logs in, they receive a JWT token that contains their role and tenant information. This token is used for all subsequent API calls.

### 2. ServiceContext Pattern

One of the most elegant parts of this architecture is the **ServiceContext** base class. Instead of passing around database sessions and user information to every function, all service classes inherit from `ServiceContext`, which automatically:

- Extracts the current user's role and tenant ID from the JWT token
- Sets up the database session
- Provides convenient access to user information (email, name, tenant details)
- Handles timezone-aware timestamps
- Ensures all queries are automatically scoped to the correct tenant

This pattern ensures **data isolation** - a driver from Tenant A can never accidentally see data from Tenant B, even if there's a bug in the code.

### 3. Database Schema & Relationships

The database uses **PostgreSQL** with a sophisticated relational design:

**Core Entities:**
- **Tenants**: The transportation companies themselves
- **TenantProfile**: Business information (company name, slug, Stripe IDs)
- **TenantSettings**: Configuration stored as JSONB (flexible key-value pairs)
- **TenantBranding**: Visual customization (colors, logos, themes)
- **TenantPricing**: Base pricing rates (per mile, per minute, base fare)

**Operational Entities:**
- **Users**: Rider/customer accounts (scoped to a tenant)
- **Drivers**: Driver accounts with different types (in-house vs. outsourced)
- **Vehicles**: Fleet management with categories, images, and status
- **Bookings**: Ride requests connecting riders, drivers, vehicles, and tenants

**Financial Entities:**
- **Transactions**: Payment records linked to bookings
- **Payouts**: Driver earnings from completed rides

**Key Design Patterns:**
- **Cascade Deletes**: If a tenant is deleted, all related data (drivers, vehicles, bookings) is automatically deleted
- **Unique Constraints**: Prevents duplicate bookings (same driver can't have two rides at the same time)
- **Foreign Keys**: Ensures referential integrity (can't create a booking for a non-existent vehicle)

### 4. Booking System

The booking system is the heart of the platform. When a rider wants to book a ride:

1. **Route Calculation**: Uses **Mapbox API** to calculate distance, estimated time, and route
2. **Price Calculation**: Complex pricing logic considers:
   - Base fare
   - Distance (per mile rate)
   - Time (per minute or per hour rate)
   - Service type (airport, hourly, dropoff)
   - Vehicle category (luxury sedan, SUV, etc.)
   - Additional fees (airport gate fees, meet-and-greet, gratuity)
3. **Payment Processing**: Integrates with **Stripe** for:
   - Deposit payments (percentage or flat fee)
   - Balance payments
   - Driver payouts via Stripe Express accounts
4. **Status Management**: Bookings go through states: `pending` → `confirmed` → `completed` (or `cancelled`)

### 5. Third-Party Integrations

**Stripe**:
- **Express Accounts**: Each tenant and driver gets a Stripe Express account to receive payments
- **Payment Intents**: Handles deposit and balance payments for bookings
- **Webhooks**: Listens for payment events (payment succeeded, failed, etc.)
- **Multi-Party Payments**: Platform takes a fee, rest goes to tenant/driver

**Mapbox**:
- Calculates routes between pickup and dropoff locations
- Provides distance in miles
- Estimates travel time with traffic considerations
- Used for accurate pricing calculations

**Resend** (Email Service):
- Sends transactional emails (booking confirmations, driver assignments, etc.)
- Modular email services for different user types (drivers, tenants, riders, admin)
- Supports white-labeling (emails can be customized per tenant)

### 6. Analytics & Business Intelligence

The system provides analytics dashboards for each role:

- **Tenant Analytics**: Total revenue, completed rides, pending bookings, driver/vehicle counts
- **Driver Analytics**: Personal booking history, completion rates, earnings
- **Rider Analytics**: Personal ride history, booking status breakdown

These use SQL aggregation queries to calculate metrics in real-time from the database.

## Data Flow Example: Booking a Ride

Let's trace through what happens when a rider books a ride:

1. **Rider submits booking request** → `POST /api/v1/bookings/set`
2. **Router validates request** → Checks authentication, validates input with Pydantic schemas
3. **BookingService processes request**:
   - Extracts tenant context (which company this rider belongs to)
   - Calls Mapbox API to get route information
   - Calculates distance and estimated price
   - Checks vehicle availability
   - Creates booking record in database with status `pending`
   - Creates Stripe payment intent for deposit
4. **Email notification sent** → Rider receives confirmation email
5. **Response returned** → Booking details with estimated price and payment information

Later, when the ride is completed:
- Driver marks booking as `completed`
- System processes final payment (balance)
- Driver receives payout to their Stripe Express account
- Transaction records are created
- Analytics are updated

## Security & Data Isolation

**Multi-tenant data isolation** is critical. The system ensures this through:

1. **JWT Token Context**: Every request includes the user's tenant ID
2. **ServiceContext Filtering**: All database queries automatically filter by `tenant_id`
3. **Database Constraints**: Foreign keys ensure data relationships stay within tenant boundaries
4. **Unique Constraints**: Include tenant_id (e.g., email must be unique per tenant, not globally)

Even if a developer forgets to add a tenant filter, the ServiceContext pattern ensures it's always applied.

## Error Handling & Logging

The system uses centralized error handling:

- **DBErrorHandler**: Catches database errors (integrity violations, constraint errors) and returns appropriate HTTP status codes
- **Comprehensive Logging**: All important events are logged (booking creation, payment processing, errors)
- **Automatic Rollbacks**: If an error occurs, database transactions are automatically rolled back

## Code Organization

```
backend/app/
├── api/
│   ├── routers/          # HTTP endpoints (thin layer, just validation)
│   ├── services/         # Business logic (the heavy lifting)
│   └── core/             # Authentication, security, dependencies
├── models/               # SQLAlchemy database models
├── schemas/              # Pydantic validation schemas
├── db/                   # Database connection setup
└── utils/                # Helper functions (logging, error handling)
```

## Technology Stack

- **Backend Framework**: FastAPI (modern, fast Python web framework)
- **Database**: PostgreSQL (robust relational database)
- **ORM**: SQLAlchemy (Python SQL toolkit)
- **Authentication**: OAuth2 with JWT tokens
- **Validation**: Pydantic (data validation using Python type annotations)
- **Migrations**: Alembic (database version control)
- **Rate Limiting**: SlowAPI with Redis
- **Containerization**: Docker (for easy deployment)

## Why This Architecture?

1. **Scalability**: Multi-tenant architecture allows one codebase to serve many companies
2. **Maintainability**: Service layer separates concerns, making code easier to test and modify
3. **Security**: Automatic tenant isolation prevents data leaks
4. **Flexibility**: JSONB settings allow tenants to customize without code changes
5. **Extensibility**: New features can be added to the service layer without touching routers or models

## Real-World Application

This system could power:
- Luxury car service companies
- Airport shuttle services
- Corporate transportation services
- Event transportation services
- Any business that needs to manage drivers, vehicles, and bookings

Each tenant gets their own branded platform, manages their own operations, but shares the same robust infrastructure.

---

*Written from a computer science student's perspective, explaining the architecture and design decisions that make this system work.*

# Maison-core

Maison-core is a scalable backend for luxury car service companies, built with FastAPI and SQLAlchemy. It supports multi-tenant architecture, booking automation, and dedicated portals for tenants, drivers, and riders.

## Features

### Core Functionality

- **Multi-tenant Architecture:** Support for multiple transportation companies.
- **Role-based Authentication:** Separate authentication for tenants, drivers, and users/riders.
- **Booking Management:** Comprehensive ride booking system with multiple service types.
- **Driver Management:** Onboarding, registration, and management of drivers.
- **Vehicle Management:** Fleet management with vehicle configurations.
- **Airport Integration:** Built-in airport data for airport transfer services.

### Service Types

- **Airport Transfers:** Automated airport pickup/dropoff with city-based airport mapping.
- **Hourly Services:** Time-based transportation services.
- **Drop-off Services:** Point-to-point transportation.

### User Roles

- **Tenants:** Transportation company administrators.
- **Drivers:** Service providers (in-house or outsourced).
- **Users/Riders:** End customers booking rides.


## Architecture

### Backend Structure
    ```cmd
    backend/
    ├── app/
    │   ├── api/
    │   │   ├── routers/          # API route definitions
    │   │   ├── services/         # Business logic layer
    │   │   └── core/             # Core functionality (OAuth2, etc.)
    │   ├── models/               # SQLAlchemy database models
    │   ├── schemas/              # Pydantic data validation schemas
    │   ├── db/                   # Database configuration
    │   ├── utils/                # Utility functions
    │   └── data/                 # Static data (airports, vehicles)
    ├── alembic/                  # Database migrations
    └── docker/                   # Docker configuration

---

## API Endpoints

### Authentication

- `POST /login/tenants` - Tenant login
- `POST /login/driver` - Driver login
- `POST /login/user` - User/rider login

### Tenant Management

- `GET /tenant/` - Get tenant information
- `POST /tenant/add` - Create new tenant
- `GET /tenant/drivers` - Get tenant's drivers
- `POST /tenant/onboard` - Onboard new driver

### Driver Management

- `PATCH /driver/register` - Driver registration/update

### User Management

- `POST /users/add` - Create new user
- `GET /users/` - Get user information

### Booking Management

- `POST /bookings/set` - Create new booking
- `GET /bookings/` - Get user's bookings

### Vehicle Management

- `GET /vehicles/` - Get vehicles
- `POST /vehicles/add` - Add new vehicle

---

## Database Models

- **Tenants:** Transportation companies
- **Drivers:** Service providers with different types (in-house/outsourced)
- **Users:** End customers
- **Vehicles:** Fleet management with configurations
- **Bookings:** Ride requests and management
- **Vehicle Configurations:** Pricing and capacity settings

---

##  Technology Stack

- **Framework:** FastAPI
- **Database:** SQLAlchemy ORM
- **Authentication:** OAuth2 with JWT tokens
- **Validation:** Pydantic schemas
- **Database Migrations:** Alembic
- **Containerization:** Docker
- **Password Hashing:** Secure password utilities

---

## Setup and Installation

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- PostgreSQL (if not using Docker)

> **Note:** Linux or macOS provides the best performance for development and production environments.

<details>
<summary><strong>Windows Development Setup</strong></summary>

#### Option 1: Native Windows Setup

    ```cmd
    # Clone the repository
    git clone <repository-url>
    cd <project-directory>

    # Create virtual environment
    python -m venv venv

    # Activate virtual environment
    venv\Scripts\activate

    # Install dependencies
    pip install -r backend\requirements.txt

    # Set up environment variables (Windows)
    copy backend\docker.env .env
    # Edit .env file with your database credentials using notepad or VS Code

    # Navigate to backend directory
    cd backend

    # Run database migrations
    alembic upgrade head

    # Start the development server
    uvicorn app.main:app --reload

#### Option2: Using Powershell
    ```cmd
    # Clone the repository
    git clone <repository-url>
    Set-Location <project-directory>

    # Create and activate virtual environment
    python -m venv venv
    .\venv\Scripts\Activate.ps1

    # Install dependencies
    pip install -r backend\requirements.txt

    # Copy environment file
    Copy-Item backend\docker.env .env

    # Navigate and run migrations
    Set-Location backend
    alembic upgrade head

    # Start server
    uvicorn app.main:app --reload

Windows-Specific Notes
Virtual Environment: Always use a virtual environment to avoid dependency conflicts.
Path Separators: Use backslashes (\) for Windows paths in commands.
PowerShell Execution Policy: You may need to run Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser to enable script execution.
Environment Variables: Edit .env file manually using any text editor.
Database: Install PostgreSQL locally or use Docker Desktop for Windows.
</details> 


<details>
<summary><strong>Linux/macOS Development </strong></summary>
    ```cmd
    # Clone the repository
    git clone <repository-url>
    cd <project-directory>

    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate

    # Install dependencies
    pip install -r backend/requirements.txt

    # Set up environment variables
    cp backend/docker.env .env
    # Edit .env with your database credentials

    # Run database migrations
    cd backend
    alembic upgrade head

    # Start the development server
    uvicorn app.main:app --reload

#### Doocker setup (cross-platform)
    ```cmd
    # Windows (Command Prompt)
    docker-compose -f docker\docker-compose.yml up -d

    # Windows (PowerShell) / Linux / macOS
    docker-compose -f docker/docker-compose.yml up -d

    # Or use the provided scripts (Linux/macOS only)
    ./start_project.sh
    ./start_tmux.sh
#### Windows with WSL2(Reccommended for windows users)
    ```cmd
    # Install WSL2 and Ubuntu
    wsl --install

    # Inside WSL2, follow the Linux setup instructions
    git clone <repository-url>
    cd <project-directory>
    python3 -m venv venv
    source venv/bin/activate
    pip install -r backend/requirements.txt
    # ... continue with Linux instructions

</details>
# Frontend Developer Setup Guide

## Backend API Base URLs
- Development: `http://localhost:8000`
- Staging: `https://staging-api.yourapp.com` (not done yet)
- Production: `https://api.yourapp.com` (not done yet)

## Authentication
- Token Type: Bearer JWT
- Login endpoints return: `access_token` and `token_type`
- Include in headers: `Authorization: Bearer <token>`

## Framework & Libraries

## Essential integrations 
- `Mapbox` or `Google maps api`
- `React DatePicker` for scheduling
- `Socket.io` Client for real-time updates
- `Axios for` API calls
- `React Hot` Toast for notifications
- `stripe` For payments and Identity confirmation  

Note:

## Authentication System

### Features to implement 
- `Role-based login screens` with different UI and branding 
- `JWT token storage` (currently localstorate) (backend devs will update to a redis session caching and storage)
- `Auto-logout` on token expiry 
- `Protected routes` based on user roles
- `login persistence` accross browser sessions
- `Password reset flow` (needs backend)

### API Integration 
- POST `/api/v1/login/tenants`
- POST `/api/v1/login/driver`
- POST `/api/v1/login/user`

## Tenant Dashboard

### Key Features 
- `Real-time booking dashboard` with status updates
- `Advanced booking filters` (date range, driver, vehicle, status)
- `Driver onboarding workflow` with form validation
- `Vehicle fleet management` with status tracking
- `Company settings`(logo, contact info, pricing, etc)
- `Analytics dashboard` (rides completed, revenue, driver performance)

### API Integration 
- GET `/api/v1/tenant/` - Company info
- GET `/api/v1/tenant/drivers` - Driver list
- POST `/api/v1/tenant/onboard` - Onboard driver
- GET `/api/v1/vehicles/` - Vehicle list
- POST `/api/v1/vehicles/add `- Add vehicle
- More endpoints will be added over time....

## Driver Portal

### Core Features
- `Driver registration form` with document upload
- `Real-time ride requests` with accept/decline
- `GPS tracking integration` for location updates
- `Ride status updates`(en route, arrived, started, completed)
- `Earnings dashboard` with ride history
- `Availability toggle` (online/offline status)
- `Push notifications` for new ride requests

### API Integration

- `PATCH /api/v1/driver/register`- Driver registration
- `GET /api/v1/bookings/available` - Available rides (needs backend)
- `PUT /api/v1/bookings/{id}/accept` - Accept ride (needs backend)
- `PUT /api/v1/bookings/{id}/status` - Update ride status (needs backend)


## Rider Experience


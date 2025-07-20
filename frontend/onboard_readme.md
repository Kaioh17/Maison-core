# Frontend Developer Setup Guide

## Backend API Base URLs
- Development: `http://localhost:8000`
- Staging: `https://staging-api.yourapp.com` (not done yet)
- Production: `https://api.yourapp.com` (not done yet)

## Authentication
- Token Type: Bearer JWT
- Login endpoints return: `access_token` and `token_type`
- Include in headers: `Authorization: Bearer <token>`
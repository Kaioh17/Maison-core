# Development Environment Decision: Repository Split

## Development Issue

While setting up the development environment, we encountered persistent problems with running Flutter inside WSL2 alongside the FastAPI backend.

### Key Problems Identified

- **Android SDK and emulator incompatibility**: Android SDK and emulator don't work smoothly inside WSL2 due to missing device bridge, graphics drivers, and path conflicts
- **Device detection failures**: Even when exposing ports or using Docker for Flutter, the emulator could not reliably detect devices
- **Development delays**: These issues caused development delays of several weeks
- **Environment conflicts**: WSL2 and Windows emulator interactions created persistent compatibility issues

## Decision: Split Into Two Repositories

To resolve these issues and streamline development, we decided to split the project into two separate repositories:

### Backend Repository
- **Technology**: FastAPI, PostgreSQL, SQLAlchemy
- **Environment**: WSL2/Docker for speed and easy containerization
- **Benefits**: 
  - Native Linux environment for Python development
  - Easy containerization and deployment
  - Fast development cycle with hot reloading

### Frontend Repository
- **Technology**: Flutter mobile application
- **Environment**: Native Windows (with Android Studio and emulators)
- **Benefits**:
  - Full Android SDK and emulator support
  - Native development tools and debugging
  - No WSL2 compatibility issues

## Benefits of This Approach

### Environment Optimization
- Each repository is dedicated to its optimal environment (backend in Linux, frontend in Windows/macOS)
- Avoids WSL to Windows emulator conflicts
- Eliminates cross-platform compatibility issues

### Development Workflow
- Cleaner collaboration: backend and frontend can evolve independently
- Separate version control and deployment pipelines
- Independent dependency management

### Communication
- Both systems communicate over HTTP
- Backend API accessible at `localhost:8000` for web/iOS development
- Backend API accessible at `10.0.2.2:8000` for Android emulator development

## Implementation Details

### Backend Configuration
- Runs in WSL2 with Docker Compose
- Exposes API on port 8000
- Database and Redis services containerized
- Hot reloading enabled for development

### Frontend Configuration
- Runs natively on Windows
- Android Studio for development and debugging
- Emulator connects to backend via `10.0.2.2:8000`
- Web/iOS development uses `localhost:8000`

### API Communication
- RESTful API endpoints for all communication
- JWT-based authentication
- CORS configured for cross-origin requests
- Consistent error handling and response formats

## Migration Steps

1. **Backend Repository**:
   - Keep existing FastAPI codebase
   - Maintain Docker configuration
   - Update documentation for standalone backend

2. **Frontend Repository**:
   - Move Flutter code to separate repository
   - Update API base URLs for different environments
   - Configure build scripts for independent deployment

3. **Documentation Updates**:
   - Update setup instructions for both repositories
   - Document API endpoints and communication protocols
   - Create development workflow guides

## Development Workflow

### Backend Development
```bash
# Start backend services
cd backend
docker-compose up -d

# Run development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Development
```bash
# Start Flutter development
cd frontend
flutter run

# For Android emulator
flutter run -d android
```

## Troubleshooting

### Common Issues
- **API Connection**: Ensure backend is running and accessible
- **CORS Errors**: Check backend CORS configuration
- **Authentication**: Verify JWT token handling
- **Network**: Confirm correct API base URLs for each platform

### Platform-Specific Notes
- **Android Emulator**: Use `10.0.2.2:8000` for API calls
- **iOS Simulator**: Use `localhost:8000` for API calls
- **Web Development**: Use `localhost:8000` for API calls

## Future Considerations

- **CI/CD**: Separate deployment pipelines for each repository
- **Versioning**: Independent version management
- **Testing**: Separate test suites for backend and frontend
- **Documentation**: Maintain separate documentation for each repository

## Conclusion

This approach unblocks development and ensures both parts of the system remain easy to maintain. The separation allows each team to work in their optimal environment while maintaining clear communication protocols between the systems.

The decision prioritizes developer productivity and eliminates the technical debt caused by trying to force incompatible tools to work together in a single environment.

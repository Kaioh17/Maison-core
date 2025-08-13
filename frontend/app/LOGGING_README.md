# Frontend Logging System

This project now includes a comprehensive frontend logging system that captures all console output and saves it locally for debugging and monitoring purposes.

## Features

- **Automatic Logging**: All `console.log`, `console.error`, `console.warn`, `console.info`, and `console.debug` calls are automatically captured
- **Persistent Storage**: Logs are saved to browser localStorage and persist across page reloads
- **Easy Download**: Logs can be downloaded as a text file with the naming convention `maison_frontend_log_YYYY-MM-DD.txt`
- **Log Management**: Built-in functions to view, clear, and manage logs

## How It Works

1. **Automatic Initialization**: The logging system is automatically initialized when the app starts (imported in `main.tsx`)
2. **Console Override**: All console methods are overridden to capture output while maintaining original functionality
3. **Local Storage**: Logs are stored in browser localStorage under the key `maison_frontend_logs`
4. **Buffer Management**: The system maintains a buffer of up to 200 log entries to prevent memory issues

## Usage

### From Browser Console

Once the app is loaded, you can access logging functions from the browser console:

```javascript
// Download all logs as a file
window.maisonLogs.downloadLogs()

// Get the current number of log entries
window.maisonLogs.getLogCount()

// Get all logs as an array
window.maisonLogs.getAllLogs()

// Clear all logs
window.maisonLogs.clearLogs()
```

### From the Dashboard

1. Navigate to the **Settings** tab in your Tenant Dashboard
2. In the **System Tools** section, you'll see a "Download Logs" button
3. Click the button to download your current logs
4. The button also shows the current number of log entries

### Programmatic Usage

You can also import and use the logging functions in your React components:

```typescript
import { downloadLogs, clearLogs, getLogCount, getAllLogs } from '@utils/logging'

// Use the functions as needed
const logCount = getLogCount()
downloadLogs()
```

## Log Format

Each log entry follows this format:
```
2024-01-15T10:30:45.123Z [LOG] Your log message here
2024-01-15T10:30:46.456Z [ERROR] Error message with details
2024-01-15T10:30:47.789Z [WARN] Warning message
```

## Benefits

- **Debugging**: Easily capture and review console output for troubleshooting
- **Monitoring**: Track user interactions and system behavior in production
- **Development**: Maintain logs across development sessions
- **Support**: Provide detailed logs to support teams when issues arise

## Technical Details

- **File**: `frontend/app/src/utils/logging.ts`
- **Initialization**: `frontend/app/src/main.tsx` (imported first)
- **Storage**: Browser localStorage
- **Buffer Size**: 200 entries maximum
- **File Naming**: `maison_frontend_log_YYYY-MM-DD.txt`

## Troubleshooting

If logging doesn't work:

1. Check browser console for any errors
2. Ensure localStorage is enabled in your browser
3. Verify the logging utility is imported in `main.tsx`
4. Check that `window.maisonLogs` is available in browser console

## Example Log Output

```
2024-01-15T10:30:45.123Z [LOG] Frontend logging initialized - all console output will be saved locally and can be downloaded as maison_frontend_log
2024-01-15T10:30:45.124Z [LOG] Use window.maisonLogs.downloadLogs() to download logs, or access other functions from window.maisonLogs
2024-01-15T10:30:45.125Z [LOG] Auth State: {"accessToken":"...","role":"tenant"}
2024-01-15T10:30:45.126Z [LOG] Starting to load dashboard data...
2024-01-15T10:30:45.127Z [ERROR] ❌ No tenant data in response: {"status":"error","message":"Not found"}
``` 
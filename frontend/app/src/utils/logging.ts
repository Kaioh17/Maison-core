// Frontend logging utility that redirects all console logging to maison_frontend_log
// This version works directly in the browser and stores logs locally

// Store original console methods
const originalConsoleLog = console.log
const originalConsoleError = console.error
const originalConsoleWarn = console.warn
const originalConsoleInfo = console.info
const originalConsoleDebug = console.debug

// Log buffer to store logs
let logBuffer: string[] = []
const MAX_BUFFER_SIZE = 200

// Helper function to format log messages
const formatLogMessage = (level: string, message: string, ...args: any[]): string => {
  const timestamp = new Date().toISOString()
  const formattedArgs = args.map(arg => 
    typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
  ).join(' ')
  
  return `${timestamp} [${level}] ${message} ${formattedArgs}`
}

// Function to save logs to localStorage and prepare for download
const saveLogs = (logEntry: string) => {
  try {
    // Add to buffer
    logBuffer.push(logEntry)
    
    // Save to localStorage
    localStorage.setItem('maison_frontend_logs', JSON.stringify(logBuffer))
    
    // If buffer is getting large, keep only recent logs
    if (logBuffer.length > MAX_BUFFER_SIZE) {
      logBuffer = logBuffer.slice(-MAX_BUFFER_SIZE)
      localStorage.setItem('maison_frontend_logs', JSON.stringify(logBuffer))
    }
  } catch (error) {
    // Fallback to original console if localStorage fails
    originalConsoleError('Failed to save logs to localStorage:', error)
  }
}

// Override console.log
console.log = (...args: any[]) => {
  const message = args.join(' ')
  const logEntry = formatLogMessage('LOG', message)
  saveLogs(logEntry)
  originalConsoleLog(...args)
}

// Override console.error
console.error = (...args: any[]) => {
  const message = args.join(' ')
  const logEntry = formatLogMessage('ERROR', message)
  saveLogs(logEntry)
  originalConsoleError(...args)
}

// Override console.warn
console.warn = (...args: any[]) => {
  const message = args.join(' ')
  const logEntry = formatLogMessage('WARN', message)
  saveLogs(logEntry)
  originalConsoleWarn(...args)
}

// Override console.info
console.info = (...args: any[]) => {
  const message = args.join(' ')
  const logEntry = formatLogMessage('INFO', message)
  saveLogs(logEntry)
  originalConsoleInfo(...args)
}

// Override console.debug
console.debug = (...args: any[]) => {
  const message = args.join(' ')
  const logEntry = formatLogMessage('DEBUG', message)
  saveLogs(logEntry)
  originalConsoleDebug(...args)
}

// Export the original console methods in case they're needed
export const originalConsole = {
  log: originalConsoleLog,
  error: originalConsoleError,
  warn: originalConsoleWarn,
  info: originalConsoleInfo,
  debug: originalConsoleDebug
}

// Function to download logs as a file
export const downloadLogs = () => {
  try {
    const logs = localStorage.getItem('maison_frontend_logs')
    if (!logs) {
      originalConsole.warn('No logs found to download')
      return
    }
    
    const logArray = JSON.parse(logs)
    const logContent = logArray.join('\n')
    
    // Create download link
    const blob = new Blob([logContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `maison_frontend_log_${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    originalConsole.log('Logs downloaded successfully')
  } catch (error) {
    originalConsole.error('Failed to download logs:', error)
  }
}

// Function to clear logs
export const clearLogs = () => {
  try {
    logBuffer = []
    localStorage.removeItem('maison_frontend_logs')
    originalConsole.log('Logs cleared successfully')
  } catch (error) {
    originalConsole.error('Failed to clear logs:', error)
  }
}

// Function to get current log count
export const getLogCount = (): number => {
  return logBuffer.length
}

// Function to get all logs as array
export const getAllLogs = (): string[] => {
  return [...logBuffer]
}

// Load existing logs from localStorage on initialization
try {
  const existingLogs = localStorage.getItem('maison_frontend_logs')
  if (existingLogs) {
    logBuffer = JSON.parse(existingLogs)
    originalConsole.log(`Loaded ${logBuffer.length} existing logs from localStorage`)
  }
} catch (error) {
  originalConsole.warn('Failed to load existing logs from localStorage:', error)
}

// Make logging functions available globally for easy access from browser console
declare global {
  interface Window {
    maisonLogs: {
      downloadLogs: () => void
      clearLogs: () => void
      getLogCount: () => number
      getAllLogs: () => string[]
    }
  }
}

window.maisonLogs = {
  downloadLogs,
  clearLogs,
  getLogCount,
  getAllLogs
}

// Initialize logging
console.log('Frontend logging initialized - all console output will be saved locally and can be downloaded as maison_frontend_log')
console.log('Use window.maisonLogs.downloadLogs() to download logs, or access other functions from window.maisonLogs') 
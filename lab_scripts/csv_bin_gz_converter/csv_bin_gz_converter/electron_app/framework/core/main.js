/**
 * Electron App Framework - Core Main Process
 * 
 * This file provides the base main process configuration with extension points
 * for application-specific functionality.
 * 
 * To customize: Create a main.js in your app root that extends this:
 * 
 * const { createApp } = require('./electron-app-framework/core/main');
 * const customHandlers = require('./app/handlers');
 * 
 * createApp({
 *   windowOptions: { width: 1200, height: 800 },
 *   handlers: customHandlers
 * });
 */

const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow = null;
let appConfig = {
  windowOptions: {
    width: 1000,
    height: 700,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false
    }
  },
  indexPath: null,  // Will be set based on app location
  preloadPath: null // Will be set based on app location
};

/**
 * Get the root directory of the actual application (not the framework)
 */
function getAppRoot() {
  // If launched from app directory, app.getAppPath() returns the app dir
  // If we're in a framework subdirectory, we need to go up
  const appPath = app.getAppPath();
  
  // Check if we're in the framework directory
  if (appPath.includes('electron-app-framework')) {
    return path.resolve(appPath, '..', '..');
  }
  
  return appPath;
}

/**
 * Get framework directory
 */
function getFrameworkRoot() {
  return path.resolve(__dirname, '..');
}

/**
 * Create the main application window
 */
function createWindow(config = {}) {
  const windowConfig = {
    ...appConfig.windowOptions,
    ...config,
    webPreferences: {
      ...appConfig.windowOptions.webPreferences,
      preload: appConfig.preloadPath || path.join(getFrameworkRoot(), 'core', 'preload.js')
    }
  };

  mainWindow = new BrowserWindow(windowConfig);

  const indexFile = appConfig.indexPath || 
                    path.join(getAppRoot(), 'app', 'renderer', 'index.html');
  
  mainWindow.loadFile(indexFile);
  
  return mainWindow;
}

/**
 * Register standard IPC handlers
 */
function registerStandardHandlers() {
  // File dialog
  ipcMain.handle('dialog:openFile', async (event, options = {}) => {
    const result = await dialog.showOpenDialog({
      properties: ['openFile'],
      ...options
    });
    return result.canceled ? '' : result.filePaths[0] || '';
  });

  // Folder dialog
  ipcMain.handle('dialog:openFolder', async (event, options = {}) => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory'],
      ...options
    });
    return result.canceled ? '' : result.filePaths[0] || '';
  });

  // Executable dialog
  ipcMain.handle('dialog:openExecutable', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openFile'],
      filters: process.platform === 'win32' 
        ? [{ name: 'Executable', extensions: ['exe'] }]
        : []
    });
    return result.canceled ? '' : result.filePaths[0] || '';
  });

  // File read helper
  ipcMain.handle('fs:readFile', async (event, filePath) => {
    try {
      return fs.readFileSync(filePath, 'utf8');
    } catch (err) {
      throw new Error(`Failed to read file: ${err.message}`);
    }
  });

  // File write helper
  ipcMain.handle('fs:writeFile', async (event, filePath, data) => {
    try {
      fs.writeFileSync(filePath, data, 'utf8');
      return true;
    } catch (err) {
      throw new Error(`Failed to write file: ${err.message}`);
    }
  });
}

/**
 * Initialize the application
 * 
 * @param {Object} config - Application configuration
 * @param {Object} config.windowOptions - BrowserWindow options
 * @param {String} config.indexPath - Path to index.html
 * @param {String} config.preloadPath - Path to preload script
 * @param {Function} config.handlers - Function to register custom IPC handlers
 * @param {Function} config.onReady - Callback when app is ready
 */
function createApp(config = {}) {
  // Merge configuration
  if (config.windowOptions) {
    appConfig.windowOptions = {
      ...appConfig.windowOptions,
      ...config.windowOptions
    };
  }
  
  if (config.indexPath) appConfig.indexPath = config.indexPath;
  if (config.preloadPath) appConfig.preloadPath = config.preloadPath;

  // Register standard handlers
  registerStandardHandlers();
  
  // Register custom handlers if provided
  if (config.handlers && typeof config.handlers === 'function') {
    config.handlers(ipcMain, { getAppRoot, getFrameworkRoot, mainWindow: () => mainWindow });
  }

  // Handle app ready
  app.whenReady().then(() => {
    createWindow();
    
    if (config.onReady) {
      config.onReady({ mainWindow, appRoot: getAppRoot(), frameworkRoot: getFrameworkRoot() });
    }

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  });

  // Quit when all windows are closed
  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });
}

module.exports = {
  createApp,
  createWindow,
  getAppRoot,
  getFrameworkRoot,
  getMainWindow: () => mainWindow
};

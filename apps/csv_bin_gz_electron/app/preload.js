/**
 * CSV to BIN.GZ Converter - Custom Preload Script
 * 
 * Extends the framework's standard API with CSV-specific methods.
 */

const { standardAPI } = require('../../electron-app-framework/core/preload');
const { contextBridge, ipcRenderer } = require('electron');

// Extend the standard API with CSV-specific methods
const csvAppAPI = {
  ...standardAPI,
  
  // CSV-specific methods
  getCsvHeader: (filePath) => ipcRenderer.invoke('csv:getHeader', filePath),
  getTemplates: () => ipcRenderer.invoke('templates:list'),
  getConfig: () => ipcRenderer.invoke('config:get'),
  runConversion: (payload) => ipcRenderer.invoke('convert:run', payload),
  
  // Event listener for conversion logs
  onLog: (callback) => ipcRenderer.on('convert:log', (_, message) => callback(message))
};

// Expose API to renderer with the same name as before for compatibility
contextBridge.exposeInMainWorld('csvApp', csvAppAPI);

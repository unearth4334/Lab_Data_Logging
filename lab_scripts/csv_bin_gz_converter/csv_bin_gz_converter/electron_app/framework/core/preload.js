/**
 * Electron App Framework - Preload Script
 * 
 * Provides a secure bridge between renderer and main processes.
 * This can be extended by application-specific preload scripts.
 */

const { contextBridge, ipcRenderer } = require('electron');

/**
 * Standard API exposed to renderer process
 */
const standardAPI = {
  // Dialog operations
  selectFile: (options) => ipcRenderer.invoke('dialog:openFile', options),
  selectFolder: (options) => ipcRenderer.invoke('dialog:openFolder', options),
  selectExecutable: () => ipcRenderer.invoke('dialog:openExecutable'),
  
  // File system operations (sandboxed through main process)
  readFile: (filePath) => ipcRenderer.invoke('fs:readFile', filePath),
  writeFile: (filePath, data) => ipcRenderer.invoke('fs:writeFile', filePath, data),
  
  // Generic IPC invoke
  invoke: (channel, ...args) => ipcRenderer.invoke(channel, ...args),
  
  // Event listeners
  on: (channel, callback) => {
    ipcRenderer.on(channel, (event, ...args) => callback(...args));
  },
  
  once: (channel, callback) => {
    ipcRenderer.once(channel, (event, ...args) => callback(...args));
  },
  
  removeListener: (channel, callback) => {
    ipcRenderer.removeListener(channel, callback);
  }
};

/**
 * Expose API to renderer
 * Applications can extend this by creating their own preload script
 * that imports this file and adds custom methods
 */
contextBridge.exposeInMainWorld('electronApp', standardAPI);

module.exports = { standardAPI };

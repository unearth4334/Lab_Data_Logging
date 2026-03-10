/**
 * CSV to BIN.GZ Converter - Custom Preload Script (bundled, self-contained)
 */

const { standardAPI } = require('../framework/core/preload');
const { contextBridge, ipcRenderer } = require('electron');

const csvAppAPI = {
  ...standardAPI,
  getCsvHeader: (filePath) => ipcRenderer.invoke('csv:getHeader', filePath),
  getTemplates: () => ipcRenderer.invoke('templates:list'),
  getConfig: () => ipcRenderer.invoke('config:get'),
  runConversion: (payload) => ipcRenderer.invoke('convert:run', payload),
  onLog: (callback) => ipcRenderer.on('convert:log', (_, message) => callback(message))
};

contextBridge.exposeInMainWorld('csvApp', csvAppAPI);

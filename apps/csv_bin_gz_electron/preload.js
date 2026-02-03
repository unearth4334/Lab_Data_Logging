const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('csvApp', {
  selectFile: () => ipcRenderer.invoke('dialog:openFile'),
  selectFolder: () => ipcRenderer.invoke('dialog:openFolder'),
  selectExecutable: () => ipcRenderer.invoke('dialog:openExecutable'),
  getCsvHeader: (filePath) => ipcRenderer.invoke('csv:getHeader', filePath),
  getTemplates: () => ipcRenderer.invoke('templates:list'),
  getConfig: () => ipcRenderer.invoke('config:get'),
  runConversion: (payload) => ipcRenderer.invoke('convert:run', payload),
  onLog: (callback) => ipcRenderer.on('convert:log', (_, message) => callback(message))
});

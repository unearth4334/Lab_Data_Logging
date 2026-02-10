/**
 * CSV to BIN.GZ Converter - Main Entry Point
 * 
 * This application uses the electron-app-framework for its core infrastructure.
 */

const { createApp } = require('../../electron-app-framework/core/main');
const csvHandlers = require('./app/handlers/csv-handlers');
const path = require('path');

createApp({
  windowOptions: {
    width: 1100,
    height: 720,
    title: 'CSV to BIN.GZ Converter'
  },
  indexPath: path.join(__dirname, 'app', 'renderer', 'index.html'),
  preloadPath: path.join(__dirname, 'app', 'preload.js'),
  handlers: csvHandlers,
  onReady: ({ appRoot }) => {
    console.log('CSV to BIN.GZ Converter ready');
    console.log('App root:', appRoot);
  }
});

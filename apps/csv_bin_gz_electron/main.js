const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { parse } = require('csv-parse/sync');
const yaml = require('js-yaml');

let mainWindow;

const repoRoot = path.resolve(app.getAppPath(), '..', '..');
const scriptsDir = path.join(repoRoot, 'scripts');
const currentScript = path.join(scriptsDir, 'csv_to_bin_gz(current).py');
const powerRailsScript = path.join(scriptsDir, 'csv_to_bin_gz(power_rails).py');
const reorderScript = path.join(scriptsDir, 'reorder_csv_columns.py');
const templatesDir = path.join(app.getAppPath(), 'column_templates');
const configPath = path.join(app.getAppPath(), 'config.yml');

function getPythonCommand(pythonPath) {
  if (pythonPath && pythonPath.trim()) {
    return pythonPath.trim();
  }
  return process.platform === 'win32' ? 'python' : 'python3';
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 720,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

function readCsvHeader(filePath) {
  const fd = fs.openSync(filePath, 'r');
  const buffer = Buffer.alloc(1024 * 1024);
  const bytesRead = fs.readSync(fd, buffer, 0, buffer.length, 0);
  fs.closeSync(fd);

  const snippet = buffer.slice(0, bytesRead).toString('utf8');
  const newlineIndex = snippet.search(/\r?\n/);
  const headerLine = newlineIndex >= 0 ? snippet.slice(0, newlineIndex) : snippet;
  const records = parse(headerLine, { relax_quotes: true });
  if (!records.length) {
    throw new Error('Unable to parse CSV header.');
  }
  return records[0];
}

function runPython(scriptPath, args, event, label) {
  return new Promise((resolve, reject) => {
    const pythonCmd = getPythonCommand(args.pythonPath);
    const spawnArgs = [scriptPath, ...args.params];
    const child = spawn(pythonCmd, spawnArgs, { cwd: repoRoot });

    const prefix = label ? `[${label}] ` : '';

    child.stdout.on('data', (data) => {
      event.sender.send('convert:log', `${prefix}${data.toString()}`);
    });

    child.stderr.on('data', (data) => {
      event.sender.send('convert:log', `${prefix}${data.toString()}`);
    });

    child.on('error', (err) => reject(err));
    child.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${label || 'Process'} failed with exit code ${code}`));
      }
    });
  });
}

ipcMain.handle('dialog:openFile', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [{ name: 'CSV Files', extensions: ['csv'] }]
  });
  if (result.canceled || !result.filePaths.length) {
    return '';
  }
  return result.filePaths[0];
});

ipcMain.handle('dialog:openFolder', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory']
  });
  if (result.canceled || !result.filePaths.length) {
    return '';
  }
  return result.filePaths[0];
});

ipcMain.handle('dialog:openExecutable', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile']
  });
  if (result.canceled || !result.filePaths.length) {
    return '';
  }
  return result.filePaths[0];
});

ipcMain.handle('csv:getHeader', async (_, filePath) => {
  return readCsvHeader(filePath);
});

ipcMain.handle('templates:list', async () => {
  if (!fs.existsSync(templatesDir)) {
    return [];
  }

  const files = fs.readdirSync(templatesDir).filter((file) => file.endsWith('.yml') || file.endsWith('.yaml'));
  return files.map((file) => {
    const fullPath = path.join(templatesDir, file);
    const raw = fs.readFileSync(fullPath, 'utf8');
    const data = yaml.load(raw) || {};
    return {
      id: file,
      name: data.name || path.parse(file).name,
      columns: Array.isArray(data.columns) ? data.columns : []
    };
  });
});

ipcMain.handle('config:get', async () => {
  if (!fs.existsSync(configPath)) {
    return {};
  }
  const raw = fs.readFileSync(configPath, 'utf8');
  const data = yaml.load(raw) || {};
  return {
    defaultPythonExecutable: data.default_python_executable || ''
  };
});

ipcMain.handle('convert:run', async (event, payload) => {
  const {
    currentCsv,
    powerRailsCsv,
    outputFolder,
    reorderConfig,
    sampleRate,
    pythonPath
  } = payload;

  if (!currentCsv || !powerRailsCsv || !outputFolder) {
    throw new Error('Missing required inputs.');
  }

  if (!fs.existsSync(currentCsv) || !fs.existsSync(powerRailsCsv)) {
    throw new Error('Input CSV file not found.');
  }

  if (!fs.existsSync(outputFolder)) {
    throw new Error('Output folder not found.');
  }

  let powerRailsInput = powerRailsCsv;

  if (reorderConfig && reorderConfig.enabled) {
    const base = path.parse(powerRailsCsv).name;
    const reorderedPath = path.join(outputFolder, `${base}.reordered.csv`);
    const orderArg = reorderConfig.order.join(',');
    const renameArg = reorderConfig.renamePairs.join(',');

    const params = [powerRailsCsv, '--order', orderArg, '--yes', '--output', reorderedPath];
    if (renameArg) {
      params.push('--rename', renameArg);
    }

    await runPython(reorderScript, { params, pythonPath }, event, 'reorder');
    powerRailsInput = reorderedPath;
  }

  const currentOutPrefix = path.join(outputFolder, 'current_capture');
  const currentParams = [currentCsv, '--out', currentOutPrefix];
  if (sampleRate && Number.isFinite(sampleRate)) {
    currentParams.push('--sps', String(sampleRate));
  }

  await runPython(currentScript, { params: currentParams, pythonPath }, event, 'current');

  const powerOutPrefix = path.join(outputFolder, 'power_rails');
  const powerParams = [powerRailsInput, '--out', powerOutPrefix];
  await runPython(powerRailsScript, { params: powerParams, pythonPath }, event, 'power');

  return { success: true };
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

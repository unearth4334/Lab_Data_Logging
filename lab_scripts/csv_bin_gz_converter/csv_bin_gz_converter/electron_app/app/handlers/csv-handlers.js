/**
 * CSV to BIN.GZ Converter - Custom IPC Handlers (bundled, self-contained)
 *
 * Path resolution:
 *   - column_templates/ and config.yml are relative to appRoot (= electron_app/)
 *   - scripts/ is looked up as  appRoot/scripts  first, then  appRoot/../scripts
 *     so it works both when bundled and when deployed under shared/csv_bin_gz_electron/
 */

const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');
const yaml = require('js-yaml');
const { executePythonScript } = require('../framework/core/ipc-helpers');

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

async function runPython(scriptPath, args, pythonPath, event) {
  return executePythonScript(
    scriptPath,
    args,
    { pythonPath },
    event,
    'convert:log'
  );
}

module.exports = function registerCsvHandlers(ipcMain, context) {
  const { getAppRoot } = context;
  const appRoot = getAppRoot();

  // Scripts: check appRoot/scripts first, then appRoot/../scripts (shared/ layout)
  const localScripts = path.join(appRoot, 'scripts');
  const parentScripts = path.join(appRoot, '..', 'scripts');
  const scriptsDir = fs.existsSync(localScripts) ? localScripts : parentScripts;

  const currentScript = path.join(scriptsDir, 'csv_to_bin_gz(current).py');
  const powerRailsScript = path.join(scriptsDir, 'csv_to_bin_gz(power_rails).py');
  const reorderScript = path.join(scriptsDir, 'reorder_csv_columns.py');

  // Templates: appRoot/column_templates (works for bundled and deployed)
  const templatesDir = path.join(appRoot, 'column_templates');

  // Config: appRoot/config.yml
  const configPath = path.join(appRoot, 'config.yml');

  ipcMain.handle('csv:getHeader', async (_, filePath) => {
    return readCsvHeader(filePath);
  });

  ipcMain.handle('templates:list', async () => {
    if (!fs.existsSync(templatesDir)) {
      return [];
    }
    const files = fs.readdirSync(templatesDir).filter((f) =>
      f.endsWith('.yml') || f.endsWith('.yaml')
    );
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
      // No config file - try to find valid Python executable
      let pythonPath = '';
      const launcherWorkdir = process.env.CSV_BIN_GZ_WORKDIR || '';
      if (launcherWorkdir) {
        const veenvPython = path.join(launcherWorkdir, '.venv', 'Scripts', 'python.exe');
        if (fs.existsSync(veenvPython)) {
          pythonPath = veenvPython;
        }
      }
      // Fallback to system python if venv not found
      if (!pythonPath || !fs.existsSync(pythonPath)) {
        pythonPath = process.platform === 'win32' ? 'python' : 'python3';
      }
      return { defaultPythonExecutable: pythonPath };
    }
    const raw = fs.readFileSync(configPath, 'utf8');
    const data = yaml.load(raw) || {};
    
    // Try to find a valid Python executable in this order:
    // 1. Config file explicit setting (if path exists)
    // 2. <launcher_cwd>/.venv/Scripts/python.exe (if CSV_BIN_GZ_WORKDIR is set)
    // 3. System python/python3
    let pythonPath = data.default_python_executable || '';
    
    if (!pythonPath || !fs.existsSync(pythonPath)) {
      const launcherWorkdir = process.env.CSV_BIN_GZ_WORKDIR || '';
      if (launcherWorkdir) {
        const veenvPython = path.join(launcherWorkdir, '.venv', 'Scripts', 'python.exe');
        if (fs.existsSync(veenvPython)) {
          pythonPath = veenvPython;
        }
      }
    }
    
    // If still no valid path, default to system python (spawn will search PATH)
    if (!pythonPath || !fs.existsSync(pythonPath)) {
      pythonPath = process.platform === 'win32' ? 'python' : 'python3';
    }

    return {
      defaultPythonExecutable: pythonPath
    };
  });

  ipcMain.handle('convert:run', async (event, payload) => {
    const { currentCsv, powerRailsCsv, outputFolder, reorderConfig, sampleRate, pythonPath } = payload;

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
      if (renameArg) params.push('--rename', renameArg);
      await runPython(reorderScript, params, pythonPath, event);
      powerRailsInput = reorderedPath;
    }

    const currentOutPrefix = path.join(outputFolder, 'current_capture');
    const currentParams = [currentCsv, '--out', currentOutPrefix];
    if (sampleRate && Number.isFinite(sampleRate)) {
      currentParams.push('--sps', String(sampleRate));
    }
    await runPython(currentScript, currentParams, pythonPath, event);

    const powerOutPrefix = path.join(outputFolder, 'power_rails');
    await runPython(powerRailsScript, [powerRailsInput, '--out', powerOutPrefix], pythonPath, event);

    return { success: true };
  });
};

/**
 * CSV to BIN.GZ Converter - Custom IPC Handlers
 * 
 * This file contains application-specific IPC handlers for the CSV converter.
 */

const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');
const yaml = require('js-yaml');
const { executePythonScript } = require('../../electron-app-framework/core/ipc-helpers');

/**
 * Read CSV file header
 */
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

/**
 * Execute Python script with labeled output
 */
async function runPython(scriptPath, args, pythonPath, event, label) {
  return executePythonScript(
    scriptPath,
    args,
    { pythonPath },
    event,
    'convert:log'
  );
}

/**
 * Register all CSV-specific IPC handlers
 */
module.exports = function registerCsvHandlers(ipcMain, context) {
  const { getAppRoot } = context;
  const appRoot = getAppRoot();
  
  // Paths
  const scriptsDir = path.join(appRoot, 'scripts');
  const currentScript = path.join(scriptsDir, 'csv_to_bin_gz(current).py');
  const powerRailsScript = path.join(scriptsDir, 'csv_to_bin_gz(power_rails).py');
  const reorderScript = path.join(scriptsDir, 'reorder_csv_columns.py');
  const templatesDir = path.join(appRoot, 'apps', 'csv_bin_gz_electron', 'column_templates');
  const configPath = path.join(appRoot, 'apps', 'csv_bin_gz_electron', 'config.yml');

  // Get CSV header
  ipcMain.handle('csv:getHeader', async (_, filePath) => {
    return readCsvHeader(filePath);
  });

  // List column templates
  ipcMain.handle('templates:list', async () => {
    if (!fs.existsSync(templatesDir)) {
      return [];
    }

    const files = fs.readdirSync(templatesDir).filter((file) => 
      file.endsWith('.yml') || file.endsWith('.yaml')
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

  // Get application config
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

  // Run conversion pipeline
  ipcMain.handle('convert:run', async (event, payload) => {
    const {
      currentCsv,
      powerRailsCsv,
      outputFolder,
      reorderConfig,
      sampleRate,
      pythonPath
    } = payload;

    // Validate inputs
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

    // Step 1: Reorder columns if needed
    if (reorderConfig && reorderConfig.enabled) {
      const base = path.parse(powerRailsCsv).name;
      const reorderedPath = path.join(outputFolder, `${base}.reordered.csv`);
      const orderArg = reorderConfig.order.join(',');
      const renameArg = reorderConfig.renamePairs.join(',');

      const params = [
        powerRailsCsv,
        '--order', orderArg,
        '--yes',
        '--output', reorderedPath
      ];
      
      if (renameArg) {
        params.push('--rename', renameArg);
      }

      await runPython(reorderScript, params, pythonPath, event, 'reorder');
      powerRailsInput = reorderedPath;
    }

    // Step 2: Convert current CSV
    const currentOutPrefix = path.join(outputFolder, 'current_capture');
    const currentParams = [currentCsv, '--out', currentOutPrefix];
    
    if (sampleRate && Number.isFinite(sampleRate)) {
      currentParams.push('--sps', String(sampleRate));
    }

    await runPython(currentScript, currentParams, pythonPath, event, 'current');

    // Step 3: Convert power rails CSV
    const powerOutPrefix = path.join(outputFolder, 'power_rails');
    const powerParams = [powerRailsInput, '--out', powerOutPrefix];
    
    await runPython(powerRailsScript, powerParams, pythonPath, event, 'power');

    return { success: true };
  });
};

/**
 * Helper utilities for IPC handlers
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * Execute a Python script and stream output to renderer
 * 
 * @param {String} scriptPath - Path to Python script
 * @param {Array} args - Script arguments
 * @param {Object} options - Execution options
 * @param {String} options.pythonPath - Custom Python executable path
 * @param {String} options.cwd - Working directory
 * @param {Object} event - IPC event for sending progress
 * @param {String} logChannel - Channel name for log messages
 */
function executePythonScript(scriptPath, args = [], options = {}, event, logChannel = 'python:log') {
  return new Promise((resolve, reject) => {
    let pythonCmd = options.pythonPath || 
                     (process.platform === 'win32' ? 'python' : 'python3');
    
    // If pythonPath was specified but doesn't exist, fallback to system python
    if (options.pythonPath && !fs.existsSync(options.pythonPath)) {
      pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    }
    
    const spawnOptions = {
      cwd: options.cwd || path.dirname(scriptPath)
    };

    const child = spawn(pythonCmd, [scriptPath, ...args], spawnOptions);

    child.stdout.on('data', (data) => {
      if (event) {
        event.sender.send(logChannel, data.toString());
      }
    });

    child.stderr.on('data', (data) => {
      if (event) {
        event.sender.send(logChannel, data.toString());
      }
    });

    child.on('error', (err) => {
      reject(new Error(`Failed to execute Python script: ${err.message}`));
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Python script exited with code ${code}`));
      }
    });
  });
}

/**
 * Read JSON file
 */
function readJSON(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(content);
  } catch (err) {
    throw new Error(`Failed to read JSON file: ${err.message}`);
  }
}

/**
 * Write JSON file
 */
function writeJSON(filePath, data, pretty = true) {
  try {
    const content = pretty ? JSON.stringify(data, null, 2) : JSON.stringify(data);
    fs.writeFileSync(filePath, content, 'utf8');
    return true;
  } catch (err) {
    throw new Error(`Failed to write JSON file: ${err.message}`);
  }
}

/**
 * Read YAML file (requires js-yaml dependency)
 */
function readYAML(filePath) {
  try {
    const yaml = require('js-yaml');
    const content = fs.readFileSync(filePath, 'utf8');
    return yaml.load(content);
  } catch (err) {
    if (err.code === 'MODULE_NOT_FOUND') {
      throw new Error('js-yaml not installed. Run: npm install js-yaml');
    }
    throw new Error(`Failed to read YAML file: ${err.message}`);
  }
}

/**
 * Write YAML file (requires js-yaml dependency)
 */
function writeYAML(filePath, data) {
  try {
    const yaml = require('js-yaml');
    const content = yaml.dump(data);
    fs.writeFileSync(filePath, content, 'utf8');
    return true;
  } catch (err) {
    if (err.code === 'MODULE_NOT_FOUND') {
      throw new Error('js-yaml not installed. Run: npm install js-yaml');
    }
    throw new Error(`Failed to write YAML file: ${err.message}`);
  }
}

/**
 * Ensure directory exists
 */
function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

/**
 * List files in directory with optional filter
 */
function listFiles(dirPath, filter = null) {
  try {
    let files = fs.readdirSync(dirPath);
    
    if (filter) {
      if (typeof filter === 'string') {
        // Extension filter
        files = files.filter(f => f.endsWith(filter));
      } else if (filter instanceof RegExp) {
        // Regex filter
        files = files.filter(f => filter.test(f));
      } else if (typeof filter === 'function') {
        // Custom filter function
        files = files.filter(filter);
      }
    }
    
    return files.map(f => path.join(dirPath, f));
  } catch (err) {
    throw new Error(`Failed to list files: ${err.message}`);
  }
}

module.exports = {
  executePythonScript,
  readJSON,
  writeJSON,
  readYAML,
  writeYAML,
  ensureDir,
  listFiles
};

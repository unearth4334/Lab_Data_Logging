const elements = {
  currentCsv: document.getElementById('currentCsv'),
  powerCsv: document.getElementById('powerCsv'),
  outputFolder: document.getElementById('outputFolder'),
  browseCurrent: document.getElementById('browseCurrent'),
  browsePower: document.getElementById('browsePower'),
  browseOutput: document.getElementById('browseOutput'),
  configureReorder: document.getElementById('configureReorder'),
  clearReorder: document.getElementById('clearReorder'),
  reorderSummary: document.getElementById('reorderSummary'),
  execute: document.getElementById('execute'),
  status: document.getElementById('status'),
  logOutput: document.getElementById('logOutput'),
  modalOverlay: document.getElementById('modalOverlay'),
  columnList: document.getElementById('columnList'),
  closeModal: document.getElementById('closeModal'),
  applyModal: document.getElementById('applyModal'),
  resetModal: document.getElementById('resetModal'),
  templateSelect: document.getElementById('templateSelect'),
  templateColumns: document.getElementById('templateColumns'),
  sampleRate: document.getElementById('sampleRate'),
  pythonPath: document.getElementById('pythonPath'),
  browsePython: document.getElementById('browsePython')
};

const state = {
  currentCsv: '',
  powerCsv: '',
  outputFolder: '',
  pythonPath: '',
  sampleRate: 500000,
  header: [],
  reorder: {
    enabled: false,
    columns: []
  }
};

const templateState = {
  templates: [],
  selectedId: ''
};

async function loadConfigDefaults() {
  try {
    const config = await window.csvApp.getConfig();
    if (config.defaultPythonExecutable) {
      state.pythonPath = config.defaultPythonExecutable;
      elements.pythonPath.value = config.defaultPythonExecutable;
    }
  } catch (err) {
    setStatus('Failed to load config defaults.', true);
  }
}

function setStatus(text, isError = false) {
  elements.status.textContent = text;
  elements.status.style.color = isError ? '#b42318' : '#1f6b3c';
}

function appendLog(message) {
  elements.logOutput.textContent += message;
  elements.logOutput.scrollTop = elements.logOutput.scrollHeight;
}

function clearLog() {
  elements.logOutput.textContent = '';
}

function updateSummary() {
  if (!state.reorder.enabled) {
    elements.reorderSummary.textContent = 'No reorder applied.';
  } else {
    elements.reorderSummary.textContent = `Reorder enabled (${state.reorder.columns.length} columns).`;
  }
}

function openModal() {
  elements.modalOverlay.classList.remove('hidden');
}

function closeModal() {
  elements.modalOverlay.classList.add('hidden');
}

function renderTemplateSelect() {
  elements.templateSelect.innerHTML = '';
  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = 'Select a template';
  elements.templateSelect.appendChild(placeholder);

  templateState.templates.forEach((template) => {
    const option = document.createElement('option');
    option.value = template.id;
    option.textContent = template.name;
    elements.templateSelect.appendChild(option);
  });

  if (templateState.selectedId) {
    elements.templateSelect.value = templateState.selectedId;
  }
}

function renderTemplateColumns() {
  elements.templateColumns.innerHTML = '';
  const template = templateState.templates.find((item) => item.id === templateState.selectedId);
  if (!template) {
    const empty = document.createElement('span');
    empty.textContent = 'No template selected.';
    elements.templateColumns.appendChild(empty);
    return;
  }

  template.columns.forEach((name) => {
    const chip = document.createElement('span');
    chip.textContent = name;
    elements.templateColumns.appendChild(chip);
  });
}

function renderColumnList() {
  elements.columnList.innerHTML = '';
  state.reorder.columns.forEach((col, idx) => {
    const row = document.createElement('div');
    row.className = 'column-row';

    const index = document.createElement('div');
    index.textContent = col.index;

    const input = document.createElement('input');
    input.type = 'text';
    input.value = col.newName;
    input.addEventListener('input', (event) => {
      col.newName = event.target.value;
    });

    const actions = document.createElement('div');
    actions.className = 'column-actions';

    const up = document.createElement('button');
    up.textContent = '↑';
    up.className = 'ghost';
    up.disabled = idx === 0;
    up.addEventListener('click', () => moveColumn(idx, -1));

    const down = document.createElement('button');
    down.textContent = '↓';
    down.className = 'ghost';
    down.disabled = idx === state.reorder.columns.length - 1;
    down.addEventListener('click', () => moveColumn(idx, 1));

    actions.appendChild(up);
    actions.appendChild(down);

    row.appendChild(index);
    row.appendChild(input);
    row.appendChild(actions);

    elements.columnList.appendChild(row);
  });
}

function moveColumn(index, direction) {
  const target = index + direction;
  if (target < 0 || target >= state.reorder.columns.length) {
    return;
  }
  const updated = [...state.reorder.columns];
  const [item] = updated.splice(index, 1);
  updated.splice(target, 0, item);
  state.reorder.columns = updated;
  renderColumnList();
}

async function ensureHeaderLoaded() {
  if (!state.powerCsv) {
    throw new Error('Select a power rails CSV first.');
  }
  const header = await window.csvApp.getCsvHeader(state.powerCsv);
  state.header = header;
  state.reorder.columns = header.map((name, idx) => ({
    index: idx,
    name,
    newName: name
  }));
}

function resetReorderState() {
  if (state.header.length) {
    state.reorder.columns = state.header.map((name, idx) => ({
      index: idx,
      name,
      newName: name
    }));
  }
}

function buildReorderConfig() {
  const order = state.reorder.columns.map((col) => col.index);
  const renamePairs = state.reorder.columns
    .filter((col) => col.newName && col.newName !== col.name)
    .map((col) => `${col.index}:${col.newName}`);

  return { order, renamePairs };
}

async function configureReorder() {
  try {
    await ensureHeaderLoaded();
    resetReorderState();
    renderColumnList();
    templateState.templates = await window.csvApp.getTemplates();
    templateState.selectedId = templateState.templates.length ? templateState.templates[0].id : '';
    renderTemplateSelect();
    renderTemplateColumns();
    openModal();
  } catch (err) {
    setStatus(err.message, true);
  }
}

async function executeConversion() {
  setStatus('Running...', false);
  clearLog();

  const payload = {
    currentCsv: state.currentCsv,
    powerRailsCsv: state.powerCsv,
    outputFolder: state.outputFolder,
    pythonPath: state.pythonPath,
    sampleRate: Number(elements.sampleRate.value)
  };

  if (state.reorder.enabled) {
    const reorderConfig = buildReorderConfig();
    payload.reorderConfig = {
      enabled: true,
      order: reorderConfig.order,
      renamePairs: reorderConfig.renamePairs
    };
  } else {
    payload.reorderConfig = { enabled: false };
  }

  try {
    await window.csvApp.runConversion(payload);
    setStatus('Completed successfully.');
  } catch (err) {
    setStatus(err.message || 'Execution failed.', true);
  }
}

window.csvApp.onLog((message) => appendLog(message));

elements.browseCurrent.addEventListener('click', async () => {
  const file = await window.csvApp.selectFile();
  if (!file) return;
  state.currentCsv = file;
  elements.currentCsv.value = file;
});

elements.browsePower.addEventListener('click', async () => {
  const file = await window.csvApp.selectFile();
  if (!file) return;
  state.powerCsv = file;
  elements.powerCsv.value = file;
  state.header = [];
  state.reorder.enabled = false;
  updateSummary();
});

elements.browseOutput.addEventListener('click', async () => {
  const folder = await window.csvApp.selectFolder();
  if (!folder) return;
  state.outputFolder = folder;
  elements.outputFolder.value = folder;
});

elements.browsePython.addEventListener('click', async () => {
  const exe = await window.csvApp.selectExecutable();
  if (!exe) return;
  state.pythonPath = exe;
  elements.pythonPath.value = exe;
});

elements.pythonPath.addEventListener('input', (event) => {
  state.pythonPath = event.target.value;
});

elements.configureReorder.addEventListener('click', configureReorder);

elements.clearReorder.addEventListener('click', () => {
  state.reorder.enabled = false;
  updateSummary();
});

elements.closeModal.addEventListener('click', closeModal);

elements.templateSelect.addEventListener('change', (event) => {
  templateState.selectedId = event.target.value;
  renderTemplateColumns();
});

elements.resetModal.addEventListener('click', () => {
  resetReorderState();
  renderColumnList();
});

elements.applyModal.addEventListener('click', () => {
  state.reorder.enabled = true;
  updateSummary();
  closeModal();
});

elements.execute.addEventListener('click', executeConversion);

updateSummary();
loadConfigDefaults();

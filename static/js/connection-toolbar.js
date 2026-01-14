/**
 * Connection Toolbar
 * 
 * A compact toolbar interface for managing VISA device connections.
 * Adapted from VastAI Connection Toolbar pattern.
 */

class ConnectionToolbar {
    constructor() {
        this.dropdownOpen = false;
        this.currentAddress = '';
        this.availableDevices = [];
    }

    /**
     * Initialize the toolbar
     */
    async init() {
        console.log('🔧 Initializing Connection Toolbar...');
        
        // Render toolbar HTML
        this.renderToolbar();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load available devices
        await this.loadDevices();
        
        console.log('✅ Connection Toolbar initialized');
    }
    
    /**
     * Render the toolbar HTML
     */
    renderToolbar() {
        // Find insertion point (before the measurement tab)
        const container = document.querySelector('.container');
        const tabContainer = document.querySelector('.tab-container');
        
        if (!container || !tabContainer) {
            console.error('❌ Could not find container or tab container');
            return;
        }
        
        // Create toolbar HTML
        const toolbarHTML = `
            <div class="connection-toolbar" id="connection-toolbar">
                <div class="toolbar-dropdown-container">
                    <div class="toolbar-connection-row">
                        <button class="toolbar-btn toolbar-connection-btn" id="toolbar-connection-btn">
                            <span class="toolbar-connection-text" id="toolbar-connection-text">📡 No device selected</span>
                            <span class="toolbar-status-icon" id="toolbar-status-icon"></span>
                        </button>
                        <button class="toolbar-btn toolbar-refresh-btn" id="toolbar-refresh-btn" title="Refresh devices">
                            <span>🔄</span>
                        </button>
                    </div>
                    
                    <div class="toolbar-dropdown" id="toolbar-dropdown">
                        <div class="toolbar-dropdown-content" id="toolbar-dropdown-content">
                            <div class="toolbar-dropdown-header">
                                <h3>📡 Connection Settings</h3>
                                <button type="button" class="toolbar-close-btn" id="toolbar-close-btn">&times;</button>
                            </div>
                            
                            <div class="toolbar-form-group">
                                <label for="toolbar-visa-address">VISA Address:</label>
                                <select id="toolbar-visa-address" name="visa_address">
                                    <option value="">Loading available devices...</option>
                                </select>
                                <small id="toolbar-visa-status">Scanning for VISA devices...</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="toolbar-backdrop" id="toolbar-backdrop"></div>
        `;
        
        // Insert toolbar before tab container
        tabContainer.insertAdjacentHTML('beforebegin', toolbarHTML);
        
        console.log('✅ Toolbar HTML rendered');
    }
    
    /**
     * Update toolbar display based on current state
     */
    updateToolbarDisplay() {
        const connectionText = document.getElementById('toolbar-connection-text');
        const statusIcon = document.getElementById('toolbar-status-icon');
        
        if (!connectionText || !statusIcon) return;
        
        // Update connection text
        if (this.currentAddress) {
            connectionText.textContent = `📡 ${this.currentAddress}`;
            connectionText.classList.add('has-connection');
            
            // Show success status
            statusIcon.className = 'toolbar-status-icon status-connected';
        } else {
            connectionText.textContent = '📡 No device selected';
            connectionText.classList.remove('has-connection');
            statusIcon.className = 'toolbar-status-icon';
        }
    }
    
    /**
     * Load available VISA devices
     */
    async loadDevices() {
        const selectElement = document.getElementById('toolbar-visa-address');
        const statusElement = document.getElementById('toolbar-visa-status');
        const refreshBtn = document.getElementById('toolbar-refresh-btn');
        
        if (!selectElement || !statusElement || !refreshBtn) return;
        
        try {
            console.log('🔄 Loading VISA devices...');
            statusElement.textContent = 'Scanning for VISA devices...';
            statusElement.className = 'toolbar-connection-status';
            refreshBtn.disabled = true;
            
            const response = await fetch('/list_visa_resources');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Clear existing options
            selectElement.innerHTML = '';
            
            if (data.error) {
                console.error('❌ VISA resource error:', data.error);
                selectElement.innerHTML = '<option value="">Error: ' + data.error + '</option>';
                statusElement.textContent = 'Error scanning for devices. PyVISA may not be configured correctly.';
                statusElement.className = 'toolbar-connection-status error';
            } else if (data.resources.length === 0) {
                console.warn('⚠️ No VISA resources found');
                selectElement.innerHTML = '<option value="">No VISA devices found</option>';
                statusElement.textContent = 'No devices found. Check connections and try refreshing.';
                statusElement.className = 'toolbar-connection-status error';
            } else {
                console.log(`✅ Found ${data.resources.length} VISA devices`);
                
                // Add a default "Select a device" option
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = '-- Select a VISA device --';
                selectElement.appendChild(defaultOption);
                
                // Add each resource as an option
                data.resources.forEach(resource => {
                    const option = document.createElement('option');
                    option.value = resource;
                    option.textContent = resource;
                    selectElement.appendChild(option);
                });
                
                this.availableDevices = data.resources;
                
                // Try to select the default from config or previously selected
                try {
                    const defaults = await fetch('/defaults').then(r => {
                        if (!r.ok) throw new Error('Failed to fetch defaults');
                        return r.json();
                    });
                    const storedAddress = localStorage.getItem('visa_address');
                    
                    if (storedAddress && data.resources.includes(storedAddress)) {
                        selectElement.value = storedAddress;
                        this.selectDevice(storedAddress);
                    } else if (defaults.visa_address && data.resources.includes(defaults.visa_address)) {
                        selectElement.value = defaults.visa_address;
                        this.selectDevice(defaults.visa_address);
                    }
                } catch (defaultsError) {
                    console.warn('⚠️ Could not load defaults:', defaultsError.message);
                    // Continue without defaults - not critical
                }
                
                statusElement.textContent = `Found ${data.resources.length} device(s). Select one from the dropdown.`;
                statusElement.className = 'toolbar-connection-status success';
            }
        } catch (error) {
            console.error('❌ Failed to load VISA devices:', error);
            selectElement.innerHTML = '<option value="">Error loading devices</option>';
            statusElement.textContent = 'Error: Could not connect to server';
            statusElement.className = 'toolbar-connection-status error';
        } finally {
            refreshBtn.disabled = false;
        }
    }
    
    /**
     * Select a device
     */
    selectDevice(address) {
        console.log(`📌 Selecting device: ${address}`);
        
        this.currentAddress = address;
        
        // Store in localStorage for persistence
        if (address) {
            localStorage.setItem('visa_address', address);
        } else {
            localStorage.removeItem('visa_address');
        }
        
        // Update the main form's visa_address field
        const mainFormSelect = document.getElementById('visa_address');
        if (mainFormSelect) {
            mainFormSelect.value = address;
        }
        
        // Update display
        this.updateToolbarDisplay();
        
        // Close dropdown
        this.closeDropdown();
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Connection button - toggle dropdown
        const connectionBtn = document.getElementById('toolbar-connection-btn');
        if (connectionBtn) {
            connectionBtn.addEventListener('click', (e) => this.toggleDropdown(e));
        }
        
        // Close button
        const closeBtn = document.getElementById('toolbar-close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeDropdown());
        }
        
        // Refresh button
        const refreshBtn = document.getElementById('toolbar-refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadDevices());
        }
        
        // Device selection
        const selectElement = document.getElementById('toolbar-visa-address');
        if (selectElement) {
            selectElement.addEventListener('change', (e) => {
                this.selectDevice(e.target.value);
            });
        }
        
        // Click outside to close dropdown
        document.addEventListener('click', (e) => this.handleClickOutside(e));
        
        // Backdrop click to close
        const backdrop = document.getElementById('toolbar-backdrop');
        if (backdrop) {
            backdrop.addEventListener('click', () => this.closeDropdown());
        }
    }
    
    /**
     * Toggle dropdown visibility
     */
    toggleDropdown(e) {
        if (e) e.stopPropagation();
        
        const dropdown = document.getElementById('toolbar-dropdown');
        const backdrop = document.getElementById('toolbar-backdrop');
        
        if (!dropdown) return;
        
        this.dropdownOpen = !this.dropdownOpen;
        
        if (this.dropdownOpen) {
            dropdown.classList.add('open');
            if (backdrop) backdrop.classList.add('open');
        } else {
            dropdown.classList.remove('open');
            if (backdrop) backdrop.classList.remove('open');
        }
    }
    
    /**
     * Close dropdown
     */
    closeDropdown() {
        const dropdown = document.getElementById('toolbar-dropdown');
        const backdrop = document.getElementById('toolbar-backdrop');
        
        this.dropdownOpen = false;
        
        if (dropdown) dropdown.classList.remove('open');
        if (backdrop) backdrop.classList.remove('open');
    }
    
    /**
     * Handle clicks outside dropdown to close it
     */
    handleClickOutside(e) {
        const toolbar = document.getElementById('connection-toolbar');
        if (toolbar && !toolbar.contains(e.target) && this.dropdownOpen) {
            this.closeDropdown();
        }
    }
    
    /**
     * Get current VISA address
     */
    getCurrentAddress() {
        return this.currentAddress || '';
    }
}

// Create and export singleton instance
const toolbarInstance = new ConnectionToolbar();

// Expose in a namespaced global object to avoid pollution
window.LabDataLogging = window.LabDataLogging || {};
window.LabDataLogging.ConnectionToolbar = toolbarInstance;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => toolbarInstance.init());
} else {
    // DOM already loaded, initialize now
    toolbarInstance.init();
}

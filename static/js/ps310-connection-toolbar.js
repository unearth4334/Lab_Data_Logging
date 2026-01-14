/**
 * Connection Toolbar for Stanford PS310 Power Supply GUI
 * 
 * A compact toolbar interface for managing VISA device connections.
 * Adapted from the general connection toolbar for PS310-specific features.
 */

class PS310ConnectionToolbar {
    constructor() {
        this.dropdownOpen = false;
        this.currentAddress = '';
        this.availableDevices = [];
        this.connected = false;
    }

    /**
     * Initialize the toolbar
     */
    async init() {
        console.log('🔧 Initializing PS310 Connection Toolbar...');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load available devices
        await this.loadDevices();
        
        console.log('✅ PS310 Connection Toolbar initialized');
    }
    
    /**
     * Update toolbar display based on current state
     */
    updateToolbarDisplay() {
        const connectionText = document.getElementById('toolbar-connection-text');
        const statusIcon = document.getElementById('toolbar-status-icon');
        
        if (!connectionText || !statusIcon) return;
        
        // Update connection text
        if (this.connected && this.currentAddress) {
            connectionText.textContent = `📡 ${this.currentAddress}`;
            connectionText.classList.add('has-connection');
            
            // Show success status
            statusIcon.className = 'toolbar-status-icon status-connected';
        } else if (this.currentAddress) {
            connectionText.textContent = `📡 ${this.currentAddress}`;
            connectionText.classList.add('has-connection');
            statusIcon.className = 'toolbar-status-icon';
        } else {
            connectionText.textContent = '📡 No device connected';
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
            } else if (!data.resources || data.resources.length === 0) {
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
                
                // Try to select the previously selected device
                const storedAddress = localStorage.getItem('ps310_visa_address');
                
                if (storedAddress && data.resources.includes(storedAddress)) {
                    selectElement.value = storedAddress;
                    this.selectDevice(storedAddress, false); // Don't auto-connect on load
                }
                
                statusElement.textContent = `Found ${data.resources.length} device(s). Select one from the dropdown.`;
                statusElement.className = 'toolbar-connection-status success';
                
                // Enable connect button if device is selected
                this.updateButtonStates();
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
    selectDevice(address, autoConnect = false) {
        console.log(`📌 Selecting device: ${address}`);
        
        this.currentAddress = address;
        
        // Store in localStorage for persistence
        if (address) {
            localStorage.setItem('ps310_visa_address', address);
        } else {
            localStorage.removeItem('ps310_visa_address');
        }
        
        // Update the main form's visa address dropdown
        const mainFormSelect = document.getElementById('visaAddress');
        if (mainFormSelect) {
            mainFormSelect.value = address;
        }
        
        // Update display
        this.updateToolbarDisplay();
        this.updateButtonStates();
        
        // Auto-connect if requested
        if (autoConnect && address) {
            this.connectDevice();
        }
    }
    
    /**
     * Update button states
     */
    updateButtonStates() {
        const connectBtn = document.getElementById('toolbar-connect-btn');
        const disconnectBtn = document.getElementById('toolbar-disconnect-btn');
        
        if (connectBtn && disconnectBtn) {
            if (this.connected) {
                connectBtn.disabled = true;
                disconnectBtn.disabled = false;
            } else {
                connectBtn.disabled = !this.currentAddress;
                disconnectBtn.disabled = true;
            }
        }
    }
    
    /**
     * Connect to the selected device
     */
    async connectDevice() {
        if (!this.currentAddress) {
            alert('Please select a VISA address first');
            return;
        }
        
        console.log(`🔗 Connecting to device: ${this.currentAddress}`);
        
        try {
            // Use the existing connectDevice function from the main GUI
            if (typeof window.connectDevice === 'function') {
                await window.connectDevice();
            } else {
                // Fallback: call API directly
                const response = await fetch('/connect', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({address: this.currentAddress})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.connected = true;
                    this.updateToolbarDisplay();
                    this.updateButtonStates();
                    this.closeDropdown();
                } else {
                    alert('Connection failed: ' + data.error);
                }
            }
        } catch (error) {
            console.error('❌ Connection error:', error);
            alert('Connection error: ' + error.message);
        }
    }
    
    /**
     * Disconnect from the device
     */
    async disconnectDevice() {
        console.log('🔌 Disconnecting from device...');
        
        try {
            // Use the existing disconnectDevice function from the main GUI
            if (typeof window.disconnectDevice === 'function') {
                await window.disconnectDevice();
            } else {
                // Fallback: call API directly
                const response = await fetch('/disconnect', {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.connected = false;
                    this.updateToolbarDisplay();
                    this.updateButtonStates();
                }
            }
        } catch (error) {
            console.error('❌ Disconnect error:', error);
        }
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
                this.selectDevice(e.target.value, false);
            });
        }
        
        // Connect button
        const connectBtn = document.getElementById('toolbar-connect-btn');
        if (connectBtn) {
            connectBtn.addEventListener('click', () => this.connectDevice());
        }
        
        // Disconnect button
        const disconnectBtn = document.getElementById('toolbar-disconnect-btn');
        if (disconnectBtn) {
            disconnectBtn.addEventListener('click', () => this.disconnectDevice());
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
     * Set connection state (called by main GUI)
     */
    setConnectionState(connected) {
        this.connected = connected;
        this.updateToolbarDisplay();
        this.updateButtonStates();
    }
    
    /**
     * Get current VISA address
     */
    getCurrentAddress() {
        return this.currentAddress || '';
    }
}

// Create and export singleton instance
const toolbarInstance = new PS310ConnectionToolbar();

// Expose in a namespaced global object to avoid pollution
window.LabDataLogging = window.LabDataLogging || {};
window.LabDataLogging.PS310ConnectionToolbar = toolbarInstance;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => toolbarInstance.init());
} else {
    // DOM already loaded, initialize now
    toolbarInstance.init();
}

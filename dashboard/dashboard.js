// Certificate Management Dashboard - JavaScript
// API Configuration
const API_URL = 'https://qnx2mwpyvb6o6lpt35bez3lywi0inesp.lambda-url.eu-west-1.on.aws/';

// Configuration (these will be populated from environment variables)
let API_CONFIG = {
    region: 'eu-west-1',
    certificatesTable: 'cert-management-dev-certificates',
    logsTable: 'cert-management-dev-certificate-logs',
    uploadsBucket: 'cert-management-dev-uploads-',
    accessKeyId: '', // Will be configured via IAM roles or environment
    secretAccessKey: '', // Will be configured via IAM roles or environment
};

// Global variables
let allCertificates = [];
let filteredCertificates = [];
let currentEditingCert = null;
let currentSortColumn = null;
let currentSortDirection = 'asc';

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
});

function initializeDashboard() {
    console.log('Initializing Certificate Management Dashboard...');
    // Load certificates first - populateEnvironmentFilter is called within loadCertificates after data is loaded
    loadCertificates();
}

function setupEventListeners() {
    // File upload (only if elements exist)
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('drop', handleFileDrop);
        fileInput.addEventListener('change', handleFileSelect);
    } else {
        console.log('Upload elements not found, skipping file upload event listeners');
    }
    
    // Forms (with defensive checks)
    const certForm = document.getElementById('certificateForm');
    const statusForm = document.getElementById('statusForm');
    
    if (certForm) {
        certForm.addEventListener('submit', handleCertificateSubmit);
    }
    if (statusForm) {
        statusForm.addEventListener('submit', handleStatusUpdate);
    }
}

// ===================================================================
// DATA LOADING AND MANAGEMENT
// ===================================================================

async function loadCertificates() {
    console.log('loadCertificates: Starting...');
    showLoading(true);
    
    try {
        console.log('loadCertificates: Calling fetchCertificatesFromAPI...');
        allCertificates = await fetchCertificatesFromAPI();
        console.log('loadCertificates: Received certificates:', allCertificates.length);
        
        filteredCertificates = [...allCertificates];
        console.log('loadCertificates: Filtered certificates:', filteredCertificates.length);
        
        console.log('loadCertificates: Updating statistics...');
        updateStatistics();
        
        console.log('loadCertificates: Rendering table...');
        renderCertificatesTable();
        
        console.log('loadCertificates: Populating environment filter...');
        populateEnvironmentFilter();
        
    } catch (error) {
        console.error('Error loading certificates:', error);
        showError('Failed to load certificates. Please try again.');
    } finally {
        showLoading(false);
    }
}

async function fetchCertificatesFromAPI() {
    // Call the actual DynamoDB API to get real certificate data
    try {
        console.log('Fetching certificates from API...');
        const response = await fetch(API_URL, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`Loaded ${data.count} certificates from DynamoDB`);
        
        return data.certificates || [];
        
    } catch (error) {
        console.error('Error fetching certificates:', error);
        
        // Show error message to user
        const tbody = document.getElementById('certificatesBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 40px; color: #d32f2f;">
                        <div>
                            <strong>⚠️ Error loading certificates</strong><br>
                            <small>${error.message}</small><br>
                            <small>Please check your internet connection and try refreshing the page.</small>
                        </div>
                    </td>
                </tr>
            `;
        }
        
        return [];
    }
}

// ===================================================================
// STATISTICS AND RENDERING
// ===================================================================

function updateStatistics() {
    const stats = {
        active: 0,
        renewal: 0,
        progress: 0,
        expired: 0
    };
    
    allCertificates.forEach(cert => {
        // Calculate actual status based on expiry date
        const daysLeft = calculateDaysLeft(cert.ExpiryDate);
        const actualStatus = calculateActualStatus(daysLeft, cert.Status);
        
        switch (actualStatus) {
            case 'Active':
                stats.active++;
                break;
            case 'Due for Renewal':
                stats.renewal++;
                break;
            case 'Renewal in Progress':
            case 'Renewal Done':
                stats.progress++;
                break;
            case 'Expired':
                stats.expired++;
                break;
        }
    });
    
    document.getElementById('activeCount').textContent = stats.active;
    document.getElementById('renewalCount').textContent = stats.renewal;
    document.getElementById('progressCount').textContent = stats.progress;
    document.getElementById('expiredCount').textContent = stats.expired;
}

function renderCertificatesTable() {
    console.log('renderCertificatesTable: Starting with', filteredCertificates.length, 'certificates');
    
    const tbody = document.getElementById('certificatesBody');
    const countElement = document.getElementById('certificateCount');
    
    console.log('renderCertificatesTable: tbody element:', tbody);
    console.log('renderCertificatesTable: countElement:', countElement);
    
    if (!tbody || !countElement) {
        console.error('renderCertificatesTable: Required DOM elements not found!');
        return;
    }
    
    tbody.innerHTML = '';
    countElement.textContent = `${filteredCertificates.length} certificates`;
    
    if (filteredCertificates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #666;">No certificates found</td></tr>';
        console.log('renderCertificatesTable: No certificates to display');
        return;
    }
    
    console.log('renderCertificatesTable: Creating rows for', filteredCertificates.length, 'certificates');
    
    filteredCertificates.forEach((cert, index) => {
        console.log(`renderCertificatesTable: Creating row ${index + 1} for:`, cert.CertificateName);
        const row = createCertificateRow(cert);
        tbody.appendChild(row);
    });
    
    console.log('renderCertificatesTable: Table rendering completed');
}

function createCertificateRow(cert) {
    const row = document.createElement('tr');
    
    const daysLeft = calculateDaysLeft(cert.ExpiryDate);
    
    // Recalculate status based on actual expiry date (override database status if needed)
    const actualStatus = calculateActualStatus(daysLeft, cert.Status);
    
    const daysLeftBadge = createDaysLeftBadge(daysLeft);
    const statusBadge = createStatusBadge(actualStatus);
    
    row.innerHTML = `
        <td>
            <strong>${cert.CertificateName}</strong>
            ${cert.Type ? `<br><small style="color: #666;">${cert.Type}</small>` : ''}
        </td>
        <td>
            <span class="environment-badge">${cert.Environment}</span>
        </td>
        <td>${cert.Application || '-'}</td>
        <td>${statusBadge}</td>
        <td>${formatDate(cert.ExpiryDate)}</td>
        <td>${daysLeftBadge}</td>
        <td>
            <div class="action-buttons">
                <button class="btn btn-primary btn-small" onclick="editCertificate('${cert.CertificateID}')" title="Edit Certificate">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn btn-success btn-small" onclick="updateStatus('${cert.CertificateID}')" title="Update Status">
                    <i class="fas fa-tasks"></i> Status
                </button>
                <button class="btn btn-warning btn-small" onclick="renewCertificate('${cert.CertificateID}')" title="Upload Renewed Certificate">
                    <i class="fas fa-upload"></i> Upload
                </button>
                <button class="btn btn-info btn-small" onclick="startRenewal('${cert.CertificateID}')" title="Start Renewal Process">
                    <i class="fas fa-sync-alt"></i> Renew
                </button>
                <button class="btn btn-secondary btn-small" onclick="viewLogs('${cert.CertificateID}')" title="View History">
                    <i class="fas fa-history"></i> Logs
                </button>
            </div>
        </td>
    `;
    
    return row;
}

function calculateActualStatus(daysLeft, currentStatus) {
    // Calculate status based on days left, but preserve manual status like "Renewal in Progress"
    if (daysLeft === null || daysLeft === undefined) {
        return currentStatus || 'Unknown';
    }
    
    // Preserve manual statuses
    const manualStatuses = ['Renewal in Progress', 'Renewal Done'];
    if (manualStatuses.includes(currentStatus)) {
        return currentStatus;
    }
    
    // Calculate based on days left
    if (daysLeft < 0) {
        return 'Expired';
    } else if (daysLeft <= 30) {
        return 'Due for Renewal';
    } else {
        return 'Active';
    }
}

function createStatusBadge(status) {
    const statusClass = status.toLowerCase().replace(/\s+/g, '-');
    const badgeClass = `status-${statusClass === 'due-for-renewal' ? 'renewal' : 
                      statusClass === 'renewal-in-progress' || statusClass === 'renewal-done' ? 'progress' : 
                      statusClass === 'expired' ? 'expired' : 'active'}`;
    
    return `<span class="status-badge ${badgeClass}">${status}</span>`;
}

function createDaysLeftBadge(days) {
    if (days === null || days === undefined) {
        return '<span class="days-badge days-normal">-</span>';
    }
    
    let badgeClass = 'days-normal';
    let text = `${days} days`;
    
    if (days < 0) {
        badgeClass = 'days-urgent';
        text = `Expired ${Math.abs(days)} days ago`;
    } else if (days <= 7) {
        badgeClass = 'days-urgent';
    } else if (days <= 30) {
        badgeClass = 'days-warning';
    }
    
    return `<span class="days-badge ${badgeClass}">${text}</span>`;
}

function calculateDaysLeft(expiryDate) {
    if (!expiryDate) return null;
    
    const expiry = new Date(expiryDate);
    const today = new Date();
    const diffTime = expiry - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays;
}

function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// ===================================================================
// FILTERING AND SEARCH
// ===================================================================

function filterCertificates() {
    const searchTerm = document.getElementById('searchBox').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    const environmentFilter = document.getElementById('environmentFilter').value;
    
    filteredCertificates = allCertificates.filter(cert => {
        const matchesSearch = !searchTerm || 
            cert.CertificateName.toLowerCase().includes(searchTerm) ||
            cert.Application.toLowerCase().includes(searchTerm) ||
            cert.OwnerEmail.toLowerCase().includes(searchTerm);
        
        const matchesStatus = !statusFilter || cert.Status === statusFilter;
        const matchesEnvironment = !environmentFilter || cert.Environment === environmentFilter;
        
        return matchesSearch && matchesStatus && matchesEnvironment;
    });
    
    renderCertificatesTable();
}

function populateEnvironmentFilter() {
    const environmentFilter = document.getElementById('environmentFilter');
    
    // Add defensive check
    if (!environmentFilter) {
        console.error('populateEnvironmentFilter: environmentFilter element not found');
        return;
    }
    
    if (!allCertificates || allCertificates.length === 0) {
        console.log('populateEnvironmentFilter: No certificates available yet');
        return;
    }
    
    const environments = [...new Set(allCertificates.map(cert => cert.Environment))];
    
    // Clear existing options except "All Environments"
    environmentFilter.innerHTML = '<option value="">All Environments</option>';
    
    environments.forEach(env => {
        const option = document.createElement('option');
        option.value = env;
        option.textContent = env;
        environmentFilter.appendChild(option);
    });
    
    console.log(`populateEnvironmentFilter: Added ${environments.length} environments to filter`);
}

function sortTable(column) {
    // Toggle sort direction if clicking the same column
    if (currentSortColumn === column) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortColumn = column;
        currentSortDirection = 'asc';
    }
    
    // Sort the filtered certificates
    filteredCertificates.sort((a, b) => {
        let aValue, bValue;
        
        switch(column) {
            case 'CertificateName':
                aValue = a.CertificateName || '';
                bValue = b.CertificateName || '';
                break;
            case 'Environment':
                aValue = a.Environment || '';
                bValue = b.Environment || '';
                break;
            case 'Application':
                aValue = a.Application || '';
                bValue = b.Application || '';
                break;
            case 'Status':
                aValue = a.Status || '';
                bValue = b.Status || '';
                break;
            case 'ExpiryDate':
                aValue = new Date(a.ExpiryDate || '9999-12-31');
                bValue = new Date(b.ExpiryDate || '9999-12-31');
                break;
            case 'DaysLeft':
                aValue = calculateDaysLeft(a.ExpiryDate);
                bValue = calculateDaysLeft(b.ExpiryDate);
                // Handle null values
                if (aValue === null) aValue = -9999;
                if (bValue === null) bValue = -9999;
                break;
            default:
                return 0;
        }
        
        // Compare values
        let comparison = 0;
        if (aValue > bValue) {
            comparison = 1;
        } else if (aValue < bValue) {
            comparison = -1;
        }
        
        // Apply sort direction
        return currentSortDirection === 'asc' ? comparison : -comparison;
    });
    
    // Update sort icons in headers
    updateSortIcons(column);
    
    // Re-render the table
    renderCertificatesTable();
}

function updateSortIcons(activeColumn) {
    // Reset all sort icons
    const headers = document.querySelectorAll('th[onclick]');
    headers.forEach(header => {
        const icon = header.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-sort';
        }
    });
    
    // Update the active column icon
    const columnMap = {
        'CertificateName': 0,
        'Environment': 1,
        'Application': 2,
        'Status': 3,
        'ExpiryDate': 4,
        'DaysLeft': 5
    };
    
    const columnIndex = columnMap[activeColumn];
    if (columnIndex !== undefined) {
        const activeHeader = headers[columnIndex];
        const icon = activeHeader.querySelector('i');
        if (icon) {
            icon.className = currentSortDirection === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down';
        }
    }
}

// ===================================================================
// MODAL MANAGEMENT
// ===================================================================

function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
    
    if (modalId === 'addCertModal' && !currentEditingCert) {
        clearCertificateForm();
        document.getElementById('modalTitle').textContent = 'Add New Certificate';
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    
    if (modalId === 'addCertModal') {
        currentEditingCert = null;
        clearCertificateForm();
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// ===================================================================
// CERTIFICATE MANAGEMENT
// ===================================================================

function clearCertificateForm() {
    document.getElementById('certificateForm').reset();
}

async function handleCertificateSubmit(event) {
    event.preventDefault();
    
    const formData = {
        CertificateName: document.getElementById('certName').value,
        Environment: document.getElementById('certEnvironment').value,
        Application: document.getElementById('certApplication').value,
        ExpiryDate: document.getElementById('certExpiryDate').value,
        Type: document.getElementById('certType').value,
        OwnerEmail: document.getElementById('certOwnerEmail').value,
        SupportEmail: document.getElementById('certSupportEmail').value,
        AccountNumber: document.getElementById('certAccountNumber').value,
    };
    
    console.log('Form data to submit:', formData);
    
    try {
        if (currentEditingCert) {
            console.log('Updating certificate:', currentEditingCert.CertificateID);
            await updateCertificate(currentEditingCert.CertificateID, formData);
            showSuccess('Certificate updated successfully!');
        } else {
            console.log('Adding new certificate...');
            await addNewCertificate(formData);
            showSuccess('Certificate added successfully!');
        }
        
        closeModal('addCertModal');
        await loadCertificates();
        
    } catch (error) {
        console.error('Error saving certificate:', error);
        console.error('Error details:', error.message, error.stack);
        showError('Failed to save certificate. Please try again. Error: ' + error.message);
    }
}

async function addNewCertificate(certData) {
    // Calculate initial status based on expiry date
    const daysLeft = calculateDaysLeft(certData.ExpiryDate);
    let status = 'Active';
    
    if (daysLeft < 0) {
        status = 'Expired';
    } else if (daysLeft <= 30) {
        status = 'Due for Renewal';
    }
    
    const newCert = {
        ...certData,
        CertificateID: generateUUID(),
        Status: status,
        DaysUntilExpiry: daysLeft.toString(),
        LastUpdatedOn: new Date().toISOString(),
        CreatedOn: new Date().toISOString(),
        Version: 1,
        ImportedFrom: 'Dashboard'
    };
    
    console.log('Sending POST request to:', API_URL);
    console.log('Certificate data:', newCert);
    
    // Call the API to add certificate to DynamoDB
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(newCert)
        });
        
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        const result = await response.json();
        console.log('Response data:', result);
        
        if (!response.ok) {
            const errorMsg = result.error || result.message || 'Failed to add certificate';
            console.error('API error:', errorMsg);
            throw new Error(errorMsg);
        }
        
        console.log('Certificate added successfully:', result);
        return result;
    } catch (error) {
        console.error('Error in addNewCertificate:', error);
        throw error;
    }
}

async function updateCertificate(certId, certData) {
    // Calculate status if expiry date changed
    if (certData.ExpiryDate) {
        const daysLeft = calculateDaysLeft(certData.ExpiryDate);
        if (daysLeft < 0) {
            certData.Status = 'Expired';
        } else if (daysLeft <= 30) {
            certData.Status = 'Due for Renewal';
        } else {
            certData.Status = 'Active';
        }
        certData.DaysUntilExpiry = daysLeft.toString();
    }
    
    const updateData = {
        ...certData,
        CertificateID: certId,
        LastUpdatedOn: new Date().toISOString()
    };
    
    // Call the API to update certificate in DynamoDB
    try {
        const response = await fetch(API_URL, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updateData)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || result.message || 'Failed to update certificate');
        }
        
        console.log('Certificate updated successfully:', result);
        return result;
    } catch (error) {
        console.error('Error updating certificate:', error);
        throw error;
    }
}

function editCertificate(certId) {
    const cert = allCertificates.find(c => c.CertificateID === certId);
    if (!cert) return;
    
    currentEditingCert = cert;
    
    // Populate form
    document.getElementById('certName').value = cert.CertificateName || '';
    document.getElementById('certEnvironment').value = cert.Environment || '';
    document.getElementById('certApplication').value = cert.Application || '';
    document.getElementById('certExpiryDate').value = cert.ExpiryDate || '';
    document.getElementById('certType').value = cert.Type || '';
    document.getElementById('certOwnerEmail').value = cert.OwnerEmail || '';
    document.getElementById('certSupportEmail').value = cert.SupportEmail || '';
    document.getElementById('certAccountNumber').value = cert.AccountNumber || '';
    
    document.getElementById('modalTitle').textContent = 'Edit Certificate';
    openModal('addCertModal');
}

// ===================================================================
// STATUS MANAGEMENT
// ===================================================================

function updateStatus(certId) {
    const cert = allCertificates.find(c => c.CertificateID === certId);
    if (!cert) return;
    
    currentEditingCert = cert;
    
    // Pre-populate current status
    document.getElementById('newStatus').value = cert.Status || '';
    document.getElementById('incidentNumber').value = cert.IncidentNumber || '';
    
    openModal('statusModal');
}

async function handleStatusUpdate(event) {
    event.preventDefault();
    
    if (!currentEditingCert) return;
    
    const statusData = {
        Status: document.getElementById('newStatus').value,
        IncidentNumber: document.getElementById('incidentNumber').value,
        StatusNotes: document.getElementById('statusNotes').value,
    };
    
    try {
        await updateCertificateStatus(currentEditingCert.CertificateID, statusData);
        showSuccess('Certificate status updated successfully!');
        closeModal('statusModal');
        await loadCertificates();
        
    } catch (error) {
        console.error('Error updating status:', error);
        showError('Failed to update certificate status. Please try again.');
    }
}

async function updateCertificateStatus(certId, statusData) {
    // In production, this would call the API and log the change
    console.log('Updating certificate status:', certId, statusData);
    
    const index = allCertificates.findIndex(cert => cert.CertificateID === certId);
    if (index !== -1) {
        allCertificates[index] = {
            ...allCertificates[index],
            ...statusData,
            LastUpdatedOn: new Date().toISOString()
        };
        
        // Add log entry (in production, this would be saved to the logs table)
        console.log('Log entry created for status change');
    }
}

// ===================================================================
// CERTIFICATE RENEWAL
// ===================================================================
// CERTIFICATE RENEWAL FUNCTIONS
// ===================================================================

function startRenewal(certId) {
    const cert = allCertificates.find(c => c.CertificateID === certId);
    if (!cert) {
        showError('Certificate not found');
        return;
    }
    
    // Confirm renewal action
    const confirmMessage = `Start renewal process for:\n\n` +
                          `Certificate: ${cert.CertificateName}\n` +
                          `Environment: ${cert.Environment}\n` +
                          `Current Status: ${cert.Status}\n` +
                          `Expiry Date: ${formatDate(cert.ExpiryDate)}\n\n` +
                          `This will change the status to "Renewal in Progress".\n\n` +
                          `Continue?`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    // Update certificate status to "Renewal in Progress"
    updateCertificateStatus(certId, 'Renewal in Progress', 'Renewal process initiated');
}

async function updateCertificateStatus(certId, newStatus, notes = '') {
    try {
        showLoading(true);
        
        const cert = allCertificates.find(c => c.CertificateID === certId);
        if (!cert) {
            throw new Error('Certificate not found');
        }
        
        // Prepare update payload
        const updatePayload = {
            CertificateID: certId,
            Status: newStatus,
            LastModified: new Date().toISOString(),
            Notes: notes
        };
        
        console.log('Updating certificate status:', updatePayload);
        
        const response = await fetch(API_URL, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatePayload)
        });
        
        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`Failed to update status: ${response.status} - ${errorData}`);
        }
        
        const result = await response.json();
        console.log('Status update result:', result);
        
        showSuccess(`Certificate status updated to "${newStatus}"`);
        
        // Reload certificates to get updated data
        await loadCertificates();
        
    } catch (error) {
        console.error('Error updating certificate status:', error);
        showError(`Failed to update status: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

function renewCertificate(certId) {
    const cert = allCertificates.find(c => c.CertificateID === certId);
    if (!cert) return;
    
    currentEditingCert = cert;
    
    // Create renewal modal HTML if it doesn't exist
    if (!document.getElementById('renewalModal')) {
        createRenewalModal();
    }
    
    // Pre-populate certificate information
    document.getElementById('renewalCertName').textContent = cert.CertificateName;
    document.getElementById('renewalCurrentExpiry').textContent = formatDate(cert.ExpiryDate);
    document.getElementById('renewalEnvironment').textContent = cert.Environment;
    
    openModal('renewalModal');
}

function createRenewalModal() {
    const modalHTML = `
    <div id="renewalModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Upload Renewed Certificate</h2>
                <span class="close" onclick="closeModal('renewalModal')">&times;</span>
            </div>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h4>Current Certificate:</h4>
                <p><strong>Name:</strong> <span id="renewalCertName"></span></p>
                <p><strong>Current Expiry:</strong> <span id="renewalCurrentExpiry"></span></p>
                <p><strong>Environment:</strong> <span id="renewalEnvironment"></span></p>
            </div>
            <form id="renewalForm">
                <div class="form-group">
                    <label for="newExpiryDate">New Expiry Date *</label>
                    <input type="date" id="newExpiryDate" required>
                </div>
                <div class="form-group">
                    <label for="renewalIncident">ServiceNow Incident Number</label>
                    <input type="text" id="renewalIncident" placeholder="INC1234567">
                </div>
                <div class="form-group">
                    <label for="renewalNotes">Renewal Notes</label>
                    <textarea id="renewalNotes" placeholder="Details about the certificate renewal..."></textarea>
                </div>
                <div class="form-group">
                    <label for="certificateFile">Upload New Certificate File (Optional)</label>
                    <input type="file" id="certificateFile" accept=".crt,.cer,.pem,.p12,.pfx">
                    <small style="color: #666;">Upload the new certificate file for backup purposes</small>
                </div>
                <div class="form-group" style="display: flex; gap: 10px;">
                    <button type="submit" class="btn btn-success">
                        <i class="fas fa-save"></i> Complete Renewal
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="closeModal('renewalModal')">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                </div>
            </form>
        </div>
    </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add form submit handler
    document.getElementById('renewalForm').addEventListener('submit', handleRenewalSubmit);
}

async function handleRenewalSubmit(event) {
    event.preventDefault();
    
    if (!currentEditingCert) return;
    
    const renewalData = {
        newExpiryDate: document.getElementById('newExpiryDate').value,
        incidentNumber: document.getElementById('renewalIncident').value,
        renewalNotes: document.getElementById('renewalNotes').value,
        certificateFile: document.getElementById('certificateFile').files[0]
    };
    
    try {
        await processCertificateRenewal(currentEditingCert.CertificateID, renewalData);
        showSuccess('Certificate renewed successfully!');
        closeModal('renewalModal');
        await loadCertificates();
        
    } catch (error) {
        console.error('Error renewing certificate:', error);
        showError('Failed to renew certificate. Please try again.');
    }
}

async function processCertificateRenewal(certId, renewalData) {
    // Archive the old certificate data
    const oldCert = allCertificates.find(cert => cert.CertificateID === certId);
    
    // Create archive entry
    const archiveEntry = {
        ...oldCert,
        ArchivedOn: new Date().toISOString(),
        ArchivedReason: 'RENEWED',
        IncidentNumber: renewalData.incidentNumber
    };
    
    // Update certificate with new expiry date and status
    const updatedCert = {
        ...oldCert,
        ExpiryDate: renewalData.newExpiryDate,
        Status: 'Active', // Reset to Active after renewal
        IncidentNumber: renewalData.incidentNumber,
        RenewedBy: 'Dashboard User', // In production, this would be the logged-in user
        RenewalLog: renewalData.renewalNotes,
        LastUpdatedOn: new Date().toISOString(),
        Version: (oldCert.Version || 1) + 1,
        PreviousVersion: oldCert.Version || 1
    };
    
    // In production, this would:
    // 1. Upload certificate file to S3 if provided
    // 2. Update DynamoDB with new certificate data
    // 3. Create log entries for the renewal
    // 4. Archive the old certificate data
    
    console.log('Processing certificate renewal:', {
        certificateId: certId,
        oldCertificate: archiveEntry,
        newCertificate: updatedCert,
        renewalData: renewalData
    });
    
    // Update local data
    const index = allCertificates.findIndex(cert => cert.CertificateID === certId);
    if (index !== -1) {
        allCertificates[index] = updatedCert;
    }
    
    // Simulate file upload if certificate file is provided
    if (renewalData.certificateFile) {
        console.log('Certificate file would be uploaded to S3:', renewalData.certificateFile.name);
    }
}

// ===================================================================
// FILE UPLOAD MANAGEMENT (Updated to remove Excel upload)
// ===================================================================

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.classList.add('dragover');
    }
}

function handleFileDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.classList.remove('dragover');
    }
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
}

function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
}

async function handleFileUpload(file) {
    if (!file.name.match(/\.(xlsx|xls)$/i)) {
        showError('Please select a valid Excel file (.xlsx or .xls)');
        return;
    }
    
    if (file.size > 50 * 1024 * 1024) { // 50MB limit
        showError('File size too large. Please select a file under 50MB.');
        return;
    }
    
    try {
        showUploadProgress(true);
        await uploadFileToS3(file);
        showSuccess('File uploaded successfully! Processing will begin automatically.');
        closeModal('uploadModal');
        
        // Refresh data after a delay to allow processing
        setTimeout(() => {
            loadCertificates();
        }, 5000);
        
    } catch (error) {
        console.error('Upload error:', error);
        showError('Failed to upload file. Please try again.');
    } finally {
        showUploadProgress(false);
    }
}

async function uploadFileToS3(file) {
    // In production, this would upload to S3 and trigger Lambda processing
    return new Promise((resolve) => {
        // Simulate upload progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += 10;
            updateProgressBar(progress);
            
            if (progress >= 100) {
                clearInterval(interval);
                resolve();
            }
        }, 200);
    });
}

function showUploadProgress(show) {
    document.getElementById('uploadProgress').style.display = show ? 'block' : 'none';
    if (!show) {
        updateProgressBar(0);
    }
}

function updateProgressBar(percentage) {
    document.getElementById('progressBar').style.width = `${percentage}%`;
    document.getElementById('uploadStatus').textContent = 
        percentage < 100 ? `Uploading file... ${percentage}%` : 'Upload complete!';
}

// ===================================================================
// UTILITY FUNCTIONS
// ===================================================================

function refreshData() {
    loadCertificates();
}

function exportData() {
    // Create CSV content
    const headers = ['Certificate Name', 'Environment', 'Application', 'Status', 'Expiry Date', 'Days Left', 'Owner Email', 'Support Email', 'Type', 'Account Number'];
    const csvContent = [
        headers.join(','),
        ...filteredCertificates.map(cert => [
            cert.CertificateName,
            cert.Environment,
            cert.Application,
            cert.Status,
            cert.ExpiryDate,
            calculateDaysLeft(cert.ExpiryDate),
            cert.OwnerEmail || '',
            cert.SupportEmail || '',
            cert.Type || '',
            cert.AccountNumber || ''
        ].map(field => `"${field}"`).join(','))
    ].join('\n');
    
    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `certificates_export_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function viewLogs(certId) {
    // In production, this would open a modal showing certificate history/logs
    alert(`Viewing logs for certificate ID: ${certId}\n\nThis would show:\n- Status change history\n- Renewal history\n- Upload history\n- Notification history`);
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

function showError(message) {
    // Simple alert for now - in production would use a proper notification system
    alert('Error: ' + message);
}

function showSuccess(message) {
    // Simple alert for now - in production would use a proper notification system
    alert('Success: ' + message);
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// ===================================================================
// AWS SDK INTEGRATION (for production)
// ===================================================================

// Note: In production, you would initialize AWS SDK here
// and replace the demo functions with actual API calls

/*
// Example AWS SDK initialization
AWS.config.update({
    region: API_CONFIG.region,
    credentials: new AWS.CognitoIdentityCredentials({
        IdentityPoolId: 'your-identity-pool-id'
    })
});

const dynamodb = new AWS.DynamoDB.DocumentClient();
const s3 = new AWS.S3();
*/
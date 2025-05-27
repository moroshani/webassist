// Show loading spinner
function showLoading() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-overlay';
    spinner.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    document.body.appendChild(spinner);
}

// Hide loading spinner
function hideLoading() {
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.remove();
    }
}

// Get CSRF token from cookie (Django recommended way)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.appendChild(toast);
    document.body.appendChild(container);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        container.remove();
    });
}

// Handle AJAX errors
function handleAjaxError(error) {
    console.error('AJAX Error:', error);
    showToast('An error occurred. Please try again.', 'danger');
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Add detailed logging for all submit buttons (especially settings form)
document.querySelectorAll('button[type="submit"]').forEach(button => {
    button.addEventListener('click', function(event) {
        console.log("Submit button clicked. Form:", this.form);
        if (this.form) {
            console.log("Form validity check:", this.form.checkValidity());
            if (this.form.checkValidity()) {
                this.disabled = true;
                this.innerHTML = `
                    <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                    Loading...
                `;
                console.log("Form is valid, attempting default submission.");
                // Default submission will proceed
            } else {
                console.log("Form is NOT valid. Forcing reportValidity().");
                this.form.reportValidity();
                // event.preventDefault(); // Optionally prevent submission if you want to handle errors customly
            }
        } else {
            console.error("Button is not associated with a form.");
        }
    });
});

// --- Bootstrap Modal for Confirm ---
function showConfirm(message, callback) {
    let modal = document.getElementById('confirmModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.innerHTML = `
        <div class="modal fade" id="confirmModal" tabindex="-1" aria-labelledby="confirmModalLabel" aria-hidden="true">
          <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title" id="confirmModalLabel">Confirm</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body" id="confirmModalBody"></div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" id="confirmModalOk">Delete</button>
              </div>
            </div>
          </div>
        </div>`;
        document.body.appendChild(modal);
    }
    document.getElementById('confirmModalBody').innerHTML = message;
    const okBtn = document.getElementById('confirmModalOk');
    const bsModal = new bootstrap.Modal(document.getElementById('confirmModal'));
    function onOk() {
        okBtn.removeEventListener('click', onOk);
        bsModal.hide();
        callback();
    }
    okBtn.addEventListener('click', onOk);
    bsModal.show();
} 
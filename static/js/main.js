// Show loading spinner
function showLoading() {
    const existingSpinner = document.querySelector('.spinner-overlay');
    if (existingSpinner) return; // Prevent multiple spinners

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
    const toastContainer = document.getElementById('toastPlacement');
    if (!toastContainer) {
        console.error('Toast container #toastPlacement not found.');
        // Fallback or create a default container if needed
        const tempContainer = document.createElement('div');
        tempContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        tempContainer.style.zIndex = "1090"; // Ensure it's above modals
        document.body.appendChild(tempContainer);
         // Use this tempContainer for the current toast
    }
    
    const toastEl = document.createElement('div'); // Renamed
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Append to the designated container or the temporary one
    (toastContainer || document.querySelector('.toast-container')).appendChild(toastEl);
    
    const bsToast = new bootstrap.Toast(toastEl);
    bsToast.show();
    
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
        // If a temporary container was used and is now empty, remove it
        const tempC = document.querySelector('.toast-container');
        if (tempC && !tempC.hasChildNodes() && tempC !== toastContainer){
            tempC.remove();
        }
    });
}

// Handle AJAX errors
function handleAjaxError(error, defaultMessage = 'An error occurred. Please try again.') {
    console.error('AJAX Error:', error);
    let message = defaultMessage;
    if (error && error.message) {
        message = error.message;
    } else if (typeof error === 'string') {
        message = error;
    }
    showToast(message, 'danger');
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Submit button loading state
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(event) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton && !submitButton.classList.contains('no-disable')) { // Add 'no-disable' class to buttons you don't want to disable
                if (form.checkValidity()) {
                    submitButton.disabled = true;
                    submitButton.innerHTML = `
                        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                        Loading...
                    `;
                } else {
                    // If form is invalid, modern browsers will show validation messages.
                    // No need to manually call reportValidity() usually, as submit event implies it.
                    // Re-enable button if submission is prevented by browser validation
                    // This might be tricky as the 'submit' event might not even fire if invalid.
                    // A 'click' listener on the button might be more robust for this part.
                }
            }
        });
    });
     // More robust submit button handling for loading state
    document.querySelectorAll('button[type="submit"]').forEach(button => {
        button.addEventListener('click', function(event) {
            const form = this.form;
            if (form && !this.classList.contains('no-disable')) {
                if (form.checkValidity()) {
                    // If the form is valid, it will submit. The 'submit' listener above will handle disabling.
                    // This click listener doesn't need to do much if valid.
                } else {
                    // If form is invalid, browser's default validation will trigger.
                    // Explicitly call reportValidity() if you want to ensure messages show
                    // or if you have custom validation logic before this.
                    if (typeof form.reportValidity === 'function') {
                        form.reportValidity();
                    }
                    // Do not disable the button here, as submission is prevented.
                }
            }
        });
    });


    // Add a placement for toast messages in base.html if it doesn't exist
    if (!document.getElementById('toastPlacement')) {
        const toastPlacement = document.createElement('div');
        toastPlacement.id = 'toastPlacement';
        toastPlacement.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        toastPlacement.style.zIndex = "1090"; // Higher than modals (Bootstrap modal z-index is 1055)
        document.body.appendChild(toastPlacement);
    }

});

// --- Bootstrap Modal for Confirm ---
function showConfirm(message, callback, title = 'Confirm Action') {
    let modalEl = document.getElementById('confirmModal');
    if (!modalEl) {
        const modalDiv = document.createElement('div');
        modalDiv.innerHTML = `
        <div class="modal fade" id="confirmModal" tabindex="-1" aria-labelledby="confirmModalLabel" aria-hidden="true">
          <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title" id="confirmModalLabel">Confirm Action</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body" id="confirmModalBody"></div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="confirmModalCancel">Cancel</button>
                <button type="button" class="btn btn-danger" id="confirmModalOk">OK</button>
              </div>
            </div>
          </div>
        </div>`;
        document.body.appendChild(modalDiv.firstChild); // Append the modal element itself
        modalEl = document.getElementById('confirmModal');
    }
    
    document.getElementById('confirmModalLabel').textContent = title;
    document.getElementById('confirmModalBody').innerHTML = message; // Use innerHTML to allow HTML in message
    
    const okBtn = document.getElementById('confirmModalOk');
    const cancelBtn = document.getElementById('confirmModalCancel');
    const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl); // Use getOrCreateInstance

    // Clone and replace the OK button to remove previous event listeners
    const newOkBtn = okBtn.cloneNode(true);
    okBtn.parentNode.replaceChild(newOkBtn, okBtn);

    newOkBtn.addEventListener('click', function onOkClick() {
        bsModal.hide();
        callback(true); // Pass true to indicate confirmation
    });
    
    // Also handle cancel/dismiss actions
    const onModalHidden = () => {
        // Check if callback was already called by OK button
        // This part might be tricky if you need to distinguish between OK and other close actions
        // For simplicity, we assume callback handles its own logic if already executed.
        modalEl.removeEventListener('hidden.bs.modal', onModalHidden);
    };
    modalEl.addEventListener('hidden.bs.modal', onModalHidden, { once: true });


    bsModal.show();
}
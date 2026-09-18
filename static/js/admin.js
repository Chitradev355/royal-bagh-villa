/**
 * admin.js - Royal Bagh Villa Admin Dashboard Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // Mobile Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const adminSidebar = document.querySelector('.admin-sidebar');
    
    if (sidebarToggle && adminSidebar) {
        sidebarToggle.addEventListener('click', () => {
            adminSidebar.classList.toggle('-translate-x-full');
        });
    }

    // Status Update Dropdowns for Orders/Bookings
    const statusSelects = document.querySelectorAll('.status-update-select');
    statusSelects.forEach(select => {
        select.addEventListener('change', async (e) => {
            const entityType = e.target.dataset.type; // 'order', 'room_booking', 'event_booking'
            const entityId = e.target.dataset.id;
            const newStatus = e.target.value;
            
            try {
                const response = await fetch(`/admin/api/status/update`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        type: entityType,
                        id: entityId,
                        status: newStatus
                    })
                });
                
                const data = await response.json();
                if (response.ok) {
                    showToast('Status updated successfully', 'success');
                } else {
                    showToast(data.error || 'Failed to update status', 'error');
                    // Revert select on failure
                    e.target.value = e.target.dataset.originalStatus;
                }
            } catch (err) {
                console.error(err);
                showToast('Network error', 'error');
                e.target.value = e.target.dataset.originalStatus;
            }
        });
        
        // Store original value to revert if API fails
        select.dataset.originalStatus = select.value;
    });

    // Delete Confirmation dialogs
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Image Upload Preview
    const imageInput = document.getElementById('image_upload');
    const imagePreview = document.getElementById('image_preview');
    
    if (imageInput && imagePreview) {
        imageInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreview.classList.remove('hidden');
                }
                reader.readAsDataURL(file);
            }
        });
    }

    // Table Filtering (Client-side simple filter)
    const searchInput = document.getElementById('table-search');
    const dataTable = document.getElementById('data-table');
    
    if (searchInput && dataTable) {
        searchInput.addEventListener('keyup', (e) => {
            const term = e.target.value.toLowerCase();
            const rows = dataTable.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(term)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
});

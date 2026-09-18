/**
 * booking.js - Event and Room Booking Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // Set minimum dates for all date inputs to today
    const dateInputs = document.querySelectorAll('input[type="date"]');
    if (dateInputs.length > 0) {
        const today = new Date().toISOString().split('T')[0];
        dateInputs.forEach(input => {
            input.setAttribute('min', today);
        });
    }

    // Date validation for check-out (must be after check-in)
    const checkInInput = document.getElementById('check_in');
    const checkOutInput = document.getElementById('check_out');
    
    if (checkInInput && checkOutInput) {
        checkInInput.addEventListener('change', () => {
            const checkInDate = new Date(checkInInput.value);
            if (!isNaN(checkInDate.getTime())) {
                // Check out min date is the day after check in
                checkInDate.setDate(checkInDate.getDate() + 1);
                const nextDay = checkInDate.toISOString().split('T')[0];
                checkOutInput.setAttribute('min', nextDay);
                
                if (checkOutInput.value && checkOutInput.value < nextDay) {
                    checkOutInput.value = nextDay;
                }
            }
        });
    }

    // Event Booking - Dynamic Quote Calculation
    const eventForm = document.getElementById('event-booking-form');
    if (eventForm) {
        const guestInput = document.getElementById('guest_count');
        const packageSelect = document.getElementById('food_package');
        const quoteDisplay = document.getElementById('estimated-quote');
        const quoteValue = document.getElementById('quote-value');

        const calculateQuote = () => {
            if (!guestInput || !packageSelect || !quoteDisplay) return;
            
            const guests = parseInt(guestInput.value) || 0;
            const pkg = packageSelect.value;
            
            let perPersonRate = 0;
            if (pkg === 'standard') perPersonRate = 1200;
            else if (pkg === 'premium') perPersonRate = 1800;
            else if (pkg === 'luxury') perPersonRate = 2500;
            else {
                quoteDisplay.classList.add('hidden');
                return;
            }

            if (guests > 0) {
                const total = guests * perPersonRate;
                quoteValue.textContent = formatCurrency(total);
                quoteDisplay.classList.remove('hidden');
            } else {
                quoteDisplay.classList.add('hidden');
            }
        };

        guestInput.addEventListener('input', calculateQuote);
        packageSelect.addEventListener('change', calculateQuote);
    }

    // Handle AJAX Form Submissions gracefully
    const ajaxForms = document.querySelectorAll('.ajax-form');
    ajaxForms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<div class="spinner"></div> Processing...';
            
            try {
                const formData = new FormData(form);
                const url = form.getAttribute('action') || window.location.href;
                
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCsrfToken()
                    }
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showToast(data.message || 'Success!', 'success');
                    if (data.redirect_url) {
                        setTimeout(() => {
                            window.location.href = data.redirect_url;
                        }, 1500);
                    } else {
                        form.reset();
                    }
                } else {
                    showToast(data.error || 'An error occurred', 'error');
                }
            } catch (err) {
                console.error('Form submission error:', err);
                showToast('Network error. Please try again.', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        });
    });

    // Check status logic
    const statusForm = document.getElementById('status-check-form');
    if (statusForm) {
        statusForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const idInput = document.getElementById('booking_id');
            const resultDiv = document.getElementById('status-result');
            
            if (!idInput.value.trim()) return;

            try {
                const response = await fetch(`/api/status/${idInput.value.trim()}`);
                const data = await response.json();
                
                if (response.ok) {
                    resultDiv.innerHTML = `
                        <div class="p-4 bg-white border border-gray-200 rounded-lg mt-4">
                            <h4 class="font-bold text-lg mb-2">Status: <span class="text-accent uppercase">${data.status}</span></h4>
                            <p class="text-gray-600">Type: ${data.type}</p>
                            <p class="text-gray-600">Date: ${data.date}</p>
                        </div>
                    `;
                    resultDiv.classList.remove('hidden');
                } else {
                    showToast(data.error || 'Record not found', 'error');
                    resultDiv.classList.add('hidden');
                }
            } catch (err) {
                showToast('Error checking status', 'error');
            }
        });
    }
});

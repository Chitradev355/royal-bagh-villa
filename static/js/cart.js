/**
 * cart.js - Royal Bagh Villa Shopping Cart Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    updateCartBadge();

    // Attach event listeners to Add to Cart buttons
    document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const itemId = e.target.closest('button').dataset.id;
            addToCart(itemId, 1);
        });
    });

    // Attach event listeners to cart page inputs
    const cartContainer = document.getElementById('cart-items-container');
    if (cartContainer) {
        cartContainer.addEventListener('change', (e) => {
            if (e.target.classList.contains('cart-qty-input')) {
                const itemId = e.target.dataset.id;
                const newQty = parseInt(e.target.value);
                if (newQty > 0) {
                    updateCartItem(itemId, newQty);
                } else {
                    removeFromCart(itemId);
                }
            }
        });

        cartContainer.addEventListener('click', (e) => {
            if (e.target.closest('.remove-item-btn')) {
                const btn = e.target.closest('.remove-item-btn');
                const itemId = btn.dataset.id;
                removeFromCart(itemId);
            }
        });
    }
});

// API Calls
const addToCart = async (itemId, quantity = 1) => {
    try {
        const response = await fetch('/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ item_id: itemId, quantity: quantity })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Item added to cart', 'success');
            updateCartBadge(data.cart_count);
        } else {
            showToast(data.error || 'Failed to add item', 'error');
        }
    } catch (err) {
        console.error('Error adding to cart:', err);
        showToast('Network error occurred', 'error');
    }
};

const updateCartItem = async (itemId, quantity) => {
    try {
        const response = await fetch('/api/cart/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ item_id: itemId, quantity: quantity })
        });
        
        if (response.ok) {
            window.location.reload(); // Reload to reflect changes in totals
        } else {
            showToast('Failed to update cart', 'error');
        }
    } catch (err) {
        console.error('Error updating cart:', err);
    }
};

const removeFromCart = async (itemId) => {
    try {
        const response = await fetch(`/api/cart/remove/${itemId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (response.ok) {
            showToast('Item removed', 'info');
            window.location.reload();
        } else {
            showToast('Failed to remove item', 'error');
        }
    } catch (err) {
        console.error('Error removing from cart:', err);
    }
};

const clearCart = async () => {
    if (!confirm('Are you sure you want to clear your cart?')) return;
    
    try {
        const response = await fetch('/api/cart/clear', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (response.ok) {
            window.location.reload();
        }
    } catch (err) {
        console.error('Error clearing cart:', err);
    }
};

// UI Updates
const updateCartBadge = async (count = null) => {
    const badge = document.getElementById('cart-badge-count');
    if (!badge) return;

    if (count !== null) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
        return;
    }

    try {
        const response = await fetch('/api/cart');
        if (response.ok) {
            const data = await response.json();
            badge.textContent = data.count;
            badge.style.display = data.count > 0 ? 'flex' : 'none';
        }
    } catch (err) {
        console.error('Error fetching cart count:', err);
    }
};

// ===== Password Show/Hide Toggle =====
function togglePassword(inputId, el) {
    const input = document.getElementById(inputId);
    if (!input) return;
    if (input.type === 'password') {
        input.type = 'text';
        el.textContent = '🙈';
    } else {
        input.type = 'password';
        el.textContent = '👁️';
    }
}

// ===== Phone Field Focus: Prompt for username/email if new user =====
function handlePhoneFocus(input) {
    if (input.value === '+91') {
        setTimeout(function() {
            if (confirm('Are you a new user? If yes, please enter your username and email for alerts.')) {
                let username = prompt('Enter your username:');
                let email = prompt('Enter your email:');
                // Optionally, you can auto-fill or handle these values as needed
                // For demo, just alert
                if (username && email) {
                    alert('Username: ' + username + '\nEmail: ' + email);
                }
            }
        }, 200);
    }
}
// ===== Main JavaScript =====

/* Mobile nav uses CSS-only checkbox toggle in base.html */

// ===== Smooth Scrolling =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ===== Flash Message Auto-Dismiss =====
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            message.style.animation = 'slideOutRight 0.3s ease forwards';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
        
        // Manual dismiss on click
        message.addEventListener('click', function() {
            message.style.animation = 'slideOutRight 0.3s ease forwards';
            setTimeout(() => {
                message.remove();
            }, 300);
        });
    });
});

// ===== Form Validation =====
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
            
            // Remove error class on input
            field.addEventListener('input', function() {
                if (this.value.trim()) {
                    this.classList.remove('error');
                }
            });
        } else {
            field.classList.remove('error');
        }
    });
    
    return isValid;
}

// Add form validation to all forms
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
                // Show error message
                const firstError = form.querySelector('.error');
                if (firstError) {
                    firstError.focus();
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    });
});

// ===== Loading States =====
function showLoading(button) {
    const originalText = button.textContent;
    button.disabled = true;
    button.innerHTML = '<span class="spinner"></span> Loading...';
    button.classList.add('loading');
    
    return () => {
        button.disabled = false;
        button.innerHTML = originalText;
        button.classList.remove('loading');
    };
}

// Add loading spinner CSS
const style = document.createElement('style');
style.textContent = `
    .spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid transparent;
        border-top: 2px solid currentColor;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .btn.loading {
        opacity: 0.7;
        cursor: not-allowed;
    }
    
    .form-control.error {
        border-color: var(--lost-color);
        box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
    }
    
    @keyframes slideOutRight {
        to {
            opacity: 0;
            transform: translateX(100px);
        }
    }
    
`;
document.head.appendChild(style);

// ===== API Helper Functions =====
const api = {
    get: async(url) => {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('API GET error:', error);
            throw error;
        }
    },
    
    post: async(url, data) => {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('API POST error:', error);
            throw error;
        }
    },
    
    put: async(url, data) => {
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('API PUT error:', error);
            throw error;
        }
    },
    
    delete: async(url) => {
        try {
            const response = await fetch(url, {
                method: 'DELETE'
            });
            if (!response.ok) throw new Error('Network response was not ok');
            return true;
        } catch (error) {
            console.error('API DELETE error:', error);
            throw error;
        }
    }
};

// ===== Image Preview =====
function setupImagePreview(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    
    if (!input || !preview) return;
    
    input.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.innerHTML = `
                    <img src="${e.target.result}" alt="Preview" style="max-width: 100%; max-height: 300px; border-radius: 0.5rem;">
                    <button type="button" onclick="clearImagePreview('${inputId}', '${previewId}')" 
                            style="position: absolute; top: 10px; right: 10px; background: var(--lost-color); 
                                   color: white; border: none; border-radius: 50%; width: 30px; height: 30px; 
                                   cursor: pointer; font-size: 16px;">×</button>
                `;
                preview.style.display = 'block';
                preview.style.position = 'relative';
            };
            reader.readAsDataURL(file);
        }
    });
}

function clearImagePreview(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    
    if (input) input.value = '';
    if (preview) {
        preview.style.display = 'none';
        preview.innerHTML = '';
    }
}

// ===== Search and Filter =====
function setupSearch(searchInputId, resultsContainerId, searchUrl) {
    const searchInput = document.getElementById(searchInputId);
    const resultsContainer = document.getElementById(resultsContainerId);
    
    if (!searchInput || !resultsContainer) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            resultsContainer.innerHTML = '';
            return;
        }
        
        searchTimeout = setTimeout(async () => {
            try {
                const results = await api.get(`${searchUrl}?q=${encodeURIComponent(query)}`);
                displaySearchResults(results, resultsContainer);
            } catch (error) {
                console.error('Search error:', error);
                resultsContainer.innerHTML = '<p class="text-error">Search failed. Please try again.</p>';
            }
        }, 300);
    });
}

function displaySearchResults(results, container) {
    if (!results || results.length === 0) {
        container.innerHTML = '<p class="text-muted">No results found.</p>';
        return;
    }
    
    const html = results.map(item => `
        <div class="search-result" onclick="window.location.href='/item/${item.item_id}'">
            <div class="search-result-image">
                ${item.image ? `<img src="/static/uploads/${item.image}" alt="${item.title}">` : '<div class="photo-placeholder">No Photo Available</div>'}
            </div>
            <div class="search-result-content">
                <h4>${item.title}</h4>
                <p class="search-result-meta">
                    <span class="category-badge ${item.category}">${item.category}</span>
                    <span class="status-pill ${item.status}">${item.status}</span>
                </p>
                <p class="search-result-location">${item.location}</p>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// ===== Infinite Scroll =====
function setupInfiniteScroll(containerId, loadMoreUrl, loadingIndicatorId) {
    const container = document.getElementById(containerId);
    const loadingIndicator = document.getElementById(loadingIndicatorId);
    
    if (!container) return;
    
    let page = 1;
    let loading = false;
    let hasMore = true;
    
    async function loadMore() {
        if (loading || !hasMore) return;
        
        loading = true;
        if (loadingIndicator) loadingIndicator.style.display = 'block';
        
        try {
            const newItems = await api.get(`${loadMoreUrl}?page=${page + 1}`);
            
            if (newItems && newItems.length > 0) {
                appendItems(newItems, container);
                page++;
            } else {
                hasMore = false;
            }
        } catch (error) {
            console.error('Load more error:', error);
        } finally {
            loading = false;
            if (loadingIndicator) loadingIndicator.style.display = 'none';
        }
    }
    
    function appendItems(items, container) {
        items.forEach(item => {
            const itemElement = createItemElement(item);
            container.appendChild(itemElement);
        });
    }
    
    function createItemElement(item) {
        const div = document.createElement('div');
        div.className = 'item-card';
        div.innerHTML = `
            <div class="item-image">
                ${item.image ? `<img src="/static/uploads/${item.image}" alt="${item.title}">` : '<div class="photo-placeholder">No Photo Available</div>'}
            </div>
            <div class="item-content">
                <h3>${item.title}</h3>
                <div class="item-meta">
                    <span class="category-badge ${item.category}">${item.category}</span>
                    <span class="status-pill ${item.status}">${item.status}</span>
                </div>
                <p class="item-description">${item.description ? item.description.substring(0, 100) + '...' : ''}</p>
                <div class="item-details">
                    <p class="location">${item.location}</p>
                    <p class="date">${new Date(item.date_reported).toLocaleDateString()}</p>
                </div>
            </div>
        `;
        div.onclick = () => window.location.href = `/item/${item.item_id}`;
        return div;
    }
    
    // Setup scroll listener
    window.addEventListener('scroll', () => {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
            loadMore();
        }
    });
}

// ===== Notification System =====
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span class="notification-message">${message}</span>
        <button class="notification-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    // Add styles
    const notificationStyle = document.createElement('style');
    notificationStyle.textContent = `
        .notification {
            position: fixed;
            top: 100px;
            right: 20px;
            max-width: 400px;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            backdrop-filter: var(--blur-sm);
            animation: slideInRight 0.3s ease;
            z-index: 1001;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }
        
        .notification-success {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid var(--found-color);
            color: var(--found-color);
        }
        
        .notification-error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid var(--lost-color);
            color: var(--lost-color);
        }
        
        .notification-info {
            background: rgba(124, 58, 237, 0.1);
            border: 1px solid var(--accent-primary);
            color: var(--accent-primary);
        }
        
        .notification-close {
            background: none;
            border: none;
            color: inherit;
            font-size: 1.25rem;
            cursor: pointer;
            padding: 0.25rem;
            border-radius: 0.25rem;
            transition: background 0.2s ease;
        }
        
        .notification-close:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        .notification-message {
            flex: 1;
        }
    `;
    
    if (!document.querySelector('style[data-notifications]')) {
        notificationStyle.setAttribute('data-notifications', '');
        document.head.appendChild(notificationStyle);
    }
    
    document.body.appendChild(notification);
    
    // Auto-dismiss
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease forwards';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// ===== Theme Toggle (Bonus Feature) =====
function setupThemeToggle() {
    const toggle = document.getElementById('themeToggle');
    if (!toggle) return;
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);
    
    toggle.addEventListener('click', function() {
        const currentTheme = document.body.getAttribute('data-theme') || 'dark';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);
    });
}

function applyTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    
    const toggle = document.getElementById('themeToggle');
    if (toggle) {
        toggle.textContent = theme === 'dark' ? 'Dark' : 'Light';
    }
    
    // Update CSS variables for light theme
    if (theme === 'light') {
        document.documentElement.style.setProperty('--bg-primary', '#f8fafc');
        document.documentElement.style.setProperty('--bg-secondary', '#e2e8f0');
        document.documentElement.style.setProperty('--text-primary', '#1e293b');
        document.documentElement.style.setProperty('--text-secondary', '#64748b');
        document.documentElement.style.setProperty('--text-muted', '#94a3b8');
        document.documentElement.style.setProperty('--border-color', 'rgba(0, 0, 0, 0.1)');
    } else {
        // Reset to default dark theme
        document.documentElement.style.removeProperty('--bg-primary');
        document.documentElement.style.removeProperty('--bg-secondary');
        document.documentElement.style.removeProperty('--text-primary');
        document.documentElement.style.removeProperty('--text-secondary');
        document.documentElement.style.removeProperty('--text-muted');
        document.documentElement.style.removeProperty('--border-color');
    }
}

// ===== Initialize on DOM Load =====
document.addEventListener('DOMContentLoaded', function() {
    // Setup theme toggle if exists
    setupThemeToggle();
    
    // Setup image previews
    setupImagePreview('image', 'imagePreview');
    
    // Add smooth reveal animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.item-card, .stat-card, .dashboard-section, .admin-section').forEach(el => {
        el.style.opacity = '0';
        observer.observe(el);
    });
});

// ===== Notification System =====
function toggleNotifications() {
    const dropdown = document.getElementById('notificationDropdown');
    const isVisible = dropdown.classList.contains('show');
    
    if (!isVisible) {
        loadNotifications();
        dropdown.classList.add('show');
    } else {
        dropdown.classList.remove('show');
    }
}

function loadNotifications() {
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            const notificationList = document.getElementById('notificationList');
            notificationList.innerHTML = '';
            
            if (data.notifications.length === 0) {
                notificationList.innerHTML = '<div class="notification-item"><p class="notification-message">No notifications</p></div>';
            } else {
                data.notifications.forEach(notif => {
                    const notifElement = createNotificationElement(notif);
                    notificationList.appendChild(notifElement);
                });
            }
        })
        .catch(error => console.error('Error loading notifications:', error));
}

function createNotificationElement(notification) {
    const div = document.createElement('div');
    div.className = `notification-item ${!notification.is_read ? 'unread' : ''}`;
    div.onclick = () => markAsRead(notification.notif_id);
    
    const timeAgo = getTimeAgo(new Date(notification.created_at));
    
    div.innerHTML = `
        <div class="notification-message">${notification.message}</div>
        <div class="notification-time">${timeAgo}</div>
    `;
    
    return div;
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + " years ago";
    
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + " months ago";
    
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + " days ago";
    
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + " hours ago";
    
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + " minutes ago";
    
    return "Just now";
}

function markAsRead(notificationId) {
    fetch('/api/notifications/read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notification_id: notificationId })
    })
    .then(response => response.json())
    .then(data => {
        // Update notification count
        updateNotificationCount(data.unread_count);
        
        // Reload notifications
        loadNotifications();
    })
    .catch(error => console.error('Error marking notification as read:', error));
}

function markAllRead() {
    fetch('/api/notifications/mark-all-read', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        // Update notification count
        updateNotificationCount(0);
        
        // Reload notifications
        loadNotifications();
    })
    .catch(error => console.error('Error marking all notifications as read:', error));
}

function updateNotificationCount(count) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    }
}

// Close notification dropdown when clicking outside
document.addEventListener('click', function(event) {
    const notificationWrapper = document.querySelector('.notification-wrapper');
    const dropdown = document.getElementById('notificationDropdown');
    
    if (notificationWrapper && !notificationWrapper.contains(event.target)) {
        dropdown.classList.remove('show');
    }
});

// ===== Utility Functions =====
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Export for use in other scripts
window.CampusFind = {
    api,
    showNotification,
    setupImagePreview,
    setupSearch,
    setupInfiniteScroll,
    showLoading,
    validateForm,
    debounce,
    formatFileSize,
    formatDate,
    truncateText
};

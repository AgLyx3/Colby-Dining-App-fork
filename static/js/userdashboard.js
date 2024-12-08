class DiningHallWaitTimes {
    constructor() {
        this.container = document.getElementById('wait-times-container');
        this.lastUpdatedElement = document.getElementById('last-updated');
        this.updateInterval = 5 * 60 * 1000; // 5 minutes
        this.retryDelay = 30000; // 30 seconds
        this.maxRetries = 3;
        this.currentRetries = 0;
    }

    init() {
        this.updateWaitTimes();
        setInterval(() => this.updateWaitTimes(), this.updateInterval);
    }

    async updateWaitTimes() {
        try {
            const response = await fetch('/api/wait-times');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            if (data.status === 'success') {
                this.currentRetries = 0; // Reset retry counter on success
                this.updateDisplay(data);
            } else {
                this.handleError('Server error', data.message);
            }
        } catch (error) {
            this.handleError('Connection error', error.message);
        }
    }

    updateDisplay(data) {
        if (!this.container || !this.lastUpdatedElement) {
            console.error('Required DOM elements not found');
            return;
        }

        // Update timestamp
        this.lastUpdatedElement.textContent = 
            `Last updated: ${new Date(data.timestamp).toLocaleTimeString()}`;

        // Clear and update container
        this.container.innerHTML = '';

        // Process each dining hall
        Object.entries(data.predictions).forEach(([location, info]) => {
            this.container.appendChild(
                this.createDiningHallElement(location, info)
            );
        });
    }

    createDiningHallElement(location, info) {
        const element = document.createElement('div');
        element.className = 'border p-2 flex-fill text-center';

        if (info.status === 'success') {
            const statusColor = this.getStatusColor(info.wait_time);
            element.innerHTML = this.getSuccessTemplate(location, info, statusColor);
        } else {
            element.innerHTML = this.getErrorTemplate(location);
        }

        return element;
    }

    getStatusColor(waitTime) {
        if (waitTime <= 10) return 'success';     // Green for short waits
        if (waitTime <= 20) return 'warning';     // Yellow for medium waits
        return 'danger';                          // Red for long waits
    }


    getSuccessTemplate(location, info, statusColor) {
        return `
            <span class="d-block fw-bold">${location}</span>
            <div class="mb-2">
                <span class="badge bg-${statusColor} mb-2">
                    ${info.wait_time} min wait
                </span>
               
            </div>
        `;
    }

    getErrorTemplate(location) {
        return `
            <span class="d-block fw-bold">${location}</span>
            <small class="text-danger">Temporarily unavailable</small>
        `;
    }

    handleError(type, message) {
        console.error(`${type}:`, message);
        
        if (this.currentRetries < this.maxRetries) {
            this.currentRetries++;
            console.log(`Retrying in ${this.retryDelay/1000} seconds... (Attempt ${this.currentRetries}/${this.maxRetries})`);
            setTimeout(() => this.updateWaitTimes(), this.retryDelay);
        } else {
            this.showError('Service temporarily unavailable');
        }
    }

    showError(message) {
        if (this.container) {
            this.container.innerHTML = `
                <div class="alert alert-warning w-100 text-center" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                    <br>
                    <small class="text-muted">Please try again later</small>
                </div>
            `;
        }
    }

    // Helper method to format date/time consistently
    formatDateTime(date) {
        return new Date(date).toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const waitTimes = new DiningHallWaitTimes();
    waitTimes.init();
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.message);
    return false;
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    return false;
});

class FavoritesManager {
    constructor() {
        this.container = document.getElementById('favorites-container');
        this.init();
    }

    async init() {
        await this.loadFavorites();
    }

    async loadFavorites() {
        try {
            const response = await fetch('/api/favorites');
            const data = await response.json();

            if (data.status === 'success') {
                this.displayFavorites(data.favorites);
            } else {
                this.showError('Failed to load favorites');
            }
        } catch (error) {
            console.error('Error loading favorites:', error);
            this.showError('Unable to load favorites');
        }
    }

    displayFavorites(favorites) {
        if (!this.container) return;

        if (!favorites.length) {
            this.container.innerHTML = `
                <div class="col-12">
                    <div class="text-center text-muted p-4">
                        <i class="fas fa-heart mb-3" style="font-size: 2rem;"></i>
                        <p>No favorite dishes yet. Add some from the menu!</p>
                        <a href="/menu" class="btn btn-primary">Browse Menu</a>
                    </div>
                </div>
            `;
            return;
        }

        this.container.innerHTML = favorites.map(favorite => `
            <div class="col-md-4">
                <div class="card h-100 border-0 shadow-sm">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <h6 class="card-title mb-3">${favorite.dish_name}</h6>
                            <button class="btn btn-link text-danger remove-favorite" 
                                data-dish="${favorite.dish_name}">
                                <i class="fas fa-heart"></i>
                            </button>
                        </div>

                    </div>
                </div>
            </div>
        `).join('');

        // Add event listeners for remove buttons
        this.container.querySelectorAll('.remove-favorite').forEach(button => {
            button.addEventListener('click', async (e) => {
                const dishName = e.currentTarget.dataset.dish;
                await this.removeFavorite(dishName);
            });
        });
    }

    async removeFavorite(dishName) {
        try {
            const response = await fetch('/api/favorites', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ dish_name: dishName })
            });

            const data = await response.json();
            if (data.status === 'success') {
                // Reload favorites to update the display
                await this.loadFavorites();
                this.showToast('Success', 'Dish removed from favorites');
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Error removing favorite:', error);
            this.showToast('Error', 'Failed to remove favorite');
        }
    }

    showError(message) {
        if (this.container) {
            this.container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-warning text-center" role="alert">
                        ${message}
                    </div>
                </div>
            `;
        }
    }

    showToast(title, message) {
        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.classList.add('toast-container', 'position-fixed', 'bottom-0', 'end-0', 'p-3');
            document.body.appendChild(toastContainer);
        }

        const toastElement = document.createElement('div');
        toastElement.classList.add('toast');
        toastElement.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${message}</div>
        `;

        toastContainer.appendChild(toastElement);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();

        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const waitTimes = new DiningHallWaitTimes();
    waitTimes.init();

    const favorites = new FavoritesManager();
    // favorites is already initialized in its constructor
});

// Add current time display
function updateCurrentTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const now = new Date();
        const options = {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        };
        timeElement.textContent = now.toLocaleTimeString('en-US', options);
    }
}

setInterval(updateCurrentTime, 1000);

// Add hover effect to wait time cards
document.querySelectorAll('.wait-time-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-5px)';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
    });
});

// Add this to userdashboard.js
document.addEventListener('DOMContentLoaded', function() {
    // Find the feedback button
    const feedbackBtn = document.querySelector('[data-feedback-btn]');
    
    if (feedbackBtn) {
        // Fetch active survey link when page loads
        fetch('/api/active-survey')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update the button's href with the survey URL
                    feedbackBtn.href = data.survey.url;
                    feedbackBtn.target = "_blank"; // Open in new tab
                    feedbackBtn.setAttribute('title', data.survey.title);
                } else {
                    // If no active survey, disable the button and show message
                    feedbackBtn.classList.add('disabled');
                    feedbackBtn.setAttribute('title', 'No active survey available');
                }
            })
            .catch(error => {
                console.error('Error fetching survey link:', error);
                feedbackBtn.classList.add('disabled');
                feedbackBtn.setAttribute('title', 'Error loading survey link');
            });
    }
});
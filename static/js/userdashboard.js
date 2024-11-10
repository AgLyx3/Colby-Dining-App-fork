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
            <div>
                <a href="/menu?location=${encodeURIComponent(location)}" class="btn btn-primary py-2 px-2">View Menu</a>
            </div>
        `;
    }

    getErrorTemplate(location) {
        return `
            <span class="d-block fw-bold">${location}</span>
            <small class="text-danger">Temporarily unavailable</small>
            <div class="mt-2">
                <a href="/menu?location=${encodeURIComponent(location)}" class="btn btn-primary py-2 px-2">View Menu</a>
            </div>
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
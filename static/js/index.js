function updateWaitTimes() {
    fetch('/api/wait-times')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const waitTimesContainer = document.querySelector('.wait-times-container');
                if (!waitTimesContainer) return;

                // Clear existing content
                waitTimesContainer.innerHTML = '';

                // Add each dining hall's wait time
                Object.entries(data.predictions).forEach(([location, prediction]) => {
                    const status = prediction.status;
                    let waitTimeHtml = '';
                    
                    if (status === 'success') {
                        // Determine status class based on wait time
                        let statusClass = 'status-low';
                        let statusText = 'Low Traffic';
                        
                        if (prediction.wait_time > 15) {
                            statusClass = 'status-high';
                            statusText = 'High Traffic';
                        } else if (prediction.wait_time > 8) {
                            statusClass = 'status-medium';
                            statusText = 'Moderate Traffic';
                        }
                        
                        // ${Math.round(prediction.wait_time)} min
                        waitTimeHtml = `
                            <div class="wait-time-card">
                                <div class="location-name">${location}</div>
                                <div class="wait-time ${statusClass}">
                                    ${prediction.wait_time} min
                                </div>
                                <div class="mt-3 text-muted">
                                    Approximate crowd: ~${prediction.crowd} people
                                </div>
                            </div>`;
                    } else if (status === 'closed') {
                        waitTimeHtml = `
                            <div class="wait-time-card">
                                <div class="location-name">${location}</div>
                                <div class="wait-time text-muted">Closed</div>
                                <div class="traffic-indicator text-muted">
                                    Currently not operating
                                </div>
                            </div>`;
                    } else {
                        waitTimeHtml = `
                            <div class="wait-time-card">
                                <div class="location-name">${location}</div>
                                <div class="wait-time text-muted">--</div>
                                <div class="traffic-indicator text-warning">
                                    Temporarily unavailable
                                </div>
                            </div>`;
                    }
                    
                    waitTimesContainer.innerHTML += waitTimeHtml;
                });

                // Update last refreshed time
                const lastUpdated = document.querySelector('.wait-times-updated');
                if (lastUpdated) {
                    const timestamp = new Date(data.timestamp);
                    lastUpdated.textContent = `Last updated: ${timestamp.toLocaleTimeString()}`;
                }
            }
        })
        .catch(error => {
            console.error('Error fetching wait times:', error);
            const waitTimesContainer = document.querySelector('.wait-times-container');
            if (waitTimesContainer) {
                waitTimesContainer.innerHTML = `
                    <div class="alert alert-warning text-center w-100" role="alert">
                        Unable to load wait times. Please try again later.
                    </div>`;
            }
        });
}

// Update wait times initially and every 30 seconds
document.addEventListener('DOMContentLoaded', () => {
    updateWaitTimes();
    setInterval(updateWaitTimes, 30000);
});

document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.getElementById('contactForm');
    const submitButton = document.getElementById('submitButton');
    const formMessage = document.getElementById('formMessage');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Disable submit button and show loading state
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending...';
            
            // Get form data
            const formData = new FormData(contactForm);
            
            // Submit form
            fetch('/submit_feedback', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Show success/error message
                formMessage.style.display = 'block';
                formMessage.className = data.success ? 
                    'alert alert-success mt-3' : 'alert alert-danger mt-3';
                formMessage.textContent = data.message;
                
                // Reset form on success
                if (data.success) {
                    contactForm.reset();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                formMessage.style.display = 'block';
                formMessage.className = 'alert alert-danger mt-3';
                formMessage.textContent = 'An error occurred. Please try again later.';
            })
            .finally(() => {
                // Re-enable submit button
                submitButton.disabled = false;
                submitButton.innerHTML = 'Submit';
                
                // Hide message after 5 seconds
                setTimeout(() => {
                    formMessage.style.display = 'none';
                }, 5000);
            });
        });
    }
});
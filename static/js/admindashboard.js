// Color scheme for the dining halls
const colors = {
    Dana: '#2c7be5',     // Professional blue
    Roberts: '#27ae60',  // Nature green
    Foss: '#e74c3c'      // Warm red
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    
    setInterval(initializeDashboard, 1000);
});

function initializeDashboard() {

    // Fetch feedback questions
    fetch('/api/admin/feedback-questions')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateFeedbackQuestions(data.questions);
            } else {
                showToast('Error', data.message || 'Failed to load questions', 'error');
            }
        })
        .catch(error => {
            console.error('Error fetching feedback questions:', error);
            showToast('Error', 'Failed to load feedback questions', 'error');
        });
}

function updateFeedbackQuestions(questions) {
    const feedbackList = document.getElementById('feedbackList');
    feedbackList.innerHTML = ''; // Clear existing content

    const pastFeedbackList = document.querySelector('#pastFeedback .list-group');
    pastFeedbackList.innerHTML = '';

    if (questions.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.classList.add('text-center', 'p-4', 'text-muted');
        emptyState.textContent = 'No feedback questions available';
        feedbackList.appendChild(emptyState);
        return;
    }

    questions.forEach(question => {
        const questionItem = document.createElement('div');
        questionItem.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-start', 'p-3');

        const questionContent = document.createElement('div');
        questionContent.classList.add('me-auto');

        const questionText = document.createElement('div');
        questionText.classList.add('mb-1');
        questionText.textContent = question.question_text;

        const questionMeta = document.createElement('small');
        questionMeta.classList.add('text-muted');
        questionMeta.innerHTML = `
            <span class="badge bg-secondary me-2">${question.question_type}</span>
            Active: ${new Date(question.active_start_date).toLocaleDateString()} - 
            ${new Date(question.active_end_date).toLocaleDateString()}
        `;

        questionContent.appendChild(questionText);
        questionContent.appendChild(questionMeta);

        const actionButtons = document.createElement('div');
        actionButtons.classList.add('btn-group', 'btn-group-sm');

        // Only create the Edit button if the question is active
        if (question.is_active) {
            const editButton = document.createElement('button');
            editButton.classList.add('btn', 'btn-outline-primary');
            editButton.innerHTML = '<i class="fas fa-edit"></i>';
            editButton.title = 'Edit Question';
            actionButtons.appendChild(editButton);
            
            // Add event listener for edit
            editButton.addEventListener('click', () => editQuestion(question));
        } else {
            const reactivateButton = document.createElement('button');
            reactivateButton.classList.add('btn', 'btn-outline-success');
            reactivateButton.innerHTML = '<i class="fas fa-sync-alt"></i>'; 
            reactivateButton.title = 'Reactivate Question'
            actionButtons.appendChild(reactivateButton)
            reactivateButton.onclick = () => reactivateQuestion(question.id);
        }

        const deleteButton = document.createElement('button');
        deleteButton.classList.add('btn', 'btn-outline-danger');
        
        
        // Check if the question is active
        if (question.is_active) {
            deleteButton.innerHTML = '<i class="fas fa-ban"></i>';  
            deleteButton.title = 'Deactivate Question';
            deleteButton.onclick = () => deactivateQuestion(question.id);
        } else {    
            deleteButton.innerHTML = '<i class="fas fa-trash"></i>';          
            deleteButton.title = 'Delete Question';
            deleteButton.onclick = () => deleteQuestion(question.id);
        }
        

        const viewResponsesButton = document.createElement('button');
        viewResponsesButton.classList.add('btn', 'btn-outline-info');
        viewResponsesButton.innerHTML = '<i class="fas fa-chart-pie"></i>';
        viewResponsesButton.title = 'View Responses';

        actionButtons.appendChild(deleteButton);
        actionButtons.appendChild(viewResponsesButton)

        questionItem.appendChild(questionContent);
        questionItem.appendChild(actionButtons);
        
        if (question.is_active) {
            feedbackList.appendChild(questionItem); // Append to active feedback
        } else {
            questionItem.classList.add('inactive');
            pastFeedbackList.appendChild(questionItem); // Append to past feedback
        }

        
        // Add event listener for view response
        viewResponsesButton.addEventListener('click', () => loadResponses(question.id, question.question_type));
    });
        
}

// Deactivate question
function deactivateQuestion(questionId) {
    if (!confirm('Are you sure you want to deactivate this question?')) {
        return;
    }

    console.log('Deactivating question:', questionId); // Debug log

    fetch(`/admin/feedback-question/${questionId}/deactivate`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            showToast('Success', 'Question deactivated successfully', 'success');
            initializeDashboard(); // Refresh the questions list
        } else {
            throw new Error(data.message || 'Failed to deactivate question');
        }
    })
    .catch(error => {
        console.error('Error deactivating question:', error);
        showToast('Error', 'Failed to deactivate question: ' + error.message, 'error');
    });
}

// Delete question
function deleteQuestion(questionId) {
    if (!confirm('Are you sure you want to permanently delete this question?')) {
        return;
    }

    console.log('Deleting question:', questionId); // Debug log

    fetch(`/admin/feedback-question/${questionId}/delete`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            showToast('Success', 'Question deleted successfully', 'success');
            initializeDashboard(); // Refresh the questions list
        } else {
            throw new Error(data.message || 'Failed to delete question');
        }
    })
    .catch(error => {
        console.error('Error deleting question:', error);
        showToast('Error', 'Failed to delete question: ' + error.message, 'error');
    });
}

// Function to reactivate a question
function reactivateQuestion(questionId) {
    fetch(`/admin/feedback-question/${questionId}`)
        .then(response => response.json())
        .then(data => {
            const question = data.question;
            
            // Check if the question is valid and has an active_end_date
            if (!question || !question.active_end_date) {
                alert('Question data is not available or incomplete.');
                return;
            }

            // Get today's date and the active_end_date from the response
            const today = new Date();
            const endDate = new Date(question.active_end_date);

            // Check if the active_end_date is beyond today
            if (endDate <= today) {
                alert("The active period for this question has ended, and it cannot be reactivated.");
                return;
            }

            // Show confirmation to the user
            if (!confirm('Are you sure you want to reactivate this question?')) {
                return;
            }

            console.log('Reactivating question:', questionId);  // Debug log

            // Send a PUT request to the backend to reactivate the question
            fetch(`/admin/feedback-question/${questionId}/reactivate`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                console.log('Reactivate response data:', data);  // Debug log
                if (data.status === 'success') {
                    showToast('Success', 'Question reactivated successfully', 'success');
                    initializeDashboard();  // Refresh the question list
                } else {
                    throw new Error(data.message || 'Failed to reactivate question');
                }
            })
            .catch(error => {
                console.error('Error reactivating question:', error);
                showToast('Error', 'Failed to reactivate question: ' + error.message, 'error');
            });
        })
        .catch(error => {
            console.error('Error fetching question data:', error);
            showToast('Error', 'Failed to fetch question data: ' + error.message, 'error');
        });
}



function editQuestion(question) {
    // Placeholder for edit functionality
    console.log('Edit question:', question);
    showToast('Info', 'Edit functionality coming soon', 'info');
}

function setupEventListeners() {
    const submitQuestionBtn = document.getElementById('submitQuestion');
    const feedbackModal = document.getElementById('feedbackModal');
    
    submitQuestionBtn.addEventListener('click', () => {
        const form = document.getElementById('feedbackForm');
        const formData = new FormData(form);

        // Basic form validation
        const questionText = formData.get('questionText');
        const startDate = formData.get('activeStartDate');
        const endDate = formData.get('activeEndDate');

        if (!questionText || !startDate || !endDate) {
            showToast('Error', 'Please fill in all required fields', 'error');
            return;
        }

        submitQuestionBtn.disabled = true;
        
        fetch('/admin/feedback-question', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showToast('Success', 'Question added successfully', 'success');
                bootstrap.Modal.getInstance(feedbackModal).hide();
                initializeDashboard();
                form.reset();
            } else {
                showToast('Error', data.message || 'Failed to add question', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error', 'Failed to add question', 'error');
        })
        .finally(() => {
            submitQuestionBtn.disabled = false;
        });
    });

    // Reset form when modal is closed
    feedbackModal.addEventListener('hidden.bs.modal', function () {
        document.getElementById('feedbackForm').reset();
    });
}

let chartInstance;

function loadResponses(questionId, questionType) {
    console.log('loadResponses function triggered');

    // Show the modal immediately
    const responsesModal = new bootstrap.Modal(document.getElementById('responsesModal'));
    responsesModal.show();

    // Set a placeholder or loading message in the modal
    const questionText = document.getElementById('responseQuestionText');
    const responseList = document.getElementById('responseList');
    const responseChart = document.getElementById('responseChart');

    questionText.textContent = 'Loading responses...'; // Placeholder text
    responseList.style.display = 'none';
    responseChart.style.display = 'none';

    // Create a URL to fetch responses based on the question ID
    const url = `/admin/feedback-question/get-response/${questionId}`;
    console.log(`Making GET request to: ${url}`);  // Log the URL being called

    // Prepare query parameters (question_type will be included in the URL itself)
    const params = new URLSearchParams({ question_type: questionType });

    // Append query parameters to the URL
    const finalUrl = `${url}?${params.toString()}`;

    // Fetch responses from the server
    fetch(finalUrl, {
        method: 'GET', // This is a GET request
    })
    .then(response => response.json())
    .then(data => {
        // Handle the data returned by the server
        if (data.question) {
            questionText.textContent = data.question; // Set the actual question text

            if (questionType === 'yes-no' || questionType === 'rating') {
                // Handle Yes/No or Rating question type and display Pie Chart
                responseList.style.display = 'none';
                responseChart.style.display = 'block';

                const chartData = processChartData(data.responses, questionType);
                console.log('Chart data:', chartData); // Debugging response data

                // Destroy previous chart if exists
                if (chartInstance) {
                    chartInstance.destroy();
                }

                // Create the Pie Chart using Chart.js
                const ctx = responseChart.getContext('2d');
                if (ctx) {
                    console.log('Chart context retrieved:', ctx);  // Ensure canvas context is retrieved
                    chartInstance = new Chart(ctx, {
                        type: 'pie',
                        data: chartData,
                    });
                } else {
                    console.error('Failed to retrieve canvas context.');
                }
            } else if (questionType === 'text') {
                // Handle Text question type and display as a list
                responseList.style.display = 'block';
                responseChart.style.display = 'none'; // Ensure chart is hidden

                // Populate the list with responses
                responseList.innerHTML = ''; // Clear any existing list items
                data.responses.forEach(response => {
                    const li = document.createElement('li');
                    li.classList.add('list-group-item');
                    li.textContent = response;
                    responseList.appendChild(li);
                });
            }
        } else {
            console.error('Failed to load responses:', data.error || 'Unknown error');
            questionText.textContent = 'Failed to load responses. Please try again.';
        }
    })
    .catch(error => {
        console.error('Error loading responses:', error);
        questionText.textContent = 'An error occurred while loading responses.';
    });
}

function processChartData(responses, questionType) {
    let chartData = {
        labels: [],
        datasets: [{
            data: [],
            backgroundColor: ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0'], // Example colors
            hoverBackgroundColor: ['#ff6666', '#3399ff', '#66ff66', '#ff9933', '#9999ff']
        }]
    };

    console.log('Processing chart data for:', questionType); // Debugging chart processing

    if (questionType === 'yes-no') {
        chartData.labels = ['Yes', 'No'];
        chartData.datasets[0].data = [
            responses['yes'] || 0,
            responses['no'] || 0
        ];
    } else if (questionType === 'rating') {
        chartData.labels = ['1', '2', '3', '4', '5'];
        chartData.datasets[0].data = [
            responses['1'] || 0,
            responses['2'] || 0,
            responses['3'] || 0,
            responses['4'] || 0,
            responses['5'] || 0
        ];
    }

    return chartData;
}

function showToast(title, message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.classList.add('toast-container', 'position-fixed', 'bottom-0', 'end-0', 'p-3');
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toastElement = document.createElement('div');
    toastElement.classList.add('toast');
    toastElement.classList.add(`bg-${type === 'error' ? 'danger' : type}`);
    toastElement.classList.add('text-white');
    
    toastElement.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">${title}</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;

    toastContainer.appendChild(toastElement);

    // Initialize and show toast
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 3000
    });
    toast.show();

    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Add this after your existing initialization code
document.getElementById('submitSurveyLink')?.addEventListener('click', function() {
    const form = document.getElementById('surveyLinkForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    const formData = new FormData(form);
    const submitButton = this;
    submitButton.disabled = true;

    fetch('/admin/survey-link', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('Success', 'Survey link added successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('surveyLinkModal')).hide();
            form.reset();
            // Optionally refresh the feedback list to show the new survey link
            initializeDashboard();
        } else {
            throw new Error(data.message || 'Failed to add survey link');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error', error.message, 'error');
    })
    .finally(() => {
        submitButton.disabled = false;
    });
});

function deleteSurveyLink(id) {
    if (!confirm('Are you sure you want to delete this survey link?')) return;

    fetch(`/admin/survey-link/${id}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('Success', 'Survey link deleted successfully', 'success');
            initializeDashboard();
        } else {
            throw new Error(data.message || 'Failed to delete survey link');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error', error.message, 'error');
    });
}
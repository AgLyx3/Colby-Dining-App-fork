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
    // Fetch wait times data
    fetch('/api/wait-times')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateWaitingTimes(data.predictions);
                updateLastRefreshed();
            }
        })
        .catch(error => {
            console.error('Error fetching wait times:', error);
            showToast('Error', 'Failed to load wait times', 'error');
        });

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

function updateLastRefreshed() {
    const now = new Date();
    document.getElementById('last-updated').textContent = 
        `Last updated: ${now.toLocaleTimeString()}`;
}

function updateWaitingTimes(predictions) {
    Object.entries(predictions).forEach(([location, data]) => {
        const element = document.querySelector(`.waiting-time[data-location="${location}"]`);
        if (element) {
            if (data.status === 'success') {
                element.textContent = `${Math.round(data.wait_time)} min`;
                
                // Update status classes
                element.classList.remove('status-low', 'status-medium', 'status-high');
                if (data.wait_time < 5) element.classList.add('status-low');
                else if (data.wait_time < 15) element.classList.add('status-medium');
                else element.classList.add('status-high');
            } else {
                element.textContent = data.message || 'N/A';
                element.classList.remove('status-low', 'status-medium', 'status-high');
            }
        }
    });
}

function updateFeedbackQuestions(questions) {
    const feedbackList = document.getElementById('feedbackList');
    feedbackList.innerHTML = ''; // Clear existing content

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

        const editButton = document.createElement('button');
        editButton.classList.add('btn', 'btn-outline-primary');
        editButton.innerHTML = '<i class="fas fa-edit"></i>';
        editButton.title = 'Edit Question';

        const deleteButton = document.createElement('button');
        deleteButton.classList.add('btn', 'btn-outline-danger');
        deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
        deleteButton.title = 'Delete Question';
        deleteButton.onclick = () => deleteQuestion(question.id); // Changed to onclick

        actionButtons.appendChild(editButton);
        actionButtons.appendChild(deleteButton);

        questionItem.appendChild(questionContent);
        questionItem.appendChild(actionButtons);
        feedbackList.appendChild(questionItem);

        // Add event listener for edit
        editButton.addEventListener('click', () => editQuestion(question));
    });
}

function deleteQuestion(questionId) {
    if (!confirm('Are you sure you want to delete this question?')) {
        return;
    }

    console.log('Deleting question:', questionId); // Debug log

    fetch(`/admin/feedback-question/${questionId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('Delete response status:', response.status); // Debug log
        return response.json();
    })
    .then(data => {
        console.log('Delete response data:', data); // Debug log
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

function editQuestion(question) {
    console.log('Editing question:', question);

    // Populate the modal with the existing question data
    const feedbackModal = document.getElementById('feedbackModal');
    const modalTitle = feedbackModal.querySelector('.modal-title');
    const submitBtn = feedbackModal.querySelector('#submitQuestion');

    // Assuming you have input fields for these values in the modal
    document.getElementById('questionText').value = question.question_text;
    document.getElementById('questionType').value = question.question_type;
    document.getElementById('activeStartDate').value = question.active_start_date;
    document.getElementById('activeEndDate').value = question.active_end_date;

    modalTitle.innerHTML = '<i class="fas fa-edit me-2"></i>Edit Feedback Question';
    submitBtn.id = 'editQuestion'; // Change button ID to indicate edit action
    submitBtn.textContent = 'Update';

    // Show the modal
    new bootstrap.Modal(feedbackModal).show();

    // Handle form submission for editing
    submitBtn.addEventListener('click', () => {
        const formData = new FormData(document.getElementById('feedbackForm'));
        formData.append('id', question.id); // Append the question id for the edit operation

        const url = '/admin/feedback-question/update'; // Endpoint for updating a question

        fetch(url, {
            method: 'PUT',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showToast('Success', 'Question updated successfully', 'success');
                bootstrap.Modal.getInstance(feedbackModal).hide(); // Hide modal after successful update
                updateFeedbackQuestions(data.questions); // Update the list of questions
            } else {
                showToast('Error', data.message || 'Update failed', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error', 'Update failed', 'error');
        });
    });
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
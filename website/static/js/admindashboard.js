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

    if (!window.waitTimeChart) {
        window.waitTimeChart = new WaitTimeAnalysis();
        window.waitTimeChart.init();
    }

    if (!window.popularDishesChart) {
        window.popularDishesChart = new PopularDishesChart();
        window.popularDishesChart.init();
    }


    // setInterval(initializeDashboard, 1000);

    const today = new Date();
    today.setDate(today.getDate() + 1);  // Add one day to today's date
        
    const tomorrow = today.toISOString().split('T')[0];

    document.getElementById('activeStartDate').setAttribute('min', today);
    document.getElementById('activeEndDate').setAttribute('min', today);
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

document.getElementById("exportFeedback").addEventListener("click", exportAll);

// function exportAll(){
//     fetch('/api/admin/feedback-questions')
//         .then(response => response.json())
//         .then(data => {
//             if (data.status === 'success') {
//                 const questions = data.questions;
//                 console.log(questions);
//
//                 questions.forEach(question =>{
//                     let question_id = question.id;
//                     let question_type = question.question_type;
//                     // exportResponse(question_id, question_type);
//
//
//
//                 })
//             } else {
//                 showToast('Error', data.message || 'Failed to load questions', 'error');
//             }
//         })
//         .catch(error => {
//             console.error('Error fetching feedback questions:', error);
//             showToast('Error', 'Failed to load feedback questions', 'error');
//         });
// }

function sanitizeFilename(filename) {
    // Remove or replace characters not allowed in filenames
    return filename
        .replace(/[/\\?%*:|"<>]/g, '_')  // Replace forbidden characters with underscore
        .replace(/\s+/g, '_')            // Replace spaces with underscore
        .substring(0, 255)               // Limit filename length
        .trim();                         // Remove leading/trailing whitespace
}

function fetchAndGenerateCSV(questionId, questionType) {
    return fetch(`/admin/feedback-question/get-response/${questionId}?question_type=${questionType}`)
        .then(response => response.json())
        .then(data => {
            if (data.question) {
                // Sanitize the filename
                const sanitizedFilename = sanitizeFilename(`${data.question}_responses.csv`);

                return {
                    filename: sanitizedFilename,
                    content: convertToCSV({
                        "Question ID": questionId,
                        "Question Text": data.question,
                        "Question Type": questionType,
                        "Response": data.responses
                    })
                };
            } else {
                console.error(`Failed to fetch responses for question ${questionId}`);
                return null;
            }
        })
        .catch(error => {
            console.error(`Error fetching responses for question ${questionId}:`, error);
            return null;
        });
}

function exportAll() {
    fetch('/api/admin/feedback-questions')
        .then(response => response.json())
        .then(async data => {
            if (data.status === 'success') {
                const questions = data.questions;

                // Use native File System Access API or fallback to multiple downloads
                if ('showDirectoryPicker' in window) {
                    // Modern browser approach using File System Access API
                    try {
                        const dirHandle = await window.showDirectoryPicker();

                        for (const question of questions) {
                            const csvData = await fetchAndGenerateCSV(question.id, question.question_type);
                            if (csvData) {
                                try {
                                    const fileHandle = await dirHandle.getFileHandle(csvData.filename, { create: true });
                                    const writable = await fileHandle.createWritable();
                                    await writable.write(csvData.content);
                                    await writable.close();
                                } catch (fileError) {
                                    console.error(`Error writing file ${csvData.filename}:`, fileError);
                                    showToast('Error', `Failed to write file for question ${question.id}`, 'error');
                                }
                            }
                        }

                        showToast('Success', 'All responses exported successfully', 'success');
                    } catch (error) {
                        console.error('Export error:', error);
                        showToast('Error', 'Failed to export responses', 'error');
                    }
                } else {
                    // Fallback: Trigger multiple file downloads
                    const promises = questions.map(question =>
                        fetchAndGenerateCSV(question.id, question.question_type)
                    );

                    Promise.all(promises).then(files => {
                        files.forEach(file => {
                            if (file) {
                                const blob = new Blob([file.content], { type: 'text/csv;charset=utf-8;' });
                                const link = document.createElement('a');
                                link.href = URL.createObjectURL(blob);
                                link.download = file.filename;
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                            }
                        });

                        showToast('Success', 'All responses exported successfully', 'success');
                    }).catch(error => {
                        console.error('Export error:', error);
                        showToast('Error', 'Failed to export responses', 'error');
                    });
                }
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

        const ExportButton = document.createElement('button');
        ExportButton.classList.add('btn', 'btn-outline-success');
        ExportButton.innerHTML = '<i class="fas fa-file-export"></i>';
        ExportButton.title = 'Export Question';

        actionButtons.appendChild(deleteButton);
        actionButtons.appendChild(viewResponsesButton);
        actionButtons.appendChild(ExportButton);

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
        // Add even listener for export
        ExportButton.addEventListener('click', () => exportResponse(question.id, question.question_type));
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

function exportResponse(questionId, questionType){
    console.log('exportResponse function triggered');

    // Show the modal immediately
    // const responsesModal = new bootstrap.Modal(document.getElementById('responsesModal'));
    // responsesModal.show();

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

            let csv_content = {"Question ID": questionId, "Question Text": data.question, "Question Type": questionType, "Response":data.responses};
            console.log(csv_content);

            // Convert to CSV
            const csvContent = convertToCSV(csv_content);

            // Create a Blob from the CSV content
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });

            // Create a link to trigger the download
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `${data.question}_responses.csv`; // Filename to download as

            // Append the link to the document body, trigger the download, then remove the link
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // Show success toast or message
            showToast('Success', 'Question responses exported successfully', 'success');
        }
        else {
            console.error('Failed to load responses:', data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error loading responses:', error);
        showToast('Error', 'Failed to load responses: ' + error.message, 'error');
    });
}
function convertToCSV(data) {
    function escapeCSV(value) {
        if (value == null) return '';
        const stringValue = String(value);
        const escapedValue = stringValue.replace(/"/g, '""');
        return escapedValue.includes(',') ? `"${escapedValue}"` : escapedValue;
    }

    const csvRows = [];
    csvRows.push(['Question ID', 'Question Text', 'Question Type'].map(escapeCSV).join(','));
    csvRows.push([
        data['Question ID'] || 'N/A',
        data['Question Text'] || 'N/A',
        data['Question Type'] || 'N/A'
    ].join(','));

    // Check if the question type is 'rating' and handle the responses accordingly
    if (data['Question Type'] === 'rating') {
        csvRows.push(['Rating', 'Count'].map(escapeCSV).join(','));

        // Iterate over the response data, which is an object of ratings and counts
        for (let i = 1; i <= 5; i++) {
            csvRows.push(`${i},${data['Response'][i] || 0}`);
        }
    }
    else if(data['Question Type'] === 'text'){
        csvRows.push(['Count', 'Response'].map(escapeCSV).join(','));
        let index = 0;

        for (let i=0; i <= data['Response'].length-1; i++){
            index = i;
            csvRows.push(`${index}, ${data['Response'][i] ||''} `);
        }

    }
    else if(data['Question Type'] === 'yes-no'){
        csvRows.push(['Response', 'Count'].map(escapeCSV).join(','));

        csvRows.push(`Yes, ${data['Response']['yes'] || 0}`);
        csvRows.push(`No, ${data['Response']['no'] || 0}`);

    }
    else {
        csvRows.push(['Unsupported question type']);
    }

    return csvRows.join('\n');
}

// Wait Time Analysis Chart
class WaitTimeAnalysis {
    constructor() {
        this.chart = null;
        this.timeRange = 'today';
        this.chartContainer = document.querySelector('.chart-container');
        this.initialized = false;
    }

    init() {
        if (!this.chartContainer || this.initialized) return;

        this.initialized = true;
        this.createChartStructure();
        this.initChart();
        this.setupEventListeners();
        this.updateChart();
    }

    createChartStructure() {
        // Create time range tabs
        const periodTabs = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div class="btn-group btn-group-sm" role="group">
                    <button type="button" class="btn btn-primary active" data-range="today">Today</button>
                    <button type="button" class="btn btn-outline-primary" data-range="week">Past Week</button>
                    <button type="button" class="btn btn-outline-primary" data-range="month">Past Month</button>
                </div>
                <div class="text-muted small">Last updated: <span id="chart-last-updated"></span></div>
            </div>`;

        // Create canvas wrapper with proper height
        const canvasWrapper = `<div style="height: 300px;"><canvas id="waitTimeChart"></canvas></div>`;

        this.chartContainer.innerHTML = periodTabs + canvasWrapper;
    }

    initChart() {
        const ctx = document.getElementById('waitTimeChart').getContext('2d');
        Chart.defaults.font.family = "'Heebo', sans-serif";
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Dana',
                        borderColor: colors.Dana,
                        backgroundColor: `${colors.Dana}1a`,
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2
                    },
                    {
                        label: 'Roberts',
                        borderColor: colors.Roberts,
                        backgroundColor: `${colors.Roberts}1a`,
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2
                    },
                    {
                        label: 'Foss',
                        borderColor: colors.Foss,
                        backgroundColor: `${colors.Foss}1a`,
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Wait Time (minutes)',
                            font: {
                                size: 12
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#000',
                        bodyColor: '#666',
                        borderColor: '#e9ecef',
                        borderWidth: 1,
                        padding: 10,
                        boxPadding: 5,
                        usePointStyle: true,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y} minutes`;
                            }
                        }
                    }
                }
            }
        });
    }

    setupEventListeners() {
        document.querySelectorAll('[data-range]').forEach(button => {
            button.addEventListener('click', (e) => {
                document.querySelectorAll('[data-range]').forEach(btn => {
                    btn.classList.remove('btn-primary', 'active');
                    btn.classList.add('btn-outline-primary');
                });
                e.target.classList.remove('btn-outline-primary');
                e.target.classList.add('btn-primary', 'active');

                this.timeRange = e.target.dataset.range;
                this.updateChart();
            });
        });
    }

    async updateChart() {
        try {
            const data = await this.fetchWaitTimeData();
            this.chart.data.labels = data.labels;
            this.chart.data.datasets.forEach((dataset, index) => {
                dataset.data = data.datasets[index].data;
            });
            
            // Update last updated time
            const lastUpdated = document.getElementById('chart-last-updated');
            if (lastUpdated) {
                lastUpdated.textContent = new Date().toLocaleTimeString();
            }
            
            this.chart.update();
        } catch (error) {
            console.error('Error updating chart:', error);
            showToast('Error', 'Failed to update wait time chart', 'error');
        }
    }

    async fetchWaitTimeData() {
        // TODO: Replace this with actual API call
        const dataPoints = this.timeRange === 'today' ? 24 : 
                         this.timeRange === 'week' ? 7 : 30;

        const labels = Array.from({ length: dataPoints }, (_, i) => {
            if (this.timeRange === 'today') {
                return `${i}:00`;
            } else {
                return `Day ${i + 1}`;
            }
        });

        const generateData = () => Array.from({ length: dataPoints }, () => 
            Math.floor(Math.random() * 15) + 5
        );

        return {
            labels,
            datasets: [
                { data: generateData() },
                { data: generateData() },
                { data: generateData() }
            ]
        };
    }
}

// Export the class to make it available globally
window.WaitTimeAnalysis = WaitTimeAnalysis;


class PopularDishesChart {
    constructor() {
        this.chart = null;
        this.chartContext = document.getElementById('popularFoodsChart').getContext('2d');
        this.initialized = false;
    }

    init() {
        if (this.initialized) return;
        this.initialized = true;
        this.createChart();
        this.updateChart();
        // Update every 5 minutes
        setInterval(() => this.updateChart(), 300000);
    }

    createChart() {
        Chart.defaults.font.family = "'Heebo', sans-serif";
        this.chart = new Chart(this.chartContext, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Number of Favorites',
                    data: [],
                    backgroundColor: [
                        colors.Dana,     // Professional blue
                        colors.Roberts,  // Nature green
                        colors.Foss,     // Warm red
                        '#f1c40f',      // Yellow
                        '#9b59b6',      // Purple
                        '#3498db'       // Light blue
                    ],
                    borderRadius: 2,
                    barThickness: 25,
                    maxBarThickness: 25
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                // layout: {
                //     padding: {
                //         top: 20,
                //         right: 25,
                //         bottom: 55,
                //         left: 25
                //     }
                // },
            
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#000',
                        bodyColor: '#666',
                        borderColor: '#e9ecef',
                        borderWidth: 1,
                        padding: 10,
                        boxPadding: 5,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                return `${context.raw} favorites`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            drawBorder: false,
                            color: '#e9ecef'
                        },
                        ticks: {
                            precision: 0,
                            font: {
                                size: 11
                            },
                            stepSize: 1 
                        },
                        max: 5
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            padding: 10,
                            font: {
                                size: 11
                            }
                        }
                    }
                }
            }
        });
    }

    async updateChart() {
        try {
            const response = await fetch('/api/trending-favorites');
            const data = await response.json();

            if (data.status === 'success' && data.favorites) {
                // Update chart data
                this.chart.data.labels = data.favorites.map(item => item.name);
                this.chart.data.datasets[0].data = data.favorites.map(item => item.favorites);
                this.chart.update();
            }
        } catch (error) {
            console.error('Error fetching popular dishes:', error);
        }
    }
}
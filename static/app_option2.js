let currentJobId = null;

// File upload handler
document.getElementById('file-upload').addEventListener('change', async (e) => {
    const files = e.target.files;
    if (files.length === 0) return;

    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }

    const statusDiv = document.getElementById('upload-status');
    statusDiv.textContent = 'Uploading...';
    statusDiv.className = 'status-message';

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (data.uploaded && data.uploaded.length > 0) {
            statusDiv.textContent = `✓ Uploaded ${data.uploaded.length} file(s)`;
            statusDiv.classList.add('success');
        } else {
            statusDiv.textContent = 'No files uploaded';
        }
    } catch (error) {
        statusDiv.textContent = `Error: ${error.message}`;
        statusDiv.classList.add('error');
    }
});

// Fetch job description from URL
document.getElementById('fetch-btn').addEventListener('click', async () => {
    const url = document.getElementById('job-url').value.trim();
    if (!url) {
        alert('Please enter a job URL');
        return;
    }

    const btn = document.getElementById('fetch-btn');
    btn.disabled = true;
    btn.textContent = 'Fetching...';

    try {
        const response = await fetch('/fetch-jd', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        const data = await response.json();

        if (data.error) {
            alert(`Error: ${data.error}`);
        } else {
            document.getElementById('job-description').value = data.text;
            if (data.warning) {
                alert(`Warning: ${data.warning}`);
            }
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Fetch Job Description';
    }
});

// Step 1: Calculate ATS Score
document.getElementById('calculate-ats-btn').addEventListener('click', async () => {
    const jobDescription = document.getElementById('job-description').value.trim();
    if (!jobDescription || jobDescription.length < 50) {
        alert('Please enter a job description (at least 50 characters)');
        return;
    }

    const btn = document.getElementById('calculate-ats-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Calculating...';

    try {
        const response = await fetch('/calculate-ats', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_description: jobDescription })
        });
        const data = await response.json();

        if (data.error) {
            alert(`Error: ${data.error}`);
            btn.disabled = false;
            btn.textContent = '🎯 Calculate ATS Score & Match Analysis';
            return;
        }

        currentJobId = data.job_id;
        
        // Show progress and poll for results
        document.getElementById('input-section').style.display = 'none';
        document.getElementById('progress-section').style.display = 'block';
        pollMatchStatus(data.job_id);

    } catch (error) {
        alert(`Error: ${error.message}`);
        btn.disabled = false;
        btn.textContent = '🎯 Calculate ATS Score & Match Analysis';
    }
});

// Poll match status
async function pollMatchStatus(jobId) {
    const progressMessage = document.getElementById('progress-message');
    const progressFill = document.querySelector('.progress-fill');

    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${jobId}`);
            const data = await response.json();

            progressMessage.textContent = data.message || 'Processing...';

            if (data.status === 'loading_docs') {
                progressFill.style.width = '20%';
            } else if (data.status === 'matching') {
                progressFill.style.width = '60%';
            } else if (data.status === 'match_complete') {
                progressFill.style.width = '100%';
                clearInterval(interval);
                showMatchResults(data.match);
            } else if (data.status === 'error') {
                clearInterval(interval);
                alert(`Error: ${data.message}`);
                resetToStart();
            }
        } catch (error) {
            clearInterval(interval);
            alert(`Error polling status: ${error.message}`);
            resetToStart();
        }
    }, 1000);
}

// Show match analysis results
function showMatchResults(match) {
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('match-section').style.display = 'block';

    // Match score
    document.getElementById('match-percentage').textContent = `${match.match_pct}%`;
    document.getElementById('match-rating-text').textContent = match.rating || 'N/A';
    document.getElementById('recommendation-text').textContent = match.recommendation || 'N/A';
    document.getElementById('summary-text').textContent = match.summary || 'No summary available';

    // Strengths
    const strengthsList = document.getElementById('strengths-list');
    strengthsList.innerHTML = '';
    (match.strengths || []).forEach(strength => {
        const li = document.createElement('li');
        li.textContent = strength;
        strengthsList.appendChild(li);
    });

    // Gaps
    const gapsList = document.getElementById('gaps-list');
    gapsList.innerHTML = '';
    (match.gaps || []).forEach(gap => {
        const li = document.createElement('li');
        li.textContent = gap;
        gapsList.appendChild(li);
    });

    // Missing keywords
    const keywordsList = document.getElementById('keywords-list');
    keywordsList.innerHTML = '';
    (match.missing_keywords || []).slice(0, 15).forEach(keyword => {
        const span = document.createElement('span');
        span.className = 'keyword-tag';
        span.textContent = keyword;
        keywordsList.appendChild(span);
    });
}

// Step 2: Build Resume (after user confirms)
document.getElementById('build-resume-btn').addEventListener('click', async () => {
    if (!currentJobId) {
        alert('No job ID found. Please calculate ATS score first.');
        return;
    }

    const btn = document.getElementById('build-resume-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Building...';

    try {
        const response = await fetch('/build-resume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_id: currentJobId })
        });
        const data = await response.json();

        if (data.error) {
            alert(`Error: ${data.error}`);
            btn.disabled = false;
            btn.textContent = '✅ Build Tailored Resume';
            return;
        }

        // Show progress and poll for resume building
        document.getElementById('match-section').style.display = 'none';
        document.getElementById('progress-section').style.display = 'block';
        pollResumeStatus(currentJobId);

    } catch (error) {
        alert(`Error: ${error.message}`);
        btn.disabled = false;
        btn.textContent = '✅ Build Tailored Resume';
    }
});

// Cancel button
document.getElementById('cancel-btn').addEventListener('click', () => {
    if (confirm('Are you sure you want to cancel? No resume will be generated.')) {
        resetToStart();
    }
});

// Poll resume building status
async function pollResumeStatus(jobId) {
    const progressMessage = document.getElementById('progress-message');
    const progressFill = document.querySelector('.progress-fill');

    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${jobId}`);
            const data = await response.json();

            progressMessage.textContent = data.message || 'Processing...';

            if (data.status === 'waiting') {
                progressFill.style.width = '20%';
            } else if (data.status === 'building') {
                progressFill.style.width = '60%';
            } else if (data.status === 'generating') {
                progressFill.style.width = '90%';
            } else if (data.status === 'done') {
                progressFill.style.width = '100%';
                clearInterval(interval);
                showDownloadSection(data);
            } else if (data.status === 'error') {
                clearInterval(interval);
                alert(`Error: ${data.message}`);
                resetToStart();
            }
        } catch (error) {
            clearInterval(interval);
            alert(`Error polling status: ${error.message}`);
            resetToStart();
        }
    }, 2000);
}

// Show download section
function showDownloadSection(data) {
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('download-section').style.display = 'block';

    document.getElementById('final-ats-score').textContent = data.ats_score || 'N/A';

    // Suggestions
    const suggestionsList = document.getElementById('suggestions-list');
    if (data.suggestions && data.suggestions.length > 0) {
        suggestionsList.innerHTML = '<h4>💡 Suggestions:</h4><ul></ul>';
        const ul = suggestionsList.querySelector('ul');
        data.suggestions.forEach(suggestion => {
            const li = document.createElement('li');
            li.textContent = suggestion;
            ul.appendChild(li);
        });
    } else {
        suggestionsList.innerHTML = '';
    }

    // Set download button handler
    document.getElementById('download-btn').onclick = () => {
        window.location.href = `/download/${data.filename}`;
    };
}

// Start over button
document.getElementById('start-over-btn').addEventListener('click', () => {
    resetToStart();
});

// Reset to start
function resetToStart() {
    currentJobId = null;
    document.getElementById('input-section').style.display = 'block';
    document.getElementById('match-section').style.display = 'none';
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('download-section').style.display = 'none';
    
    document.getElementById('calculate-ats-btn').disabled = false;
    document.getElementById('calculate-ats-btn').textContent = '🎯 Calculate ATS Score & Match Analysis';
    
    document.querySelector('.progress-fill').style.width = '0%';
}

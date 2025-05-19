// Main JavaScript for UKG System

// Update confidence value when slider changes
document.getElementById('confidence-slider').addEventListener('input', function() {
    document.getElementById('confidence-value').textContent = this.value;
});

// Handle form submission
document.getElementById('query-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const queryText = document.getElementById('query-input').value.trim();
    const confidenceTarget = document.getElementById('confidence-slider').value;
    
    if (queryText) {
        processQuery(queryText, confidenceTarget);
    }
});

// Process query and get response
function processQuery(queryText, confidenceTarget) {
    // Show loading indicator
    const resultCard = document.getElementById('result-card');
    resultCard.classList.remove('d-none');
    
    const loadingIndicator = document.getElementById('loading-indicator');
    loadingIndicator.classList.remove('d-none');
    
    const resultContent = document.getElementById('result-content');
    resultContent.innerHTML = '';
    
    document.getElementById('session-id').textContent = 'Session: Processing...';
    document.getElementById('confidence-badge').textContent = 'Confidence: -';
    document.getElementById('result-metadata').textContent = '';
    
    // Submit query to API
    fetch('/api/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: queryText,
            target_confidence: parseFloat(confidenceTarget)
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        displayResult(data);
    })
    .catch(error => {
        console.error('Error:', error);
        resultContent.innerHTML = `
            <div class="alert alert-danger">
                <h4>Error Processing Query</h4>
                <p>${error.message}</p>
            </div>
        `;
    })
    .finally(() => {
        loadingIndicator.classList.add('d-none');
    });
}

// Display query result
function displayResult(data) {
    const resultContent = document.getElementById('result-content');
    const sessionIdBadge = document.getElementById('session-id');
    const confidenceBadge = document.getElementById('confidence-badge');
    const resultMetadata = document.getElementById('result-metadata');
    
    // Update session ID
    sessionIdBadge.textContent = `Session: ${data.session_id.substring(0, 8)}...`;
    
    // Update confidence and style based on value
    const confidence = data.confidence;
    confidenceBadge.textContent = `Confidence: ${(confidence * 100).toFixed(1)}%`;
    
    if (confidence < 0.7) {
        confidenceBadge.className = 'badge bg-danger';
    } else if (confidence < 0.85) {
        confidenceBadge.className = 'badge bg-warning text-dark';
    } else {
        confidenceBadge.className = 'badge bg-success';
    }
    
    // Render answer text with markdown
    const answerText = data.answer_text || 'No answer provided.';
    resultContent.innerHTML = marked.parse(answerText);
    
    // Add metadata
    const metadataText = [
        `Status: ${data.status}`,
        `Passes: ${data.passes_executed}`,
        `Processed: ${new Date(data.processing_metadata.timestamp).toLocaleString()}`
    ].join(' | ');
    
    resultMetadata.textContent = metadataText;
}

// Load system statistics
function loadSystemStats() {
    // Load graph statistics
    fetch('/api/graph_stats')
        .then(response => response.json())
        .then(data => {
            const graphStats = document.getElementById('graph-stats');
            
            // Format node types for display
            let nodeTypesHtml = '<ul class="list-unstyled mb-0">';
            Object.entries(data.node_types).slice(0, 5).forEach(([type, count]) => {
                nodeTypesHtml += `<li><span class="badge bg-secondary">${count}</span> ${type}</li>`;
            });
            nodeTypesHtml += '</ul>';
            
            graphStats.innerHTML = `
                <div class="d-flex justify-content-between">
                    <div><strong>Nodes:</strong> ${data.total_nodes}</div>
                    <div><strong>Edges:</strong> ${data.total_edges}</div>
                </div>
                <div class="mt-2">
                    <strong>Top Node Types:</strong>
                    ${nodeTypesHtml}
                </div>
            `;
        })
        .catch(error => {
            console.error('Error fetching graph stats:', error);
            document.getElementById('graph-stats').innerHTML = '<div class="alert alert-warning">Error loading graph statistics</div>';
        });
    
    // Load memory statistics
    fetch('/api/memory_stats')
        .then(response => response.json())
        .then(data => {
            const memoryStats = document.getElementById('memory-stats');
            
            // Format entry types for display
            let entryTypesHtml = '<ul class="list-unstyled mb-0">';
            Object.entries(data.entry_types).slice(0, 5).forEach(([type, count]) => {
                entryTypesHtml += `<li><span class="badge bg-secondary">${count}</span> ${type}</li>`;
            });
            entryTypesHtml += '</ul>';
            
            memoryStats.innerHTML = `
                <div><strong>Total Entries:</strong> ${data.total_entries}</div>
                <div><strong>Size:</strong> ${(data.memory_size_bytes / 1024).toFixed(2)} KB</div>
                <div class="mt-2">
                    <strong>Entry Types:</strong>
                    ${entryTypesHtml}
                </div>
            `;
        })
        .catch(error => {
            console.error('Error fetching memory stats:', error);
            document.getElementById('memory-stats').innerHTML = '<div class="alert alert-warning">Error loading memory statistics</div>';
        });
}

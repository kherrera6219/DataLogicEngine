/**
 * Universal Knowledge Graph (UKG) - Main JavaScript
 * Handles client-side interactions for the UKG application
 */

document.addEventListener('DOMContentLoaded', function() {
  // Sidebar toggle
  const sidebarToggle = document.getElementById('sidebar-toggle');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
      document.body.classList.toggle('sidebar-collapsed');
      
      // Store preference in localStorage
      const isSidebarCollapsed = document.body.classList.contains('sidebar-collapsed');
      localStorage.setItem('sidebar-collapsed', isSidebarCollapsed);
    });
    
    // Check localStorage for sidebar state
    const storedSidebarState = localStorage.getItem('sidebar-collapsed');
    if (storedSidebarState === 'true') {
      document.body.classList.add('sidebar-collapsed');
    }
  }
  
  // Theme toggle (if present)
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', function() {
      document.body.classList.toggle('light-theme');
      document.body.classList.toggle('dark-theme');
      
      // Store preference in localStorage
      const isLightTheme = document.body.classList.contains('light-theme');
      localStorage.setItem('light-theme', isLightTheme);
    });
    
    // Check localStorage for theme preference
    const storedTheme = localStorage.getItem('light-theme');
    if (storedTheme === 'true' && document.body.classList.contains('dark-theme')) {
      document.body.classList.remove('dark-theme');
      document.body.classList.add('light-theme');
    }
  }
  
  // Handle alert close buttons
  const alertCloseButtons = document.querySelectorAll('.close-alert');
  alertCloseButtons.forEach(button => {
    button.addEventListener('click', function() {
      const alert = this.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        setTimeout(() => {
          alert.style.display = 'none';
        }, 300);
      }
    });
  });
  
  // Handle mobile sidebar
  const handleResize = () => {
    if (window.innerWidth < 992) {
      document.body.classList.add('sidebar-collapsed');
      
      // For mobile, add click handler to show/hide sidebar
      document.addEventListener('click', function(e) {
        if (e.target.matches('#sidebar-toggle, #sidebar-toggle *')) {
          document.body.classList.toggle('sidebar-open');
          e.stopPropagation();
        } else if (!e.target.closest('.app-sidebar') && document.body.classList.contains('sidebar-open')) {
          document.body.classList.remove('sidebar-open');
        }
      });
    }
  };
  
  // Initial check
  handleResize();
  
  // Listen for window resize
  window.addEventListener('resize', handleResize);
  
  // Initialize any Knowledge Graph visualization if present
  initializeGraphVisualization();
  
  // Initialize chatbot if present
  initializeChatbot();
});

/**
 * Initialize Knowledge Graph Visualization if present on the page
 */
function initializeGraphVisualization() {
  const graphContainer = document.getElementById('graph-container');
  if (!graphContainer) return;
  
  // This would normally connect to a library like D3.js or similar
  // For now, we'll just add a placeholder
  graphContainer.innerHTML = '<div class="graph-placeholder">Loading graph visualization...</div>';
  
  // In a real implementation, this would fetch graph data and render it
  fetch('/api/graph')
    .then(response => response.json())
    .then(data => {
      console.log('Graph data loaded:', data);
      // Initialize and render graph with the data
      // Example: initD3Graph(graphContainer, data);
    })
    .catch(error => {
      console.error('Error loading graph data:', error);
      graphContainer.innerHTML = '<div class="graph-error">Error loading graph data. Please try again later.</div>';
    });
}

/**
 * Initialize chatbot interface if present
 */
function initializeChatbot() {
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatMessages = document.getElementById('chat-messages');
  
  if (!chatForm || !chatInput || !chatMessages) return;
  
  chatForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const message = chatInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    
    // Clear input
    chatInput.value = '';
    
    // Show typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'chat-message system typing-indicator';
    typingIndicator.innerHTML = 'UKG is thinking<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>';
    chatMessages.appendChild(typingIndicator);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Make API request to backend
    fetch('/api/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query: message })
    })
    .then(response => response.json())
    .then(data => {
      // Remove typing indicator
      chatMessages.removeChild(typingIndicator);
      
      // Add response to chat
      addChatMessage(data.response, 'system');
      
      // If there's confidence data, add it
      if (data.confidenceScore) {
        const confidenceIndicator = document.createElement('div');
        confidenceIndicator.className = 'confidence-indicator';
        confidenceIndicator.innerHTML = `<small>Confidence: ${Math.round(data.confidenceScore * 100)}% (Layer ${data.activeLayer || 1})</small>`;
        chatMessages.appendChild(confidenceIndicator);
      }
    })
    .catch(error => {
      // Remove typing indicator
      chatMessages.removeChild(typingIndicator);
      
      // Add error message
      addChatMessage('Sorry, there was an error processing your request. Please try again.', 'system error');
      console.error('Chat error:', error);
    });
  });
  
  /**
   * Add a message to the chat interface
   */
  function addChatMessage(message, type) {
    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${type}`;
    messageElement.textContent = message;
    
    chatMessages.appendChild(messageElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

/**
 * Handle Knowledge Graph filtering if present
 */
function handleGraphFilters() {
  const filterForm = document.getElementById('graph-filter-form');
  if (!filterForm) return;
  
  filterForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Get filter values
    const axis = document.getElementById('filter-axis').value;
    const nodeType = document.getElementById('filter-node-type').value;
    
    // Update graph with filters
    updateGraphVisualization({ axis, nodeType });
  });
  
  // Reset filters button
  const resetButton = document.getElementById('reset-filters');
  if (resetButton) {
    resetButton.addEventListener('click', function() {
      document.getElementById('filter-axis').value = '0';
      document.getElementById('filter-node-type').value = 'all';
      updateGraphVisualization({});
    });
  }
}

/**
 * Update the graph visualization with new filters
 */
function updateGraphVisualization(filters) {
  const graphContainer = document.getElementById('graph-container');
  if (!graphContainer) return;
  
  // Show loading state
  graphContainer.classList.add('loading');
  
  // Build query string from filters
  const queryParams = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) queryParams.append(key, value);
  });
  
  // Fetch updated graph data
  fetch(`/api/graph?${queryParams.toString()}`)
    .then(response => response.json())
    .then(data => {
      // Remove loading state
      graphContainer.classList.remove('loading');
      
      // Update graph visualization
      console.log('Updated graph data:', data);
      // Example: updateD3Graph(graphContainer, data);
    })
    .catch(error => {
      // Remove loading state
      graphContainer.classList.remove('loading');
      
      console.error('Error updating graph:', error);
      // Show error state
    });
}
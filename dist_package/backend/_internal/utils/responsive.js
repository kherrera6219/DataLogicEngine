
// Responsive utility functions for UKG System

// Mobile sidebar visibility toggle handler
export const toggleSidebar = () => {
  const sidebar = document.querySelector('.chat-sidebar');
  if (sidebar) {
    sidebar.classList.toggle('show');
  }
};

// Close sidebar when clicking outside on mobile
export const setupSidebarClickOutside = () => {
  const sidebar = document.querySelector('.chat-sidebar');
  const toggleButton = document.querySelector('.sidebar-toggle');
  
  if (sidebar && toggleButton) {
    document.addEventListener('click', (event) => {
      const isClickInside = sidebar.contains(event.target) || toggleButton.contains(event.target);
      
      if (!isClickInside && sidebar.classList.contains('show')) {
        sidebar.classList.remove('show');
      }
    });
  }
};

// Detect screen size for responsive adjustments
export const getScreenSize = () => {
  if (typeof window === 'undefined') return 'lg'; // Default for SSR
  
  const width = window.innerWidth;
  if (width < 576) return 'xs';
  if (width < 768) return 'sm';
  if (width < 992) return 'md';
  if (width < 1200) return 'lg';
  return 'xl';
};

// Adjust element height based on viewport
export const adjustHeight = (element, offset = 0) => {
  if (!element) return;
  
  const windowHeight = window.innerHeight;
  element.style.height = `${windowHeight - offset}px`;
};

// Initialize all responsive handlers
export const initResponsiveHandlers = () => {
  // Set up sidebar toggle for mobile
  const toggleButton = document.querySelector('.sidebar-toggle');
  if (toggleButton) {
    toggleButton.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleSidebar();
    });
  }
  
  // Set up outside click handling
  setupSidebarClickOutside();
  
  // Resize handler for adjusting heights
  const resizeHandler = () => {
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
      const headerHeight = 60; // Adjust based on your header
      const footerHeight = 60; // Adjust based on your footer
      const marginOffset = 32; // Additional margins/padding
      
      if (window.innerWidth < 768) {
        // Mobile view
        adjustHeight(chatContainer, headerHeight + footerHeight + marginOffset);
      } else {
        // Desktop view
        adjustHeight(chatContainer, headerHeight + footerHeight + marginOffset);
      }
    }
  };
  
  // Initial call and event listener
  resizeHandler();
  window.addEventListener('resize', resizeHandler);
  
  return () => {
    window.removeEventListener('resize', resizeHandler);
  };
};

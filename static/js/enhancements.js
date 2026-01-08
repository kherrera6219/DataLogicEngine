/**
 * DataLogicEngine - Enhanced JavaScript Utilities
 * Modern interactions and UI enhancements
 */

// ===== Toast Notifications =====
class Toast {
    static container = null;

    static init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            this.container.style.cssText = `
                position: fixed;
                bottom: 2rem;
                right: 2rem;
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
                z-index: 3000;
            `;
            document.body.appendChild(this.container);
        }
    }

    static show(message, type = 'info', duration = 4000) {
        this.init();
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span class="material-icons">${this.getIcon(type)}</span>
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <span class="material-icons">close</span>
            </button>
        `;
        toast.style.cssText = `
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 1rem 1.5rem;
            background: var(--dark-bg-secondary);
            border-radius: 8px;
            box-shadow: var(--shadow-lg);
            border-left: 4px solid ${this.getColor(type)};
            transform: translateX(120%);
            transition: transform 0.3s ease;
        `;
        
        this.container.appendChild(toast);
        
        // Trigger animation
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(0)';
        });
        
        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                toast.style.transform = 'translateX(120%)';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
        
        return toast;
    }

    static getIcon(type) {
        const icons = {
            success: 'check_circle',
            error: 'error',
            warning: 'warning',
            info: 'info'
        };
        return icons[type] || 'info';
    }

    static getColor(type) {
        const colors = {
            success: 'var(--success)',
            error: 'var(--danger)',
            warning: 'var(--warning)',
            info: 'var(--info)'
        };
        return colors[type] || 'var(--info)';
    }

    static success(message) { return this.show(message, 'success'); }
    static error(message) { return this.show(message, 'error'); }
    static warning(message) { return this.show(message, 'warning'); }
    static info(message) { return this.show(message, 'info'); }
}

// ===== Loading States =====
class Loading {
    static show(element, text = 'Loading...') {
        const original = element.innerHTML;
        element.dataset.originalContent = original;
        element.disabled = true;
        element.classList.add('loading');
        element.innerHTML = `
            <span class="spinner"></span>
            <span>${text}</span>
        `;
    }

    static hide(element) {
        element.innerHTML = element.dataset.originalContent;
        element.disabled = false;
        element.classList.remove('loading');
    }

    static skeleton(container, count = 3) {
        const skeletons = [];
        for (let i = 0; i < count; i++) {
            const skeleton = document.createElement('div');
            skeleton.className = 'skeleton';
            skeleton.style.cssText = `
                height: 60px;
                margin-bottom: 1rem;
                border-radius: 8px;
            `;
            container.appendChild(skeleton);
            skeletons.push(skeleton);
        }
        return skeletons;
    }
}

// ===== Scroll Progress Indicator =====
class ScrollProgress {
    static init() {
        const indicator = document.createElement('div');
        indicator.className = 'scroll-indicator';
        document.body.appendChild(indicator);

        window.addEventListener('scroll', () => {
            const scrollTop = window.scrollY;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const progress = (scrollTop / docHeight) * 100;
            indicator.style.width = `${progress}%`;
        });
    }
}

// ===== Intersection Observer Animations =====
class AnimateOnScroll {
    static init() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        document.querySelectorAll('[data-animate]').forEach(el => {
            el.classList.add('animate-hidden');
            observer.observe(el);
        });
    }
}

// ===== Theme Management =====
class ThemeManager {
    static init() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        this.setTheme(savedTheme);
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (!localStorage.getItem('theme')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    static setTheme(theme) {
        document.body.classList.remove('dark-theme', 'light-theme');
        document.body.classList.add(`${theme}-theme`);
        localStorage.setItem('theme', theme);
        
        // Update meta theme-color for mobile browsers
        const metaTheme = document.querySelector('meta[name="theme-color"]');
        if (metaTheme) {
            metaTheme.content = theme === 'dark' ? '#121212' : '#f8f9fa';
        }
    }

    static toggle() {
        const currentTheme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
        this.setTheme(currentTheme === 'dark' ? 'light' : 'dark');
    }
}

// ===== Modal Manager =====
class Modal {
    static open(id) {
        const modal = document.getElementById(id);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }

    static close(id) {
        const modal = document.getElementById(id);
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    static create(options) {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${options.title || ''}</h3>
                    <button class="modal-close" onclick="Modal.close('${options.id}')">
                        <span class="material-icons">close</span>
                    </button>
                </div>
                <div class="modal-body">
                    ${options.content || ''}
                </div>
                ${options.footer ? `<div class="modal-footer">${options.footer}</div>` : ''}
            </div>
        `;
        overlay.id = options.id;
        overlay.addEventListener('click', e => {
            if (e.target === overlay) this.close(options.id);
        });
        document.body.appendChild(overlay);
        return overlay;
    }
}

// ===== Search with Debounce =====
class Search {
    static debounce(func, wait = 300) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    static init(inputId, callback) {
        const input = document.getElementById(inputId);
        if (!input) return;

        const debouncedSearch = this.debounce(async (query) => {
            if (query.length < 2) return;
            
            try {
                const response = await fetch(`/api/v1/search/suggest?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                callback(data.suggestions || []);
            } catch (error) {
                console.error('Search error:', error);
            }
        });

        input.addEventListener('input', e => debouncedSearch(e.target.value));
    }
}

// ===== Keyboard Navigation =====
class KeyboardNav {
    static init() {
        document.addEventListener('keydown', e => {
            // ESC closes modals
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal-overlay.show').forEach(modal => {
                    Modal.close(modal.id);
                });
            }
            
            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('.search-enhanced input, #global-search');
                if (searchInput) searchInput.focus();
            }
        });
    }
}

// ===== Initialize All Enhancements =====
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
    ScrollProgress.init();
    AnimateOnScroll.init();
    KeyboardNav.init();
    
    // Initialize tooltips
    document.querySelectorAll('[data-tooltip]').forEach(el => {
        el.classList.add('tooltip');
    });
});

// Export for use in other modules
window.Toast = Toast;
window.Loading = Loading;
window.Modal = Modal;
window.Search = Search;
window.ThemeManager = ThemeManager;

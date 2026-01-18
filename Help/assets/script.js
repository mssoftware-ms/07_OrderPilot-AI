/**
 * OrderPilot-AI Help System
 * Interactive JavaScript functionality
 */

// ==========================================
// Tab Switching
// ==========================================

/**
 * Initialize tab switching functionality
 */
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');

            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            const targetContent = document.getElementById(targetTab);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });

    // Activate first tab by default
    if (tabButtons.length > 0 && tabContents.length > 0) {
        tabButtons[0].classList.add('active');
        tabContents[0].classList.add('active');
    }
}

// ==========================================
// Copy to Clipboard
// ==========================================

/**
 * Initialize copy-to-clipboard functionality for code blocks
 */
function initCopyButtons() {
    const codeBlocks = document.querySelectorAll('pre code');

    codeBlocks.forEach(codeBlock => {
        const pre = codeBlock.parentElement;

        // Wrap pre in .code-block if not already wrapped
        if (!pre.parentElement.classList.contains('code-block')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'code-block';
            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(pre);
        }

        // Create copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.textContent = 'Copy';
        copyBtn.setAttribute('aria-label', 'Copy code to clipboard');

        copyBtn.addEventListener('click', async () => {
            const code = codeBlock.textContent;

            try {
                await navigator.clipboard.writeText(code);

                // Visual feedback
                copyBtn.textContent = 'Copied!';
                copyBtn.classList.add('copied');

                setTimeout(() => {
                    copyBtn.textContent = 'Copy';
                    copyBtn.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy code:', err);
                copyBtn.textContent = 'Failed';

                setTimeout(() => {
                    copyBtn.textContent = 'Copy';
                }, 2000);
            }
        });

        pre.parentElement.appendChild(copyBtn);
    });
}

// ==========================================
// Smooth Scrolling
// ==========================================

/**
 * Initialize smooth scrolling for anchor links
 */
function initSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');

            // Skip if href is just "#"
            if (href === '#') return;

            e.preventDefault();

            const targetId = href.substring(1);
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });

                // Update URL without jumping
                history.pushState(null, null, href);
            }
        });
    });
}

// ==========================================
// Active Navigation Highlighting
// ==========================================

/**
 * Highlight active navigation item based on scroll position
 */
function initActiveNav() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('nav a[href^="#"]');

    function highlightNav() {
        let currentSection = '';

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;

            // Account for sticky header height
            if (window.scrollY >= sectionTop - 200) {
                currentSection = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            const href = link.getAttribute('href');

            if (href === `#${currentSection}`) {
                link.classList.add('active');
            }
        });
    }

    // Throttle scroll event for performance
    let scrollTimeout;
    window.addEventListener('scroll', () => {
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }

        scrollTimeout = setTimeout(highlightNav, 50);
    });

    // Initial highlight
    highlightNav();
}

// ==========================================
// Mobile Menu Toggle
// ==========================================

/**
 * Initialize mobile navigation toggle
 */
function initMobileMenu() {
    const nav = document.querySelector('nav ul');

    // Create mobile menu button
    const menuBtn = document.createElement('button');
    menuBtn.className = 'mobile-menu-btn';
    menuBtn.innerHTML = '☰';
    menuBtn.setAttribute('aria-label', 'Toggle navigation menu');

    menuBtn.addEventListener('click', () => {
        nav.classList.toggle('mobile-open');
        menuBtn.classList.toggle('open');
        menuBtn.innerHTML = menuBtn.classList.contains('open') ? '✕' : '☰';
    });

    // Insert button before nav
    const navElement = document.querySelector('nav');
    if (navElement && window.innerWidth <= 768) {
        navElement.insertBefore(menuBtn, nav);
    }

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!navElement.contains(e.target) && nav.classList.contains('mobile-open')) {
            nav.classList.remove('mobile-open');
            menuBtn.classList.remove('open');
            menuBtn.innerHTML = '☰';
        }
    });

    // Close menu when clicking a link
    const navLinks = nav.querySelectorAll('a');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (nav.classList.contains('mobile-open')) {
                nav.classList.remove('mobile-open');
                menuBtn.classList.remove('open');
                menuBtn.innerHTML = '☰';
            }
        });
    });
}

// ==========================================
// Search Functionality (Optional Enhancement)
// ==========================================

/**
 * Initialize search functionality
 */
function initSearch() {
    const searchInput = document.getElementById('search-input');

    if (!searchInput) return;

    const searchableElements = document.querySelectorAll('section, .module-card, .feature-card');

    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();

        searchableElements.forEach(element => {
            const text = element.textContent.toLowerCase();

            if (text.includes(searchTerm) || searchTerm === '') {
                element.style.display = '';
            } else {
                element.style.display = 'none';
            }
        });
    });
}

// ==========================================
// Accordion Functionality
// ==========================================

/**
 * Initialize accordion functionality for expandable sections
 */
function initAccordions() {
    const accordionHeaders = document.querySelectorAll('.accordion-header');

    accordionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const content = header.nextElementSibling;
            const isOpen = header.classList.contains('open');

            // Close all accordions
            accordionHeaders.forEach(h => {
                h.classList.remove('open');
                if (h.nextElementSibling) {
                    h.nextElementSibling.style.display = 'none';
                }
            });

            // Toggle current accordion
            if (!isOpen) {
                header.classList.add('open');
                if (content) {
                    content.style.display = 'block';
                }
            }
        });
    });
}

// ==========================================
// Back to Top Button
// ==========================================

/**
 * Initialize back-to-top button
 */
function initBackToTop() {
    // Create button
    const backToTopBtn = document.createElement('button');
    backToTopBtn.className = 'back-to-top';
    backToTopBtn.innerHTML = '↑';
    backToTopBtn.setAttribute('aria-label', 'Back to top');
    backToTopBtn.style.display = 'none';

    document.body.appendChild(backToTopBtn);

    // Show/hide button based on scroll
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTopBtn.style.display = 'flex';
        } else {
            backToTopBtn.style.display = 'none';
        }
    });

    // Scroll to top on click
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// ==========================================
// Tooltip Functionality
// ==========================================

/**
 * Initialize tooltips for elements with data-tooltip attribute
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');

    tooltipElements.forEach(element => {
        const tooltipText = element.getAttribute('data-tooltip');

        // Create tooltip element
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = tooltipText;
        tooltip.style.display = 'none';

        element.appendChild(tooltip);

        element.addEventListener('mouseenter', () => {
            tooltip.style.display = 'block';
        });

        element.addEventListener('mouseleave', () => {
            tooltip.style.display = 'none';
        });
    });
}

// ==========================================
// Theme Toggle (Optional)
// ==========================================

/**
 * Initialize theme toggle between dark and light modes
 */
function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');

    if (!themeToggle) return;

    // Load saved theme preference
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
}

// ==========================================
// Module Card Click Handlers
// ==========================================

/**
 * Initialize module card click handlers
 */
function initModuleCards() {
    const moduleCards = document.querySelectorAll('.module-card');

    moduleCards.forEach(card => {
        const link = card.querySelector('.btn');

        if (link) {
            // Make entire card clickable
            card.addEventListener('click', (e) => {
                // Don't trigger if clicking the button directly
                if (e.target !== link) {
                    link.click();
                }
            });

            // Add keyboard accessibility
            card.setAttribute('tabindex', '0');
            card.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    link.click();
                }
            });
        }
    });
}

// ==========================================
// Code Syntax Highlighting (Optional)
// ==========================================

/**
 * Apply basic syntax highlighting to code blocks
 */
function initSyntaxHighlighting() {
    const codeBlocks = document.querySelectorAll('pre code');

    codeBlocks.forEach(block => {
        // Auto-detect language from class or data attribute
        const language = block.className.match(/language-(\w+)/)?.[1] || 'python';

        // Add language indicator
        const langLabel = document.createElement('span');
        langLabel.className = 'code-lang';
        langLabel.textContent = language.toUpperCase();

        const pre = block.parentElement;
        if (pre.parentElement.classList.contains('code-block')) {
            pre.parentElement.insertBefore(langLabel, pre);
        }
    });
}

// ==========================================
// Performance Monitoring
// ==========================================

/**
 * Log performance metrics (development only)
 */
function logPerformance() {
    if (window.performance && window.performance.timing) {
        const timing = window.performance.timing;
        const loadTime = timing.loadEventEnd - timing.navigationStart;

        console.log(`%c📊 Performance Metrics`, 'color: #ff6b35; font-weight: bold;');
        console.log(`Page Load Time: ${loadTime}ms`);
        console.log(`DOM Content Loaded: ${timing.domContentLoadedEventEnd - timing.navigationStart}ms`);
    }
}

// ==========================================
// Initialization
// ==========================================

/**
 * Initialize all functionality when DOM is ready
 */
function init() {
    console.log('%c🚀 OrderPilot-AI Help System', 'color: #ff6b35; font-size: 16px; font-weight: bold;');
    console.log('%cInitializing interactive features...', 'color: #b0b0b0;');

    // Core functionality
    initTabs();
    initCopyButtons();
    initSmoothScroll();
    initActiveNav();
    initModuleCards();

    // Enhanced functionality
    initMobileMenu();
    initBackToTop();
    initTooltips();
    initAccordions();
    initSearch();
    initSyntaxHighlighting();
    initThemeToggle();

    // Development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        logPerformance();
    }

    console.log('%c✅ Initialization complete', 'color: #4ade80; font-weight: bold;');
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    // DOMContentLoaded already fired
    init();
}

// ==========================================
// Expose API for external use
// ==========================================

window.OrderPilotHelp = {
    version: '1.0.0',
    initTabs,
    initCopyButtons,
    initSmoothScroll,
    initActiveNav,
    initSearch
};
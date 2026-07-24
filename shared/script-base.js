// ===================================
// Amadeus Events - Shared Base JavaScript
// Dark mode, mobile menu, scroll animations
// ===================================

(function () {
    'use strict';

    // Dark Mode Toggle (dark is the default)
    const themeToggle = document.getElementById('theme-toggle');
    const html = document.documentElement;

    const currentTheme = localStorage.getItem('theme') || 'dark';
    html.setAttribute('data-theme', currentTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const current = html.getAttribute('data-theme');
            const newTheme = current === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }

    // Mobile Menu Toggle
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (mobileMenuToggle && navLinks) {
        mobileMenuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            mobileMenuToggle.classList.toggle('active');
        });

        document.querySelectorAll('.nav-links a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('active');
                mobileMenuToggle.classList.remove('active');
            });
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.navbar')) {
                navLinks.classList.remove('active');
                mobileMenuToggle.classList.remove('active');
            }
        });
    }

    // Smooth Scroll with Offset for Fixed Nav
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offsetTop = target.offsetTop - 80;
                window.scrollTo({ top: offsetTop, behavior: 'smooth' });
            }
        });
    });

    // Scroll Animation for Elements
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });

    // Navbar shadow on scroll
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 100) {
                navbar.style.boxShadow = '0 4px 20px rgba(38, 0, 90, 0.2)';
            } else {
                navbar.style.boxShadow = '0 2px 10px rgba(38, 0, 90, 0.1)';
            }
        });
    }

    const scrollCue = document.querySelector('.scroll-cue');
    const hero = document.querySelector('.hero');

    if (scrollCue && hero) {
        const updateScrollCueVisibility = () => {
            const heroRect = hero.getBoundingClientRect();
            const isAtPageTop = window.scrollY <= 1;
            const isHeroFullyVisible = heroRect.bottom <= window.innerHeight;
            scrollCue.classList.toggle('is-hidden', !(isAtPageTop && isHeroFullyVisible));
        };

        updateScrollCueVisibility();
        window.addEventListener('scroll', updateScrollCueVisibility, { passive: true });
        window.addEventListener('resize', updateScrollCueVisibility);
    }

    // Easter egg: click yellow Mac control to slide the code window partly out on the right.
    const codeWindow = document.querySelector('.code-window');
    const yellowControl = document.querySelector('.window-controls span:nth-child(2)');
    if (codeWindow && yellowControl) {
        yellowControl.setAttribute('role', 'button');
        yellowControl.setAttribute('tabindex', '0');
        yellowControl.setAttribute('aria-label', 'Toggle code window peek mode');

        const togglePeek = () => {
            codeWindow.classList.toggle('is-peeking-right');
        };

        yellowControl.addEventListener('click', togglePeek);
        yellowControl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                togglePeek();
            }
        });
    }

    if (codeWindow) {
        const compileMessages = [
            'Initializing conference chaos module...',
            'Linting slide decks for missing semicolons...',
            'Defragmenting timetable to avoid lunch-time keynotes...',
            'Reprinting signage after "minor" branding tweak...',
            'Verifying Wi-Fi can survive live demos...',
            'Locking speaker lineup and hiding the edit button...'
        ];

        const runCompileEasterEgg = () => {
            if (codeWindow.classList.contains('is-compiling')) return;

            codeWindow.classList.add('is-compiling');

            const overlay = document.createElement('div');
            overlay.className = 'compile-overlay';
            overlay.innerHTML = [
                '<div class="compile-title">EVENT BUILD PIPELINE</div>',
                '<div class="compile-status" aria-live="polite">Compiling talks...</div>',
                '<div class="compile-bar"><span></span></div>',
                '<div class="compile-percent">0%</div>'
            ].join('');

            codeWindow.appendChild(overlay);

            const statusEl = overlay.querySelector('.compile-status');
            const barEl = overlay.querySelector('.compile-bar span');
            const percentEl = overlay.querySelector('.compile-percent');

            const stageCount = compileMessages.length;
            const stageDelayMs = 1200;
            let stageIndex = 0;

            if (statusEl) statusEl.textContent = compileMessages[stageIndex];
            if (barEl) barEl.style.width = '0%';
            if (percentEl) percentEl.textContent = '0%';

            const advanceStage = () => {
                stageIndex += 1;

                if (stageIndex < stageCount) {
                    const progress = Math.round((stageIndex / stageCount) * 100);
                    if (statusEl) statusEl.textContent = compileMessages[stageIndex];
                    if (barEl) barEl.style.width = `${progress}%`;
                    if (percentEl) percentEl.textContent = `${progress}%`;

                    window.setTimeout(advanceStage, stageDelayMs);
                    return;
                }

                if (barEl) barEl.style.width = '100%';
                if (percentEl) percentEl.textContent = '100%';

                if (statusEl) statusEl.textContent = 'Build complete. Schedule shipped, sanity pending.';

                window.setTimeout(() => {
                    overlay.remove();
                    codeWindow.classList.remove('is-compiling');
                }, 5000);
            };

            window.setTimeout(advanceStage, stageDelayMs);
        };

        codeWindow.addEventListener('dblclick', runCompileEasterEgg);
    }
})();

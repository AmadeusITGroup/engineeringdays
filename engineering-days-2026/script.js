// ===================================
// Dark Mode Toggle
// ===================================

const themeToggle = document.getElementById('theme-toggle');
const html = document.documentElement;

// Check for saved theme preference or default to light mode
const currentTheme = localStorage.getItem('theme') || 'light';
html.setAttribute('data-theme', currentTheme);

themeToggle.addEventListener('click', () => {
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
});

// ===================================
// Mobile Menu Toggle
// ===================================

const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
const navLinks = document.querySelector('.nav-links');

mobileMenuToggle.addEventListener('click', () => {
    navLinks.classList.toggle('active');
    mobileMenuToggle.classList.toggle('active');
});

// Close mobile menu when clicking on a link
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => {
        navLinks.classList.remove('active');
        mobileMenuToggle.classList.remove('active');
    });
});

// Close mobile menu when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.navbar')) {
        navLinks.classList.remove('active');
        mobileMenuToggle.classList.remove('active');
    }
});

// ===================================
// Link Handling (Smooth Scroll & External)
// ===================================

document.addEventListener('click', (e) => {
    const anchor = e.target.closest('a');
    if (!anchor) return;

    const href = anchor.getAttribute('href');
    if (!href) return;

    // 1. Handle Smooth Scroll for Internal Anchors
    if (href.startsWith('#') && href.length > 1) {
        const target = document.querySelector(href);
        if (target) {
            e.preventDefault();
            const offsetTop = target.offsetTop - 80; // Adjust for fixed navbar height
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    }

    // 2. Handle External Links (Open in New Tab if not specified)
    if (href.startsWith('http') && !href.includes(window.location.hostname)) {
        if (!anchor.target) {
            anchor.target = '_blank';
            anchor.rel = 'noopener noreferrer';
        }
    }
});

// ===================================
// Scroll Animation for Elements
// ===================================

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

// Observe all cards and sections for animation
const animatedElements = document.querySelectorAll('.stat-card, .session-card, .track-card, .info-box');
animatedElements.forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// ===================================
// Navbar Background on Scroll
// ===================================

const navbar = document.querySelector('.navbar');
let lastScroll = 0;

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 100) {
        navbar.style.boxShadow = '0 4px 20px rgba(38, 0, 90, 0.2)';
    } else {
        navbar.style.boxShadow = '0 2px 10px rgba(38, 0, 90, 0.1)';
    }
    
    lastScroll = currentScroll;
});

// ===================================
// Countdown Timer (Optional Enhancement)
// ===================================

function updateCountdown() {
    const eventDate = new Date('2026-04-29T09:00:00');
    const now = new Date();
    const diff = eventDate - now;
    
    if (diff > 0) {
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        
        // You can add a countdown display element in HTML if desired
        // document.getElementById('countdown').innerHTML = `${days}d ${hours}h ${minutes}m`;
    }
}

// Update countdown every minute
// setInterval(updateCountdown, 60000);
// updateCountdown();

// ===================================
// Easter Egg: Konami Code
// ===================================

let konamiCode = [];
const konamiSequence = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];

document.addEventListener('keydown', (e) => {
    konamiCode.push(e.key);
    konamiCode = konamiCode.slice(-10);
    
    if (konamiCode.join('') === konamiSequence.join('')) {
        document.body.style.animation = 'rainbow 2s infinite';
        setTimeout(() => {
            document.body.style.animation = '';
        }, 10000);
    }
});

// Add rainbow animation CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes rainbow {
        0% { filter: hue-rotate(0deg); }
        100% { filter: hue-rotate(360deg); }
    }
`;
document.head.appendChild(style);

// ===================================
// Performance: Lazy Loading Images (if you add images later)
// ===================================

if ('loading' in HTMLImageElement.prototype) {
    const images = document.querySelectorAll('img[loading="lazy"]');
    images.forEach(img => {
        img.src = img.dataset.src;
    });
} else {
    // Fallback for browsers that don't support lazy loading
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
    document.body.appendChild(script);
}

// ===================================
// Analytics Event Tracking (Optional)
// ===================================

// Track CTA button clicks
document.querySelectorAll('.btn-primary').forEach(btn => {
    btn.addEventListener('click', (e) => {
        // Add your analytics tracking here
        console.log('CTA clicked:', e.target.textContent);
    });
});

// ===================================
// Console Easter Egg for Developers
// ===================================

console.log(`%c
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   < Amadeus Engineering Days 2026 />                          ║
║                                                               ║
║   📅  April 29-30, 2026                                       ║
║   📍  7 sites across 4 continents                             ║
║   🎤  80+ sessions | 90+ speakers                             ║
║                                                               ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║   👋 Hello, curious developer!                                ║
║                                                               ║
║   Nice to see you poking around in the console!               ║
║   This site was built with 🤖 AI assistance (Claude)          ║
║   because, let's be honest, we had better things to do        ║
║   than hand-craft every pixel. Time is precious!              ║
║                                                               ║
║   Found a bug? That's a feature. 😉                           ║
║   Want to contribute? PRs welcome!                            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
`, 'font-family: monospace; color: #b650ff; font-size: 11px; line-height: 1.4;');

console.log('%c🚀 See you at Engineering Days!', 'font-size: 14px; font-weight: bold; color: #ff58ac;');

// Load and display full program in console
fetch('schedule.json')
    .then(r => r.json())
    .then(data => {
        const sessions = data.schedule.conference.days.flatMap(day => 
            Object.values(day.rooms).flat()
        );
        
        const day1 = sessions.filter(s => s.date?.startsWith('2026-04-29')).sort((a, b) => a.start.localeCompare(b.start));
        const day2 = sessions.filter(s => s.date?.startsWith('2026-04-30')).sort((a, b) => a.start.localeCompare(b.start));
        
        console.log('%c\n📋 FULL PROGRAM (expand sections below)', 'font-size: 14px; font-weight: bold; color: #ff58ac;');
        console.log('%cTip: Click the arrows ▶ to expand each day!', 'font-size: 11px; color: #aaa; font-style: italic;');
        
        console.groupCollapsed('%c📅 Day 1 — Wednesday, April 29 (' + day1.length + ' sessions)', 'font-size: 12px; font-weight: bold; color: #b650ff;');
        console.table(day1.map(s => ({
            '⏰ Time': s.start.slice(0, 5),
            '📍 Room': s.room.replace(/\s*\([^)]+\)/, ''),
            '🎤 Type': s.type,
            '📝 Title': s.title.length > 50 ? s.title.slice(0, 47) + '...' : s.title,
            '👤 Speaker': s.persons?.map(p => p.public_name).join(', ').slice(0, 30) || '-'
        })));
        console.groupEnd();
        
        console.groupCollapsed('%c📅 Day 2 — Thursday, April 30 (' + day2.length + ' sessions)', 'font-size: 12px; font-weight: bold; color: #b650ff;');
        console.table(day2.map(s => ({
            '⏰ Time': s.start.slice(0, 5),
            '📍 Room': s.room.replace(/\s*\([^)]+\)/, ''),
            '🎤 Type': s.type,
            '📝 Title': s.title.length > 50 ? s.title.slice(0, 47) + '...' : s.title,
            '👤 Speaker': s.persons?.map(p => p.public_name).join(', ').slice(0, 30) || '-'
        })));
        console.groupEnd();
        
        // Bonus: expose program as global for curious devs
        window.engineeringDays = {
            sessions: sessions,
            day1: day1,
            day2: day2,
            speakers: [...new Set(sessions.flatMap(s => s.persons?.map(p => p.public_name) || []))],
            rooms: [...new Set(sessions.map(s => s.room))],
            tracks: [...new Set(sessions.map(s => s.track))],
            search: (query) => sessions.filter(s => 
                s.title.toLowerCase().includes(query.toLowerCase()) ||
                s.persons?.some(p => p.public_name.toLowerCase().includes(query.toLowerCase()))
            )
        };
        
        console.log('%c\n💡 Pro tip: Use engineeringDays object to explore!', 'font-size: 11px; color: #b650ff;');
        console.log('%c   engineeringDays.sessions     → All sessions', 'font-size: 10px; color: #aaa; font-family: monospace;');
        console.log('%c   engineeringDays.speakers     → All speaker names', 'font-size: 10px; color: #aaa; font-family: monospace;');
        console.log('%c   engineeringDays.search("AI") → Find sessions about AI', 'font-size: 10px; color: #aaa; font-family: monospace;');
    })
    .catch(() => {
        // Silently fail if schedule.json not available (e.g., on index.html)
    });

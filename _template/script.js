// ===================================
// Event-specific JavaScript
// Add custom behavior for this event here
// ===================================

// The shared base script (script-base.js) handles:
// - Dark mode toggle
// - Mobile menu
// - Smooth scrolling
// - Scroll animations (add class "animate-on-scroll" to elements)
// - Navbar shadow on scroll

// Example: Countdown timer
function updateCountdown() {
    // Update the target date from config.json
    const eventDate = new Date('2026-06-15T09:00:00');
    const now = new Date();
    const diff = eventDate - now;

    if (diff > 0) {
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const countdown = document.getElementById('countdown');
        if (countdown) {
            countdown.textContent = `${days}d ${hours}h until the event`;
        }
    }
}

// Uncomment to enable countdown:
// setInterval(updateCountdown, 60000);
// updateCountdown();

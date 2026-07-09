// Event-specific JavaScript
// Loads config.json and renders dynamic sections (tracks, session types, stats).
// Non-technical users can edit config.json to update the website content.

document.addEventListener('DOMContentLoaded', () => {
    fetch('config.json')
        .then(r => r.json())
        .then(renderEvent)
        .catch(err => console.warn('Could not load config.json:', err));
});

function renderEvent(event) {
    // Render stats
    const statsGrid = document.getElementById('stats-grid');
    if (statsGrid && event.stats && event.stats.length) {
        statsGrid.innerHTML = event.stats.map(stat => `
            <div class="stat-card">
                <div class="stat-icon">${stat.icon}</div>
                <div class="stat-number">${stat.number}</div>
                <div class="stat-label">${stat.label}</div>
                <p class="stat-description">${stat.description}</p>
            </div>
        `).join('');
    }

    // Render session types
    const sessionsGrid = document.getElementById('sessions-grid');
    if (sessionsGrid && event.sessionTypes && event.sessionTypes.length) {
        sessionsGrid.innerHTML = event.sessionTypes.map(stype => `
            <div class="session-card">
                <div class="session-header">
                    <h3>${stype.name}</h3>
                    <span class="session-duration">${stype.duration || (stype.count ? stype.count + ' sessions' : '')}</span>
                </div>
                <p>${stype.description}</p>
            </div>
        `).join('');
    }

    // Render tracks
    const tracksGrid = document.getElementById('tracks-grid');
    if (tracksGrid && event.tracks && event.tracks.length) {
        tracksGrid.innerHTML = event.tracks.map(track => `
            <div class="track-card">
                <div class="track-icon">${track.icon}</div>
                <h3>${track.name}</h3>
                <p>${track.description}</p>
            </div>
        `).join('');
    }

    // Update description if present
    const descEl = document.getElementById('event-description');
    if (descEl && event.description) {
        descEl.textContent = event.description;
    }

    // Update locations
    const locEl = document.getElementById('event-locations');
    if (locEl && event.locations && event.locations.length) {
        locEl.innerHTML = 'Hosted at ' + event.locations.map(l => `<strong>${l}</strong>`).join(', ') + '.';
    }
}

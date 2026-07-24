// Event-specific JavaScript
// Loads config.json and renders index.html from config-driven data.

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('config.json', { cache: 'no-store' });
        const event = await response.json();
        renderEvent(event);
        await updateProgramLinks(event);
    } catch (err) {
        console.warn('Could not load config.json:', err);
    }
});

function renderEvent(event) {
    applyMetadata(event);
    renderStats(event.stats);
    renderSessionTypes(event.sessionTypes);
    renderTracks(event.tracks);
    renderAboutSection(event);
    renderCodeSnippet(event);
}

function applyMetadata(event) {
    if (event.eventName) {
        document.title = `${event.eventName} | Amadeus Events`;

        const heroTitle = document.querySelector('.hero-title');
        if (heroTitle) {
            heroTitle.textContent = event.eventName;
        }

        const navLogo = document.querySelector('.nav-brand .logo-text');
        if (navLogo) {
            navLogo.textContent = event.eventName;
        }

        const footerLogo = document.querySelector('.footer-brand .logo-text');
        if (footerLogo) {
            footerLogo.textContent = event.eventName;
        }
    }

    if (event.organizer) {
        const navByline = document.querySelector('.nav-byline');
        if (navByline) {
            navByline.textContent = `by ${event.organizer}`;
        }
    }

    if (event.tagline) {
        const heroSubtitle = document.querySelector('.hero-subtitle');
        if (heroSubtitle) {
            heroSubtitle.textContent = event.tagline;
        }

        const footerTagline = document.querySelector('.footer-tagline');
        if (footerTagline) {
            footerTagline.textContent = event.organizer ? `A ${event.organizer} Event` : 'An Amadeus Event';
        }
    }

    const dateEl = document.querySelector('.date-highlight');
    if (dateEl && event.dates && event.dates.display) {
        dateEl.textContent = event.dates.display;
    }

    if (event.contact) {
        const mailto = `mailto:${event.contact}`;
        const navContact = document.getElementById('nav-contact-link');
        const ctaContact = document.getElementById('contact-cta-link');
        const footerContact = document.getElementById('footer-contact-link');

        if (navContact) {
            navContact.href = mailto;
        }
        if (ctaContact) {
            ctaContact.href = mailto;
        }
        if (footerContact) {
            footerContact.href = mailto;
        }
    }

    if (event.dates && event.dates.start) {
        const eventYear = new Date(event.dates.start).getFullYear();
        if (!Number.isNaN(eventYear)) {
            const footerYear = document.querySelector('.footer-bottom p');
            if (footerYear) {
                footerYear.textContent = `(c) ${eventYear} Amadeus. All rights reserved.`;
            }
        }
    }
}

function renderStats(stats) {
    const statsGrid = document.getElementById('stats-grid');
    if (!statsGrid || !Array.isArray(stats) || stats.length === 0) {
        return;
    }

    statsGrid.innerHTML = stats.map(stat => `
        <div class="stat-card">
            <div class="stat-icon">${stat.icon || ''}</div>
            <div class="stat-number">${stat.number || ''}</div>
            <div class="stat-label">${stat.label || ''}</div>
            <p class="stat-description">${stat.description || ''}</p>
        </div>
    `).join('');
}

function renderSessionTypes(sessionTypes) {
    const sessionsGrid = document.getElementById('sessions-grid');
    if (!sessionsGrid || !Array.isArray(sessionTypes) || sessionTypes.length === 0) {
        return;
    }

    sessionsGrid.innerHTML = sessionTypes.map(stype => `
        <div class="session-card">
            <div class="session-header">
                <h3>${stype.name || ''}</h3>
                <span class="session-duration">${stype.duration || (stype.count ? `${stype.count} sessions` : '')}</span>
            </div>
            <p>${stype.description || ''}</p>
        </div>
    `).join('');
}

function renderTracks(tracks) {
    const tracksGrid = document.getElementById('tracks-grid');
    if (!tracksGrid || !Array.isArray(tracks) || tracks.length === 0) {
        return;
    }

    tracksGrid.innerHTML = tracks.map(track => `
        <div class="track-card">
            <div class="track-icon">${track.icon || ''}</div>
            <h3>${track.name || ''}</h3>
            <p>${track.description || ''}</p>
        </div>
    `).join('');
}

function renderAboutSection(event) {
    const descEl = document.getElementById('event-description');
    if (descEl && event.description) {
        descEl.textContent = event.description;
    }

    const locEl = document.getElementById('event-locations');
    if (locEl && Array.isArray(event.locations) && event.locations.length) {
        locEl.innerHTML = `Hosted at ${event.locations.map(location => `<strong>${location}</strong>`).join(', ')}.`;
    }
}

function renderCodeSnippet(event) {
    const codeBlock = document.querySelector('.code-content code');
    if (!codeBlock) {
        return;
    }

    const sessionCount = Array.isArray(event.sessionTypes)
        ? event.sessionTypes.reduce((total, type) => total + (Number(type.count) || 0), 0)
        : 0;

    const speakerStat = Array.isArray(event.stats)
        ? event.stats.find(stat => typeof stat.label === 'string' && stat.label.toLowerCase() === 'speakers')
        : null;
    const speakersValue = speakerStat ? speakerStat.number : 'n/a';

    const status = window.eventStatus || 'coming soon';
    codeBlock.innerHTML = `<span class="code-keyword">const</span> <span class="code-variable">event</span> = {\n  <span class="code-property">name</span>: <span class="code-string">"${event.eventName || ''}"</span>,\n  <span class="code-property">dates</span>: <span class="code-string">"${(event.dates && event.dates.display) || ''}"</span>,\n  <span class="code-property">sessions</span>: <span class="code-number">${sessionCount || 'n/a'}</span>,\n  <span class="code-property">speakers</span>: <span class="code-number">${speakersValue}</span>,\n  <span class="code-property">status</span>: <span class="code-string">"${status}"</span>\n};`;
}

function getCfpHref(event) {
    if (event.cfpUrl) {
        return event.cfpUrl;
    }
    // Fallback to mailto if cfpUrl not provided
    const contact = event.contact || 'devrel@amadeus.com';
    const eventName = event.eventName || 'Amadeus Event';
    return `mailto:${contact}?subject=${encodeURIComponent(`Talk proposal for ${eventName}`)}`;
}

function showCfpLink(cfpHref) {
    const nav = document.getElementById('cfp-nav-link');
    const hero = document.getElementById('cfp-hero-cta');
    const footer = document.getElementById('cfp-footer-link');

    if (nav) {
        nav.href = cfpHref;
        nav.textContent = 'Submit a talk';
        nav.style.display = 'inline-block';
    }
    if (hero) {
        hero.href = cfpHref;
        hero.innerHTML = 'Submit a talk (CFP) <span class="arrow">→</span>';
        hero.style.display = 'inline-block';
    }
    if (footer) {
        footer.href = cfpHref;
        footer.textContent = 'Submit a talk';
        footer.style.display = 'inline';
    }
}

function hideCfpLink() {
    const nav = document.getElementById('cfp-nav-link');
    const hero = document.getElementById('cfp-hero-cta');
    const footer = document.getElementById('cfp-footer-link');

    if (nav) nav.style.display = 'none';
    if (hero) hero.style.display = 'none';
    if (footer) footer.style.display = 'none';
}

function showProgramLink() {
    const nav = document.getElementById('program-nav-link');
    const hero = document.getElementById('program-hero-cta');
    const footer = document.getElementById('program-footer-link');

    if (nav) {
        nav.href = 'program.html';
        nav.textContent = 'Program';
        nav.style.display = 'inline-block';
    }
    if (hero) {
        hero.href = 'program.html';
        hero.innerHTML = 'View Program <span class="arrow">→</span>';
        hero.style.display = 'inline-block';
    }
    if (footer) {
        footer.href = 'program.html';
        footer.textContent = 'Program';
        footer.style.display = 'inline';
    }
}

function hideProgramLink() {
    const nav = document.getElementById('program-nav-link');
    const hero = document.getElementById('program-hero-cta');
    const footer = document.getElementById('program-footer-link');

    if (nav) nav.style.display = 'none';
    if (hero) hero.style.display = 'none';
    if (footer) footer.style.display = 'none';
}

function computeStatus(hasProgramPage, showCfp) {
    if (hasProgramPage && !showCfp) return 'ready to rock';
    if (hasProgramPage && showCfp) return 'ready & accepting';
    if (!hasProgramPage && showCfp) return 'call for papers';
    return 'coming soon';
}

async function updateProgramLinks(event) {
    const cfpHref = getCfpHref(event);
    const showCfp = event.showCfp !== false; // defaults to true if not specified

    let hasSessions = false;
    let hasProgramPage = false;

    try {
        const sessionsResponse = await fetch('sessions.json', { cache: 'no-store' });
        if (sessionsResponse.ok) {
            const sessions = await sessionsResponse.json();
            hasSessions = Array.isArray(sessions) && sessions.length > 0;
        }
    } catch (error) {
        hasSessions = false;
    }

    try {
        const programResponse = await fetch('program.html', { cache: 'no-store' });
        hasProgramPage = programResponse.ok;
    } catch (error) {
        hasProgramPage = false;
    }

    // Handle program link
    if (hasSessions && hasProgramPage) {
        showProgramLink();
    } else {
        hideProgramLink();
    }

    // Handle CFP link (independent)
    if (showCfp) {
        showCfpLink(cfpHref);
    } else {
        hideCfpLink();
    }

    // Update status in code snippet
    window.eventStatus = computeStatus(hasProgramPage, showCfp);
}

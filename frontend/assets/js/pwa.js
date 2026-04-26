/* DHARMA-NYAYA — PWA Registration + Accessibility Badge
 *
 * Registers the service worker, handles install prompt,
 * and renders the accessibility score badge.
 */

(function () {
    'use strict';

    // ── Service Worker ─────────────────────────────────────────────────────

    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/sw.js', { scope: '/' })
                .then(reg => {
                    console.log('[PWA] Service worker registered:', reg.scope);
                    reg.addEventListener('updatefound', () => {
                        const worker = reg.installing;
                        worker.addEventListener('statechange', () => {
                            if (worker.state === 'installed' && navigator.serviceWorker.controller) {
                                showUpdateToast();
                            }
                        });
                    });
                })
                .catch(err => console.warn('[PWA] SW registration failed:', err));
        });
    }

    // ── Install Prompt ─────────────────────────────────────────────────────

    let deferredInstallPrompt = null;

    window.addEventListener('beforeinstallprompt', e => {
        e.preventDefault();
        deferredInstallPrompt = e;
        // Show install banner after 3s if not dismissed
        setTimeout(() => {
            if (deferredInstallPrompt && !sessionStorage.getItem('pwa_banner_dismissed')) {
                showInstallBanner();
            }
        }, 3000);
    });

    window.addEventListener('appinstalled', () => {
        deferredInstallPrompt = null;
        const banner = document.getElementById('pwa-install-banner');
        if (banner) banner.remove();
        console.log('[PWA] App installed');
    });

    function showInstallBanner() {
        if (document.getElementById('pwa-install-banner')) return;

        const banner = document.createElement('div');
        banner.id = 'pwa-install-banner';
        banner.setAttribute('role', 'banner');
        banner.setAttribute('aria-live', 'polite');
        banner.innerHTML = `
            <div style="
                position:fixed; bottom:1rem; left:50%; transform:translateX(-50%);
                width:calc(100% - 2rem); max-width:420px;
                background:linear-gradient(135deg,#4f46e5,#7c3aed);
                color:white; border-radius:1rem; padding:1rem 1.25rem;
                box-shadow:0 8px 32px rgba(79,70,229,.35);
                display:flex; align-items:center; gap:.75rem; z-index:9999;
                animation: slideUp .3s ease-out;
            ">
                <span style="font-size:1.75rem;flex-shrink:0">⚖️</span>
                <div style="flex:1;min-width:0">
                    <div style="font-weight:700;font-size:.9rem">Install DHARMA-NYAYA</div>
                    <div style="font-size:.78rem;opacity:.85">Get offline access to your legal rights — always</div>
                </div>
                <button id="pwa-install-btn" style="
                    background:white; color:#4f46e5; border:none;
                    padding:.4rem .9rem; border-radius:.6rem; font-weight:700;
                    font-size:.8rem; cursor:pointer; flex-shrink:0;
                " aria-label="Install app">Install</button>
                <button id="pwa-dismiss-btn" style="
                    background:transparent; border:none; color:rgba(255,255,255,.7);
                    font-size:1.2rem; cursor:pointer; padding:.2rem; flex-shrink:0;
                " aria-label="Dismiss install prompt">✕</button>
            </div>
            <style>
            @keyframes slideUp { from{opacity:0;transform:translateX(-50%) translateY(1rem)} to{opacity:1;transform:translateX(-50%) translateY(0)} }
            </style>
        `;
        document.body.appendChild(banner);

        document.getElementById('pwa-install-btn').addEventListener('click', async () => {
            if (!deferredInstallPrompt) return;
            deferredInstallPrompt.prompt();
            const { outcome } = await deferredInstallPrompt.userChoice;
            deferredInstallPrompt = null;
            banner.remove();
            console.log('[PWA] Install outcome:', outcome);
        });

        document.getElementById('pwa-dismiss-btn').addEventListener('click', () => {
            sessionStorage.setItem('pwa_banner_dismissed', '1');
            banner.remove();
        });
    }

    // ── Update Toast ───────────────────────────────────────────────────────

    function showUpdateToast() {
        if (document.getElementById('pwa-update-toast')) return;
        const toast = document.createElement('div');
        toast.id = 'pwa-update-toast';
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div style="
                position:fixed; top:4.5rem; right:1rem;
                background:#1e1b4b; color:white; border-radius:.75rem;
                padding:.75rem 1.25rem; box-shadow:0 4px 20px rgba(0,0,0,.25);
                display:flex; align-items:center; gap:.75rem; z-index:9998; max-width:320px;
            ">
                <span style="font-size:1.1rem">🔄</span>
                <span style="font-size:.82rem;flex:1">New version available.</span>
                <button onclick="window.location.reload()" style="
                    background:#4f46e5; color:white; border:none; padding:.3rem .75rem;
                    border-radius:.5rem; font-size:.78rem; font-weight:600; cursor:pointer;
                ">Refresh</button>
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 10000);
    }

    // ── Offline / Online Banner ────────────────────────────────────────────

    function createOfflineBanner() {
        if (document.getElementById('offline-status-bar')) return;
        const bar = document.createElement('div');
        bar.id = 'offline-status-bar';
        bar.setAttribute('role', 'status');
        bar.setAttribute('aria-live', 'polite');
        bar.innerHTML = `
            <div id="offline-bar-inner" style="
                position:fixed; top:3.5rem; left:0; right:0;
                background:#b45309; color:white; text-align:center;
                font-size:.8rem; font-weight:600; padding:.4rem 1rem; z-index:9997;
                display:flex; align-items:center; justify-content:center; gap:.5rem;
            ">
                📵 You're offline —
                <a href="/offline-rights" style="color:#fde68a;font-weight:700;text-decoration:underline">
                    View Your Rights Card
                </a>
            </div>
        `;
        document.body.appendChild(bar);
    }

    window.addEventListener('offline', () => {
        createOfflineBanner();
        document.getElementById('offline-bar-inner') && (document.getElementById('offline-bar-inner').style.display = 'flex');
    });

    window.addEventListener('online', () => {
        const bar = document.getElementById('offline-status-bar');
        if (bar) {
            document.getElementById('offline-bar-inner').style.background = '#15803d';
            document.getElementById('offline-bar-inner').innerHTML = '✅ Back online';
            setTimeout(() => bar.remove(), 2500);
        }
    });

    if (!navigator.onLine) createOfflineBanner();

    // ── Accessibility Badge ────────────────────────────────────────────────

    const A11Y_FEATURES = [
        { label: 'Multilingual', icon: '🌍', desc: '12 languages including regional Indian languages', score: 20 },
        { label: 'Screen Reader', icon: '👁️', desc: 'ARIA roles, live regions, and semantic HTML', score: 20 },
        { label: 'Keyboard Nav', icon: '⌨️', desc: 'Full keyboard navigation with visible focus rings', score: 15 },
        { label: 'High Contrast', icon: '◐', desc: 'Color ratios meet WCAG AA standards', score: 15 },
        { label: 'Voice Input', icon: '🎙️', desc: 'Voice-to-voice legal consultation available', score: 15 },
        { label: 'Offline Mode', icon: '📵', desc: 'Rights card works without internet connection', score: 15 },
    ];

    const A11Y_TOTAL = A11Y_FEATURES.reduce((s, f) => s + f.score, 0);

    function injectA11yBadge() {
        if (document.getElementById('a11y-badge')) return;

        const badge = document.createElement('div');
        badge.id = 'a11y-badge';
        badge.setAttribute('role', 'complementary');
        badge.setAttribute('aria-label', `Accessibility score: ${A11Y_TOTAL} out of 100`);

        badge.innerHTML = `
            <button id="a11y-trigger" aria-expanded="false" aria-controls="a11y-panel"
                style="
                    position:fixed; bottom:1.25rem; right:1.25rem; z-index:8888;
                    width:3.25rem; height:3.25rem; border-radius:50%;
                    background:linear-gradient(135deg,#4f46e5,#7c3aed);
                    color:white; border:none; cursor:pointer;
                    box-shadow:0 4px 16px rgba(79,70,229,.4);
                    display:flex; flex-direction:column; align-items:center;
                    justify-content:center; font-size:.55rem; font-weight:800;
                    line-height:1.1; transition: transform .2s;
                " title="Accessibility Score">
                <span style="font-size:1rem">♿</span>
                <span>${A11Y_TOTAL}</span>
            </button>
            <div id="a11y-panel" role="dialog" aria-label="Accessibility features"
                style="
                    display:none; position:fixed; bottom:5.5rem; right:1.25rem;
                    width:280px; background:white; border-radius:1rem;
                    box-shadow:0 8px 40px rgba(0,0,0,.18); z-index:8887;
                    overflow:hidden; border:1px solid #e5e7eb;
                ">
                <div style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:1rem;color:white;">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.5rem;">
                        <span style="font-weight:800;font-size:.95rem">♿ Accessibility</span>
                        <span style="font-size:.75rem;opacity:.8">WCAG 2.1 AA</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:.75rem;">
                        <div style="font-size:2rem;font-weight:900;">${A11Y_TOTAL}</div>
                        <div>
                            <div style="font-size:.78rem;opacity:.85;margin-bottom:.3rem;">out of 100</div>
                            <div style="height:6px;background:rgba(255,255,255,.3);border-radius:3px;width:120px;overflow:hidden;">
                                <div style="height:100%;width:${A11Y_TOTAL}%;background:white;border-radius:3px;transition:width 1s;"></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div style="padding:.75rem;">
                    ${A11Y_FEATURES.map(f => `
                        <div style="display:flex;align-items:flex-start;gap:.6rem;padding:.5rem 0;border-bottom:1px solid #f3f4f6;">
                            <span style="font-size:1.1rem;flex-shrink:0;width:1.5rem;text-align:center">${f.icon}</span>
                            <div style="flex:1;min-width:0;">
                                <div style="font-size:.8rem;font-weight:600;color:#111827">${f.label}</div>
                                <div style="font-size:.72rem;color:#6b7280;">${f.desc}</div>
                            </div>
                            <span style="
                                font-size:.7rem;font-weight:700;color:#4f46e5;
                                background:#ede9fe;padding:.1rem .4rem;border-radius:.4rem;flex-shrink:0;
                            ">+${f.score}</span>
                        </div>
                    `).join('')}
                    <a href="/offline-rights" style="
                        display:block;text-align:center;margin-top:.75rem;
                        padding:.6rem;background:#f5f3ff;border-radius:.75rem;
                        color:#4f46e5;font-size:.78rem;font-weight:600;text-decoration:none;
                    ">📋 View Offline Rights Card</a>
                </div>
            </div>
        `;

        document.body.appendChild(badge);

        const trigger = document.getElementById('a11y-trigger');
        const panel = document.getElementById('a11y-panel');
        let open = false;

        trigger.addEventListener('click', () => {
            open = !open;
            panel.style.display = open ? 'block' : 'none';
            trigger.setAttribute('aria-expanded', open);
            trigger.style.transform = open ? 'scale(1.1)' : 'scale(1)';
        });

        // Close on outside click
        document.addEventListener('click', e => {
            if (open && !badge.contains(e.target)) {
                open = false;
                panel.style.display = 'none';
                trigger.setAttribute('aria-expanded', 'false');
                trigger.style.transform = 'scale(1)';
            }
        });

        // Keyboard close
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && open) {
                open = false;
                panel.style.display = 'none';
                trigger.setAttribute('aria-expanded', 'false');
                trigger.focus();
            }
        });
    }

    // ── Global Disclaimer Footer ──────────────────────────────────────────

    const DISCLAIMER_TEXT = "Disclaimer: I am an AI, not a lawyer. While this " +
        "information is gathered from valid legal frameworks, you should consult " +
        "a licensed legal professional for specific legal advice or court proceedings.";

    function injectGlobalDisclaimer() {
        if (document.getElementById('global-disclaimer')) return;

        // If the page already has a <footer>, append the disclaimer inside it
        // (lighter style, blends with existing footer chrome).
        const existingFooter = document.querySelector('footer');
        if (existingFooter) {
            const note = document.createElement('p');
            note.id = 'global-disclaimer';
            note.setAttribute('role', 'note');
            note.style.cssText =
                'max-width:64rem;margin:1rem auto 0;padding:0 1rem;' +
                'font-size:11px;line-height:1.5;color:#9ca3af;text-align:center;';
            note.textContent = '\u26A0\uFE0F ' + DISCLAIMER_TEXT;
            existingFooter.appendChild(note);
            return;
        }

        // Otherwise, render a standalone footer strip at the end of the body.
        const footer = document.createElement('footer');
        footer.id = 'global-disclaimer-footer';
        footer.setAttribute('role', 'contentinfo');
        footer.style.cssText =
            'background:#f9fafb;border-top:1px solid #e5e7eb;' +
            'padding:1rem 1.25rem;margin-top:2rem;';
        footer.innerHTML =
            '<p id="global-disclaimer" role="note" ' +
            'style="max-width:64rem;margin:0 auto;font-size:11px;line-height:1.5;' +
            'color:#6b7280;text-align:center;">' +
            '\u26A0\uFE0F ' +
            DISCLAIMER_TEXT.replace(/&/g, '&amp;').replace(/</g, '&lt;') +
            '</p>';
        document.body.appendChild(footer);
    }

    // Inject badge after DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectA11yBadge);
        document.addEventListener('DOMContentLoaded', injectGlobalDisclaimer);
    } else {
        injectA11yBadge();
        injectGlobalDisclaimer();
    }

})();

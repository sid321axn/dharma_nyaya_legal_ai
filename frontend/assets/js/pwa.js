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

    // ── Accessibility Patches (runtime WCAG 2.1 AA fixes) ─────────────────
    //
    // The HTML pages were authored across many files and ship small but
    // recurring accessibility gaps (icon-only buttons missing aria-label,
    // decorative SVGs not hidden from AT, an unlabeled language picker,
    // dynamic chat region not announced, no skip-link, etc.). Rather than
    // touch every HTML file, we patch the live DOM here so every page that
    // loads pwa.js gets the same fixes.

    function ensureFocusStyles() {
        if (document.getElementById('a11y-focus-styles')) return;
        const s = document.createElement('style');
        s.id = 'a11y-focus-styles';
        s.textContent = `
            /* WCAG 2.4.7 — Visible keyboard focus on every interactive element */
            a:focus-visible, button:focus-visible, [role="button"]:focus-visible,
            input:focus-visible, select:focus-visible, textarea:focus-visible,
            [tabindex]:focus-visible {
                outline: 3px solid #4f46e5 !important;
                outline-offset: 2px !important;
                border-radius: 4px;
            }
            .a11y-skip-link {
                position: absolute; top: -40px; left: 8px;
                background: #4f46e5; color: white; padding: .5rem 1rem;
                border-radius: 0 0 .5rem .5rem; font-weight: 700;
                z-index: 99999; text-decoration: none; font-size: .9rem;
                transition: top .15s;
            }
            .a11y-skip-link:focus { top: 0; }
            .sr-only {
                position:absolute !important; width:1px !important; height:1px !important;
                padding:0 !important; margin:-1px !important; overflow:hidden !important;
                clip:rect(0,0,0,0) !important; white-space:nowrap !important; border:0 !important;
            }

            /* WCAG 1.4.3 — Contrast (Minimum) AA fixes for shared Tailwind utilities.
               These elements appear on every page via the shared <nav> and feature cards. */

            /* Gradient brand text — provide a solid fallback color so AT/axe can
               measure contrast. Background-clip still wins visually in supporting
               browsers; the solid color only shows if clip is unsupported, but
               axe-core uses the computed color property to assess contrast. */
            .nav-glass .bg-clip-text.text-transparent,
            .bg-clip-text.text-transparent {
                color: #4338ca !important;       /* indigo-700, 7.4:1 on white */
                -webkit-text-fill-color: transparent;  /* keep gradient visible */
            }

            /* Nav links: text-gray-500 (#6b7280) on rgba(255,255,255,.85) glass
               drops below 4.5:1. Force darker gray-700 for nav links only. */
            nav.nav-glass a.text-gray-500,
            nav.nav-glass a.text-sm.text-gray-500 {
                color: #374151 !important;       /* gray-700, 10.3:1 on white */
            }
            nav.nav-glass a.text-gray-500:hover {
                color: #3730a3 !important;       /* indigo-800 */
            }

            /* Body paragraphs that use text-gray-500 for descriptive copy
               also fall short on white. Bump to gray-600. */
            p.text-gray-500 {
                color: #4b5563 !important;       /* gray-600, 7.0:1 on white */
            }

            /* Footer dark theme: text-gray-400 on bg-gray-900 is fine,
               but text-gray-500 on the same bg is 4.6:1 — borderline.
               Bump to gray-300 for safety. */
            footer.bg-gray-900 .text-gray-500 {
                color: #d1d5db !important;       /* gray-300 */
            }
        `;
        document.head.appendChild(s);
    }

    function addSkipLink() {
        if (document.querySelector('.a11y-skip-link')) return;
        const main = document.querySelector('main, [role="main"], #main, #content');
        if (main && !main.id) main.id = 'main-content';
        const targetId = main ? main.id : null;
        if (!targetId) return;
        const a = document.createElement('a');
        a.href = '#' + targetId;
        a.className = 'a11y-skip-link';
        a.textContent = 'Skip to main content';
        document.body.insertBefore(a, document.body.firstChild);
    }

    function patchHtmlLang() {
        // Reflect the saved UI language on <html lang> for screen readers.
        try {
            const lang = localStorage.getItem('lang') || document.documentElement.lang || 'en';
            if (lang) document.documentElement.lang = lang;
        } catch (_) { /* storage blocked */ }
    }

    // Known icon-only button IDs that never carry a title in the HTML.
    const KNOWN_BTN_LABELS = {
        'theme-toggle':   'Toggle theme',
        'mic-btn':        'Toggle voice input',
        'mute-btn':       'Toggle mute',
        'pdf-btn':        'Download PDF report',
        'upload-btn':     'Upload document',
        'send-btn':       'Send message',
    };

    function patchIconButtons(root) {
        // 1.1.1 / 4.1.2 — Icon-only buttons need an accessible name.
        // Priority: aria-label > aria-labelledby > visible text > title > known-ID map > id slug.
        root.querySelectorAll('button, a[role="button"]').forEach(btn => {
            const text = (btn.textContent || '').replace(/\s+/g, '').trim();
            const hasName = btn.hasAttribute('aria-label') ||
                            btn.hasAttribute('aria-labelledby') ||
                            text.length > 1;
            if (hasName) return;  // already labelled
            // 1. promote title
            if (btn.title) { btn.setAttribute('aria-label', btn.title); return; }
            // 2. known-ID lookup
            if (btn.id && KNOWN_BTN_LABELS[btn.id]) {
                btn.setAttribute('aria-label', KNOWN_BTN_LABELS[btn.id]); return;
            }
            // 3. humanise id as last resort (e.g. "theme-toggle" → "Theme toggle")
            if (btn.id) {
                const label = btn.id.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                btn.setAttribute('aria-label', label);
            }


            btn.querySelectorAll('svg').forEach(svg => {
                if (!svg.hasAttribute('aria-hidden') && !svg.hasAttribute('aria-label')) {
                    svg.setAttribute('aria-hidden', 'true');
                    svg.setAttribute('focusable', 'false');
                }
            });
        });

        // Standalone SVGs anywhere → hide from AT unless explicitly labelled.
        root.querySelectorAll('svg:not([aria-label]):not([aria-labelledby]):not([role="img"])').forEach(svg => {
            if (!svg.hasAttribute('aria-hidden')) {
                svg.setAttribute('aria-hidden', 'true');
                svg.setAttribute('focusable', 'false');
            }
        });
    }

    function patchFormControls(root) {
        // 1.3.1 / 3.3.2 — Every form control needs a programmatic label.
        const named = el => el.hasAttribute('aria-label') ||
                            el.hasAttribute('aria-labelledby') ||
                            el.hasAttribute('title') ||
                            (el.id && root.querySelector(`label[for="${CSS.escape(el.id)}"]`)) ||
                            el.closest('label');

        root.querySelectorAll('select, input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea').forEach(el => {
            if (named(el)) return;
            // Heuristic: language picker → "Language"
            if (el.id === 'lang-select' || /lang/i.test(el.name || '')) {
                el.setAttribute('aria-label', 'Language');
                return;
            }
            const ph = el.getAttribute('placeholder');
            if (ph) { el.setAttribute('aria-label', ph); return; }
            el.setAttribute('aria-label', el.id || el.name || 'Input');
        });
    }

    function patchLandmarks(root) {
        // 1.3.1 — Announce dynamic chat container and drop zone.
        const chat = root.querySelector('#chat-messages');
        if (chat && !chat.hasAttribute('role')) {
            chat.setAttribute('role', 'log');
            chat.setAttribute('aria-live', 'polite');
            chat.setAttribute('aria-relevant', 'additions');
            chat.setAttribute('aria-label', 'Chat conversation');
        }
        const drop = root.querySelector('#drop-zone');
        if (drop && !drop.hasAttribute('aria-label')) {
            drop.setAttribute('role', 'button');
            drop.setAttribute('tabindex', '0');
            drop.setAttribute('aria-label', 'Upload a document. Click or press Enter to choose a file.');
            drop.addEventListener('keydown', e => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    root.querySelector('#file-input')?.click();
                }
            });
        }
        // Ensure exactly one <main> landmark exists.
        if (!root.querySelector('main, [role="main"]')) {
            const candidate = root.querySelector('section, article, .container, .max-w-7xl');
            if (candidate) candidate.setAttribute('role', 'main');
        }
    }

    function patchToggleButtons(root) {
        // 4.1.2 — Toggles should expose state via aria-pressed.
        ['theme-toggle', 'mute-btn', 'mic-btn'].forEach(id => {
            const el = root.getElementById ? root.getElementById(id) : document.getElementById(id);
            if (!el || el.dataset.a11yToggle === '1') return;
            el.dataset.a11yToggle = '1';
            if (!el.hasAttribute('aria-pressed')) el.setAttribute('aria-pressed', 'false');
            el.addEventListener('click', () => {
                const cur = el.getAttribute('aria-pressed') === 'true';
                el.setAttribute('aria-pressed', cur ? 'false' : 'true');
            });
        });
    }

    function applyA11yPatches() {
        ensureFocusStyles();
        patchHtmlLang();
        addSkipLink();
        patchIconButtons(document);
        patchFormControls(document);
        patchLandmarks(document);
        patchToggleButtons(document);

        // Re-run on dynamic DOM mutations (chat bubbles, modals, etc.)
        const mo = new MutationObserver(muts => {
            for (const m of muts) {
                m.addedNodes.forEach(node => {
                    if (node.nodeType !== 1) return;
                    patchIconButtons(node.parentNode || document);
                    patchFormControls(node.parentNode || document);
                });
            }
        });
        mo.observe(document.body, { childList: true, subtree: true });
    }

    // ── Accessibility Badge (live axe-core audit, no fake score) ──────────

    function injectA11yBadge() {
        if (document.getElementById('a11y-badge')) return;

        const badge = document.createElement('div');
        badge.id = 'a11y-badge';
        badge.setAttribute('role', 'complementary');
        badge.setAttribute('aria-label', 'Accessibility tools');

        badge.innerHTML = `
            <button id="a11y-trigger" type="button"
                aria-expanded="false" aria-controls="a11y-panel"
                aria-label="Open accessibility tools"
                style="
                    position:fixed; bottom:1.25rem; right:1.25rem; z-index:8888;
                    width:3.25rem; height:3.25rem; border-radius:50%;
                    background:linear-gradient(135deg,#4f46e5,#7c3aed);
                    color:white; border:none; cursor:pointer;
                    box-shadow:0 4px 16px rgba(79,70,229,.4);
                    display:flex; flex-direction:column; align-items:center;
                    justify-content:center; font-size:.6rem; font-weight:800;
                    line-height:1.1; transition: transform .2s;
                ">
                <span aria-hidden="true" style="font-size:1.1rem">♿</span>
                <span aria-hidden="true">A11y</span>
            </button>
            <div id="a11y-panel" role="dialog" aria-modal="false"
                aria-label="Accessibility tools and live audit"
                style="
                    display:none; position:fixed; bottom:5.5rem; right:1.25rem;
                    width:min(420px, calc(100vw - 2.5rem)); max-height:80vh; overflow:auto;
                    background:white; border-radius:1rem;
                    box-shadow:0 8px 40px rgba(0,0,0,.18); z-index:8887;
                    border:1px solid #e5e7eb;
                ">
                <div style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:1rem;color:white;">
                    <div style="display:flex;align-items:center;justify-content:space-between;">
                        <span style="font-weight:800;font-size:.95rem">
                            <span aria-hidden="true">♿</span> Accessibility
                        </span>
                        <span style="font-size:.72rem;opacity:.85">Targets WCAG 2.1 AA</span>
                    </div>
                    <p style="margin:.5rem 0 0;font-size:.74rem;opacity:.9;line-height:1.45;">
                        Run a live audit of this page using the open-source
                        <strong>axe-core</strong> engine (Deque Systems).
                    </p>
                </div>
                <div style="padding:.85rem;">
                    <button id="a11y-run-audit" type="button"
                        style="width:100%;padding:.65rem;border-radius:.6rem;border:none;
                               background:#4f46e5;color:white;font-weight:700;font-size:.85rem;
                               cursor:pointer;">
                        Run live audit on this page
                    </button>
                    <div id="a11y-audit-result" aria-live="polite"
                        style="margin-top:.75rem;font-size:.78rem;color:#374151;"></div>

                    <div style="margin-top:.85rem;padding-top:.75rem;border-top:1px solid #f3f4f6;">
                        <div style="font-size:.78rem;font-weight:700;color:#111827;margin-bottom:.4rem;">
                            Built-in accessibility features
                        </div>
                        <ul style="list-style:none;padding:0;margin:0;font-size:.74rem;color:#4b5563;line-height:1.7;">
                            <li>• Skip-to-main-content link (Tab on load)</li>
                            <li>• Visible keyboard focus rings (WCAG 2.4.7)</li>
                            <li>• ARIA live regions for chat &amp; toasts</li>
                            <li>• Labelled icon buttons &amp; language picker</li>
                            <li>• 12 languages incl. Indian regional</li>
                            <li>• Voice input (mic) on chat &amp; voice pages</li>
                            <li>• Offline rights card &amp; install banner</li>
                        </ul>
                        <a href="/offline-rights" style="
                            display:block;text-align:center;margin-top:.75rem;
                            padding:.55rem;background:#f5f3ff;border-radius:.6rem;
                            color:#4f46e5;font-size:.76rem;font-weight:600;text-decoration:none;
                        ">View Offline Rights Card</a>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(badge);

        const trigger = document.getElementById('a11y-trigger');
        const panel = document.getElementById('a11y-panel');
        const runBtn = document.getElementById('a11y-run-audit');
        const result = document.getElementById('a11y-audit-result');
        let open = false;

        const setOpen = (val) => {
            open = val;
            panel.style.display = open ? 'block' : 'none';
            trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
            trigger.style.transform = open ? 'scale(1.08)' : 'scale(1)';
        };

        trigger.addEventListener('click', e => { e.stopPropagation(); setOpen(!open); });

        document.addEventListener('click', e => {
            if (open && !badge.contains(e.target)) setOpen(false);
        });
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && open) { setOpen(false); trigger.focus(); }
        });

        runBtn.addEventListener('click', () => runLiveA11yAudit(runBtn, result));
    }

    // Lazy-load axe-core from CDN and run a real WCAG 2.1 AA audit on
    // the current page. The score reported here is computed from actual
    // findings, not a hardcoded constant.
    async function runLiveA11yAudit(btn, result) {
        btn.disabled = true;
        const originalLabel = btn.textContent;
        btn.textContent = 'Loading axe-core…';
        result.innerHTML = '';

        try {
            if (!window.axe) {
                await new Promise((resolve, reject) => {
                    const s = document.createElement('script');
                    // axe-core official CDN build (Deque Systems, MIT license).
                    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.0/axe.min.js';
                    s.onload = resolve;
                    s.onerror = () => reject(new Error('Could not load axe-core (offline?)'));
                    document.head.appendChild(s);
                });
            }
            btn.textContent = 'Auditing…';

            // Exclude the badge itself so its own DOM doesn't skew results.
            const ctx = { exclude: [['#a11y-badge'], ['#feedback-widget-root']] };
            const opts = { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } };
            const r = await window.axe.run(ctx, opts);

            const violations = r.violations.length;
            const passes = r.passes.length;
            const incomplete = r.incomplete.length;
            const total = violations + passes;
            const score = total === 0 ? 100 : Math.round((passes / total) * 100);

            const color = violations === 0 ? '#15803d' : violations <= 3 ? '#b45309' : '#b91c1c';
            const escapeHtml = str => String(str).replace(/[&<>"']/g, c => (
                { '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]
            ));
            const list = r.violations.slice(0, 6).map(v => {
                const nodeDetails = v.nodes.slice(0, 3).map(n => {
                    const sel = Array.isArray(n.target) ? n.target.join(' ') : String(n.target);
                    const summary = (n.failureSummary || '').split('\n').slice(0, 3).join(' ');
                    const html = (n.html || '').slice(0, 160);
                    return `
                        <div style="margin-top:.35rem;padding:.4rem .5rem;background:#fef2f2;border-left:3px solid ${color};border-radius:.3rem;">
                            <div style="font-family:ui-monospace,monospace;font-size:.7rem;color:#991b1b;word-break:break-all;">${escapeHtml(sel)}</div>
                            <div style="font-family:ui-monospace,monospace;font-size:.68rem;color:#4b5563;margin-top:.2rem;word-break:break-all;">${escapeHtml(html)}</div>
                            ${summary ? `<div style="font-size:.68rem;color:#374151;margin-top:.2rem;">${escapeHtml(summary)}</div>` : ''}
                        </div>`;
                }).join('');
                return `
                    <li style="margin:.5rem 0;">
                        <strong style="color:${color}">${v.impact || 'minor'}</strong> —
                        ${v.help} <span style="color:#6b7280">(${v.nodes.length} node${v.nodes.length>1?'s':''})</span>
                        <a href="${v.helpUrl}" target="_blank" rel="noopener"
                            style="color:#4f46e5;font-size:.72rem;">learn&nbsp;more</a>
                        ${nodeDetails}
                    </li>
                `;
            }).join('');

            result.innerHTML = `
                <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:.5rem;">
                    <div style="font-size:1.6rem;font-weight:900;color:${color};line-height:1;">${score}</div>
                    <div style="font-size:.75rem;color:#4b5563;">
                        ${passes} passed · <strong style="color:${color}">${violations} failed</strong>
                        ${incomplete ? ` · ${incomplete} need review` : ''}
                    </div>
                </div>
                ${violations === 0
                    ? '<div style="color:#15803d;font-weight:600;">✓ No WCAG 2.1 A/AA violations detected on this page.</div>'
                    : `<ul style="list-style:none;padding:0;margin:0;font-size:.76rem;color:#374151;">${list}</ul>`}
                <div style="margin-top:.6rem;font-size:.75rem;color:#4b5563;">
                    Engine: axe-core ${window.axe.version || ''}. Audit each route separately.
                </div>
            `;
        } catch (err) {
            result.innerHTML = `<div style="color:#b91c1c;">Audit failed: ${err.message}</div>`;
        } finally {
            btn.disabled = false;
            btn.textContent = originalLabel;
        }
    }

    // ── Global Disclaimer Footer ──────────────────────────────────────────

    const DISCLAIMER_TEXT = "Disclaimer: I am an AI, not a lawyer. While this " +
        "information is gathered from valid legal frameworks, you should consult " +
        "a licensed legal professional for specific legal advice or court proceedings.";

    function injectGlobalDisclaimer() {
        if (document.getElementById('global-disclaimer')) return;

        // If the page already has a <footer>, append the disclaimer inside it.
        // We render it in a self-contained light pill so contrast (WCAG 1.4.3)
        // is preserved regardless of the parent footer's background (some pages
        // ship a dark bg-gray-900 footer where #4b5563 text would only hit
        // 2.3:1).
        const existingFooter = document.querySelector('footer');
        if (existingFooter) {
            const note = document.createElement('p');
            note.id = 'global-disclaimer';
            note.setAttribute('role', 'note');
            note.style.cssText =
                'max-width:64rem;margin:1rem auto 0;padding:.6rem 1rem;' +
                'background:#f9fafb;border:1px solid #e5e7eb;border-radius:.6rem;' +
                'font-size:12px;line-height:1.5;color:#1f2937;text-align:center;';
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
            'style="max-width:64rem;margin:0 auto;font-size:12px;line-height:1.5;' +
            'color:#4b5563;text-align:center;">' +
            '\u26A0\uFE0F ' +
            DISCLAIMER_TEXT.replace(/&/g, '&amp;').replace(/</g, '&lt;') +
            '</p>';
        document.body.appendChild(footer);
    }

    // ── Responsive Mobile Nav ──────────────────────────────────────────────
    //
    // Pages share a `<nav class="nav-glass">` with an inner flex row containing
    // a brand block followed by a long list of links + a language picker. On
    // small screens that row overflows horizontally and gets clipped. We
    // collapse the link group behind a hamburger button on viewports
    // ≤ 1024px without touching individual HTML pages.

    function injectMobileNavStyles() {
        if (document.getElementById('mobile-nav-styles')) return;
        const style = document.createElement('style');
        style.id = 'mobile-nav-styles';
        style.textContent = `
            #mobile-nav-toggle { display: none; }
            @media (max-width: 1024px) {
                nav.nav-glass [data-mobile-links] {
                    display: none !important;
                }
                nav.nav-glass.mobile-open [data-mobile-links] {
                    display: flex !important;
                    flex-direction: column;
                    align-items: stretch;
                    position: absolute;
                    top: 100%;
                    left: 0;
                    right: 0;
                    background: white;
                    padding: 0.75rem 1rem 1rem;
                    gap: 0.25rem;
                    border-top: 1px solid #e5e7eb;
                    box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
                    max-height: calc(100vh - 4rem);
                    overflow-y: auto;
                    z-index: 60;
                }
                nav.nav-glass.mobile-open [data-mobile-links] > * {
                    width: 100%;
                    margin: 0 !important;
                    padding: 0.65rem 0.5rem;
                    border-radius: 0.5rem;
                }
                nav.nav-glass.mobile-open [data-mobile-links] > a:hover,
                nav.nav-glass.mobile-open [data-mobile-links] > button:hover {
                    background: #f5f3ff;
                }
                nav.nav-glass.mobile-open [data-mobile-links] select {
                    width: 100%;
                }
                nav.nav-glass {
                    position: relative;
                }
                #mobile-nav-toggle {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 2.5rem;
                    height: 2.5rem;
                    border-radius: 0.6rem;
                    border: 1px solid #e5e7eb;
                    background: white;
                    color: #4f46e5;
                    cursor: pointer;
                    margin-left: auto;
                }
                #mobile-nav-toggle:focus-visible {
                    outline: 2px solid #4f46e5;
                    outline-offset: 2px;
                }
            }
        `;
        document.head.appendChild(style);
    }

    function injectMobileNav() {
        injectMobileNavStyles();

        document.querySelectorAll('nav.nav-glass').forEach(nav => {
            if (nav.dataset.mobileEnhanced === '1') return;
            nav.dataset.mobileEnhanced = '1';

            // The inner row is the first descendant flex with at least 2 children.
            const innerRow = nav.querySelector('.flex.items-center.justify-between');
            if (!innerRow || innerRow.children.length < 2) return;

            // Treat every direct child after the first (brand) as the "links" group.
            // If there are exactly 2 children and the second is itself a flex
            // container, mark that as the links group; otherwise wrap the rest.
            let linksGroup = innerRow.children[1];
            const looksLikeFlex =
                linksGroup &&
                /flex/.test(linksGroup.className || '') &&
                innerRow.children.length === 2;

            if (!looksLikeFlex) {
                linksGroup = document.createElement('div');
                linksGroup.className = 'flex items-center space-x-3';
                while (innerRow.children.length > 1) {
                    linksGroup.appendChild(innerRow.children[1]);
                }
                innerRow.appendChild(linksGroup);
            }
            linksGroup.setAttribute('data-mobile-links', '');

            // Hamburger button
            const btn = document.createElement('button');
            btn.id = 'mobile-nav-toggle';
            btn.type = 'button';
            btn.setAttribute('aria-label', 'Toggle navigation menu');
            btn.setAttribute('aria-expanded', 'false');
            btn.innerHTML =
                '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">' +
                '<line x1="4" y1="7"  x2="20" y2="7"/>' +
                '<line x1="4" y1="12" x2="20" y2="12"/>' +
                '<line x1="4" y1="17" x2="20" y2="17"/>' +
                '</svg>';
            innerRow.appendChild(btn);

            const close = () => {
                nav.classList.remove('mobile-open');
                btn.setAttribute('aria-expanded', 'false');
            };
            const toggle = () => {
                const open = nav.classList.toggle('mobile-open');
                btn.setAttribute('aria-expanded', open ? 'true' : 'false');
            };
            btn.addEventListener('click', e => { e.stopPropagation(); toggle(); });

            // Close when clicking outside or following a link
            document.addEventListener('click', e => {
                if (!nav.classList.contains('mobile-open')) return;
                if (!nav.contains(e.target)) close();
            });
            linksGroup.addEventListener('click', e => {
                if (e.target.closest('a')) close();
            });
            window.addEventListener('resize', () => {
                if (window.innerWidth > 1024) close();
            });
            document.addEventListener('keydown', e => {
                if (e.key === 'Escape') close();
            });
        });
    }

    // Inject badge + a11y patches after DOM is ready
    function bootstrapPwaUi() {
        applyA11yPatches();   // run BEFORE the badge so its own DOM is patched too
        injectA11yBadge();
        injectGlobalDisclaimer();
        injectFeedbackWidget();
        injectMobileNav();
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootstrapPwaUi);
    } else {
        bootstrapPwaUi();
    }

    // ── Feedback Widget ────────────────────────────────────────────────────
    //
    // Floating button (bottom-left, away from the a11y badge on the right)
    // that opens a modal with: name, 5-star rating, message, optional location.
    // Posts to /api/feedback. Page identifier comes from window.location.pathname.

    function injectFeedbackWidget() {
        if (document.getElementById('feedback-fab')) return;

        const wrap = document.createElement('div');
        wrap.id = 'feedback-widget-root';
        wrap.innerHTML = `
            <button id="feedback-fab" type="button" aria-haspopup="dialog"
                aria-controls="feedback-modal" aria-label="Send feedback"
                title="Send feedback"
                style="
                    position:fixed; bottom:5rem; left:1.25rem; z-index:8890;
                    height:3.25rem; padding:0 1rem; border-radius:9999px;
                    background:linear-gradient(135deg,#f59e0b,#ef4444);
                    color:white; border:none; cursor:pointer; font-weight:700;
                    font-size:.82rem; display:flex; align-items:center; gap:.45rem;
                    box-shadow:0 4px 16px rgba(239,68,68,.4);
                    transition: transform .15s;
                ">
                <span style="font-size:1.05rem">💬</span>
                <span>Feedback</span>
            </button>

            <div id="feedback-modal" role="dialog" aria-modal="true"
                aria-labelledby="feedback-modal-title"
                style="
                    position:fixed; inset:0; z-index:9999;
                    background:rgba(15,23,42,.55);
                    display:none; align-items:center; justify-content:center;
                    padding:1rem;
                ">
                <form id="feedback-form" novalidate
                    style="
                        background:white; border-radius:1rem; width:100%;
                        max-width:440px; max-height:90vh; overflow:auto;
                        box-shadow:0 20px 50px rgba(0,0,0,.25);
                    ">
                    <div style="
                        padding:1rem 1.25rem;
                        background:linear-gradient(135deg,#f59e0b,#ef4444);
                        color:white; display:flex; align-items:center;
                        justify-content:space-between;
                    ">
                        <h2 id="feedback-modal-title"
                            style="margin:0;font-size:1rem;font-weight:800;">
                            💬 Share your feedback
                        </h2>
                        <button type="button" id="feedback-close"
                            aria-label="Close feedback"
                            style="background:transparent;border:none;color:white;
                                font-size:1.25rem;cursor:pointer;line-height:1;">✕</button>
                    </div>

                    <div style="padding:1rem 1.25rem;display:flex;flex-direction:column;gap:.75rem;">
                        <label style="display:flex;flex-direction:column;gap:.25rem;font-size:.8rem;color:#374151;font-weight:600;">
                            Your name <span style="color:#4b5563;font-weight:400;">(optional)</span>
                            <input id="fb-name" type="text" maxlength="120" autocomplete="name"
                                style="padding:.55rem .75rem;border:1px solid #e5e7eb;border-radius:.5rem;font-size:.88rem;">
                        </label>

                        <div>
                            <div style="font-size:.8rem;color:#374151;font-weight:600;margin-bottom:.25rem;">
                                Rating <span style="color:#ef4444">*</span>
                            </div>
                            <div id="fb-stars" role="radiogroup" aria-label="Star rating"
                                style="display:flex;gap:.25rem;font-size:1.6rem;cursor:pointer;user-select:none;">
                                ${[1,2,3,4,5].map(n => `
                                    <span data-star="${n}" role="radio" aria-checked="false"
                                        tabindex="0"
                                        style="color:#d1d5db;transition:color .1s;">★</span>
                                `).join('')}
                            </div>
                        </div>

                        <label style="display:flex;flex-direction:column;gap:.25rem;font-size:.8rem;color:#374151;font-weight:600;">
                            Your feedback
                            <textarea id="fb-message" rows="4" maxlength="4000"
                                placeholder="What worked well? What could be better?"
                                style="padding:.55rem .75rem;border:1px solid #e5e7eb;border-radius:.5rem;font-size:.88rem;resize:vertical;"></textarea>
                        </label>

                        <div style="display:flex;align-items:center;gap:.5rem;font-size:.78rem;color:#4b5563;">
                            <input id="fb-loc-opt" type="checkbox" style="width:1rem;height:1rem;">
                            <label for="fb-loc-opt">Attach my location (helps us improve regional support)</label>
                        </div>
                        <div id="fb-loc-status"
                            style="font-size:.75rem;color:#4b5563;min-height:1rem;"></div>

                        <div id="fb-error" role="alert"
                            style="display:none;color:#b91c1c;background:#fef2f2;border:1px solid #fecaca;padding:.55rem .75rem;border-radius:.5rem;font-size:.8rem;"></div>

                        <div style="display:flex;gap:.5rem;justify-content:flex-end;margin-top:.25rem;">
                            <button type="button" id="fb-cancel"
                                style="padding:.55rem 1rem;border-radius:.5rem;border:1px solid #e5e7eb;background:white;color:#374151;font-weight:600;cursor:pointer;font-size:.85rem;">
                                Cancel
                            </button>
                            <button type="submit" id="fb-submit"
                                style="padding:.55rem 1.1rem;border-radius:.5rem;border:none;background:linear-gradient(135deg,#f59e0b,#ef4444);color:white;font-weight:700;cursor:pointer;font-size:.85rem;">
                                Send
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        `;
        document.body.appendChild(wrap);

        const fab = document.getElementById('feedback-fab');
        const modal = document.getElementById('feedback-modal');
        const closeBtn = document.getElementById('feedback-close');
        const cancelBtn = document.getElementById('fb-cancel');
        const form = document.getElementById('feedback-form');
        const stars = document.querySelectorAll('#fb-stars [data-star]');
        const errorBox = document.getElementById('fb-error');
        const locOpt = document.getElementById('fb-loc-opt');
        const locStatus = document.getElementById('fb-loc-status');
        const submitBtn = document.getElementById('fb-submit');

        let rating = 0;
        let coords = null;
        let locationLabel = '';

        function paintStars(active) {
            stars.forEach(s => {
                const n = parseInt(s.dataset.star, 10);
                s.style.color = n <= active ? '#f59e0b' : '#d1d5db';
                s.setAttribute('aria-checked', n === rating ? 'true' : 'false');
            });
        }
        stars.forEach(s => {
            s.addEventListener('mouseenter', () => paintStars(parseInt(s.dataset.star, 10)));
            s.addEventListener('mouseleave', () => paintStars(rating));
            s.addEventListener('click', () => { rating = parseInt(s.dataset.star, 10); paintStars(rating); });
            s.addEventListener('keydown', e => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    rating = parseInt(s.dataset.star, 10); paintStars(rating);
                }
            });
        });

        function openModal() {
            errorBox.style.display = 'none';
            modal.style.display = 'flex';
            fab.setAttribute('aria-expanded', 'true');
            setTimeout(() => document.getElementById('fb-name')?.focus(), 50);
        }
        function closeModal() {
            modal.style.display = 'none';
            fab.setAttribute('aria-expanded', 'false');
        }
        fab.addEventListener('click', openModal);
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
        document.addEventListener('keydown', e => { if (e.key === 'Escape' && modal.style.display !== 'none') closeModal(); });

        locOpt.addEventListener('change', async () => {
            if (!locOpt.checked) {
                coords = null; locationLabel = '';
                locStatus.textContent = '';
                return;
            }
            if (!('geolocation' in navigator)) {
                locStatus.textContent = 'Geolocation not supported in this browser.';
                locOpt.checked = false;
                return;
            }
            locStatus.textContent = 'Detecting location…';
            navigator.geolocation.getCurrentPosition(async (pos) => {
                coords = { lat: pos.coords.latitude, lon: pos.coords.longitude };
                locationLabel = `${coords.lat.toFixed(3)}, ${coords.lon.toFixed(3)}`;
                // Best-effort reverse geocode (free, no key) — silently ignore on failure
                try {
                    const r = await fetch(
                        `https://nominatim.openstreetmap.org/reverse?lat=${coords.lat}&lon=${coords.lon}&format=json&zoom=10`,
                        { headers: { 'Accept': 'application/json' } }
                    );
                    if (r.ok) {
                        const j = await r.json();
                        if (j && j.display_name) locationLabel = j.display_name.slice(0, 240);
                    }
                } catch (_) { /* keep coords-only label */ }
                locStatus.textContent = `📍 ${locationLabel}`;
            }, (err) => {
                locStatus.textContent = `Could not detect location (${err.message}).`;
                locOpt.checked = false;
            }, { timeout: 8000, maximumAge: 60000 });
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorBox.style.display = 'none';

            if (rating < 1 || rating > 5) {
                errorBox.textContent = 'Please select a star rating.';
                errorBox.style.display = 'block';
                return;
            }

            const payload = {
                name: document.getElementById('fb-name').value.trim() || null,
                page: window.location.pathname || null,
                rating,
                message: document.getElementById('fb-message').value.trim() || null,
                location: locationLabel || null,
                latitude: coords ? coords.lat : null,
                longitude: coords ? coords.lon : null,
            };

            submitBtn.disabled = true;
            submitBtn.textContent = 'Sending…';
            try {
                const r = await fetch('/api/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (!r.ok) {
                    const detail = await r.text().catch(() => '');
                    throw new Error(`HTTP ${r.status} ${detail}`.trim());
                }
                // success
                form.reset();
                rating = 0; coords = null; locationLabel = '';
                paintStars(0);
                locStatus.textContent = '';
                closeModal();
                showFeedbackToast();
            } catch (err) {
                errorBox.textContent = `Could not send feedback. ${err.message || ''}`.trim();
                errorBox.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Send';
            }
        });
    }

    function showFeedbackToast() {
        const toast = document.createElement('div');
        toast.setAttribute('role', 'status');
        toast.setAttribute('aria-live', 'polite');
        toast.style.cssText =
            'position:fixed;bottom:1.25rem;left:50%;transform:translateX(-50%);' +
            'background:#10b981;color:white;font-weight:700;font-size:.85rem;' +
            'padding:.6rem 1rem;border-radius:9999px;z-index:9999;' +
            'box-shadow:0 8px 24px rgba(16,185,129,.4);';
        toast.textContent = '✅ Thanks for your feedback!';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3500);
    }

})();

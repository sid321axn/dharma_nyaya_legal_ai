/* DHARMA-NYAYA — Connectivity-aware offline chat queue + offline-mode entry
 *
 * Responsibilities:
 *  1. Detect real-time online/offline status (navigator.onLine + reachability ping).
 *     The status is exposed via window.DNNet but it does NOT mutate the menu —
 *     transient reachability failures must never hide nav items.
 *  2. Show a small floating "Offline Mode" pill that lets the user jump to the
 *     offline guides / rights card at any time. The pill is dismissible.
 *  3. Provide a global offline chat queue (localStorage backed):
 *       - window.queueOfflineChat(message, language)  -> returns queue id
 *       - On 'online' the queue is flushed to /api/chat, responses are stored,
 *         a desktop / in-app notification fires and (if user is on /chat)
 *         responses are appended to the conversation directly.
 *       - Duplicate submissions are prevented via a queued-id map and a
 *         single-flight flush lock.
 */
(function () {
    'use strict';

    // ── Connectivity ──────────────────────────────────────────────────────

    const REACHABILITY_URL = '/manifest.json'; // small, same-origin
    const REACHABILITY_INTERVAL_MS = 30000;    // 30 s background poll
    let _isOnline = navigator.onLine;
    const _listeners = new Set();

    function notify() {
        _listeners.forEach(fn => { try { fn(_isOnline); } catch (e) {} });
    }

    function setOnline(state) {
        if (state === _isOnline) return;
        _isOnline = state;
        notify();
        if (state) flushChatQueue();
    }

    // We require TWO consecutive failures before declaring "offline" so a single
    // flaky request never flips the UI on a healthy connection.
    let _consecutiveFailures = 0;
    async function probeReachability() {
        try {
            const ctrl = new AbortController();
            const t = setTimeout(() => ctrl.abort(), 5000);
            // No cache-buster: we WANT the service-worker cache hit when present,
            // because that proves the page is at least functional. A real network
            // failure still surfaces because the SW falls through on cache miss.
            const resp = await fetch(REACHABILITY_URL,
                { method: 'GET', cache: 'no-store', signal: ctrl.signal });
            clearTimeout(t);
            if (resp && resp.ok) {
                _consecutiveFailures = 0;
                setOnline(true);
            } else {
                _consecutiveFailures++;
                if (_consecutiveFailures >= 2) setOnline(false);
            }
        } catch (e) {
            _consecutiveFailures++;
            if (_consecutiveFailures >= 2) setOnline(false);
        }
    }

    window.addEventListener('online',  () => { _consecutiveFailures = 0; setOnline(true);  });
    window.addEventListener('offline', () => { setOnline(false); });
    setInterval(probeReachability, REACHABILITY_INTERVAL_MS);

    // Public connectivity API
    window.DNNet = {
        isOnline: () => _isOnline,
        onChange: (fn) => { _listeners.add(fn); return () => _listeners.delete(fn); },
        forceProbe: probeReachability,
    };

    // ── "Offline Mode" entry pill ─────────────────────────────────────────

    const OFFLINE_PAGES = new Set(['/offline-guides', '/offline-rights']);
    function currentPath() {
        return (location.pathname.replace(/\/+$/, '') || '/');
    }

    // Always hide the "Offline Guides" / "Offline Rights" entries from the
    // top navigation — the floating pill below is the canonical entry point.
    // (Hiding them has nothing to do with current connectivity, so the menu
    // never reshuffles based on transient network state.)
    function hideOfflineNavLinks() {
        const anchors = document.querySelectorAll('nav a[href]');
        anchors.forEach(a => {
            const href = a.getAttribute('href') || '';
            if (href === '/offline-guides' || href === '/offline-rights') {
                a.style.display = 'none';
            }
        });
    }

    function injectOfflinePill() {
        if (document.getElementById('offline-mode-pill')) return;
        if (OFFLINE_PAGES.has(currentPath())) return;            // not needed there
        if (sessionStorage.getItem('offline_pill_dismissed')) return;

        const wrap = document.createElement('div');
        wrap.id = 'offline-mode-pill';
        wrap.setAttribute('role', 'complementary');
        wrap.innerHTML = `
            <div style="
                position:fixed; bottom:1.25rem; left:1.25rem; z-index:8889;
                background:linear-gradient(135deg,#0f766e,#0891b2);
                color:white; border-radius:9999px; padding:.55rem .9rem;
                box-shadow:0 4px 16px rgba(13,148,136,.35);
                display:flex; align-items:center; gap:.5rem;
                font-size:.82rem; font-weight:600;
                animation: dnPillIn .25s ease-out;
            ">
                <span style="font-size:1rem;line-height:1">📋</span>
                <a href="/offline-guides" style="color:white;text-decoration:none;white-space:nowrap;">
                    Offline Mode
                </a>
                <button id="offline-pill-dismiss" aria-label="Dismiss"
                    style="background:transparent;border:none;color:rgba(255,255,255,.75);
                    cursor:pointer;font-size:.95rem;line-height:1;padding:0 .1rem;">✕</button>
            </div>
            <style>
                @keyframes dnPillIn { from{opacity:0;transform:translateY(.5rem)} to{opacity:1;transform:translateY(0)} }
            </style>
        `;
        document.body.appendChild(wrap);
        const dismiss = document.getElementById('offline-pill-dismiss');
        if (dismiss) dismiss.addEventListener('click', () => {
            sessionStorage.setItem('offline_pill_dismissed', '1');
            wrap.remove();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            hideOfflineNavLinks();
            injectOfflinePill();
        });
    } else {
        hideOfflineNavLinks();
        injectOfflinePill();
    }

    // ── Offline chat queue ────────────────────────────────────────────────

    const QUEUE_KEY     = 'dharma_chat_queue';      // pending: [{id,message,language,ts}]
    const RESPONSES_KEY = 'dharma_chat_responses';  // delivered: [{id,message,reply,language,ts,seen}]
    let _flushing = false;

    function loadList(key) {
        try { return JSON.parse(localStorage.getItem(key) || '[]'); }
        catch { return []; }
    }
    function saveList(key, list) {
        try { localStorage.setItem(key, JSON.stringify(list)); } catch (e) {}
    }
    function uid() {
        return 'q_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
    }

    function queueOfflineChat(message, language) {
        const msg = (message || '').trim();
        if (!msg) return null;
        const queue = loadList(QUEUE_KEY);
        // Prevent duplicate submission of the same pending text
        if (queue.some(q => q.message === msg)) {
            return queue.find(q => q.message === msg).id;
        }
        const item = { id: uid(), message: msg, language: language || 'en', ts: Date.now() };
        queue.push(item);
        saveList(QUEUE_KEY, queue);
        showToast(t('chatQueued', '📵 Saved. Will send when you are back online.'));
        return item.id;
    }

    async function flushChatQueue() {
        if (_flushing) return;
        const queue = loadList(QUEUE_KEY);
        if (!queue.length) return;
        _flushing = true;

        const remaining = [];
        const newlyDelivered = [];

        for (const item of queue) {
            try {
                const resp = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: item.message,
                        language: item.language,
                        session_id: null,
                    }),
                });
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                const data = await resp.json();
                const reply = data.reply || data.response || data.message || '';
                const delivered = {
                    id: item.id,
                    message: item.message,
                    reply,
                    language: data.language || item.language,
                    ts: Date.now(),
                    seen: false,
                };
                newlyDelivered.push(delivered);
            } catch (e) {
                // Still offline or transient failure — keep in queue for next try.
                remaining.push(item);
            }
        }

        saveList(QUEUE_KEY, remaining);
        if (newlyDelivered.length) {
            const all = loadList(RESPONSES_KEY).concat(newlyDelivered);
            saveList(RESPONSES_KEY, all);
            handleDeliveredResponses(newlyDelivered);
        }
        _flushing = false;
    }

    function handleDeliveredResponses(items) {
        // 1. If we are on the chat page, append bubbles immediately and mark seen.
        const isChat = (location.pathname.replace(/\/+$/, '') || '/') === '/chat';
        if (isChat && typeof window.addChatBubble === 'function') {
            items.forEach(it => {
                try {
                    window.addChatBubble(it.message, 'user');
                    window.addChatBubble(it.reply || '(no response)', 'assistant');
                    it.seen = true;
                } catch (e) {}
            });
            // persist the seen flag
            const all = loadList(RESPONSES_KEY).map(r => {
                const m = items.find(x => x.id === r.id);
                return m ? Object.assign({}, r, { seen: true }) : r;
            });
            saveList(RESPONSES_KEY, all);
        }

        // 2. In-app toast with link back to chat
        const msg = items.length === 1
            ? t('chatRespOne', '💬 1 chat response is ready.')
            : t('chatRespMany', '💬 {n} chat responses are ready.').replace('{n}', items.length);
        showToast(msg, { actionLabel: t('openChat', 'Open Chat'), actionHref: '/chat' });

        // 3. Browser notification (if permission previously granted)
        try {
            if ('Notification' in window && Notification.permission === 'granted') {
                const n = new Notification('DHARMA-NYAYA', {
                    body: msg,
                    icon: '/assets/icons/icon-192.png',
                    tag: 'dharma-chat-queue',
                });
                n.onclick = () => { window.focus(); window.location.href = '/chat'; n.close(); };
            }
        } catch (e) {}
    }

    // Render any unseen responses when the chat page is opened
    function renderPendingResponsesOnChat() {
        const isChat = (location.pathname.replace(/\/+$/, '') || '/') === '/chat';
        if (!isChat || typeof window.addChatBubble !== 'function') return;
        const all = loadList(RESPONSES_KEY);
        const unseen = all.filter(r => !r.seen);
        if (!unseen.length) return;
        unseen.forEach(r => {
            try {
                window.addChatBubble(r.message, 'user');
                window.addChatBubble(r.reply || '(no response)', 'assistant');
            } catch (e) {}
        });
        const updated = all.map(r => Object.assign({}, r, { seen: true }));
        saveList(RESPONSES_KEY, updated);
    }

    // Wait for app.js to finish defining addChatBubble before rendering pending.
    function whenChatReady(cb) {
        if (typeof window.addChatBubble === 'function') return cb();
        let tries = 0;
        const iv = setInterval(() => {
            if (typeof window.addChatBubble === 'function' || ++tries > 40) {
                clearInterval(iv); cb();
            }
        }, 100);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => whenChatReady(renderPendingResponsesOnChat));
    } else {
        whenChatReady(renderPendingResponsesOnChat);
    }

    // ── In-app toast ──────────────────────────────────────────────────────

    function showToast(message, opts) {
        opts = opts || {};
        const host = document.body;
        if (!host) return;
        const wrap = document.createElement('div');
        wrap.setAttribute('role', 'status');
        wrap.style.cssText = `
            position:fixed; top:4.5rem; left:50%; transform:translateX(-50%);
            background:#1e1b4b; color:white; border-radius:.75rem;
            padding:.7rem 1rem; box-shadow:0 4px 20px rgba(0,0,0,.25);
            display:flex; align-items:center; gap:.75rem; z-index:9999;
            max-width:90vw; font-size:.85rem;
        `;
        const text = document.createElement('span');
        text.textContent = message;
        text.style.flex = '1';
        wrap.appendChild(text);
        if (opts.actionLabel && opts.actionHref) {
            const a = document.createElement('a');
            a.href = opts.actionHref;
            a.textContent = opts.actionLabel;
            a.style.cssText = `
                background:#4f46e5; color:white; padding:.3rem .7rem;
                border-radius:.5rem; font-weight:600; text-decoration:none;
                font-size:.8rem;
            `;
            wrap.appendChild(a);
        }
        const close = document.createElement('button');
        close.textContent = '✕';
        close.setAttribute('aria-label', 'Close');
        close.style.cssText = 'background:transparent;border:none;color:rgba(255,255,255,.7);cursor:pointer;font-size:1rem;';
        close.onclick = () => wrap.remove();
        wrap.appendChild(close);
        host.appendChild(wrap);
        setTimeout(() => { if (wrap.parentNode) wrap.remove(); }, 8000);
    }

    function t(key, fallback) {
        try {
            if (typeof window.t === 'function') {
                const v = window.t(key);
                if (v && v !== key) return v;
            }
        } catch (e) {}
        return fallback;
    }

    // Ask for notification permission on first user interaction (non-blocking)
    function requestNotifyPermissionLazy() {
        if (!('Notification' in window)) return;
        if (Notification.permission !== 'default') return;
        const ask = () => {
            Notification.requestPermission().catch(() => {});
            window.removeEventListener('click', ask);
            window.removeEventListener('keydown', ask);
        };
        window.addEventListener('click',  ask, { once: true });
        window.addEventListener('keydown', ask, { once: true });
    }
    requestNotifyPermissionLazy();

    // Attempt to flush on load if we are already online and queue is non-empty.
    if (_isOnline) setTimeout(flushChatQueue, 500);

    // Public API
    window.queueOfflineChat = queueOfflineChat;
    window.flushOfflineChatQueue = flushChatQueue;
})();

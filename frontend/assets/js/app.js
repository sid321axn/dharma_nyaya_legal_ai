/* DHARMA-NYAYA — Main application JavaScript */

const API_BASE = '';
const CHAT_ICON = 'data:image/png;base64,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';

// ── Theme Toggle ──────────────────────────────────────────────────────────

function initTheme() {
    const saved = localStorage.getItem('dharma_theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcon(saved);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('dharma_theme', next);
    updateThemeIcon(next);
}

function updateThemeIcon(theme) {
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;
    btn.innerHTML = theme === 'dark'
        ? '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>'
        : '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>';
}

// ── API Helpers ───────────────────────────────────────────────────────────

async function apiPost(endpoint, data) {
    const resp = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    return resp.json();
}

async function apiGet(endpoint) {
    const resp = await fetch(`${API_BASE}${endpoint}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
}

async function apiUpload(endpoint, formData) {
    const resp = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        body: formData,
    });
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    return resp.json();
}

// ── Chat Functions ────────────────────────────────────────────────────────

let sessionId = null;

function addChatBubble(text, role, mood) {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    const wrapper = document.createElement('div');
    wrapper.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-4`;

    if (role === 'assistant') {
        // Build row: avatar + bubble
        const row = document.createElement('div');
        row.className = 'assistant-row';

        // Animated avatar — chat icon image
        const avatarHTML = `
            <div class="avatar-container" id="avatar-ring-latest">
                <img class="avatar-img" id="avatar-face-latest" src="${CHAT_ICON}" alt="AI" width="48" height="48" style="width:48px;height:48px;border-radius:50%;object-fit:cover;border:3px solid #6366f1;" />
            </div>`;

        const avatarDiv = document.createElement('div');
        avatarDiv.innerHTML = avatarHTML.trim();

        // Split response into intro (for speaking) and detailed body
        const { intro, body } = splitResponse(text);

        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble assistant';

        // Typewriter streaming effect
        row.appendChild(avatarDiv.firstChild);
        row.appendChild(bubble);
        wrapper.appendChild(row);
        container.appendChild(wrapper);
        container.scrollTop = container.scrollHeight;

        // Apply concerned expression if the situation warrants it
        if (mood === 'concerned') {
            const face = document.getElementById('avatar-face-latest');
            if (face) face.classList.add('concerned');
        }

        // Start typewriter — renders formatted HTML progressively
        typewriterEffect(bubble, text, container);
    } else {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${role}`;
        bubble.innerHTML = formatMessage(text);
        wrapper.appendChild(bubble);
        container.appendChild(wrapper);
        container.scrollTop = container.scrollHeight;
    }
}

function extractSummary(text) {
    // Grab the full introductory paragraph — everything before the first
    // section heading (###) or horizontal rule (---).
    const lines = text.split('\n');
    const introLines = [];
    for (const line of lines) {
        const trimmed = line.trim();
        // Stop at section headings or horizontal rules
        if (trimmed.startsWith('###') || trimmed.startsWith('---') ||
            trimmed.startsWith('## ') || /^#{1,4}\s/.test(trimmed)) {
            break;
        }
        const clean = trimmed.replace(/[*_`]/g, '').trim();
        if (clean) introLines.push(clean);
    }
    let summary = introLines.join(' ') || text.replace(/[#*_`]/g, '').substring(0, 300);
    // Cap length for faster TTS generation
    if (summary.length > 250) summary = summary.substring(0, 247) + '...';
    return summary;
}

/**
 * Split the response into { intro, body }.
 * intro = everything before the first ### or ---
 * body  = the rest (the detailed sections)
 */
function splitResponse(text) {
    const lines = text.split('\n');
    let splitIdx = -1;
    for (let i = 0; i < lines.length; i++) {
        const trimmed = lines[i].trim();
        if (trimmed.startsWith('###') || trimmed.startsWith('---') ||
            trimmed.startsWith('## ') || /^#{1,4}\s/.test(trimmed)) {
            splitIdx = i;
            break;
        }
    }
    if (splitIdx <= 0) {
        return { intro: text, body: '' };
    }
    return {
        intro: lines.slice(0, splitIdx).join('\n'),
        body: lines.slice(splitIdx).join('\n'),
    };
}

// ── TTS (Text-to-Speech) with lip-sync — Google Cloud TTS ───────────

// Clean text for TTS — strip all markdown symbols
function cleanForTTS(text) {
    return text
        .replace(/#{1,6}\s*/g, '')
        .replace(/\*\*\*(.*?)\*\*\*/g, '$1')
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/`(.*?)`/g, '$1')
        .replace(/---+/g, '')
        .replace(/\n+/g, '. ')
        .replace(/\s+/g, ' ')
        .trim();
}

// ── Audio Unlock (call on user gesture to bypass autoplay policy) ──

let _audioCtx = null;
let _activeSource = null;

function getAudioCtx() {
    if (!_audioCtx) _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    return _audioCtx;
}

function unlockAudio() {
    try {
        const ctx = getAudioCtx();
        if (ctx.state === 'suspended') ctx.resume();
        // Play a tiny silent buffer to fully unlock
        const buf = ctx.createBuffer(1, 1, 22050);
        const src = ctx.createBufferSource();
        src.buffer = buf;
        src.connect(ctx.destination);
        src.start(0);
    } catch (e) { /* ignore */ }
}

// Active audio element (kept for stop control)
let activeAudio = null;

/**
 * Core audio player — decodes WAV/PCM ArrayBuffer and plays via AudioContext.
 * AudioContext stays unlocked after the user gesture, so this always works.
 */
function playAudioBuffer(arrayBuffer, onStart, onEnd) {
    const ctx = getAudioCtx();
    if (ctx.state === 'suspended') ctx.resume();

    // Stop any previous playback
    if (_activeSource) { try { _activeSource.stop(); } catch(e){} _activeSource = null; }

    ctx.decodeAudioData(arrayBuffer, (audioBuffer) => {
        const source = ctx.createBufferSource();
        source.buffer = audioBuffer;

        // Add a gain node for volume control
        const gainNode = ctx.createGain();
        gainNode.gain.value = 1.0;
        source.connect(gainNode);
        gainNode.connect(ctx.destination);

        _activeSource = source;
        if (onStart) onStart();

        source.onended = () => {
            _activeSource = null;
            if (onEnd) onEnd();
        };

        source.start(0);
    }, (err) => {
        console.error('[TTS] Audio decode error:', err);
        if (onEnd) onEnd();
    });
}

function stopCurrentAudio() {
    if (_activeSource) { try { _activeSource.stop(); } catch(e){} _activeSource = null; }
    if (activeAudio) { activeAudio.pause(); activeAudio = null; }
    if (window.speechSynthesis) window.speechSynthesis.cancel();
}

/**
 * Play a pre-fetched TTS response (fetch promise).
 * Called from sendMessage so audio starts as soon as TTS arrives.
 */
async function playTTSBlob(respPromise) {
    const face = document.getElementById('avatar-face-latest');
    const ring = document.getElementById('avatar-ring-latest');

    const startAnim = () => {
        if (face) face.classList.add('speaking');
        if (ring) ring.classList.add('speaking');
    };
    const stopAnim = () => {
        if (face) face.classList.remove('speaking');
        if (ring) ring.classList.remove('speaking');
    };

    stopCurrentAudio();

    try {
        const resp = await respPromise;
        if (!resp || !resp.ok || resp.status !== 200) { stopAnim(); return; }

        const arrayBuffer = await resp.arrayBuffer();
        if (!arrayBuffer || arrayBuffer.byteLength === 0) { stopAnim(); return; }

        playAudioBuffer(arrayBuffer, startAnim, stopAnim);
    } catch (e) {
        console.log('[TTS] Play error:', e.message);
        stopAnim();
    }
}

/**
 * Speak text using backend /api/tts (Gemini 2.5 Flash TTS).
 * Used for click-to-replay on the voice bar.
 */
async function speakText(text, voiceBarEl) {
    if (!text) return;

    const cleanText = cleanForTTS(text);
    if (!cleanText) return;

    const lang = getCurrentLanguage();

    // Animation helpers
    const face = document.getElementById('avatar-face-latest');
    const ring = document.getElementById('avatar-ring-latest');
    const icon = voiceBarEl ? voiceBarEl.querySelector('.speaker-icon') : null;

    const startAnimation = () => {
        if (face) face.classList.add('speaking');
        if (ring) ring.classList.add('speaking');
        if (icon) icon.classList.add('animating');
    };
    const stopAnimation = () => {
        if (face) face.classList.remove('speaking');
        if (ring) ring.classList.remove('speaking');
        if (icon) icon.classList.remove('animating');
    };

    stopCurrentAudio();

    try {
        const resp = await fetch(`${API_BASE}/api/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: cleanText, language: lang }),
        });

        if (resp.ok && resp.status === 200) {
            const arrayBuffer = await resp.arrayBuffer();
            if (arrayBuffer && arrayBuffer.byteLength > 0) {
                playAudioBuffer(arrayBuffer, startAnimation, stopAnimation);
                return;
            }
        }

        console.log('[TTS] Backend TTS unavailable, trying Web Speech API');
        speakWithWebSpeech(cleanText, lang, startAnimation, stopAnimation);

    } catch (err) {
        console.log('[TTS] Error:', err.message, '— trying Web Speech API');
        speakWithWebSpeech(cleanText, lang, startAnimation, stopAnimation);
    }
}

const WEB_SPEECH_LANG = {
    hi: 'hi-IN', bn: 'bn-IN', ta: 'ta-IN', te: 'te-IN', kn: 'kn-IN',
    uk: 'uk-UA', en: 'en-IN', sat: 'hi-IN',
};

function speakWithWebSpeech(text, lang, startAnimation, stopAnimation) {
    if (!window.speechSynthesis) { stopAnimation(); return; }
    window.speechSynthesis.cancel();

    setTimeout(() => {
        const ttsLang = WEB_SPEECH_LANG[lang] || 'en-IN';
        const utter = new SpeechSynthesisUtterance(text);
        utter.lang = ttsLang;
        utter.volume = 1;
        utter.rate = 0.95;
        utter.pitch = 1.05;

        // Find a voice
        const voices = window.speechSynthesis.getVoices();
        const prefix = ttsLang.split('-')[0];
        const voice = voices.find(v => v.lang && v.lang.startsWith(prefix));
        if (voice) utter.voice = voice;

        startAnimation();
        utter.onend = stopAnimation;
        utter.onerror = stopAnimation;

        window.speechSynthesis.speak(utter);

        // Chrome keepAlive workaround
        const keepAlive = setInterval(() => {
            if (!window.speechSynthesis.speaking) { clearInterval(keepAlive); return; }
            window.speechSynthesis.pause();
            window.speechSynthesis.resume();
        }, 10000);
        utter.onend = () => { clearInterval(keepAlive); stopAnimation(); };
        utter.onerror = utter.onend;
    }, 100);
}

function formatMessage(text) {
    // Rich markdown formatting
    return text
        // Headings
        .replace(/^#### (.*?)$/gm, '<h4>$1</h4>')
        .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
        // Bold + italic
        .replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Horizontal rule
        .replace(/^---+$/gm, '<hr>')
        // Unordered list items
        .replace(/^\* (.*?)$/gm, '<li>$1</li>')
        .replace(/^- (.*?)$/gm, '<li>$1</li>')
        // Numbered list items
        .replace(/^\d+\.\s+(.*?)$/gm, '<li>$1</li>')
        // Wrap consecutive <li> in <ul>
        .replace(/((?:<li>.*?<\/li>\n?)+)/g, '<ul>$1</ul>')
        // Inline code
        .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded text-sm">$1</code>')
        // Newlines
        .replace(/\n/g, '<br>');
}

function showTyping() {
    // No-op — replaced by agent status panel
}

// ── Typewriter Sound Effect ───────────────────────────────────────────

/**
 * Generate a short synthetic typewriter "click" via AudioContext.
 * No external audio files needed — pure oscillator + noise burst.
 */
function playTypewriterClick() {
    try {
        const ctx = getAudioCtx();
        if (ctx.state === 'suspended') return; // no gesture yet
        const now = ctx.currentTime;

        // Short noise burst for the "click"
        const bufLen = Math.floor(ctx.sampleRate * 0.012); // 12ms
        const noiseBuf = ctx.createBuffer(1, bufLen, ctx.sampleRate);
        const data = noiseBuf.getChannelData(0);
        for (let i = 0; i < bufLen; i++) {
            data[i] = (Math.random() * 2 - 1) * 0.3;
        }
        const noise = ctx.createBufferSource();
        noise.buffer = noiseBuf;

        // Bandpass filter to shape it into a "key" click
        const filter = ctx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.value = 3000 + Math.random() * 2000; // slight variation
        filter.Q.value = 1.5;

        // Envelope for quick attack & decay
        const gain = ctx.createGain();
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.012);

        noise.connect(filter);
        filter.connect(gain);
        gain.connect(ctx.destination);
        noise.start(now);
        noise.stop(now + 0.015);
    } catch (e) { /* silent fail */ }
}

// ── Typewriter Effect ─────────────────────────────────────────────────

/**
 * Progressively reveal formatted HTML content with a typing effect.
 * Splits the markdown into lines, formats each, and reveals word-by-word
 * with a blinking cursor and typewriter clicking sound.
 */
function typewriterEffect(bubble, rawText, container) {
    const formattedHTML = formatMessage(rawText);

    // Parse into a temporary container to get DOM nodes
    const temp = document.createElement('div');
    temp.innerHTML = formattedHTML;

    // Collect all text nodes with their parent elements
    const segments = [];
    function collectNodes(parent) {
        for (const node of parent.childNodes) {
            if (node.nodeType === Node.TEXT_NODE) {
                const text = node.textContent;
                if (text.trim() || text.includes('\n')) {
                    segments.push({ type: 'text', text, parent: node.parentNode, node });
                }
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                segments.push({ type: 'open', el: node });
                collectNodes(node);
                segments.push({ type: 'close', el: node });
            }
        }
    }
    collectNodes(temp);

    // Build word queue from segments
    const queue = [];
    for (const seg of segments) {
        if (seg.type === 'text') {
            // Split text into words, preserving spaces
            const words = seg.text.match(/\S+|\s+/g) || [];
            for (const w of words) queue.push({ type: 'word', text: w });
        } else if (seg.type === 'open') {
            const clone = seg.el.cloneNode(false); // tag only, no children
            queue.push({ type: 'open', tag: clone });
        } else {
            queue.push({ type: 'close' });
        }
    }

    // Cursor element
    const cursor = document.createElement('span');
    cursor.className = 'typing-cursor';

    bubble.innerHTML = '';
    bubble.appendChild(cursor);

    // Stack to track current parent for appending
    const stack = [bubble];
    let idx = 0;

    // Speed: ~45ms per word for a visible typing feel
    const WORD_DELAY = 45;

    function typeNext() {
        if (idx >= queue.length) {
            // Done — remove cursor
            if (cursor.parentNode) cursor.remove();
            return;
        }

        const item = queue[idx++];

        if (item.type === 'open') {
            const parent = stack[stack.length - 1];
            // Insert before cursor, then move cursor inside
            parent.insertBefore(item.tag, cursor);
            item.tag.appendChild(cursor);
            stack.push(item.tag);
            // Don't delay on tag opens — process next immediately
            typeNext();
        } else if (item.type === 'close') {
            const closed = stack.pop();
            const parent = stack[stack.length - 1];
            // Move cursor back to parent after the closed element
            parent.insertBefore(cursor, closed.nextSibling);
            typeNext();
        } else {
            // Word or whitespace
            const parent = stack[stack.length - 1];
            const textNode = document.createTextNode(item.text);
            parent.insertBefore(textNode, cursor);

            // Auto-scroll
            container.scrollTop = container.scrollHeight;

            // Batch whitespace-only items for speed
            if (!item.text.trim()) {
                typeNext();
            } else {
                // Play typewriter click on each visible word
                if (!_ttsMuted) playTypewriterClick();
                setTimeout(typeNext, WORD_DELAY);
            }
        }
    }

    typeNext();
}

function hideTyping() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
}

// ── Mood Detection (for avatar expressions) ──────────────────────────

const CONCERN_DOMAINS = new Set([
    'domestic_violence', 'harassment', 'sexual_harassment', 'abuse',
    'child_abuse', 'dowry', 'assault', 'murder', 'kidnapping',
    'human_trafficking', 'cyber_crime', 'fraud', 'extortion',
]);

const CONCERN_KEYWORDS = /domestic\s*violence|harassment|abuse|assault|murder|kidnap|threat|extortion|dowry|molestation|rape|torture|victim|FIR|\u0939\u093f\u0902\u0938\u093e|\u0909\u0924\u094d\u092a\u0940\u0921\u093c\u0928|\u0926\u0941\u0930\u094d\u0935\u094d\u092f\u0935\u0939\u093e\u0930|\u092e\u093e\u0930\u092a\u0940\u091f|\u0927\u092e\u0915\u0940|\u0905\u092a\u0939\u0930\u0923|\u0936\u094b\u0937\u0923/i;

function detectMood(reply, metadata) {
    // Check domain from backend metadata
    if (metadata && metadata.domain && CONCERN_DOMAINS.has(metadata.domain)) {
        return 'concerned';
    }
    // Fallback: check reply text for concerning keywords
    if (CONCERN_KEYWORDS.test(reply)) {
        return 'concerned';
    }
    return 'neutral';
}

// ── Input Language Detection (Unicode script heuristics) ─────────────

const SCRIPT_PATTERNS = [
    { lang: 'hi', re: /[\u0900-\u097F]/ },   // Devanagari → Hindi
    { lang: 'bn', re: /[\u0980-\u09FF]/ },   // Bengali
    { lang: 'ta', re: /[\u0B80-\u0BFF]/ },   // Tamil
    { lang: 'te', re: /[\u0C00-\u0C7F]/ },   // Telugu
    { lang: 'kn', re: /[\u0C80-\u0CFF]/ },   // Kannada
    { lang: 'uk', re: /[\u0400-\u04FF]/ },   // Cyrillic → Ukrainian
    { lang: 'sat', re: /[\u1C50-\u1C7F]/ },  // Ol Chiki → Santali
];

function detectInputLanguage(text) {
    for (const { lang, re } of SCRIPT_PATTERNS) {
        if (re.test(text)) return lang;
    }
    return null; // couldn't detect → fall back to UI language
}

// ── Agent Status Panel ────────────────────────────────────────────────

const STEP_ORDER = ['reading', 'detecting', 'routing', 'thinking', 'translating', 'preparing'];

const STEP_ICONS = {
    waiting: '<span class="text-gray-400">○</span>',
    active:  '<div class="step-spinner"></div>',
    done:    '<span>✓</span>',
};

// Translate a step key using an explicit language override (or fall back to current)
function tStep(key, replacements = {}, lang = null) {
    let text;
    if (lang && TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) {
        text = TRANSLATIONS[lang][key];
    } else {
        text = t(key);
    }
    for (const [k, v] of Object.entries(replacements)) {
        text = text.replace(`{${k}}`, v);
    }
    return text;
}

function createStatusPanel(lang) {
    const container = document.getElementById('chat-messages');
    if (!container) return null;

    const wrapper = document.createElement('div');
    wrapper.id = 'agent-status-wrapper';
    wrapper.className = 'flex justify-start mb-4';

    const panel = document.createElement('div');
    panel.className = 'agent-status-panel';
    panel.id = 'agent-status-panel';

    const headerText = tStep('agentsWorking', {}, lang);
    panel.innerHTML = `
        <div class="panel-header">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            <span id="panel-header-text">${headerText}</span>
        </div>
        <div id="agent-steps"></div>
    `;

    wrapper.appendChild(panel);
    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
    return document.getElementById('agent-steps');
}

/**
 * Re-render all existing step labels + header in the detected language.
 * Called once when the 'detecting' step comes back done with a language.
 */
function relabelStatusPanel(lang) {
    // Update header
    const header = document.getElementById('panel-header-text');
    if (header) header.textContent = tStep('agentsWorking', {}, lang);

    // Update all existing step labels
    for (const name of STEP_ORDER) {
        const stepEl = document.getElementById(`step-${name}`);
        if (!stepEl) continue;
        const isDone = stepEl.classList.contains('done');
        const key = isDone ? `step_${name}_done` : `step_${name}`;
        const agent = stepEl.dataset.agent || '';
        const domain = stepEl.dataset.domain || '';
        const labelEl = stepEl.querySelector('.step-label');
        if (labelEl) labelEl.textContent = tStep(key, { agent, domain }, lang);
    }
}

function updateStep(stepsContainer, stepName, status, agent, detail, lang) {
    if (!stepsContainer) return;
    const container = document.getElementById('chat-messages');

    let stepEl = document.getElementById(`step-${stepName}`);
    if (!stepEl) {
        stepEl = document.createElement('div');
        stepEl.id = `step-${stepName}`;
        stepEl.className = `agent-step ${status}`;
        stepEl.dataset.agent = agent || '';
        stepEl.dataset.domain = (detail && detail.domain) || '';

        const stepKey = status === 'done'
            ? (`step_${stepName}_done`)
            : (`step_${stepName}`);
        const label = tStep(stepKey, { agent: agent || '', domain: (detail && detail.domain) || '' }, lang);

        stepEl.innerHTML = `
            <div class="step-icon">${STEP_ICONS[status]}</div>
            <span class="step-label">${label}</span>
        `;
        stepsContainer.appendChild(stepEl);
    } else {
        // Update existing step
        stepEl.className = `agent-step ${status}`;
        stepEl.querySelector('.step-icon').innerHTML = STEP_ICONS[status];

        if (status === 'done') {
            const doneKey = `step_${stepName}_done`;
            const doneText = tStep(doneKey, { agent: agent || '', domain: (detail && detail.domain) || '' }, lang);
            if (doneText !== doneKey) {
                stepEl.querySelector('.step-label').textContent = doneText;
            }
        }
    }

    // Show detail badge (e.g., detected language)
    if (detail && status === 'done') {
        const existing = stepEl.querySelector('.step-detail');
        if (!existing) {
            const detailEl = document.createElement('div');
            detailEl.className = 'step-detail';
            if (detail.domain) {
                detailEl.textContent = `📋 ${detail.domain}${detail.language ? ' · ' + detail.language : ''}`;
            } else if (detail.chosen_agent) {
                detailEl.textContent = `🤝 ${detail.chosen_agent}`;
            }
            if (detailEl.textContent) {
                stepEl.appendChild(detailEl);
            }
        }
    }

    if (container) container.scrollTop = container.scrollHeight;
}

function removeStatusPanel() {
    const el = document.getElementById('agent-status-wrapper');
    if (el) el.remove();
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    if (!input) return;
    const message = input.value.trim();
    if (!message) return;

    // Unlock audio on this user gesture so auto-speak works after response
    unlockAudio();

    // ── Offline path: queue locally and let network.js flush on reconnect ──
    const onlineApi = (window.DNNet && typeof window.DNNet.isOnline === 'function')
        ? window.DNNet.isOnline()
        : navigator.onLine;
    if (!onlineApi && typeof window.queueOfflineChat === 'function') {
        input.value = '';
        addChatBubble(message, 'user');
        recordMessage('user', message);
        const offlineMsg = (typeof t === 'function' && t('chatQueuedBubble'))
            || '📵 You are offline. I\'ve saved your question and will answer the moment you\'re back online.';
        addChatBubble(offlineMsg, 'assistant');
        window.queueOfflineChat(message, getCurrentLanguage());
        return;
    }

    input.value = '';
    addChatBubble(message, 'user');
    recordMessage('user', message);

    // Detect language from the typed text immediately so labels render correctly
    let detectedLang = detectInputLanguage(message) || getCurrentLanguage();

    // Create the live agent status panel (already in the right language)
    const stepsContainer = createStatusPanel(detectedLang);

    try {
        const resp = await fetch(`${API_BASE}/api/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                language: getCurrentLanguage(),
                session_id: sessionId,
            }),
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${resp.status}`);
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const jsonStr = line.slice(6).trim();
                if (!jsonStr) continue;

                try {
                    const event = JSON.parse(jsonStr);

                    if (event.type === 'step') {
                        // If backend detected a different language, update
                        if (event.step === 'detecting' && event.status === 'done' &&
                            event.detail && event.detail.language &&
                            event.detail.language !== detectedLang) {
                            detectedLang = event.detail.language;
                            relabelStatusPanel(detectedLang);
                        }

                        updateStep(
                            stepsContainer,
                            event.step,
                            event.status,
                            event.agent,
                            event.detail,
                            detectedLang
                        );
                    } else if (event.type === 'done') {
                        // Remove status panel and show the actual reply
                        removeStatusPanel();
                        sessionId = event.session_id;

                        // Use backend-generated tts_text (first 2 paragraphs + closing)
                        const ttsText = event.tts_text || '';
                        let ttsPromise = null;
                        if (ttsText && !_ttsMuted) {
                            ttsPromise = fetch(`${API_BASE}/api/tts`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ text: ttsText, language: event.language || detectedLang || getCurrentLanguage() }),
                            }).catch(() => null);
                        }

                        // Render chat bubble with mood based on content
                        const mood = detectMood(event.reply, event.metadata);
                        addChatBubble(event.reply, 'assistant', mood);
                        recordMessage('assistant', event.reply);

                        // Auto-play audio (if not muted)
                        if (ttsPromise) playTTSBlob(ttsPromise);
                    }
                } catch (e) {
                    // Skip malformed JSON lines
                }
            }
        }
    } catch (err) {
        removeStatusPanel();
        addChatBubble(t('errorGeneric') + ' ' + err.message, 'assistant');
    }
}

// ── Document Upload ───────────────────────────────────────────────────────

function initDropZone() {
    const zone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    if (!zone || !fileInput) return;

    zone.addEventListener('click', () => fileInput.click());

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) handleFileUpload(fileInput.files[0]);
    });
}

async function handleFileUpload(file) {
    const resultPanel = document.getElementById('analysis-result');
    const loadingEl = document.getElementById('analysis-loading');
    if (loadingEl) loadingEl.classList.remove('hidden');
    if (resultPanel) resultPanel.classList.add('hidden');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('language', getCurrentLanguage());
    formData.append('session_id', sessionId || '');

    try {
        const data = await apiUpload('/api/document/upload', formData);
        if (loadingEl) loadingEl.classList.add('hidden');
        displayAnalysis(data.analysis);
    } catch (err) {
        if (loadingEl) loadingEl.classList.add('hidden');
        alert(t('errorGeneric') + ': ' + err.message);
    }
}

function displayAnalysis(analysis) {
    const panel = document.getElementById('analysis-result');
    if (!panel) return;
    panel.classList.remove('hidden');

    document.getElementById('analysis-summary').textContent = analysis.summary || '';
    
    const risksEl = document.getElementById('analysis-risks');
    risksEl.innerHTML = (analysis.risks || []).map(r =>
        `<span class="risk-badge high">${r}</span>`
    ).join(' ');

    const clausesEl = document.getElementById('analysis-clauses');
    clausesEl.innerHTML = (analysis.key_clauses || []).map(c =>
        `<li class="py-1">${c}</li>`
    ).join('');

    document.getElementById('analysis-advice').textContent = analysis.advice || '';
}

// ── Dashboard ─────────────────────────────────────────────────────────────

async function loadCases() {
    const tbody = document.getElementById('cases-tbody');
    if (!tbody) return;

    try {
        const cases = await apiGet('/api/cases');
        if (cases.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-8 text-gray-400">No cases yet. Start a chat to create one.</td></tr>';
            return;
        }
        tbody.innerHTML = cases.map(c => `
            <tr class="border-b border-gray-100 hover:bg-gray-50 transition">
                <td class="py-3 px-4 font-mono text-xs text-gray-500">${c.id}</td>
                <td class="py-3 px-4 font-medium">${c.title || 'Untitled'}</td>
                <td class="py-3 px-4"><span class="px-2 py-1 rounded-full text-xs font-semibold ${statusColor(c.status)}">${c.status}</span></td>
                <td class="py-3 px-4 text-sm text-gray-500">${c.legal_domain || '-'}</td>
                <td class="py-3 px-4 text-sm text-gray-500">${new Date(c.created_at).toLocaleDateString()}</td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-8 text-red-400">Failed to load cases</td></tr>';
    }
}

function statusColor(status) {
    const colors = {
        open: 'bg-blue-100 text-blue-700',
        in_progress: 'bg-yellow-100 text-yellow-700',
        resolved: 'bg-green-100 text-green-700',
        closed: 'bg-gray-100 text-gray-600',
    };
    return colors[status] || colors.open;
}

// ── PDF Report Download ───────────────────────────────────────────────────

// Track conversation messages for PDF export
const chatHistory = [];

function recordMessage(role, content) {
    chatHistory.push({ role, content });
}

async function downloadPDFReport() {
    if (chatHistory.length === 0) {
        alert('No conversation to export. Start a chat first.');
        return;
    }
    const btn = document.getElementById('pdf-btn');
    if (btn) btn.disabled = true;

    try {
        const resp = await fetch(API_BASE + '/api/report/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: 'Legal Consultation Report',
                language: getCurrentLanguage(),
                messages: chatHistory,
            }),
        });
        if (!resp.ok) throw new Error('PDF generation failed');

        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dharma_nyaya_report_${Date.now()}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (err) {
        alert('Could not generate PDF: ' + err.message);
    } finally {
        if (btn) btn.disabled = false;
    }
}

// ── Init ──────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    setLanguage(getCurrentLanguage());
    initDropZone();

    // Enter key to send
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // Language selector
    const langSelect = document.getElementById('lang-select');
    if (langSelect) {
        langSelect.addEventListener('change', (e) => setLanguage(e.target.value));
    }

    // Load dashboard
    if (document.getElementById('cases-tbody')) loadCases();
});

// ── Voice Input (Speech Recognition) ─────────────────────────────────────

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let _recognition = null;
let _micActive = false;
let _ttsMuted = localStorage.getItem('dharma_tts_muted') === 'true';

// Apply saved mute state on load
document.addEventListener('DOMContentLoaded', () => {
    updateMuteUI();
});

function toggleMute() {
    _ttsMuted = !_ttsMuted;
    localStorage.setItem('dharma_tts_muted', _ttsMuted);
    if (_ttsMuted) stopCurrentAudio();
    updateMuteUI();
}

function updateMuteUI() {
    const onIcon = document.getElementById('mute-icon-on');
    const offIcon = document.getElementById('mute-icon-off');
    const btn = document.getElementById('mute-btn');
    if (!onIcon || !offIcon) return;
    if (_ttsMuted) {
        onIcon.classList.add('hidden');
        offIcon.classList.remove('hidden');
        if (btn) btn.title = 'Unmute Auto-Speak';
    } else {
        onIcon.classList.remove('hidden');
        offIcon.classList.add('hidden');
        if (btn) btn.title = 'Mute Auto-Speak';
    }
}

const LANG_TO_SPEECH = {
    en: 'en-IN', hi: 'hi-IN', bn: 'bn-IN', ta: 'ta-IN',
    te: 'te-IN', kn: 'kn-IN', sat: 'hi-IN', uk: 'uk-UA'
};

function toggleVoiceInput() {
    if (!SpeechRecognition) {
        alert('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
        return;
    }
    if (_micActive) {
        stopVoiceInput();
        return;
    }
    startVoiceInput();
}

function startVoiceInput() {
    const micBtn = document.getElementById('mic-btn');
    const chatInput = document.getElementById('chat-input');
    if (!chatInput) return;

    _recognition = new SpeechRecognition();
    const lang = getCurrentLanguage();
    _recognition.lang = LANG_TO_SPEECH[lang] || 'en-IN';
    _recognition.continuous = true;
    _recognition.interimResults = true;

    _micActive = true;
    if (micBtn) {
        micBtn.classList.remove('text-gray-500');
        micBtn.classList.add('text-red-500', 'animate-pulse');
    }

    let finalTranscript = '';
    const existing = chatInput.value;

    _recognition.onresult = (e) => {
        let interim = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) {
                finalTranscript += e.results[i][0].transcript + ' ';
            } else {
                interim += e.results[i][0].transcript;
            }
        }
        chatInput.value = (existing ? existing + ' ' : '') + finalTranscript + interim;
        chatInput.style.height = 'auto';
        chatInput.style.height = chatInput.scrollHeight + 'px';
    };

    _recognition.onend = () => {
        // Auto-restart if user hasn't manually stopped — keeps mic alive through pauses
        if (_micActive) {
            try { _recognition.start(); } catch(e) {}
            return;
        }
        chatInput.value = (existing ? existing + ' ' : '') + finalTranscript.trim();
        resetMicUI();
    };

    _recognition.onerror = (e) => {
        console.error('Speech recognition error:', e.error);
        if (e.error === 'not-allowed') {
            alert('Microphone access denied. Please allow microphone permission and try again.');
            resetMicUI();
        } else if (e.error === 'no-speech') {
            // No speech detected — keep listening, onend will auto-restart
        } else if (e.error === 'aborted') {
            resetMicUI();
        }
    };

    _recognition.start();
}

function stopVoiceInput() {
    _micActive = false;
    if (_recognition) {
        _recognition.stop();
    }
}

function resetMicUI() {
    _micActive = false;
    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        micBtn.classList.remove('text-red-500', 'animate-pulse');
        micBtn.classList.add('text-gray-500');
    }
    _recognition = null;
}

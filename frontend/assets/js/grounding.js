/**
 * Shared renderer for Google Search grounded source badges.
 *
 * Backend payloads (Spot-the-Trap, Predict) include:
 *   sources: [{ title, uri }]
 *
 * Sources come from Gemma 4's grounding_metadata.grounding_chunks.
 *
 * Usage:
 *   GroundingUI.renderInto('grounding-section', sources);
 *   // Legacy 3-arg form is also supported (validations is ignored):
 *   GroundingUI.renderInto('grounding-section', validations, sources);
 */
(function (global) {
    'use strict';

    function esc(s) {
        const d = document.createElement('div');
        d.textContent = s == null ? '' : String(s);
        return d.innerHTML;
    }

    function renderSourceBadge(s) {
        const title = esc(s.title || s.uri || 'Source');
        const uri = esc(s.uri || '#');
        return `<a href="${uri}" target="_blank" rel="noopener noreferrer"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-700 rounded-full text-xs font-medium transition max-w-full">
            <span>🔗</span>
            <span class="truncate" style="max-width:18rem">${title}</span>
        </a>`;
    }

    function renderInto(containerId, arg2, arg3) {
        // Accept renderInto(id, sources) OR legacy renderInto(id, validations, sources).
        const sources = Array.isArray(arg3) ? arg3 : (Array.isArray(arg2) ? arg2 : []);
        const el = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
        if (!el) return;
        if (sources.length === 0) {
            el.classList.add('hidden');
            el.innerHTML = '';
            return;
        }
        el.classList.remove('hidden');
        el.innerHTML = `
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 space-y-3">
                <div class="flex items-center gap-2">
                    <span class="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-sm">🔗</span>
                    <div>
                        <h3 class="text-sm font-bold text-gray-800">Verified Sources</h3>
                        <p class="text-[11px] text-gray-500">Live Google Search results from Gemma 4 grounding</p>
                    </div>
                </div>
                <div class="flex flex-wrap gap-2">${sources.map(renderSourceBadge).join('')}</div>
            </div>`;
    }

    global.GroundingUI = { renderInto };
})(window);

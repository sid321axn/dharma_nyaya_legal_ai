/* DHARMA-NYAYA — Know Your Rights Quiz Engine
   Questions & translations served from SQLite via /api/quiz/questions */

// ── State ──────────────────────────────────────────────────────────────────
let _quizBank = {};       // { topic: [{ q, opts, ans, explain }] }
let _quizBankLoaded = ''; // language code that is loaded
let currentTopic = '';
let questions = [];
let currentQ = 0;
let score = 0;
let answered = false;

function getQuizLang() {
    return localStorage.getItem('dharma_lang') || 'en';
}

// ── Topic metadata (used to build topic cards dynamically) ─────────────────
const TOPIC_META = {
    // Indian topics
    fundamental_rights:      { emoji: '⚖️', title: 'Fundamental Rights',       desc: 'Articles 14–32 of the Constitution',       border: 'border-indigo-100', hover: 'hover:border-indigo-400', hoverText: 'group-hover:text-indigo-600', i18nTitle: 'quizTopicFundamental', i18nDesc: 'quizTopicFundamentalDesc' },
    police_rights:           { emoji: '🚔', title: 'Rights During Arrest',      desc: 'What to do when police stop you',           border: 'border-red-100',    hover: 'hover:border-red-400',    hoverText: 'group-hover:text-red-600',    i18nTitle: 'quizTopicPolice',       i18nDesc: 'quizTopicPoliceDesc' },
    women_rights:            { emoji: '👩', title: "Women's Rights",            desc: 'Protection laws & workplace rights',        border: 'border-pink-100',   hover: 'hover:border-pink-400',   hoverText: 'group-hover:text-pink-600',   i18nTitle: 'quizTopicWomen',        i18nDesc: 'quizTopicWomenDesc' },
    consumer_rights:         { emoji: '🛒', title: 'Consumer Rights',           desc: 'Protection against fraud & deficiency',     border: 'border-green-100',  hover: 'hover:border-green-400',  hoverText: 'group-hover:text-green-600',  i18nTitle: 'quizTopicConsumer',     i18nDesc: 'quizTopicConsumerDesc' },
    property_rights:         { emoji: '🏠', title: 'Property & Tenant Rights',  desc: 'Rent, eviction, registration laws',         border: 'border-amber-100',  hover: 'hover:border-amber-400',  hoverText: 'group-hover:text-amber-600',  i18nTitle: 'quizTopicProperty',     i18nDesc: 'quizTopicPropertyDesc' },
    labour_rights:           { emoji: '👷', title: 'Labour Rights',             desc: 'Wages, working hours, PF, ESI',             border: 'border-cyan-100',   hover: 'hover:border-cyan-400',   hoverText: 'group-hover:text-cyan-600',   i18nTitle: 'quizTopicLabour',       i18nDesc: 'quizTopicLabourDesc' },
    // Ukrainian topics (EU host-country rights)
    uk_temporary_protection: { emoji: '🛡️', title: 'Temporary Protection Status',   desc: 'EU residence rights & registration',           border: 'border-blue-100',    hover: 'hover:border-blue-400',    hoverText: 'group-hover:text-blue-600',    i18nTitle: 'quizTopicUkTempProt',     i18nDesc: 'quizTopicUkTempProtDesc' },
    uk_employment_rights:    { emoji: '💼', title: 'Work Rights in Host Countries', desc: 'Employment, wages & labour protections',        border: 'border-indigo-100',  hover: 'hover:border-indigo-400',  hoverText: 'group-hover:text-indigo-600',  i18nTitle: 'quizTopicUkEmployment',   i18nDesc: 'quizTopicUkEmploymentDesc' },
    uk_housing_rights:       { emoji: '🏘️', title: 'Housing & Accommodation',       desc: 'Tenant rights, eviction & safety standards',   border: 'border-amber-100',   hover: 'hover:border-amber-400',   hoverText: 'group-hover:text-amber-600',   i18nTitle: 'quizTopicUkHousing',      i18nDesc: 'quizTopicUkHousingDesc' },
    uk_healthcare_rights:    { emoji: '🏥', title: 'Healthcare Access Rights',      desc: 'Medical care, prescriptions & mental health',   border: 'border-green-100',   hover: 'hover:border-green-400',   hoverText: 'group-hover:text-green-600',   i18nTitle: 'quizTopicUkHealthcare',   i18nDesc: 'quizTopicUkHealthcareDesc' },
    uk_children_education:   { emoji: '📚', title: "Children's Education Rights",   desc: 'School enrolment, language & SEN support',     border: 'border-purple-100',  hover: 'hover:border-purple-400',  hoverText: 'group-hover:text-purple-600',  i18nTitle: 'quizTopicUkEducation',    i18nDesc: 'quizTopicUkEducationDesc' },
    uk_social_benefits:      { emoji: '💶', title: 'Social Benefits & Support',     desc: 'Welfare, child benefit & integration funds',    border: 'border-emerald-100', hover: 'hover:border-emerald-400', hoverText: 'group-hover:text-emerald-600', i18nTitle: 'quizTopicUkSocialBen',    i18nDesc: 'quizTopicUkSocialBenDesc' },
    uk_border_rights:        { emoji: '🛂', title: 'Border & Transit Rights',       desc: 'Entry, asylum procedures & documentation',     border: 'border-red-100',     hover: 'hover:border-red-400',     hoverText: 'group-hover:text-red-600',     i18nTitle: 'quizTopicUkBorder',       i18nDesc: 'quizTopicUkBorderDesc' },
};

// ── Build and render topic cards ───────────────────────────────────────────
function buildTopicCard(topicKey) {
    var m = TOPIC_META[topicKey] || { emoji: '📋', title: topicKey, desc: '', border: 'border-gray-100', hover: 'hover:border-gray-400', hoverText: 'group-hover:text-gray-600' };
    var titleAttr = m.i18nTitle ? ' data-i18n="' + m.i18nTitle + '"' : '';
    var descAttr  = m.i18nDesc  ? ' data-i18n="' + m.i18nDesc  + '"' : '';
    return '<button onclick="startQuiz(\'' + topicKey + '\')" class="quiz-topic-btn bg-white rounded-2xl border-2 ' + m.border + ' p-6 text-left ' + m.hover + ' hover:shadow-lg transition-all group">'
         + '<div class="text-3xl mb-3">' + m.emoji + '</div>'
         + '<h3 class="text-lg font-bold text-gray-800 ' + m.hoverText + ' transition"' + titleAttr + '>' + m.title + '</h3>'
         + '<p class="text-sm text-gray-400 mt-1"' + descAttr + '>' + m.desc + '</p>'
         + '</button>';
}

// Renders topic cards immediately from TOPIC_META — no API call needed
function renderTopicCards(lang) {
    var topicsDiv = document.getElementById('quiz-topics');
    if (!topicsDiv || topicsDiv.classList.contains('hidden')) return;

    var subtitle = document.querySelector('[data-i18n="quizSubtitle"]');

    if (lang === 'uk') {
        if (subtitle) subtitle.textContent = 'Пройдіть тест про права українців у країнах ЄС — дізнайтеся більше!';
        var ukTopicOrder = ['uk_temporary_protection', 'uk_employment_rights', 'uk_housing_rights', 'uk_healthcare_rights', 'uk_children_education', 'uk_social_benefits', 'uk_border_rights'];
        topicsDiv.innerHTML = ukTopicOrder.map(buildTopicCard).join('');
    } else {
        var defaultOrder = ['fundamental_rights', 'police_rights', 'women_rights', 'consumer_rights', 'property_rights', 'labour_rights'];
        topicsDiv.innerHTML = defaultOrder.map(buildTopicCard).join('');
    }
    // Re-apply i18n translations to newly rendered cards (works for both EN and UK)
    if (typeof setLanguage === 'function') setLanguage(lang);
}

// ── Load questions from SQLite backend ─────────────────────────────────────

// Loads questions in the background — does NOT touch the topic card UI
async function loadQuizBank(lang) {
    if (_quizBankLoaded === lang && Object.keys(_quizBank).length > 0) return;
    try {
        const resp = await fetch('/api/quiz/questions?language=' + encodeURIComponent(lang));
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const data = await resp.json();
        _quizBank = data.topics || {};
        _quizBankLoaded = data.language || lang;
    } catch (e) {
        console.error('Failed to load quiz bank:', e);
        _quizBank = {};
        _quizBankLoaded = '';
    }
}

// ── Quiz Flow ──────────────────────────────────────────────────────────────

async function startQuiz(topic) {
    currentTopic = topic;
    currentQ = 0;
    score = 0;
    answered = false;

    document.getElementById('quiz-topics').classList.add('hidden');
    document.getElementById('quiz-container').classList.remove('hidden');
    document.getElementById('quiz-results').classList.add('hidden');

    const lang = getQuizLang();

    // If questions aren't cached yet, show a brief inline spinner and wait
    if (_quizBankLoaded !== lang || Object.keys(_quizBank).length === 0) {
        document.getElementById('quiz-question').textContent = '\u23F3 Loading questions...';
        document.getElementById('quiz-options').innerHTML = '';
        await loadQuizBank(lang);
    }

    const bank = _quizBank[topic] || [];
    if (bank.length === 0) {
        document.getElementById('quiz-question').textContent = 'No questions available for this topic.';
        return;
    }

    questions = shuffleArray([...bank]).slice(0, 5);
    renderQuestion();
}

function shuffleArray(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
}

function renderQuestion() {
    const q = questions[currentQ];
    answered = false;

    document.getElementById('quiz-q-number').textContent = 'Q' + (currentQ + 1);
    document.getElementById('quiz-question').textContent = q.q;
    document.getElementById('quiz-progress-text').textContent = (currentQ + 1) + ' / ' + questions.length;
    document.getElementById('quiz-progress-bar').style.width = ((currentQ) / questions.length * 100) + '%';
    document.getElementById('quiz-score-live').textContent = (t('quizScoreText') ? '' : 'Score: ') + score;
    document.getElementById('quiz-explanation').classList.add('hidden');
    document.getElementById('quiz-next-btn').textContent = (t('quizNextBtn') || 'Next Question') + ' \u2192';

    const optsDiv = document.getElementById('quiz-options');
    optsDiv.innerHTML = '';

    q.opts.forEach(function(opt, idx) {
        const btn = document.createElement('button');
        btn.className = 'quiz-option w-full text-left px-5 py-4 rounded-xl border-2 border-gray-200 hover:border-indigo-400 hover:bg-indigo-50 transition-all font-medium text-gray-700';
        btn.innerHTML = '<span class="inline-block w-8 h-8 rounded-lg bg-gray-100 text-center leading-8 font-bold text-gray-500 mr-3">' + String.fromCharCode(65 + idx) + '</span>' + opt;
        btn.onclick = function() { selectAnswer(idx); };
        optsDiv.appendChild(btn);
    });
}

function selectAnswer(idx) {
    if (answered) return;
    answered = true;

    const q = questions[currentQ];
    const correct = q.ans === idx;
    if (correct) score++;

    const buttons = document.querySelectorAll('.quiz-option');
    buttons.forEach(function(btn, i) {
        btn.disabled = true;
        btn.classList.remove('hover:border-indigo-400', 'hover:bg-indigo-50');
        if (i === q.ans) {
            btn.classList.remove('border-gray-200');
            btn.classList.add('border-green-500', 'bg-green-50', 'text-green-700');
        } else if (i === idx && !correct) {
            btn.classList.remove('border-gray-200');
            btn.classList.add('border-red-400', 'bg-red-50', 'text-red-700', 'line-through');
        }
    });

    const expDiv = document.getElementById('quiz-explanation');
    expDiv.classList.remove('hidden');
    document.getElementById('quiz-result-icon').textContent = correct ? '\u2705' : '\u274C';
    document.getElementById('quiz-result-text').textContent = correct ? (t('quizCorrect') || 'Correct!') : (t('quizIncorrect') || 'Incorrect');
    document.getElementById('quiz-result-text').className = 'font-bold text-lg ' + (correct ? 'text-green-700' : 'text-red-700');
    document.getElementById('quiz-explanation-text').textContent = q.explain;
    document.getElementById('quiz-score-live').textContent = '' + score;

    if (currentQ === questions.length - 1) {
        document.getElementById('quiz-next-btn').textContent = (t('quizSeeResults') || 'See Results') + ' \uD83C\uDFC6';
    }
}

function nextQuestion() {
    currentQ++;
    if (currentQ >= questions.length) {
        showResults();
        return;
    }
    renderQuestion();
}

function showResults() {
    document.getElementById('quiz-container').classList.add('hidden');
    document.getElementById('quiz-results').classList.remove('hidden');

    const pct = Math.round((score / questions.length) * 100);
    const scoreText = (t('quizScoreText') || 'You scored {score} out of {total} ({pct}%)')
        .replace('{score}', score)
        .replace('{total}', questions.length)
        .replace('{pct}', pct);
    document.getElementById('results-score').textContent = scoreText;

    setTimeout(function() {
        document.getElementById('results-bar').style.width = pct + '%';
    }, 100);

    var emoji, message, badge;
    if (pct === 100) {
        emoji = '\uD83C\uDFC6'; message = 'Perfect! You know your rights amazingly well!'; badge = 'Legal Scholar \uD83C\uDF93';
    } else if (pct >= 80) {
        emoji = '\uD83C\uDF1F'; message = 'Excellent! You have strong legal awareness.'; badge = 'Rights Champion \uD83D\uDCAA';
    } else if (pct >= 60) {
        emoji = '\uD83D\uDC4D'; message = 'Good knowledge! Keep learning to strengthen your rights awareness.'; badge = 'Aware Citizen \uD83D\uDCDA';
    } else if (pct >= 40) {
        emoji = '\uD83D\uDCD6'; message = "You're getting there! Chat with our AI to learn more about your rights."; badge = '';
    } else {
        emoji = '\uD83D\uDCA1'; message = "Don't worry! Use DHARMA-NYAYA to learn about your legal rights anytime."; badge = '';
    }

    document.getElementById('results-emoji').textContent = emoji;
    document.getElementById('results-message').textContent = message;

    if (badge) {
        document.getElementById('results-badge').classList.remove('hidden');
        document.getElementById('badge-text').textContent = badge;
    }
}

// ── On page load: render topic cards instantly, then prefetch questions ────
document.addEventListener('DOMContentLoaded', function() {
    var lang = getQuizLang();
    renderTopicCards(lang);        // instant — no API needed
    loadQuizBank(lang);            // background prefetch so questions are ready
});

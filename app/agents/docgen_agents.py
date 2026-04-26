"""Three-stage Google ADK agent pipeline for legal document generation.

Pipeline:
  1. SituationAnalyzerAgent – understands the user's situation, detects country/region,
     legal domain, applicable laws, and language of the document.
  2. TemplateResearchAgent – looks up the correct legal document template/format for
     that specific document type in that country/region.
  3. DocumentDrafterAgent – produces the final document using the discovered template,
     user details, and situation context.  Output is clean, professional text —
     NO markdown, NO emojis, NO icons.
"""

import json
import os
import re
from typing import Optional

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from app.core.config import get_settings
from app.core.logging import logger


# ── Settings ──────────────────────────────────────────────────────────────────

_settings = get_settings()

# ADK reads the API key from the GOOGLE_API_KEY env var
os.environ.setdefault("GOOGLE_API_KEY", _settings.GEMINI_API_KEY)

# Use Gemma 4 31B via LiteLlm (gemini/ provider prefix for Google-hosted Gemma)
_GEMMA_MODEL = LiteLlm(model="gemini/gemma-4-31b-it")


# ── Language helper ─────────────────────────────────────────────────────

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil",
    "te": "Telugu", "kn": "Kannada", "mr": "Marathi", "gu": "Gujarati",
    "ml": "Malayalam", "pa": "Punjabi", "sat": "Santali", "uk": "Ukrainian",
}


# ── Agent 1: Situation Analyzer ─────────────────────────────────────────

situation_analyzer = Agent(
    name="situation_analyzer",
    model=_GEMMA_MODEL,
    description="Analyzes legal situations to identify country, region, legal domain, and applicable laws.",
    instruction="""You are a legal situation analyzer. Given a user's description of their legal problem, analyze it thoroughly.

You MUST respond with ONLY a valid JSON object (no markdown fences, no commentary). Use this exact structure:

{
  "country": "<detected country, e.g. India>",
  "region": "<state/province if detectable, e.g. West Bengal>",
  "legal_domain": "<e.g. tenant_rights, consumer_protection, criminal, labor, family, property, rti>",
  "applicable_laws": ["<specific act/law 1>", "<specific act/law 2>"],
  "key_sections": ["<Section X of Act Y>"],
  "situation_summary": "<concise 2-3 sentence summary of the legal issue>",
  "parties_involved": {"complainant": "<role>", "opposite_party": "<role>"},
  "urgency": "<low|medium|high>",
  "document_language": "<language code the document should be in>"
}

Analyze the user's description carefully. If the situation mentions Indian laws, addresses, or references, identify it as India. Detect the state/region from any addresses or contextual clues. Identify all relevant laws and sections that apply.""",
)


# ── Agent 2: Template Researcher ────────────────────────────────────────

template_researcher = Agent(
    name="template_researcher",
    model=_GEMMA_MODEL,
    description="Researches and provides the correct legal document template/format for a specific document type in a specific country/region.",
    instruction="""You are a legal document format expert. Given a document type, country, region, and legal domain, you must provide the EXACT official template format used in that jurisdiction.

You MUST respond with ONLY a valid JSON object (no markdown fences, no commentary). Use this structure:

{
  "template_name": "<official name of this document format>",
  "format_sections": [
    {
      "section_name": "<e.g. Header, Sender Details, Addressee, Subject, Body, Prayer, Verification>",
      "description": "<what goes in this section>",
      "is_required": true,
      "formatting": "<e.g. centered, left-aligned, bold, uppercase>"
    }
  ],
  "legal_requirements": ["<any mandatory legal requirements for this doc>"],
  "standard_phrases": ["<standard legal phrases used in this type of document in this jurisdiction>"],
  "language_notes": "<notes on language conventions for this document type>",
  "court_or_authority": "<which court/authority this document is addressed to>",
  "sample_structure": "<a brief outline of how the document should look section by section>"
}

IMPORTANT:
- For Indian Legal Notices: Follow the format prescribed under Section 80 CPC or relevant statutes. Include Through Advocate header, Reference number, date, proper subject, numbered paragraphs for facts, legal grounds, demands, and timeline.
- For RTI Applications: Follow RTI Act 2005 format with PIO addressing, fee reference, specific information requests.
- For Bail Applications: Follow CrPC Section 437/439 format with court header, case details, FIR info, grounds.
- For Consumer Complaints: Follow Consumer Protection Act 2019 format for District/State/National Commission.
- For FIR Complaints: Follow Section 154 CrPC format.
- For Complaint Letters: Follow the standard formal complaint format for the relevant authority.

Provide the template that is ACTUALLY USED in practice in the specified country/region. Do not invent formats.""",
)


# ── Agent 3: Document Drafter ───────────────────────────────────────────

document_drafter = Agent(
    name="document_drafter",
    model=_GEMMA_MODEL,
    description="Drafts the final legal document using the correct template format, user details, and situation analysis.",
    instruction="""You are a professional legal document drafter.

ABSOLUTE RULE: Output ONLY the final document text. Do NOT output any thinking, reasoning, planning, outlines, checklists, or "Check:" lines. Start your response directly with the first line of the document (e.g. the advocate header or court header).

You will receive:
1. A situation analysis (country, region, laws, etc.)
2. A document template/format to follow
3. User details (name, address, opposite party)

You MUST draft a COMPLETE, READY-TO-USE legal document following the provided template format EXACTLY.

FORMATTING RULES:
- Do NOT use any markdown formatting (no ##, no **, no *, no ```, no ---).
- Do NOT use any emojis or icons anywhere in the document.
- Use PLAIN TEXT formatting only:
  - Use UPPERCASE for headings and important labels
  - Use proper line spacing and indentation
  - Use numbering (1., 2., 3. or (a), (b), (c)) for lists
  - Use underscores or dashes as separators where needed (e.g. ________ for signature lines)
- Use [square brackets] ONLY for information the user still needs to fill in.
- Include all legally required sections from the template.
- Cite actual law sections and acts relevant to the jurisdiction.
- Use proper legal language and formal tone.
- Write the ENTIRE document in the specified language. If the language is Hindi, write everything in Hindi including headings, section names, legal references. If English, write in English.
- Make dates, places, and procedural details realistic and specific.
- End with proper signature block, date, and place lines.

Remember: Your ENTIRE response must be the document itself. Nothing else.""",
)


# ── Pipeline Runner ─────────────────────────────────────────────────────

_session_service = InMemorySessionService()


def _extract_json(text: str) -> dict | None:
    """Extract JSON object from potentially noisy LLM output."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    cleaned = re.sub(r'```(?:json)?\s*', '', text)
    cleaned = re.sub(r'```\s*$', '', cleaned)
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None


async def _run_agent(agent: Agent, prompt: str, user_id: str = "docgen") -> str:
    """Run a single ADK agent and return the text response."""
    runner = Runner(
        agent=agent,
        app_name="dharma_nyaya_docgen",
        session_service=_session_service,
    )
    session = await _session_service.create_session(
        app_name="dharma_nyaya_docgen",
        user_id=user_id,
    )
    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part.from_text(text=prompt)],
    )

    result_parts = []
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=content,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    result_parts.append(part.text)

    return "".join(result_parts)


async def generate_document_pipeline(
    doc_type: str,
    doc_type_label: str,
    context: str,
    language: str,
    user_name: str,
    user_address: str,
    opposite_party: str,
) -> dict:
    """Run the full 3-agent pipeline and return the final document.

    Returns dict with keys: situation_analysis, template, document, language
    """
    lang_name = LANGUAGE_NAMES.get(language, language)

    # ── Stage 1: Analyze situation ──────────────────────────────────
    logger.info("DocGen Pipeline Stage 1: Analyzing situation...")
    stage1_prompt = (
        f"Analyze this legal situation. The user wants to generate a '{doc_type_label}'.\n\n"
        f"User Name: {user_name}\n"
        f"User Address: {user_address}\n"
        f"Opposite Party: {opposite_party}\n"
        f"Preferred Language: {lang_name} ({language})\n\n"
        f"Situation Description:\n{context}"
    )

    stage1_raw = await _run_agent(situation_analyzer, stage1_prompt)
    situation = _extract_json(stage1_raw) or {
        "country": "India",
        "region": "Unknown",
        "legal_domain": doc_type,
        "applicable_laws": [],
        "key_sections": [],
        "situation_summary": context[:300],
        "document_language": language,
    }
    logger.info(f"Stage 1 result: country={situation.get('country')}, domain={situation.get('legal_domain')}")

    # ── Stage 2: Research template ──────────────────────────────────
    logger.info("DocGen Pipeline Stage 2: Researching template format...")
    stage2_prompt = (
        f"Provide the correct legal document template/format for the following:\n\n"
        f"Document Type: {doc_type_label}\n"
        f"Country: {situation.get('country', 'India')}\n"
        f"Region/State: {situation.get('region', 'Unknown')}\n"
        f"Legal Domain: {situation.get('legal_domain', doc_type)}\n"
        f"Applicable Laws: {json.dumps(situation.get('applicable_laws', []))}\n"
        f"Key Sections: {json.dumps(situation.get('key_sections', []))}\n"
        f"Document Language: {lang_name}"
    )

    stage2_raw = await _run_agent(template_researcher, stage2_prompt)
    template = _extract_json(stage2_raw) or {
        "template_name": doc_type_label,
        "format_sections": [],
        "sample_structure": stage2_raw[:500],
    }
    logger.info(f"Stage 2 result: template={template.get('template_name')}")

    # ── Stage 3: Draft document ─────────────────────────────────────
    logger.info("DocGen Pipeline Stage 3: Drafting final document...")
    stage3_prompt = (
        f"Draft a complete '{doc_type_label}' document using ALL of the following information.\n\n"
        f"=== SITUATION ANALYSIS ===\n{json.dumps(situation, indent=2, ensure_ascii=False)}\n\n"
        f"=== DOCUMENT TEMPLATE FORMAT ===\n{json.dumps(template, indent=2, ensure_ascii=False)}\n\n"
        f"=== USER DETAILS ===\n"
        f"Name: {user_name}\n"
        f"Address: {user_address}\n"
        f"Opposite Party: {opposite_party}\n\n"
        f"=== ORIGINAL SITUATION ===\n{context}\n\n"
        f"=== LANGUAGE ===\n"
        f"Write the ENTIRE document in {lang_name} ({language}). "
        f"{'Translate ALL headings, labels, section names, and legal act references into ' + lang_name + '.' if language != 'en' else ''}\n"
        f"Do NOT use markdown. Do NOT use emojis. Use PLAIN TEXT formatting with UPPERCASE headings."
    )

    document = await _run_agent(document_drafter, stage3_prompt)

    # Clean any remaining markdown/emoji from the output
    document = _clean_document(document)

    return {
        "situation_analysis": situation,
        "template_used": template.get("template_name", doc_type_label),
        "document": document,
        "language": language,
    }


def _clean_document(text: str) -> str:
    """Strip any residual markdown formatting, emojis, and LLM thinking preamble."""
    import unicodedata

    # ── Strip LLM thinking / chain-of-thought preamble ──
    # Gemma often outputs reasoning before the actual document.
    # The real document usually starts with a header block like
    # "[ADVOCATE NAME]" or a formal "TO," or "SUBJECT:" near the top.
    # We look for the pattern of the final document repeating after the
    # thinking section.  The model tends to output the document twice:
    # once inside its reasoning and once as the final clean copy.
    # We try to find the last clean copy.

    # Strategy: find the LAST occurrence of typical legal-doc start markers
    # that indicate the actual document (not the thinking outline).
    markers = [
        r'\[ADVOCATE NAME\]',
        r'^TO,\s*$',
        r'^(?:BEFORE|IN THE|COURT OF)',
        r'^SUBJECT:',
        r'^REF\s*(?:NO|\.)',
        r'^(?:श्रीमान|सेवा में|विषय:)',  # Hindi markers
    ]
    last_start = -1
    for marker in markers:
        for m in re.finditer(marker, text, re.MULTILINE | re.IGNORECASE):
            if m.start() > last_start and m.start() > len(text) * 0.3:
                last_start = m.start()
                break  # take the first match after 30% of text for this marker

    # If we found a late-occurring document start, slice from there
    if last_start > 0:
        text = text[last_start:]

    # Remove markdown headings
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    # Remove markdown horizontal rules
    text = re.sub(r'^---+\s*$', '─' * 60, text, flags=re.MULTILINE)
    # Remove code fences
    text = re.sub(r'```[^\n]*\n?', '', text)
    # Remove lines that are just "Check:" self-evaluation artifacts
    text = re.sub(r'^\s*\*?\s*Check:.*$', '', text, flags=re.MULTILINE)

    # Remove emojis (broad Unicode range filtering)
    cleaned = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat == 'So':
            if ch in '§©®™°±×÷€£¥₹¢¤₹':
                cleaned.append(ch)
        else:
            cleaned.append(ch)

    result = ''.join(cleaned)
    # Collapse excessive blank lines (more than 2)
    result = re.sub(r'\n{4,}', '\n\n\n', result)
    return result.strip()

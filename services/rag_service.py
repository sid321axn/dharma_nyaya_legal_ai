"""RAG (Retrieval-Augmented Generation) service stub.
Replace with vector DB (e.g., ChromaDB, Pinecone) in production.
"""

from typing import Optional
from app.core.logging import logger


# Stub legal knowledge base — in production, replace with vector search
_LEGAL_KB: list[dict] = [
    {
        "domain": "labor",
        "title": "Minimum Wages Act, 1948",
        "sections": ["Section 3 - Fixing of minimum rates of wages",
                      "Section 12 - Payment of minimum rates of wages"],
        "summary": "Employers must pay wages not less than the minimum rate fixed by the government.",
    },
    {
        "domain": "consumer",
        "title": "Consumer Protection Act, 2019",
        "sections": ["Section 2(7) - Definition of Consumer",
                      "Section 35 - Jurisdiction of District Commission"],
        "summary": "Consumers can file complaints for defective goods or deficient services.",
    },
    {
        "domain": "property",
        "title": "Transfer of Property Act, 1882",
        "sections": ["Section 54 - Sale defined",
                      "Section 58 - Mortgage defined"],
        "summary": "Governs transfer of property between living persons.",
    },
    {
        "domain": "family",
        "title": "Protection of Women from Domestic Violence Act, 2005",
        "sections": ["Section 3 - Definition of domestic violence",
                      "Section 12 - Application to Magistrate"],
        "summary": "Provides protection to women from domestic violence.",
    },
    {
        "domain": "criminal",
        "title": "Indian Penal Code, 1860",
        "sections": ["Section 302 - Punishment for murder",
                      "Section 420 - Cheating"],
        "summary": "Defines criminal offences and their punishments.",
    },
    {
        "domain": "rti",
        "title": "Right to Information Act, 2005",
        "sections": ["Section 6 - Request for obtaining information",
                      "Section 7 - Disposal of request"],
        "summary": "Citizens can request information from public authorities.",
    },
]


class RAGService:
    """Stub retrieval-augmented generation service."""

    async def search(self, query: str, domain: Optional[str] = None,
                     top_k: int = 3) -> list[dict]:
        """Search the legal knowledge base (stub)."""
        results = _LEGAL_KB
        if domain:
            results = [r for r in results if r["domain"] == domain.lower()]

        # Simple keyword matching (replace with vector similarity in production)
        query_lower = query.lower()
        scored = []
        for item in results:
            score = sum(1 for word in query_lower.split()
                        if word in item["title"].lower() or word in item["summary"].lower())
            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    def format_context(self, results: list[dict]) -> str:
        """Format search results as context for the LLM."""
        if not results:
            return "No specific legal references found."

        parts = []
        for r in results:
            sections = ", ".join(r["sections"])
            parts.append(f"**{r['title']}**\nSections: {sections}\n{r['summary']}")
        return "\n\n".join(parts)


rag_service = RAGService()

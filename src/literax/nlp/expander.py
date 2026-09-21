from typing import List, Dict

class QueryExpander:
    """Generates academic query expansions, boolean queries, and bilingual translations."""

    ID_TO_EN_MAP: Dict[str, str] = {
        "deteksi": "detection",
        "klasifikasi": "classification",
        "prediksi": "prediction",
        "menggunakan": "using",
        "dengan": "with",
        "pembelajaran mesin": "machine learning",
        "jaringan saraf": "neural network",
        "kecerdasan buatan": "artificial intelligence",
        "keamanan siber": "cybersecurity",
        "analisis": "analysis",
        "optimasi": "optimization",
        "metode": "method"
    }

    SYNONYMS: Dict[str, List[str]] = {
        "machine learning": ["deep learning", "artificial intelligence", "ML"],
        "phishing": ["phishing URL", "phishing website", "malicious domain"],
        "detection": ["classification", "identification", "recognition"],
        "cybersecurity": ["network security", "information security"]
    }

    @classmethod
    def get_synonyms(cls, term: str) -> List[str]:
        """Retrieves known academic synonyms for a given term, if available."""
        return cls.SYNONYMS.get(term.lower().strip(), []).copy()

    @classmethod
    def translate_to_english(cls, query: str) -> str:
        """Translates known Indonesian academic keywords to English."""
        text = query.lower()
        for id_phrase, en_phrase in sorted(cls.ID_TO_EN_MAP.items(), key=lambda x: len(x[0]), reverse=True):
            if id_phrase in text:
                text = text.replace(id_phrase, en_phrase)
        return text

    @classmethod
    def expand(cls, corrected_query: str) -> List[str]:
        """Expands a single query into a list of targeted academic search strings."""
        expansions: List[str] = [corrected_query]

        # 1. English translated equivalent
        en_version = cls.translate_to_english(corrected_query)
        if en_version != corrected_query:
            expansions.append(en_version)

        # 2. Boolean phrase combination
        if "machine learning" in en_version and "phishing" in en_version:
            expansions.append('"machine learning" AND "phishing detection"')
            expansions.append('"phishing URL classification" AND "deep learning"')
            expansions.append('"AI-based phishing detection"')
        elif "phishing" in en_version:
            expansions.append(f'"{en_version}"')
            expansions.append(f"{en_version} survey")

        # Deduplicate while preserving order
        seen = set()
        unique_expansions = []
        for q in expansions:
            q_clean = q.strip()
            if q_clean and q_clean not in seen:
                seen.add(q_clean)
                unique_expansions.append(q_clean)

        return unique_expansions

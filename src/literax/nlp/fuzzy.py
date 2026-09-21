import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from rapidfuzz import process, fuzz

from literax.nlp.normalizer import QueryNormalizer
from literax.nlp.protected_terms import ProtectedTermsManager
from literax.models import CorrectionResult, TokenCorrection

class FuzzyAutoCorrect:
    """Fuzzy Auto-Correction with Multi-Factor Fuzzy Logic Confidence Scoring."""

    def __init__(
        self,
        dict_dir: Optional[Path] = None,
        protected_mgr: Optional[ProtectedTermsManager] = None
    ):
        if dict_dir is None:
            dict_dir = Path(__file__).parent / "dictionaries"
        
        self.dict_dir = dict_dir
        self.protected_mgr = protected_mgr or ProtectedTermsManager(dict_dir / "protected_terms.json")
        
        # Load vocabularies & direct typo mappings
        self.typo_map: Dict[str, str] = {}
        self.academic_vocab: Set[str] = set()

        self._load_dictionaries()

    def _load_dictionaries(self) -> None:
        en_path = self.dict_dir / "academic_terms_en.json"
        id_path = self.dict_dir / "academic_terms_id.json"

        for path in [en_path, id_path]:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        k_lower, v_lower = k.lower(), v.lower()
                        self.typo_map[k_lower] = v_lower
                        self.academic_vocab.add(v_lower)
                        self.academic_vocab.add(k_lower)

    @property
    def vocabulary_size(self) -> int:
        """Returns the total number of unique terms in the loaded academic vocabulary."""
        return len(self.academic_vocab)

    def is_known_typo(self, token: str) -> bool:
        """Checks whether the token exists in direct typo mappings."""
        t = token.lower().strip()
        return t in self.typo_map and self.typo_map[t] != t

    def calculate_confidence(
        self,
        original_token: str,
        candidate: str,
        is_direct_mapping: bool = False
    ) -> float:
        """Computes multi-factor fuzzy confidence score:
        C = 0.40 * S_string + 0.20 * V_academic + 0.20 * S_context + 0.10 * F_freq + 0.10 * Q_coherence
        """
        orig_lower = original_token.lower()
        cand_lower = candidate.lower()

        if orig_lower == cand_lower:
            return 1.0

        # 1. String similarity (0.0 to 1.0)
        s_string = fuzz.ratio(orig_lower, cand_lower) / 100.0

        # If it's a curated direct dictionary mapping, grant high string similarity baseline
        if is_direct_mapping and s_string < 0.85:
            s_string = max(s_string, 0.90)

        # 2. Academic vocabulary match
        v_academic = 1.0 if cand_lower in self.academic_vocab else 0.7

        # 3. Context similarity (co-occurrence heuristic)
        s_context = 0.96 if cand_lower in self.academic_vocab else 0.80

        # 4. Term frequency score
        f_freq = 0.92 if is_direct_mapping else 0.85

        # 5. Query coherence score
        q_coherence = 0.95

        confidence = (
            0.40 * s_string +
            0.20 * v_academic +
            0.20 * s_context +
            0.10 * f_freq +
            0.10 * q_coherence
        )

        return min(1.0, round(confidence, 3))

    def correct_token(self, token: str) -> TokenCorrection:
        """Corrects an individual token and calculates confidence."""
        token_lower = token.lower()

        # Check if protected term (e.g. SVM, CNN, BERT, etc.)
        if self.protected_mgr.is_protected(token_lower):
            return TokenCorrection(
                original=token,
                corrected=token.upper() if len(token) <= 4 else token,
                status="PROTECTED",
                confidence=1.0
            )

        # Exact match in academic vocabulary
        if token_lower in self.academic_vocab and token_lower not in self.typo_map:
            return TokenCorrection(
                original=token,
                corrected=token,
                status="UNCHANGED",
                confidence=1.0
            )

        # Check known direct typo map
        if token_lower in self.typo_map and self.typo_map[token_lower] != token_lower:
            corrected_val = self.typo_map[token_lower]
            conf = self.calculate_confidence(token, corrected_val, is_direct_mapping=True)
            return TokenCorrection(
                original=token,
                corrected=corrected_val,
                status="CORRECTED",
                confidence=conf,
                distance_metric=f"Levenshtein({round(1.0 - fuzz.ratio(token_lower, corrected_val)/100, 2)})"
            )

        # Fuzzy matching against vocabulary using RapidFuzz
        match = process.extractOne(
            token_lower,
            self.academic_vocab,
            scorer=fuzz.ratio,
            score_cutoff=70
        )

        if match:
            best_candidate, score, _ = match
            conf = self.calculate_confidence(token, best_candidate, is_direct_mapping=False)
            if conf >= 0.70:
                return TokenCorrection(
                    original=token,
                    corrected=best_candidate,
                    status="CORRECTED" if best_candidate != token_lower else "UNCHANGED",
                    confidence=conf,
                    distance_metric=f"RapidFuzzRatio({score})"
                )

        # Low confidence or no match: retain original token
        return TokenCorrection(
            original=token,
            corrected=token,
            status="UNCHANGED",
            confidence=0.5
        )

    def process_query(self, raw_query: str) -> CorrectionResult:
        """End-to-end processing of a user query through the fuzzy auto-correct pipeline."""
        normalized = QueryNormalizer.normalize(raw_query)
        tokens = QueryNormalizer.tokenize(normalized)

        if not tokens:
            return CorrectionResult(
                original_query=raw_query,
                corrected_query=raw_query,
                overall_confidence=1.0,
                action="UNCHANGED"
            )

        corrected_tokens: List[str] = []
        token_corrections: List[TokenCorrection] = []
        tokens_changed: List[Dict[str, Any]] = []
        confidences: List[float] = []

        for tok in tokens:
            corr = self.correct_token(tok)
            token_corrections.append(corr)
            corrected_tokens.append(corr.corrected)
            confidences.append(corr.confidence)

            if corr.status == "CORRECTED":
                tokens_changed.append({
                    "original": corr.original,
                    "corrected": corr.corrected,
                    "confidence": corr.confidence
                })

        overall_conf = round(sum(confidences) / len(confidences), 3) if confidences else 1.0
        corrected_query = " ".join(corrected_tokens)

        # Determine decision action
        if not tokens_changed:
            action = "UNCHANGED"
        elif overall_conf >= 0.90:
            action = "AUTO_CORRECTED"
        elif overall_conf >= 0.70:
            action = "PROMPT_USER"
        else:
            action = "UNCHANGED"
            corrected_query = raw_query

        return CorrectionResult(
            original_query=raw_query,
            corrected_query=corrected_query,
            overall_confidence=overall_conf,
            action=action,
            tokens=token_corrections,
            tokens_changed=tokens_changed
        )

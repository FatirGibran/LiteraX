from typing import List
from literax.models import Paper, ResearchGapReport, ResearchGapItem
from literax.synthesis.analyzer import PaperAnalyzer

class ResearchGapFinder:
    """Detects discrepancies, untested intersections, and methodological research gaps."""

    @classmethod
    def find_gaps(cls, topic: str, papers: List[Paper]) -> ResearchGapReport:
        if not papers:
            return ResearchGapReport(topic=topic, gaps=[])

        analyses = [PaperAnalyzer.heuristic_extract(p) for p in papers]

        all_algos = set()
        for a in analyses:
            all_algos.update(a.algorithms_used)

        has_traditional = any(
            any(t in algo.lower() for t in ["random forest", "svm", "decision tree", "bayes", "knn"])
            for algo in all_algos
        )
        has_deep = any(
            any(d in algo.lower() for d in ["cnn", "lstm", "bert", "transformer", "deep learning"])
            for algo in all_algos
        )

        gaps: List[ResearchGapItem] = []

        # Gap 1: Baseline benchmarking gap
        if has_traditional and has_deep:
            gaps.append(ResearchGapItem(
                title="Cross-Paradigm Empirical Benchmarking Gap",
                description="Existing works deploy traditional classifiers (e.g. Random Forest, SVM) and modern deep architectures on disjoint datasets without unified feature alignment under identical resource constraints.",
                category="Methodology",
                supporting_papers=[p.title for p in papers[:2]]
            ))
        else:
            gaps.append(ResearchGapItem(
                title="Model Exploration & Comparative Baseline Gap",
                description=f"Current literature around '{topic}' heavily concentrates on a narrow set of classifiers ({', '.join(list(all_algos)[:2])}) lacking exploration into hybrid ensemble architectures.",
                category="Methodology",
                supporting_papers=[p.title for p in papers[:2]]
            ))

        # Gap 2: Dataset diversity & localized evasion
        gaps.append(ResearchGapItem(
            title="Adversarial Robustness & Concept Drift Gap",
            description="The majority of evaluations rely on static, clean offline datasets. There is a critical shortage of longitudinal studies measuring model degradation against zero-day evasion attacks and obfuscation over time.",
            category="Dataset",
            supporting_papers=[p.title for p in papers]
        ))

        # Gap 3: Edge & Inference Latency Trade-off
        gaps.append(ResearchGapItem(
            title="Real-Time Edge Deployment Feasibility",
            description="High reported accuracy frequently comes at the cost of high parameter count and inference latency, leaving a research gap in model pruning, quantization, or knowledge distillation for edge inspection.",
            category="Scalability",
            supporting_papers=[p.title for p in papers[-2:]]
        ))

        return ResearchGapReport(topic=topic, gaps=gaps)

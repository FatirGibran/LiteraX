import re
from typing import List, Optional
from literax.models import Paper, BrainstormResult, BrainstormIdea

class ResearchBrainstormer:
    """AI Research Brainstorming & Ideation Engine.
    
    Synthesizes academic problems, formulates high-impact thesis/paper topics,
    recommends state-of-the-art methodology combinations, and highlights potential novelty.
    """

    @classmethod
    def generate(cls, topic: str, seed_papers: Optional[List[Paper]] = None) -> BrainstormResult:
        papers = seed_papers or []
        clean_topic = topic.strip()
        topic_title = clean_topic.title()

        # Extract context algorithms or models from seed papers if available
        observed_algos = []
        for p in papers:
            text = f"{p.title} {p.abstract or ''}".lower()
            for algo in ["transformer", "bert", "lstm", "cnn", "random forest", "xgboost", "svm", "gnn", "llm"]:
                if algo in text and algo.upper() not in [a.upper() for a in observed_algos]:
                    observed_algos.append(algo.title())

        primary_algo = observed_algos[0] if observed_algos else "Deep Neural Architectures"
        secondary_algo = observed_algos[1] if len(observed_algos) > 1 else "Ensemble Classifiers"

        core_problem = (
            f"Penelitian pada domain '{clean_topic}' saat ini menghadapi tantangan trade-off antara "
            f"akurasi deteksi/prediksi, ketahanan terhadap data dinamis (concept drift/zero-day), "
            f"dan efisiensi komputasi untuk implementasi skala produksi riil."
        )

        # Idea 1: Hybrid / Multi-modal Architectural Innovation
        idea_1 = BrainstormIdea(
            title_id=f"Pengembangan Arsitektur Hybrid {primary_algo} dan Feature Engineering Adaptif untuk {topic_title}",
            title_en=f"A Novel Hybrid {primary_algo} with Adaptive Feature Representation for Robust {topic_title}",
            focus="Inovasi Arsitektur & Penguatan Representasi Fitur",
            suggested_methods=[primary_algo, "Attention Mechanism", "Lightweight Gradient Boosting"],
            suggested_datasets=["Standard Benchmark Open Corpus", "Kaggle & HuggingFace Datasets"],
            novelty_points="Menggabungkan representasi fitur global dan kontekstual lokal untuk mengatasi keterbatasan model tunggal.",
            expected_contribution="Meningkatkan metrik F1-score dan mengurangi False Positive Rate (FPR) secara signifikan."
        )

        # Idea 2: Robustness against Adversarial Perturbations & Concept Drift
        idea_2 = BrainstormIdea(
            title_id=f"Analisis Ketahanan Adversarial dan Mitigasi Concept Drift pada Sistem {topic_title}",
            title_en=f"Longitudinal Robustness and Adversarial Defense Framework for {topic_title}",
            focus="Adversarial Resilience & Longitudinal Drift Evaluation",
            suggested_methods=["Adversarial Training", "Continual Learning", "Self-Supervised Pretraining"],
            suggested_datasets=["Longitudinal Real-world Stream Data", "Adversarially Perturbed Benchmarks"],
            novelty_points="Evaluasi performa model di bawah kondisi perturbasi zero-day dan perubahan distribusi data berkala.",
            expected_contribution="Menyediakan protokol evaluasi empiris baru yang lebih tahan terhadap serangan evasif di dunia nyata."
        )

        # Idea 3: Edge Computing / Resource-Constrained Deployment
        idea_3 = BrainstormIdea(
            title_id=f"Optimasi Model {topic_title} Menggunakan Knowledge Distillation untuk Perangkat Edge / IoT",
            title_en=f"Lightweight {topic_title} via Knowledge Distillation and Quantization for Edge Devices",
            focus="Efisiensi Komputasi & Inferensi Real-time",
            suggested_methods=["Knowledge Distillation", "Post-Training Quantization (INT8)", "Model Pruning"],
            suggested_datasets=["Edge-Emulated IoT Traffic", "Resource-Constrained Embedded Corpus"],
            novelty_points="Memangkas ukuran model dan latensi inferensi hingga 70% dengan degradasi akurasi di bawah 1%.",
            expected_contribution="Memungkinkan deteksi/analisis dilakukan secara lokal di perangkat tanpa ketergantungan server cloud."
        )

        landscape = (
            f"Spektrum metodologi pada topik '{clean_topic}' saat ini didominasi oleh "
            f"{primary_algo} dan varian {secondary_algo}. Tren mutakhir bergerak menuju "
            f"model yang lebih hemat resource (efficient AI) dan mampu menjelaskan keputusan (Explainable AI / XAI)."
        )

        datasets = [
            "UCI Machine Learning Repository / OpenML Benchmark",
            "Kaggle & HuggingFace Datasets (Domain-Specific)",
            "IEEE Dataport / Mendeley Data Open Repositories"
        ]

        challenges = [
            "Ketidakseimbangan kelas (Class Imbalance) yang ekstrem pada data riil.",
            "Keterbatasan anotasi data berlabel (kebutuhan teknik semi-supervised / self-supervised).",
            "Menjaga interpretabilitas model agar hasil prediksi dapat dipertanggungjawabkan (XAI)."
        ]

        return BrainstormResult(
            topic=clean_topic,
            core_problem=core_problem,
            ideas=[idea_1, idea_2, idea_3],
            methodology_landscape=landscape,
            benchmark_datasets=datasets,
            practical_challenges=challenges,
            seed_papers=papers[:3]
        )

    @classmethod
    def to_markdown(cls, result: BrainstormResult) -> str:
        """Renders brainstorming dossier into structured Markdown format."""
        lines = [
            f"💡 *RESEARCH BRAINSTORMING DOSSIER*\n"
            f"🎯 *Topik:* `{result.topic}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
            f"🚨 *Rumusan Masalah Utama:*\n{result.core_problem}\n",
            f"🚀 *REKOMENDASI 3 TOPIK / JUDUL RISET:*\n"
        ]

        for idx, idea in enumerate(result.ideas, 1):
            methods_str = ", ".join(idea.suggested_methods)
            lines.append(
                f"*{idx}. {idea.title_id}*\n"
                f"   🇬🇧 _{idea.title_en}_\n"
                f"   • *Fokus:* {idea.focus}\n"
                f"   • *Metodologi Rekomendasi:* `{methods_str}`\n"
                f"   • *Reasoning Kebaruan (Novelty):* {idea.novelty_points}\n"
                f"   • *Kontribusi:* {idea.expected_contribution}\n"
            )

        lines.append("📊 *Rekomendasi Dataset Acuan:*")
        for ds in result.benchmark_datasets:
            lines.append(f"• {ds}")

        lines.append("\n⚠️ *Tantangan Eksperimen yang Perlu Diantisipasi:*")
        for ch in result.practical_challenges:
            lines.append(f"• {ch}")

        if result.seed_papers:
            lines.append("\n📚 *Artikel Acuan & Direct Link Rekomendasi:*")
            for p in result.seed_papers:
                link = p.direct_url or "https://scholar.google.com"
                year_str = f"({p.year})" if p.year else ""
                lines.append(f"• [{p.title}]({link}) {year_str}")

        return "\n".join(lines)

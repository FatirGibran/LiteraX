import asyncio
from literax.nlp.fuzzy import FuzzyAutoCorrect
from literax.engine.aggregator import PaperAggregator
from literax.models import SearchQuery

async def run_test():
    print("Testing Fuzzy Engine...")
    f = FuzzyAutoCorrect()
    res = f.process_query("bantu aku cari artikel tentang soekarno")
    print("Fuzzy result:", res.action, res.corrected_query)

    print("Testing Aggregator with 'soekarno'...")
    a = PaperAggregator()
    q = SearchQuery(raw_query="soekarno", limit=3)
    papers = await a.search(q)
    print("Papers found:", len(papers))
    for p in papers:
        print(f" - {p.title} ({p.year}) - {p.source}")

if __name__ == "__main__":
    asyncio.run(run_test())

import pytest
from unittest.mock import patch, MagicMock
from literax.providers.sinta_garuda import SintaGarudaProvider
from literax.models import SearchQuery

@pytest.mark.asyncio
async def test_sinta_garuda_search_success():
    provider = SintaGarudaProvider()
    mock_html = """
    <html>
      <body>
        <div class="article-item">
          <a class="title-article" href="/documents/detail/12345">
            Sistem Pakar Diagnosa Penyakit Tanaman Padi
          </a>
          <div class="author-article">Budi Santoso, Siti Rahayu</div>
          <div class="abstract-article">
            Penelitian ini membahas penerapan metode Certainty Factor untuk mendiagnosa hama padi.
          </div>
        </div>
      </body>
    </html>
    """

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = mock_html
        mock_get.return_value = mock_resp

        results = await provider.search(SearchQuery(raw_query="sistem pakar padi"))
        assert len(results) == 1
        paper = results[0]
        assert paper.title == "Sistem Pakar Diagnosa Penyakit Tanaman Padi"
        assert len(paper.authors) == 2
        assert paper.authors[0].name == "Budi Santoso"
        assert paper.authors[1].name == "Siti Rahayu"
        assert "Certainty Factor" in (paper.abstract or "")
        assert paper.open_access is True
        assert paper.source == "GARUDA / SINTA"
        assert paper.landing_page_url == "https://garuda.kemdikbud.go.id/documents?q=sistem pakar padi"

@pytest.mark.asyncio
async def test_sinta_garuda_non_200():
    provider = SintaGarudaProvider()
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_get.return_value = mock_resp

        results = await provider.search(SearchQuery(raw_query="kecerdasan buatan"))
        assert results == []

@pytest.mark.asyncio
async def test_sinta_garuda_exception():
    provider = SintaGarudaProvider()
    with patch("httpx.AsyncClient.get", side_effect=Exception("ReadTimeout")):
        results = await provider.search(SearchQuery(raw_query="machine learning"))
        assert results == []

@pytest.mark.asyncio
async def test_sinta_garuda_stubs():
    provider = SintaGarudaProvider()
    assert await provider.get_paper("garuda_123") is None
    assert await provider.get_citation("garuda_123") == ""

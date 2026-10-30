import pytest

from app.tools import fetch
from app.tools.fetch import _validate_url, fetch_webpage


@pytest.mark.parametrize("url", [
    "file:///etc/passwd", "http://localhost:8000/", "http://127.0.0.1/",
    "http://10.0.0.5/", "http://169.254.169.254/latest/meta-data/",
    "http://user:pw@example.com/",
])
def test_rejects_unsafe_urls(url):
    with pytest.raises(ValueError):
        _validate_url(url)


class FakeResponse:
    def __init__(self, status=200, headers=None, body=b"", encoding="utf-8"):
        self.status_code = status
        self.headers = headers or {"Content-Type": "text/html; charset=utf-8"}
        self.encoding = encoding
        self._body = body

    def iter_content(self, chunk_size=1):
        for i in range(0, len(self._body), chunk_size):
            yield self._body[i:i + chunk_size]

    def close(self):
        pass


HTML = b"""<html><head><title>Research Guide</title></head><body>
<script>ignore this script</script><nav>Navigation</nav>
<main><p>Evidence from the webpage.</p></main></body></html>"""


@pytest.fixture(autouse=True)
def _no_dns(monkeypatch):
    monkeypatch.setattr(fetch, "_validate_url", lambda url: url)


def test_extracts_readable_html(monkeypatch):
    monkeypatch.setattr(fetch.requests, "get", lambda url, **kw: FakeResponse(body=HTML))
    result = fetch_webpage("https://example.com/research")
    assert result["title"] == "Research Guide"
    assert "Evidence from the webpage." in result["content"]
    assert "ignore this script" not in result["content"]
    assert "Navigation" not in result["content"]


def test_follows_one_redirect(monkeypatch):
    responses = [FakeResponse(302, {"Location": "https://www.example.com/r"}),
                 FakeResponse(body=HTML)]
    monkeypatch.setattr(fetch.requests, "get", lambda url, **kw: responses.pop(0))
    assert "Evidence" in fetch_webpage("https://example.com/r")["content"]


def test_redirect_loop_is_rejected(monkeypatch):
    monkeypatch.setattr(fetch.requests, "get",
                        lambda url, **kw: FakeResponse(302, {"Location": "https://example.com/"}))
    with pytest.raises(RuntimeError, match="Too many redirects"):
        fetch_webpage("https://example.com/")


def test_pdf_is_skipped_gracefully(monkeypatch):
    monkeypatch.setattr(fetch.requests, "get", lambda url, **kw: FakeResponse(
        headers={"Content-Type": "application/pdf"}))
    with pytest.raises(RuntimeError, match="PDF"):
        fetch_webpage("https://example.com/a.pdf")


def test_download_is_size_capped(monkeypatch):
    monkeypatch.setattr(fetch, "MAX_DOWNLOAD_BYTES", 100)
    big = b"<html><body><main>" + b"a" * 10_000 + b"</main></body></html>"
    monkeypatch.setattr(fetch.requests, "get", lambda url, **kw: FakeResponse(body=big))
    assert len(fetch_webpage("https://example.com/")["content"]) <= 100


import pytest

from app.tools.fetch import _validate_url, fetch_webpage


def test_rejects_non_http_scheme():
    with pytest.raises(ValueError):
        _validate_url("file:///C:/Windows/win.ini")


def test_rejects_localhost():
    with pytest.raises(ValueError):
        _validate_url("http://localhost:8000/")


def test_extracts_readable_html(monkeypatch):
    class FakeResponse:
        status_code = 200
        headers = {"Content-Type": "text/html; charset=utf-8"}
        text = """
        <html>
          <head><title>Research Guide</title></head>
          <body>
            <script>ignore this script</script>
            <nav>Navigation</nav>
            <main><p>Evidence from the webpage.</p></main>
          </body>
        </html>
        """

    def fake_get(url, **kwargs):
        assert url == "https://example.com/research"
        assert kwargs["allow_redirects"] is False
        return FakeResponse()

    monkeypatch.setattr("app.tools.fetch._validate_url", lambda url: url)
    monkeypatch.setattr("app.tools.fetch.requests.get", fake_get)

    result = fetch_webpage("https://example.com/research")

    assert result["title"] == "Research Guide"
    assert "Evidence from the webpage." in result["content"]
    assert "ignore this script" not in result["content"]


def test_rejects_redirects(monkeypatch):
    class FakeResponse:
        status_code = 302
        headers = {"Location": "https://example.org/"}

    monkeypatch.setattr("app.tools.fetch._validate_url", lambda url: url)
    monkeypatch.setattr(
        "app.tools.fetch.requests.get",
        lambda url, **kwargs: FakeResponse(),
    )

    with pytest.raises(RuntimeError, match="redirected"):
        fetch_webpage("https://example.com/")

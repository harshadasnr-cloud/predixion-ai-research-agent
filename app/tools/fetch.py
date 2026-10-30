import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

MAX_CONTENT_LENGTH = 20_000
MAX_DOWNLOAD_BYTES = 1_000_000   # never download more than 1 MB
MAX_REDIRECTS = 3
REQUEST_TIMEOUT = (3, 10)


def _validate_url(url: str) -> str:
    """Allow public HTTP(S) URLs and reject local/private destinations (SSRF guard)."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Only HTTP and HTTPS URLs are allowed.")
        if not hostname or parsed.username or parsed.password:
            raise ValueError("Invalid URL.")
        if hostname.lower() == "localhost" or hostname.endswith(".localhost"):
            raise ValueError("Local URLs are not allowed.")

        try:
            addresses = [ipaddress.ip_address(hostname)]
        except ValueError:
            try:
                addresses = [
                    ipaddress.ip_address(item[4][0])
                    for item in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
                ]
            except socket.gaierror:
                raise ValueError("The URL hostname could not be resolved.") from None

        if not addresses or any(not a.is_global for a in addresses):
            raise ValueError("Private or non-public destinations are not allowed.")
        return url
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Unsafe or invalid URL: {exc}") from None


def _read_capped(response) -> str:
    chunks, total = [], 0
    for chunk in response.iter_content(chunk_size=16_384):
        if not chunk:
            continue
        chunks.append(chunk)
        total += len(chunk)
        if total >= MAX_DOWNLOAD_BYTES:
            break
    raw = b"".join(chunks)[:MAX_DOWNLOAD_BYTES]
    return raw.decode(response.encoding or "utf-8", errors="replace")


def fetch_webpage(url: str) -> dict:
    """Fetch a public page: re-validates every redirect hop, caps download size."""
    current = url
    response = None

    for _ in range(MAX_REDIRECTS + 1):
        safe_url = _validate_url(current)
        try:
            response = requests.get(
                safe_url,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False,
                stream=True,
                headers={"User-Agent": "ResearchAgent/0.2"},
            )
        except requests.RequestException:
            raise RuntimeError(
                "Could not retrieve the webpage. Check the URL or try another source."
            ) from None

        if 300 <= response.status_code < 400:
            location = response.headers.get("Location")
            response.close()
            response = None
            if not location:
                raise RuntimeError("Redirect without a Location header.")
            current = urljoin(safe_url, location)
            continue
        break

    if response is None:
        raise RuntimeError("Too many redirects.")

    if response.status_code >= 400:
        response.close()
        raise RuntimeError(f"The webpage returned HTTP status {response.status_code}.")

    content_type = response.headers.get("Content-Type", "").lower()
    if "application/pdf" in content_type:
        response.close()
        raise RuntimeError("PDF pages are not supported yet.")
    if "text/html" not in content_type:
        response.close()
        raise RuntimeError("The URL did not return an HTML webpage.")

    html = _read_capped(response)
    response.close()

    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
        element.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    container = soup.find("main") or soup.find("article") or soup.body or soup
    text = container.get_text(" ", strip=True)
    if not text:
        raise RuntimeError("No readable text was found on the webpage.")

    return {"url": safe_url, "title": title[:300], "content": text[:MAX_CONTENT_LENGTH]}

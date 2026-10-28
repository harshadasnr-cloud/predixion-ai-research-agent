
import ipaddress
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


MAX_CONTENT_LENGTH = 20_000
REQUEST_TIMEOUT = (3, 10)


def _validate_url(url: str) -> str:
    """Allow public HTTP(S) URLs and reject local/private destinations."""
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
                    for item in socket.getaddrinfo(
                        hostname, None, type=socket.SOCK_STREAM
                    )
                ]
            except socket.gaierror:
                raise ValueError("The URL hostname could not be resolved.") from None

        if not addresses or any(
            not address.is_global for address in addresses
        ):
            raise ValueError("Private or non-public destinations are not allowed.")

        return url
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Unsafe or invalid URL: {exc}") from None


def fetch_webpage(url: str) -> dict:
    """Fetch a public webpage and return its title and readable text."""
    safe_url = _validate_url(url)

    try:
        response = requests.get(
            safe_url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
            headers={"User-Agent": "PredixionResearchAgent/0.1"},
        )
    except requests.RequestException:
        raise RuntimeError(
            "Could not retrieve the webpage. Check the URL or try another source."
        ) from None

    if 300 <= response.status_code < 400:
        raise RuntimeError(
            "The webpage redirected. Redirects are not followed for safety."
        )

    if response.status_code >= 400:
        raise RuntimeError(
            f"The webpage returned HTTP status {response.status_code}."
        )

    content_type = response.headers.get("Content-Type", "").lower()
    if "text/html" not in content_type:
        raise RuntimeError("The URL did not return an HTML webpage.")

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        element.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    text = soup.get_text(" ", strip=True)

    if not text:
        raise RuntimeError("No readable text was found on the webpage.")

    return {
        "url": safe_url,
        "title": title[:300],
        "content": text[:MAX_CONTENT_LENGTH],
    }

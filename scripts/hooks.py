from urllib.parse import urlparse

from bs4 import BeautifulSoup


def on_post_page(output_content: str, *, page, config, **kwargs) -> str:
    """
    Add target="_blank" to external links
    """
    soup = BeautifulSoup(output_content, "html.parser")

    site_url = config.get("site_url", "")
    site_host = urlparse(site_url).netloc if site_url else ""

    for tag in soup.find_all("a", href=True):
        target_blank = False
        href = tag["href"]

        if href.endswith(".pdf"):
            target_blank = True
        elif href.startswith(("http://", "https://")):
            if site_host and urlparse(href).netloc == site_host:
                continue

            target_blank = True

        if not target_blank:
            continue

        tag["target"] = "_blank"
        existing_rel = set(tag.get("rel", []))
        existing_rel.update({"noopener", "noreferrer"})
        tag["rel"] = " ".join(sorted(existing_rel))

    return str(soup)

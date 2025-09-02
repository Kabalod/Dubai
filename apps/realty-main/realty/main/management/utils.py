import logging
from pathlib import Path

import httpx
from scrapy.selector import Selector

logger = logging.getLogger(__name__)


def safe_str_value(value) -> str:
    """
    Safely convert a value to string.
    If None or NaN, return an empty string.
    Removes invisible chars like \u202c and strips whitespace.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip().replace("\u202c", "")


def download_dubai_pulse_csv(site_url: str, file_type: str) -> Path:
    logger.info(f"Reading the page {site_url} to extract download_url and update_date.")
    response = httpx.get(site_url, timeout=30)
    selector = Selector(text=response.text)
    update_date = selector.css("div.update-date::text").get().strip()
    update_date = update_date.replace("Updated:", "").strip()
    download_url = selector.css(
        'div[data-original-title="Download"] a.action-icon-anchor::attr(href)'
    ).get()
    if not download_url:
        download_url = selector.css(
            f'a[href*="/download/{file_type}.csv"]::attr(href)'
        ).get()
    folder = Path(file_type)
    folder.mkdir(exist_ok=True)
    filename = folder / f"{update_date.strip().replace(' ', '-')}.csv"
    if filename.exists():
        logger.info(f"File '{filename}' already exists. Skipping.")
        return filename
    logger.info(f"Downloading the file from {download_url} to {filename}")
    try:
        with httpx.stream("GET", download_url) as response:
            with open(filename, "wb") as file:
                for chunk in response.iter_bytes():
                    file.write(chunk)
    except httpx.HTTPError as e:
        logger.error(f"Failed to download the file from {download_url}.")
        filename.unlink()
        raise e
    logger.info(f"Downloaded {filename}.")
    return filename

import asyncio
import sys

# Set asyncio event loop policy for Windows if applicable
# Removing this as it's in main.py and we're switching to async_playwright
# if sys.platform == "win32":
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
import logging
import re # For splitting title and author
from urllib.parse import quote_plus, urljoin # For URL encoding and joining

# Removed Playwright imports - no longer needed
# from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.core.config import settings # Import settings to access the cookie

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AUDIOBOOK_BAY_URL = "https://audiobookbay.lu" # Base URL, ensure no trailing slash for urljoin
# Consider making this configurable or adding logic to try mirrors if one fails.

# _get_headers is now primarily for httpx, Playwright handles cookies differently
def _get_httpx_headers() -> Dict[str, str]:
    """Prepares headers for httpx requests (e.g., for get_audiobook_details)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": AUDIOBOOK_BAY_URL + "/"
    }
    # Cookie for httpx requests, if needed for get_audiobook_details directly
    if settings.AUDIOBOOK_BAY_COOKIE: 
        headers["Cookie"] = settings.AUDIOBOOK_BAY_COOKIE
    return headers

def _parse_title_author(text: str) -> Dict[str, str]:
    """Helper to parse combined title and author string."""
    parts = text.split(" - ", 1)
    if len(parts) == 2:
        return {"title": parts[0].strip(), "author": parts[1].strip()}
    else:
        # Fallback if " - " delimiter is not found
        # Check if the last part after a comma might be the author (common in some listings)
        comma_parts = text.rsplit(", ", 1)
        if len(comma_parts) == 2 and len(comma_parts[1]) < 70: # Increased length for author part a bit
            if ' ' in comma_parts[1] or len(comma_parts[1].split()) <= 5: 
                return {"title": comma_parts[0].strip(), "author": comma_parts[1].strip()}
        return {"title": text.strip(), "author": "N/A"}

async def _fetch_search_results_with_httpx(query: str, page: int = 1) -> List[Dict[str, Any]]:
    """Use httpx to fetch search results."""
    search_results = []
    base_search_url = AUDIOBOOK_BAY_URL
    search_url_with_query = f"{base_search_url}/?s={quote_plus(query)}"
    if page > 1:
        search_url_with_query = f"{base_search_url}/page/{page}/?s={quote_plus(query)}"

    logger.info(f"Searching AudiobookBay with httpx for query: '{query}' on page {page} at URL: {search_url_with_query}")
    
    try:
        async with httpx.AsyncClient(headers=_get_httpx_headers(), timeout=30.0, follow_redirects=True) as client:
            response = await client.get(search_url_with_query)
            response.raise_for_status()
            html_content = response.text
            
            if not html_content:
                logger.warning(f"httpx returned empty content for {search_url_with_query}. Skipping parsing.")
                return []
                
            soup = BeautifulSoup(html_content, "html.parser")
            posts = soup.find_all("div", class_="post")
            
            if not posts:
                logger.info(f"No posts found with selector 'div.post' for query: '{query}' on page {page}")
                return []
            
            for post_element in posts:
                title_author_text = "N/A"
                detail_page_url_relative = None
                cover_url = None
                language = None
                
                # Try to extract language from the post content, but don't filter by it
                post_content_div = post_element.find("div", class_="postContent")
                if post_content_div:
                    # Look for text that indicates language
                    content_text = post_content_div.get_text()
                    language_match = re.search(r"Language:\s*([^\r\n,]+)", content_text)
                    if language_match:
                        language = language_match.group(1).strip()
                
                title_div = post_element.find("div", class_="postTitle")
                if title_div:
                    h2_tag = title_div.find("h2")
                    if h2_tag:
                        a_tag = h2_tag.find("a")
                        if a_tag and a_tag.has_attr('href'):
                            title_author_text = a_tag.text.strip()
                            detail_page_url_relative = a_tag['href']
                parsed_name = _parse_title_author(title_author_text)
                title = parsed_name['title']
                author = parsed_name['author']
                
                if post_content_div:
                    center_p_image_container = post_content_div.find("p", class_="center")
                    if center_p_image_container:
                        img_a_tag = center_p_image_container.find_next_sibling("p", class_="center")
                        if img_a_tag:
                            img_tag_candidate = img_a_tag.find("img")
                            if img_tag_candidate and img_tag_candidate.has_attr('src'):
                                cover_url = img_tag_candidate['src']
                        if not cover_url: # Try the first p.center if the sibling logic fails
                            img_tag_candidate_alt = center_p_image_container.find("img")
                            if img_tag_candidate_alt and img_tag_candidate_alt.has_attr('src'):
                                cover_url = img_tag_candidate_alt['src']
                if cover_url and not cover_url.startswith("http"):
                    cover_url = urljoin(AUDIOBOOK_BAY_URL + "/", cover_url.lstrip('/'))
                detail_page_url_absolute = None
                if detail_page_url_relative:
                    detail_page_url_absolute = urljoin(AUDIOBOOK_BAY_URL + "/", detail_page_url_relative.lstrip('/'))
                direct_download_link_relative = None
                post_meta_div = post_element.find("div", class_="postMeta")
                if post_meta_div:
                    dd_span = post_meta_div.find("span", class_="postComments")
                    if dd_span:
                        dd_a_tag = dd_span.find("a", string="Direct Download", rel="nofollow")
                        if dd_a_tag and dd_a_tag.has_attr('href'):
                            direct_download_link_relative = dd_a_tag['href']
                raw_dd_link_absolute = None
                if direct_download_link_relative:
                    raw_dd_link_absolute = urljoin(AUDIOBOOK_BAY_URL + "/", direct_download_link_relative.lstrip('/'))

                if title != "N/A" and detail_page_url_absolute:
                    search_results.append({
                        "title": title,
                        "author": author,
                        "detail_page_url": detail_page_url_absolute,
                        "cover_url": cover_url,
                        "language": language,
                        "magnet_link": None, # Magnet link is fetched from detail page
                        "raw_direct_download_link": raw_dd_link_absolute # If available on search page
                    })
                else:
                    logger.warning(f"Could not parse all required fields for a post. Title: '{title}', Detail URL: '{detail_page_url_absolute}'")
                
            if not search_results and posts:
                logger.warning(f"Posts were found for '{query}', but no items could be fully parsed.")
            
            return search_results
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e.response.status_code} while fetching search results for {query}")
    except httpx.RequestError as e:
        logger.error(f"Request error occurred while fetching search results for {query}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during httpx scraping for '{query}': {e}", exc_info=True)
    
    return []

async def search_audiobooks(query: str, page: int = 1) -> List[Dict[str, Any]]:
    logger.info(f"Initiating httpx search for query: '{query}' on page {page}")
    try:
        results = await _fetch_search_results_with_httpx(query, page)
        return results
    except Exception as e:
        logger.error(f"An unexpected error occurred during search for '{query}': {e}", exc_info=True)
        return [] # Return empty list on error to maintain consistent return type

async def get_audiobook_details(detail_page_url: str) -> Optional[Dict[str, Any]]:
    """
    Fetches detailed information for a single audiobook from its detail page.
    THIS IS WHERE THE MAGNET LINK SHOULD BE FOUND.
    You will need to provide an example HTML of a detail page to implement this.

    Args:
        detail_page_url: The URL of the audiobook's detail page.
    
    Returns:
        A dictionary with detailed audiobook information including the magnet_link,
        or None if an error occurs or magnet link not found.
    """
    logger.info(f"Fetching details from: {detail_page_url} using httpx")
    if not detail_page_url or not detail_page_url.startswith("http"):
        logger.error(f"Invalid detail_page_url: {detail_page_url}")
        return None
    try:
        # get_audiobook_details can still use httpx if direct loading works for detail pages
        async with httpx.AsyncClient(headers=_get_httpx_headers(), timeout=15.0, follow_redirects=True) as client:
            response = await client.get(detail_page_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            # --- Parsing logic for detail page (based on example_details.html) ---
            title = "N/A"
            h1_title = soup.find("h1", itemprop="name")
            if h1_title:
                title = h1_title.text.strip()

            description_parts = []
            desc_div = soup.find("div", class_="desc", itemprop="description")
            if desc_div:
                for p_tag in desc_div.find_all("p"):
                    description_parts.append(p_tag.text.strip())
            description = "\n".join(description_parts).strip() if description_parts else "N/A"

            # Extract language information
            language = None
            content_text = soup.get_text()
            language_match = re.search(r"Language:\s*([^\r\n,]+)", content_text)
            if language_match:
                language = language_match.group(1).strip()

            cover_img_tag = soup.find("img", itemprop="image")
            cover_url = cover_img_tag['src'] if cover_img_tag and cover_img_tag.has_attr('src') else None
            if cover_url and not cover_url.startswith("http"):
                 cover_url = urljoin(AUDIOBOOK_BAY_URL + "/", cover_url.lstrip('/'))

            narrator_span = soup.find("span", itemprop="readBy") # More specific itemprop for narrator if available
            if not narrator_span:
                narrator_span = soup.find("span", class_="narrator") # Fallback to class
            narrator = narrator_span.text.strip() if narrator_span else "N/A"

            # Author parsing from detail page
            final_author = "N/A"
            author_span_itemprop = desc_div.find("span", itemprop="author") if desc_div else None
            if author_span_itemprop and author_span_itemprop.find_parent("a"): # ensure it's the linked author
                final_author = author_span_itemprop.text.strip()
            
            # Refine title and author from the main h1 title if possible
            parsed_title_info = _parse_title_author(title)
            final_title = parsed_title_info['title']
            if parsed_title_info['author'] != "N/A" and final_author == "N/A": # Prioritize author from title if detail specific is N/A
                final_author = parsed_title_info['author']
            elif final_author == "N/A" and parsed_title_info['author'] != "N/A": # If itemprop author was not found, use from title
                 final_author = parsed_title_info['author']
            elif final_author != "N/A" and parsed_title_info['author'] != "N/A" and final_author != parsed_title_info['author']:
                logger.info(f"Author mismatch: itemprop/class='{final_author}', title_parse='{parsed_title_info['author']}'. Using itemprop/class.")

            info_hash = None
            trackers = []
            torrent_info_table = soup.find("table", class_="torrent_info")
            if torrent_info_table:
                rows = torrent_info_table.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) == 2:
                        field_name = cols[0].text.strip()
                        field_value = cols[1].text.strip()
                        if field_name == "Info Hash:":
                            info_hash = field_value
                        elif field_name == "Tracker:" or field_name == "Announce URL:":
                            if field_value not in trackers: # Avoid duplicate trackers
                                trackers.append(field_value)
            
            magnet_link = None
            if info_hash:
                magnet_link = f"magnet:?xt=urn:btih:{info_hash}&dn={quote_plus(final_title)}"
                for tracker_url in trackers:
                    magnet_link += f"&tr={quote_plus(tracker_url)}"
                logger.info(f"Constructed magnet link for '{final_title}': {magnet_link}")
            else:
                logger.warning(f"Info Hash not found on detail page: {detail_page_url}, cannot construct magnet link.")

            return {
                "title": final_title,
                "author": final_author,
                "narrator": narrator,
                "description": description,
                "language": language,
                "magnet_link": magnet_link, 
                "cover_url": cover_url,
                "detail_page_url": detail_page_url,
                "info_hash": info_hash,
                "trackers": list(set(trackers)) # Ensure unique trackers
            }
            # --- End parsing logic for detail page ---

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text if hasattr(e.response, 'text') else 'N/A'} while fetching {detail_page_url}")
    except httpx.RequestError as e:
        logger.error(f"Request error occurred while fetching {detail_page_url}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching details from {detail_page_url}: {e}", exc_info=True)
    return None

# Example usage (for testing purposes, can be removed later)
if __name__ == "__main__":
    async def main_test():
        logger.info("--- Starting Scraper Test (httpx only) ---")
        queries = ["Harry Potter", "The Martian", "Project Hail Mary", "Dune"]
        for query in queries:
            logger.info(f"\n--- Testing search for: {query} ---")
            results = await search_audiobooks(query, page=1) # Test with default page 1
            if results:
                logger.info(f"Found {len(results)} results for '{query}':")
                for i, book in enumerate(results[:2]):
                    logger.info(f"  {i+1}. Title: {book['title']}")
                    logger.info(f"     Author: {book['author']}")
                    logger.info(f"     Detail URL: {book['detail_page_url']}")
                    logger.info(f"     Cover: {book['cover_url']}")
                    logger.info(f"     Raw DD Link: {book['raw_direct_download_link']}")
                    if i == 0 and book['detail_page_url']:
                        logger.info(f"    \n    --- Testing detail page for: {book['title']} ---")
                        details = await get_audiobook_details(book['detail_page_url'])
                        if details:
                            logger.info(f"    Details: Magnet found: {details.get('magnet_link') is not None}")
                            logger.info(f"    Narrator: {details.get('narrator')}")
                        else:
                            logger.info(f"    Could not fetch details for {book['detail_page_url']}")
            else:
                logger.info(f"No results found or error occurred during search for '{query}'.")
        logger.info("--- Scraper Test Finished ---")
    asyncio.run(main_test()) 
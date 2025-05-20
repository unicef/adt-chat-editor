from pathlib import Path
from typing import Optional
import aiofiles
from bs4 import BeautifulSoup


async def read_html_file(file_path: str | Path) -> str:
    """
    Read an HTML file and return its content asynchronously.

    Args:
        file_path: Path to the HTML file

    Returns:
        The HTML content as a string
    """
    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
        return await f.read()


def extract_text_from_html(html_content: str) -> str:
    """
    Extract text content from HTML while preserving structure.

    Args:
        html_content: HTML content as string

    Returns:
        Text content with HTML structure preserved
    """
    soup = BeautifulSoup(html_content, "html.parser")
    return str(soup)


async def prepare_html_context(
    file_path: Optional[str | Path] = None, html_content: Optional[str] = None
) -> str:
    """
    Prepare HTML content for the text editing prompt.
    Either file_path or html_content must be provided.

    Args:
        file_path: Path to the HTML file
        html_content: HTML content as string

    Returns:
        Formatted HTML content for the prompt
    """
    if file_path:
        html_content = await read_html_file(file_path)
    elif not html_content:
        raise ValueError("Either file_path or html_content must be provided")

    # Extract text while preserving structure
    text_content = extract_text_from_html(html_content)

    return f"""Here is the HTML content to edit:

{text_content}

Please edit the text while preserving all HTML tags and structure."""

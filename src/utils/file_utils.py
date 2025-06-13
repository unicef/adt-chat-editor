import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union

import aiofiles
from bs4 import BeautifulSoup, Tag

from src.settings import OUTPUT_DIR, TRANSLATIONS_DIR, HTML_CONTENTS_DIR, custom_logger

logger = custom_logger("Sub-agents Workflow Routes")


async def get_relative_path(path: str, start: str) -> str:
    """Get relative path asynchronously.

    Args:
        path (str): The path to get the relative path of
        start (str): The starting path

    Returns:
        str: The relative path
    """
    return await asyncio.to_thread(os.path.relpath, path, start)


async def get_html_files(output_dir: str) -> List[str]:
    """Get all HTML files from the output directory asynchronously.

    Args:
        output_dir (str): The output directory

    Returns:
        List[str]: A list of HTML file paths
    """
    output_path = Path(output_dir)
    # Use asyncio.to_thread to run the blocking glob operation in a thread pool
    files = await asyncio.to_thread(lambda: list(output_path.glob("*.html")))
    return [str(f) for f in files]


async def read_html_file(file_path: str) -> str:
    """Read HTML file content asynchronously.

    Args:
        file_path (str): The path to the HTML file

    Returns:
        str: The content of the HTML file
    """
    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
        return await f.read()


async def write_html_file(file_path: str, content: str) -> None:
    """Write content to HTML file asynchronously.

    Args:
        file_path (str): The path to the HTML file
        content (str): The content to write to the HTML file
    """
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(content)


async def read_translation_file(translation_file_path: str) -> dict:
    async with aiofiles.open(translation_file_path, "r", encoding="utf-8") as file:
        contents = await file.read()
        translation_data = json.loads(contents)
    return translation_data


async def extract_html_content_async(
    html: str, translations_dict: Dict[str, str], clean_whitespace: bool = True
) -> str:
    """Extract translated textual content from HTML using data-id, data-aria-id, and placeholder attributes.

    Args:
        html (str): HTML string to parse.
        translations_dict (Dict[str, str]): Dictionary of translations (keys are attribute values).
        clean_whitespace (bool): Whether to clean excess whitespace.

    Returns:
        str: Translated text content.
    """

    def sync_extract(html_content: str, translations: Dict[str, str]) -> str:
        full_content = []

        soup = BeautifulSoup(html_content, "html.parser")

        # Remove unwanted elements
        for element in soup(["script", "style", "noscript", "iframe"]):
            element.decompose()

        # Replace text for tags with data-id or data-aria-id
        for tag in soup.find_all(attrs={"data-id": True}):
            key = tag["data-id"]
            if key in translations:
                full_content.append(translations[key])

        for tag in soup.find_all(attrs={"data-aria-id": True}):
            key = tag["data-aria-id"]
            if key in translations:
                full_content.append(translations[key])

        # Replace placeholder attributes
        for tag in soup.find_all(attrs={"placeholder": True}):
            key = tag["placeholder"]
            if key in translations:
                full_content.append(translations[key])

        return full_content

    return await asyncio.to_thread(sync_extract, html, translations_dict)


async def extract_layout_properties_async(
    html: str,
    include_element_type: bool = True,
    include_dimensions: bool = True,
    include_classes: bool = True,
    include_styles: bool = False,
    include_position: bool = True,
    max_depth: Optional[int] = None,
) -> List[Dict[str, Union[str, Dict[str, str]]]]:
    """Async version of HTML layout properties extraction.

    Args:
        html (str): HTML string to parse
        include_element_type (bool): Include HTML tag type
        include_dimensions (bool): Include width/height if available
        include_classes (bool): Include class list if available
        include_styles (bool): Include style attributes if available
        include_position (bool): Include position in DOM (parent-child relationships)
        max_depth (Optional[int]): Maximum depth to traverse in DOM tree (None for unlimited)

    Returns:
        List[Dict]: List of elements with their layout properties
    """

    def sync_extract(html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        elements = []

        def traverse(node: Tag, depth: int = 0, parent_id: Optional[str] = None):
            if max_depth is not None and depth > max_depth:
                return

            element_data = {
                "id": f"element-{len(elements)}",
                "tag": node.name if include_element_type else None,
            }

            if include_dimensions:
                element_data.update(
                    {"width": node.get("width"), "height": node.get("height")}
                )

            if include_classes and node.get("class"):
                classes = node.get("class") or []
                element_data["classes"] = " ".join(classes)

            if include_styles and node.get("style"):
                styles = {}
                style_str = str(node.get("style") or "")
                for style in style_str.split(";"):
                    if ":" in style:
                        prop, val = style.split(":", 1)
                        styles[prop.strip()] = val.strip()
                element_data["styles"] = styles

            if include_position:
                element_data.update(
                    {
                        "depth": depth,
                        "parent_id": parent_id,
                        "child_count": len(list(node.children)),
                    }
                )

            # Only include if we have at least one property
            if any(v is not None for v in element_data.values() if v != {}):
                elements.append(
                    {k: v for k, v in element_data.items() if v is not None}
                )
                current_id = element_data["id"]

                for child in node.children:
                    if isinstance(child, Tag):
                        traverse(child, depth + 1, current_id)

        traverse(soup)
        return elements

    return await asyncio.to_thread(sync_extract, html)


async def get_language_from_translation_files() -> List[str]:
    """Get language codes from translation folders.

    Returns:
        List[str]: List of language codes (e.g., ['es', 'en', 'es_uy', ...])
    """
    translations_path = os.path.join(OUTPUT_DIR, TRANSLATIONS_DIR)

    try:
        # List all directories in the translations folder
        items = await asyncio.to_thread(os.listdir, translations_path)
    except FileNotFoundError:
        logger.debug(f"Translation file not found: {translations_path}")
        return []  # Directory doesn't exist → no languages

    # Filter only directories that contain 'translations.json'
    valid_languages = []
    for lang_dir in items:
        lang_path = os.path.join(translations_path, lang_dir)
        translations_file = os.path.join(lang_path, "translations.json")

        if await asyncio.to_thread(
            os.path.isdir, lang_path
        ) and await asyncio.to_thread(os.path.isfile, translations_file):
            valid_languages.append(lang_dir)

    return valid_languages


async def delete_html_files_async(
    file_paths: List[str], output_dir: str
) -> Dict[str, List[str]]:
    """Async function to safely move HTML files to a 'deleted_html' directory.
    Creates the directory if it doesn't exist.

    Args:
        file_paths: List of file paths to HTML files that should be moved
        output_dir: Base directory where 'deleted_html' folder will be created/maintained

    Returns:
        Dictionary with two lists:
        {
            "moved": List of successfully moved files (format "old_path → new_path"),
            "failed": List of failed operations with error details
        }
    """

    def sync_move(paths: List[str], base_dir: str) -> Dict[str, List[str]]:
        moved = []
        failed = []

        # Ensure deleted directory exists (creates if needed)
        deleted_dir = os.path.join(base_dir, "deleted_html")
        try:
            os.makedirs(deleted_dir, exist_ok=True)  # Critical safety check
        except OSError as e:
            # If we can't even create the directory, fail all operations
            return {
                "moved": [],
                "failed": [
                    f"{path} (failed to create deletion directory: {str(e)})"
                    for path in paths
                ],
            }

        for path in paths:
            if not path.endswith(".html"):
                failed.append(f"{path} (not an .html file)")
                continue

            try:
                if os.path.exists(path):
                    filename = os.path.basename(path)
                    new_path = os.path.join(deleted_dir, filename)

                    # Handle filename conflicts
                    counter = 1
                    while os.path.exists(new_path):
                        name, ext = os.path.splitext(filename)
                        new_path = os.path.join(deleted_dir, f"{name}_{counter}{ext}")
                        counter += 1

                    # Perform the actual move
                    shutil.move(path, new_path)
                    moved.append(f"{path} → {new_path}")
                else:
                    failed.append(f"{path} (file not found)")
            except Exception as e:
                failed.append(f"{path} (error: {str(e)})")

        return {"moved": moved, "failed": failed}

    return await asyncio.to_thread(sync_move, file_paths, output_dir)


async def find_and_duplicate_nav_line(
    nav_content: str, original_href: str, new_href: str
) -> str:
    """Finds the nav line with the original href and creates a duplicate with the new href.

    Args:
        nav_content: The full nav HTML content as string
        original_href: The href to search for (e.g. "los_biomas.html")
        new_href: The new href to replace with (e.g. "new_file.html")

    Returns:
        The new nav line with updated href
    """
    # Find the line containing the original href
    lines = nav_content.split("\n")
    for line in lines:
        if f'href="{original_href}"' in line:
            # Create new line by replacing the href
            new_line = line.replace(f'href="{original_href}"', f'href="{new_href}"')
            return new_line

    raise ValueError(f"Could not find nav item with href='{original_href}'")


async def write_nav_line(nav_content: str, nav_line: str) -> str:
    """Inserts a new navigation line just before the closing </nav> tag.

    Args:
        nav_content: The full content of the nav HTML as a string
        nav_line: The new <li> line to insert

    Returns:
        The updated nav content with the new line inserted
    """
    # Find the last closing nav tag position
    closing_nav_pos = nav_content.rfind("</nav>")

    if closing_nav_pos == -1:
        raise ValueError("Could not find closing </nav> tag in nav content")

    # Insert the new line before the closing tag with proper indentation
    updated_content = (
        nav_content[:closing_nav_pos].rstrip()
        + "\n"
        + nav_line.strip()
        + "\n" * 2
        + nav_content[closing_nav_pos:]
    )

    return updated_content


async def remove_nav_line_by_href(nav_content: str, href_to_remove: str) -> str:
    """Removes a navigation line that contains the specified href value.

    Args:
        nav_content: The full nav HTML content as string
        href_to_remove: The href value to search for and remove (e.g. "los_biomas.html")

    Returns:
        The updated nav content with the line removed
    """
    # Split the content into lines
    lines = nav_content.split("\n")

    # Find and remove the line containing the href
    updated_lines = []
    href_pattern = f'href="{href_to_remove}"'

    for line in lines:
        if href_pattern in line:
            continue  # Skip this line
        updated_lines.append(line)

    # If no line was removed, raise an error
    if len(lines) == len(updated_lines):
        raise ValueError(f"No nav line found with href='{href_to_remove}'")

    # Join the lines back together
    updated_nav = "\n".join(updated_lines)

    return updated_nav


async def install_tailwind():
    logger.info("Installing Tailwind resources")

    cleanup_cmd = "rm -rf node_modules package-lock.json && npm set registry https://registry.npmmirror.com"
    install_cmd = "npm install"

    try:
        # Step 1: Cleanup and set registry
        logger.info("Cleaning up and setting registry")
        cleanup_process = await asyncio.create_subprocess_shell(
            cleanup_cmd,
            cwd=OUTPUT_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        cleanup_stdout, cleanup_stderr = await cleanup_process.communicate()
        if cleanup_process.returncode != 0:
            logger.error(f"Cleanup/registry command failed: {cleanup_stderr.decode()}")
            return False

        # Step 2: Run npm install
        logger.info("Running npm install")
        install_process = await asyncio.create_subprocess_shell(
            install_cmd,
            cwd=OUTPUT_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        install_stdout, install_stderr = await install_process.communicate()
        if install_process.returncode == 0:
            logger.info("Tailwind resources installed successfully")
            return True
        else:
            logger.error(f"Tailwind installation failed: {install_stderr.decode()}")
            return False

    except Exception as e:
        logger.error(f"Error installing Tailwind: {str(e)}")
        return False


async def update_tailwind(output_dir: str, input_css_path: str, output_css_path: str):
    logger.info("Updating Tailwind css file")

    # Prepare the command
    cmd = f"npx tailwindcss -i {input_css_path} -o {output_css_path}"

    try:
        # Run the command asynchronously
        process = await asyncio.create_subprocess_shell(
            cmd,
            cwd=output_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Wait for the process to complete (note the await)
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info("Tailwind css updated successfully")
            return True
        else:
            logger.error(f"Tailwind update failed: {stderr.decode()}")
            return False

    except Exception as e:
        logger.error(f"Error updating Tailwind: {str(e)}")
        return False


async def extract_and_save_html_contents(
    language: str, output_dir: str, translations_dir: str
) -> str:
    translation_file_path = os.path.join(
        output_dir,
        translations_dir,
        language,
        "translations.json",
    )

    try:
        # Read the translation file
        translation_file = await read_translation_file(translation_file_path)

        # Get and process all HTML files
        html_files = await get_html_files(output_dir)
        available_html_files: List[Dict[str, str]] = []

        for html_file in html_files:
            html_content = await read_html_file(html_file)
            extracted_content = await extract_html_content_async(
                html_content,
                translation_file["texts"],
            )
            html_dict = {
                "html_name": html_file,
                "html_content": extracted_content,
            }
            available_html_files.append(html_dict)

        # Save the result as a JSON file
        save_path = f"{HTML_CONTENTS_DIR}/translation_{language}.json"

        # Ensure the directory exists
        await asyncio.to_thread(os.makedirs, os.path.dirname(save_path), exist_ok=True)

        # Write JSON asynchronously
        await asyncio.to_thread(
            lambda: json.dump(
                available_html_files,
                open(save_path, "w", encoding="utf-8"),
                ensure_ascii=False,
                indent=2,
            )
        )

        logger.info(f"Saved translated HTML content to: {save_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving translated HTML contents: {str(e)}")
        return False


async def load_translated_html_contents(language: str):
    path = f"{HTML_CONTENTS_DIR}/translation_{language}.json"

    def load_json():
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    data = await asyncio.to_thread(load_json)

    return data

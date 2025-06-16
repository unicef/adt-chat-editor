from typing import Optional
import base64
from pathlib import Path

from fastapi import APIRouter, Query
from fastapi_pagination import Page, paginate
from fastapi_pagination.utils import disable_installed_extensions_check

from src.settings import custom_logger
from src.structs import Book, BookInfo, BookContent, Chapter, PageContent
from src.utils.image_utils import get_sample_cover_image


# Create the logger
logger = custom_logger("Books API Router")
disable_installed_extensions_check()

# Create router
router = APIRouter(
    prefix="/books",
    tags=["Books"],
)


# Define the endpoints
@router.get("", response_model=Page[Book])
def get_books(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page"),
) -> Page[Book]:
    """Get a paginated list of books."""
    logger.info(f"Getting books: page={page}, size={size}")
    books = []
    cover_image = get_sample_cover_image()
    for i in range(50):
        book = Book(
            id=f"book_{i}",
            title=f"Book {i}",
            author=f"Author {i}",
            cover_image=cover_image,
            description=f"Description for book {i}",
        )
        books.append(book)

    # Calculate start and end indices for the requested page
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    page_books = books[start_idx:end_idx]

    logger.info(f"Returning page {page} with {len(page_books)} books")
    return Page(
        items=page_books,
        total=len(books),
        page=page,
        size=size,
        pages=(len(books) + size - 1) // size,
    )


@router.post("/{id}/start")
async def start_book_editing(id: str):
    """Start the editing process for an ADT."""
    logger.debug(f"Starting book editing: id={id}")
    # TODO: Implement book editing start logic
    return {"status": "started"}


@router.get("/{id}/status")
async def get_book_status(id: str):
    """Check the status of the ADT."""
    logger.debug(f"Getting book status: id={id}")
    # TODO: Implement book status check logic
    return {"status": "ready"}


@router.get("/{id}/refresh")
async def refresh_book(id: str):
    """Refresh the book."""
    logger.debug(f"Refreshing book: id={id}")
    # TODO: Implement book refresh logic
    return {"status": "refreshed"}


@router.get("/{book_id}", response_model=BookInfo)
async def get_book_info(book_id: str):
    """Get information about a specific book."""
    logger.info(f"Getting info for book {book_id}")
    # For now, return a sample book
    return BookInfo(
        id=book_id,
        title=f"Sample Book {book_id}",
        author="Sample Author",
        chapters=[
            Chapter(
                id=f"chapter_{i}",
                title=f"Chapter {i}",
            )
            for i in range(10)
        ],
    )


@router.get("/{book_id}/content", response_model=Page[PageContent])
async def get_book_content(
    book_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page"),
):
    """Get the content of a specific book page."""
    logger.info(f"Getting content for book {book_id}, page {page}")
    # For now, return sample content
    contents = [
        PageContent(
            page_id=f"page_{i}",
            title=f"Page {i}",
            contents=f"Sample content for page {i} of book {book_id}",
        )
        for i in range(50)  # Generate 50 sample pages
    ]

    # Calculate start and end indices for the requested page
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    page_contents = contents[start_idx:end_idx]

    logger.info(f"Returning page {page} with {len(page_contents)} contents")
    return Page(
        items=page_contents,
        total=len(contents),
        page=page,
        size=size,
        pages=(len(contents) + size - 1) // size,
    )

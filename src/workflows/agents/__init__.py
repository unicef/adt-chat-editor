AVAILABLE_AGENTS = [
    {
        "name": "Text Edit Agent",
        "description": """
            Modifies only plain text — grammar, phrasing, tone, and clarity — to improve educational quality.
            Must not alter HTML tags, structure, or layout.
        """,
    },
    {
        "name": "Layout Edit Agent",
        "description": """
            Adjusts HTML/CSS layout only — spacing, alignment, font styles, or responsiveness.
            Must not change textual content or image meaning.
        """,
    },
    {
        "name": "Layout Mirror Agent",
        "description": """
            Copies layout structure and styling from reference (template) HTML files to target files.
            Must not modify template files or change any text content.
        """,
    },
    {
        "name": "Web Merge Agent",
        "description": """
            Combines multiple HTML files into one unified page.
            Preserves layout logic and styling using semantic HTML and Tailwind CSS.
            Must avoid duplication and modify only as needed for merging.
        """,
    },
    {
        "name": "Web Split Agent",
        "description": """
            Splits a single HTML file into multiple standalone pages based on user-defined logic.
            Each result must be complete, accessible, and use consistent HTML and Tailwind structure.
        """,
    },
    {
        "name": "Web Delete Agent",
        "description": """
            Deletes only the HTML files explicitly requested by the user.
            Must not affect other files or their content.
        """,
    },
]

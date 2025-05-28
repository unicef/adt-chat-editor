AVAILABLE_AGENTS = [
    {
        "name": "Text Edit Agent",
        "description": """
            Text Editing** involves **only modifying plain textual content** such as:
              - Grammar, spelling, clarity, tone, or phrasing
              - Improving the educational or instructional quality of the text
              - Ensuring the text remains aligned with HTML structure without modifying \
              any tags, attributes, or layout elements
        """,
    },
    {
        "name": "Layout Edit Agent",
        "description": """
            **Layout Editing** involves **only changing HTML and CSS structure** related to presentation, such as:
              - Font size, font color, margins, padding, alignment, or display mode
              - Adjusting structure for better visual hierarchy or responsiveness
              - Ensuring layout changes preserve accessibility and do not alter the actual text or image content
        """,
    },
    {
        "name": "Layout Mirror Agent",
        "description": """
            **Layout Mirroring** involves **copying the layout structure and visual styling** from one or more base (template) HTML files and applying them to other target HTML files. This includes:
              - Replicating class names, spacing, alignment, and structural elements
              - The base template files must remain unchanged and are used strictly as references
              - No textual content should be modified during this process
        """,
    },
]

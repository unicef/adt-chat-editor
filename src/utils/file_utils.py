import os
import shutil
from pathlib import Path

from src.workflows.state import ADTState


def is_output_empty() -> bool:
    """Check if the output directory is empty."""
    output_dir = "data/output"
    if not os.path.exists(output_dir):
        return True
    return len(os.listdir(output_dir)) == 0


def copy_input_to_output(state: ADTState) -> ADTState:
    """Copy all files from input to output folder if output is empty."""
    input_dir = "data/input"
    output_dir = "data/output"

    # Add the user query to the state
    state.user_query = str(state.messages[-1].content)

    # Check if output is empty
    if not is_output_empty():
        return state

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Copy all files from input to output
    for item in os.listdir(input_dir):
        input_path = os.path.join(input_dir, item)
        output_path = os.path.join(output_dir, item)

        if os.path.isfile(input_path):
            shutil.copy2(input_path, output_path)
        elif os.path.isdir(input_path):
            shutil.copytree(input_path, output_path, dirs_exist_ok=True)

    return state

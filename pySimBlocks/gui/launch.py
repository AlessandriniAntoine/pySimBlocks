import os
import subprocess
import sys

def main():
    """
    Entry point for pysimblocks CLI
    """

    # --------------------------------------------------
    # Resolve project directory
    # --------------------------------------------------
    if len(sys.argv) > 1:
        project_dir = os.path.abspath(sys.argv[1])
    else:
        project_dir = os.getcwd()

    if not os.path.isdir(project_dir):
        raise RuntimeError(f"Invalid project directory: {project_dir}")

    # --------------------------------------------------
    # Launch Streamlit editor
    # --------------------------------------------------
    base = os.path.dirname(os.path.abspath(__file__))
    editor = os.path.join(base, "editor.py")

    cmd = [
        sys.executable,
        "-m", "streamlit", "run",
        editor,
        "--",
        project_dir
    ]

    subprocess.run(cmd)

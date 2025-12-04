import os
import subprocess
import sys

def main():
    """Entry point for pysimblocks CLI"""
    base = os.path.dirname(os.path.abspath(__file__))
    editor = os.path.join(base, "editor.py")

    # Run Streamlit on editor.py
    cmd = [sys.executable, "-m", "streamlit", "run", editor]
    subprocess.run(cmd)

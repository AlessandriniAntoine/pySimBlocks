"""
CLI tools for pySimBlocks maintenance.

Usage:
    pysimblocks-update
"""

from pySimBlocks.tools.generate_blocks_index import generate_blocks_index


def main():
    print("Running pySimBlocks index update...")
    generate_blocks_index()
    print("pySimBlocks update complete.")

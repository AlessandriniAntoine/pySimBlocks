from pathlib import Path
from PySide6.QtWidgets import  QTextBrowser, QDialog, QVBoxLayout


class HelpDialog(QDialog):
    def __init__(self, md_path: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(md_path.name)
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)

        with md_path.open("r") as f:
            browser.setMarkdown(f.read())

        layout.addWidget(browser)

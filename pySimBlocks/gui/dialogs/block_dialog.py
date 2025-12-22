import ast
from PySide6.QtWidgets import (
    QHBoxLayout,
    QDialog,
    QLabel,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QComboBox,
    QFrame,
    QTextBrowser,
    QMessageBox,
    QSizePolicy
)
from PySide6.QtCore import Qt

from pySimBlocks.gui.dialogs.help_dialog import HelpDialog


class BlockDialog(QDialog):
    def __init__(self, block):
        super().__init__()
        self.block = block
        self.setWindowTitle("Edit block")
        self.setMinimumWidth(300)
        self.param_widgets = {}

        main_layout = QVBoxLayout(self)


        self.param_widgets = {}
        self.param_labels = {}
        self.depends_rules = {}

        self.build_parameters_form(main_layout)

        # --- Buttons row ---
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        ok_btn = QPushButton("Ok")
        ok_btn.setDefault(True)
        ok_btn.setAutoDefault(True)
        ok_btn.clicked.connect(self.ok)
        buttons_layout.addWidget(ok_btn)

        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.open_help)
        buttons_layout.addWidget(help_btn)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply)
        buttons_layout.addWidget(apply_btn)

        main_layout.addLayout(buttons_layout)

    # ------------------------------------------------------------
    # Form
    def description_part(self, form):
        title = QLabel(f"<b>{self.block.instance.meta.name}</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        form.addRow(title)

        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        frame.setLineWidth(1)

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(8, 6, 8, 6)

        desc = QTextBrowser()
        desc.setMarkdown(self.block.instance.meta.description)
        desc.setReadOnly(True)
        desc.setFrameShape(QFrame.NoFrame)
        desc.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        desc.document().setTextWidth(400)
        desc.setFixedHeight(int(desc.document().size().height()) + 6)

        frame_layout.addWidget(desc)
        form.addRow(frame)

    def build_parameters_form(self, layout):
        meta_params = self.block.instance.meta.parameters
        inst_params = self.block.instance.parameters

        form = QFormLayout()
        self.description_part(form)

        # --- Block name ---
        self.name_edit = QLineEdit(self.block.instance.name)
        form.addRow(QLabel("Block name:"), self.name_edit)

        for pname, pmeta in meta_params.items():
            widget = self._create_param_widget(pname, pmeta, inst_params)
            if widget is None:
                continue

            label = QLabel(f"{pname}:")
            if "description" in pmeta:
                label.setToolTip(pmeta["description"])
            form.addRow(label, widget)

            self.param_widgets[pname] = widget
            self.param_labels[pname] = label

            if "depends_on" in pmeta:
                self.depends_rules[pname] = pmeta["depends_on"]

        layout.addLayout(form)

        self.update_visibility()


    def update_visibility(self):
        inst_params = self.block.instance.parameters

        for pname, rules in self.depends_rules.items():
            visible = True

            dep_name = rules["parameter"]
            allowed_values = rules["values"]

            current_value = inst_params.get(dep_name)

            if current_value not in allowed_values:
                visible = False

            widget = self.param_widgets[pname]
            label = self.param_labels[pname]

            widget.setVisible(visible)
            label.setVisible(visible)


    # ------------------------------------------------------------
    # Buttons
    def apply(self):
        self.block.instance.name = self.name_edit.text()
        for pname, widget in self.param_widgets.items():
            if isinstance(widget, QComboBox):
                self.block.instance.parameters[pname] = widget.currentText()

            elif isinstance(widget, QLineEdit):
                text = widget.text().strip()
                if not text:
                    self.block.instance.parameters[pname] = None
                    continue
                try:
                    value = ast.literal_eval(text)
                except Exception:
                    value = text   # fallback (string simple)
                self.block.instance.parameters[pname] = value

        self.block.refresh_ports()

    def ok(self):
        self.apply()
        self.accept()

    def open_help(self):
        help_path = self.block.instance.meta.doc_path

        if help_path.exists():
            dialog = HelpDialog(help_path, self)
            dialog.exec()
        else:
            QMessageBox.information(self, "Help", "No documentation available.")


    # ------------------------------------------------------------
    # internal methods
    def _create_param_widget(self, name, meta, inst_params):
        ptype = meta.get("type")
        value = inst_params.get(name)

        # ENUM
        if ptype == "enum":
            combo = QComboBox()
            for v in meta.get("enum", []):
                combo.addItem(str(v))
            if value is not None:
                combo.setCurrentText(str(value))
            combo.currentTextChanged.connect(
                lambda val, name=name: self._on_param_changed(name, val)
            )
            return combo

        # SCALAR / FLOAT / INT / VECTOR / MATRIX
        edit = QLineEdit()
        if value is not None:
            edit.setText(str(value))
        elif "default" in meta:
            edit.setText(str(meta["default"]))

        return edit


    def _on_param_changed(self, name, value):
        self.block.instance.parameters[name] = value
        self.update_visibility()

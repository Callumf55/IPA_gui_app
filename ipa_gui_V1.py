import os
import pandas as pd
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QPushButton,
    QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QTextEdit, QDoubleSpinBox, QGroupBox, QSizePolicy, QSpinBox, QCheckBox
)
from ipa_run_pipeline import run_ipa_pipeline

class IPAGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IPA Pipeline GUI")
        self.setMinimumSize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.ms1_input = QLineEdit()
        form_layout.addRow("MS1 Input File:", self.create_browse_row(self.ms1_input))

        self.adducts_input = QLineEdit()
        form_layout.addRow("Adducts File:", self.create_browse_row(self.adducts_input))

        self.db_ms1_input = QLineEdit()
        form_layout.addRow("MS1 Database File:", self.create_browse_row(self.db_ms1_input))

        self.ms2_input = QLineEdit()
        form_layout.addRow("MS2 Input File (optional):", self.create_browse_row(self.ms2_input))

        self.db_ms2_input = QLineEdit()
        form_layout.addRow("MS2 Database File (optional):", self.create_browse_row(self.db_ms2_input))

        self.bio_input = QLineEdit()
        form_layout.addRow("Biological Network File (optional):", self.create_browse_row(self.bio_input))

        self.output_dir_input = QLineEdit()
        form_layout.addRow("Output Directory:", self.create_browse_row(self.output_dir_input, dir_mode=True))

        self.ionisation_box = QComboBox()
        self.ionisation_box.addItems(["Positive", "Negative"])
        form_layout.addRow("Ionisation Mode:", self.ionisation_box)

        self.ppm_spin = QSpinBox()
        self.ppm_spin.setRange(1, 100)
        self.ppm_spin.setValue(10)
        form_layout.addRow("PPM:", self.ppm_spin)

        self.iter_spin = QSpinBox()
        self.iter_spin.setRange(1, 10000)
        self.iter_spin.setValue(100)
        form_layout.addRow("Gibbs Sampler Iterations:", self.iter_spin)

        self.gibbs_selector = QComboBox()
        self.gibbs_selector.addItems(["adduct", "biochemical", "biochemical and adduct"])
        form_layout.addRow("Gibbs Sampler Type:", self.gibbs_selector)
        
        self.run_clustering_checkbox = QCheckBox("Run Clustering")
        self.run_clustering_checkbox.setChecked(True)
        form_layout.addRow(self.run_clustering_checkbox)

        self.run_gibbs_checkbox = QCheckBox("Run Gibbs Sampling")
        self.run_gibbs_checkbox.setChecked(True)
        form_layout.addRow(self.run_gibbs_checkbox)

        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["csv", "tsv", "xlsx"])
        form_layout.addRow("Export Format:", self.export_format_combo)

        self.summary_filename = QLineEdit("summary_annotations.csv")
        form_layout.addRow("Summary Output Filename:", self.summary_filename)

        self.run_button = QPushButton("Run IPA Pipeline")
        self.run_button.clicked.connect(self.run_pipeline)

        layout.addLayout(form_layout)
        layout.addWidget(self.run_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def create_browse_row(self, line_edit, dir_mode=False):
        row = QHBoxLayout()
        row.addWidget(line_edit)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self.browse_file(line_edit, dir_mode))
        row.addWidget(browse_btn)
        container = QWidget()
        container.setLayout(row)
        return container

    def browse_file(self, line_edit, dir_mode=False):
        if dir_mode:
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if path:
            line_edit.setText(path)

    def run_pipeline(self):
        run_ipa_pipeline(
            ms1_input_path=self.ms1_input.text(),
            adducts_path=self.adducts_input.text(),
            db_ms1_path=self.db_ms1_input.text(),
            output_dir=self.output_dir_input.text(),
            ms2_input_path=self.ms2_input.text() or None,
            db_ms2_path=self.db_ms2_input.text() or None,
            ionisation=1 if self.ionisation_box.currentText() == "Positive" else -1,
            ppm=self.ppm_spin.value(),
            run_clustering=self.run_clustering_checkbox.isChecked(),
            run_gibbs=self.run_gibbs_checkbox.isChecked(),
            gibbs_iterations=self.iter_spin.value(),
            gibbs_version=self.gibbs_selector.currentText(),
            Bio=self.bio_input.text() or None,
            export_format=self.export_format_combo.currentText(),
            summary_filename=self.summary_filename.text()
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IPAGUI()
    window.show()
    sys.exit(app.exec())

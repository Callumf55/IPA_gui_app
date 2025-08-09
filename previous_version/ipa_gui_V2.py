import os
import sys
import logging
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QPushButton,
    QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QTextEdit, QDoubleSpinBox, QGroupBox, QSizePolicy,
    QSpinBox, QCheckBox, QMessageBox, QProgressBar
)
from PySide6.QtCore import QThread, Signal, QObject

from ipa_run_pipeline_V2 import run_ipa_pipeline


# --- Redirect print() and logging to GUI console ---
class EmittingStream(QObject):
    text_written = Signal(str)

    def write(self, text):
        if text.strip():  # avoid empty lines
            self.text_written.emit(str(text))

    def flush(self):
        pass


# --- Custom logging handler ---
class QTextEditLogger(logging.Handler):
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)


# --- Worker thread ---
class PipelineWorker(QThread):
    finished = Signal()
    error = Signal(str)

    def __init__(self, pipeline_args):
        super().__init__()
        self.pipeline_args = pipeline_args

    def run(self):
        try:
            run_ipa_pipeline(**self.pipeline_args)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


# --- Main GUI Class ---
class IPAGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IPA Pipeline GUI")
        self.setMinimumSize(800, 600)

        # Save original stdout/stderr in case you want to restore later
        self._stdout = sys.stdout
        self._stderr = sys.stderr

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

        # Console output
        self.console = QTextEdit()
        self.console.setReadOnly(True)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)

        layout.addLayout(form_layout)
        layout.addWidget(self.run_button)
        layout.addWidget(QLabel("Console Output:"))
        layout.addWidget(self.console)
        layout.addWidget(self.progress_bar)

        # Redirect stdout/stderr to console
        stdout_stream = EmittingStream()
        stderr_stream = EmittingStream()
        stdout_stream.text_written.connect(self.console.append)
        stderr_stream.text_written.connect(self.console.append)
        sys.stdout = stdout_stream
        sys.stderr = stderr_stream

        # Also set up logging
        log_handler = QTextEditLogger(self.console)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(log_handler)
        logging.getLogger().setLevel(logging.INFO)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Test log to confirm console output
        logging.info("IPA GUI initialized successfully.")

    def create_browse_row(self, line_edit, dir_mode=False):
        container = QWidget()
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)

        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(lambda: self.browse_file(line_edit, dir_mode))

        line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row_layout.addWidget(line_edit, 1)
        row_layout.addWidget(browse_btn, 0)

        return container

    def browse_file(self, line_edit, dir_mode=False):
        if dir_mode:
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File", filter="Data Files (*.csv *.tsv *.xlsx);;All Files (*)")
        if path:
            line_edit.setText(path)

    def run_pipeline(self):
        required_fields = [
            (self.ms1_input, "MS1 Input File"),
            (self.adducts_input, "Adducts File"),
            (self.db_ms1_input, "MS1 Database File"),
            (self.output_dir_input, "Output Directory"),
        ]
        missing = [name for field, name in required_fields if not field.text().strip()]
        if missing:
            QMessageBox.warning(self, "Missing Inputs", f"Please fill in: {', '.join(missing)}")
            return

        self.console.clear()
        self.progress_bar.setVisible(True)

        args = {
            "ms1_input_path": self.ms1_input.text(),
            "adducts_path": self.adducts_input.text(),
            "db_ms1_path": self.db_ms1_input.text(),
            "output_dir": self.output_dir_input.text(),
            "ms2_input_path": self.ms2_input.text() or None,
            "db_ms2_path": self.db_ms2_input.text() or None,
            "ionisation": 1 if self.ionisation_box.currentText() == "Positive" else -1,
            "ppm": self.ppm_spin.value(),
            "run_clustering": self.run_clustering_checkbox.isChecked(),
            "run_gibbs": self.run_gibbs_checkbox.isChecked(),
            "gibbs_iterations": self.iter_spin.value(),
            "gibbs_version": self.gibbs_selector.currentText(),
            "Bio": self.bio_input.text() or None,
            "export_format": self.export_format_combo.currentText(),
            "summary_filename": self.summary_filename.text()
        }

        self.worker = PipelineWorker(args)
        self.worker.finished.connect(self.pipeline_done)
        self.worker.error.connect(self.pipeline_failed)
        self.worker.start()

    def pipeline_done(self):
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Done", "Pipeline completed successfully!")

    def pipeline_failed(self, error_message):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Pipeline failed:\n{error_message}")

    def closeEvent(self, event):
        # Restore original stdout/stderr on close
        sys.stdout = self._stdout
        sys.stderr = self._stderr
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IPAGUI()
    window.show()
    sys.exit(app.exec())

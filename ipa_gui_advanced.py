import os
import sys
import logging
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QPushButton,
    QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QTextEdit, QSpinBox, QCheckBox, QMessageBox,
    QGroupBox, QDoubleSpinBox, QScrollArea, QProgressBar, QSizePolicy
)
from PySide6.QtCore import QThread, Signal, QObject

from ipa_run_pipeline_ad import run_ipa_pipeline


class EmittingStream(QObject):
    text_written = Signal(str)

    def write(self, text):
        if text.strip():
            self.text_written.emit(str(text))

    def flush(self):
        pass


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


class IPAGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IPA Pipeline GUI")
        self.setMinimumSize(1000, 800)
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        def browse_row(widget, is_dir=False):
            container = QWidget()
            row_layout = QHBoxLayout(container)
            row_layout.setContentsMargins(0, 0, 0, 0)
            browse_btn = QPushButton("Browse")
            browse_btn.setFixedWidth(80)
            browse_btn.clicked.connect(lambda: self.browse(widget, is_dir))
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            row_layout.addWidget(widget, 1)
            row_layout.addWidget(browse_btn)
            return container

        # Inputs
        self.ms1_input = QLineEdit()
        form_layout.addRow("MS1 Input File:", browse_row(self.ms1_input))

        self.adducts_input = QLineEdit()
        form_layout.addRow("Adducts File:", browse_row(self.adducts_input))

        self.db_ms1_input = QLineEdit()
        form_layout.addRow("MS1 Database File:", browse_row(self.db_ms1_input))

        self.ms2_input = QLineEdit()
        form_layout.addRow("MS2 Input File (optional):", browse_row(self.ms2_input))

        self.db_ms2_input = QLineEdit()
        form_layout.addRow("MS2 Database File (optional):", browse_row(self.db_ms2_input))

        self.bio_input = QLineEdit()
        form_layout.addRow("Biological Network File (optional):", browse_row(self.bio_input))

        self.output_dir_input = QLineEdit()
        form_layout.addRow("Output Directory:", browse_row(self.output_dir_input, is_dir=True))

        self.ionisation_box = QComboBox()
        self.ionisation_box.addItems(["Positive", "Negative"])
        form_layout.addRow("Ionisation Mode:", self.ionisation_box)

        self.ppm_spin = QSpinBox()
        self.ppm_spin.setRange(1, 1000)
        self.ppm_spin.setValue(5)
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
        self.run_gibbs_checkbox.setChecked(False)
        form_layout.addRow(self.run_gibbs_checkbox)

        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["csv", "tsv", "xlsx"])
        form_layout.addRow("Export Format:", self.export_format_combo)

        self.summary_filename = QLineEdit("summary_annotations.csv")
        form_layout.addRow("Summary Output Filename:", self.summary_filename)

        self.export_most_likely_checkbox = QCheckBox("Export Most Likely Annotations")
        self.export_most_likely_checkbox.setChecked(True)
        self.export_most_likely_checkbox.toggled.connect(lambda val: self.most_likely_filename.setEnabled(val))
        form_layout.addRow(self.export_most_likely_checkbox)

        self.most_likely_filename = QLineEdit("most_likely_annotations.csv")
        form_layout.addRow("Most Likely Output Filename:", self.most_likely_filename)

        self.advanced_checkbox = QCheckBox("Enable Advanced Settings")
        self.advanced_checkbox.setChecked(False)
        self.advanced_checkbox.toggled.connect(self.toggle_advanced_group)
        form_layout.addRow(self.advanced_checkbox)

        self.advanced_group = QGroupBox("Advanced Settings")
        self.advanced_group.setVisible(False)
        advanced_form = QFormLayout()

        def floatbox(default, minv=0, maxv=99999):
            box = QDoubleSpinBox()
            box.setRange(minv, maxv)
            box.setValue(default)
            return box

        def intbox(default, minv=0, maxv=10000):
            box = QSpinBox()
            box.setRange(minv, maxv)
            box.setValue(default)
            return box

        # Clustering
        self.Cthr = floatbox(0.8)
        self.RTwin = floatbox(1.0)
        self.Intmode = QComboBox()
        self.Intmode.addItems(["max", "ave"])
        advanced_form.addRow("Clustering Cthr:", self.Cthr)
        advanced_form.addRow("Clustering RTwin:", self.RTwin)
        advanced_form.addRow("Clustering Intmode:", self.Intmode)

        # Isotope
        self.isoDiff = floatbox(1.0)
        self.MinIsoRatio = floatbox(0.5)
        self.isotope_ppm = intbox(100)
        advanced_form.addRow("Isotope Mass Diff:", self.isoDiff)
        advanced_form.addRow("Min Isotope Ratio:", self.MinIsoRatio)
        advanced_form.addRow("Isotope ppm:", self.isotope_ppm)

        # Annotation
        self.me = floatbox(5.48579909065e-04)
        self.ratiosd = floatbox(0.9)
        self.ppmunk = intbox(10)
        self.ratiounk = floatbox(0.7)
        self.ppmthr = intbox(10)
        self.pRTNone = floatbox(0.1)
        self.pRTout = floatbox(0.1)
        advanced_form.addRow("Electron Mass (me):", self.me)
        advanced_form.addRow("Intensity Ratio SD:", self.ratiosd)
        advanced_form.addRow("ppmunk:", self.ppmunk)
        advanced_form.addRow("ratiounk:", self.ratiounk)
        advanced_form.addRow("ppmthr:", self.ppmthr)
        advanced_form.addRow("pRTNone:", self.pRTNone)
        advanced_form.addRow("pRTout:", self.pRTout)

        # Gibbs
        self.burn = intbox(10)
        self.delta_add = floatbox(1.0)
        self.delta_bio = floatbox(1.0)
        self.all_out = QCheckBox()
        advanced_form.addRow("Burn-in Iterations:", self.burn)
        advanced_form.addRow("Delta (Adduct):", self.delta_add)
        advanced_form.addRow("Delta (Bio):", self.delta_bio)
        advanced_form.addRow("Return All Iterations:", self.all_out)

        self.advanced_group.setLayout(advanced_form)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addLayout(form_layout)
        layout.addWidget(self.advanced_group)

        self.run_button = QPushButton("Run IPA Pipeline")
        self.run_button.clicked.connect(self.run_pipeline)
        layout.addWidget(self.run_button)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(QLabel("Console Output:"))
        layout.addWidget(self.console)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        scroll.setWidget(container)
        self.setCentralWidget(scroll)

        sys.stdout = EmittingStream(text_written=self.console.append)
        sys.stderr = EmittingStream(text_written=self.console.append)

    def toggle_advanced_group(self, checked):
        self.advanced_group.setVisible(checked)

    def browse(self, line_edit, is_dir=False):
        if is_dir:
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "CSV Files (*.csv);;All Files (*)")
        if path:
            line_edit.setText(path)

    def run_pipeline(self):
        # Validate required files
        required_files = {
            "MS1 Input": self.ms1_input.text(),
            "Adducts File": self.adducts_input.text(),
            "MS1 DB File": self.db_ms1_input.text(),
            "Output Directory": self.output_dir_input.text()
        }
        for name, path in required_files.items():
            if not os.path.exists(path):
                QMessageBox.critical(self, "Input Error", f"{name} not found:\n{path}")
                return

        args = {
            "ms1_input_path": os.path.normpath(self.ms1_input.text()),
            "adducts_path": os.path.normpath(self.adducts_input.text()),
            "db_ms1_path": os.path.normpath(self.db_ms1_input.text()),
            "output_dir": os.path.normpath(self.output_dir_input.text()),
            "ms2_input_path": os.path.normpath(self.ms2_input.text()) or None,
            "db_ms2_path": os.path.normpath(self.db_ms2_input.text()) or None,
            "ionisation": 1 if self.ionisation_box.currentText() == "Positive" else -1,
            "ppm": self.ppm_spin.value(),
            "run_clustering": self.run_clustering_checkbox.isChecked(),
            "run_gibbs": self.run_gibbs_checkbox.isChecked(),
            "gibbs_iterations": self.iter_spin.value(),
            "gibbs_version": self.gibbs_selector.currentText(),
            "Bio": os.path.normpath(self.bio_input.text()) or None,
            "export_format": self.export_format_combo.currentText(),
            "summary_filename": self.summary_filename.text(),
            "most_likely_filename": self.most_likely_filename.text() if self.export_most_likely_checkbox.isChecked() else "",
        }

        if self.advanced_checkbox.isChecked():
            args["advanced_options"] = {
                "clustering_Cthr": self.Cthr.value(),
                "clustering_RTwin": self.RTwin.value(),
                "clustering_Intmode": self.Intmode.currentText(),
                "isoDiff": self.isoDiff.value(),
                "MinIsoRatio": self.MinIsoRatio.value(),
                "isotope_ppm": self.isotope_ppm.value(),
                "me": self.me.value(),
                "ratiosd": self.ratiosd.value(),
                "ppmunk": self.ppmunk.value(),
                "ratiounk": self.ratiounk.value(),
                "ppmthr": self.ppmthr.value(),
                "pRTNone": self.pRTNone.value(),
                "pRTout": self.pRTout.value(),
                "burn": self.burn.value(),
                "delta_add": self.delta_add.value(),
                "delta_bio": self.delta_bio.value(),
                "all_out": self.all_out.isChecked(),
            }

        self.console.clear()
        self.progress_bar.setVisible(True)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IPAGUI()
    window.show()
    sys.exit(app.exec())

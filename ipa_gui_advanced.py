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
        def help_link(url):
            label = QLabel(f'<a href="{url}" title="View documentation" style="text-decoration: none;">?</a>')
            label.setOpenExternalLinks(True)
            return label

        # Updated MS1 row with help link
        ms1_row = QWidget()
        ms1_layout = QHBoxLayout(ms1_row)
        ms1_layout.setContentsMargins(0, 0, 0, 0)
        ms1_layout.addWidget(self.ms1_input, 1)
        ms1_layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#1-ms1-data"))
        ms1_layout.addWidget(QPushButton("Browse", clicked=lambda: self.browse(self.ms1_input)))
        form_layout.addRow("MS1 Input File:", ms1_row)

        self.adducts_input = QLineEdit()
        form_layout.addRow("Adducts File:", browse_row(self.adducts_input))

        self.db_ms1_input = QLineEdit()
        def help_link(url):
            label = QLabel(f'<a href="{url}" title="View documentation" style="text-decoration: none;">?</a>')
            label.setOpenExternalLinks(True)
            return label

        # Updated db_MS1 row with help link
        db_ms1_row = QWidget()
        db_ms1_layout = QHBoxLayout(db_ms1_row)
        db_ms1_layout.setContentsMargins(0, 0, 0, 0)
        db_ms1_layout.addWidget(self.db_ms1_input, 1)
        db_ms1_layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#2-ms1-database-file-required"))
        db_ms1_layout.addWidget(QPushButton("Browse", clicked=lambda: self.browse(self.db_ms1_input)))
        form_layout.addRow("MS1 Database Input File:", db_ms1_row)

        self.ms2_input = QLineEdit()
        def help_link(url):
            label = QLabel(f'<a href="{url}" title="View documentation" style="text-decoration: none;">?</a>')
            label.setOpenExternalLinks(True)
            return label

        # Updated MS2 row with help link
        ms2_row = QWidget()
        ms2_layout = QHBoxLayout(ms2_row)
        ms2_layout.setContentsMargins(0, 0, 0, 0)
        ms2_layout.addWidget(self.ms2_input, 1)
        ms2_layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#2-ms2-data"))
        ms2_layout.addWidget(QPushButton("Browse", clicked=lambda: self.browse(self.ms2_input)))
        form_layout.addRow("MS2 Input File (optional):", ms2_row)

        self.db_ms2_input = QLineEdit()
        def help_link(url):
            label = QLabel(f'<a href="{url}" title="View documentation" style="text-decoration: none;">?</a>')
            label.setOpenExternalLinks(True)
            return label

        # Updated db_ms2 row with help link
        db_ms2_row = QWidget()
        db_ms2_layout = QHBoxLayout(db_ms2_row)
        db_ms2_layout.setContentsMargins(0, 0, 0, 0)
        db_ms2_layout.addWidget(self.db_ms2_input, 1)
        db_ms2_layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#3-ms2-database-file-only-required-if-ms2-data-is-available"))
        db_ms2_layout.addWidget(QPushButton("Browse", clicked=lambda: self.browse(self.db_ms2_input)))
        form_layout.addRow("MS2 Database Input File (optional):", db_ms2_row)

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
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ppm_spin)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#ppm"))
        form_layout.addRow("PPM:", row)


        self.iter_spin = QSpinBox()
        self.iter_spin.setRange(1, 10000)
        self.iter_spin.setValue(100)
        
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.iter_spin)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#gibbs-sampler-iterations"))
        form_layout.addRow("Gibbs Sampler Iterations:", row)

        self.ncores_spin = QSpinBox()
        self.ncores_spin.setRange(1, os.cpu_count() or 64)
        self.ncores_spin.setValue(1)
        self.ncores_spin.setSingleStep(1)
        self.ncores_spin.setSuffix(" cores")

        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ncores_spin)
        form_layout.addRow("CPU Cores:", row)

        self.gibbs_selector = QComboBox()
        self.gibbs_selector.addItems(["adduct", "biochemical", "biochemical and adduct"])

        # Help label for Gibbs Sampler
        self.gibbs_help_link = QLabel()
        self.gibbs_help_link.setOpenExternalLinks(True)

        # Function to update help link based on selected Gibbs sampler
        def update_gibbs_help(index):
            mapping = {
                "adduct": "https://github.com/Callumf55/IPA_GUI/blob/main/README.md#5-computing-posterior-probabilities-integrating-adducts-connections",
                "biochemical": "https://github.com/Callumf55/IPA_GUI/blob/main/README.md#6-computing-posterior-probabilities-integrating-biochemical-connections",
                "biochemical and adduct": "https://github.com/Callumf55/IPA_GUI/blob/main/README.md#7-computing-posterior-probabilities-integrating-both-adducts-and-biochemical-connections"
            }
            current = self.gibbs_selector.currentText()
            url = mapping.get(current, "#")
            self.gibbs_help_link.setText(f'<a href="{url}" title="View documentation" style="text-decoration: none;">?</a>')

        # Update once at startup and connect to selection change
        update_gibbs_help(0)
        self.gibbs_selector.currentIndexChanged.connect(update_gibbs_help)

        # Add selector + help link to row
        gibbs_row = QWidget()
        gibbs_layout = QHBoxLayout(gibbs_row)
        gibbs_layout.setContentsMargins(0, 0, 0, 0)
        gibbs_layout.addWidget(self.gibbs_selector)
        gibbs_layout.addWidget(self.gibbs_help_link)
        form_layout.addRow("Gibbs Sampler Type:", gibbs_row)


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

        def floatbox(default, minv=0, maxv=99999, step = 1.0, decimals=10):
            box = QDoubleSpinBox()
            box.setRange(minv, maxv)
            box.setDecimals(decimals)
            box.setSingleStep(step)
            box.setValue(default)
            return box

        def intbox(default, minv=0, maxv=10000, step=1):
            box = QSpinBox()
            box.setRange(minv, maxv)
            box.setSingleStep(step)
            box.setValue(default)
            return box

        # Clustering
        self.Cthr = floatbox(0.8, step = 0.05, decimals=2)
        self.RTwin = floatbox(1.0, step = 0.1, decimals=2)
        self.Intmode = QComboBox()
        self.Intmode.addItems(["max", "ave"])
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.Cthr)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#clustering-cthr"))
        advanced_form.addRow("Clustering Cthr:", row)

        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.RTwin)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#clustering-rtwin"))
        advanced_form.addRow("Clustering RTwin:", row)

        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.Intmode)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#clustering-intmode"))
        advanced_form.addRow("Clustering Intmode:", row)

        # Isotope
        self.isoDiff = floatbox(1.0, step=0.1, decimals=2, minv = 0)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.isoDiff)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#isotope-mass-diff"))
        advanced_form.addRow("Isotope Mass Diff:", row)

        self.MinIsoRatio = floatbox(0.5, step=0.01, decimals = 2)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.MinIsoRatio)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#min-isotope-ratio"))
        advanced_form.addRow("Min Isotope Ratio:", row)

        self.isotope_ppm = intbox(100)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.isotope_ppm)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#isotope-ppm"))
        advanced_form.addRow("Isotope ppm:", row)


        # Annotation
        self.me = floatbox(5.48579909065e-04, step=1e-10, minv=0.0, maxv=1.0, decimals=10)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.me)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#electron-mass-me"))
        advanced_form.addRow("Electron Mass (me):", row)

        self.ratiosd = floatbox(0.9, step = 0.05, decimals=2)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ratiosd)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#intensity-ratio-sd"))
        advanced_form.addRow("Intensity Ratio SD:", row)

        self.ppmunk = intbox(10)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ppmunk)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#ppmunk"))
        advanced_form.addRow("ppmunk:", row)

        self.ratiounk = floatbox(0.7, step = 0.05, decimals=2)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ratiounk)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#ratiounk"))
        advanced_form.addRow("ratiounk:", row)

        self.ppmthr = intbox(10)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ppmthr)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#ppmthr"))
        advanced_form.addRow("ppmthr:", row)

        self.pRTNone = floatbox(0.1, step = 0.01, decimals=2)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.pRTNone)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#prtnone"))
        advanced_form.addRow("pRTNone:", row)

        self.pRTout = floatbox(0.1, step = 0.01, decimals=2)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.pRTout)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#prtout"))
        advanced_form.addRow("pRTout:", row)


        # MSMS Annotation Settings
        self.mzdCS = floatbox(0.0, step=0.01, decimals=2)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.mzdCS)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#mzdcs"))
        advanced_form.addRow("mzdCS:", row)

        self.ppmCS = intbox(10)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ppmCS)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#ppmcs"))
        advanced_form.addRow("ppmCS:", row)

        self.CSunk = floatbox(0.7, step=0.05, decimals=2)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.CSunk)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#csunk"))
        advanced_form.addRow("CSunk:", row)

        self.evfilt = QCheckBox()
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.evfilt)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#evfilt"))
        advanced_form.addRow("evfilt:", row)


        # Gibbs
        self.burn = intbox(10)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.burn)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#burn-in-iterations"))
        advanced_form.addRow("Burn-in Iterations:", row)

        self.delta_add = floatbox(1.0, step=0.1, decimals=2)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.delta_add)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#delta-adduct"))
        advanced_form.addRow("Delta (Adduct):", row)

        self.delta_bio = floatbox(1.0, step=0.1, decimals=2)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.delta_bio)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#delta-bio"))
        advanced_form.addRow("Delta (Bio):", row)

        self.all_out = QCheckBox()
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.all_out)
        layout.addWidget(help_link("https://github.com/Callumf55/IPA_GUI/blob/main/README.md#all-out"))
        advanced_form.addRow("Return All Iterations:", row)

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

        def _safe_path(text):
            s = text.strip()
            return os.path.normpath(s) if s else None

        args = {
            "ms1_input_path": os.path.normpath(self.ms1_input.text()),
            "adducts_path": os.path.normpath(self.adducts_input.text()),
            "db_ms1_path": os.path.normpath(self.db_ms1_input.text()),
            "output_dir": os.path.normpath(self.output_dir_input.text()),
            "ms2_input_path": _safe_path(self.ms2_input.text()),
            "db_ms2_path": _safe_path(self.db_ms2_input.text()),
            "ionisation": 1 if self.ionisation_box.currentText() == "Positive" else -1,
            "ppm": self.ppm_spin.value(),
            "run_clustering": self.run_clustering_checkbox.isChecked(),
            "run_gibbs": self.run_gibbs_checkbox.isChecked(),
            "gibbs_iterations": self.iter_spin.value(),
            "gibbs_version": self.gibbs_selector.currentText(),
            "Bio": _safe_path(self.bio_input.text()),
            "export_format": self.export_format_combo.currentText(),
            "summary_filename": self.summary_filename.text(),
            "most_likely_filename": self.most_likely_filename.text() if self.export_most_likely_checkbox.isChecked() else "",
            "ncores": self.ncores_spin.value(),
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
                "mzdCS": self.mzdCS.value(),
                "ppmCS": self.ppmCS.value(),
                "CSunk": self.CSunk.value(),
                "evfilt": self.evfilt.isChecked(),
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


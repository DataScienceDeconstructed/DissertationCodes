import sys
import os
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QSlider, QCheckBox, QComboBox,
    QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# Extract variable values from directory path
def parse_variables(filepath):
    vars_of_interest = ["Umin", "rad", "den", "gap", "len", "NP"]
    out = {}
    parts = filepath.split(os.sep)
    for var in vars_of_interest:
        out[var] = "missing"
    for part in parts:
        for var in vars_of_interest:
            if part.startswith(var + "_"):
                out[var] = part.split("_", 1)[1]
    return out


class DataSetPanel(QWidget):
    def __init__(self, title, sync_checkbox=False):
        super().__init__()
        self.data = None
        self.slice_axis = 0
        self.im = None
        self.cbar = None

        layout = QVBoxLayout()
        hlayout = QHBoxLayout()

        self.load_btn = QPushButton(f"Load {title}")
        self.var_labels = {v: QLabel(f"{v}: missing") for v in
                           ["Umin", "rad", "den", "gap", "len", "NP"]}
        self.axis_box = QComboBox()
        self.axis_box.addItems(["X", "Y", "Z"])
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        hlayout.addWidget(self.load_btn)
        for v in self.var_labels.values():
            hlayout.addWidget(v)
        hlayout.addWidget(QLabel("Axis:"))
        hlayout.addWidget(self.axis_box)
        hlayout.addWidget(self.slider)

        if sync_checkbox:
            self.sync = QCheckBox("Sync with File1")
            hlayout.addWidget(self.sync)

        layout.addLayout(hlayout)

        # Matplotlib figure for summation + slice
        self.fig = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Open Data File", "", "NumPy files (*.npy *.dat)"
        )
        if fname:
            try:
                self.data = np.load(fname)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")
                return
            # update labels
            parsed = parse_variables(fname)
            for k, lbl in self.var_labels.items():
                lbl.setText(f"{k}: {parsed[k]}")
            # reset slider
            self.slider.setMinimum(0)
            self.slider.setMaximum(self.data.shape[self.slice_axis] - 1)
            self.slider.setValue(self.data.shape[self.slice_axis] // 2)
            self.update_view()

    def get_slice(self):
        if self.data is None:
            return None
        idx = self.slider.value()
        if self.slice_axis == 0:
            return self.data[idx, :, :]
        elif self.slice_axis == 1:
            return self.data[:, idx, :]
        else:
            return self.data[:, :, idx]

    def update_view(self):
        if self.data is None:
            return
        slice2d = self.get_slice()
        if slice2d is None:
            return
        self.fig.clear()

        # --- Summation plot ---
        ax_sum = self.fig.add_subplot(1, 2, 1)
        sums = [np.sum(self.data, axis=i) for i in range(3)]
        labels = ["X", "Y", "Z"]
        for lab, s in zip(labels, sums):
            s_flat = np.sum(s, axis=tuple(range(1, s.ndim)))
            s_norm = s_flat / np.max(s_flat) if np.max(s_flat) != 0 else s_flat
            ax_sum.plot(np.arange(len(s_norm)), s_norm, label=f"Sum {lab}")
        ax_sum.axvline(self.slider.value(), color="orange")
        ax_sum.legend()

        # --- Slice plot ---
        ax_slice = self.fig.add_subplot(1, 2, 2)
        if self.im is None:
            self.im = ax_slice.imshow(slice2d, cmap="viridis", origin="lower")
            self.cbar = self.fig.colorbar(self.im, ax=ax_slice)
        else:
            self.im.set_data(slice2d)
            self.im.set_clim(vmin=slice2d.min(), vmax=slice2d.max())
            if self.cbar:
                self.cbar.update_normal(self.im)

        self.canvas.draw_idle()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-file Slice Viewer")
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        # Panels
        self.panel1 = DataSetPanel("File1")
        self.panel2 = DataSetPanel("File2", sync_checkbox=True)
        self.panel_diff = DataSetPanel("Difference", sync_checkbox=True)

        layout.addWidget(self.panel1)
        layout.addWidget(self.panel2)
        layout.addWidget(self.panel_diff)

        central.setLayout(layout)

        # Connect buttons
        self.panel1.load_btn.clicked.connect(self.panel1.load_file)
        self.panel2.load_btn.clicked.connect(self.panel2.load_file)

        # Sync sliders
        self.panel1.slider.valueChanged.connect(self.sync_sliders)
        self.panel1.axis_box.currentIndexChanged.connect(self.sync_sliders)
        self.panel2.slider.valueChanged.connect(self.sync_sliders)
        self.panel2.axis_box.currentIndexChanged.connect(self.sync_sliders)

        # Update difference when files load or sliders move
        self.panel1.load_btn.clicked.connect(self.update_difference)
        self.panel2.load_btn.clicked.connect(self.update_difference)
        self.panel1.slider.valueChanged.connect(self.update_difference)
        self.panel2.slider.valueChanged.connect(self.update_difference)
        self.panel1.axis_box.currentIndexChanged.connect(self.update_difference)
        self.panel2.axis_box.currentIndexChanged.connect(self.update_difference)

    def sync_sliders(self):
        if self.panel2.data is not None and hasattr(self.panel2, "sync") and self.panel2.sync.isChecked():
            self.panel2.slice_axis = self.panel1.axis_box.currentIndex()
            self.panel2.axis_box.setCurrentIndex(self.panel1.axis_box.currentIndex())
            self.panel2.slider.setValue(self.panel1.slider.value())
            self.panel2.update_view()
        if self.panel_diff.data is not None and hasattr(self.panel_diff, "sync") and self.panel_diff.sync.isChecked():
            self.panel_diff.slice_axis = self.panel1.axis_box.currentIndex()
            self.panel_diff.axis_box.setCurrentIndex(self.panel1.axis_box.currentIndex())
            self.panel_diff.slider.setValue(self.panel1.slider.value())
            self.panel_diff.update_view()

    def update_difference(self):
        if self.panel1.data is None or self.panel2.data is None:
            return
        if self.panel1.data.shape != self.panel2.data.shape:
            QMessageBox.warning(self, "Shape mismatch",
                                "Files are different shapes; cannot subtract.")
            return
        self.panel_diff.data = self.panel1.data - self.panel2.data
        self.panel_diff.slice_axis = self.panel1.axis_box.currentIndex()
        self.panel_diff.slider.setMinimum(0)
        self.panel_diff.slider.setMaximum(self.panel_diff.data.shape[self.panel_diff.slice_axis] - 1)
        self.panel_diff.slider.setValue(self.panel1.slider.value())
        self.panel_diff.update_view()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

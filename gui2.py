import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QSlider, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Axis mapping
AXIS_MAP = {'X': 0, 'Y': 1, 'Z': 2}


class DensityExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("4D Density Explorer — Two Files + Difference")
        self.resize(1600, 1050)

        # Data storage
        self.data = {1: None, 2: None, 'diff': None}
        self.paths = {1: None, 2: None}

        # Per-dataset UI state
        self.selected_type = {1: 0, 2: 0, 'diff': 0}
        self.slice_axis = {1: 'Z', 2: 'Z', 'diff': 'Z'}
        self.slice_index = {1: 0, 2: 0, 'diff': 0}
        self.sync_to_file1 = {2: False, 'diff': False}

        # Store active colorbars so we can clear them
        self.colorbars = {1: None, 2: None, 'diff': None}

        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        # Controls row
        ctrl_row = QHBoxLayout()
        layout.addLayout(ctrl_row)

        # File loaders
        self.labels = {}
        self.sliders = {}
        self.sync_checks = {}

        for key in [1, 2]:
            box = QVBoxLayout()
            ctrl_row.addLayout(box)
            btn = QPushButton(f"Load File {key}")
            btn.clicked.connect(lambda _, k=key: self.load_file(k))
            box.addWidget(btn)
            self.labels[key] = QLabel("No file loaded")
            box.addWidget(self.labels[key])
            # Slice slider
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.valueChanged.connect(lambda v, k=key: self.on_slider_changed(k, v))
            box.addWidget(slider)
            self.sliders[key] = slider
            if key == 2:
                sync = QCheckBox("Sync to File 1")
                sync.stateChanged.connect(lambda state, k=2: self.set_sync(k, state))
                box.addWidget(sync)
                self.sync_checks[key] = sync

        # Diff file controls
        box = QVBoxLayout()
        ctrl_row.addLayout(box)
        self.labels['diff'] = QLabel("Difference dataset")
        box.addWidget(self.labels['diff'])
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.valueChanged.connect(lambda v, k='diff': self.on_slider_changed(k, v))
        box.addWidget(slider)
        self.sliders['diff'] = slider
        sync = QCheckBox("Sync to File 1")
        sync.stateChanged.connect(lambda state, k='diff': self.set_sync(k, state))
        box.addWidget(sync)
        self.sync_checks['diff'] = sync

        # Plot canvas
        self.fig, self.axarr = plt.subplots(3, 4, figsize=(14, 9))
        self.fig.subplots_adjust(hspace=0.6, wspace=0.4)
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        # Map: dataset -> row of axes
        self.axes = {1: self.axarr[0], 2: self.axarr[1], 'diff': self.axarr[2]}

    # ---------------- File handling ----------------
    def load_file(self, key):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Open File {key}", "",
            "Data Files (*.npy *.dat);;All Files (*)"
        )
        if not path:
            return
        try:
            arr = np.load(path, allow_pickle=False)
        except Exception:
            try:
                arr = np.loadtxt(path)
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Could not load file:\n{e}")
                return
        if arr.ndim != 4:
            QMessageBox.critical(self, "Shape Error", f"File {os.path.basename(path)} does not have 4D shape.")
            return
        self.data[key] = arr
        self.paths[key] = path
        self.labels[key].setText(os.path.basename(path))
        self.sliders[key].setMaximum(arr.shape[2] - 1)
        self.sliders[key].setValue(arr.shape[2] // 2)

        # If both loaded, compute difference
        if self.data[1] is not None and self.data[2] is not None:
            if self.data[1].shape == self.data[2].shape:
                self.data['diff'] = self.data[1] - self.data[2]
                self.sliders['diff'].setMaximum(self.data['diff'].shape[2] - 1)
                self.sliders['diff'].setValue(self.data['diff'].shape[2] // 2)
            else:
                QMessageBox.warning(self, "Shape Mismatch", "Files cannot be subtracted: different shapes.")
                self.data['diff'] = None

        self.update_view(key)
        if key in [1, 2] and self.data['diff'] is not None:
            self.update_view('diff')

    # ---------------- Events ----------------
    def set_sync(self, key, state):
        self.sync_to_file1[key] = (state == Qt.Checked)

    def on_slider_changed(self, key, value):
        self.slice_index[key] = value
        if key == 1:
            for k in [2, 'diff']:
                if self.sync_to_file1[k]:
                    self.sliders[k].blockSignals(True)
                    self.sliders[k].setValue(value)
                    self.sliders[k].blockSignals(False)
                    self.slice_index[k] = value
                    self.update_view(k)
        self.update_view(key)

    # ---------------- Updates ----------------
    def update_view(self, key):
        if self.data[key] is None:
            return
        self._update_summaries(key)
        self._update_slice_plot(key)
        self.canvas.draw_idle()

    def _update_summaries(self, key):
        data = self.data[key]
        axes_row = self.axes[key]
        for i in range(3):
            axes_row[i].clear()

        num_types = data.shape[3]
        colors = cm.get_cmap('tab20', max(10, num_types))

        sel_t = self.selected_type[key]
        for t in range(num_types):
            vol = data[:, :, :, t]
            x_vals = vol.sum(axis=(1, 2))
            y_vals = vol.sum(axis=(0, 2))
            z_vals = vol.sum(axis=(0, 1))

            def norm(v):
                vmax = float(np.max(np.abs(v))) if v.size else 0.0
                return (v / vmax) if vmax > 0 else v

            series = [norm(x_vals), norm(y_vals), norm(z_vals)]
            for i in range(3):
                axes_row[i].plot(
                    series[i], label=f"Type {t}", color=colors(t),
                    linewidth=2 if t == sel_t else 1, alpha=1.0 if t == sel_t else 0.6
                )

        titles = ["X (ΣY,Z)", "Y (ΣX,Z)", "Z (ΣX,Y)"]
        for i in range(3):
            axes_row[i].set_title(titles[i])
            axes_row[i].set_xlabel("Index")
            axes_row[i].set_ylabel("Normalized Density")
            axes_row[i].set_ylim(-1.05, 1.05)
            axes_row[i].axhline(0, color='black', linestyle=':')

        axis_idx = AXIS_MAP[self.slice_axis[key]]
        axes_row[axis_idx].axvline(self.slice_index[key], color='orange', linestyle='--')

        for i in range(3):
            axes_row[i].legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                               ncol=min(4, max(1, num_types)), fontsize='small', frameon=False)

    def _update_slice_plot(self, key):
        data = self.data[key]
        ax = self.axes[key][3]
        ax.clear()

        # Remove old colorbar if present
        if self.colorbars[key] is not None:
            self.colorbars[key].remove()
            self.colorbars[key] = None

        t = int(np.clip(self.selected_type[key], 0, data.shape[3]-1))
        vol = data[:, :, :, t]
        axis_txt = self.slice_axis[key]
        idx = int(np.clip(self.slice_index[key], 0, vol.shape[AXIS_MAP[axis_txt]]-1))

        if axis_txt == 'X':
            slice_2d = vol[idx, :, :]
            xlab, ylab = 'Y', 'Z'
        elif axis_txt == 'Y':
            slice_2d = vol[:, idx, :]
            xlab, ylab = 'X', 'Z'
        else:
            slice_2d = vol[:, :, idx]
            xlab, ylab = 'X', 'Y'

        slice_2d = np.squeeze(slice_2d)
        if slice_2d.ndim != 2:
            QMessageBox.warning(self, "Slice Error", f"Unexpected slice shape {slice_2d.shape} for imshow.")
            return

        im = ax.imshow(slice_2d.T, origin='lower', aspect='auto', cmap='viridis')
        ax.set_title(f"{axis_txt}-slice at {idx} (Type {t})")
        ax.set_xlabel(xlab)
        ax.set_ylabel(ylab)

        # Add colorbar next to slice
        self.colorbars[key] = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)


if __name__ == "__main__":
    app = QApplication([])
    win = DensityExplorer()
    win.show()
    app.exec_()

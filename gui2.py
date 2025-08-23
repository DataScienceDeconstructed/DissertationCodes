import sys
import os
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QComboBox, QSlider, QLabel, QCheckBox,
    QMessageBox
)
from PyQt5.QtCore import Qt


AXIS_MAP = {"X": 0, "Y": 1, "Z": 2}
VARS_OF_INTEREST = ["Umin", "rad", "den", "gap", "len", "NP"]


class DensityExplorer(QMainWindow):
    """
    Dual 4D density explorer for arrays shaped (X, Y, Z, T).
    Each file gets its own controls and a row of 4 plots:
      - 3 line plots showing normalized sums along X, Y, Z for ALL types (T)
      - 1 imshow showing a 2D slice of the SELECTED type at the chosen axis/index

    A "Sync Controls" checkbox can mirror File 1's slice axis + index to File 2.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("4D Density Explorer (Two Files)")

        # Data holders
        self.data = {1: None, 2: None}  # dict[file_id] -> ndarray
        self.filepaths = {1: None, 2: None}

        # Per-file UI state
        self.selected_type = {1: 0, 2: 0}
        self.slice_axis = {1: 'Z', 2: 'Z'}
        self.slice_index = {1: 0, 2: 0}

        # Build UI
        self._build_ui()

    # ---------------- UI BUILD -----------------
    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # --- Row of controls for File 1 ---
        self.controls1 = self._make_controls_row(file_id=1)
        root.addLayout(self.controls1['layout'])

        # Sync checkbox
        sync_row = QHBoxLayout()
        self.sync_checkbox = QCheckBox("Sync slice axis & index to File 2")
        self.sync_checkbox.stateChanged.connect(self._toggle_sync)
        sync_row.addWidget(self.sync_checkbox)
        sync_row.addStretch(1)
        root.addLayout(sync_row)

        # --- Row of controls for File 2 ---
        self.controls2 = self._make_controls_row(file_id=2)
        root.addLayout(self.controls2['layout'])

        # Figure: 2 rows x 4 columns
        self.fig, ax_grid = plt.subplots(2, 4, figsize=(16, 8))
        self.axes = {
            1: ax_grid[0, :],  # 4 axes for file 1
            2: ax_grid[1, :],  # 4 axes for file 2
        }
        self.canvas = FigureCanvas(self.fig)
        root.addWidget(self.canvas)

        self._init_empty_plots()

    def _make_controls_row(self, file_id: int):
        """Create a controls row for a given file_id (1 or 2)."""
        row = {}
        layout = QVBoxLayout()

        top = QHBoxLayout()
        load_btn = QPushButton(f"Load File {file_id} (.npy or .dat)")
        load_btn.clicked.connect(lambda: self._load_file(file_id))
        top.addWidget(load_btn)

        # Type selector: list 0..T-1 (filled after load)
        type_combo = QComboBox()
        type_combo.currentIndexChanged.connect(lambda _=None, fid=file_id: self._on_type_changed(fid))
        top.addWidget(QLabel("Type:"))
        top.addWidget(type_combo)

        # Axis selector: X/Y/Z
        axis_combo = QComboBox()
        axis_combo.addItems(["X", "Y", "Z"])
        axis_combo.setCurrentText('Z')
        axis_combo.currentIndexChanged.connect(lambda _=None, fid=file_id: self._on_axis_changed(fid))
        top.addWidget(QLabel("Slice Axis:"))
        top.addWidget(axis_combo)

        # Slice slider
        slider = QSlider(Qt.Horizontal)
        slider.valueChanged.connect(lambda _=None, fid=file_id: self._on_slider_changed(fid))
        top.addWidget(QLabel("Slice Index:"))
        top.addWidget(slider)

        layout.addLayout(top)

        # Variables label row
        var_layout = QHBoxLayout()
        labels = {}
        for var in VARS_OF_INTEREST:
            lbl = QLabel(f"{var} = missing")
            labels[var] = lbl
            var_layout.addWidget(lbl)
        var_layout.addStretch(1)
        layout.addLayout(var_layout)

        row['layout'] = layout
        row['type_combo'] = type_combo
        row['axis_combo'] = axis_combo
        row['slider'] = slider
        row['var_labels'] = labels
        return row

    def _init_empty_plots(self):
        for fid in (1, 2):
            for i in range(3):
                ax = self.axes[fid][i]
                ax.clear()
                ax.set_title(["X (ΣY,Z)", "Y (ΣX,Z)", "Z (ΣX,Y)"][i])
                ax.set_xlabel("Index")
                ax.set_ylabel("Normalized Density")
                ax.set_ylim(0, 1.05)
            ax = self.axes[fid][3]
            ax.clear()
            ax.set_title("Slice (load a file)")
        self.fig.tight_layout()
        self.canvas.draw()

    # --------------- FILE LOADING ----------------
    def _load_file(self, file_id: int):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open NumPy Array", "", "NumPy Arrays (*.npy *.dat)"
        )
        if not path:
            return

        try:
            arr = np.load(path)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load file:\n{e}")
            return

        if arr.ndim != 4:
            QMessageBox.critical(self, "Shape Error", f"Loaded array has shape {arr.shape}. Expected 4D (X, Y, Z, T).")
            return

        self.data[file_id] = arr
        self.filepaths[file_id] = path

        # Populate type selector 0..T-1
        T = arr.shape[3]
        combo = self.controls1['type_combo'] if file_id == 1 else self.controls2['type_combo']
        combo.blockSignals(True)
        combo.clear()
        combo.addItems([str(i) for i in range(T)])
        combo.setCurrentIndex(0)
        combo.blockSignals(False)
        self.selected_type[file_id] = 0

        # Reset axis/slider bounds for current axis
        self._reset_slider_bounds(file_id)

        # Update variable labels from path
        vars_found = self._parse_variables_from_path(path)
        labels = self.controls1['var_labels'] if file_id == 1 else self.controls2['var_labels']
        for k, lbl in labels.items():
            lbl.setText(f"{k} = {vars_found[k]}")

        # Draw
        self._update_all_plots(file_id)

        # If syncing is enabled and file_id == 2, immediately mirror axis/index
        if file_id == 2 and self.sync_checkbox.isChecked():
            self._apply_sync_values()
            self._update_all_plots(2)

    def _parse_variables_from_path(self, filepath: str):
        vars_dict = {k: "missing" for k in VARS_OF_INTEREST}
        parts = os.path.normpath(filepath).split(os.sep)
        for part in parts:
            if "_" in part:
                name, value = part.split("_", 1)
                if name in vars_dict:
                    vars_dict[name] = value
        return vars_dict

    def _reset_slider_bounds(self, file_id: int):
        data = self.data[file_id]
        if data is None:
            return
        axis = self.slice_axis[file_id]
        max_index = data.shape[AXIS_MAP[axis]] - 1
        slider = self.controls1['slider'] if file_id == 1 else self.controls2['slider']
        slider.blockSignals(True)
        slider.setMinimum(0)
        slider.setMaximum(max_index)
        slider.setValue(0)
        slider.blockSignals(False)
        self.slice_index[file_id] = 0

    # --------------- EVENT HANDLERS ---------------
    def _on_type_changed(self, file_id: int):
        if self.data[file_id] is None:
            return
        combo = self.controls1['type_combo'] if file_id == 1 else self.controls2['type_combo']
        txt = combo.currentText()
        if txt.isdigit():
            self.selected_type[file_id] = int(txt)
        self._update_all_plots(file_id)

    def _on_axis_changed(self, file_id: int):
        combo = self.controls1['axis_combo'] if file_id == 1 else self.controls2['axis_combo']
        axis = combo.currentText()
        self.slice_axis[file_id] = axis
        self._reset_slider_bounds(file_id)
        self._update_all_plots(file_id)

        # If syncing from file 1 -> file 2
        if self.sync_checkbox.isChecked() and file_id == 1 and self.data[2] is not None:
            self._apply_sync_values()
            self._update_all_plots(2)

    def _on_slider_changed(self, file_id: int):
        slider = self.controls1['slider'] if file_id == 1 else self.controls2['slider']
        self.slice_index[file_id] = slider.value()
        self._update_slice_plot(file_id)

        # mirror if syncing and source is file 1
        if self.sync_checkbox.isChecked() and file_id == 1 and self.data[2] is not None:
            self._apply_sync_values()
            self._update_slice_plot(2)

    def _apply_sync_values(self):
        # Mirror axis and index from file 1 -> file 2 (clamped to bounds)
        axis1 = self.slice_axis[1]
        idx1 = self.slice_index[1]

        # Set axis combo 2 to axis1
        axis_combo2 = self.controls2['axis_combo']
        axis_combo2.blockSignals(True)
        axis_combo2.setCurrentText(axis1)
        axis_combo2.blockSignals(False)
        self.slice_axis[2] = axis1

        # Adjust slider2 bounds for its data and set value clamped
        self._reset_slider_bounds(2)
        slider2 = self.controls2['slider']
        clamped = max(slider2.minimum(), min(idx1, slider2.maximum()))
        slider2.blockSignals(True)
        slider2.setValue(clamped)
        slider2.blockSignals(False)
        self.slice_index[2] = clamped

        # Disable axis/slider in file 2 while synced
        enabled = not self.sync_checkbox.isChecked()
        axis_combo2.setEnabled(enabled)
        slider2.setEnabled(enabled)

    def _toggle_sync(self, state):
        if state == Qt.Checked:
            # Immediately mirror current values
            if self.data[1] is not None:
                self._apply_sync_values()
                if self.data[2] is not None:
                    self._update_all_plots(2)
        else:
            # Re-enable controls for file 2
            self.controls2['axis_combo'].setEnabled(True)
            self.controls2['slider'].setEnabled(True)

    # --------------- PLOTTING ---------------
    def _update_all_plots(self, file_id: int):
        self._update_summaries(file_id)
        self._update_slice_plot(file_id)
        self.fig.tight_layout()
        self.canvas.draw()

    def _update_summaries(self, file_id: int):
        data = self.data[file_id]
        if data is None:
            return
        axes_row = self.axes[file_id]

        # Clear the 3 summary axes
        for i in range(3):
            axes_row[i].clear()

        num_types = data.shape[3]
        colors = cm.get_cmap('tab20', max(10, num_types))

        for t in range(num_types):
            vol = data[:, :, :, t]
            x_vals = vol.sum(axis=(1, 2))
            y_vals = vol.sum(axis=(0, 2))
            z_vals = vol.sum(axis=(0, 1))

            # Normalize safely
            def norm(v):
                vmax = float(v.max()) if v.size > 0 else 0.0
                return (v / vmax) if vmax > 0 else v

            x_vals = norm(x_vals)
            y_vals = norm(y_vals)
            z_vals = norm(z_vals)

            for i, arr1d in enumerate([x_vals, y_vals, z_vals]):
                axes_row[i].plot(
                    arr1d,
                    label=f"Type {t}",
                    color=colors(t),
                    linewidth=2 if t == self.selected_type[file_id] else 1,
                    alpha=1.0 if t == self.selected_type[file_id] else 0.6,
                )

        titles = ["X (ΣY,Z)", "Y (ΣX,Z)", "Z (ΣX,Y)"]
        for i in range(3):
            axes_row[i].set_title(titles[i])
            axes_row[i].set_xlabel("Index")
            axes_row[i].set_ylabel("Normalized Density")
            axes_row[i].set_ylim(0, 1.05)

        # Add/refresh orange slice line on the axis being sliced
        axis_idx = AXIS_MAP[self.slice_axis[file_id]]
        for i in range(3):
            # remove previous slice lines
            ax = axes_row[i]
            for line in list(ax.get_lines()):
                if getattr(line, 'is_slice_line', False):
                    line.remove()
            if i == axis_idx:
                vline = ax.axvline(self.slice_index[file_id], color='orange', linestyle='--')
                # tag line so we can remove it later
                vline.is_slice_line = True

        # Legend under plots
        for i in range(3):
            axes_row[i].legend(
                loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=min(4, max(1, data.shape[3])),
                fontsize='small', frameon=False
            )

    def _update_slice_plot(self, file_id: int):
        data = self.data[file_id]
        if data is None:
            return
        ax_img = self.axes[file_id][3]
        ax_img.clear()

        t = self.selected_type[file_id]
        if t < 0 or t >= data.shape[3]:
            return

        vol = data[:, :, :, t]
        axis = self.slice_axis[file_id]
        idx = self.slice_index[file_id]

        # Build 2D slice
        if axis == 'X':
            slice_2d = vol[idx, :, :]
            xlab, ylab = 'Y', 'Z'
        elif axis == 'Y':
            slice_2d = vol[:, idx, :]
            xlab, ylab = 'X', 'Z'
        else:  # 'Z'
            slice_2d = vol[:, :, idx]
            xlab, ylab = 'X', 'Y'

        # Ensure it's 2D
        if slice_2d.ndim != 2:
            # This should not happen, but guard just in case
            slice_2d = np.squeeze(slice_2d)
            if slice_2d.ndim != 2:
                QMessageBox.warning(self, "Slice Error", f"Unexpected slice shape {slice_2d.shape} for imshow.")
                return

        im = ax_img.imshow(slice_2d.T, origin='lower', aspect='auto', cmap='viridis')
        ax_img.set_title(f"{axis}-slice at {idx} (Type {t})")
        ax_img.set_xlabel(xlab)
        ax_img.set_ylabel(ylab)

        # Add a colorbar per row's image axis (optional, lightweight)
        # Remove previous colorbars for this axis if any
        # (Matplotlib handles reuse; keeping simple by not adding persistent colorbars.)

        self.canvas.draw_idle()


def main():
    app = QApplication(sys.argv)
    win = DensityExplorer()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

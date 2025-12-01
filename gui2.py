import sys
import os
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QComboBox, QSlider, QLabel, QCheckBox,
    QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt

import gap_brush_analysis

# ---------------- Constants ----------------
VARS = ["Umin", "rad", "den", "gap", "len", "NP", "system x", "system y", "system z", "concentration at z"]
AXIS_MAP = {"X": 0, "Y": 1, "Z": 2}


class DensityExplorer(QMainWindow):
    """4D (X,Y,Z,T) density explorer for two files + their difference.

    Controls (top): load buttons, variable labels, type/axis selectors, sliders, and sync checkboxes.
    Plots   (bottom): 3 rows (File 1, File 2, Diff), each with:
      - 3 summary line plots (X, Y, Z sums, all types overlaid, selected type highlighted)
      - 1 slice viewer (imshow) with a persistent colorbar for the selected type at current axis/index.

    Sync checkboxes mirror File 1's axis + slider to File 2 and/or Diff (with clamping).
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("4D Density Explorer — Two Files + Difference")
        self.resize(1600, 1050)

        # Data storage
        self.data = {1: None, 2: None, 'diff': None}
        self.paths = {1: None, 2: None}
        self.last_frame_path = {1: None, 2: None}
        self.file_xyz_path = {1: None, 2: None}
        # Per-dataset UI state
        self.selected_type = {1: 0, 2: 0, 'diff': 0}
        self.slice_axis = {1: 'Z', 2: 'Z', 'diff': 'Z'}
        self.slice_index = {1: 0, 2: 0, 'diff': 0}
        self.sync_to_file1 = {2: False, 'diff': False}

        # Persistent artists for slice panels
        self.slice_images = {1: None, 2: None, 'diff': None}   # matplotlib.image.AxesImage
        self.colorbars    = {1: None, 2: None, 'diff': None}   # matplotlib.colorbar.Colorbar
        self.RDPs = {1: {'brush': None, 'gap': None}, 2: {'brush': None, 'gap': None}}
        self.concentrations = {1: {'brush': None, 'gap': None}, 2: {'brush': None, 'gap': None}}
        self._build_ui()

    # ----------------------------- UI -----------------------------
    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # ====== Controls (Top) ======
        # ---- Controls row for File 1 ----
        root.addWidget(self._make_dataset_header("File 1 Controls"))
        self.ctrl1 = self._make_controls_row(file_id=1)
        root.addLayout(self.ctrl1['layout'])

        # ---- Controls row for File 2 (with sync) ----
        root.addWidget(self._make_dataset_header("File 2 Controls"))
        self.ctrl2 = self._make_controls_row(file_id=2, with_sync=True)
        root.addLayout(self.ctrl2['layout'])

        # ---- Controls row for Diff (computed) ----
        root.addWidget(self._make_dataset_header("Difference Controls (File 2 − File 1)"))
        self.ctrlD = self._make_controls_row(file_id='diff', with_sync=True, is_diff=True)
        root.addLayout(self.ctrlD['layout'])

        # ====== Plots (Bottom): 3 rows × 4 columns ======
        self.fig, grid = plt.subplots(3, 4, figsize=(16, 12))
        self.axes = {
            1: grid[0, :],      # row 0: File 1
            2: grid[1, :],      # row 1: File 2
            'diff': grid[2, :], # row 2: Diff
        }
        self.canvas = FigureCanvas(self.fig)
        root.addWidget(self.canvas)

        self._init_empty_plots()

    def _make_dataset_header(self, title: str) -> QLabel:
        return QLabel(f"<b>{title}</b>")

    def _make_controls_row(self, file_id, with_sync: bool = False, is_diff: bool = False):
        row = {}
        layout = QVBoxLayout()

        # --- Variables from path (for File 1 and File 2) ---
        var_row = QHBoxLayout()
        var_labels = {}
        if not is_diff:
            for v in VARS:
                lab = QLabel(f"{v} = missing")
                var_labels[v] = lab
                var_row.addWidget(lab)
        else:
            var_row.addWidget(QLabel("Diff variables are derived from the two loaded files"))
        var_row.addStretch(1)
        layout.addLayout(var_row)

        # --- Controls line: load (except diff), type, axis, slider (expanding), sync (if applicable) ---
        top = QHBoxLayout()

        # Load button
        if not is_diff:
            load_btn = QPushButton(f"Load {'File 1' if file_id==1 else 'File 2'} (.npy / .dat)")
            load_btn.clicked.connect(lambda: self._load_file(file_id))
            top.addWidget(load_btn)
        else:
            info = QLabel("Computed automatically when both files are loaded (matching shape).")
            top.addWidget(info)

        # Type selector (enabled after load)
        type_combo = QComboBox()
        type_combo.currentIndexChanged.connect(lambda _=None, fid=file_id: self._on_type_changed(fid))
        type_combo.setEnabled(False)
        top.addWidget(QLabel("Type:"))
        top.addWidget(type_combo)

        # Axis selector
        axis_combo = QComboBox()
        axis_combo.addItems(["X", "Y", "Z"])
        axis_combo.setCurrentText('Z')
        axis_combo.currentIndexChanged.connect(lambda _=None, fid=file_id: self._on_axis_changed(fid))
        top.addWidget(QLabel("Slice Axis:"))
        top.addWidget(axis_combo)

        # Slider (put LAST and make it expand to the right edge)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 0)
        slider.setValue(0)
        slider.valueChanged.connect(lambda _=None, fid=file_id: self._on_slider_changed(fid))
        slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top.addWidget(QLabel("Slice Index:"))
        top.addWidget(slider, stretch=1)

        # Sync checkbox if requested (file 2 and diff)
        sync_cb = None
        if with_sync:
            sync_cb = QCheckBox("Sync to File 1")
            sync_cb.stateChanged.connect(lambda state, fid=file_id: self._toggle_sync(fid, state))
            top.addWidget(sync_cb)

        layout.addLayout(top)

        # Store references
        row['layout'] = layout
        row['type_combo'] = type_combo
        row['axis_combo'] = axis_combo
        row['slider'] = slider
        row['sync_cb'] = sync_cb
        row['var_labels'] = var_labels
        return row



    def _init_empty_plots(self):
        titles = ["X (ΣY,Z)", "Y (ΣX,Z)", "Z (ΣX,Y)"]
        for key in (1, 2, 'diff'):
            # reset persistent artists
            self.slice_images[key] = None
            if self.colorbars[key] is not None:
                try:
                    self.colorbars[key].remove()
                except Exception:
                    pass
                self.colorbars[key] = None

            for i in range(3):
                ax = self.axes[key][i]
                ax.clear()
                ax.set_title(titles[i])
                ax.set_xlabel("Index")
                ax.set_ylabel("Normalized Density")
                ax.set_ylim(-1.05, 1.05)
                ax.axhline(0.0, color='black', linestyle=':')
            ax = self.axes[key][3]
            ax.clear()
            if key == 'diff':
                ax.set_title("Slice (load both files to compute difference)")
            else:
                ax.set_title("Slice (load a file)")
        self.fig.tight_layout()
        self.canvas.draw()

    # ----------------------------- Load & Parse -----------------------------
    def _load_file(self, file_id: int):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open NumPy Array", "", "NumPy Arrays (*.npy *.dat);;All Files (*)"
        )
        if not path:
            return
        try:
            arr = np.load(path, allow_pickle=False)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load file:\n{e}")
            return
        if arr.ndim != 4:
            QMessageBox.critical(self, "Shape Error", f"Loaded array has shape {arr.shape}. Expected 4D (X, Y, Z, T).")
            return

        self.data[file_id] = arr
        self.paths[file_id] = path

        last_frame_path = Path(path)
        parent_path = str(last_frame_path.parent)
        last_frame_str = parent_path +"/last_frame.xyz"
        self.last_frame_path[file_id] = last_frame_str

        file_xyz_path = Path(path)
        file_xyz_path_parent = Path(file_xyz_path.parent)
        ext = ".xyz"

        files = list(file_xyz_path_parent.glob(f"frames_exp*{ext}"))
        self.file_xyz_path[file_id] = str(files[0])

        vals = {v: 'missing' for v in VARS}
        for part in os.path.normpath(
                self.last_frame_path[file_id]
                ).split(os.sep):
            if '_' in part:
                name, value = part.split('_', 1)
                if name in vals:
                    vals[name] = value
#"system x", "system y", "system z", "concentration at z"
        vals["system x"] = arr.shape[0]
        vals["system y"] = arr.shape[1]
        vals["system z"] = arr.shape[2]

        self.RDPs[file_id]['brush'],self.RDPs[file_id]['gap'], self.concentrations[file_id]['brush'] = gap_brush_analysis.calc_2D_avg_RDP(self.file_xyz_path[file_id],
                                                           arr.shape[:3],
                                                           int(vals['gap']),
                                                           int(vals['NP']),
                                                           int(vals['len'])
                                                           )
        vals["concentration at z"] = self.concentrations[file_id]['brush'][0]

        # self.RDPs[file_id]['brush'],self.RDPs[file_id]['gap'] = gap_brush_analysis.calc_2D_RDP(self.last_frame_path[file_id],
        #                                       arr.shape[:3],
        #                                       int(vals['gap']),
        #                                       int(vals['NP']),
        #                                       int(vals['len'])
        #                                       )

        # Reset slice artists for this dataset (so first draw recreates imshow + cbar once)
        self._reset_slice_artists(file_id)

        # Populate type selector 0..T-1
        T = arr.shape[3]
        ctrl = self._ctrl_for(file_id)
        combo = ctrl['type_combo']
        combo.blockSignals(True)
        combo.clear()
        combo.addItems([str(i) for i in range(T)])
        combo.setCurrentIndex(0)
        combo.setEnabled(True)
        combo.blockSignals(False)
        self.selected_type[file_id] = 0

        # Reset axis/slider bounds and variables
        self._reset_slider_bounds(file_id)
        self._update_var_labels_from_path(file_id, path, arr.shape[:3])

        # Update plots for this dataset
        self._update_all_plots(file_id)

        # Try compute diff if both loaded
        self._compute_or_clear_diff()

        # If File 1 changed and others are synced, mirror now
        if file_id == 1:
            if self.sync_to_file1[2] and self.data[2] is not None:
                self._apply_sync_to_dataset(2)
                self._update_all_plots(2)
            if self.sync_to_file1['diff'] and self.data['diff'] is not None:
                self._apply_sync_to_dataset('diff')
                self._update_all_plots('diff')

    def _reset_slice_artists(self, key):
        # Remove persistent colorbar if it exists; reset image handle.
        if self.colorbars[key] is not None:
            try:
                self.colorbars[key].remove()
            except Exception:
                pass
            self.colorbars[key] = None
        self.slice_images[key] = None

    def _update_var_labels_from_path(self, file_id: int, path: str, _system_dims):
        # Parse variables from directory names: varname_value
        vals = {v: 'missing' for v in VARS}
        for part in os.path.normpath(path).split(os.sep):
            if '_' in part:
                name, value = part.split('_', 1)
                if name in vals:
                    vals[name] = value

        vals["system x"] = str(_system_dims[0])
        vals["system y"] = str(_system_dims[1])
        vals["system z"] = str(_system_dims[2])

        labels = self._ctrl_for(file_id)['var_labels']
        for k, lab in labels.items():
            lab.setText(f"{k} = {vals[k]}")

    def _compute_or_clear_diff(self):
        d1, d2 = self.data[1], self.data[2]
        if d1 is None or d2 is None:
            self.data['diff'] = None
            self._clear_diff_controls()
            self._clear_diff_plots()
            return
        if d1.shape != d2.shape:
            self.data['diff'] = None
            self._clear_diff_controls()
            self._clear_diff_plots()
            QMessageBox.critical(
                self, "Shape Mismatch",
                f"File 1 shape {d1.shape} and File 2 shape {d2.shape} do not match. Cannot compute difference."
            )
            return

        # Compute diff: File 2 − File 1
        self.data['diff'] = d2 - d1

        # Reset slice artists for diff (so we create once with cbar)
        self._reset_slice_artists('diff')

        # Setup diff type selector
        T = d1.shape[3]
        combo = self.ctrlD['type_combo']
        combo.blockSignals(True)
        combo.clear()
        combo.addItems([str(i) for i in range(T)])
        combo.setCurrentIndex(min(self.selected_type['diff'], T-1))
        combo.setEnabled(True)
        combo.blockSignals(False)

        # Reset slider bounds for diff
        self._reset_slider_bounds('diff')

        # If synced, mirror now
        if self.sync_to_file1['diff'] and self.data[1] is not None:
            self._apply_sync_to_dataset('diff')

        # Draw diff row
        self._update_all_plots('diff')

    def _clear_diff_controls(self):
        self.ctrlD['type_combo'].clear()
        self.ctrlD['type_combo'].setEnabled(False)
        self.ctrlD['slider'].setRange(0, 0)
        self.ctrlD['slider'].setValue(0)

    def _clear_diff_plots(self):
        titles = ["X (ΣY,Z)", "Y (ΣX,Z)", "Z (ΣX,Y)"]
        # reset persistent artists
        self._reset_slice_artists('diff')
        for i in range(4):
            ax = self.axes['diff'][i]
            ax.clear()
        for i in range(3):
            self.axes['diff'][i].set_title(titles[i])
            self.axes['diff'][i].set_ylim(-1.05, 1.05)
            self.axes['diff'][i].set_xlabel("Index")
            self.axes['diff'][i].set_ylabel("Normalized Density")
            self.axes['diff'][i].axhline(0.0, color='black', linestyle=':')
        self.axes['diff'][3].set_title("Slice (load both files to compute difference)")
        self.fig.tight_layout()
        self.canvas.draw()

    # ------------------------- Event handlers -------------------------
    def _on_type_changed(self, key):
        if self.data.get(key) is None:
            return
        ctrl = self._ctrl_for(key)
        txt = ctrl['type_combo'].currentText()
        if txt.isdigit():
            self.selected_type[key] = int(txt)
        self._update_all_plots(key)

    def _on_axis_changed(self, key):
        ctrl = self._ctrl_for(key)
        self.slice_axis[key] = ctrl['axis_combo'].currentText()
        self._reset_slider_bounds(key)
        # When axis changes, we can keep same image artist; imshow supports new shape via set_data
        self._update_all_plots(key)
        # Propagate if File 1 changed and targets are synced
        if key == 1:
            if self.sync_to_file1[2] and self.data[2] is not None:
                self._apply_sync_to_dataset(2)
                self._update_all_plots(2)
            if self.sync_to_file1['diff'] and self.data['diff'] is not None:
                self._apply_sync_to_dataset('diff')
                self._update_all_plots('diff')

    def _on_slider_changed(self, key):
        ctrl = self._ctrl_for(key)
        self.slice_index[key] = ctrl['slider'].value()
        self._update_all_plots(key)
        # Propagate if File 1 changed and targets are synced
        if key == 1:
            if self.sync_to_file1[2] and self.data[2] is not None:
                self._apply_sync_to_dataset(2)
                self._update_all_plots(2)
            if self.sync_to_file1['diff'] and self.data['diff'] is not None:
                self._apply_sync_to_dataset('diff')
                self._update_all_plots('diff')

            labels = self._ctrl_for(key)['var_labels']
            #labels["concentration at z"].setText(self, self.concentrations[1]['brush'][self.slice_index[key]])
            for k, lab in labels.items():
                if k == "concentration at z":
                    lab.setText(f"{k} = {self.concentrations[1]['brush'][self.slice_index[key]]}")

    def _toggle_sync(self, key, state):
        self.sync_to_file1[key] = (state == Qt.Checked)
        ctrl = self._ctrl_for(key)
        ctrl['axis_combo'].setEnabled(not self.sync_to_file1[key])
        ctrl['slider'].setEnabled(not self.sync_to_file1[key])
        if self.sync_to_file1[key] and self.data[1] is not None:
            self._apply_sync_to_dataset(key)
            self._update_all_plots(key)

    # ------------------------- Helpers -------------------------
    def _ctrl_for(self, key):
        return self.ctrl1 if key == 1 else (self.ctrl2 if key == 2 else self.ctrlD)

    def _reset_slider_bounds(self, key):
        data = self.data.get(key)
        if data is None:
            return
        axis = AXIS_MAP[self.slice_axis[key]]
        max_index = max(0, data.shape[axis] - 1)
        ctrl = self._ctrl_for(key)
        sld = ctrl['slider']
        sld.blockSignals(True)
        sld.setRange(0, max_index)
        if self.slice_index[key] > max_index:
            self.slice_index[key] = max_index
        sld.setValue(self.slice_index[key])
        sld.blockSignals(False)

    def _apply_sync_to_dataset(self, dst_key):
        # Mirror File 1 axis/index to dst_key (clamped to bounds)
        if self.data.get(dst_key) is None or self.data.get(1) is None:
            return
        axis_txt = self.slice_axis[1]
        idx = self.slice_index[1]
        self.slice_axis[dst_key] = axis_txt

        dst_ctrl = self._ctrl_for(dst_key)
        # Set axis combo (block signals to avoid recursion)
        dst_ctrl['axis_combo'].blockSignals(True)
        dst_ctrl['axis_combo'].setCurrentText(axis_txt)
        dst_ctrl['axis_combo'].blockSignals(False)

        # Clamp index to dst bounds
        self._reset_slider_bounds(dst_key)
        dst_sld = dst_ctrl['slider']
        clamped = int(np.clip(idx, dst_sld.minimum(), dst_sld.maximum()))
        dst_ctrl['slider'].blockSignals(True)
        dst_ctrl['slider'].setValue(clamped)
        dst_ctrl['slider'].blockSignals(False)
        self.slice_index[dst_key] = clamped

    # ------------------------- Plotting -------------------------
    def _update_all_plots(self, key):
        if self.data.get(key) is None:
            return
        self._update_summaries(key)
        self._update_slice_plot(key)
        self.fig.tight_layout()
        self.canvas.draw_idle()

    def _update_summaries(self, key):
        data = self.data[key]
        axes_row = self.axes[key]
        # Clear the 3 summary axes
        for i in range(3):
            axes_row[i].clear()

        num_types = data.shape[3]
        colors = cm.get_cmap('tab20', max(10, num_types))

        # Plot all types with highlight on selected
        sel_t = self.selected_type[key]
        for t in range(num_types):
            vol = data[:, :, :, t]
            x_vals = vol.sum(axis=(1, 2))
            y_vals = vol.sum(axis=(0, 2))
            z_vals = vol.sum(axis=(0, 1))

            # Normalize using absolute max (so curves lie in [-1, 1])
            def norm(v):
                vmax = float(np.max(np.abs(v))) if v.size else 0.0
                return (v / vmax) if vmax > 0 else v

            series = [norm(x_vals), norm(y_vals), norm(z_vals)]
            for i in range(3):
                axes_row[i].plot(
                    series[i],
                    label=f"Type {t}",
                    color=colors(t),
                    linewidth=2 if t == sel_t else 1,
                    alpha=1.0 if t == sel_t else 0.6
                )

        titles = ["X (ΣY,Z)", "Y (ΣX,Z)", "Z (ΣX,Y)"]
        for i in range(3):
            axes_row[i].set_title(titles[i])
            axes_row[i].set_xlabel("Index")
            axes_row[i].set_ylabel("Normalized Density")
            axes_row[i].set_ylim(-1.05, 1.05)
            # Dotted black zero-line for positive/negative reference
            axes_row[i].axhline(0.0, color='black', linestyle=':')

        # Orange slice line on the currently selected axis plot
        axis_idx = AXIS_MAP[self.slice_axis[key]]
        axes_row[axis_idx].axvline(self.slice_index[key], color='orange', linestyle='--')
        # add above to concentration plot ^^
        # Legend below each plot
        for i in range(3):
            axes_row[i].legend(
                loc='upper center',
                bbox_to_anchor=(0.5, -0.15),
                ncol=min(4, max(1, num_types)),
                fontsize='small',
                frameon=False
            )

    def _update_slice_plot(self, key):
        """Update (or first-time create) the slice imshow + persistent colorbar without shrinking."""
        data = self.data[key]
        ax = self.axes[key][3]

        # Compute 2D slice (ensure strictly 2D)
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

        # Create once; then only update data + color limits + colorbar scaling.
        if self.slice_images[key] is None:
            ax.cla()  # clear once on first draw to ensure a clean axes
            im = ax.imshow(slice_2d.T, origin='lower', aspect='auto', cmap='viridis')
            ax.set_title(f"{axis_txt}-slice at {idx} (Type {t})")
            ax.set_xlabel(xlab)
            ax.set_ylabel(ylab)
            # Create colorbar once and keep reference
            cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            self.slice_images[key] = im
            self.colorbars[key] = cbar
        else:
            # Update existing image & labels/clim; DO NOT recreate colorbar
            im = self.slice_images[key]
            im.set_data(slice_2d.T)
            # Update color scaling to new data range
            vmin = float(np.min(slice_2d)) if slice_2d.size else 0.0
            vmax = float(np.max(slice_2d)) if slice_2d.size else 1.0
            if vmin == vmax:
                # Avoid zero range; expand slightly
                eps = 1e-12
                vmin -= eps
                vmax += eps
            im.set_clim(vmin=vmin, vmax=vmax)

            ax.set_title(f"{axis_txt}-slice at {idx} (Type {t})")
            ax.set_xlabel(xlab)
            ax.set_ylabel(ylab)

            # Refresh the existing colorbar to match updated image
            if self.colorbars[key] is not None:
                self.colorbars[key].update_normal(im)

        if key == 1:
            key = 2
            #grab new axis object

            axes_row = self.axes[key]
            # Clear the 3 summary axes
            for i in range(3):
                axes_row[i].clear()

            axes_row[2].set_title("Z Plane RDP")
            axes_row[2].plot(
                self.RDPs[1]['brush'][self.slice_index[1]],
                label="RDP for Z plane",
                linewidth=1,
                alpha=1.0,

            )
            axes_row[1].set_title("Z Plane NP Concentration")
            axes_row[1].plot(
                self.concentrations[1]['brush'] ,
                label="NP Concentration",
                linewidth=1,
                alpha=1.0,

            )

            ax = self.axes[key][3]

            slice_xy = slice_2d - np.mean(slice_2d)
            fft2d = np.fft.fftshift(np.fft.fft2(slice_xy))
            slice_2d =  np.abs(fft2d)

            if self.slice_images[key] is None:
                ax.cla()  # clear once on first draw to ensure a clean axes
                im = ax.imshow(slice_2d.T, origin='lower', aspect='auto', cmap='viridis')
                ax.set_title(f"Z Plane FFT at {idx} (Type {t})")
                ax.set_xlabel(xlab)
                ax.set_ylabel(ylab)
                # Create colorbar once and keep reference
                cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                self.slice_images[key] = im
                self.colorbars[key] = cbar
            else:
                # Update existing image & labels/clim; DO NOT recreate colorbar
                im = self.slice_images[key]
                im.set_data(slice_2d.T)
                # Update color scaling to new data range
                vmin = float(np.min(slice_2d)) if slice_2d.size else 0.0
                vmax = float(np.max(slice_2d)) if slice_2d.size else 1.0
                if vmin == vmax:
                    # Avoid zero range; expand slightly
                    eps = 1e-12
                    vmin -= eps
                    vmax += eps
                im.set_clim(vmin=vmin, vmax=vmax)

                ax.set_title(f"{axis_txt}-slice at {idx} (Type {t})")
                ax.set_xlabel(xlab)
                ax.set_ylabel(ylab)

                # Refresh the existing colorbar to match updated image
                if self.colorbars[key] is not None:
                    self.colorbars[key].update_normal(im)



def main():
    app = QApplication(sys.argv)
    win = DensityExplorer()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

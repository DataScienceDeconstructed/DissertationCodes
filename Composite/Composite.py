import numpy as np
import matplotlib.pyplot as plt

class Polymer_Sim():

    def __init__(self, _length=128, ):
        self.frame_data = None
        self.heights = None
        self.heightshist = None

    def calc_heights(self):
        if self.frame_data is not None:
            #subtract z component of end monomer from base monomer
            self.heights = self.frame_data[:,:,-1,2] - self.frame_data[:,:,0,2]

    def prepframe(self,_size=[5,5], _threshold=51.121):
        # adjust particle positions so that they are continuous along the polymers. This keeps PBC from affecting Rcm
        # calculations

        if self.frame_data is not None:

            for i in range(1,self.frame_data.shape[2]):
                for j in range(2):
                    mask = (self.frame_data[:, :, i,j] - self.frame_data[:, :, i-1,j]) < -_size[j]
                    self.frame_data[mask,i,j] += _threshold

                    mask = (self.frame_data[:, :, i, j] - self.frame_data[:, :, i-1, j]) > _size[j]
                    self.frame_data[mask, i, j] -= _threshold

            # plt.plot(np.diff(self.frame_data[1, :, :, 0], axis=1))
            # plt.show()
            # plt.plot(np.diff(self.frame_data[1, :, :, 1], axis=1))
            # plt.show()
            # pass

    def calc_Rglat(self):
        if self.frame_data is not None:
            monocount = self.frame_data.shape[2]
            Rgs = np.zeros(self.frame_data.shape[0:2])
            Rcms = np.zeros((self.frame_data.shape[0],self.frame_data.shape[1],2))

            plt.plot(np.diff(self.frame_data[1, :, :, 0], axis=1))
            plt.show()
            plt.plot(np.diff(self.frame_data[1, :, :, 1], axis=1))
            plt.show()

            for i in range(monocount):
                Rcms[:,:,:] += self.frame_data[:,:,i,0:2]
            Rcms[:,:,:] /= np.float32(monocount)

            for j in range(monocount):

                arg = self.frame_data[:,:,j,0:2] - Rcms[:,:,:]
                norm = np.linalg.norm(arg, axis=2)
                Rgs[:, :] += norm
                pass
            #normalize
            Rgs[:,:] /= np.float32(monocount)

            plt.plot(Rgs[-1,:])
            plt.show()
            return None
    def parse_simulation_file_stream(self, filepath, expected_groups=800, expected_particles=None, max_frames=None,  frame_break=None):
        def parse_frame(file_iter, frame_idx):
            """Parses a single frame from the file iterator."""
            frame_lines = []
            lines_read = 0
            while lines_read < particles_per_frame:
                try:
                    line = next(file_iter).strip()
                except StopIteration:
                    print(f"[ERROR] Unexpected end of file while reading frame {frame_idx}.")
                    return None

                if not line:
                    continue  # skip empty lines

                parts = line.split()
                if len(parts) != 4:
                    print(f"[SKIP] Frame {frame_idx}: malformed line: {line}")
                    continue

                try:
                    particle_type = int(parts[0])
                    x, y, z = map(float, parts[1:])
                except ValueError:
                    print(f"[SKIP] Frame {frame_idx}: non-integer type or non-numeric coordinates: {line}")
                    continue

                frame_lines.append((particle_type, x, y, z))
                lines_read += 1

            # Grouping particles
            groups = []
            current_group = []

            for idx, (ptype, x, y, z) in enumerate(frame_lines):
                if ptype == 0:
                    if current_group:
                        groups.append(current_group)
                    current_group = []
                current_group.append([x, y, z])

            if current_group:
                groups.append(current_group)

            if len(groups) != expected_groups:
                print(f"[ALERT] Frame {frame_idx}: Expected {expected_groups} groups, found {len(groups)}.")

            if expected_particles is not None:
                for gid, group in enumerate(groups):
                    if len(group) != expected_particles:
                        print(
                            f"[ALERT] Frame {frame_idx}, Group {gid}: Expected {expected_particles} particles, found {len(group)}.")

            return groups

        frame_data = []
        with open(filepath, 'r') as f:
            file_iter = iter(f)

            try:
                first_line = next(file_iter).strip()
                particles_per_frame = int(first_line)
                print(f"[INFO] Particles per frame: {particles_per_frame}")
            except (StopIteration, ValueError):
                raise ValueError("[ERROR] First line must be an integer (number of particles per frame).")

            try:
                header = next(file_iter).strip()
                print(f"[INFO] Header line: \"{header}\"")
            except StopIteration:
                raise ValueError("[ERROR] Missing header line after first line.")

            frame_idx = 0
            while True:
                try:
                    line = next(file_iter).strip()
                except StopIteration:
                    break  # End of file

                if not line:
                    continue

                # Detect start of a new frame
                try:
                    count = int(line)
                    next_line = next(file_iter).strip()
                    if next_line != header:
                        print(f"[WARNING] Frame {frame_idx}: Unexpected header line: {next_line}")
                        continue
                    # Parse the next frame
                    frame = parse_frame(file_iter, frame_idx)
                    if frame:
                        if expected_particles is None:
                            expected_particles = len(frame[0])
                            print(f"[INFO] Auto-detected {expected_particles} particles per group.")

                        frame_data.append(frame)
                        frame_idx += 1
                        print(f"[INFO] Parsed frame {frame_idx}")

                    if max_frames and frame_idx >= max_frames:
                        break
                    if frame_break is not None:
                        if len(frame_data) == frame_break:
                            break
                except ValueError:
                    print(f"[SKIP] Line doesn't start a frame (not an integer): {line}")
                except StopIteration:
                    break

        print(f"\n[SUMMARY] Total frames parsed: {frame_idx}")
        print(f"[SUMMARY] Expected groups per frame: {expected_groups}")
        print(f"[SUMMARY] Expected particles per group: {expected_particles}")

        # Convert to NumPy array if possible
        try:
            data_array = np.array(frame_data, dtype=np.float32)
            print(f"[INFO] Final data array shape: {data_array.shape}")
            self.frame_data = data_array
            return data_array
        except Exception as e:
            print(f"[ERROR] Could not convert frame data to NumPy array: {e}")
            return frame_data  # Return raw list if array conversion fails

if __name__ == "__main__":
    filename = "/home/clayton/Disertation/gap_sims/frames_exp_3_f_Umin-0-175_rad2_den0-3_gap0_len128_NP0.xyz"
    Simulation = Polymer_Sim()
    Simulation.parse_simulation_file_stream(filename, frame_break=100)
    Simulation.calc_heights()
    Simulation.prepframe()
    Simulation.calc_Rglat()
    print("main function")
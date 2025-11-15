
base_dir = "/scratch/chdavis/exp_4/NP_BRUSH/Umin_-0.175/rad_2/den_0.1/gap_0/len_32/NP_1024"

file ="/frames_exp_4_Umin-0-175_rad2_den0-1_gap0_len32_NP1024.xyz"

def read_from_end(filepath, n):
    """
    Generator that yields chunks of N lines at a time,
    starting from the end of the file and moving backward.
    """
    yields = 0

    with open(filepath, "rb") as f:  # open in binary to handle seeking precisely
        f.seek(0, 2)  # move to end of file
        file_size = f.tell()

        buffer = b""
        block_size = 1024*1024
        pos = file_size

        lines = []

        while pos > 0:

            # read next block from the end
            read_size = min(block_size, pos)
            pos -= read_size
            f.seek(pos)
            data = f.read(read_size)
            buffer = data + buffer  # prepend chunk

            # split into lines
            parts = buffer.split(b"\n")

            # keep the first partial line for next iteration
            buffer = parts[0]
            full_lines = parts[1:]

            # process complete lines in reverse order
            for line in reversed(full_lines):
                lines.append(line.decode("utf-8", errors="replace"))
                if len(lines) == n:
                    yield lines
                    lines = []

        # handle leftover buffer at start of file
        if buffer:
            lines.append(buffer.decode("utf-8", errors="replace"))


        if lines:
            yield list(reversed(lines))  # oldest lines first



# Example usage:
if __name__ == "__main__":
    filename = base_dir + file #"example.txt"

    # get last frame from frame file and save it
    frame_lines = 0
    with open(filename, 'r') as fp:
        frame_lines = int(fp.readline()) + 2

    n = 5  # number of lines per chunk
    yields = 0
    for chunk in read_from_end(filename, frame_lines):
        print("---- Chunk ----")
        for line in chunk:
            print(line)
        yields += 1
        if yields > 200:
            break
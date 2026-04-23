import sys
import os
import subprocess
import utils

if __name__ == "__main__":
    # check if enough arguments are provided
    if len(sys.argv) != 3:
        print("usage: python mediaconvert.py <input_directory> <target_format>")
        sys.exit(1)

    input_dir = sys.argv[1]
    target_ext = sys.argv[2]
    
    # normalize extension (ensure it starts with dot)
    if not target_ext.startswith('.'):
        target_ext = f".{target_ext}"

    if not os.path.isdir(input_dir):
        print(f"error: '{input_dir}' is not a valid directory.")
        sys.exit(1)

    # setup output directory and log path
    out_dir = utils.get_output_dir()
    log_file = os.path.join(out_dir, "history.csv")

    files_found = False

    # process each file in the input directory
    for file_path in utils.find_files(input_dir):
        files_found = True
        
        # detect tool (ffmpeg or magick)
        tool = utils.detect_tool(file_path)
        if not tool:
            print(f"skipping '{file_path}': unknown or unsupported media type.")
            continue

        orig_filename = os.path.basename(file_path)
        out_filename = utils.generate_out_name(orig_filename) + target_ext
        out_filepath = os.path.join(out_dir, out_filename)

        # build subprocess command based on the selected tool
        if tool == 'ffmpeg':
            # -y flag forces overwrite without asking
            cmd = ['ffmpeg', '-y', '-i', file_path, out_filepath]
        elif tool == 'magick':
            cmd = ['magick', file_path, out_filepath]

        print(f"converting '{orig_filename}' to '{target_ext}' using {tool}...")

        try:
            # run the external tool, capture output to keep terminal clean
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if process.returncode == 0:
                print(f"success: saved as '{out_filename}'")
                utils.log_history(log_file, file_path, target_ext, out_filepath, tool)
            else:
                print(f"error converting '{orig_filename}'. tool output:")
                print(process.stderr.decode('utf-8', errors='ignore'))
                
        except FileNotFoundError:
            print(f"critical error: tool '{tool}' is not installed or not in system PATH.")
            
    if not files_found:
        print("no files found in the specified directory.")
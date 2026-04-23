import os
import csv
import mimetypes
from datetime import datetime

def get_output_dir():
    # fetch dir from env or use default ./converted/
    target_dir = os.environ.get("CONVERTED_DIR", os.path.join(os.getcwd(), "converted"))
    
    # create dir if not exists
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        
    return target_dir

def find_files(directory):
    # yield all file paths from given dir
    if os.path.exists(directory) and os.path.isdir(directory):
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isfile(full_path):
                yield full_path

def detect_tool(filepath):
    # guess file type based on extension
    mime_type, _ = mimetypes.guess_type(filepath)
    
    if not mime_type:
        return None
        
    # assign tool based on mime type
    if mime_type.startswith('video') or mime_type.startswith('audio'):
        return 'ffmpeg'
    elif mime_type.startswith('image'):
        return 'magick'
        
    return None

def generate_out_name(original_name):
    # format: yyyymmdd-originalname
    date_prefix = datetime.now().strftime("%Y%m%d")
    base_name = os.path.splitext(original_name)[0]
    return f"{date_prefix}-{base_name}"

def log_history(log_path, orig_path, target_ext, out_path, tool):
    # log conversion details to csv
    file_exists = os.path.exists(log_path)
    
    with open(log_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # write header for new file
        if not file_exists:
            writer.writerow(['timestamp', 'original_path', 'target_format', 'output_path', 'tool'])
            
        timestamp = datetime.now().isoformat()
        writer.writerow([timestamp, orig_path, target_ext, out_path, tool])
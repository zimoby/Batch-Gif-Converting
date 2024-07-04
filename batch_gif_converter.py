#!/usr/bin/env python3

import itertools
import os
import subprocess
import logging
from pathlib import Path
import schedule
import time
import argparse
import yaml
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_video_info(input_path: str) -> dict:
    """Get video information using ffprobe."""
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        input_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def convert_video_to_gif(input_path: str, output_path: str, dither_options: list, width: int = None, fps: float = None):
    """
    Convert a video file to GIF format.
    
    Args:
    input_path (str): Path to the input video file.
    output_path (str): Path to save the output GIF.
    dither_options (list): List of dither options to use.
    width (int): Width to scale the output GIF. If None, use original width.
    fps (float): Frames per second for the output GIF. If None, use original FPS.
    """
    file_folder = os.path.dirname(input_path)
    file_name, _ = os.path.splitext(os.path.basename(output_path))
    palette_file = str(Path(file_folder, "palette_temp.png"))

    video_info = get_video_info(input_path)
    original_width = int(video_info['streams'][0]['width'])
    original_fps = eval(video_info['streams'][0]['avg_frame_rate'])

    width = width or original_width
    fps = fps or original_fps

    stats_modes = ["diff"]

    for dither in dither_options:
        min_iter, max_iter = (2, 3) if dither == "bayer" else (1, 2)

        for iter_val, stat in itertools.product(range(min_iter, max_iter + 1), stats_modes):
            dither_output_path = str(Path(file_folder, f"{file_name}_{dither}.gif"))
            
            palette_gen_command = f'ffmpeg -i "{input_path}" -vf "scale={width}:-1:flags=lanczos,palettegen=stats_mode={stat}" -y "{palette_file}"'
            convert_to_gif_command = f'ffmpeg -i "{input_path}" -i "{palette_file}" -filter_complex "fps={fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither={dither}:bayer_scale={iter_val}:diff_mode=rectangle" -y "{dither_output_path}"'

            subprocess.run(palette_gen_command, shell=True, check=True)
            subprocess.run(convert_to_gif_command, shell=True, check=True)

            os.remove(palette_file)
            logging.info(f"Created GIF with {dither} dither: {dither_output_path}")

def is_file_ready(filepath: str, timeout: int = 300, check_interval: int = 5) -> bool:
    """
    Check if a file is ready to be processed.
    
    Args:
    filepath (str): Path to the file.
    timeout (int): Maximum time to wait for the file to be ready (in seconds). Default is 300 seconds.
    check_interval (int): Time between checks (in seconds). Default is 5 seconds.
    
    Returns:
    bool: True if the file is ready, False otherwise.
    """
    start_time = time.time()
    last_size = -1

    while time.time() - start_time < timeout:
        if not os.path.exists(filepath):
            time.sleep(check_interval)
            continue

        current_size = os.path.getsize(filepath)
        
        if current_size == last_size:
            try:
                # Try to open the file in read-write mode
                with open(filepath, 'r+b'):
                    pass
                return True
            except IOError:
                # File is still being written
                pass
        
        last_size = current_size
        time.sleep(check_interval)

    logging.warning(f"Timeout reached for file: {filepath}")
    return False

def process_folder(video_folder_path: str, config: dict):
    """Process all video files in a given folder."""
    if not os.path.exists(video_folder_path):
        os.makedirs(video_folder_path)

    video_files = {f for f in os.listdir(video_folder_path) if f.lower().endswith(('.mp4', '.avi', '.mkv', '.mov'))}
    
    for file in video_files:
        file_path = os.path.join(video_folder_path, file)
        file_name, _ = os.path.splitext(file)
        output_path = str(Path(video_folder_path, f"{file_name}.gif"))
            
        if os.path.isfile(file_path) and is_file_ready(file_path):
            logging.info(f"Processing file {file_path}")
            convert_video_to_gif(
                file_path, 
                output_path, 
                config['dither_options'],
                config.get('width'),
                config.get('fps')
            )
            
            try:
                os.remove(file_path)
                logging.info(f"Deleted original video file: {file_path}")
            except FileNotFoundError:
                logging.error(f"Could not find {file_path} to delete.")

def check_and_convert_videos(root_video_folder_path: str, config: dict):
    """Check and convert videos in the root folder and all subfolders."""
    for dirpath, _, _ in os.walk(root_video_folder_path):
        process_folder(dirpath, config)

def load_config(config_path: str) -> dict:
    """Load configuration from a YAML file."""
    with open(config_path, 'r') as config_file:
        return yaml.safe_load(config_file)

def main():
    parser = argparse.ArgumentParser(description="Batch convert videos to GIFs.")
    parser.add_argument("--config", default="config.yaml", help="Path to the configuration file")
    args = parser.parse_args()

    config = load_config(args.config)
    root_paths = config.get('root_paths', [])
    schedule_interval = config.get('schedule_interval', 2)

    def scheduled_task():
        for root_path in root_paths:
            check_and_convert_videos(root_path, config)

    schedule.every(schedule_interval).minutes.do(scheduled_task)

    logging.info(f"Starting batch conversion. Checking folders every {schedule_interval} minutes.")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
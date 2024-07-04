# Batch GIF Converter

This Python script automates the process of converting video files to GIF format in batch. It supports multiple locations, dither options.

## Features

- Automatic processing of new files in specified directories
- Scheduled execution at specified intervals

## Requirements

- Python 3.6+
- FFmpeg

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/batch-gif-converter.git
   cd batch-gif-converter
   ```

2. Install the required Python packages:
  
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure FFmpeg is installed on your system. If not, you can download it from [FFmpeg's official website](https://ffmpeg.org/download.html).

## Configuration

1) Copy the example configuration file:

```bash
cp config.yaml.example config.yaml
```

Edit config.yaml to suit your needs. The configuration file has the following structure:

```yaml
root_paths:
  - /path/to/video/folder1
  - /path/to/video/folder2
schedule_interval: 2  # in minutes
dither_options:
  - bayer
  - floyd_steinberg
width: 1040  # Optional: output GIF width. If not specified, original video width will be used.
fps: 24  # Optional: output GIF fps. If not specified, original video fps will be used.
```

Adjust the root_paths, schedule_interval, dither_options, width, and fps according to your requirements.

## Usage

Run the script with:

```bash
python batch_gif_converter.py
```

You can specify a custom config file location:

```bash
python batch_gif_converter.py --config /path/to/custom_config.yaml
```

The script will:

1. Monitor the specified directories for new video files.
2. Convert new video files to GIF format using the specified dither options.
3. Create separate GIF files for each dither option, appending the dither type to the filename.
4. Delete the original video file after successful conversion.

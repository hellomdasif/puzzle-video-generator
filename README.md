# Puzzle Video Generator

Create engaging puzzle challenge videos by overlaying animated puzzle pieces from an image onto a background video. The puzzle piece moves around and occasionally aligns perfectly, creating an interactive visual challenge.

## Features

- 🎨 **5 Shape Options**: Circle, Square, Diamond, Hexagon, Oval
- 🎭 **Background Removal**: Automatic background removal using rembg
- 🎬 **3 Movement Styles**: Chaotic, Rotating, Zigzag
- 🎵 **Audio Mixing**: Mix custom audio with background video audio
- ⚙️ **Highly Customizable**: Control size, position, colors, and timing
- 📐 **Smart Positioning**: Auto-centered cuts with configurable top margin

## Dependencies

### Required Software
- **Python 3.7+**
- **FFmpeg** (for video processing)

### Python Packages
Install required packages:
```bash
pip3 install rembg pillow
```

## Installation

1. Clone or download this repository
2. Install Python dependencies:
   ```bash
   pip3 install rembg pillow
   ```
3. Ensure FFmpeg is installed:
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

## Basic Usage

```bash
python3 puzzle_video_generator.py -i image.jpg -b video.mp4 -o output.mp4
```

## Command Line Arguments

### Required Arguments

| Argument | Description |
|----------|-------------|
| `-i, --input-image` | Path to input image (puzzle piece source) |
| `-b, --background-video` | Path to background video (9:16 format recommended) |
| `-o, --output` | Path for output video |

### Video Settings

| Argument | Default | Range | Description |
|----------|---------|-------|-------------|
| `--duration` | 12 | - | Video duration in seconds |
| `--fps` | 30 | 1-120 | Frames per second |

### Piece Configuration

| Argument | Default | Options/Range | Description |
|----------|---------|---------------|-------------|
| `--cut-percentage` | 20 | 1-50 | Size of cut piece as % of image |
| `--cut-shape` | random | circle, square, diamond, hexagon, oval, random | Shape of puzzle piece |
| `--piece-scale` | 1.0 | 0.5-2.0 | Size multiplier for piece |

### Animation Settings

| Argument | Default | Options/Range | Description |
|----------|---------|---------------|-------------|
| `--num-alignments` | random (3-5) | 1-20 | Number of perfect alignments |
| `--movement-style` | chaotic | chaotic, rotating, zigzag, random | Movement pattern |
| `--alignment-hold-time` | 15 | 0-90 | Frames to hold piece at aligned position |

### Visual Settings

| Argument | Default | Options | Description |
|----------|---------|---------|-------------|
| `--hole-color` | red | red, black, blue, green, yellow, purple, orange, pink, cyan, random, or hex (#FF0000) | Color of hole in image |
| `--image-coverage` | 80 | 50-95 | Percentage of video that image should cover |
| `--margin-top` | 10 | 0-90 | Top margin % to avoid cutting from |

### Audio Settings

| Argument | Default | Range | Description |
|----------|---------|-------|-------------|
| `--audio-file` | None | - | Path to custom audio file (optional) |
| `--audio-volume` | 100 | 0-200 | Background video audio volume % |
| `--audio-custom-volume` | 100 | 0-200 | Custom audio file volume % |

## Examples

### Basic Example
```bash
python3 puzzle_video_generator.py \
  -i image.jpg \
  -b video.mp4 \
  -o output.mp4
```

### With Custom Audio
```bash
python3 puzzle_video_generator.py \
  -i photo.png \
  -b background.mp4 \
  -o result.mp4 \
  --cut-percentage 30 \
  --cut-shape circle \
  --hole-color blue \
  --num-alignments 5 \
  --audio-file music.mp3 \
  --audio-volume 50 \
  --audio-custom-volume 100
```

### Advanced Configuration
```bash
python3 puzzle_video_generator.py \
  -i image.jpg \
  -b video.mp4 \
  -o output.mp4 \
  --cut-percentage 25 \
  --cut-shape diamond \
  --piece-scale 1.2 \
  --hole-color "#FF00FF" \
  --num-alignments 4 \
  --movement-style rotating \
  --fps 60 \
  --audio-file audio.mp3 \
  --audio-volume 10 \
  --audio-custom-volume 100 \
  --margin-top 20 \
  --image-coverage 75 \
  --alignment-hold-time 20
```

### Full Control Example
```bash
python3 puzzle_video_generator.py \
  -i '/path/to/image.jpg' \
  -b /path/to/video.mp4 \
  -o output.mp4 \
  --cut-percentage 30 \
  --cut-shape random \
  --hole-color red \
  --movement-style random \
  --piece-scale 1.5 \
  --fps 30 \
  --margin-top 15 \
  --audio-volume 10 \
  --audio-file /path/to/audio.mp3 \
  --audio-custom-volume 100 \
  --alignment-hold-time 15 \
  --image-coverage 95
```

## How It Works

1. **Background Removal**: Uses rembg to remove the background from the input image
2. **Image Scaling**: Scales the image to fit the video based on `--image-coverage` parameter
3. **Piece Extraction**: Cuts a piece from the image based on shape and size parameters
4. **Hole Creation**: Creates a colored hole in the main image where the piece was cut
5. **Movement Generation**: Generates keyframes for piece movement with alignment points
6. **Video Composition**: Overlays the main image and animated piece on the background video
7. **Audio Mixing**: Mixes background video audio with custom audio (if provided)

## Shape Options

### Circle
Perfect circular puzzle piece - classic puzzle shape

### Square
Square/rectangular piece - simple and clear

### Diamond
Rhombus/diamond shaped piece - geometric style

### Hexagon
Octagon-like 6-sided piece - modern look

### Oval
Horizontal ellipse - wider than tall, smooth shape

## Movement Styles

### Chaotic
Linear vertical sweeps with random horizontal positioning

### Rotating
Piece rotates while moving between alignment points

### Zigzag
Diagonal movement alternating between corners

## Tips

1. **Video Format**: Use 9:16 (portrait) videos for best results
2. **Image Quality**: Higher resolution images produce better puzzle pieces
3. **Audio Balance**: Adjust `--audio-volume` and `--audio-custom-volume` to balance sound levels
4. **Alignment Timing**: Use `--alignment-hold-time` to control how long the piece stays aligned
5. **Piece Size**: Combine `--cut-percentage` and `--piece-scale` for precise size control
6. **Top Margin**: Use `--margin-top` to avoid cutting from faces/important areas at the top
7. **Image Coverage**: Adjust `--image-coverage` to control how much of the video the image covers

## Output

- **Format**: MP4 (H.264 video, AAC audio)
- **Resolution**: Same as background video
- **Duration**: Limited to 12 seconds maximum
- **FPS**: Configurable (default 30fps)

## Troubleshooting

### FFmpeg Not Found
```bash
# Install FFmpeg first
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Linux
```

### Background Removal Fails
The script will continue with the original image if rembg fails. To fix:
```bash
pip3 install --upgrade rembg
```

### Audio Issues
- Ensure audio file format is supported (MP3, AAC, WAV)
- Check that background video has audio track
- Adjust volume levels with `--audio-volume` and `--audio-custom-volume`

### Video Quality
- Use higher `--fps` for smoother animation (30-60 recommended)
- Ensure input image is high resolution
- Use appropriate `--cut-percentage` (20-30 recommended)

## Version History

- **v4** (Current): Added 5 working shapes (circle, square, diamond, hexagon, oval)
- **v3**: Simplified cut positioning with margin-top only
- **v2**: Simplified margin system
- **v1**: Initial release

## License

This project is open source and available for personal and commercial use.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

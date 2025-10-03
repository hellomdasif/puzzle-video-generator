# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based puzzle video generator that creates challenge videos by overlaying animated puzzle pieces from a source image onto a background video (9:16 format). The core functionality extracts a piece from an input image and animates it moving around over the background video with occasional perfect alignments.

## Dependencies

### Required
- **FFmpeg**: Required for all image/video processing operations (ffprobe, ffmpeg)
- **Python 3.7+**: Core language
- **rembg**: Background removal library
- **Pillow (PIL)**: Image processing library

### Installation
```bash
pip3 install rembg pillow
```

## Running the Script

Execute with command-line arguments:
```bash
python3 puzzle_video_generator.py -i image.jpg -b video.mp4 -o output.mp4
```

See README.md for full list of options and examples.

## Architecture

### Single-Class Design

The entire application is contained in the `PuzzleVideoGenerator` class, which orchestrates:

1. **Video/Image Analysis** ([puzzle_video_generator.py:110-145](puzzle_video_generator.py#L110-L145))
   - Uses `ffprobe` to get background video dimensions and duration
   - Uses `ffprobe` to get puzzle image dimensions
   - Automatically uses background video duration if not specified

2. **Asset Creation** ([puzzle_video_generator.py:147-176](puzzle_video_generator.py#L147-L176))
   - Extracts cut piece from source image with optional masking (circle/square shapes)
   - Generates temporary PNG file in `temp_frames/` directory
   - No background modification needed (uses video directly)

3. **Motion Planning** ([puzzle_video_generator.py:179-270](puzzle_video_generator.py#L179-L270))
   - Generates random alignment count (4-8) if not specified
   - Generates keyframes for piece movement over background video
   - Calculates alignment frames where piece returns to center position
   - Supports three movement styles: chaotic, smooth, rotating

4. **Video Synthesis** ([puzzle_video_generator.py:291-325](puzzle_video_generator.py#L291-L325))
   - Builds complex FFmpeg filter expressions for interpolated motion
   - Overlays animated puzzle piece on background video
   - Uses FFmpeg overlay filter with dynamic x/y/rotation expressions
   - Creates final MP4 with H.264 encoding
   - Preserves audio from background video if present

### Key Algorithm: Expression-Based Interpolation

The system generates mathematical expressions for FFmpeg's eval system to enable smooth interpolation between keyframes without rendering individual frames. See `_build_interpolation_expr()` ([puzzle_video_generator.py:327-352](puzzle_video_generator.py#L327-L352)) which creates nested conditional expressions like:
```
if(lt(t,t1),v0+((v1-v0)/(t1-t0))*(t-t0), if(lt(t,t2),...))
```

## Configuration Parameters

### Main Parameters
- `cut_percentage`: Size of extracted piece relative to image (1-50, default: 20)
- `num_alignments`: Number of perfect alignments (1-20, default: random 3-5)
- `cut_shape`: 'circle', 'square', 'diamond', 'hexagon', 'oval', or 'random'
- `movement_style`: 'chaotic', 'rotating', 'zigzag', or 'random'
- `piece_scale`: Size multiplier (0.5-2.0, default: 1.0)
- `margin_top`: Top margin % to avoid cutting from (0-90, default: 10)
- `image_coverage`: % of video that image covers (50-95, default: 80)
- `alignment_hold_time`: Frames to hold at alignment (0-90, default: 15)
- `hole_color`: Color of hole ('red', 'blue', hex like '#FF0000', etc.)

### Video Parameters
- `input_image`: Path to source image
- `background_video`: Path to 9:16 background video
- `audio_file`: Optional custom audio file
- `duration`: Video length in seconds (max 12, default: auto from video/audio)
- `fps`: Frames per second (1-120, default: 30)

## Temporary Files

The script creates a `temp_frames/` directory (sibling to output video) containing:
- `no_bg.png`: Image with background removed
- `main_image_hole.png`: Main image with colored hole where piece was cut
- `cut_piece.png`: The extracted puzzle piece with alpha channel and shape mask

This directory is automatically cleaned up after video generation.

## Output Format

Final video maintains the background video's aspect ratio (9:16) and includes:
- Original background video content
- Animated puzzle piece overlay
- Preserved audio from background video (if present)
- H.264 encoding with yuv420p pixel format

## Important Workflow Rules

### Git Push Policy
**CRITICAL**: NEVER push to git automatically. ONLY push when the user explicitly says "push", "push it", "commit and push", or similar approval. Always wait for explicit user approval before running `git push`.

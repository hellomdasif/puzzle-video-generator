# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based puzzle video generator that creates challenge videos by overlaying animated puzzle pieces from a source image onto a background video (9:16 format). The core functionality extracts a piece from an input image and animates it moving around over the background video with occasional perfect alignments at the center position.

## Dependencies

- **FFmpeg**: Required for all image/video processing operations (ffprobe, ffmpeg)
- **Python 3**: Standard library only (subprocess, random, math, os, pathlib)

## Running the Script

Execute directly:
```bash
python3 puzzle_video_generator.py
```

The script uses hardcoded paths in `main()`. To use custom images/videos/paths, either:
1. Modify the constants in `main()` (INPUT_IMAGE, BACKGROUND_VIDEO, OUTPUT_DIR, OUTPUT_VIDEO)
2. Import and use `PuzzleVideoGenerator` class programmatically

If no background video is found, the script automatically creates a sample 9:16 background video with gradient.

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

Main generation parameters (`generate_puzzle_video()` method):
- `cut_percentage`: Size of extracted piece relative to background video (10-30 recommended)
- `num_alignments`: Number of perfect alignment moments (default: None for random 4-8)
- `cut_shape`: 'circle', 'square', or 'random'
- `movement_style`: 'chaotic', 'smooth', or 'rotating'

Video parameters (constructor):
- `input_image`: Path to source image for puzzle piece
- `background_video`: Path to 9:16 background video
- `duration`: Video length in seconds (default: None, uses background video duration)
- `fps`: Frames per second (default: 30)

## Temporary Files

The script creates a `temp_frames/` directory (sibling to output video) containing:
- `cut_piece.png`: The extracted puzzle piece with alpha channel (circular or square mask)

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

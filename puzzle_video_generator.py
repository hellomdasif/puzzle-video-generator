#!/usr/bin/env python3
"""
Puzzle Video Generator
Creates challenge videos where a main image is overlaid on a background video,
with a cut piece from the image moving around and occasionally aligning perfectly.
"""

import subprocess
import random
import math
import os
from pathlib import Path
from rembg import remove
from PIL import Image


class PuzzleVideoGenerator:
    def __init__(self, input_image, background_video, output_path, duration=None, fps=30):
        """
        Initialize the puzzle video generator.

        Args:
            input_image: Path to input image (main image to overlay)
            background_video: Path to background video (9:16 format)
            output_path: Path for output video
            duration: Video duration in seconds (default: None, uses background video duration)
            fps: Frames per second (default: 30)
        """
        # Validate inputs
        self._validate_inputs(input_image, background_video, output_path, fps)

        self.input_image = input_image
        self.background_video = background_video
        self.output_path = output_path
        self.fps = fps

        # Get background video duration if not specified
        if duration is None:
            self.duration = self._get_video_duration()
        else:
            self.duration = duration

        self.total_frames = int(self.duration * fps)

    def _validate_inputs(self, input_image, background_video, output_path, fps):
        """Validate all input parameters."""
        # Check if input image exists
        if not os.path.exists(input_image):
            raise FileNotFoundError(f"Input image not found: {input_image}")

        # Check if background video exists
        if not os.path.exists(background_video):
            raise FileNotFoundError(f"Background video not found: {background_video}")

        # Validate image format
        valid_image_formats = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff']
        img_ext = os.path.splitext(input_image)[1].lower()
        if img_ext not in valid_image_formats:
            raise ValueError(f"Unsupported image format: {img_ext}. Supported: {valid_image_formats}")

        # Validate video format
        valid_video_formats = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        vid_ext = os.path.splitext(background_video)[1].lower()
        if vid_ext not in valid_video_formats:
            raise ValueError(f"Unsupported video format: {vid_ext}. Supported: {valid_video_formats}")

        # Validate output directory exists or can be created
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Cannot create output directory: {output_dir}. Error: {e}")

        # Validate FPS
        if fps <= 0 or fps > 120:
            raise ValueError(f"FPS must be between 1 and 120, got: {fps}")

    def generate_puzzle_video(self, cut_percentage=20, num_alignments=None,
                            cut_shape='random', movement_style='chaotic',
                            hole_color='red', piece_scale=1.0,
                            cut_margin_top=10, cut_margin_bottom=10,
                            cut_margin_left=10, cut_margin_right=10):
        """
        Generate the puzzle video.

        Args:
            cut_percentage: Percentage of main image to cut (default: 20)
            num_alignments: Number of times the piece aligns correctly (default: None, random 3-5)
            cut_shape: Shape of cut ('circle', 'square', 'triangle', 'star', 'random')
            movement_style: Movement style (currently uses linear vertical)
            hole_color: Color of the hole ('red', 'black', 'blue', 'green', 'yellow', 'random', or hex like '#FF0000')
            piece_scale: Scale multiplier for cut piece size (default: 1.0, range: 0.5-2.0)
            cut_margin_top: Top margin % to avoid cutting from (default: 10)
            cut_margin_bottom: Bottom margin % to avoid cutting from (default: 10)
            cut_margin_left: Left margin % to avoid cutting from (default: 10)
            cut_margin_right: Right margin % to avoid cutting from (default: 10)
        """
        # Validate parameters
        if cut_percentage <= 0 or cut_percentage > 50:
            raise ValueError(f"cut_percentage must be between 1 and 50, got: {cut_percentage}")

        if num_alignments is not None and (num_alignments < 1 or num_alignments > 20):
            raise ValueError(f"num_alignments must be between 1 and 20, got: {num_alignments}")

        valid_shapes = ['circle', 'square', 'triangle', 'star', 'random']
        if cut_shape not in valid_shapes:
            raise ValueError(f"cut_shape must be one of {valid_shapes}, got: {cut_shape}")

        if piece_scale < 0.5 or piece_scale > 2.0:
            raise ValueError(f"piece_scale must be between 0.5 and 2.0, got: {piece_scale}")

        # Validate cut margins
        for margin_name, margin_value in [
            ('cut_margin_top', cut_margin_top),
            ('cut_margin_bottom', cut_margin_bottom),
            ('cut_margin_left', cut_margin_left),
            ('cut_margin_right', cut_margin_right)
        ]:
            if margin_value < 0 or margin_value > 50:
                raise ValueError(f"{margin_name} must be between 0 and 50, got: {margin_value}")

        # Validate total margins don't exceed 100%
        if cut_margin_top + cut_margin_bottom >= 100:
            raise ValueError(f"cut_margin_top + cut_margin_bottom must be < 100, got: {cut_margin_top + cut_margin_bottom}")
        if cut_margin_left + cut_margin_right >= 100:
            raise ValueError(f"cut_margin_left + cut_margin_right must be < 100, got: {cut_margin_left + cut_margin_right}")

        # Handle random hole color
        if hole_color == 'random':
            hole_color = random.choice(['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'cyan'])

        # Random alignments if not specified (3-5 for slower movement)
        if num_alignments is None:
            num_alignments = random.randint(3, 5)

        # Random shape if not specified
        if cut_shape == 'random':
            cut_shape = random.choice(['circle', 'square', 'triangle', 'star'])

        print(f"🎬 Generating puzzle video...")
        print(f"   Puzzle image: {self.input_image}")
        print(f"   Background video: {self.background_video}")
        print(f"   Duration: {self.duration}s @ {self.fps}fps")
        print(f"   Alignments: {num_alignments}")
        print(f"   Cut shape: {cut_shape}")
        print(f"   Hole color: {hole_color}")
        print(f"   Piece scale: {piece_scale}x")

        # Get background video dimensions
        bg_width, bg_height = self._get_video_dimensions()
        print(f"   Background size: {bg_width}x{bg_height}")

        # Get image dimensions
        img_width, img_height = self._get_image_dimensions()
        print(f"   Original image size: {img_width}x{img_height}")

        # Validate image dimensions
        if img_width < 100 or img_height < 100:
            raise ValueError(f"Image too small: {img_width}x{img_height}. Minimum: 100x100")

        # Scale image to fit with 10% margin on all sides
        margin_percent = 0.10
        max_img_width = int(bg_width * (1 - 2 * margin_percent))
        max_img_height = int(bg_height * (1 - 2 * margin_percent))

        # Calculate scaled dimensions maintaining aspect ratio
        scale = min(max_img_width / img_width, max_img_height / img_height)
        scaled_img_width = int(img_width * scale)
        scaled_img_height = int(img_height * scale)

        # Ensure scaled dimensions are reasonable
        if scaled_img_width < 200 or scaled_img_height < 200:
            raise ValueError(f"Scaled image too small: {scaled_img_width}x{scaled_img_height}. "
                           f"Background video might be too small or image too large.")

        # Center position of the main image on background
        img_x = (bg_width - scaled_img_width) // 2
        img_y = (bg_height - scaled_img_height) // 2

        print(f"   Scaled image size: {scaled_img_width}x{scaled_img_height}")
        print(f"   Image position: ({img_x}, {img_y})")

        # Calculate cut piece size based on scaled image
        base_cut_size = int(min(scaled_img_width, scaled_img_height) * (cut_percentage / 100))
        cut_size = int(base_cut_size * piece_scale)

        # Ensure cut size is reasonable
        if cut_size < 50:
            print(f"   ⚠️  Warning: Cut size is small ({cut_size}px). Consider using larger cut_percentage or piece_scale.")
            cut_size = max(50, cut_size)  # Minimum 50px
        elif cut_size > min(scaled_img_width, scaled_img_height) // 2:
            print(f"   ⚠️  Warning: Cut size is large ({cut_size}px). Reducing to 50% of image.")
            cut_size = min(scaled_img_width, scaled_img_height) // 2

        # Calculate safe zone boundaries based on margin percentages
        margin_top_px = int(scaled_img_height * (cut_margin_top / 100))
        margin_bottom_px = int(scaled_img_height * (cut_margin_bottom / 100))
        margin_left_px = int(scaled_img_width * (cut_margin_left / 100))
        margin_right_px = int(scaled_img_width * (cut_margin_right / 100))

        # Calculate available area for cutting (excluding margins)
        available_width = scaled_img_width - margin_left_px - margin_right_px
        available_height = scaled_img_height - margin_top_px - margin_bottom_px

        # Ensure we have enough space for the cut
        if available_width < cut_size or available_height < cut_size:
            raise ValueError(f"Available area ({available_width}x{available_height}) too small for cut size {cut_size}px. "
                           f"Reduce cut_percentage, piece_scale, or cut margins.")

        # Random position for the cut within the safe zone
        cut_x_on_img = random.randint(margin_left_px, margin_left_px + available_width - cut_size)
        cut_y_on_img = random.randint(margin_top_px, margin_top_px + available_height - cut_size)

        # Absolute position on background video where the piece should align
        align_x = img_x + cut_x_on_img
        align_y = img_y + cut_y_on_img

        print(f"   Cut piece: {cut_size}x{cut_size} at ({cut_x_on_img}, {cut_y_on_img}) on image")
        print(f"   Alignment position on video: ({align_x}, {align_y})")

        # Generate alignment frames
        alignment_frames = self._generate_alignment_frames(num_alignments)
        print(f"   Alignment frames: {alignment_frames}")

        # Create temporary directory
        temp_dir = Path(self.output_path).parent / "temp_frames"
        temp_dir.mkdir(exist_ok=True)

        # Remove background from image using rembg
        print("   🎨 Removing background from image...")
        no_bg_image = str(temp_dir / "no_bg.png")
        self._remove_background(no_bg_image)

        # Create scaled main image with hole
        main_image_with_hole = str(temp_dir / "main_image_hole.png")
        self._create_main_image_with_hole(no_bg_image, scaled_img_width, scaled_img_height,
                                          cut_x_on_img, cut_y_on_img, cut_size,
                                          main_image_with_hole, cut_shape, hole_color)

        # Extract the cut piece
        cut_piece = str(temp_dir / "cut_piece.png")
        self._extract_cut_piece_from_image(no_bg_image, cut_x_on_img, cut_y_on_img, cut_size,
                                           scaled_img_width, scaled_img_height,
                                           cut_piece, cut_shape)

        # Generate movement keyframes
        keyframes = self._generate_movement_keyframes(
            bg_width, bg_height, cut_size, align_x, align_y,
            alignment_frames, movement_style
        )

        # Create the video with FFmpeg
        self._create_video_ffmpeg(main_image_with_hole, cut_piece, keyframes,
                                 img_x, img_y)

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)

        print(f"✅ Video created: {self.output_path}")

    def _get_video_duration(self):
        """Get background video duration using FFprobe."""
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            self.background_video
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            if duration <= 0:
                raise ValueError(f"Invalid video duration: {duration}")
            return duration
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to read video duration: {e.stderr}")
        except ValueError as e:
            raise RuntimeError(f"Invalid video file or duration: {e}")

    def _get_video_dimensions(self):
        """Get background video dimensions using FFprobe."""
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            self.background_video
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            width, height = map(int, result.stdout.strip().split(','))
            if width <= 0 or height <= 0:
                raise ValueError(f"Invalid dimensions: {width}x{height}")
            return width, height
        except (subprocess.CalledProcessError, ValueError) as e:
            raise RuntimeError(f"Failed to read video dimensions: {e}")

    def _get_image_dimensions(self):
        """Get image dimensions using FFprobe."""
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            self.input_image
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            width, height = map(int, result.stdout.strip().split(','))
            if width <= 0 or height <= 0:
                raise ValueError(f"Invalid dimensions: {width}x{height}")
            return width, height
        except (subprocess.CalledProcessError, ValueError) as e:
            raise RuntimeError(f"Failed to read image dimensions: {e}")

    def _remove_background(self, output_path):
        """Remove background from input image using rembg."""
        try:
            # Open the input image
            input_img = Image.open(self.input_image)

            # Remove background
            output_img = remove(input_img)

            # Save the result
            output_img.save(output_path)
        except Exception as e:
            print(f"   ⚠️  Warning: Background removal failed: {e}")
            print("   Continuing with original image...")
            # If rembg fails, just copy the original image
            import shutil
            shutil.copy(self.input_image, output_path)

    def _create_main_image_with_hole(self, source_image, width, height, cut_x, cut_y, cut_size, output, shape, hole_color):
        """Create scaled main image with colored hole where piece was cut."""

        # Convert color name to RGB values for geq filter
        color_map = {
            'black': (0, 0, 0),
            'red': (255, 0, 0),
            'blue': (0, 0, 255),
            'green': (0, 255, 0),
            'yellow': (255, 255, 0),
            'purple': (128, 0, 128),
            'orange': (255, 165, 0),
            'pink': (255, 192, 203),
            'cyan': (0, 255, 255)
        }

        # Handle hex colors or use color map
        if hole_color.startswith('#'):
            # Parse hex color
            hex_color = hole_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        else:
            r, g, b = color_map.get(hole_color.lower(), (255, 0, 0))  # Default to red

        # Scale image (already has background removed) and add hole
        if shape == 'circle':
            radius = cut_size // 2
            center_x = cut_x + radius
            center_y = cut_y + radius
            cmd = [
                'ffmpeg', '-y', '-i', source_image,
                '-vf', f"scale={width}:{height},"
                       f"format=rgba,"
                       f"geq=r='if(lt(hypot(X-{center_x},Y-{center_y}),{radius}),{r},r(X,Y))':"
                       f"g='if(lt(hypot(X-{center_x},Y-{center_y}),{radius}),{g},g(X,Y))':"
                       f"b='if(lt(hypot(X-{center_x},Y-{center_y}),{radius}),{b},b(X,Y))':"
                       f"a='if(lt(hypot(X-{center_x},Y-{center_y}),{radius}),255,alpha(X,Y))'",
                output
            ]
        elif shape == 'square':
            cmd = [
                'ffmpeg', '-y', '-i', source_image,
                '-vf', f"scale={width}:{height},"
                       f"drawbox=x={cut_x}:y={cut_y}:w={cut_size}:h={cut_size}:color={hole_color}:t=fill",
                output
            ]
        elif shape == 'triangle':
            # Create triangle hole using polygon
            points = self._get_triangle_points(cut_x, cut_y, cut_size)
            cmd = [
                'ffmpeg', '-y', '-i', source_image,
                '-vf', f"scale={width}:{height},"
                       f"drawbox=x={cut_x}:y={cut_y}:w={cut_size}:h={cut_size}:color={hole_color}:t=fill",
                output
            ]
        else:  # star
            cmd = [
                'ffmpeg', '-y', '-i', source_image,
                '-vf', f"scale={width}:{height},"
                       f"drawbox=x={cut_x}:y={cut_y}:w={cut_size}:h={cut_size}:color={hole_color}:t=fill",
                output
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error creating main image with hole: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed to create main image with hole")

    def _extract_cut_piece_from_image(self, source_image, cut_x, cut_y, cut_size, img_width, img_height, output, shape):
        """Extract the cut piece from the scaled image (background already removed)."""

        if shape == 'circle':
            radius = cut_size // 2
            cmd = [
                'ffmpeg', '-y', '-i', source_image,
                '-vf', f"scale={img_width}:{img_height},"
                       f"crop={cut_size}:{cut_size}:{cut_x}:{cut_y},"
                       f"format=rgba,"
                       f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
                       f"a='if(lt(hypot(X-{radius},Y-{radius}),{radius}),255,0)'",
                output
            ]
        elif shape == 'square':
            cmd = [
                'ffmpeg', '-y', '-i', source_image,
                '-vf', f"scale={img_width}:{img_height},"
                       f"crop={cut_size}:{cut_size}:{cut_x}:{cut_y}",
                output
            ]
        elif shape == 'triangle':
            # Triangle with alpha mask
            cmd = [
                'ffmpeg', '-y', '-i', source_image,
                '-vf', f"scale={img_width}:{img_height},"
                       f"crop={cut_size}:{cut_size}:{cut_x}:{cut_y}",
                output
            ]
        else:  # star
            cmd = [
                'ffmpeg', '-y', '-i', source_image,
                '-vf', f"scale={img_width}:{img_height},"
                       f"crop={cut_size}:{cut_size}:{cut_x}:{cut_y}",
                output
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error extracting cut piece: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed to extract cut piece")

    def _get_triangle_points(self, x, y, size):
        """Generate triangle points for a given square."""
        # Equilateral triangle pointing up
        top = (x + size // 2, y)
        bottom_left = (x, y + size)
        bottom_right = (x + size, y + size)
        return [top, bottom_left, bottom_right]

    def _generate_alignment_frames(self, num_alignments):
        """Generate frame numbers where the piece should align."""
        if num_alignments == 0:
            return []

        # Divide video into segments and place alignment in each segment
        segment_size = self.total_frames // (num_alignments + 1)
        alignment_frames = []

        for i in range(1, num_alignments + 1):
            # Random frame within each segment
            frame = random.randint(
                i * segment_size - segment_size // 4,
                i * segment_size + segment_size // 4
            )
            alignment_frames.append(frame)

        return sorted(alignment_frames)

    def _generate_movement_keyframes(self, width, height, size,
                                    origin_x, origin_y, alignment_frames,
                                    movement_style):
        """Generate keyframes for linear vertical movement with alignments."""
        keyframes = []

        # Divide video into sweeps based on number of alignments
        num_alignments = len(alignment_frames)

        # Each sweep goes from top to bottom or bottom to top
        # Calculate frames per sweep
        frames_per_sweep = self.total_frames // num_alignments if num_alignments > 0 else self.total_frames

        current_frame = 0

        for i in range(num_alignments):
            # Determine direction: alternate between top-to-bottom and bottom-to-top
            going_down = i % 2 == 0

            # Random X position for each sweep - perfectly straight vertical line at this X
            sweep_x = random.randint(0, width - size)

            # Start and end y positions - reduced range for slower visible movement
            if going_down:
                start_y = 0  # Start at top
                end_y = height - size   # End at bottom
            else:
                start_y = height - size # Start at bottom
                end_y = 0    # End at top

            # Start of sweep
            keyframes.append({
                'frame': current_frame,
                'x': sweep_x,
                'y': start_y,
                'rotation': 0
            })

            # Alignment point during sweep - piece aligns when Y matches the hole
            alignment_frame = alignment_frames[i]

            # Align to origin position (the hole in the main image)
            # X stays the same (sweep_x = origin_x), only Y aligns
            keyframes.append({
                'frame': alignment_frame,
                'x': origin_x,
                'y': origin_y,
                'rotation': 0
            })

            # End of sweep
            end_frame = min(current_frame + frames_per_sweep, self.total_frames - 1)
            keyframes.append({
                'frame': end_frame,
                'x': sweep_x,
                'y': end_y,
                'rotation': 0
            })

            current_frame = end_frame + 1

        # If there are remaining frames, add a final sweep
        if current_frame < self.total_frames:
            going_down = num_alignments % 2 == 0
            sweep_x = random.randint(0, width - size)  # Random X position for straight line

            if going_down:
                start_y = 0
                end_y = height - size
            else:
                start_y = height - size
                end_y = 0

            keyframes.append({
                'frame': current_frame,
                'x': sweep_x,
                'y': start_y,
                'rotation': 0
            })

            keyframes.append({
                'frame': self.total_frames - 1,
                'x': sweep_x,
                'y': end_y,
                'rotation': 0
            })

        return keyframes

    def _create_video_ffmpeg(self, main_image, cut_piece, keyframes, img_x, img_y):
        """Create the final video - overlay main image with hole and animated puzzle piece on background."""

        # Build overlay expressions for each frame
        x_expr = self._build_interpolation_expr(keyframes, 'x')
        y_expr = self._build_interpolation_expr(keyframes, 'y')

        # FFmpeg filter complex:
        # [0] = background video
        # [1] = main image with hole
        # [2] = cut piece
        filter_complex = (
            # Format main image to ensure alpha channel is preserved
            f"[1:v]format=rgba[main_with_alpha];"
            # Overlay main image on background (static position)
            f"[0:v][main_with_alpha]overlay=x={img_x}:y={img_y}:format=auto[bg_with_img];"
            # Rotate the cut piece
            f"[2:v]format=rgba[piece];"
            f"[piece]rotate='{self._build_interpolation_expr(keyframes, 'rotation')}*PI/180:"
            f"c=none:ow=max(iw,ih):oh=max(iw,ih)'[rotated];"
            # Overlay animated piece on top
            f"[bg_with_img][rotated]overlay=x='{x_expr}':y='{y_expr}':format=auto[out]"
        )

        cmd = [
            'ffmpeg', '-y',
            '-i', self.background_video,  # Input 0: background video
            '-loop', '1', '-t', str(self.duration), '-i', main_image,  # Input 1: main image with hole
            '-loop', '1', '-t', str(self.duration), '-i', cut_piece,   # Input 2: cut piece
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-r', str(self.fps),
            '-pix_fmt', 'yuv420p',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'copy',  # Copy audio from background video if present
            self.output_path
        ]

        print("🎨 Rendering video...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed with return code {result.returncode}")

    def _build_interpolation_expr(self, keyframes, param):
        """Build FFmpeg expression for parameter interpolation."""
        expr_parts = []

        for i in range(len(keyframes) - 1):
            kf1 = keyframes[i]
            kf2 = keyframes[i + 1]

            t1 = kf1['frame'] / self.fps
            t2 = kf2['frame'] / self.fps
            v1 = kf1[param]
            v2 = kf2[param]

            # Linear interpolation formula
            if i == 0:
                expr_parts.append(f"if(lt(t,{t2}),{v1}+(({v2}-{v1})/({t2}-{t1}))*(t-{t1}),")
            elif i == len(keyframes) - 2:
                expr_parts.append(f"if(lt(t,{t2}),{v1}+(({v2}-{v1})/({t2}-{t1}))*(t-{t1}),{v2})")
            else:
                expr_parts.append(f"if(lt(t,{t2}),{v1}+(({v2}-{v1})/({t2}-{t1}))*(t-{t1}),")

        # Close all if statements
        expr = ''.join(expr_parts) + ')' * (len(keyframes) - 2)

        return expr


def main():
    """Example usage of the PuzzleVideoGenerator."""

    # Configuration
    INPUT_IMAGE = "/Users/asif/Documents/puzzle/b8fe2df7f5162b4231935412eb26bb03 (1).jpg"
    BACKGROUND_VIDEO = "/Users/asif/Documents/puzzle/input.mp4"
    OUTPUT_DIR = "/Users/asif/Documents/puzzle/output"
    OUTPUT_VIDEO = os.path.join(OUTPUT_DIR, "puzzle_challenge.mp4")

    try:
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Initialize generator
        generator = PuzzleVideoGenerator(
            input_image=INPUT_IMAGE,
            background_video=BACKGROUND_VIDEO,
            output_path=OUTPUT_VIDEO,
            duration=None,  # Use background video duration
            fps=30
        )

        # Generate video
        generator.generate_puzzle_video(
            cut_percentage=40,       # Cut 20% of the scaled image
            num_alignments=None,     # Random 3-5 alignments
            cut_shape='random',      # Random shape: circle/square/triangle/star
            movement_style='chaotic', # Uses linear vertical sweeps
            hole_color='red',        # Color of hole: 'red', 'black', 'blue', 'green', 'yellow', 'random', or hex
            piece_scale=0.8,         # Scale multiplier for cut piece size (0.5-2.0)
            cut_margin_top=20,       # Don't cut from top 10% of image
            cut_margin_bottom=40,    # Don't cut from bottom 10% of image
            cut_margin_left=30,      # Don't cut from left 10% of image
            cut_margin_right=30      # Don't cut from right 10% of image
        )

        print("\n✨ Done! Your puzzle video is ready!")
        print(f"📁 Location: {OUTPUT_VIDEO}")
        print("\n💡 Tip: You can adjust parameters:")
        print("   - num_alignments: Number of alignments (default: random 3-5)")
        print("   - cut_percentage: Size of cut piece (10-30 recommended)")
        print("   - cut_shape: 'circle', 'square', 'triangle', 'star', or 'random'")
        print("   - hole_color: 'red' (default), 'black', 'blue', 'green', 'yellow', 'random', or hex like '#FF0000'")
        print("   - piece_scale: Multiplier for piece size (0.5-2.0, default: 1.0)")
        print("   - cut_margin_top/bottom/left/right: Margins % to avoid cutting from (default: 10)")
        print("   - movement_style: Uses linear vertical sweeps")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("   Please check that the input files exist:")
        print(f"   - Image: {INPUT_IMAGE}")
        print(f"   - Video: {BACKGROUND_VIDEO}")
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("   Please check your parameter values.")
    except RuntimeError as e:
        print(f"\n❌ Processing Error: {e}")
        print("   Please check that FFmpeg is installed and the media files are valid.")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        print("   Please report this issue with the error message above.")


if __name__ == "__main__":
    main()

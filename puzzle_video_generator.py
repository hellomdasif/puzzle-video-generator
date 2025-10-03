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
import argparse
from pathlib import Path
from rembg import remove
from PIL import Image


class PuzzleVideoGenerator:
    def __init__(self, input_image, background_video, output_path, audio_file=None, duration=None, fps=30):
        """
        Initialize the puzzle video generator.

        Args:
            input_image: Path to input image (main image to overlay)
            background_video: Path to background video (9:16 format)
            output_path: Path for output video
            audio_file: Path to audio file (default: None, uses background video audio)
            duration: Video duration in seconds (default: None, uses audio/background video duration)
            fps: Frames per second (default: 30)
        """
        # Validate inputs
        self._validate_inputs(input_image, background_video, output_path, fps, audio_file)

        self.input_image = input_image
        self.background_video = background_video
        self.output_path = output_path
        self.audio_file = audio_file
        self.fps = fps

        # Get duration: use explicit duration (default 12s from argparse)
        if duration is None:
            if audio_file:
                self.duration = self._get_audio_duration()
            else:
                self.duration = self._get_video_duration()
        else:
            self.duration = duration

        # Hard limit to 12 seconds
        self.duration = min(self.duration, 12)

        # Use ceil to ensure we cover the full duration without gaps
        import math
        self.total_frames = math.ceil(self.duration * fps)

    def _validate_inputs(self, input_image, background_video, output_path, fps, audio_file):
        """Validate all input parameters."""
        # Check if input image exists
        if not os.path.exists(input_image):
            raise FileNotFoundError(f"Input image not found: {input_image}")

        # Check if background video exists
        if not os.path.exists(background_video):
            raise FileNotFoundError(f"Background video not found: {background_video}")

        # Check if audio file exists (if provided)
        if audio_file and not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

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
                            cut_margin_top=10, cut_margin_bottom=45,
                            cut_margin_left=20, cut_margin_right=20,
                            audio_volume=100, audio_custom_volume=100,
                            alignment_hold_time=0.5, image_coverage=80):
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
            cut_margin_bottom: Bottom margin % to avoid cutting from (default: 45)
            cut_margin_left: Left margin % to avoid cutting from (default: 20)
            cut_margin_right: Right margin % to avoid cutting from (default: 20)
            audio_volume: Background video audio volume % (default: 100, range: 0-200)
            audio_custom_volume: Custom audio file volume % (default: 100, range: 0-200)
            alignment_hold_time: Time in seconds to hold piece at aligned position (default: 0.5, range: 0-3)
            image_coverage: Percentage of video that image should cover (default: 80, range: 50-95)
        """
        # Validate parameters
        if cut_percentage <= 0 or cut_percentage > 50:
            raise ValueError(f"cut_percentage must be between 1 and 50, got: {cut_percentage}")

        if num_alignments is not None and (num_alignments < 1 or num_alignments > 20):
            raise ValueError(f"num_alignments must be between 1 and 20, got: {num_alignments}")

        valid_shapes = ['circle', 'square', 'triangle', 'star', 'random']
        if cut_shape not in valid_shapes:
            raise ValueError(f"cut_shape must be one of {valid_shapes}, got: {cut_shape}")

        valid_movement_styles = ['chaotic', 'rotating', 'zigzag', 'random']
        if movement_style not in valid_movement_styles:
            raise ValueError(f"movement_style must be one of {valid_movement_styles}, got: {movement_style}")

        # Random movement style if not specified
        if movement_style == 'random':
            movement_style = random.choice(['chaotic', 'rotating', 'zigzag'])

        if piece_scale < 0.5 or piece_scale > 2.0:
            raise ValueError(f"piece_scale must be between 0.5 and 2.0, got: {piece_scale}")

        if audio_volume < 0 or audio_volume > 200:
            raise ValueError(f"audio_volume must be between 0 and 200, got: {audio_volume}")

        if audio_custom_volume < 0 or audio_custom_volume > 200:
            raise ValueError(f"audio_custom_volume must be between 0 and 200, got: {audio_custom_volume}")

        if alignment_hold_time < 0 or alignment_hold_time > 3:
            raise ValueError(f"alignment_hold_time must be between 0 and 3, got: {alignment_hold_time}")

        if image_coverage < 50 or image_coverage > 95:
            raise ValueError(f"image_coverage must be between 50 and 95, got: {image_coverage}")

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
        print(f"   Movement style: {movement_style}")
        print(f"   Hole color: {hole_color}")
        print(f"   Piece scale: {piece_scale}x")
        print(f"   Image coverage: {image_coverage}%")

        # Get background video dimensions
        bg_width, bg_height = self._get_video_dimensions()
        print(f"   Background size: {bg_width}x{bg_height}")

        # Get image dimensions
        img_width, img_height = self._get_image_dimensions()
        print(f"   Original image size: {img_width}x{img_height}")

        # Validate image dimensions
        if img_width < 100 or img_height < 100:
            raise ValueError(f"Image too small: {img_width}x{img_height}. Minimum: 100x100")

        # Scale image based on image_coverage percentage relative to video width (for 9:16 videos)
        # Calculate target size based on coverage percentage of video width
        coverage_decimal = image_coverage / 100.0
        target_width = int(bg_width * coverage_decimal)

        # Calculate scaled dimensions maintaining aspect ratio
        # Scale based on width to ensure consistent sizing across all images
        scale = target_width / img_width
        scaled_img_width = int(img_width * scale)
        scaled_img_height = int(img_height * scale)

        # Ensure image doesn't exceed video height
        if scaled_img_height > bg_height * 0.95:
            scale = (bg_height * 0.95) / img_height
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
            alignment_frames, movement_style, alignment_hold_time
        )

        # Create the video with FFmpeg
        self._create_video_ffmpeg(main_image_with_hole, cut_piece, keyframes,
                                 img_x, img_y, audio_volume, audio_custom_volume)

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

    def _get_audio_duration(self):
        """Get audio file duration using FFprobe."""
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            self.audio_file
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            if duration <= 0:
                raise ValueError(f"Invalid audio duration: {duration}")
            return duration
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to read audio duration: {e.stderr}")
        except ValueError as e:
            raise RuntimeError(f"Invalid audio file or duration: {e}")

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
                                    movement_style, alignment_hold_time):
        """Generate keyframes based on movement style."""
        if movement_style == 'chaotic':
            return self._generate_chaotic_movement(width, height, size, origin_x, origin_y, alignment_frames, alignment_hold_time)
        elif movement_style == 'rotating':
            return self._generate_rotating_movement(width, height, size, origin_x, origin_y, alignment_frames, alignment_hold_time)
        elif movement_style == 'zigzag':
            return self._generate_zigzag_movement(width, height, size, origin_x, origin_y, alignment_frames, alignment_hold_time)
        else:
            # Default to chaotic
            return self._generate_chaotic_movement(width, height, size, origin_x, origin_y, alignment_frames, alignment_hold_time)

    def _generate_chaotic_movement(self, width, height, size, origin_x, origin_y, alignment_frames, alignment_hold_time):
        """Generate keyframes for linear vertical movement with alignments."""
        keyframes = []
        num_alignments = len(alignment_frames)

        if num_alignments == 0:
            # No alignments - continuous vertical sweeps
            num_sweeps = 3  # At least 3 sweeps for continuous movement
            frames_per_sweep = self.total_frames // num_sweeps

            for i in range(num_sweeps):
                going_down = i % 2 == 0
                sweep_x = random.randint(0, width - size)

                start_frame = i * frames_per_sweep
                end_frame = (i + 1) * frames_per_sweep if i < num_sweeps - 1 else self.total_frames - 1

                if going_down:
                    start_y = 0
                    end_y = height - size
                else:
                    start_y = height - size
                    end_y = 0

                keyframes.append({
                    'frame': start_frame,
                    'x': sweep_x,
                    'y': start_y,
                    'rotation': 0
                })

                keyframes.append({
                    'frame': end_frame,
                    'x': sweep_x,
                    'y': end_y,
                    'rotation': 0
                })

            return keyframes

        # With alignments - ensure continuous movement
        # Calculate frames per segment (between alignments)
        total_segments = num_alignments + 1
        frames_per_segment = self.total_frames // total_segments

        for i in range(num_alignments + 1):
            going_down = i % 2 == 0
            sweep_x = random.randint(0, width - size)

            # Start frame of this segment
            start_frame = i * frames_per_segment

            # End frame of this segment
            if i == num_alignments:
                # Last segment - ensure we have a keyframe at the very end
                # Use both total_frames-1 AND add a bit more to cover full duration
                mid_frame = start_frame + (self.total_frames - 1 - start_frame) // 2
                end_frame = self.total_frames - 1
            else:
                end_frame = (i + 1) * frames_per_segment - 1
                mid_frame = None

            if going_down:
                start_y = 0
                end_y = height - size
            else:
                start_y = height - size
                end_y = 0

            # Start of segment
            keyframes.append({
                'frame': start_frame,
                'x': sweep_x,
                'y': start_y,
                'rotation': 0
            })

            # Alignment (if this segment has one)
            if i < num_alignments:
                alignment_frame = alignment_frames[i]
                # Hold period: piece stays at alignment
                hold_frames = max(int(self.fps * alignment_hold_time), 1)  # At least 1 frame

                # Add approach keyframe 5 frames before alignment to slow down
                approach_frames = 5
                if alignment_frame > approach_frames:
                    keyframes.append({
                        'frame': alignment_frame - approach_frames,
                        'x': origin_x,
                        'y': origin_y,
                        'rotation': 0
                    })

                # Keyframe at alignment start
                keyframes.append({
                    'frame': alignment_frame,
                    'x': origin_x,
                    'y': origin_y,
                    'rotation': 0
                })

                # Keyframe at end of hold period (piece still aligned)
                keyframes.append({
                    'frame': alignment_frame + hold_frames,
                    'x': origin_x,
                    'y': origin_y,
                    'rotation': 0
                })

            # For last segment, add a mid-point keyframe for smoother motion
            if i == num_alignments and mid_frame:
                mid_y = start_y + (end_y - start_y) // 2
                keyframes.append({
                    'frame': mid_frame,
                    'x': sweep_x,
                    'y': mid_y,
                    'rotation': 0
                })

            # End of segment (moving to end position)
            keyframes.append({
                'frame': end_frame,
                'x': sweep_x,
                'y': end_y,
                'rotation': 0
            })

        return keyframes

    def _generate_rotating_movement(self, width, height, size, origin_x, origin_y, alignment_frames, alignment_hold_time):
        """Generate movement with rotation."""
        keyframes = []
        num_alignments = len(alignment_frames)
        frames_per_segment = self.total_frames // (num_alignments + 1) if num_alignments > 0 else self.total_frames
        current_frame = 0
        current_rotation = 0

        for i in range(num_alignments):
            # Random position with rotation
            keyframes.append({
                'frame': current_frame,
                'x': random.randint(0, width - size),
                'y': random.randint(0, height - size),
                'rotation': current_rotation
            })

            # Alignment (no rotation when aligned)
            alignment_frame = alignment_frames[i]
            hold_frames = max(int(self.fps * alignment_hold_time), 1)

            # Add approach keyframe to slow down before alignment
            approach_frames = 5
            if alignment_frame > approach_frames:
                keyframes.append({
                    'frame': alignment_frame - approach_frames,
                    'x': origin_x,
                    'y': origin_y,
                    'rotation': 0
                })

            keyframes.append({
                'frame': alignment_frame,
                'x': origin_x,
                'y': origin_y,
                'rotation': 0
            })

            # Hold at alignment
            keyframes.append({
                'frame': alignment_frame + hold_frames,
                'x': origin_x,
                'y': origin_y,
                'rotation': 0
            })

            # Increase rotation for next segment
            current_rotation += random.randint(90, 270)
            current_frame = min(current_frame + frames_per_segment, self.total_frames - 1)

        # Final position with rotation
        keyframes.append({
            'frame': self.total_frames - 1,
            'x': random.randint(0, width - size),
            'y': random.randint(0, height - size),
            'rotation': current_rotation + random.randint(90, 180)
        })

        return keyframes

    def _generate_zigzag_movement(self, width, height, size, origin_x, origin_y, alignment_frames, alignment_hold_time):
        """Generate zigzag diagonal movement."""
        keyframes = []
        num_alignments = len(alignment_frames)
        frames_per_segment = self.total_frames // (num_alignments + 1) if num_alignments > 0 else self.total_frames
        current_frame = 0

        for i in range(num_alignments):
            # Zigzag pattern - alternate corners
            if i % 4 == 0:
                x, y = 0, 0  # Top-left
            elif i % 4 == 1:
                x, y = width - size, 0  # Top-right
            elif i % 4 == 2:
                x, y = width - size, height - size  # Bottom-right
            else:
                x, y = 0, height - size  # Bottom-left

            keyframes.append({
                'frame': current_frame,
                'x': x,
                'y': y,
                'rotation': 0
            })

            # Alignment
            alignment_frame = alignment_frames[i]
            hold_frames = max(int(self.fps * alignment_hold_time), 1)

            # Add approach keyframe to slow down before alignment
            approach_frames = 5
            if alignment_frame > approach_frames:
                keyframes.append({
                    'frame': alignment_frame - approach_frames,
                    'x': origin_x,
                    'y': origin_y,
                    'rotation': 0
                })

            keyframes.append({
                'frame': alignment_frame,
                'x': origin_x,
                'y': origin_y,
                'rotation': 0
            })

            # Hold at alignment
            keyframes.append({
                'frame': alignment_frame + hold_frames,
                'x': origin_x,
                'y': origin_y,
                'rotation': 0
            })

            current_frame = min(current_frame + frames_per_segment, self.total_frames - 1)

        # Final corner
        final_corner = num_alignments % 4
        if final_corner == 0:
            x, y = 0, 0
        elif final_corner == 1:
            x, y = width - size, 0
        elif final_corner == 2:
            x, y = width - size, height - size
        else:
            x, y = 0, height - size

        keyframes.append({
            'frame': self.total_frames - 1,
            'x': x,
            'y': y,
            'rotation': 0
        })

        return keyframes

    def _create_video_ffmpeg(self, main_image, cut_piece, keyframes, img_x, img_y, audio_volume, audio_custom_volume):
        """Create the final video - overlay main image with hole and animated puzzle piece on background."""

        # Build overlay expressions for each frame
        x_expr = self._build_interpolation_expr(keyframes, 'x')
        y_expr = self._build_interpolation_expr(keyframes, 'y')

        # Calculate volume multipliers (percentage to decimal)
        bg_volume_multiplier = audio_volume / 100.0
        custom_volume_multiplier = audio_custom_volume / 100.0

        if self.audio_file:
            # If custom audio file is provided, mix it with background video audio
            # FFmpeg filter complex:
            # [0] = background video
            # [1] = main image with hole
            # [2] = cut piece
            # [3] = custom audio file
            filter_complex = (
                # Trim background video to exact duration
                f"[0:v]trim=duration={self.duration},setpts=PTS-STARTPTS[bg_trimmed];"
                # Format main image to ensure alpha channel is preserved
                f"[1:v]format=rgba[main_with_alpha];"
                # Overlay main image on background (static position)
                f"[bg_trimmed][main_with_alpha]overlay=x={img_x}:y={img_y}:format=auto[bg_with_img];"
                # Rotate the cut piece
                f"[2:v]format=rgba[piece];"
                f"[piece]rotate='{self._build_interpolation_expr(keyframes, 'rotation')}*PI/180:"
                f"c=none:ow=max(iw,ih):oh=max(iw,ih)'[rotated];"
                # Overlay animated piece on top
                f"[bg_with_img][rotated]overlay=x='{x_expr}':y='{y_expr}':format=auto[out];"
                # Trim and apply volume to background video audio
                f"[0:a]atrim=duration={self.duration},asetpts=PTS-STARTPTS,volume={bg_volume_multiplier},apad=whole_dur={self.duration}[bg_audio];"
                # Trim and apply volume to custom audio file
                f"[3:a]atrim=duration={self.duration},asetpts=PTS-STARTPTS,volume={custom_volume_multiplier},apad=whole_dur={self.duration}[custom_audio];"
                # Mix both audio sources - use longest duration to prevent cutoff
                f"[bg_audio][custom_audio]amix=inputs=2:duration=longest:dropout_transition=0,atrim=duration={self.duration}[aout]"
            )

            cmd = [
                'ffmpeg', '-y',
                '-t', str(self.duration), '-i', self.background_video,  # Input 0: background video (trimmed)
                '-loop', '1', '-t', str(self.duration), '-i', main_image,  # Input 1: main image with hole
                '-loop', '1', '-t', str(self.duration), '-i', cut_piece,   # Input 2: cut piece
                '-t', str(self.duration), '-i', self.audio_file,  # Input 3: custom audio file (trimmed)
                '-filter_complex', filter_complex,
                '-map', '[out]',  # Map video output
                '-map', '[aout]',  # Map mixed audio output
                '-r', str(self.fps),
                '-t', str(self.duration),  # Force output duration
                '-pix_fmt', 'yuv420p',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-c:a', 'aac',  # Encode audio to AAC
                '-b:a', '192k',  # Audio bitrate
                self.output_path
            ]
        else:
            # No custom audio file, use only background video audio
            # FFmpeg filter complex:
            # [0] = background video
            # [1] = main image with hole
            # [2] = cut piece
            filter_complex = (
                # Trim background video to exact duration
                f"[0:v]trim=duration={self.duration},setpts=PTS-STARTPTS[bg_trimmed];"
                # Format main image to ensure alpha channel is preserved
                f"[1:v]format=rgba[main_with_alpha];"
                # Overlay main image on background (static position)
                f"[bg_trimmed][main_with_alpha]overlay=x={img_x}:y={img_y}:format=auto[bg_with_img];"
                # Rotate the cut piece
                f"[2:v]format=rgba[piece];"
                f"[piece]rotate='{self._build_interpolation_expr(keyframes, 'rotation')}*PI/180:"
                f"c=none:ow=max(iw,ih):oh=max(iw,ih)'[rotated];"
                # Overlay animated piece on top
                f"[bg_with_img][rotated]overlay=x='{x_expr}':y='{y_expr}':format=auto[out]"
            )

            cmd = [
                'ffmpeg', '-y',
                '-t', str(self.duration), '-i', self.background_video,  # Input 0: background video (trimmed)
                '-loop', '1', '-t', str(self.duration), '-i', main_image,  # Input 1: main image with hole
                '-loop', '1', '-t', str(self.duration), '-i', cut_piece,   # Input 2: cut piece
                '-filter_complex', filter_complex,
                '-map', '[out]',
                '-map', '0:a?',  # Map audio from background video if present (0:a? means optional)
                '-r', str(self.fps),
                '-t', str(self.duration),  # Force output duration
                '-pix_fmt', 'yuv420p',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-af', f'atrim=duration={self.duration},asetpts=PTS-STARTPTS,volume={bg_volume_multiplier},apad=whole_dur={self.duration}',  # Trim, apply volume, and pad
                '-c:a', 'aac',  # Encode audio to AAC
                '-b:a', '192k',  # Audio bitrate
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
                # For the last segment, continue interpolation beyond t2 to fill remaining time
                # This ensures movement continues until the very end of the video
                expr_parts.append(f"{v1}+(({v2}-{v1})/({t2}-{t1}))*(t-{t1})")
            else:
                expr_parts.append(f"if(lt(t,{t2}),{v1}+(({v2}-{v1})/({t2}-{t1}))*(t-{t1}),")

        # Close all if statements
        expr = ''.join(expr_parts) + ')' * (len(keyframes) - 2)

        return expr


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Puzzle Video Generator - Create challenge videos with animated puzzle pieces',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Minimal usage with defaults
  python3 puzzle_video_generator.py -i image.jpg -b video.mp4 -o output.mp4

  # Custom settings with audio file
  python3 puzzle_video_generator.py -i photo.png -b bg.mp4 -o result.mp4 \\
    --cut-percentage 30 --cut-shape circle --hole-color blue --num-alignments 5 \\
    --audio-file music.mp3 --audio-volume 50 --audio-custom-volume 100

  # Advanced with all options
  python3 puzzle_video_generator.py -i image.jpg -b video.mp4 -o output.mp4 \\
    --cut-percentage 25 --cut-shape star --piece-scale 1.2 \\
    --hole-color "#FF00FF" --num-alignments 4 --movement-style rotating \\
    --fps 60 --audio-file audio.mp3 --audio-volume 10 --audio-custom-volume 100 \\
    --margin-top 15 --margin-bottom 45 --margin-left 20 --margin-right 20
        """
    )

    # Required arguments
    required = parser.add_argument_group('required arguments')
    required.add_argument('-i', '--input-image', required=True,
                          help='Path to input image (puzzle piece source)')
    required.add_argument('-b', '--background-video', required=True,
                          help='Path to background video (9:16 format recommended)')
    required.add_argument('-o', '--output', required=True,
                          help='Path for output video')

    # Video settings
    video_group = parser.add_argument_group('video settings')
    video_group.add_argument('--duration', type=float, default=12,
                             help='Video duration in seconds (default: 12)')
    video_group.add_argument('--fps', type=int, default=30,
                             help='Frames per second (default: 30, range: 1-120)')

    # Piece configuration
    piece_group = parser.add_argument_group('piece configuration')
    piece_group.add_argument('--cut-percentage', type=int, default=20,
                             help='Size of cut piece as %% of image (default: 20, range: 1-50)')
    piece_group.add_argument('--cut-shape', type=str, default='random',
                             choices=['circle', 'square', 'triangle', 'star', 'random'],
                             help='Shape of puzzle piece (default: random)')
    piece_group.add_argument('--piece-scale', type=float, default=1.0,
                             help='Size multiplier for piece (default: 1.0, range: 0.5-2.0)')

    # Animation settings
    anim_group = parser.add_argument_group('animation settings')
    anim_group.add_argument('--num-alignments', type=int, default=None,
                            help='Number of perfect alignments (default: random 3-5, range: 1-20)')
    anim_group.add_argument('--movement-style', type=str, default='chaotic',
                            choices=['chaotic', 'rotating', 'zigzag', 'random'],
                            help='Movement pattern (default: chaotic)')
    anim_group.add_argument('--alignment-hold-time', type=float, default=0.5,
                            help='Time in seconds to hold piece at aligned position (default: 0.5, range: 0-3)')

    # Visual settings
    visual_group = parser.add_argument_group('visual settings')
    visual_group.add_argument('--hole-color', type=str, default='red',
                              help='Color of hole (default: red, options: red/black/blue/green/yellow/purple/orange/pink/cyan/random or hex like #FF0000)')
    visual_group.add_argument('--image-coverage', type=int, default=80,
                              help='Percentage of video that image should cover (default: 80, range: 50-95)')

    # Audio settings
    audio_group = parser.add_argument_group('audio settings')
    audio_group.add_argument('--audio-file', type=str, default=None,
                             help='Path to custom audio file (optional, will be mixed with background video audio)')
    audio_group.add_argument('--audio-volume', type=int, default=100,
                             help='Background video audio volume %% (default: 100, range: 0-200)')
    audio_group.add_argument('--audio-custom-volume', type=int, default=100,
                             help='Custom audio file volume %% (default: 100, range: 0-200)')

    # Cut margins
    margin_group = parser.add_argument_group('cut margins (percentage of image to avoid)')
    margin_group.add_argument('--margin-top', type=int, default=10,
                              help='Top margin %% (default: 10, range: 0-50)')
    margin_group.add_argument('--margin-bottom', type=int, default=45,
                              help='Bottom margin %% (default: 45, range: 0-50)')
    margin_group.add_argument('--margin-left', type=int, default=20,
                              help='Left margin %% (default: 20, range: 0-50)')
    margin_group.add_argument('--margin-right', type=int, default=20,
                              help='Right margin %% (default: 20, range: 0-50)')

    return parser.parse_args()


def main():
    """Main entry point with argument parsing."""
    args = parse_arguments()

    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Initialize generator
        generator = PuzzleVideoGenerator(
            input_image=args.input_image,
            background_video=args.background_video,
            output_path=args.output,
            audio_file=args.audio_file,
            duration=args.duration,
            fps=args.fps
        )

        # Generate video
        generator.generate_puzzle_video(
            cut_percentage=args.cut_percentage,
            num_alignments=args.num_alignments,
            cut_shape=args.cut_shape,
            movement_style=args.movement_style,
            hole_color=args.hole_color,
            piece_scale=args.piece_scale,
            cut_margin_top=args.margin_top,
            cut_margin_bottom=args.margin_bottom,
            cut_margin_left=args.margin_left,
            cut_margin_right=args.margin_right,
            audio_volume=args.audio_volume,
            audio_custom_volume=args.audio_custom_volume,
            alignment_hold_time=args.alignment_hold_time,
            image_coverage=args.image_coverage
        )

        print("\n✨ Done! Your puzzle video is ready!")
        print(f"📁 Location: {args.output}")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("   Please check that the input files exist.")
        return 1
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("   Please check your parameter values.")
        return 1
    except RuntimeError as e:
        print(f"\n❌ Processing Error: {e}")
        print("   Please check that FFmpeg is installed and the media files are valid.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        print("   Please report this issue with the error message above.")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

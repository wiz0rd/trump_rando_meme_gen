import os
import sys
import random
import pyperclip
import traceback
from tkinter import *
from tkinter import messagebox, colorchooser, ttk, filedialog, simpledialog
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
import io
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Print
from asciimatics.renderers import ColourImageFile, FigletText, Rainbow, SpeechBubble, StaticRenderer
from asciimatics.exceptions import ResizeScreenError
from PIL import ImageTk
import numpy as np
import pyfiglet
import time
import shutil
import threading

# Version number
VERSION = "2.0 ULTRA"

# Directories and files
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(SCRIPT_DIR, 'trump_pics')
BW_IMAGES_DIR = os.path.join(SCRIPT_DIR, 'trump_pics_bw')  # B&W images
ASCII_DIR = os.path.join(SCRIPT_DIR, 'trump_pics_ascii')  # ASCII art
GEN_IMAGES_DIR = os.path.join(SCRIPT_DIR, 'genImages')
PHRASES_FILE = os.path.join(SCRIPT_DIR, 'phrases.txt')
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.txt')

# Ensure directories exist
os.makedirs(GEN_IMAGES_DIR, exist_ok=True)
os.makedirs(BW_IMAGES_DIR, exist_ok=True)
os.makedirs(ASCII_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)  # Ensure main images directory exists too

# Load images and phrases
try:
    color_images = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.jpg', '.png'))]
except:
    color_images = []

# Initial empty lists
bw_images = []
ascii_images = []

# Load phrases
try:
    with open(PHRASES_FILE, 'r') as f:
        phrases = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    # Create default phrases file if it doesn't exist
    default_phrases = [
        "Make Memes Great Again",
        "Tremendous Memes, Believe Me",
        "You're Fired!",
        "We're Going to Win, Win, Win!",
        "Nobody Makes Better Memes Than Me",
        "I Have The Best Words"
    ]
    with open(PHRASES_FILE, 'w') as f:
        for phrase in default_phrases:
            f.write(phrase + '\n')
    phrases = default_phrases

# Available Figlet fonts that are more legible
FIGLET_FONTS = ['big', 'slant', 'standard', 'banner', 'doom', 'epic', 'larry3d', 'small', 
                'digital', 'ivrit', 'bubble', 'mini', 'script', 'shadow', 'smscript', 'starwars']

# Text color options
TEXT_COLORS = [
    "rainbow",
    "red",
    "blue",
    "green",
    "yellow",
    "magenta",
    "cyan",
    "white",
    "usa" # Custom red-white-blue alternating
]

# ASCII character sets - from high contrast to artistic
ASCII_SETS = {
    "High Contrast": "@%#*+=-:. ",
    "Blocks": "█▓▒░ ",
    "Classic": ".:-=+*#%@",
    "Detailed": '$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,"^`\'. ',
    "Minimal": "@#. "
}

# Default ASCII set
CURRENT_ASCII_SET = "High Contrast"

# ASCII art width options
ASCII_WIDTHS = [40, 60, 80, 100, 120, 160, 200]
CURRENT_ASCII_WIDTH = 120

# Global variables
meme_generated = False
current_meme = None
current_meme_image = None
current_ascii_art = None
current_display_mode = "normal"  # Can be "normal", "bw", or "ascii"
is_generating = False  # Flag to prevent multiple generation requests

# User settings with defaults
settings = {
    "ascii_set": CURRENT_ASCII_SET,
    "ascii_width": CURRENT_ASCII_WIDTH,
    "default_mode": "random",  # can be "normal", "bw", "ascii", or "random"
    "auto_copy": True,
    "show_splash": True,
    "theme": "dark"  # can be "dark" or "light"
}

def load_settings():
    """Load user settings from config file"""
    global settings, CURRENT_ASCII_SET, CURRENT_ASCII_WIDTH
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if key in settings:
                            # Convert to appropriate type
                            if value.lower() == 'true':
                                settings[key] = True
                            elif value.lower() == 'false':
                                settings[key] = False
                            elif key == 'ascii_width' and value.isdigit():
                                settings[key] = int(value)
                            else:
                                settings[key] = value
            
            # Update current values
            CURRENT_ASCII_SET = settings["ascii_set"]
            CURRENT_ASCII_WIDTH = settings["ascii_width"]
            
    except Exception as e:
        print(f"Error loading settings: {str(e)}")

def save_settings():
    """Save user settings to config file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            for key, value in settings.items():
                f.write(f"{key}={value}\n")
    except Exception as e:
        print(f"Error saving settings: {str(e)}")

def create_bw_versions():
    """Create B&W versions of color images if they don't exist already"""
    global bw_images
    
    # First check for existing B&W images
    bw_images = [f for f in os.listdir(BW_IMAGES_DIR) if f.lower().endswith(('.jpg', '.png'))]
    
    if not bw_images and color_images:
        print("Creating black and white versions of images...")
        for img_file in color_images:
            try:
                img_path = os.path.join(IMAGES_DIR, img_file)
                img = Image.open(img_path).convert('L')  # Convert to grayscale
                # Enhance contrast
                img = ImageOps.autocontrast(img, cutoff=2)
                # Apply slight sharpening for better definition
                img = ImageEnhance.Sharpness(img).enhance(1.5)
                
                bw_path = os.path.join(BW_IMAGES_DIR, f"bw_{img_file}")
                img.save(bw_path)
                print(f"Created B&W version: {bw_path}")
            except Exception as e:
                print(f"Error creating B&W version of {img_file}: {str(e)}")
        
        # Update the bw_images list after creating them
        bw_images = [f for f in os.listdir(BW_IMAGES_DIR) if f.lower().endswith(('.jpg', '.png'))]

def image_to_ascii(image_path, width=CURRENT_ASCII_WIDTH, char_set=None):
    """Convert an image to ASCII art with dramatically improved quality"""
    if char_set is None:
        char_set = ASCII_SETS[CURRENT_ASCII_SET]
    
    try:
        # Open image and convert to grayscale
        img = Image.open(image_path).convert('L')
        
        # Resize image while maintaining aspect ratio
        width_original, height_original = img.size
        aspect_ratio = height_original / width_original
        # Adjust for terminal character aspect ratio (characters are taller than wide)
        height = int(width * aspect_ratio * 0.43)
        img = img.resize((width, height))
        
        # Enhance the image for better ASCII conversion
        img = ImageOps.autocontrast(img, cutoff=2)
        img = ImageEnhance.Sharpness(img).enhance(1.5)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        
        # Convert pixels to ASCII characters
        pixels = list(img.getdata())
        ascii_str = ''
        for i, pixel in enumerate(pixels):
            # Map pixel value (0-255) to ASCII character
            index = (pixel * (len(char_set) - 1)) // 255
            ascii_str += char_set[int(index)]
            if (i + 1) % width == 0:
                ascii_str += '\n'
        
        return ascii_str
    except Exception as e:
        print(f"Error creating ASCII art: {str(e)}")
        return f"Error: {str(e)}"

def create_ascii_versions():
    """Create ASCII art versions of images with improved quality"""
    global ascii_images
    
    # First check for existing ASCII images
    ascii_images = [f for f in os.listdir(ASCII_DIR) if f.lower().endswith('.txt')]
    
    if not ascii_images and color_images:
        print("Creating improved ASCII art versions of images...")
        for img_file in color_images:
            try:
                img_path = os.path.join(IMAGES_DIR, img_file)
                # Use current width and character set
                ascii_art = image_to_ascii(img_path, width=CURRENT_ASCII_WIDTH, 
                                          char_set=ASCII_SETS[CURRENT_ASCII_SET])
                
                # Save ASCII art to file
                base_name = os.path.splitext(img_file)[0]
                ascii_path = os.path.join(ASCII_DIR, f"{base_name}_ascii.txt")
                
                with open(ascii_path, 'w') as f:
                    f.write(ascii_art)
                
                print(f"Created ASCII version: {ascii_path}")
            except Exception as e:
                print(f"Error creating ASCII version of {img_file}: {str(e)}")
        
        # Update the ascii_images list after creating them
        ascii_images = [f for f in os.listdir(ASCII_DIR) if f.lower().endswith('.txt')]

def get_font_height(font, text):
    """Get the height of text using a font in a PIL-version-independent way"""
    try:
        # Try the new method first (for newer PIL versions)
        bbox = font.getbbox(text)
        return bbox[3] - bbox[1]
    except AttributeError:
        try:
            # Fall back to older method
            return font.getsize(text)[1]
        except AttributeError:
            # Last resort approximation
            return font.size + 4  # Approximate line height

def generate_meme(screen):
    global meme_generated, current_meme, current_meme_image, current_ascii_art, current_display_mode, is_generating
    
    # Check if generation is already in progress
    if is_generating:
        return
    
    is_generating = True
    meme_generated = True
    
    try:
        # Decide display mode based on settings
        if settings["default_mode"] == "random":
            display_mode = random.choice(["normal", "bw", "ascii"])
        else:
            display_mode = settings["default_mode"]
        
        current_display_mode = display_mode
        
        # Randomly select text style
        text_color = random.choice(TEXT_COLORS)
        font_style = random.choice(FIGLET_FONTS)
        phrase = random.choice(phrases)
        
        # Select the image based on display mode
        if display_mode == "bw" and bw_images:
            image = random.choice(bw_images)
            image_dir = BW_IMAGES_DIR
            image_type = "bw"
        elif display_mode == "ascii" and ascii_images:
            ascii_file = random.choice(ascii_images)
            with open(os.path.join(ASCII_DIR, ascii_file), 'r') as f:
                current_ascii_art = f.read()
            image_type = "ascii"
            image = ascii_file  # Store filename for reference
        else:
            image = random.choice(color_images)
            image_dir = IMAGES_DIR
            image_type = "color"
        
        # Store current meme info
        current_meme = {
            "image": image,
            "phrase": phrase,
            "font": font_style,
            "display_mode": display_mode,
            "text_color": text_color
        }
        
        # Calculate screen dimensions
        max_height = screen.height - 14  # Leave more space for text
        
        # Create display effects based on mode
        effects = []
        
        if display_mode == "ascii":
            # ASCII art display
            lines = current_ascii_art.split('\n')
            for i, line in enumerate(lines):
                if i < max_height:  # Prevent going off screen
                    effects.append(
                        Print(screen, 
                              StaticRenderer([line]), 
                              i)  # Use actual line position
                    )
        else:
            # Image display (color or B&W)
            image_path = os.path.join(image_dir, image)
            effects.append(
                Print(screen,
                      ColourImageFile(screen, image_path, height=max_height, 
                                      uni=screen.unicode_aware, dither=False),
                      0,
                      speed=1)
            )
        
        # Add text with appropriate renderer
        if text_color == "rainbow":
            text_renderer = Rainbow(screen, FigletText(phrase, font=font_style))
            effects.append(
                Print(screen,
                     text_renderer,
                     screen.height - 12,
                     speed=1,
                     start_frame=20)
            )
        elif text_color == "usa":
            # For USA colors, we'll use the built-in capabilities
            text_renderer = FigletText(phrase, font=font_style)
            effects.append(
                Print(screen,
                     text_renderer,
                     screen.height - 12,
                     colour=screen.COLOUR_RED,
                     speed=1,
                     start_frame=20)
            )
        else:
            # Use one of the basic colors - map to asciimatics color constants
            color_map = {
                "red": screen.COLOUR_RED,
                "green": screen.COLOUR_GREEN,
                "blue": screen.COLOUR_BLUE,
                "yellow": screen.COLOUR_YELLOW,
                "magenta": screen.COLOUR_MAGENTA,
                "cyan": screen.COLOUR_CYAN,
                "white": screen.COLOUR_WHITE
            }
            
            asciimatics_color = color_map.get(text_color, screen.COLOUR_WHITE)
            text_renderer = FigletText(phrase, font=font_style)
            
            effects.append(
                Print(screen,
                     text_renderer,
                     screen.height - 12,
                     colour=asciimatics_color,
                     speed=1,
                     start_frame=20)
            )
        
        # Create the PIL image for saving/clipboard
        if display_mode == "ascii":
            create_pil_ascii_meme(current_ascii_art, phrase, font_style, text_color)
        else:
            image_path = os.path.join(image_dir, image)
            create_pil_meme(image_path, phrase, font_style, text_color)
        
        # Auto-copy to clipboard if enabled
        if settings["auto_copy"]:
            copy_to_clipboard()
        
        # Play the scene
        scene = Scene(effects, -1)
        screen.play([scene], stop_on_resize=True, repeat=False)
        
    except Exception as e:
        print(f"Error generating meme: {str(e)}")
        traceback.print_exc()
    finally:
        is_generating = False

def create_pil_ascii_meme(ascii_art, phrase, font_name, text_color):
    """Create a PIL Image of ASCII art meme with improved quality"""
    global current_meme_image
    
    # Calculate size based on ASCII content
    lines = ascii_art.split('\n')
    width = max(len(line) for line in lines) * 10  # Wider spacing for better readability
    height = len(lines) * 18 + 200  # Taller spacing + room for text
    
    # Create a blank image with black background
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Try to use a monospace font for ASCII art
    try:
        ascii_font = ImageFont.truetype("Courier New", 14)
    except:
        try:
            ascii_font = ImageFont.truetype("DejaVuSansMono", 14)
        except:
            ascii_font = ImageFont.load_default()
    
    # Draw ASCII art with improved spacing
    y_offset = 10
    for line in lines:
        draw.text((10, y_offset), line, fill="#FFFFFF", font=ascii_font)
        y_offset += 16
    
    # Draw the phrase text
    try:
        # Use Impact font for the phrase (classic meme font)
        text_font = ImageFont.truetype("Impact", 40)
    except:
        try:
            # Alternative fonts
            text_font = ImageFont.truetype("Arial Bold", 40)
        except:
            text_font = ImageFont.load_default()
    
    # Calculate text wrapping
    words = phrase.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        text_width = draw.textlength(test_line, font=text_font)
        
        if text_width > width - 20:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    text = '\n'.join(lines)
    text_y = y_offset + 30
    
    # Convert text color to RGB
    color_map = {
        "rainbow": None,
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "magenta": (255, 0, 255),
        "cyan": (0, 255, 255),
        "white": (255, 255, 255),
        "usa": None
    }
    
    # Handle special color modes
    if text_color == "rainbow":
        # Draw rainbow text (simplified)
        rainbow_colors = [(255,0,0), (255,127,0), (255,255,0), 
                         (0,255,0), (0,0,255), (75,0,130), (148,0,211)]
        char_x = 10
        for i, line in enumerate(lines):
            for j, char in enumerate(line):
                color_idx = (i + j) % len(rainbow_colors)
                r, g, b = rainbow_colors[color_idx]
                hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                # Add black outline for better readability
                for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
                    draw.text((char_x + offset[0], text_y + i*40 + offset[1]), 
                              char, fill="#000000", font=text_font)
                draw.text((char_x, text_y + i*40), char, fill=hex_color, font=text_font)
                char_x += draw.textlength(char, font=text_font)
            char_x = 10
    elif text_color == "usa":
        # Draw USA color text
        usa_colors = [(255,0,0), (255,255,255), (0,0,255)]
        char_x = 10
        for i, line in enumerate(lines):
            for j, char in enumerate(line):
                color_idx = j % 3
                r, g, b = usa_colors[color_idx]
                hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                # Add black outline for better readability
                for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
                    draw.text((char_x + offset[0], text_y + i*40 + offset[1]), 
                              char, fill="#000000", font=text_font)
                draw.text((char_x, text_y + i*40), char, fill=hex_color, font=text_font)
                char_x += draw.textlength(char, font=text_font)
            char_x = 10
    else:
        # Use a single color
        color = color_map.get(text_color, (255, 255, 255))
        
        # Classic meme text style - white with black outline
        for i, line in enumerate(lines):
            # Calculate width to center the text
            line_width = draw.textlength(line, font=text_font)
            x_position = (width - line_width) // 2
            
            # Draw black outline (thicker for better visibility)
            for offset_x in range(-3, 4):
                for offset_y in range(-3, 4):
                    if abs(offset_x) + abs(offset_y) >= 3:  # Skip inner pixels for a cleaner outline
                        continue
                    draw.text((x_position + offset_x, text_y + i*40 + offset_y), 
                              line, fill="#000000", font=text_font)
            
            # Draw the main text
            if isinstance(color, tuple) and len(color) == 3:
                hex_color = "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])
                draw.text((x_position, text_y + i*40), line, fill=hex_color, font=text_font)
            else:
                # Default to white text
                draw.text((x_position, text_y + i*40), line, fill="#FFFFFF", font=text_font)
    
    current_meme_image = img

def create_pil_meme(image_path, phrase, font_name, text_color):
    """Create a high-quality PIL Image of the meme that can be saved or copied"""
    global current_meme_image
    
    # Open the base image
    img = Image.open(image_path)
    
    # Resize if needed while maintaining aspect ratio
    max_size = (800, 600)
    img.thumbnail(max_size, Image.LANCZOS)
    
    # Create a drawing context
    draw = ImageDraw.Draw(img)
    
    # Try to use Impact font (classic meme font)
    try:
        font_size = 50  # Larger for better visibility
        font = ImageFont.truetype("Impact", font_size)
    except:
        try:
            # Fallback to Arial Bold
            font = ImageFont.truetype("Arial Bold", font_size)
        except:
            # Last resort fallback
            font = ImageFont.load_default()
    
    # Split phrase into words for wrapping
    words = phrase.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        text_width = draw.textlength(test_line, font=font)
        
        if text_width > img.width - 20:
            # Remove the last word
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Convert text color to RGB
    color_map = {
        "rainbow": None,
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "magenta": (255, 0, 255),
        "cyan": (0, 255, 255),
        "white": (255, 255, 255),
        "usa": None
    }
    
    # Calculate positions for top and bottom text (classic meme style)
    img_height = img.height
    img_width = img.width
    
    # Split text to top and bottom if there are multiple lines
    top_lines = []
    bottom_lines = []
    
    if len(lines) == 1:
        # Just put the single line at the bottom
        bottom_lines = lines
    elif len(lines) == 2:
        # One line at top, one at bottom
        top_lines = [lines[0]]
        bottom_lines = [lines[1]]
    else:
        # Distribute lines, with more at the bottom if odd number
        middle = len(lines) // 2
        top_lines = lines[:middle]
        bottom_lines = lines[middle:]
    
    # Draw top text
    y_position = 10
    for i, line in enumerate(top_lines):
        # Calculate width to center the text
        line_width = draw.textlength(line, font=font)
        x_position = (img_width - line_width) // 2
        
        # Handle special color modes
        if text_color == "rainbow":
            # Draw rainbow text
            rainbow_colors = [(255,0,0), (255,127,0), (255,255,0), 
                             (0,255,0), (0,0,255), (75,0,130), (148,0,211)]
            char_x = x_position
            for j, char in enumerate(line):
                color_idx = j % len(rainbow_colors)
                r, g, b = rainbow_colors[color_idx]
                hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                
                # Draw thick black outline
                for offset_x in range(-3, 4):
                    for offset_y in range(-3, 4):
                        if abs(offset_x) + abs(offset_y) >= 3:
                            continue
                        draw.text((char_x + offset_x, y_position + i*font_size + offset_y), 
                                 char, fill="#000000", font=font)
                
                # Draw colored character
                draw.text((char_x, y_position + i*font_size), 
                         char, fill=hex_color, font=font)
                char_x += draw.textlength(char, font=font)
        elif text_color == "usa":
            # Draw USA color text
            usa_colors = [(255,0,0), (255,255,255), (0,0,255)]
            char_x = x_position
            for j, char in enumerate(line):
                color_idx = j % 3
                r, g, b = usa_colors[color_idx]
                hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                
                # Draw thick black outline
                for offset_x in range(-3, 4):
                    for offset_y in range(-3, 4):
                        if abs(offset_x) + abs(offset_y) >= 3:
                            continue
                        draw.text((char_x + offset_x, y_position + i*font_size + offset_y), 
                                 char, fill="#000000", font=font)
                
                # Draw colored character
                draw.text((char_x, y_position + i*font_size), 
                         char, fill=hex_color, font=font)
                char_x += draw.textlength(char, font=font)
        else:
            # Classic meme text - white with black outline
            color = color_map.get(text_color, (255, 255, 255))
            hex_color = "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2]) if isinstance(color, tuple) else "#FFFFFF"
            
            # Draw thick black outline
            for offset_x in range(-3, 4):
                for offset_y in range(-3, 4):
                    if abs(offset_x) + abs(offset_y) >= 3:
                        continue
                    draw.text((x_position + offset_x, y_position + i*font_size + offset_y), 
                             line, fill="#000000", font=font)
            
            # Draw the main text
            draw.text((x_position, y_position + i*font_size), line, fill=hex_color, font=font)
    
    # Draw bottom text
    y_position = img_height - (len(bottom_lines) * font_size) - 10
    for i, line in enumerate(bottom_lines):
        # Calculate width to center the text
        line_width = draw.textlength(line, font=font)
        x_position = (img_width - line_width) // 2
        
        # Handle special color modes (same as top text)
        if text_color == "rainbow":
            rainbow_colors = [(255,0,0), (255,127,0), (255,255,0), 
                             (0,255,0), (0,0,255), (75,0,130), (148,0,211)]
            char_x = x_position
            for j, char in enumerate(line):
                color_idx = j % len(rainbow_colors)
                r, g, b = rainbow_colors[color_idx]
                hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                
                # Draw thick black outline
                for offset_x in range(-3, 4):
                    for offset_y in range(-3, 4):
                        if abs(offset_x) + abs(offset_y) >= 3:
                            continue
                        draw.text((char_x + offset_x, y_position + i*font_size + offset_y), 
                                 char, fill="#000000", font=font)
                
                # Draw colored character
                draw.text((char_x, y_position + i*font_size), 
                         char, fill=hex_color, font=font)
                char_x += draw.textlength(char, font=font)
        elif text_color == "usa":
            usa_colors = [(255,0,0), (255,255,255), (0,0,255)]
            char_x = x_position
            for j, char in enumerate(line):
                color_idx = j % 3
                r, g, b = usa_colors[color_idx]
                hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                
                # Draw thick black outline
                for offset_x in range(-3, 4):
                    for offset_y in range(-3, 4):
                        if abs(offset_x) + abs(offset_y) >= 3:
                            continue
                        draw.text((char_x + offset_x, y_position + i*font_size + offset_y), 
                                 char, fill="#000000", font=font)
                
                # Draw colored character
                draw.text((char_x, y_position + i*font_size), 
                         char, fill=hex_color, font=font)
                char_x += draw.textlength(char, font=font)
        else:
            # Classic meme text - white with black outline
            color = color_map.get(text_color, (255, 255, 255))
            hex_color = "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2]) if isinstance(color, tuple) else "#FFFFFF"
            
            # Draw thick black outline
            for offset_x in range(-3, 4):
                for offset_y in range(-3, 4):
                    if abs(offset_x) + abs(offset_y) >= 3:
                        continue
                    draw.text((x_position + offset_x, y_position + i*font_size + offset_y), 
                             line, fill="#000000", font=font)
            
            # Draw the main text
            draw.text((x_position, y_position + i*font_size), line, fill=hex_color, font=font)
    
    current_meme_image = img

def copy_to_clipboard():
    """Copy the current meme image to clipboard"""
    global current_meme_image
    
    if not current_meme_image:
        return False
    
    # Save image to a temporary buffer
    buffer = io.BytesIO()
    current_meme_image.save(buffer, 'PNG')
    buffer.seek(0)
    
    try:
        # For Windows, we can use this method
        import win32clipboard
        from io import BytesIO
        
        data = buffer.getvalue()
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        return True
    except ImportError:
        # For Linux systems
        try:
            import subprocess
            
            # Save to temporary file
            temp_path = os.path.join(GEN_IMAGES_DIR, 'temp_clipboard.png')
            current_meme_image.save(temp_path)
            
            # Use xclip to copy to clipboard
            try:
                subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-i', temp_path], check=True)
                success = True
            except subprocess.CalledProcessError:
                # Try with wl-copy for Wayland
                try:
                    subprocess.run(['wl-copy', '-t', 'image/png', '-f', temp_path], check=True)
                    success = True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    success = False
            
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return success
        except Exception as e:
            print(f"Could not copy image to clipboard: {str(e)}")
            return False

def export_ascii_to_clipboard():
    """Export the current ASCII art to clipboard as text"""
    global current_ascii_art
    
    if not current_ascii_art:
        return False
    
    try:
        pyperclip.copy(current_ascii_art)
        return True
    except Exception as e:
        print(f"Error copying ASCII to clipboard: {str(e)}")
        return False

def meme_loop():
    """Run the meme generation in the main thread with debugging"""
    global is_generating
    
    try:
        # Update status
        status_var.set("Generating meme...")
        window.update()  # Force the UI to update
        
        print("Entering meme_loop")
        
        # Direct call to Screen.wrapper in the main thread
        Screen.wrapper(generate_meme)
        
        print("Meme generation completed")
        status_var.set("Meme generated successfully!")
    except Exception as e:
        print(f"Error generating meme: {str(e)}")
        traceback.print_exc()
        messagebox.showerror("Error", f"Failed to generate meme: {str(e)}")
        status_var.set(f"Error: {str(e)}")
    finally:
        # Make sure to reset generating flag
        is_generating = False

def regenerate_ascii_art(force=False):
    """Regenerate all ASCII art with current settings"""
    if force or messagebox.askyesno("Regenerate ASCII Art", 
                                   f"Regenerate all ASCII art using '{CURRENT_ASCII_SET}' characters at width {CURRENT_ASCII_WIDTH}?"):
        # Create a progress window
        progress_window = Toplevel()
        progress_window.title("Generating ASCII Art")
        progress_window.geometry("300x100")
        
        progress_label = Label(progress_window, text="Creating ASCII art...", padx=10, pady=10)
        progress_label.pack()
        
        progress_bar = ttk.Progressbar(progress_window, orient="horizontal", 
                                     length=280, mode="determinate")
        progress_bar.pack(padx=10, pady=10)
        
        # Create thread for generating ASCII art
        def generate_ascii_thread():
            # First empty the ASCII directory to remove old files
            for file in os.listdir(ASCII_DIR):
                file_path = os.path.join(ASCII_DIR, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            # Generate new ASCII art
            total_images = len(color_images)
            for i, img_file in enumerate(color_images):
                try:
                    img_path = os.path.join(IMAGES_DIR, img_file)
                    ascii_art = image_to_ascii(img_path, width=CURRENT_ASCII_WIDTH, 
                                             char_set=ASCII_SETS[CURRENT_ASCII_SET])
                    
                    # Save ASCII art to file
                    base_name = os.path.splitext(img_file)[0]
                    ascii_path = os.path.join(ASCII_DIR, f"{base_name}_ascii.txt")
                    
                    with open(ascii_path, 'w') as f:
                        f.write(ascii_art)
                    
                    # Update progress
                    progress = int((i + 1) / total_images * 100)
                    progress_bar["value"] = progress
                    progress_label["text"] = f"Processing image {i+1} of {total_images}..."
                    
                except Exception as e:
                    print(f"Error creating ASCII version of {img_file}: {str(e)}")
            
            # Update the ascii_images list after creating them
            global ascii_images
            ascii_images = [f for f in os.listdir(ASCII_DIR) if f.lower().endswith('.txt')]
            
            # Close progress window
            progress_window.destroy()
            messagebox.showinfo("Success", f"Generated {len(ascii_images)} ASCII art images!")
        
        # Start the thread
        threading.Thread(target=generate_ascii_thread).start()

def display_meme_in_window():
    """Display the current meme in a Tkinter window"""
    global current_meme_image
    
    if current_meme_image is None:
        messagebox.showinfo("Info", "No meme has been generated yet!")
        return
        
    # Create a new window to display the meme
    meme_window = Toplevel(window)
    meme_window.title("Your Trump Meme")
    
    # Convert PIL image to Tkinter PhotoImage
    photo_img = ImageTk.PhotoImage(current_meme_image)
    
    # Keep a reference to prevent garbage collection
    meme_window.photo_img = photo_img
    
    # Display the image
    label = Label(meme_window, image=photo_img)
    label.pack(padx=10, pady=10)
    
    # Add buttons
    btn_frame = Frame(meme_window)
    btn_frame.pack(pady=10)
    
    Button(btn_frame, text="Save", command=on_save_meme,
           bg="#00cc52", fg="white", width=10).grid(row=0, column=0, padx=5)
    Button(btn_frame, text="Copy", command=copy_to_clipboard,
           bg="#0052cc", fg="white", width=10).grid(row=0, column=1, padx=5)
    Button(btn_frame, text="Close", command=meme_window.destroy,
           bg="#cc0000", fg="white", width=10).grid(row=0, column=2, padx=5)

def on_generate_meme():
    """Handle the generate meme button click with a direct approach"""
    global is_generating, meme_generated, current_meme, current_meme_image, current_ascii_art, current_display_mode
    
    if is_generating:
        messagebox.showinfo("Please Wait", "Already generating a meme. Please wait.")
        return
    
    # Set flag to prevent multiple generations
    is_generating = True
    status_var.set("Generating meme...")
    window.update()
    
    try:
        # Check if we have any images to work with
        if not color_images:
            messagebox.showerror("Error", "No images found! Please add some images.")
            is_generating = False
            status_var.set("Error: No images available")
            return
        
        # Decide display mode based on settings
        if settings["default_mode"] == "random":
            display_mode = random.choice(["normal", "bw", "ascii"])
        else:
            display_mode = settings["default_mode"]
        
        current_display_mode = display_mode
        
        # Randomly select text style
        text_color = random.choice(TEXT_COLORS)
        font_style = random.choice(FIGLET_FONTS)
        phrase = random.choice(phrases)
        
        # Select the image based on display mode
        if display_mode == "bw" and bw_images:
            image = random.choice(bw_images)
            image_dir = BW_IMAGES_DIR
        elif display_mode == "ascii" and ascii_images:
            ascii_file = random.choice(ascii_images)
            with open(os.path.join(ASCII_DIR, ascii_file), 'r') as f:
                current_ascii_art = f.read()
            image = ascii_file
            # For ASCII art, create the image directly
            create_pil_ascii_meme(current_ascii_art, phrase, font_style, text_color)
        else:
            image = random.choice(color_images)
            image_dir = IMAGES_DIR
            # Create the meme image
            image_path = os.path.join(image_dir, image)
            create_pil_meme(image_path, phrase, font_style, text_color)
        
        # Store meme info
        meme_generated = True
        current_meme = {
            "image": image,
            "phrase": phrase,
            "font": font_style,
            "display_mode": display_mode,
            "text_color": text_color
        }
        
        # Display the meme
        if display_mode == "ascii":
            try:
                # Try to display in terminal using asciimatics
                Screen.wrapper(show_ascii_meme)
            except Exception as e:
                print(f"Terminal display error: {e}")
                # Fall back to window display
                display_meme_in_window()
        else:
            # For image-based memes, show in window
            display_meme_in_window()
        
        # Auto-copy if enabled
        if settings["auto_copy"]:
            copy_to_clipboard()
            
        status_var.set("Meme generated successfully!")
        
    except Exception as e:
        print(f"Error generating meme: {str(e)}")
        traceback.print_exc()
        messagebox.showerror("Error", f"Failed to generate meme: {str(e)}")
        status_var.set(f"Error: {str(e)}")
    finally:
        is_generating = False

def show_ascii_meme(screen):
    """Show ASCII art meme in terminal using asciimatics"""
    global current_ascii_art
    
    if not current_ascii_art:
        return
    
    # Calculate screen dimensions
    max_height = screen.height - 4
    
    # Create display effects
    effects = []
    
    # ASCII art display
    lines = current_ascii_art.split('\n')
    for i, line in enumerate(lines):
        if i < max_height:  # Prevent going off screen
            effects.append(
                Print(screen, 
                      StaticRenderer([line]), 
                      i)  # Use actual line position
            )
    
    # Play the scene
    scene = Scene(effects, -1)
    screen.play([scene], stop_on_resize=True, repeat=False)
    
    # Wait for user input to close
    screen.wait_for_input(10.0)  # Wait up to 10 seconds or until key press

def on_save_meme():
    """Save the current meme to disk and possibly copy to clipboard"""
    global current_meme, current_meme_image
    
    if not meme_generated or not current_meme:
        messagebox.showinfo("Info", "Please generate a meme first.")
        return
    
    # Let user choose where to save
    initial_filename = f"trump_meme_{random.randint(1000, 9999)}"
    file_path = filedialog.asksaveasfilename(
        initialdir=GEN_IMAGES_DIR,
        initialfile=initial_filename,
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
    )
    
    if not file_path:  # User cancelled
        return
        
    # Save text info alongside image
    txt_path = os.path.splitext(file_path)[0] + ".txt"
    
    try:
        # Save image
        if current_meme_image:
            current_meme_image.save(file_path)
        
        # Save text info
        meme_info = f"Trump Meme Generator Pro {VERSION}\n"
        meme_info += f"Created: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        meme_info += f"Meme Info:\n"
        meme_info += f"Image: {current_meme['image']}\n"
        meme_info += f"Phrase: {current_meme['phrase']}\n"
        meme_info += f"Font: {current_meme['font']}\n"
        meme_info += f"Display Mode: {current_meme['display_mode']}\n"
        meme_info += f"Text Color: {current_meme['text_color']}\n"
        
        with open(txt_path, 'w') as f:
            f.write(meme_info)
        
        # Also copy to clipboard unless auto-copy is on (in which case it's already copied)
        clipboard_success = True
        if not settings["auto_copy"]:
            clipboard_success = copy_to_clipboard()
        
        if clipboard_success:
            messagebox.showinfo("Success", 
                               f"Meme saved to {os.path.basename(file_path)} and copied to clipboard.")
            status_var.set(f"Meme saved and copied to clipboard!")
        else:
            # Fallback to copying the text
            pyperclip.copy(meme_info)
            messagebox.showinfo("Partial Success", 
                               f"Meme saved to {os.path.basename(file_path)}. Could not copy image to clipboard, but text info was copied.")
            status_var.set(f"Meme saved. Only text copied to clipboard.")
    except Exception as e:
        error_message = f"Failed to save meme: {str(e)}\n"
        traceback.print_exc()
        messagebox.showerror("Error", f"Failed to save meme: {str(e)}")
        status_var.set(f"Error: {str(e)}")

def copy_last_meme():
    """Copy the last generated meme to clipboard"""
    if not current_meme_image:
        messagebox.showinfo("Info", "Please generate a meme first.")
        return
    
    # If we're in ASCII mode, give the option to copy as text or as image
    if current_meme and current_meme["display_mode"] == "ascii" and current_ascii_art:
        copy_mode = messagebox.askyesno("Copy Options", 
                                      "Copy as text (Yes) or as image (No)?", 
                                      default=messagebox.NO)
        if copy_mode:
            success = export_ascii_to_clipboard()
        else:
            success = copy_to_clipboard()
    else:
        success = copy_to_clipboard()
    
    if success:
        messagebox.showinfo("Success", "Meme copied to clipboard.")
        status_var.set("Meme copied to clipboard!")
    else:
        messagebox.showinfo("Error", "Could not copy to clipboard.")
        status_var.set("Error: Could not copy to clipboard")

def add_phrase():
    """Add a new phrase to the phrases list"""
    new_phrase = simpledialog.askstring("Add Phrase", "Enter a new Trump-worthy phrase:")
    if new_phrase and new_phrase.strip():
        phrases.append(new_phrase.strip())
        
        # Save to file
        with open(PHRASES_FILE, 'a') as f:
            f.write(new_phrase.strip() + '\n')
        
        messagebox.showinfo("Success", f"Added new phrase: {new_phrase}")

def edit_phrases():
    """Open a window to edit all phrases"""
    phrases_window = Toplevel()
    phrases_window.title("Edit Trump Phrases")
    phrases_window.geometry("600x400")
    
    # Create a text widget for editing
    text_widget = Text(phrases_window, wrap=WORD, padx=10, pady=10)
    text_widget.pack(expand=True, fill=BOTH, padx=10, pady=10)
    
    # Insert all phrases
    for phrase in phrases:
        text_widget.insert(END, phrase + '\n')
    
    # Create frame for buttons
    btn_frame = Frame(phrases_window)
    btn_frame.pack(pady=10)
    
    def save_phrases():
        # Get all text and split into lines
        all_text = text_widget.get(1.0, END)
        new_phrases = [line.strip() for line in all_text.splitlines() if line.strip()]
        
        # Update global phrases
        global phrases
        phrases = new_phrases
        
        # Save to file
        with open(PHRASES_FILE, 'w') as f:
            for phrase in new_phrases:
                f.write(phrase + '\n')
        
        messagebox.showinfo("Success", f"Saved {len(new_phrases)} phrases!")
        phrases_window.destroy()
    
    # Add save and cancel buttons
    Button(btn_frame, text="Save", command=save_phrases, 
         bg="#00cc52", fg="white", font=("Arial", 10), width=10).grid(row=0, column=0, padx=5)
    Button(btn_frame, text="Cancel", command=phrases_window.destroy, 
         bg="#cc0000", fg="white", font=("Arial", 10), width=10).grid(row=0, column=1, padx=5)

def open_settings():
    """Open settings dialog"""
    settings_window = Toplevel()
    settings_window.title("Trump Meme Generator Settings")
    settings_window.geometry("500x450")
    
    # Create a notebook for tabs
    notebook = ttk.Notebook(settings_window)
    notebook.pack(expand=True, fill=BOTH, padx=10, pady=10)
    
    # General settings tab
    general_tab = Frame(notebook)
    notebook.add(general_tab, text="General")
    
    # ASCII settings tab
    ascii_tab = Frame(notebook)
    notebook.add(ascii_tab, text="ASCII Art")
    
    # About tab
    about_tab = Frame(notebook)
    notebook.add(about_tab, text="About")
    
    # General settings
    Label(general_tab, text="Default Display Mode:", anchor=W).grid(row=0, column=0, sticky=W, padx=5, pady=5)
    mode_var = StringVar(value=settings["default_mode"])
    ttk.Combobox(general_tab, textvariable=mode_var, 
               values=["random", "normal", "bw", "ascii"]).grid(row=0, column=1, sticky=W, padx=5, pady=5)
    
    auto_copy_var = BooleanVar(value=settings["auto_copy"])
    Checkbutton(general_tab, text="Auto-copy to clipboard", variable=auto_copy_var).grid(row=1, column=0, sticky=W, padx=5, pady=5, columnspan=2)
    
    show_splash_var = BooleanVar(value=settings["show_splash"])
    Checkbutton(general_tab, text="Show splash screen on startup", variable=show_splash_var).grid(row=2, column=0, sticky=W, padx=5, pady=5, columnspan=2)
    
    theme_var = StringVar(value=settings["theme"])
    Label(general_tab, text="Theme:", anchor=W).grid(row=3, column=0, sticky=W, padx=5, pady=5)
    ttk.Combobox(general_tab, textvariable=theme_var, 
               values=["dark", "light"]).grid(row=3, column=1, sticky=W, padx=5, pady=5)
    
    # ASCII settings
    Label(ascii_tab, text="ASCII Character Set:", anchor=W).grid(row=0, column=0, sticky=W, padx=5, pady=5)
    ascii_set_var = StringVar(value=CURRENT_ASCII_SET)
    ttk.Combobox(ascii_tab, textvariable=ascii_set_var, 
               values=list(ASCII_SETS.keys())).grid(row=0, column=1, sticky=W, padx=5, pady=5)
    
    Label(ascii_tab, text="ASCII Width:", anchor=W).grid(row=1, column=0, sticky=W, padx=5, pady=5)
    ascii_width_var = IntVar(value=CURRENT_ASCII_WIDTH)
    ttk.Combobox(ascii_tab, textvariable=ascii_width_var, 
               values=ASCII_WIDTHS).grid(row=1, column=1, sticky=W, padx=5, pady=5)
    
    # Preview of ASCII character sets
    Label(ascii_tab, text="Character Set Preview:", anchor=W).grid(row=2, column=0, sticky=W, padx=5, pady=5, columnspan=2)
    preview_frame = Frame(ascii_tab, bd=1, relief=SUNKEN)
    preview_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=W+E)
    
    preview_text = Text(preview_frame, height=5, width=50, bg="black", fg="white", font=("Courier", 10))
    preview_text.pack(padx=5, pady=5)
    
    # Update preview when changing ASCII set
    def update_preview(*args):
        selected_set = ascii_set_var.get()
        if selected_set in ASCII_SETS:
            preview_text.delete(1.0, END)
            preview_text.insert(END, "Characters from darkest to lightest:\n")
            preview_text.insert(END, ASCII_SETS[selected_set])
    
    ascii_set_var.trace("w", update_preview)
    update_preview()  # Initial preview
    
    Button(ascii_tab, text="Regenerate ASCII Art", command=lambda: regenerate_ascii_art(force=True),
         bg="#0052cc", fg="white").grid(row=4, column=0, columnspan=2, padx=5, pady=15)
    
    # About tab
    Label(about_tab, text=f"Trump Meme Generator Pro {VERSION}", font=("Arial", 14, "bold")).pack(pady=10)
    Label(about_tab, text="The ultimate tool for creating Trump memes!").pack(pady=5)
    Label(about_tab, text="© 2025 Meme Industries").pack(pady=5)
    
    # Credits
    credits_frame = Frame(about_tab, bd=1, relief=SUNKEN)
    credits_frame.pack(fill=X, padx=10, pady=10)
    Label(credits_frame, text="Credits", font=("Arial", 10, "bold")).pack(anchor=W, padx=5, pady=5)
    Label(credits_frame, text="• ASCII art generation improved with help from Claude 3.7").pack(anchor=W, padx=5)
    Label(credits_frame, text="• Made with Python, Tkinter, PIL, and Asciimatics").pack(anchor=W, padx=5)
    Label(credits_frame, text="• Special thanks to the meme community").pack(anchor=W, padx=5, pady=5)
    
    def save_settings_dialog():
        # Update settings with new values
        settings["default_mode"] = mode_var.get()
        settings["auto_copy"] = auto_copy_var.get()
        settings["show_splash"] = show_splash_var.get()
        settings["theme"] = theme_var.get()
        settings["ascii_set"] = ascii_set_var.get()
        settings["ascii_width"] = ascii_width_var.get()
        
        # Update globals
        global CURRENT_ASCII_SET, CURRENT_ASCII_WIDTH
        CURRENT_ASCII_SET = settings["ascii_set"]
        CURRENT_ASCII_WIDTH = settings["ascii_width"]
        
        # Save to file
        save_settings()
        
        # Apply theme if changed
        apply_theme()
        
        messagebox.showinfo("Settings Saved", "Your settings have been saved and applied.")
        settings_window.destroy()
    
    # Buttons at bottom
    btn_frame = Frame(settings_window)
    btn_frame.pack(pady=10)
    
    Button(btn_frame, text="Save", command=save_settings_dialog, 
         bg="#00cc52", fg="white", width=10).grid(row=0, column=0, padx=5)
    Button(btn_frame, text="Cancel", command=settings_window.destroy, 
         bg="#cc0000", fg="white", width=10).grid(row=0, column=1, padx=5)

def apply_theme():
    """Apply the current theme to the UI"""
    theme = settings.get("theme", "dark")
    
    if theme == "dark":
        bg_color = "black"
        fg_color = "white"
        button_bg = "#333333"
    else:
        bg_color = "white"
        fg_color = "black"
        button_bg = "#dddddd"
    
    # Update main window
    window.configure(bg=bg_color)
    
    # Update all child widgets
    for child in window.winfo_children():
        widget_type = child.winfo_class()
        if widget_type in ('Frame', 'Label'):
            child.configure(bg=bg_color)
            if widget_type == 'Label':
                child.configure(fg=fg_color)
        
        # If it's a frame, update its children too
        if widget_type == 'Frame':
            for subchild in child.winfo_children():
                subwidget_type = subchild.winfo_class()
                if subwidget_type == 'Label':
                    subchild.configure(bg=bg_color, fg=fg_color)

def on_quit():
    """Clean exit the application"""
    if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
        window.quit()
        window.destroy()
        sys.exit()

def import_images():
    """Import new images to the collection"""
    file_paths = filedialog.askopenfilenames(
        title="Select Trump Images",
        filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
    )
    
    if not file_paths:
        return
    
    # Create progress window
    progress_window = Toplevel()
    progress_window.title("Importing Images")
    progress_window.geometry("300x100")
    
    progress_label = Label(progress_window, text="Importing images...", padx=10, pady=10)
    progress_label.pack()
    
    progress_bar = ttk.Progressbar(progress_window, orient="horizontal", 
                                 length=280, mode="determinate")
    progress_bar.pack(padx=10, pady=10)
    
    # Create thread for importing
    def import_thread():
        global color_images  # Move the global declaration to the beginning of the function
        imported_count = 0
        for i, file_path in enumerate(file_paths):
            try:
                # Get file name
                file_name = os.path.basename(file_path)
                
                # Check if file already exists
                if file_name in color_images:
                    new_name = f"{os.path.splitext(file_name)[0]}_{random.randint(1000,9999)}{os.path.splitext(file_name)[1]}"
                else:
                    new_name = file_name
                
                # Copy file to images directory
                dest_path = os.path.join(IMAGES_DIR, new_name)
                shutil.copy2(file_path, dest_path)
                
                # Update progress
                progress = int((i + 1) / len(file_paths) * 100)
                progress_bar["value"] = progress
                progress_label["text"] = f"Importing image {i+1} of {len(file_paths)}..."
                
                imported_count += 1
                
            except Exception as e:
                print(f"Error importing image {file_path}: {str(e)}")
        
        # Update global list
        color_images = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.jpg', '.png'))]
        
        # Create B&W and ASCII versions
        create_bw_versions()
        create_ascii_versions()
        
        # Close progress window
        progress_window.destroy()
        messagebox.showinfo("Import Complete", f"Successfully imported {imported_count} images.")
    
    # Start the thread
    threading.Thread(target=import_thread).start()

# Main functionality
# Load settings before creating window
load_settings()

# Create B&W and ASCII versions if needed
create_bw_versions()
create_ascii_versions()

# Create main window
window = Tk()
window.title(f"Trump Meme Generator Pro {VERSION}")
window.configure(bg="black" if settings["theme"] == "dark" else "white")
window.geometry("650x550")  # Larger window for better display
window.resizable(True, True)  # Allow window to be resized

# Create menu bar
menu_bar = Menu(window)
window.config(menu=menu_bar)

# File menu
file_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Generate Meme", command=on_generate_meme)
file_menu.add_command(label="Save Meme", command=on_save_meme)
file_menu.add_command(label="Copy to Clipboard", command=copy_last_meme)
file_menu.add_separator()
file_menu.add_command(label="Import Images", command=import_images)
file_menu.add_separator()
file_menu.add_command(label="Settings", command=open_settings)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=on_quit)

# Edit menu
edit_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Edit", menu=edit_menu)
edit_menu.add_command(label="Add Phrase", command=add_phrase)
edit_menu.add_command(label="Edit Phrases", command=edit_phrases)

# Tools menu
tools_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Tools", menu=tools_menu)
tools_menu.add_command(label="Regenerate ASCII Art", command=lambda: regenerate_ascii_art(force=True))

# Splash screen if enabled
if settings["show_splash"]:
    try:
        splash_image = PhotoImage(file="trumpsplash.gif")
        splash_label = Label(window, image=splash_image, bg="black")
        splash_label.pack(pady=10)
    except:
        # Fallback if splash image is missing
        # Create a title with custom pyfiglet text
        try:
            custom_font = random.choice(['slant', 'big', 'doom', 'standard'])
            title_text = pyfiglet.figlet_format("TRUMP MEME", font=custom_font)
            Label(window, text=title_text, font=("Courier", 10), fg="white", bg="black", justify=LEFT).pack(pady=10)
            subtitle = pyfiglet.figlet_format("GENERATOR PRO", font=custom_font)
            Label(window, text=subtitle, font=("Courier", 10), fg="red", bg="black", justify=LEFT).pack(pady=5)
        except:
            # Ultimate fallback
            Label(window, text="TRUMP MEME GENERATOR PRO", font=("Impact", 24), fg="red", bg="black").pack(pady=20)
            Label(window, text="VERSION " + VERSION, font=("Impact", 16), fg="white", bg="black").pack(pady=5)

# Create a frame for buttons
button_frame = Frame(window, bg="black" if settings["theme"] == "dark" else "white")
button_frame.pack(pady=20)

# Create buttons with improved styling
Button(button_frame, text="Generate Meme", command=on_generate_meme, width=20, height=2,
       bg="#0052cc", fg="white", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=10)

Button(button_frame, text="Save & Copy", command=on_save_meme, width=20, height=2,
       bg="#00cc52", fg="white", font=("Arial", 12, "bold")).grid(row=0, column=1, padx=10, pady=10)

Button(button_frame, text="Copy Last Meme", command=copy_last_meme, width=20, height=2,
       bg="#cc5200", fg="white", font=("Arial", 12, "bold")).grid(row=1, column=0, padx=10, pady=10)

Button(button_frame, text="Quit", command=on_quit, width=20, height=2,
       bg="#cc0000", fg="white", font=("Arial", 12, "bold")).grid(row=1, column=1, padx=10, pady=10)

# Display modes frame
modes_frame = Frame(window, bg="black" if settings["theme"] == "dark" else "white")
modes_frame.pack(pady=5)

fg_color = "white" if settings["theme"] == "dark" else "black"
Label(modes_frame, text="Available Display Modes:", fg=fg_color, 
     bg="black" if settings["theme"] == "dark" else "white",
     font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=3, pady=5)

# Mode indicators 
Label(modes_frame, text="Color Images", fg="#00cc52" if color_images else "gray", 
     bg="black" if settings["theme"] == "dark" else "white").grid(row=1, column=0, padx=20)
Label(modes_frame, text="B&W Images", fg="#00cc52" if bw_images else "gray", 
     bg="black" if settings["theme"] == "dark" else "white").grid(row=1, column=1, padx=20)
Label(modes_frame, text="ASCII Art", fg="#00cc52" if ascii_images else "gray", 
     bg="black" if settings["theme"] == "dark" else "white").grid(row=1, column=2, padx=20)

# Settings indicator
settings_text = f"ASCII: {CURRENT_ASCII_SET} ({CURRENT_ASCII_WIDTH}px) | Mode: {settings['default_mode'].capitalize()}"
settings_label = Label(modes_frame, text=settings_text, fg=fg_color, 
                     bg="black" if settings["theme"] == "dark" else "white", font=("Arial", 8))
settings_label.grid(row=2, column=0, columnspan=3, pady=5)

# Status bar
status_var = StringVar()
status_var.set("Ready - Create amazing Trump memes!")
status_bar = Label(window, textvariable=status_var, fg=fg_color, 
                 bg="black" if settings["theme"] == "dark" else "white", 
                 bd=1, relief=SUNKEN, anchor=W)
status_bar.pack(side=BOTTOM, fill=X)

# Apply theme
apply_theme()

# Main loop
window.mainloop()
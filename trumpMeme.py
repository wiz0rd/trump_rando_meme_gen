import os
import sys
import random
import pyperclip
import traceback
from tkinter import *
from tkinter import messagebox, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Print
from asciimatics.renderers import ColourImageFile, FigletText, Rainbow, SpeechBubble, StaticRenderer
from asciimatics.exceptions import ResizeScreenError
import numpy as np
import pyfiglet

# Directories and files
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(SCRIPT_DIR, 'trump_pics')
BW_IMAGES_DIR = os.path.join(SCRIPT_DIR, 'trump_pics_bw')  # New directory for B&W images
ASCII_DIR = os.path.join(SCRIPT_DIR, 'trump_pics_ascii')  # New directory for ASCII art
GEN_IMAGES_DIR = os.path.join(SCRIPT_DIR, 'genImages')
PHRASES_FILE = os.path.join(SCRIPT_DIR, 'phrases.txt')

# Ensure directories exist
os.makedirs(GEN_IMAGES_DIR, exist_ok=True)
os.makedirs(BW_IMAGES_DIR, exist_ok=True)
os.makedirs(ASCII_DIR, exist_ok=True)

# Load images and phrases
color_images = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.jpg', '.png'))]
# Initial empty lists
bw_images = []
ascii_images = []

with open(PHRASES_FILE, 'r') as f:
    phrases = [line.strip() for line in f]

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

# ASCII characters for art - improved character set for better contrast
ASCII_CHARS = ['$', '@', 'B', '%', '8', '&', 'W', 'M', '#', '*', 'o', 'a', 'h', 'k', 'b', 'd', 'p', 'q', 'w', 'm', 'Z', 'O', '0', 'Q', 'L', 'C', 'J', 'U', 'Y', 'X', 'z', 'c', 'v', 'u', 'n', 'x', 'r', 'j', 'f', 't', '/', '\\', '|', '(', ')', '1', '{', '}', '[', ']', '?', '-', '_', '+', '~', '<', '>', 'i', '!', 'l', 'I', ';', ':', ',', '"', '^', '`', '\'', '.', ' ']

# Global variables
meme_generated = False
current_meme = None
current_meme_image = None
current_ascii_art = None
current_display_mode = "normal"  # Can be "normal", "bw", or "ascii"

def create_bw_versions():
    """Create B&W versions of color images if they don't exist already"""
    global bw_images
    
    # First check for existing B&W images
    bw_images = [f for f in os.listdir(BW_IMAGES_DIR) if f.lower().endswith(('.jpg', '.png'))]
    
    if not bw_images:
        print("Creating black and white versions of images...")
        for img_file in color_images:
            try:
                img_path = os.path.join(IMAGES_DIR, img_file)
                img = Image.open(img_path).convert('L')  # Convert to grayscale
                # Enhance contrast
                img = ImageOps.autocontrast(img, cutoff=2)
                bw_path = os.path.join(BW_IMAGES_DIR, f"bw_{img_file}")
                img.save(bw_path)
                print(f"Created B&W version: {bw_path}")
            except Exception as e:
                print(f"Error creating B&W version of {img_file}: {str(e)}")
        
        # Update the bw_images list after creating them
        bw_images = [f for f in os.listdir(BW_IMAGES_DIR) if f.lower().endswith(('.jpg', '.png'))]

def image_to_ascii(image_path, width=120):
    """Convert an image to ASCII art with improved quality"""
    try:
        # Open image and convert to grayscale
        img = Image.open(image_path).convert('L')
        
        # Resize image while maintaining aspect ratio
        width_original, height_original = img.size
        aspect_ratio = height_original / width_original
        height = int(width * aspect_ratio * 0.5)  # Multiply by 0.5 to account for character aspect ratio
        img = img.resize((width, height))
        
        # Enhance contrast for better ASCII definition
        img = ImageOps.autocontrast(img, cutoff=5)
        
        # Convert pixels to ASCII characters
        pixels = list(img.getdata())
        ascii_str = ''
        for i, pixel in enumerate(pixels):
            # Map pixel value (0-255) to ASCII character
            ascii_index = pixel * (len(ASCII_CHARS) - 1) // 255
            ascii_str += ASCII_CHARS[ascii_index]
            if (i + 1) % width == 0:
                ascii_str += '\n'
        
        return ascii_str
    except Exception as e:
        print(f"Error creating ASCII art: {str(e)}")
        return f"Error: {str(e)}"

def create_ascii_versions():
    """Create ASCII art versions of images with improved quality"""
    global ascii_images
    
    # Force re-creation of ASCII art for better quality
    print("Creating ASCII art versions of images...")
    for img_file in color_images:
        try:
            img_path = os.path.join(IMAGES_DIR, img_file)
            ascii_art = image_to_ascii(img_path, width=120)  # Use wider width for more detail
            
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

def generate_meme(screen):
    global meme_generated, current_meme, current_meme_image, current_ascii_art, current_display_mode
    meme_generated = True
    
    # Decide display mode
    display_mode = random.choice(["normal", "bw", "ascii"])
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
    
    # Play the scene
    scene = Scene(effects, -1)
    screen.play([scene], stop_on_resize=True, repeat=False)

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

def create_pil_ascii_meme(ascii_art, phrase, font_name, text_color):
    """Create a PIL Image of ASCII art meme"""
    global current_meme_image
    
    # Calculate size based on ASCII content
    lines = ascii_art.split('\n')
    width = max(len(line) for line in lines) * 8  # Approx width in pixels
    height = len(lines) * 16 + 200  # Height with extra space for text
    
    # Create a blank image with black background
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Try to use a monospace font for ASCII art
    try:
        ascii_font = ImageFont.truetype("Courier New", 12)
    except:
        ascii_font = ImageFont.load_default()
    
    # Draw ASCII art
    y_offset = 10
    for line in lines:
        draw.text((10, y_offset), line, fill="#FFFFFF", font=ascii_font)
        y_offset += 16
    
    # Draw the phrase text
    try:
        # Use a larger font for the phrase
        text_font = ImageFont.truetype("Impact", 36)
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
    text_y = y_offset + 20
    
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
                draw.text((char_x, text_y), char, fill=hex_color, font=text_font)
                char_x += draw.textlength(char, font=text_font)
            char_x = 10
            # Use version-independent way to get line height
            text_y += get_font_height(text_font, line)
    elif text_color == "usa":
        # Draw USA color text
        usa_colors = [(255,0,0), (255,255,255), (0,0,255)]
        char_x = 10
        for i, line in enumerate(lines):
            for j, char in enumerate(line):
                color_idx = j % 3
                r, g, b = usa_colors[color_idx]
                hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                draw.text((char_x, text_y), char, fill=hex_color, font=text_font)
                char_x += draw.textlength(char, font=text_font)
            char_x = 10
            # Use version-independent way to get line height
            text_y += get_font_height(text_font, line)
    else:
        # Use a single color
        color = color_map.get(text_color, (255, 255, 255))
        
        # Add shadow/outline for better readability
        for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
            draw.text((10 + offset[0], text_y + offset[1]), text, font=text_font, fill="#000000")
        
        # Draw the main text in the selected color
        if isinstance(color, tuple) and len(color) == 3:
            # Convert RGB tuple to hex string
            hex_color = "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])
            draw.text((10, text_y), text, font=text_font, fill=hex_color)
        else:
            # Fallback to white if something's wrong with the color
            draw.text((10, text_y), text, font=text_font, fill="#FFFFFF")
    
    current_meme_image = img

def create_pil_meme(image_path, phrase, font_name, text_color):
    """Create a PIL Image of the meme that can be saved or copied"""
    global current_meme_image
    
    # Open the base image
    img = Image.open(image_path)
    
    # Resize if needed while maintaining aspect ratio
    max_size = (800, 600)
    img.thumbnail(max_size, Image.LANCZOS)
    
    # Create a drawing context
    draw = ImageDraw.Draw(img)
    
    # Try to use a better font for the image version
    try:
        # Use Impact font for meme style
        font_size = 36
        font = ImageFont.truetype("Impact", font_size)
    except:
        try:
            # Fallback to Arial
            font = ImageFont.truetype("Arial", font_size)
        except:
            # Last resort fallback
            font = ImageFont.load_default()
    
    # Prepare text
    # Break long phrases into multiple lines
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
    
    text = '\n'.join(lines)
    text_y = img.height - (len(lines) * font_size) - 20
    
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
                # Draw black outline first
                for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
                    draw.text((char_x + offset[0], text_y + i*font_size + offset[1]), 
                             char, fill="#000000", font=font)
                # Draw colored character
                draw.text((char_x, text_y + i*font_size), 
                         char, fill=hex_color, font=font)
                char_x += draw.textlength(char, font=font)
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
                # Draw black outline first
                for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
                    draw.text((char_x + offset[0], text_y + i*font_size + offset[1]), 
                             char, fill="#000000", font=font)
                # Draw colored character
                draw.text((char_x, text_y + i*font_size), 
                         char, fill=hex_color, font=font)
                char_x += draw.textlength(char, font=font)
            char_x = 10
    else:
        # Use a single color
        color = color_map.get(text_color, (255, 255, 255))
        
        # Add shadow/outline for better readability
        for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
            draw.text((10 + offset[0], text_y + offset[1]), text, font=font, fill="#000000")
        
        # Draw the main text in the selected color
        if isinstance(color, tuple) and len(color) == 3:
            # Convert RGB tuple to hex string
            hex_color = "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])
            draw.text((10, text_y), text, font=font, fill=hex_color)
        else:
            # Fallback to white if something's wrong with the color
            draw.text((10, text_y), text, font=font, fill="#FFFFFF")
    
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

def meme_loop():
    while True:
        try:
            Screen.wrapper(generate_meme)
            break
        except ResizeScreenError:
            pass

def on_generate_meme():
    meme_loop()

def on_save_meme():
    global current_meme, current_meme_image
    if not meme_generated or not current_meme:
        messagebox.showinfo("Info", "Please generate a meme first.")
        return
    
    # Save the image file
    save_name = f"trump_meme_{random.randint(1000, 9999)}"
    save_path_img = os.path.join(GEN_IMAGES_DIR, f"{save_name}.png")
    save_path_txt = os.path.join(GEN_IMAGES_DIR, f"{save_name}.txt")
    
    try:
        # Save image
        if current_meme_image:
            current_meme_image.save(save_path_img)
        
        # Save text info
        meme_info = f"Meme Info:\n"
        meme_info += f"Image: {current_meme['image']}\n"
        meme_info += f"Phrase: {current_meme['phrase']}\n"
        meme_info += f"Font: {current_meme['font']}\n"
        meme_info += f"Display Mode: {current_meme['display_mode']}\n"
        meme_info += f"Text Color: {current_meme['text_color']}"
        
        with open(save_path_txt, 'w') as f:
            f.write(meme_info)
        
        # Try to copy to clipboard
        clipboard_success = copy_to_clipboard()
        
        if clipboard_success:
            messagebox.showinfo("Success", 
                               f"Meme saved to {save_path_img} and copied to clipboard.")
            status_var.set(f"Meme saved and copied to clipboard!")
        else:
            # Fallback to copying the text
            pyperclip.copy(meme_info)
            messagebox.showinfo("Partial Success", 
                               f"Meme saved to {save_path_img}. Could not copy image to clipboard, but text info was copied.")
            status_var.set(f"Meme saved. Only text copied to clipboard.")
    except Exception as e:
        error_message = f"Failed to save meme: {str(e)}\n"
        error_message += f"Current working directory: {os.getcwd()}\n"
        error_message += f"GEN_IMAGES_DIR: {GEN_IMAGES_DIR}\n"
        error_message += f"Does GEN_IMAGES_DIR exist? {os.path.exists(GEN_IMAGES_DIR)}\n"
        error_message += "Traceback:\n" + traceback.format_exc()
        print(error_message)  # Print to console for debugging
        messagebox.showerror("Error", error_message)
        status_var.set(f"Error: {str(e)}")

def copy_last_meme():
    """Copy the last generated meme to clipboard"""
    if not current_meme_image:
        messagebox.showinfo("Info", "Please generate a meme first.")
        return
    
    success = copy_to_clipboard()
    
    if success:
        messagebox.showinfo("Success", "Meme copied to clipboard.")
        status_var.set("Meme copied to clipboard!")
    else:
        messagebox.showinfo("Error", "Could not copy image to clipboard.")
        status_var.set("Error: Could not copy to clipboard")

def on_quit():
    window.quit()
    window.destroy()
    sys.exit()

# Create B&W and ASCII versions if needed
create_bw_versions()
create_ascii_versions()

# Create main window
window = Tk()
window.title("Trump Meme Generator Pro")
window.configure(bg="black")
window.geometry("600x500")  # Increased height for better display

# Load and display splash image
try:
    splash_image = PhotoImage(file="trumpsplash.gif")
    Label(window, image=splash_image, bg="black").pack(pady=10)
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
        Label(window, text="TRUMP MEME GENERATOR PRO", font=("Impact", 24), fg="white", bg="black").pack(pady=20)

# Create a frame for buttons
button_frame = Frame(window, bg="black")
button_frame.pack(pady=10)

# Create buttons with improved styling
Button(button_frame, text="Generate Meme", command=on_generate_meme, width=20, 
       bg="#0052cc", fg="white", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=8)

Button(button_frame, text="Save & Copy", command=on_save_meme, width=20,
       bg="#00cc52", fg="white", font=("Arial", 12)).grid(row=0, column=1, padx=5, pady=8)

Button(button_frame, text="Copy Last Meme", command=copy_last_meme, width=20,
       bg="#cc5200", fg="white", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=8)

Button(button_frame, text="Quit", command=on_quit, width=20,
       bg="#cc0000", fg="white", font=("Arial", 12)).grid(row=1, column=1, padx=5, pady=8)

# Display modes frame
modes_frame = Frame(window, bg="black")
modes_frame.pack(pady=5)

Label(modes_frame, text="Available Display Modes:", fg="white", bg="black").grid(row=0, column=0, columnspan=3, pady=5)

# Mode indicators 
Label(modes_frame, text="Color Images", fg="#00cc52" if color_images else "gray", bg="black").grid(row=1, column=0, padx=10)
Label(modes_frame, text="B&W Images", fg="#00cc52" if bw_images else "gray", bg="black").grid(row=1, column=1, padx=10)
Label(modes_frame, text="ASCII Art", fg="#00cc52" if ascii_images else "gray", bg="black").grid(row=1, column=2, padx=10)

# Status bar
status_var = StringVar()
status_var.set("Ready - Create amazing Trump memes!")
status_bar = Label(window, textvariable=status_var, fg="white", bg="black", bd=1, relief=SUNKEN, anchor=W)
status_bar.pack(side=BOTTOM, fill=X)

window.mainloop()
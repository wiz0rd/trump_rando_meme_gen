import os
import sys
import random
import pyperclip
import traceback
from tkinter import *
from tkinter import messagebox
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Print, Cycle, Stars
from asciimatics.renderers import FigletText, SpeechBubble, Box, Rainbow, Fire, ColourImageFile, StaticRenderer
from asciimatics.particles import RingFirework, StarFirework
from asciimatics.exceptions import ResizeScreenError
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

# Directories and files
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(SCRIPT_DIR, 'trump_pics')
GEN_IMAGES_DIR = os.path.join(SCRIPT_DIR, 'genImages')
PHRASES_FILE = os.path.join(SCRIPT_DIR, 'phrases.txt')

# Ensure genImages directory exists
os.makedirs(GEN_IMAGES_DIR, exist_ok=True)

# Load images and phrases
images = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
with open(PHRASES_FILE, 'r') as f:
    phrases = [line.strip() for line in f]

# Global variables
meme_generated = False
current_meme = None

# Web-like character set for higher quality ASCII art
# Ordered from darkest to lightest for proper mapping
ASCII_CHARS = "@%#*+=-:. "

# Alternative character sets to try
ALT_CHARS = [
    "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. ",
    "@QB#NgWM8RDHdmSAKbq5EX2$ZPUwGey92F4CALTtfjzuvxnr[]{}?-_+<>|i!lI;:,\"^`'. ",
    "█▓▒░@#$%&?*+;:,. "
]

# Available figlet fonts for variety (pre-tested to work)
FIGLET_FONTS = [
    'big', 'block', 'mini', 'small', 'standard'
]

def resize_image(image, new_width=300):
    """Resize image maintaining aspect ratio"""
    width, height = image.size
    ratio = height / width / 1.8  # Terminal characters aspect ratio
    new_height = int(new_width * ratio)
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
    return resized_image

def enhance_image(image):
    """Apply image enhancements for optimal ASCII conversion"""
    # Auto-level the image to improve contrast distribution
    image = ImageOps.autocontrast(image, cutoff=0.5)
    
    # Apply edge enhancement
    image = image.filter(ImageFilter.EDGE_ENHANCE)
    
    # Apply a precise amount of contrast enhancement
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.8)  # Increased contrast for more definition
    
    # Brighten slightly
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.1)
    
    # Sharpen the image slightly
    image = image.filter(ImageFilter.SHARPEN)
    
    return image

def map_pixels_to_ascii(image, char_set=None):
    """Convert pixel brightness values to ASCII characters"""
    if char_set is None:
        char_set = ASCII_CHARS
    
    pixels = list(image.getdata())
    width = image.width
    
    # Number of ASCII characters minus 1 for zero-indexing
    num_chars = len(char_set) - 1
    
    ascii_rows = []
    for i in range(0, len(pixels), width):
        row_pixels = pixels[i:i+width]
        # Map each pixel to an ASCII character (darker pixels get denser characters)
        row_chars = [char_set[min(int((255 - pixel) * num_chars / 255), num_chars)] for pixel in row_pixels]
        ascii_rows.append(''.join(row_chars))
    
    return '\n'.join(ascii_rows)

def img_to_ascii(image_path, new_width=300, char_set=None):
    """Convert image to high-quality ASCII art"""
    try:
        # Open and process image
        image = Image.open(image_path)
        
        # Resize the image to desired width while maintaining aspect ratio
        image = resize_image(image, new_width)
        
        # Apply enhancements
        image = enhance_image(image)
        
        # Convert to grayscale
        image = image.convert('L')
        
        # Map pixels to ASCII characters
        ascii_art = map_pixels_to_ascii(image, char_set)
        
        return ascii_art
    except Exception as e:
        print(f"Error converting image to ASCII: {str(e)}")
        traceback.print_exc()
        return "Error: Failed to convert image to ASCII art."

def resize_and_enhance_image(image_path):
    """Prepare an image for color ASCII display"""
    try:
        # Open the image
        image = Image.open(image_path)
        
        # Enhance image quality
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.3)
        
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)
        
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.2)
        
        # Save the enhanced image to a temporary file
        temp_path = os.path.join(SCRIPT_DIR, 'temp_enhanced.png')
        image.save(temp_path)
        
        return temp_path
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        traceback.print_exc()
        return image_path

def get_random_text_effect(screen, phrase, y_pos):
    """Generate a random text effect for the meme phrase with proper parameters"""
    
    # Select a random figlet font (pre-tested to work)
    selected_font = random.choice(FIGLET_FONTS)
    
    # Randomly choose between different text effect types
    effect_type = random.randint(0, 5)
    
    if effect_type == 0:
        # Rainbow effect
        return Print(screen, Rainbow(screen, FigletText(phrase, font=selected_font)), 
                     y_pos, speed=1, start_frame=20)
    
    elif effect_type == 1:
        # Cycle effect (simple version)
        return Cycle(screen, FigletText(phrase, font=selected_font), 
                     y_pos)
    
    elif effect_type == 2:
        # Fire effect
        return Print(screen, Fire(screen.height, screen.width, FigletText(phrase, font=selected_font), 0.4, 30, 
                     screen.colours), y_pos, speed=1, transparent=False)
    
    elif effect_type == 3:
        # Speech bubble
        bubble_type = random.choice(["l", "r"])  # Only use left and right bubbles
        return Print(screen, SpeechBubble(phrase, bubble_type), 
                     y_pos)
    
    elif effect_type == 4:
        # Box effect
        # Create a box with the phrase, no width/height params to avoid conflict
        return Print(screen, Box(phrase), y_pos)
    
    else:
        # Default to Rainbow with different font
        return Print(screen, Rainbow(screen, FigletText(phrase, font=selected_font)), 
                     y_pos, speed=1, start_frame=20)

def generate_meme(screen):
    global meme_generated, current_meme
    meme_generated = True
    
    # Select random image and phrase
    image = random.choice(images)
    phrase = random.choice(phrases)
    current_meme = (image, phrase)
    
    # Generate ASCII art based on screen width (limited to 300 for quality)
    screen_width = min(300, screen.width - 4)
    image_path = os.path.join(IMAGES_DIR, image)
    
    # Decide between ASCII art and color image
    use_color = random.choice([True, False])
    
    if use_color:
        # Use color image
        max_height = screen.height - 10  # Leave room for text
        enhanced_path = resize_and_enhance_image(image_path)
        image_effect = Print(screen,
                         ColourImageFile(screen, enhanced_path, height=max_height, 
                                       uni=screen.unicode_aware, dither=screen.unicode_aware),
                         0)
    else:
        # Use ASCII art with random character set
        char_set = random.choice(ALT_CHARS)
        ascii_art = img_to_ascii(image_path, new_width=screen_width, char_set=char_set)
        image_effect = Print(screen, StaticRenderer(images=[ascii_art]), 0, 
                         colour=Screen.COLOUR_WHITE, bg=Screen.COLOUR_BLACK)
    
    # Create a random text effect for the phrase
    text_effect = get_random_text_effect(screen, phrase, screen.height - 10)
    
    # Add some pizzazz - occasional background effects
    effects = [image_effect, text_effect]
    
    # 30% chance to add fireworks
    if random.random() < 0.3:
        for _ in range(random.randint(1, 3)):
            firework_types = [StarFirework, RingFirework]
            effects.append(random.choice(firework_types)(screen,
                                              random.randint(0, screen.width),
                                              random.randint(screen.height // 3, screen.height * 2 // 3),
                                              random.randint(20, 30),
                                              start_frame=random.randint(0, 50)))
    
    # 20% chance to add stars
    if random.random() < 0.2:
        effects.append(Stars(screen, screen.width))
    
    scene = Scene(effects, -1)  # -1 means the scene will stay on screen
    screen.play([scene], stop_on_resize=True, repeat=False)
    
    # Clean up temporary file if created
    if use_color:
        try:
            temp_path = os.path.join(SCRIPT_DIR, 'temp_enhanced.png')
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            print(f"Error removing temporary file: {str(e)}")

def meme_loop():
    while True:
        try:
            Screen.wrapper(generate_meme)
            break
        except ResizeScreenError:
            pass
        except Exception as e:
            print(f"Error in meme loop: {str(e)}")
            traceback.print_exc()
            break

def on_generate_meme():
    meme_loop()

def on_save_meme():
    global current_meme
    if not meme_generated or not current_meme:
        messagebox.showinfo("Info", "Please generate a meme first.")
        return
    
    image, phrase = current_meme
    save_path = os.path.join(GEN_IMAGES_DIR, f"meme_{random.randint(1000, 9999)}.txt")
    
    # Generate high-resolution ASCII art for saving
    image_path = os.path.join(IMAGES_DIR, image)
    
    # Try different character sets and choose the best one
    best_art = None
    best_score = 0
    
    for char_set in ALT_CHARS:
        ascii_art = img_to_ascii(image_path, new_width=300, char_set=char_set)
        # Score based on character variety and line count
        score = len(set(ascii_art)) * ascii_art.count('\n')
        if score > best_score:
            best_score = score
            best_art = ascii_art
    
    if not best_art:
        # Fallback to default character set
        best_art = img_to_ascii(image_path, new_width=300)
    
    meme_info = f"Image: {image}\nPhrase: {phrase}\n\n{best_art}"
    
    try:
        print(f"Attempting to save meme to: {save_path}")
        
        with open(save_path, 'w') as f:
            f.write(meme_info)
        
        print("File written successfully")
        
        pyperclip.copy(meme_info)
        
        print("Copied to clipboard")
        
        messagebox.showinfo("Success", f"Awesome retro meme saved to {save_path} and copied to clipboard!")
    except Exception as e:
        error_message = f"Failed to save meme: {str(e)}\n"
        error_message += f"Current working directory: {os.getcwd()}\n"
        error_message += f"GEN_IMAGES_DIR: {GEN_IMAGES_DIR}\n"
        error_message += f"Does GEN_IMAGES_DIR exist? {os.path.exists(GEN_IMAGES_DIR)}\n"
        error_message += "Traceback:\n" + traceback.format_exc()
        print(error_message)  # Print to console for debugging
        messagebox.showerror("Error", error_message)

def on_quit():
    window.quit()
    window.destroy()
    sys.exit()

# Create main window
window = Tk()
window.title("Trump Meme Generator - RETRO POP EDITION")
window.configure(bg="black")

# Load and display splash image
try:
    splash_image = PhotoImage(file=os.path.join(SCRIPT_DIR, "trumpsplash.gif"))
    Label(window, image=splash_image, bg="black").pack(pady=10)
except Exception as e:
    print(f"Error loading splash image: {str(e)}")
    Label(window, text="Trump Meme Generator", font=("Arial", 20), fg="white", bg="black").pack(pady=20)

# Create buttons with more exciting text
Button(window, text="GENERATE AWESOME MEME!", command=on_generate_meme, width=25, 
       bg="yellow", fg="black", font=("Arial", 10, "bold")).pack(pady=5)
Button(window, text="SAVE THIS MASTERPIECE", command=on_save_meme, width=25,
       bg="lime", fg="black", font=("Arial", 10, "bold")).pack(pady=5)
Button(window, text="EXIT (but why would you?)", command=on_quit, width=25,
       bg="red", fg="white", font=("Arial", 10, "bold")).pack(pady=5)

if __name__ == "__main__":
    window.mainloop()

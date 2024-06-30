import os
import sys
import random
import pyperclip
import traceback
from tkinter import *
from tkinter import messagebox
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Print
from asciimatics.renderers import FigletText, Rainbow, StaticRenderer
from asciimatics.exceptions import ResizeScreenError
from PIL import Image

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

# ASCII characters from dark to light
ASCII_CHARS = '@%#*+=-:. '

def resize_image(image, new_width=80):
    width, height = image.size
    ratio = height / width / 2  # Divide by 2 to account for terminal character aspect ratio
    new_height = int(new_width * ratio)
    resized_image = image.resize((new_width, new_height))
    return resized_image

def rgb_to_ansi_color(r, g, b):
    # Convert RGB to the closest ANSI color (0-15)
    ansi = 16 + (36 * (r // 51)) + (6 * (g // 51)) + (b // 51)
    return ansi

def pixel_to_ascii(pixel):
    r, g, b = pixel
    brightness = (r + g + b) / 3
    ascii_char = ASCII_CHARS[min(int(brightness // 25), len(ASCII_CHARS) - 1)]
    return ascii_char, rgb_to_ansi_color(r, g, b)

def img_to_ascii_color(image_path, new_width=80):
    image = Image.open(image_path)
    image = resize_image(image, new_width)
    
    ascii_chars = []
    for y in range(image.height):
        for x in range(image.width):
            pixel = image.getpixel((x, y))
            ascii_chars.append(pixel_to_ascii(pixel))
        ascii_chars.append(('\n', 0))  # New line at the end of each row
    
    return ascii_chars

def generate_meme(screen):
    global meme_generated, current_meme
    meme_generated = True
    
    # Select random image and phrase
    image = random.choice(images)
    phrase = random.choice(phrases)
    current_meme = (image, phrase)
    
    # Generate color ASCII art
    image_path = os.path.join(IMAGES_DIR, image)
    ascii_art = img_to_ascii_color(image_path, new_width=min(80, screen.width))
    
    # Create scene
    effects = [
        Print(screen, StaticRenderer(images=[ascii_art]), 0, 
              colour_map=True),
        Print(screen,
              Rainbow(screen, FigletText(phrase, font='small')),
              screen.height - 5,  # Position text closer to the bottom
              speed=1,
              start_frame=20)
    ]
    
    scene = Scene(effects, -1)  # -1 means the scene will stay on screen
    screen.play([scene], stop_on_resize=True, repeat=False)

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
    global current_meme
    if not meme_generated or not current_meme:
        messagebox.showinfo("Info", "Please generate a meme first.")
        return
    
    image, phrase = current_meme
    save_path = os.path.join(GEN_IMAGES_DIR, f"meme_{random.randint(1000, 9999)}.txt")
    
    meme_info = f"Image: {image}\nPhrase: {phrase}"
    
    try:
        print(f"Attempting to save meme to: {save_path}")
        
        with open(save_path, 'w') as f:
            f.write(meme_info)
        
        print("File written successfully")
        
        pyperclip.copy(meme_info)
        
        print("Copied to clipboard")
        
        messagebox.showinfo("Success", f"Meme info saved to {save_path} and copied to clipboard.")
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
window.title("Trump Meme Generator")
window.configure(bg="black")

# Load and display splash image
splash_image = PhotoImage(file="trumpsplash.gif")
Label(window, image=splash_image, bg="black").pack(pady=10)

# Create buttons
Button(window, text="Generate Meme", command=on_generate_meme, width=20).pack(pady=5)
Button(window, text="Save Meme", command=on_save_meme, width=20).pack(pady=5)
Button(window, text="Quit", command=on_quit, width=20).pack(pady=5)

window.mainloop()
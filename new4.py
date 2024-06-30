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
from asciimatics.renderers import ColourImageFile, FigletText, Rainbow
from asciimatics.exceptions import ResizeScreenError

# Directories and files
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(SCRIPT_DIR, 'trump_pics')
GEN_IMAGES_DIR = os.path.join(SCRIPT_DIR, 'genImages')
PHRASES_FILE = os.path.join(SCRIPT_DIR, 'phrases.txt')

# Ensure genImages directory exists
os.makedirs(GEN_IMAGES_DIR, exist_ok=True)

# Load images and phrases
images = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith('.jpg')]
with open(PHRASES_FILE, 'r') as f:
    phrases = [line.strip() for line in f]

# Global variables
meme_generated = False
current_meme = None

def generate_meme(screen):
    global meme_generated, current_meme
    meme_generated = True
    
    # Select random image and phrase
    image = random.choice(images)
    phrase = random.choice(phrases)
    current_meme = (image, phrase)
    
    # Calculate the best image dimensions
    max_height = screen.height - 10  # Leave more space for text
    image_path = os.path.join(IMAGES_DIR, image)
    
    # Create scene
    effects = [
        Print(screen,
              ColourImageFile(screen, image_path, height=max_height, 
                              uni=screen.unicode_aware, dither=False),
              0,
              speed=1),
        Print(screen,
              Rainbow(screen, FigletText(phrase, font='slant')),
              screen.height - 10,  # Position text at the bottom
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
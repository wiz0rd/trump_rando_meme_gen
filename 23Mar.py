import os
import sys
import random
import pyperclip
import traceback
from tkinter import *
from tkinter import messagebox, font
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Print, Cycle, Stars, Matrix
from asciimatics.renderers import FigletText, SpeechBubble, Rainbow, ColourImageFile, ImageFile
from asciimatics.particles import RingFirework, StarFirework
from asciimatics.exceptions import ResizeScreenError

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

# Available figlet fonts that are guaranteed to work
FIGLET_FONTS = [
    'big', 'small', 'standard'
]

def get_text_effect(screen, phrase, y_pos):
    """Generate a random text effect for the meme phrase"""
    # Select a random figlet font
    selected_font = random.choice(FIGLET_FONTS)
    
    # Randomly choose between text effects
    effect_type = random.randint(0, 2)
    
    # Create text renderers
    figlet_text = FigletText(phrase, font=selected_font)
    
    if effect_type == 0:
        # Rainbow effect
        return Print(screen, Rainbow(screen, figlet_text), y_pos, speed=1)
    elif effect_type == 1:
        # Cycle effect (simple)
        return Cycle(screen, figlet_text, y_pos)
    else:
        # Speech bubble
        bubble_type = random.choice(["l", "r"])
        return Print(screen, SpeechBubble(phrase, bubble_type), y_pos)

def extract_ascii_art(text_renderer):
    """Extract ASCII art from a renderer's output"""
    art_lines = []
    try:
        # Get the rendered text
        rendered = text_renderer.rendered_text
        
        # Extract just the characters
        for line in rendered:
            art_line = ''.join(char for char, _, _ in line)
            art_lines.append(art_line)
        
        return '\n'.join(art_lines)
    except Exception as e:
        print(f"Error extracting ASCII art: {e}")
        traceback.print_exc()
        return "[Error extracting ASCII art]"

def generate_meme(screen):
    global meme_generated, current_meme
    meme_generated = True
    
    # Select random image and phrase
    image = random.choice(images)
    phrase = random.choice(phrases)
    
    # Set up image path
    image_path = os.path.join(IMAGES_DIR, image)
    
    # Decide between ASCII art and color image
    use_color = random.choice([True, False])
    
    try:
        if use_color:
            # Use color image
            max_height = screen.height - 10
            image_renderer = ColourImageFile(screen, image_path, height=max_height, 
                                          uni=screen.unicode_aware, dither=screen.unicode_aware)
        else:
            # Use black and white ASCII art
            max_height = screen.height - 10
            image_renderer = ImageFile(image_path, height=max_height, 
                                    colours=screen.colours, 
                                    uni=screen.unicode_aware,
                                    dither=screen.unicode_aware)
        
        # Create image effect
        image_effect = Print(screen, image_renderer, 0)
        
        # Create text effect
        text_effect = get_text_effect(screen, phrase, screen.height - 10)
        
        # Add background effects (sometimes)
        effects = [image_effect, text_effect]
        
        if random.random() < 0.3:
            # Matrix effect
            effects.append(Matrix(screen, stop_frame=200))
        
        if random.random() < 0.3:
            # Stars
            effects.append(Stars(screen, screen.width))
        
        if random.random() < 0.2:
            # Fireworks
            for _ in range(random.randint(1, 3)):
                effects.append(StarFirework(screen,
                                         random.randint(0, screen.width),
                                         random.randint(screen.height // 3, screen.height * 2 // 3),
                                         random.randint(20, 30),
                                         start_frame=random.randint(0, 50)))
        
        # Create and play the scene
        scene = Scene(effects, -1)
        screen.play([scene], stop_on_resize=True, repeat=False)
        
        # Store current meme info
        current_meme = (image, phrase, not use_color)
        
    except Exception as e:
        print(f"Error in generate_meme: {e}")
        traceback.print_exc()

def meme_loop():
    while True:
        try:
            Screen.wrapper(generate_meme)
            break
        except ResizeScreenError:
            pass
        except Exception as e:
            print(f"Error in meme loop: {e}")
            traceback.print_exc()
            break

def create_ascii_art(filename, height=40):
    """Create ASCII art for a file using asciimatics ImageFile renderer"""
    # Create a new renderer just for saving
    try:
        renderer = ImageFile(filename, height=height, colours=8, 
                           uni=False, dither=True)
        
        # Extract the ASCII art
        result = extract_ascii_art(renderer)
        return result
    except Exception as e:
        print(f"Error creating ASCII art: {e}")
        traceback.print_exc()
        return f"[Error creating ASCII art for {os.path.basename(filename)}]"

def on_generate_meme():
    meme_loop()

def on_save_meme():
    global current_meme
    if not meme_generated or not current_meme:
        messagebox.showinfo("Info", "Please generate a meme first.")
        return
    
    image, phrase, was_ascii = current_meme
    save_path = os.path.join(GEN_IMAGES_DIR, f"meme_{random.randint(1000, 9999)}.txt")
    
    try:
        # Generate ASCII art with asciimatics
        image_path = os.path.join(IMAGES_DIR, image)
        ascii_art = create_ascii_art(image_path, height=40)
        
        # Create full meme text
        meme_info = f"Image: {image}\nPhrase: {phrase}\n\n{ascii_art}"
        
        # Save to file
        with open(save_path, 'w') as f:
            f.write(meme_info)
        
        # Copy to clipboard
        pyperclip.copy(meme_info)
        
        messagebox.showinfo("Success", f"NINJA MEME saved to {save_path} and copied to clipboard!")
    except Exception as e:
        error_message = f"Failed to save meme: {str(e)}"
        print(error_message)
        traceback.print_exc()
        messagebox.showerror("Error", error_message)

def on_quit():
    window.quit()
    window.destroy()
    sys.exit()

# Create main window
window = Tk()
window.title("TRUMP MEME GENERATOR - ASCIIMATICS EDITION")
window.configure(bg="black")

# Try to load Comic Sans font
try:
    comic_sans = font.Font(family="Comic Sans MS", size=12, weight="bold")
except:
    comic_sans = font.Font(size=12, weight="bold")

# Load splash image
try:
    splash_image = PhotoImage(file=os.path.join(SCRIPT_DIR, "trumpsplash.gif"))
    Label(window, image=splash_image, bg="black").pack(pady=10)
except Exception as e:
    print(f"Error loading splash image: {e}")
    Label(window, text="TRUMP MEME GENERATOR", 
          font=comic_sans, fg="#8A2BE2", bg="black").pack(pady=20)

# Create buttons
Button(window, text="GENERATE MEME!", command=on_generate_meme, width=25, 
       bg="#FFD700", fg="black", font=comic_sans).pack(pady=5)
       
Button(window, text="SAVE THIS MASTERPIECE", command=on_save_meme, width=25,
       bg="#9932CC", fg="white", font=comic_sans).pack(pady=5)
       
Button(window, text="EXIT", command=on_quit, width=25,
       bg="#FF1493", fg="white", font=comic_sans).pack(pady=5)

if __name__ == "__main__":
    window.mainloop()

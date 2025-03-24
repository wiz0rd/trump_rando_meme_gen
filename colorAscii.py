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
from asciimatics.renderers import FigletText, Rainbow, ColourImageFile
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

# Optimal character set for saving to file
ASCII_CHARS = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "

def resize_and_enhance_image(image_path, new_height=None):
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

def generate_ascii_art_for_saving(image_path, width=300):
    """Generate high-quality ASCII art for saving to file"""
    try:
        # Open and process image
        image = Image.open(image_path)
        
        # Resize the image to desired width while maintaining aspect ratio
        orig_width, orig_height = image.size
        ratio = orig_height / orig_width / 1.8  # Terminal characters are about 1.8x taller than wide
        height = int(width * ratio)
        resized_image = image.resize((width, height), Image.LANCZOS)
        
        # Apply enhancements for better quality
        resized_image = ImageOps.autocontrast(resized_image, cutoff=0.5)
        
        enhancer = ImageEnhance.Contrast(resized_image)
        enhanced_image = enhancer.enhance(1.5)
        
        enhancer = ImageEnhance.Sharpness(enhanced_image)
        enhanced_image = enhancer.enhance(1.3)
        
        # Convert to grayscale
        gray_image = enhanced_image.convert('L')
        
        # Map pixels to ASCII characters
        pixels = list(gray_image.getdata())
        char_count = len(ASCII_CHARS) - 1
        
        ascii_art = []
        for i in range(0, len(pixels), width):
            row_pixels = pixels[i:i+width]
            # Map pixel values to ASCII chars (invert so darker pixels get denser chars)
            row_chars = [ASCII_CHARS[min(int((255 - pixel) * char_count / 255), char_count)] for pixel in row_pixels]
            ascii_art.append(''.join(row_chars))
        
        return '\n'.join(ascii_art)
    except Exception as e:
        print(f"Error generating ASCII art: {str(e)}")
        traceback.print_exc()
        return "Error generating ASCII art."

def generate_meme(screen):
    global meme_generated, current_meme
    meme_generated = True
    
    # Select random image and phrase
    image = random.choice(images)
    phrase = random.choice(phrases)
    current_meme = (image, phrase)
    
    # Calculate the best image height based on screen size
    max_height = screen.height - 10  # Leave room for text
    image_path = os.path.join(IMAGES_DIR, image)
    
    # Enhance image for better display
    enhanced_path = resize_and_enhance_image(image_path)
    
    # Create scene with color image and phrase using built-in ColourImageFile renderer
    effects = [
        Print(screen,
              ColourImageFile(screen, enhanced_path, height=max_height, 
                            uni=screen.unicode_aware, dither=screen.unicode_aware),
              0),
        Print(screen,
              Rainbow(screen, FigletText(phrase, font='small')),
              screen.height - 8,  # Position text near the bottom
              speed=1,
              start_frame=20)
    ]
    
    scene = Scene(effects, -1)  # -1 means the scene will stay on screen
    screen.play([scene], stop_on_resize=True, repeat=False)
    
    # Clean up temporary file
    try:
        if enhanced_path != image_path and os.path.exists(enhanced_path):
            os.remove(enhanced_path)
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
    
    # Generate high-quality ASCII art for saving
    image_path = os.path.join(IMAGES_DIR, image)
    ascii_art = generate_ascii_art_for_saving(image_path, width=300)  # 300 width as specified
    
    meme_info = f"Image: {image}\nPhrase: {phrase}\n\n{ascii_art}"
    
    try:
        print(f"Attempting to save meme to: {save_path}")
        
        with open(save_path, 'w') as f:
            f.write(meme_info)
        
        print("File written successfully")
        
        pyperclip.copy(meme_info)
        
        print("Copied to clipboard")
        
        messagebox.showinfo("Success", f"Meme saved to {save_path} and copied to clipboard.")
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
window.title("Trump Meme Generator - Color")
window.configure(bg="black")

# Load and display splash image
try:
    splash_image = PhotoImage(file=os.path.join(SCRIPT_DIR, "trumpsplash.gif"))
    Label(window, image=splash_image, bg="black").pack(pady=10)
except Exception as e:
    print(f"Error loading splash image: {str(e)}")
    Label(window, text="Trump Meme Generator", font=("Arial", 20), fg="white", bg="black").pack(pady=20)

# Create buttons
Button(window, text="Generate Meme", command=on_generate_meme, width=20).pack(pady=5)
Button(window, text="Save Meme", command=on_save_meme, width=20).pack(pady=5)
Button(window, text="Quit", command=on_quit, width=20).pack(pady=5)

if __name__ == "__main__":
    window.mainloop()

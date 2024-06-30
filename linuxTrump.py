import os
import sys
import random
import pyperclip
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Print
from asciimatics.renderers import FigletText, Rainbow, StaticRenderer
from asciimatics.exceptions import ResizeScreenError, StopApplication
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

# ASCII characters from dark to light
ASCII_CHARS = '@%#*+=-:. '

def resize_image(image, new_width=80):
    width, height = image.size
    ratio = height / width / 2  # Divide by 2 to account for terminal character aspect ratio
    new_height = int(new_width * ratio)
    resized_image = image.resize((new_width, new_height))
    return resized_image

def rgb_to_ansi_color(r, g, b):
    # Convert RGB to the closest ANSI color (0-255)
    return 16 + (36 * (r // 51)) + (6 * (g // 51)) + (b // 51)

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

class MemeGenerator(Scene):
    def __init__(self, screen):
        self.screen = screen
        self.current_meme = None
        self.generate_meme()
        super(MemeGenerator, self).__init__([])

    def generate_meme(self):
        # Select random image and phrase
        image = random.choice(images)
        phrase = random.choice(phrases)
        self.current_meme = (image, phrase)
        
        # Generate color ASCII art
        image_path = os.path.join(IMAGES_DIR, image)
        ascii_art = img_to_ascii_color(image_path, new_width=min(80, self.screen.width))
        
        # Create effects
        self.effects = [
            Print(self.screen, StaticRenderer(images=[ascii_art]), 0, 
                  colour_map=True),
            Print(self.screen,
                  Rainbow(self.screen, FigletText(phrase, font='small')),
                  self.screen.height - 5,  # Position text closer to the bottom
                  speed=1,
                  start_frame=20)
        ]

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code == ord(' '):
                self.generate_meme()
                raise NextScene("Meme")
            elif event.key_code in (ord('S'), ord('s')):
                self.save_meme()
            elif event.key_code in (ord('Q'), ord('q')):
                raise StopApplication("User quit")
        return super(MemeGenerator, self).process_event(event)

    def save_meme(self):
        if not self.current_meme:
            return
        
        image, phrase = self.current_meme
        save_path = os.path.join(GEN_IMAGES_DIR, f"meme_{random.randint(1000, 9999)}.txt")
        
        meme_info = f"Image: {image}\nPhrase: {phrase}"
        
        try:
            with open(save_path, 'w') as f:
                f.write(meme_info)
            
            pyperclip.copy(meme_info)
            
            self.screen.print_at(f"Meme saved to {save_path} and copied to clipboard!",
                                 0, self.screen.height - 1)
        except Exception as e:
            self.screen.print_at(f"Failed to save meme: {str(e)}",
                                 0, self.screen.height - 1)

def main(screen):
    scenes = [
        Scene([MemeGenerator(screen)], -1, name="Meme")
    ]
    
    screen.play(scenes, stop_on_resize=True, start_scene=scenes[0])

if __name__ == "__main__":
    while True:
        try:
            Screen.wrapper(main)
            break
        except ResizeScreenError:
            pass
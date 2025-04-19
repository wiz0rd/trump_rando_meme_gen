import os
import sys
import random
import pyperclip
import traceback
from tkinter import *
from tkinter import messagebox, font
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Print, Cycle, Stars, Matrix, BannerText, Scroll, Snow
from asciimatics.renderers import FigletText, SpeechBubble, Rainbow, ColourImageFile, ImageFile
from asciimatics.renderers import Fire, StaticRenderer
from asciimatics.particles import RingFirework, StarFirework, Explosion
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

# Color selection for text effects
fore_select = [195, 255, 201, 51, 171, 202, 163, 213]  # Added more bright colors
back_select = [200, 14, 0, 4, 54, 19, 55, 91]  # Added more background options

# Available figlet fonts that are guaranteed to work
FIGLET_FONTS = [
    'big', 'small', 'standard', 'banner', 'slant'
]

# Try to add 'usaflag' font if available
try:
    test = FigletText("Test", font='usaflag')
    FIGLET_FONTS.append('usaflag')
except Exception:
    pass

def create_edge_fire_effect(screen, phrase):
    """Create a fire effect around the edges"""
    try:
        # Create a fire pattern that surrounds the edges
        width = screen.width
        fire_pattern = ""
        
        # Top edge
        fire_pattern += "#" * width + "\n"
        
        # Middle - empty except for sides
        for _ in range(10):
            fire_pattern += "#" + " " * (width - 2) + "#\n"
        
        # Bottom edge
        fire_pattern += "#" * width + "\n"
        
        # Create a fire renderer with the edge pattern
        return Fire(
            screen.height,     # Full height
            width,             # Full width  
            fire_pattern,      # Edge pattern
            1.0,               # Maximum intensity
            150,               # Very hot spots
            screen.colours,    # Use all available colors
            bg=False           # Don't render background colors only
        )
    except Exception as e:
        print(f"Edge fire effect failed: {e}")
        traceback.print_exc()
        return None

def create_bottom_fire_effect(screen, phrase):
    """Create a fire effect at the bottom"""
    try:
        # Create a fire pattern for the bottom
        width = screen.width
        fire_pattern = ""
        
        # Create a thick line of fire source at the bottom
        for _ in range(3):
            fire_pattern += "#" * width + "\n"
        
        # Create a fire renderer with the bottom pattern
        return Fire(
            15,                # Height of fire
            width,             # Full width
            fire_pattern,      # Bottom pattern
            1.0,               # Maximum intensity
            200,               # Extra hot spots
            screen.colours,    # Use all available colors
            bg=False           # Don't render background colors only
        )
    except Exception as e:
        print(f"Bottom fire effect failed: {e}")
        traceback.print_exc()
        return None

def create_text_outline_fire(screen, phrase):
    """Create a fire effect that outlines text"""
    try:
        # First, render the figlet text to a string to get the pattern
        figlet = FigletText(phrase, font=random.choice(FIGLET_FONTS))
        
        # Get the rendered text from the figlet renderer
        rendered_text = figlet.rendered_text
        
        # Convert the rendered_text to a plain string for the fire emitter
        emitter_lines = []
        for line in rendered_text:
            emitter_line = ''.join('#' if c != ' ' else ' ' for c, _, _ in line)
            emitter_lines.append(emitter_line)
        
        emitter_text = '\n'.join(emitter_lines)
        
        # Create the fire renderer with the text outline
        return Fire(
            screen.height // 3,  # Height of fire box
            screen.width,        # Width of fire box
            emitter_text,        # Heat source (text outline)
            1.0,                 # Maximum intensity
            200,                 # Very hot spots for brightness
            screen.colours,      # Use all available colors
            bg=False             # Don't render background colors only
        )
    except Exception as e:
        print(f"Text outline fire failed: {e}")
        traceback.print_exc()
        return None

def create_rain_effect(screen):
    """Create a custom rain effect using falling characters"""
    try:
        # We'll create a class to handle the rain effect
        class RainEffect(Print):
            def __init__(self, screen):
                # Initialize raindrops as an empty list
                self._raindrops = []
                self._screen = screen
                self._rate = random.randint(10, 25)  # More drops per frame
                self._frame = 0
                # Initialize with an empty renderer to avoid errors
                super().__init__(screen, StaticRenderer([""]), 0)
            
            def _update(self, frame_no):
                self._frame += 1
                
                # Add new raindrops periodically
                if self._frame % 2 == 0:
                    for _ in range(self._rate):
                        x = random.randint(0, self._screen.width - 1)
                        # Each raindrop has x, y, character, and color
                        raindrop_char = random.choice("|/\\'.`~!;:,")
                        raindrop_color = random.choice([
                            Screen.COLOUR_CYAN, 
                            Screen.COLOUR_BLUE,
                            Screen.COLOUR_WHITE
                        ])
                        self._raindrops.append([x, 0, raindrop_char, raindrop_color])
                
                # Move existing raindrops down and draw them
                for drop in self._raindrops[:]:
                    x, y, char, color = drop
                    # Draw the raindrop
                    self._screen.print_at(char, x, y, color, 0)
                    # Move it down
                    drop[1] += 1
                    # Remove if it's off screen
                    if drop[1] >= self._screen.height:
                        self._raindrops.remove(drop)
        
        return RainEffect(screen)
    except Exception as e:
        print(f"Rain effect failed: {e}")
        return None

def create_snow_effect_enhanced(screen):
    """Create an enhanced snow effect"""
    try:
        return Snow(screen, count=200)  # Double the snowflakes
    except Exception as e:
        print(f"Enhanced snow effect failed: {e}")
        return None

def generate_meme(screen):
    """Generate a meme using asciimatics rendering with multiple scenes"""
    global meme_generated, current_meme
    
    # Select random image and phrase
    image = random.choice(images)
    phrase = random.choice(phrases)
    current_meme = (image, phrase)
    meme_generated = True
    
    # Set up image path
    image_path = os.path.join(IMAGES_DIR, image)
    
    # Create multiple scenes for different display styles
    scenes = []
    
    print("Creating Scene 1: B&W ASCII Art")
    # Scene 1: Black and White ASCII Art with text banner
    font_choice = random.choice(FIGLET_FONTS)
    effects1 = [
        Print(screen, ImageFile(image_path, screen.height - 10, colours=screen.colours),
              0),
        Print(screen,
              FigletText(phrase, font=font_choice),
              screen.height - 8,
              colour=random.choice(fore_select))
    ]
    scenes.append(Scene(effects1))
    
    print("Creating Scene 2: Color Version")
    # Scene 2: Color version with fancy text
    font_choice = random.choice(FIGLET_FONTS)
    color_choice = random.choice(fore_select)
    bg_choice = random.choice(back_select)
    
    effects2 = [
        Print(screen,
              ColourImageFile(screen, image_path, screen.height-10,
                            uni=screen.unicode_aware,
                            dither=screen.unicode_aware),
              0),
        Print(screen,
              FigletText(phrase, font=font_choice),
              screen.height-8,
              colour=color_choice, bg=bg_choice if screen.unicode_aware else 0)
    ]
    scenes.append(Scene(effects2))
    
    print("Creating Scene 3: Edge Fire Effect")
    # Scene 3: Edge Fire effect
    edge_fire = create_edge_fire_effect(screen, phrase)
    
    if edge_fire:
        effects3 = [
            Print(screen,
                 ColourImageFile(screen, image_path, screen.height-10,
                               uni=screen.unicode_aware,
                               dither=screen.unicode_aware),
                 0),
            Print(screen, edge_fire, 0),  # Place fire at the edges
            Print(screen,
                 FigletText(phrase, font=random.choice(FIGLET_FONTS)),
                 screen.height - 8,
                 colour=Screen.COLOUR_RED)
        ]
        scenes.append(Scene(effects3))
        print("Edge fire effect created successfully")
    
    print("Creating Scene 4: Bottom Fire Effect")
    # Scene 4: Bottom Fire effect
    bottom_fire = create_bottom_fire_effect(screen, phrase)
    
    if bottom_fire:
        effects4 = [
            Print(screen,
                 ColourImageFile(screen, image_path, screen.height-15,
                               uni=screen.unicode_aware,
                               dither=screen.unicode_aware),
                 0),
            Print(screen,
                 FigletText(phrase, font=random.choice(FIGLET_FONTS)),
                 screen.height - 15,
                 colour=Screen.COLOUR_YELLOW),
            Print(screen, bottom_fire, screen.height - 10)  # Place fire at the bottom
        ]
        scenes.append(Scene(effects4))
        print("Bottom fire effect created successfully")
    
    print("Creating Scene 5: Text Outline Fire")
    # Scene 5: Text Outline Fire effect
    text_fire = create_text_outline_fire(screen, phrase)
    
    if text_fire:
        effects5 = [
            Print(screen,
                 ColourImageFile(screen, image_path, screen.height-25,
                               uni=screen.unicode_aware,
                               dither=screen.unicode_aware),
                 0),
            Print(screen, text_fire, screen.height - 20),  # Place fire around text
            Print(screen,
                 FigletText(phrase, font=random.choice(FIGLET_FONTS)),
                 screen.height - 15,
                 colour=Screen.COLOUR_WHITE)
        ]
        scenes.append(Scene(effects5))
        print("Text outline fire effect created successfully")
    
    print("Creating Scene 6: Enhanced Snow Effect")
    # Scene 6: Enhanced Snow effect
    enhanced_snow = create_snow_effect_enhanced(screen)
    
    if enhanced_snow:
        effects6 = [
            Print(screen,
                 ColourImageFile(screen, image_path, screen.height-10,
                               uni=screen.unicode_aware,
                               dither=screen.unicode_aware),
                 0),
            Print(screen,
                 FigletText(phrase, font=random.choice(FIGLET_FONTS)),
                 screen.height-8,
                 colour=Screen.COLOUR_CYAN),
            enhanced_snow
        ]
        scenes.append(Scene(effects6))
        print("Enhanced snow effect created successfully")
    
    print("Creating Scene 7: Enhanced Rain Effect")
    # Scene 7: Enhanced Rain effect
    effects7 = [
        Print(screen,
             ColourImageFile(screen, image_path, screen.height-10,
                           uni=screen.unicode_aware,
                           dither=screen.unicode_aware),
             0),
        Print(screen,
             FigletText(phrase, font=random.choice(FIGLET_FONTS)),
             screen.height-8,
             colour=Screen.COLOUR_BLUE)
    ]
    
    # Try to add rain effect
    rain = create_rain_effect(screen)
    if rain:
        effects7.append(rain)
        scenes.append(Scene(effects7))
        print("Enhanced rain effect created successfully")
    
    print("Creating Scene 8: Ultimate Effects Mix")
    # Scene 8: Ultimate effects mix
    effects8 = [
        Print(screen,
             ColourImageFile(screen, image_path, screen.height-10,
                           uni=screen.unicode_aware,
                           dither=screen.unicode_aware),
             0),
        Print(screen,
             Rainbow(screen, FigletText(phrase, font=random.choice(FIGLET_FONTS))),
             screen.height-8,
             speed=1),
        Stars(screen, screen.width * 2)  # Double the stars
    ]
    
    # Add Matrix effect
    effects8.append(Matrix(screen, stop_frame=100))
    print("Added Matrix effect")
    
    # Add Fireworks for excitement - more of them!
    for _ in range(random.randint(4, 8)):  # Double the fireworks
        firework_type = random.choice([StarFirework, RingFirework])
        effects8.append(firework_type(
            screen,
            random.randint(0, screen.width),
            random.randint(screen.height // 4, screen.height * 3 // 4),
            random.randint(20, 40),  # Bigger explosions
            start_frame=random.randint(0, 100)
        ))
    print("Added enhanced firework effects")
    
    scenes.append(Scene(effects8))
    
    print(f"Created {len(scenes)} scenes total")
    
    # Play all scenes
    screen.play(scenes, stop_on_resize=True)

def extract_ascii_art(image_path, height=40):
    """Extract ASCII art from an image using asciimatics ImageFile"""
    try:
        # Create ImageFile renderer
        renderer = ImageFile(image_path, height=height, colours=8)
        
        # Extract ASCII art from renderer
        ascii_lines = []
        for line in renderer.rendered_text:
            ascii_line = ''.join(char for char, _, _ in line)
            ascii_lines.append(ascii_line)
        
        return '\n'.join(ascii_lines)
    except Exception as e:
        print(f"Error extracting ASCII art: {str(e)}")
        traceback.print_exc()
        return f"[Error extracting ASCII art: {e}]"

def meme_loop():
    """Run the meme generation in a loop, handling screen resize events"""
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
    """Button handler for generating memes"""
    meme_loop()

def on_save_meme():
    """Button handler for saving memes"""
    global current_meme, meme_generated
    
    if not meme_generated or not current_meme:
        messagebox.showinfo("Info", "Please generate a meme first!")
        return
    
    image, phrase = current_meme
    save_path = os.path.join(GEN_IMAGES_DIR, f"meme_{random.randint(1000, 9999)}.txt")
    
    try:
        # Generate ASCII art from the image
        image_path = os.path.join(IMAGES_DIR, image)
        ascii_art = extract_ascii_art(image_path, height=40)
        
        # Create complete meme content
        meme_content = f"Image: {image}\nPhrase: {phrase}\n\n{ascii_art}"
        
        # Save to file
        with open(save_path, 'w') as f:
            f.write(meme_content)
        
        # Copy to clipboard
        pyperclip.copy(meme_content)
        
        messagebox.showinfo("Success", f"EPIC MEME saved to {save_path} and copied to clipboard!")
    except Exception as e:
        error_msg = f"Error saving meme: {e}"
        print(error_msg)
        traceback.print_exc()
        messagebox.showerror("Error", error_msg)

def on_quit():
    """Button handler for exiting"""
    window.destroy()
    sys.exit()

# Create main window with custom styling
window = Tk()
window.title("ULTIMATE TRUMP MEME GENERATOR 9000")
window.configure(bg="black")

# Try to load Comic Sans font for extra flashiness
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
    Label(window, text="ULTIMATE TRUMP MEME GENERATOR", 
          font=comic_sans, fg="#8A2BE2", bg="black").pack(pady=20)

# Create buttons with exciting text and Comic Sans-like font
Button(window, text="GENERATE EPIC MEME!", command=on_generate_meme, width=25, 
       bg="#FFD700", fg="black", font=comic_sans).pack(pady=5)
       
Button(window, text="SAVE THIS MASTERPIECE", command=on_save_meme, width=25,
       bg="#9932CC", fg="white", font=comic_sans).pack(pady=5)
       
Button(window, text="EXIT THE MADNESS", command=on_quit, width=25,
       bg="#FF1493", fg="white", font=comic_sans).pack(pady=5)

# Add a cool subtitle
Label(window, text="The coolest meme generator in the known universe", 
      font=("Arial", 8), fg="#00FFFF", bg="black").pack(pady=2)

if __name__ == "__main__":
    window.mainloop()
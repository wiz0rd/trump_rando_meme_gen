import os
import random
from PIL import Image, ImageDraw, ImageFont
import keyboard
import pyperclip

# Define paths
cwd = os.getcwd()
icwd = os.path.join(cwd, 'trump_pics')
gen_images_dir = os.path.join(cwd, 'genImages')
phrases_file = os.path.join(cwd, 'phrases.txt')

if not os.path.exists(gen_images_dir):
    os.makedirs(gen_images_dir)

def generate_meme():
    # Randomly select an image file
    files = [f for f in os.listdir(icwd) if os.path.isfile(os.path.join(icwd, f))]
    selected_file = random.choice(files)
    img_path = os.path.join(icwd, selected_file)
    img = Image.open(img_path)

    # Randomly select a phrase
    with open(phrases_file, 'r') as file:
        phrases = file.readlines()
    phrase = random.choice(phrases).strip()

    # Create a Draw object
    draw = ImageDraw.Draw(img)

    # Specify the font (adjust the path to your font file as necessary)
    font_path = "arial.ttf"  # This path might need to be adjusted
    font_size = 40
    font = ImageFont.truetype(font_path, font_size)

    # Measure the size of the text to be drawn, using the font
    text_width, text_height = draw.textsize(phrase, font=font)

    # Calculate the position for the text
    image_width, image_height = img.size
    x = (image_width - text_width) / 2
    y = image_height - text_height - 10  # Adjust positioning as needed

    # Draw the text onto the image
    draw.text((x, y), phrase, fill="white", font=font)

    return img, selected_file
def save_and_copy_to_clipboard(img, filename):
    save_path = os.path.join(gen_images_dir, filename)
    img.save(save_path)
    pyperclip.copy(save_path)
    print(f"Image saved to {save_path} and path copied to clipboard.")

def main():
    print("Press 'Space' to generate a new meme. Press 's' to save and copy the path to the clipboard.")
    while True:
        if keyboard.is_pressed('space'):
            img, filename = generate_meme()
            img.show()  # Show the image with the phrase rendered on it
            while keyboard.is_pressed('space'):  # Wait for space to be released
                pass
        elif keyboard.is_pressed('s'):
            if 'img' in locals():
                save_and_copy_to_clipboard(img, filename)
                break  # Exit the loop after saving
            else:
                print("Generate a meme first by pressing 'Space'.")
            while keyboard.is_pressed('s'):  # Wait for s to be released
                pass

if __name__ == "__main__":
    main()
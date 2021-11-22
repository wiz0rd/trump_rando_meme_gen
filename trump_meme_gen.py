from __future__ import division
from tkinter import *
import pyperclip
import sys
import os
from asciimatics.effects import BannerText, Print, Scroll
from asciimatics.renderers import ColourImageFile, FigletText, ImageFile
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import random

cwd = os.getcwd()

icwd = os.getcwd() + '/trump_pics/'

images = []

phrase_list = []

for filename in os.listdir(icwd):
    images.append(filename)

with open('phrases.txt', 'r') as f:
    for line in f:
        line = line.rstrip()
        phrase_list.append(line)

def demo(screen):
    image = icwd + random.choice(images)
    scenes = []
    effects = [
        Print(screen, ImageFile(image, screen.height - 2, colours=screen.colours),
              0,
              stop_frame=100),
    ]
    scenes.append(Scene(effects))
    effects = [
        Print(screen,
              ColourImageFile(screen, image, screen.height-2,
                              uni=screen.unicode_aware,
                              dither=screen.unicode_aware),
              0,
              stop_frame=200),
        Print(screen,
              FigletText(random.choice(phrase_list),
                         font='usaflag' if screen.width > 80 else 'banner'),
              screen.height//1-8,
              colour=195, bg=200 if screen.unicode_aware else 0),
    ]
    scenes.append(Scene(effects))
    effects = [
        Print(screen,
              ColourImageFile(screen, image, screen.height,
                              uni=screen.unicode_aware),
              screen.height,
              speed=1,
              stop_frame=(40+screen.height)*3),
        Scroll(screen, 3)
    ]
    scenes.append(Scene(effects))
    effects = [
        BannerText(screen,
                   ColourImageFile(screen, image, screen.height-2,
                                   uni=screen.unicode_aware, dither=screen.unicode_aware),
                   0, 0),
    ]
    scenes.append(Scene(effects))

    screen.play(scenes, stop_on_resize=True)

#Makes a click definition
def click():
    if __name__ == "__main__":
        while True:
            try:
                Screen.wrapper(demo)
                sys.exit(0)
            except ResizeScreenError:
                pass



window = Tk()
window.title("Donald J Trump MEME Generator 1.0")
window.configure(background="black")

# Add a Photo
photo1 = PhotoImage(file="trumpsplash.gif")
Label (window, image=photo1, bg="black") .grid(row=0, column=0, sticky=W)

# Adds a submit button
Button(window, text="SUBMIT", width=6, command=click) .grid(row=3, column=0, sticky=W)

# Defines a Exit Function
def close_window():
    window.destroy()
    exit()

# Defines an Exit Button
Button(window, text="Exit", width=14, command=close_window) .grid(row=7, column=0, sticky=E)

window.mainloop()

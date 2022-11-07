
# Auditorise

*(A submission for a Hackathon on the topic 'Impractical Inventions')*

It is a well-known fact that, today, the world faces a grave threat to its existence.
We all have heard of this crisis at some point or another. It is said to have far-reaching 
implications for all of Earth and its most important fauna. 

It, of course, is increasing screentime.

This app lets you strain your eyes lesser by converting images into audio. With 
_**a bit of**_ practise, you can train yourself to _'see'_ sound.

This can also be used by visually-disabled people to access their computers faster and more 
efficiently. The traditional (TTS) method is far too slow and many applications don't support 
them fully. In contrast, a 256 by 256 RGB image can usually be played back as audio in under 
3 seconds using **_Auditorise_** _(found in informal tests run on a Windows 11 system)_.

The frontend of the app is written in Python and the backend is written in **_COBOL_**.

### Why _COBOL_?

This application was made to be backwards-compatible with as many systems as possible, which 
is why the image-to-audio converter, was written in 
**_COBOL_**. 

This language was chosen because it, till today, retains support for programming on punched-cards. 
As you can expect from a programming language of the name **COmmon Business-Oriented Language**, it
takes backwards-compatibility very seriously.

To add support for a new system, all that is required is to:

1. Buy a **_COBOL_** compiler compatible with that system
2. Wait for the stack of punch-cards containing the compiler and this code to arrive by 
   multiple couriers
3. Buy a card-sorting machine to arrange all the punch cards in the right order
4. Compile [`auditorise-core.cob`](.\backwards-compatible\auditorise-core.cob)
5. Sleep for the night and return next morning to find that the compiler is still running
6. Consult your school / college counsellor for moral and emotional support
7. And then, write a frontend for the application, with the language / framework of _**your**_
   choice!

In case a frontend does not exist for your system, no problem! You can still run it from the 
command-line. You _only_ have to input RGB values for about 65536 (256 * 256) pixels.

Also, the compiled executable must be in [`backwards-compatible/bin/`](.\backwards-compatible\bin)


### About the app

The app has 4 pages:

- **_About Page_**: This file is displayed
- **_From-Camera Page_**: Captures an image from your camera and converts it to audio
- **_From-Screen Page_**: Takes a screenshot and converts it to audio
- **_From-Files Page_**: Convert images (_PNG_, _JPG_, _JPEG_ images) from your system into audio

Keybinds for the app:

- `Alt + a`: Opens **_About Page_**
- `Alt + c`: Opens **_From-Camera Page_**
  - `Alt + space`: Captures image
- `Alt + s`: Opens **_From-Screen Page_**
  - `Alt + space`: Captures image
- `Alt + f`: Opens **_From-Files Page_**
- `Alt + p`: Play / Pause
- `Alt + q`: Quit

The **_COBOL_** backend converts a `(65536, 3)` _numpy_ array (reshaped from `(256, 256, 3)`) passed 
as input in [`backwards-compatible/__inout__/in.txt`](.\backwards-compatible\\__inout__\in.txt) into 
audio and then writes it into 
[`backwards-compatible/__inout__/out.txt`](.\backwards-compatible\\__inout__\out.txt).
It uses a [Hilbert curve](https://en.wikipedia.org/wiki/Hilbert_curve) _(a space-filling curve which 
preserves locality quite well)_ to map a 2-dimensional image into a 1-dimensional space (audio).

After that, the **_COBOL_** program maps the colour value of each pixel to audio.

Because it is hard for a human to learn to distinguish all 256 values of each colour, it has been
divided into 8 bands instead (each spanning a range of 32), which was then written into the output
audio.

The mapping is:

- `RED` to amplitude of the output audio
  - 0 - 8 units of amplitude
  - 0 - 4 units below 0, rest above
- `GREEN` to some kind of [_timbre_](https://en.wikipedia.org/wiki/Timbre), in the output audio
  - 0 - 8 units
  - 1 unit = 1 / 4 of the total amplitude
- `BLUE` to wavelength of the output audio
  - 1 - 8 units of time added

The app resizes all input images to size `(256, 256)`, as Hilbert curves are easiest to implement 
on squares.

The app uses the `tkinter` standard library module for its frontend.

The following packages were used:
- `pillow` to read images from file and manipulate them
- `ttkthemes` for the UI
- `opencv-python` to get input images
- `sounddevice` to play the audio
- `numpy` to manipulate the input image and output audio arrays
- `tkinterweb` to render this MarkDown file, converted to **HTML**, inside the app

### Forwards-compatibility

I have also taken utmost care and forethought in the matter of 
forwards-compatibility _(the opposite of backwards-compatibility)_.
Therefore, I have included a forwards-compatible version in 
[`forwards-compatible/`](.\forwards-compatible). 

It contains a **_PDF_** showing the format of a legal 
["cease-and-desist" letter](.\forwards-compatible\General-Cease-and-Desist-Letter-Template.pdf),
to allow for future mega-corporations to easily sue independent developers like me, and then 
take credit for our work. 

As you can clearly see, I have given a lot of thought into this matter.

_(This **PDF** was taken from 
[eForms.com](https://eforms.com/download/2018/01/General-Cease-and-Desist-Letter-Template.pdf).)_

### Sources & Building from source

This app has only been tested, and built, on Windows.

The frontend for this app is written in Python 3. The dependencies are given in 
[`requirements.txt`](.\backwards-compatible\requirements.txt): 
```commandline
cffi==1.15.0
numpy==1.23.4
opencv-python==4.6.0.66
Pillow==9.3.0
pycparser==2.21
sounddevice==0.4.5
tkinterweb==3.15.6
ttkthemes==3.2.2
```

You can install them by running:
```commandline
pip install -r backwards-compatible\requirements.txt
```

[GNUCobol v2.0.0](https://sourceforge.net/projects/gnucobol/) with 
[OpenCobolIDE v4.7.6](https://pypi.org/project/OpenCobolIDE/) was used to compile the *_COBOL_* code.
This was the command used by the IDE (run over a _POSIX_ compatibility layer):
```commandline
cobc.exe -x -o bin\auditorise-core.exe -std=default -x auditorise-core.cob
```

[pandoc](https://pandoc.org/index.html) was used to convert this MarkDown file into HTML, to display
it in the **_About Page_**:
```commandline
pandoc -s README.md -o .\backwards-compatible\__assets__\converted-README.html
```
You can view the HTML file [here](.\backwards-compatible\\__assets__\converted-README.html).

All other files in [`backwards-compatible/__assets__/`](.\backwards-compatible\\__assets__) are 
original, and made with 
[**_(MS)_** Paint v11.2208.6.0](https://apps.microsoft.com/store/detail/paint/9PCFS5B6T72H) _(Windows 11 version)_.

The **PDF** in 
[`forwards-compatible/`](.\forwards-compatible\General-Cease-and-Desist-Letter-Template.pdf) was
taken from [_eForms.com_](https://eforms.com/download/2018/01/General-Cease-and-Desist-Letter-Template.pdf).

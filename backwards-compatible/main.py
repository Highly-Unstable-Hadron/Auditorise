import subprocess
import tkinter as tk
import tkinter.ttk as ttk
import webbrowser
from tkinter import filedialog, messagebox
import cv2
import numpy as np
import sounddevice
import tkinterweb
import ttkthemes
from PIL import ImageTk, Image, ImageGrab

MINSIZE_X, MINSIZE_Y = 1000, 600
NUM_ROWS, NUM_COLUMNS = 5, 4
APP_ICON = '__assets__/app_title.png'
PLAY_PAUSE_ICONS = ('__assets__/play.png', '__assets__/pause.png')
CAPTURE_PIC_ICON = '__assets__/capture.png'
NAVBAR_ICONS = (('__assets__/camera_unfocused.png', '__assets__/camera_focused.png'),
                ('__assets__/screenshot_unfocused.png', '__assets__/screenshot_focused.png'),
                ('__assets__/file_unfocused.png', '__assets__/file_focused.png'))
STYLE = {
    'bg': 'black',
    'fg': 'red',
    'fg2': 'white'
}
ABOUT_PAGE = r'__assets__/converted-README.html'
SIZES = ((100, 78), (150, 116),  # Not-pressed and pressed sizes for navbar
         (50, 50))  # Play-pause button size

NP_ARRAY_LEN = 256
COBOL_EXECUTABLE = r'.\bin\auditorise-core.exe'
COBOL_INP_FILE = '__inout__/in.txt'
COBOL_OUT_FILE = '__inout__/out.txt'


class NowPlaying:
    def __init__(self, isPlaying: bool, totalTime: int, timeElapsed: int):
        self.isPlaying = isPlaying
        self.total = totalTime  # Both in seconds
        self.elapsed = timeElapsed

    def reinit(self, toPlay: np.ndarray, frames: int):
        self.toPlay: np.ndarray = toPlay[:]
        self.frames = frames
        self.playback_stream = sounddevice.OutputStream(samplerate=48_000, channels=1, dtype='int16', callback=self.update, latency='low')
        self.frames_done = 0
        self.total = frames / self.playback_stream.samplerate

    @staticmethod
    def fmt(time: float) -> str:
        """Formats time (given in seconds) into a string of form 'hours:minutes:seconds'"""
        fmttime = [0, 0]
        fmttime[0], fmttime[1] = divmod(time, 60)
        if fmttime[0] < 10:
            fmttime[0] = '0'+str(int(fmttime[0]))
        return f'{fmttime[0]}:{fmttime[1]:.1f}'

    def __bool__(self):
        return self.isPlaying

    def update(self, outdata: np.ndarray, frames: int, time, status):
        if self.isPlaying:
            if (n_f:= frames + self.frames_done) > self.frames > self.frames_done:
                outdata.fill(0)
                self.frames_done = self.frames
                self.isPlaying = False
            else:
                outdata[:] = self.toPlay[self.frames_done:n_f]
                self.frames_done += frames
        else:
            outdata.fill(0)

    def play_toggle(self) -> bool:
        if not self.isPlaying:
            if self.frames == self.frames_done:
                self.reinit(self.toPlay, self.frames)
            self.isPlaying = True
            self.playback_stream.start()
        else:
            self.playback_stream.stop()
            self.isPlaying = False

    @property
    def totalTime(self) -> str:
        return self.fmt(self.total)

    @property
    def timeElapsed(self) -> str:
        # self.elapsed = round(self.frames_done / self.playback_stream.samplerate)
        return self.fmt(self.elapsed)


class Auditorise:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title('Auditorise')
        self.win.minsize(MINSIZE_X, MINSIZE_Y)

        self.style = ttkthemes.ThemedStyle(theme='breeze')
        self.style.configure('TFrame', background=STYLE['bg'])  # , relief='ridge')  # For debugging
        self.style.configure('Horizontal.TProgressbar', background=STYLE['bg'], foreground=STYLE['fg'])
        self.style.configure('Vertical.TScrollbar', background=STYLE['bg'], foreground=STYLE['fg'])

        # Frames
        self.everything = ttk.Frame(master=self.win, style='TFrame', width=MINSIZE_X, height=MINSIZE_Y)

        self.title_frame = ttk.Frame(master=self.everything, style='TFrame', width=MINSIZE_X, height=MINSIZE_Y/5)
        self.nav_frame = ttk.Frame(master=self.everything, style='TFrame', width=MINSIZE_X/4, height=4*MINSIZE_Y/5)
        self.page_frame = tk.Frame(master=self.everything, bg=STYLE['bg'], width=3*MINSIZE_X/4, height=3*MINSIZE_Y/5)
        self.audiobar = ttk.Frame(master=self.everything, style='TFrame', width=3*MINSIZE_X/4, height=MINSIZE_Y/5)

        # App icon
        self.app_icon = ImageTk.PhotoImage(
            Image.open(APP_ICON).resize(size=(MINSIZE_X, int(MINSIZE_Y/5)))
        )
        self.about_page_btn = tk.Button(master=self.title_frame, image=self.app_icon, bg=STYLE['bg'], borderwidth=0, activebackground=STYLE['bg'], command=self.about_page)
        self.about_page_btn.grid(row=0, column=0, sticky='nsew')

        # Navigation frame
        self.cam_page_btn = tk.Button(master=self.nav_frame, bg=STYLE['bg'], borderwidth=0, activebackground=STYLE['bg'], command=self.camera_page, anchor='center')
        self.screenshot_page_btn = tk.Button(master=self.nav_frame, bg=STYLE['bg'], borderwidth=0, activebackground=STYLE['bg'], command=self.screenshot_page, anchor='center')
        self.files_page_btn = tk.Button(master=self.nav_frame, bg=STYLE['bg'], borderwidth=0, activebackground=STYLE['bg'], command=self.file_page, anchor='center')
        hacky = tk.Frame(master=self.nav_frame, width=SIZES[1][0], borderwidth=0, bg=STYLE['bg'],
                         height=0)  # So that the entire window doesn't jerk violently when the buttons change size on pressing

        self.active_state = (0, 0, 0)  # Tells which button was pressed most recently
        self.navbar_icons = [[ImageTk.PhotoImage(
            Image.open(i).resize(
                size=SIZES[pos2]
            )) for pos2, i in enumerate(NAVBAR_ICONS[pos])]
            for pos, j in enumerate(NAVBAR_ICONS)]
        self.navbar_buttons = (self.cam_page_btn, self.screenshot_page_btn, self.files_page_btn)  # For self.update_navbar_icons()
        self.update_navbar_icons()

        self.cam_page_btn.grid(row=0, column=0, sticky='nsew')
        self.screenshot_page_btn.grid(row=1, column=0, sticky='nsew')
        self.files_page_btn.grid(row=2, column=0, sticky='nsew')
        hacky.grid(row=3, column=0, sticky='nsew', padx=100)

        self.nav_frame.rowconfigure(0, weight=1)
        self.nav_frame.rowconfigure(1, weight=1)
        self.nav_frame.rowconfigure(2, weight=1)
        self.nav_frame.rowconfigure(3, weight=1)
        self.nav_frame.columnconfigure(0, weight=1)

        # Audio bar frame
        self.time_elapsed = tk.StringVar()
        self.total_time = tk.StringVar()
        self.time_elapsed.set('00:00.0')
        self.total_time.set('00:00.0')
        self.now_playing = NowPlaying(isPlaying=False, timeElapsed=0, totalTime=0)

        self.time_elapsed_lbl = tk.Label(master=self.audiobar, bg=STYLE['bg'], textvariable=self.time_elapsed, fg=STYLE['fg2'])
        self.total_time_lbl = tk.Label(master=self.audiobar, bg=STYLE['bg'], textvariable=self.total_time, fg=STYLE['fg2'])
        self.audio_progressbar = ttk.Progressbar(master=self.audiobar, style='Horizontal.TProgressbar',
                                                 length=3*MINSIZE_X/4 - 200, orient='horizontal', mode='determinate')

        self.play_pause_icons = [ImageTk.PhotoImage(Image.open(i).resize(size=SIZES[2])) for i in PLAY_PAUSE_ICONS]
        self.play_pause_btn = tk.Button(master=self.audiobar, image=self.play_pause_icons[0], bg=STYLE['bg'], borderwidth=0, width=50, anchor='center',
                                        activebackground=STYLE['bg'], command=self.play_pause_callback)

        self.time_elapsed_lbl.grid(row=0, column=0, sticky='nsew')
        self.audio_progressbar.grid(row=0, column=1, sticky="nsew")
        self.total_time_lbl.grid(row=0, column=2, sticky='nsew')
        self.play_pause_btn.grid(row=1, column=1, sticky='ns')

        self.audiobar.rowconfigure(0, weight=1)
        self.audiobar.rowconfigure(1, weight=1)
        self.audiobar.columnconfigure(0, weight=1)
        self.audiobar.columnconfigure(1, weight=3)
        self.audiobar.columnconfigure(2, weight=1)

        # Preprocessed page frame
        ## Camera page
        self.video_stream = cv2.VideoCapture(0)
        self.capture_icon = ImageTk.PhotoImage(Image.open(CAPTURE_PIC_ICON).resize(size=SIZES[2]))
        self.stop_updating_video = True

        # Grid-ing the frames
        self.everything.grid(row=0, column=0, sticky='nsew')

        self.title_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')
        self.nav_frame.grid(row=1, column=0, rowspan=2, sticky='nsew')
        self.page_frame.grid(row=1, column=1, sticky='nsew')
        self.audiobar.grid(row=2, column=1, sticky='nsew')

        self.everything.columnconfigure(0, weight=1)
        self.everything.columnconfigure(1, weight=3)
        self.everything.rowconfigure(0, weight=1)
        self.everything.rowconfigure(1, weight=3)
        self.everything.rowconfigure(2, weight=1)

        self.win.rowconfigure(0, weight=1)  # To allow the window to resize
        self.win.columnconfigure(0, weight=1)

        self.win.bind('<Alt-c>', self.camera_page)
        self.win.bind('<Alt-s>', self.screenshot_page)
        self.win.bind('<Alt-f>', self.file_page)
        self.win.bind('<Alt-a>', self.about_page)
        self.win.bind('<Alt-p>', self.play_pause_callback)
        self.win.bind('<Alt-q>', self.__del__)

        self.about_page()  # Open About Page

        self.win.mainloop()

    def __del__(self, keybind_info = None):
        try:
            if self.video_stream.isOpened():
                self.video_stream.release()  # Safe disposal of cv2.VideoCapture
        except:
            pass
        try:
            self.win.destroy()
        except:
            pass
        for k, v in self.__dict__.items():
            del k, v

    def about_page(self, keybind_info = None):
        """Displays README.md (converted into HTML)"""
        self.active_state = (0, 0, 0)
        self.update_navbar_icons()
        def redirect_to_browser(link: str):
            link = link.lstrip('file:///')
            webbrowser.open(link)
        html_frame = tkinterweb.HtmlFrame(master=self.page_frame, messages_enabled=False)  # To render the converted MD file
        html_frame.on_link_click(redirect_to_browser)
        for child in html_frame.winfo_children():
            if isinstance(child, ttk.Scrollbar):
                child.configure(style='Vertical.TScrollbar')  # Changing the background colour to black
        with open(ABOUT_PAGE, 'r', encoding='utf-8') as about_file:
            html_frame.load_html(about_file.read())
        html_frame.grid(row=0, column=0, sticky='nsew')
        self.page_frame.rowconfigure(index=0, weight=1)
        self.page_frame.columnconfigure(index=0, weight=1)

    def camera_page(self, keybind_info = None):
        """Lets you capture an image from your camera and converts it to audio"""
        self.active_state = (1, 0, 0)
        self.update_navbar_icons()
        if not self.video_stream.isOpened():
            self.video_stream.open(0)
        self.stop_updating_video = False
        def update_video_display():
            if 'video_display' in self.page_frame.children and not self.stop_updating_video:
                self.frame = ImageTk.PhotoImage(Image.fromarray(
                    cv2.cvtColor(self.video_stream.read()[1], cv2.COLOR_BGR2RGB)
                ).resize((256, 256)))  # frame has to be an attribute of the class because tkinter needs access to the variable itself, not just it's value
                video_display['image'] = self.frame
                self.win.after(int(1000/30), update_video_display)   # 30 frames/second
            else:
                self.video_stream.release()  # Cleanup
                self.win.unbind('<Alt-space>', seq)

        def capture_image(keybind_info_ = None):  # Callback of capture_btn
            self.stop_updating_video = True

            capture_btn.destroy()
            retry.grid(row=1, column=0, sticky='nsew')

            captured_image = Image.fromarray(
                cv2.cvtColor(self.video_stream.read()[1], cv2.COLOR_BGR2RGB)
            ).resize(size=(256, 256))  # It's easier to implement Hilbert curves in a square
            self.frame = ImageTk.PhotoImage(captured_image)  # Freeze
            video_display['image'] = self.frame
            captured_image = np.asarray(captured_image)   # Convert to array after resizing
            self.process_image(captured_image)

        video_display = tk.Label(master=self.page_frame, name='video_display', bg=STYLE['bg'], fg='red', text='Error: Unable to access camera')
        capture_btn = tk.Button(master=self.page_frame, image=self.capture_icon, bg=STYLE['bg'], borderwidth=0, activebackground=STYLE['bg'],
                                anchor='center', command=capture_image)
        retry = tk.Button(master=self.page_frame, text='Retry?', bg=STYLE['fg'], fg=STYLE['fg2'], borderwidth=0, activebackground=STYLE['bg'],
                          anchor='center', command=self.camera_page)

        video_display.grid(row=0, column=0, sticky='nsew')
        capture_btn.grid(row=1, column=0, sticky='nsew')

        self.page_frame.rowconfigure(0, weight=3)
        self.page_frame.rowconfigure(1, weight=1)
        self.page_frame.rowconfigure(2, weight=1)
        self.page_frame.columnconfigure(0, weight=4)

        seq = self.win.bind('<Alt-space>', capture_image)
        update_video_display()

    def screenshot_page(self, keybind_info = None):
        """Takes a screenshot and converts it to audio"""
        self.active_state = (0, 1, 0)
        self.update_navbar_icons()

        def capture():
            self.win.iconify()
            image = ImageGrab.grab().resize(size=(256, 256))
            self.frame = ImageTk.PhotoImage(image)
            image_display['image'] = self.frame
            self.win.deiconify()
            image = np.asarray(image)
            self.process_image(image)

        def minimise_and_wait(keybind_info_ = None):
            self.win.iconify()
            self.win.after(500, capture)

        image_display = tk.Label(master=self.page_frame, bg=STYLE['bg'], height=25, width=25)
        capture_btn = tk.Button(master=self.page_frame, bg=STYLE['fg'], fg=STYLE['fg2'], text='Take Screenshot...',
                                command=minimise_and_wait, anchor='center')
        image_display.grid(row=0, column=0, sticky='nsew')
        capture_btn.grid(row=1, column=0, sticky='nsew')
        self.page_frame.rowconfigure(index=0, weight=25)
        self.page_frame.rowconfigure(index=1, weight=1)
        self.page_frame.columnconfigure(index=0, weight=1)

        self.win.bind('<Alt-space>', minimise_and_wait)

    def file_page(self, keybind_info = None):
        """Convert images (_PNG_, _JPG_, _JPEG_ images) from your system into audio"""
        self.active_state = (0, 0, 1)
        self.update_navbar_icons()
        def set_lbl_img(file):
            try:
                im = Image.fromarray(
                    cv2.cvtColor(cv2.imread(file), cv2.COLOR_BGR2RGB)
                ).resize(size=(256, 256))  # Using cv2.imread() to get images in RGB
                self.frame = ImageTk.PhotoImage(im)
                image_display['image'] = self.frame
                im = np.asarray(im)  # Convert back to array
                self.process_image(im)
            except cv2.error:
                messagebox.showerror(title='Auditorise Error', message='Invalid file path.')
        def get_path():
            path = path_entry.get()
            set_lbl_img(path)
        def browse():
            file = filedialog.askopenfilename(filetypes=[('PNG', '*.png'), ('JPG', '*.jpg'), ('JPEG', '*.jpeg')],
                                              title='Open Images')
            path_entry.delete(0, 69)
            path_entry.insert(0, file)
            set_lbl_img(file)
        image_display = tk.Label(master=self.page_frame, bg=STYLE['bg'], height=25, width=25)
        path_entry = tk.Entry(master=self.page_frame, bg=STYLE['bg'], fg=STYLE['fg2'], width=70)
        path_btn = tk.Button(master=self.page_frame, bg=STYLE['fg'], fg=STYLE['fg2'], text='Enter...', command=get_path, anchor='center')
        browse_btn = tk.Button(master=self.page_frame, bg=STYLE['fg'], fg=STYLE['fg2'], text='Browse...', command=browse)

        image_display.grid(row=0, column=0, columnspan=2, sticky='nsew')
        path_entry.grid(row=1, column=0, sticky='nsew', ipadx=5)
        path_btn.grid(row=1, column=1, sticky='nsew')
        browse_btn.grid(row=2, column=1, sticky='nsew')
        self.page_frame.rowconfigure(0, weight=20)
        self.page_frame.rowconfigure(1, weight=1)
        self.page_frame.rowconfigure(2, weight=1)
        self.page_frame.columnconfigure(0, weight=5)
        self.page_frame.columnconfigure(1, weight=1)

    def play_pause_callback(self, keybind_info = None):
        """Play / pause"""
        self.now_playing.play_toggle()
        self.play_pause_btn['image'] = self.play_pause_icons[self.now_playing.isPlaying]
        def update_progressbar():
            if self.now_playing.isPlaying:
                if self.now_playing.frames_done < self.now_playing.frames:
                    self.now_playing.elapsed = self.audio_progressbar['value']/self.now_playing.playback_stream.samplerate
                    self.time_elapsed.set(self.now_playing.timeElapsed)
                    self.audio_progressbar['value']=self.now_playing.frames_done
                    self.win.after(10, update_progressbar)  # Timed callback
            else:
                self.play_pause_btn['image'] = self.play_pause_icons[0]
        if self.now_playing:
            self.total_time.set(self.now_playing.totalTime)
            self.time_elapsed.set(self.now_playing.timeElapsed)
            self.audio_progressbar['maximum'] = self.now_playing.frames+1  # Because the progressbar can't stop at the end for some reason
            update_progressbar()

    def update_navbar_icons(self):
        """Makes sure only one button is in state 'pressed' at any given time, and does cleanup when a new page is opened"""
        for num, state in enumerate(self.active_state):
            self.navbar_buttons[num]['image'] = self.navbar_icons[num][state]
        for child in self.page_frame.winfo_children():  # Clearing page frame to allow the next page to take the place
            child.destroy()

    def process_image(self, image: np.ndarray):
        """Calls the compiled COBOL executable"""
        np.savetxt(COBOL_INP_FILE, image.reshape((NP_ARRAY_LEN**2, 3)), delimiter=' ', fmt='%3u', newline='\n')
        with open(COBOL_OUT_FILE, 'w') as outfile:
            with open(COBOL_INP_FILE, 'r') as infile:
                proc = subprocess.run(COBOL_EXECUTABLE, stdin=infile, stdout=outfile)
                aud_array = np.loadtxt(COBOL_OUT_FILE, dtype=np.int16).reshape((-1, 1))
        print(f'Conversion successful: {proc}\n{aud_array}\n{aud_array.shape}')
        self.now_playing.reinit(aud_array, proc.returncode - 1)
        self.total_time.set(self.now_playing.totalTime)
        self.time_elapsed.set(self.now_playing.timeElapsed)
        self.play_pause_callback()


if __name__ == '__main__':
    Auditorise()
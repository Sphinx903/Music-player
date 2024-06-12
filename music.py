import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pygame
from mutagen.mp3 import MP3
import os
import random
import threading
from PIL import Image, ImageTk

# Initialize pygame mixer
pygame.mixer.init()

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Flexidoba")
        self.root.geometry("700x500")

        # Playlist and current song
        self.playlist = []
        self.current_song_index = 0

        # Whether repeat is on or off
        self.repeat_on = False

        # UI Elements
        self.create_widgets()

    def create_widgets(self):
        # Frame to contain buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=20)

        # Resize images to standard size
        icon_size = (32, 32)
        load_image = Image.open("images/load_icon.png").resize(icon_size)
        self.load_icon = ImageTk.PhotoImage(load_image)
        self.load_button = ttk.Button(button_frame, image=self.load_icon, command=self.load_music)
        self.load_button.grid(row=0, column=0, padx=5)

        play_image = Image.open("images/play_icon.png").resize(icon_size)
        self.play_icon = ImageTk.PhotoImage(play_image)
        self.play_button = ttk.Button(button_frame, image=self.play_icon, command=self.play_music)
        self.play_button.grid(row=0, column=1, padx=5)

        pause_image = Image.open("images/pause_icon.png").resize(icon_size)
        self.pause_icon = ImageTk.PhotoImage(pause_image)
        self.pause_button = ttk.Button(button_frame, image=self.pause_icon, command=self.pause_music)
        self.pause_button.grid(row=0, column=2, padx=5)

        stop_image = Image.open("images/stop_icon.png").resize(icon_size)
        self.stop_icon = ImageTk.PhotoImage(stop_image)
        self.stop_button = ttk.Button(button_frame, image=self.stop_icon, command=self.stop_music)
        self.stop_button.grid(row=0, column=3, padx=5)

        prev_image = Image.open("images/prev_icon.png").resize(icon_size)
        self.prev_icon = ImageTk.PhotoImage(prev_image)
        self.prev_button = ttk.Button(button_frame, image=self.prev_icon, command=self.prev_song)
        self.prev_button.grid(row=0, column=5, padx=5)

        next_image = Image.open("images/next_icon.png").resize(icon_size)
        self.next_icon = ImageTk.PhotoImage(next_image)
        self.next_button = ttk.Button(button_frame, image=self.next_icon, command=self.next_song)
        self.next_button.grid(row=0, column=4, padx=5)

        shuffle_image = Image.open("images/shuffle_icon.png").resize(icon_size)
        self.shuffle_icon = ImageTk.PhotoImage(shuffle_image)
        self.shuffle_button = ttk.Button(button_frame, image=self.shuffle_icon, command=self.shuffle_playlist)
        self.shuffle_button.grid(row=0, column=6, padx=5)

        repeat_image = Image.open("images/repeat_icon.png").resize(icon_size)
        self.repeat_icon = ImageTk.PhotoImage(repeat_image)
        self.repeat_button = ttk.Button(button_frame, image=self.repeat_icon, command=self.toggle_repeat)
        self.repeat_button.grid(row=0, column=7, padx=5)

        # Volume control
        volume_frame = ttk.Frame(self.root)
        volume_frame.pack(pady=10)

        self.volume_label = ttk.Label(volume_frame, text="Volume:")
        self.volume_label.grid(row=0, column=0, padx=5)

        self.volume_scale = ttk.Scale(volume_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, command=self.set_volume)
        self.volume_scale.grid(row=0, column=1, padx=5)
        self.volume_scale.set(0.5)  # Default volume

        # Playlist panel
        playlist_frame = ttk.Frame(self.root)
        playlist_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.playlist_label = ttk.Label(playlist_frame, text="Playlist:")
        self.playlist_label.pack(pady=5)

        self.playlist_box = tk.Listbox(playlist_frame, selectmode=tk.SINGLE)
        self.playlist_box.pack(fill=tk.BOTH, expand=True)
        self.playlist_box.bind('<<ListboxSelect>>', self.on_select)

        # # Metadata display
        # self.metadata_label = ttk.Label(self.root, text="", justify=tk.LEFT)
        # self.metadata_label.pack(pady=10)

        # Title label
        self.title_label = ttk.Label(self.root, text="Flexidoba", foreground="blue", font=("Arial", 30, "bold"))
        self.title_label.pack(pady=10)

        # Style configuration
        self.style = ttk.Style()
        self.style.configure('TButton', padding=5, relief=tk.RAISED)

    def load_music(self):
        files = filedialog.askopenfilenames(filetypes=[("MP3 Files", "*.mp3")])
        for file in files:
            self.playlist.append(file)
            self.playlist_box.insert(tk.END, os.path.basename(file))
    
    def play_music(self):
     if self.playlist:
        if not hasattr(self, 'shuffled_playlist'):
            self.shuffled_playlist = self.playlist.copy()
            random.shuffle(self.shuffled_playlist)
        song = self.shuffled_playlist[self.current_song_index]
        pygame.mixer.music.load(song)
        pygame.mixer.music.play()
        self.display_metadata(song)
        # Highlight currently playing song
        self.playlist_box.selection_clear(0, tk.END)
        self.playlist_box.selection_set(self.current_song_index)
        self.playlist_box.activate(self.current_song_index)

    
    def pause_music(self):
        pygame.mixer.music.pause()
    
    def stop_music(self):
        pygame.mixer.music.stop()
    
    def next_song(self):
      if self.playlist:
        if not hasattr(self, 'shuffled_playlist'):
            self.shuffled_playlist = self.playlist.copy()
            random.shuffle(self.shuffled_playlist)
        self.current_song_index = (self.current_song_index + 1) % len(self.shuffled_playlist)
        self.play_music()

    
    def prev_song(self):
      if self.playlist:
        if not hasattr(self, 'shuffled_playlist'):
            self.shuffled_playlist = self.playlist.copy()
            random.shuffle(self.shuffled_playlist)
        self.current_song_index = (self.current_song_index - 1) % len(self.shuffled_playlist)
        self.play_music()


    def shuffle_playlist(self):
        if self.playlist:
            random.shuffle(self.playlist)
            self.playlist_box.delete(0, tk.END)
            for song in self.playlist:
                self.playlist_box.insert(tk.END, os.path.basename(song))
    
    def toggle_repeat(self):
        self.repeat_on = not self.repeat_on
        # Change the icon color to indicate repeat status
        if self.repeat_on:
            repeat_image = Image.open("repeat_icon_on.png").resize((32, 32))
        else:
            repeat_image = Image.open("repeat_icon.png").resize((32, 32))
        self.repeat_icon = ImageTk.PhotoImage(repeat_image)
        self.repeat_button.configure(image=self.repeat_icon)

    def set_volume(self, volume):
        pygame.mixer.music.set_volume(float(volume))

    def display_metadata(self, song):
        audio = MP3(song)
        metadata = f"Title: {audio.get('TIT2', 'Unknown')}\n"
        metadata += f"Artist: {audio.get('TPE1', 'Unknown')}\n"
        metadata += f"Album: {audio.get('TALB', 'Unknown')}\n"
        metadata += f"Duration: {audio.info.length:.2f} seconds"
        # self.metadata_label.config(text=metadata)

    def on_select(self, event):
        # Update current song index when selection changes
        if self.playlist_box.curselection():
            self.current_song_index = self.playlist_box.curselection()[0]

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayer(root)
    root.mainloop()

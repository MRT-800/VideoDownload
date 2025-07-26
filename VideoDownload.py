import os
import sys  # <<< ADDED
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from yt_dlp import YoutubeDL

APP_TITLE = "VideoGrabber"

QUALITY_MAP = {
    "Best available": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "Audio only (mp3)": "bestaudio/best"
}

class DownloaderGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("650x400")
        self.resizable(False, False)
        self.configure(bg="black")

        self.url_var = tk.StringVar()
        self.path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.quality_var = tk.StringVar(value="Best available")
        self.status_var = tk.StringVar(value="Idle")
        self.speed_var = tk.StringVar(value="")
        self.eta_var = tk.StringVar(value="")
        self.percent_var = tk.DoubleVar(value=0.0)
        self.last_downloaded_file = None

        self._style_theme()
        self._build_ui()
        self.downloading = False

    # ---------- NEW HELPERS ----------

    def _app_base_dir(self):
        """
        Returns the base folder where resources live.
        - If running as PyInstaller onefile exe: sys._MEIPASS
        - Else: folder of this .py file
        """
        if getattr(sys, "frozen", False):
            return sys._MEIPASS  # PyInstaller temp extraction dir
        return os.path.dirname(os.path.abspath(__file__))

    def _ffmpeg_path(self):
        """
        Build the absolute path to ffmpeg.exe shipped with the app.
        Works both when frozen and when run from source.
        """
        base = self._app_base_dir()
        # Keep your structure: <app>/ffmpeg/ffmpeg.exe
        return os.path.join(base, "ffmpeg", "ffmpeg.exe")

    # ---------------------------------

    def _style_theme(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="black", foreground="#76b900", font=("Comic Sans MS", 10, "bold"))
        style.configure("TButton", background="#76b900", foreground="black", font=("Comic Sans MS", 10, "bold"))
        style.configure("TFrame", background="black")
        style.configure("TLabelframe", background="black", foreground="#76b900", font=("Comic Sans MS", 10, "bold"))
        style.configure("TEntry", fieldbackground="black", foreground="white", insertcolor="white")
        style.configure("TCombobox", fieldbackground="black", background="black", foreground="white")
        style.configure("Horizontal.TProgressbar", troughcolor="black", background="#76b900")

    def _build_ui(self):
        pad = 8

        # URL
        url_frame = ttk.LabelFrame(self, text="Video URL")
        url_frame.pack(fill="x", padx=pad, pady=(pad, 0))
        ttk.Label(url_frame, text="Video URL:", style="TLabel").pack(side="left", padx=pad, pady=pad)
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var)
        url_entry.pack(fill="x", padx=pad, pady=pad)
        url_entry.configure(foreground="white")

        # Options
        opt_frame = ttk.LabelFrame(self, text="Options")
        opt_frame.pack(fill="x", padx=pad, pady=pad)

        ttk.Label(opt_frame, text="Quality:", style="TLabel").grid(row=0, column=0, sticky="w", padx=pad, pady=pad)
        quality_cb = ttk.Combobox(opt_frame, values=list(QUALITY_MAP.keys()), textvariable=self.quality_var, state="readonly")
        quality_cb.grid(row=0, column=1, sticky="we", padx=pad, pady=pad)

        ttk.Label(opt_frame, text="Download to:", style="TLabel").grid(row=1, column=0, sticky="w", padx=pad, pady=pad)
        path_entry = ttk.Entry(opt_frame, textvariable=self.path_var)
        path_entry.grid(row=1, column=1, sticky="we", padx=pad, pady=pad)
        browse_btn = ttk.Button(opt_frame, text="Browse…", command=self._browse_dir)
        browse_btn.grid(row=1, column=2, sticky="e", padx=pad, pady=pad)

        opt_frame.columnconfigure(1, weight=1)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=pad, pady=(0, pad))
        self.download_btn = ttk.Button(btn_frame, text="Download", command=self._on_download_click)
        self.download_btn.pack(side="left", padx=pad)

        # Progress
        prog_frame = ttk.LabelFrame(self, text="Progress")
        prog_frame.pack(fill="x", padx=pad, pady=pad)
        ttk.Label(prog_frame, text="Progress:", style="TLabel").pack(side="left", padx=pad, pady=pad)
        self.progress = ttk.Progressbar(prog_frame, variable=self.percent_var, maximum=100, style="Horizontal.TProgressbar")
        self.progress.pack(fill="x", padx=pad, pady=(pad, 0))

        status_row = ttk.Frame(prog_frame)
        status_row.pack(fill="x", padx=pad, pady=(pad, pad))
        ttk.Label(status_row, textvariable=self.status_var, style="TLabel").pack(side="left")
        ttk.Label(status_row, textvariable=self.speed_var, style="TLabel").pack(side="right")
        ttk.Label(status_row, textvariable=self.eta_var, style="TLabel").pack(side="right", padx=(0, 10))

        # Log
        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(fill="both", expand=True, padx=pad, pady=(0, pad))
        ttk.Label(log_frame, text="Log:", style="TLabel").pack(side="left", padx=pad, pady=pad)
        self.log_text = tk.Text(log_frame, height=8, wrap="word", state="disabled", bg="black", fg="#76b900", insertbackground="white", font=("Comic Sans MS", 10, "bold"))
        self.log_text.pack(fill="both", expand=True, padx=pad, pady=pad)

        # DONE button (hidden initially)
        self.done_btn = tk.Button(self, text="DONE!", font=("Comic Sans MS", 14, "bold"), bg="#76b900", fg="black", command=self._open_last_file)
        self.done_btn.pack_forget()

    def _browse_dir(self):
        directory = filedialog.askdirectory(initialdir=self.path_var.get() or os.path.expanduser("~"))
        if directory:
            self.path_var.set(directory)

    def _open_last_file(self):
        if self.last_downloaded_file and os.path.exists(self.last_downloaded_file):
            try:
                if os.name == "nt":
                    os.startfile(os.path.dirname(self.last_downloaded_file))
                else:
                    import subprocess
                    subprocess.Popen(["xdg-open", os.path.dirname(self.last_downloaded_file)])
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Warning", "No file found.")

    def _on_download_click(self):
        if self.downloading:
            messagebox.showinfo("Please wait", "A download is already running.")
            return

        url = self.url_var.get().strip()
        outdir = self.path_var.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Please paste a video URL.")
            return
        if not os.path.isdir(outdir):
            messagebox.showwarning("Invalid folder", "Select a valid download folder.")
            return

        quality = self.quality_var.get()
        fmt = QUALITY_MAP.get(quality, "bestvideo+bestaudio/best")

        self.downloading = True
        self.download_btn.configure(state="disabled")
        self.done_btn.pack_forget()
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._set_status("Starting…")

        thread = threading.Thread(target=self._download_thread, args=(url, outdir, fmt, quality), daemon=True)
        thread.start()

    def _download_thread(self, url, outdir, fmt, quality_label):
        def hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                percent = (downloaded / total * 100) if total else 0
                speed = d.get('speed')
                eta = d.get('eta')

                self._update_progress(percent, speed, eta)
                self._set_status("Downloading…")
            elif d['status'] == 'finished':
                self._update_progress(100, None, None)
                self._set_status("Post-processing…")
                self.last_downloaded_file = d.get('filename')

        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # CHANGED: resolve ffmpeg path dynamically (works on any PC).
        ffmpeg_exe = self._ffmpeg_path()
        # You can pass either the binary or the folder. Using the binary path is fine:
        ffmpeg_loc = ffmpeg_exe
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        ydl_opts = {
            'format': fmt,
            'outtmpl': os.path.join(outdir, '%(title)s.%(ext)s'),
            'progress_hooks': [hook],
            'noprogress': True,
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': ffmpeg_loc,  # <<< CHANGED
        }

        if "Audio only" in quality_label:
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })

        try:
            with YoutubeDL(ydl_opts) as ydl:
                self._log(f"URL: {url}\nFormat: {quality_label}\nSaving to: {outdir}\nUsing ffmpeg: {ffmpeg_exe}\n")
                ydl.download([url])
            self._set_status("Done.")
            self._log("✅ Download complete.\n")
            self.after(0, lambda: self.done_btn.pack(pady=10))
        except Exception as e:
            self._set_status("Error")
            self._log(f"❌ {e}\n")
            messagebox.showerror("Download failed", str(e))
        finally:
            self.downloading = False
            self.download_btn.configure(state="normal")

    def _update_progress(self, percent, speed, eta):
        def _inner():
            self.percent_var.set(percent)
            self.progress.update_idletasks()
            self.speed_var.set(f"{self._human_readable_size(speed)}/s" if speed else "")
            self.eta_var.set(f"ETA: {self._format_time(eta)}" if eta else "")
        self.after(0, _inner)

    def _set_status(self, text):
        self.after(0, lambda: self.status_var.set(text))

    def _log(self, text):
        def _inner():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", text)
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.after(0, _inner)

    @staticmethod
    def _human_readable_size(num, suffix="B"):
        for unit in ["", "K", "M", "G", "T", "P"]:
            if not num:
                return "0B"
            if abs(num) < 1024.0:
                return f"{num:3.1f}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}Y{suffix}"

    @staticmethod
    def _format_time(seconds):
        if seconds is None:
            return "?"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


if __name__ == "__main__":
    app = DownloaderGUI()
    app.mainloop()

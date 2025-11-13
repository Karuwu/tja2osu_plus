import os
import zipfile
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from tja2osu_plus import convertio as tja_convert
except Exception:
    tja_convert = None

AUDIO_EXTS = (".ogg", ".mp3", ".wav", ".flac")

def norm_course(name: str) -> str:
    n = name.lower()
    if n in ("kantan", "easy", "0"): return "Kantan"
    if n in ("futsuu", "normal", "1"): return "Futsuu"
    if n in ("muzukashii", "muzukashi", "hard", "2"): return "Muzukashii"
    if n in ("oni", "3"): return "Oni"
    if n in ("ura oni", "ura", "inner oni", "inner", "edit", "4"): return "Inner Oni"
    return name

def list_tja_files(path: str):
    if os.path.isfile(path) and path.lower().endswith(".tja"):
        yield path
        return
    for dirpath, _, files in os.walk(path):
        for f in files:
            if f.lower().endswith(".tja"):
                yield os.path.join(dirpath, f)

def _pick_audio_file(input_dir: str):
    if not os.path.isdir(input_dir):
        return None
    files = os.listdir(input_dir)
    # Prefer .ogg if available, else by order
    for ext in AUDIO_EXTS:
        for f in files:
            if f.lower().endswith(ext):
                return os.path.join(input_dir, f)
    return None

def _rewrite_osu_audio_to_ogg(osu_path: str) -> bytes:
    # Read .osu and rewrite AudioFilename to "audio.ogg" for packaging
    with open(osu_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("AudioFilename:"):
            lines[i] = "AudioFilename: audio.ogg"
            break
    return ("\n".join(lines) + "\n").encode("utf-8")

def _make_osz_for_single_tja(out_dir: str, new_osu_files: list, input_audio_dir: str,
                             copy_audio: bool, keep_osu_files: bool):
    """
    Bundle all new_osu_files from this TJA into ONE .osz.
    Optionally embed audio as audio.ogg. Optionally remove the .osu after packaging.
    """
    if not new_osu_files:
        return

    # Derive archive base name from the first .osu (strip [Version])
    base_name = os.path.splitext(os.path.basename(new_osu_files[0]))[0]
    if "[" in base_name:
        base_name = base_name.split("[", 1)[0].rstrip()
    os.makedirs(out_dir, exist_ok=True)
    osz_path = os.path.join(out_dir, f"{base_name}.osz")

    audio_src = _pick_audio_file(input_audio_dir) if copy_audio else None

    with zipfile.ZipFile(osz_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for osu_path in new_osu_files:
            rewritten = _rewrite_osu_audio_to_ogg(osu_path)
            zf.writestr(os.path.basename(osu_path), rewritten)

        if audio_src:
            with open(audio_src, "rb") as af:
                zf.writestr("audio.ogg", af.read())

    if not keep_osu_files:
        for p in new_osu_files:
            try: os.remove(p)
            except Exception: pass

class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.master.title("tja2osu GUI")
        try:
            self.master.tk.call("tk", "scaling", 1.2)  # nicer on macOS
        except Exception:
            pass

        # ----- state -----
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.keep_structure = tk.BooleanVar(value=True)
        self.copy_audio_fs = tk.BooleanVar(value=False)  # copy audio into folders

        self.export_osz = tk.BooleanVar(value=False)
        self.copy_audio = tk.BooleanVar(value=True)   # default ON (for .osz)
        self.keep_osu   = tk.BooleanVar(value=False)  # default OFF

        self.skip_double = tk.BooleanVar(value=True)
        self.artist = tk.StringVar()
        self.creator = tk.StringVar()

        self.courses = {
            "Kantan": tk.BooleanVar(value=False),
            "Futsuu": tk.BooleanVar(value=False),
            "Muzukashii": tk.BooleanVar(value=False),
            "Oni": tk.BooleanVar(value=True),
            "Inner Oni": tk.BooleanVar(value=True),
        }
        self.levels = {i: tk.BooleanVar(value=False) for i in range(1, 11)}

        self.branch_N = tk.BooleanVar(value=False)
        self.branch_E = tk.BooleanVar(value=False)
        self.branch_M = tk.BooleanVar(value=True)

        # ----- layout -----
        self.grid(sticky="nsew")
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        style = ttk.Style()
        try:
            if "macOS" in style.theme_names():
                style.theme_use("macOS")
        except Exception:
            pass

        frm_in = ttk.LabelFrame(self, text="Input / Output")
        frm_in.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        frm_in.columnconfigure(1, weight=1)

        ttk.Label(frm_in, text="Input path (.tja or folder):").grid(row=0, column=0, sticky="w", padx=6, pady=(8,2))
        ent_in = ttk.Entry(frm_in, textvariable=self.input_path)
        ent_in.grid(row=0, column=1, sticky="ew", padx=6, pady=(8,2))
        ttk.Button(frm_in, text="Browse File", command=self._browse_tja).grid(row=0, column=2, padx=4, pady=(8,2))
        ttk.Button(frm_in, text="Browse Folder", command=self._browse_dir).grid(row=0, column=3, padx=(0,6), pady=(8,2))

        ttk.Label(frm_in, text="Output path (folder):").grid(row=1, column=0, sticky="w", padx=6, pady=2)
        ent_out = ttk.Entry(frm_in, textvariable=self.output_path)
        ent_out.grid(row=1, column=1, sticky="ew", padx=6, pady=2)
        ttk.Button(frm_in, text="Select Output", command=self._browse_output).grid(row=1, column=2, columnspan=2, padx=4, pady=2, sticky="e")

        # Row under the group
        row1 = ttk.Frame(self)
        row1.grid(row=1, column=0, sticky="ew", padx=6, pady=(0,6))
        row1.columnconfigure(0, weight=1)
        self.chk_keep = ttk.Checkbutton(row1, text="Keep Folder Structure (for directory input)", variable=self.keep_structure)
        self.chk_keep.grid(row=0, column=0, sticky="w")
        self.chk_copy_audio_fs = ttk.Checkbutton(row1, text="Copy Audio (into output folders)", variable=self.copy_audio_fs)
        self.chk_copy_audio_fs.grid(row=0, column=1, sticky="w", padx=(16,0))

        frm_meta = ttk.LabelFrame(self, text="Metadata (defaults: Artist=Various, Creator=tja2osu)")
        frm_meta.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        frm_meta.columnconfigure(1, weight=1)
        frm_meta.columnconfigure(3, weight=1)
        ttk.Label(frm_meta, text="Artist:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(frm_meta, textvariable=self.artist).grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        ttk.Label(frm_meta, text="Creator:").grid(row=0, column=2, padx=6, pady=6, sticky="w")
        ttk.Entry(frm_meta, textvariable=self.creator).grid(row=0, column=3, padx=6, pady=6, sticky="ew")

        frm_filters = ttk.LabelFrame(self, text="Filters")
        frm_filters.grid(row=3, column=0, sticky="ew", padx=4, pady=4)
        for c in range(4): frm_filters.columnconfigure(c, weight=1)

        box_courses = ttk.Frame(frm_filters); box_courses.grid(row=0, column=0, columnspan=4, sticky="ew", padx=6, pady=(6,2))
        ttk.Label(box_courses, text="Course:").grid(row=0, column=0, padx=(0,8), sticky="w")
        for idx, name in enumerate(["Kantan", "Futsuu", "Muzukashii", "Oni", "Inner Oni"], start=1):
            ttk.Checkbutton(box_courses, text=name, variable=self.courses[name]).grid(row=0, column=idx, padx=4, sticky="w")

        box_levels = ttk.Frame(frm_filters); box_levels.grid(row=1, column=0, columnspan=4, sticky="ew", padx=6, pady=(2,6))
        ttk.Label(box_levels, text="Level (★):").grid(row=0, column=0, padx=(0,8), sticky="w")
        for i in range(1, 11):
            ttk.Checkbutton(box_levels, text=str(i), variable=self.levels[i]).grid(row=0, column=i, padx=4, sticky="w")

        box_opts = ttk.Frame(frm_filters); box_opts.grid(row=2, column=0, columnspan=4, sticky="ew", padx=6, pady=(0,6))
        ttk.Checkbutton(box_opts, text="Skip Double", variable=self.skip_double).grid(row=0, column=0, padx=(0,12), sticky="w")
        # store the Export as .osz checkbox so we can enable/disable it
        self.chk_export_osz = ttk.Checkbutton(box_opts, text="Export as .osz",
                                              variable=self.export_osz, command=self._toggle_export_children)
        self.chk_export_osz.grid(row=0, column=1, padx=12, sticky="w")

        # Children options under Export as .osz
        box_export_children = ttk.Frame(frm_filters)
        box_export_children.grid(row=3, column=0, columnspan=4, sticky="w", padx=36, pady=(0,8))
        self.chk_copy_audio = ttk.Checkbutton(box_export_children, text="Copy Audio into .osz (as audio.ogg)", variable=self.copy_audio)
        self.chk_copy_audio.grid(row=0, column=0, padx=(0,12), sticky="w")
        self.chk_keep_osu = ttk.Checkbutton(box_export_children, text="Keep .osu files (otherwise only .osz is kept)", variable=self.keep_osu)
        self.chk_keep_osu.grid(row=0, column=1, padx=(0,12), sticky="w")

        box_branch = ttk.Frame(frm_filters); box_branch.grid(row=4, column=0, columnspan=4, sticky="ew", padx=6, pady=(0,8))
        ttk.Label(box_branch, text="Branch:").grid(row=0, column=0, padx=(0,8), sticky="w")
        ttk.Checkbutton(box_branch, text="N", variable=self.branch_N).grid(row=0, column=1, padx=4, sticky="w")
        ttk.Checkbutton(box_branch, text="E", variable=self.branch_E).grid(row=0, column=2, padx=4, sticky="w")
        ttk.Checkbutton(box_branch, text="M", variable=self.branch_M).grid(row=0, column=3, padx=4, sticky="w")
        ttk.Label(box_branch, text="(Only applicable to branched charts)").grid(row=0, column=4, padx=12, sticky="w")

        frm_bottom = ttk.Frame(self); frm_bottom.grid(row=4, column=0, sticky="nsew", padx=4, pady=4)
        frm_bottom.columnconfigure(0, weight=1); frm_bottom.rowconfigure(0, weight=1)
        frm_log = ttk.LabelFrame(frm_bottom, text="Log"); frm_log.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0,6))
        frm_log.columnconfigure(0, weight=1); frm_log.rowconfigure(0, weight=1)
        self.txt_log = tk.Text(frm_log, height=6, wrap="word")
        self.txt_log.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.btn_convert = ttk.Button(frm_bottom, text="Convert", command=self._convert_clicked)
        self.btn_convert.grid(row=1, column=0, sticky="e")

        self._wire_validation()
        self._toggle_export_children()

    def _toggle_export_children(self):
        if self.export_osz.get():
            self.chk_copy_audio.state(["!disabled"])
            self.chk_keep_osu.state(["!disabled"])
        else:
            self.chk_copy_audio.state(["disabled"])
            self.chk_keep_osu.state(["disabled"])

    def _wire_validation(self):
        def update_state(*_):
            ip = self.input_path.get().strip()
            is_dir = os.path.isdir(ip)

            # Keep/Copy-Audio-for-folders are only meaningful for directory inputs
            self.chk_keep.state(["!disabled"] if is_dir else ["disabled"])
            self.chk_copy_audio_fs.state(["!disabled"] if is_dir else ["disabled"])

            # NEW: disable .osz export when input is a single .tja file
            if is_dir:
                self.chk_export_osz.state(["!disabled"])
            else:
                # turn off export_osz and disable the checkbox + its children
                self.export_osz.set(False)
                self.chk_export_osz.state(["disabled"])
                self._toggle_export_children()  # will disable child options

            can = bool(self.input_path.get().strip()) and bool(self.output_path.get().strip())
            if can: self.btn_convert.state(["!disabled"])
            else:   self.btn_convert.state(["disabled"])

        self.input_path.trace_add("write", update_state)
        self.output_path.trace_add("write", update_state)
        update_state()

    def _browse_tja(self):
        path = filedialog.askopenfilename(title="Select a TJA file", filetypes=[("TJA files","*.tja")])
        if path: self.input_path.set(path)

    def _browse_dir(self):
        path = filedialog.askdirectory(title="Select a folder containing TJA files")
        if path: self.input_path.set(path)

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path: self.output_path.set(path)

    def log(self, msg: str):
        self.txt_log.insert("end", msg + "\n")
        self.txt_log.see("end")
        self.update_idletasks()

    def _convert_clicked(self):
        if tja_convert is None:
            messagebox.showerror("Error", "Could not import converter. Ensure tja2osu_fixed_branches.py is available.")
            return

        inp = self.input_path.get().strip()
        out_root = self.output_path.get().strip()
        if not inp or not out_root:
            messagebox.showwarning("Missing fields", "Input and Output paths are required.")
            return

        artist = (self.artist.get().strip() or "Various")
        creator = (self.creator.get().strip() or "tja2osu")

        selected_courses = [norm_course(n) for n, v in self.courses.items() if v.get()]
        allowed_versions = selected_courses if selected_courses else None

        selected_levels = [lvl for lvl, v in self.levels.items() if v.get()]
        allowed_levels = selected_levels if selected_levels else None

        skip_double = self.skip_double.get()

        export_osz = self.export_osz.get()
        copy_audio = self.copy_audio.get()
        keep_osu = self.keep_osu.get()

        branches = []
        if self.branch_N.get(): branches.append("N")
        if self.branch_E.get(): branches.append("E")
        if self.branch_M.get(): branches.append("M")
        if not branches: branches = ["M"]

        keep_struct = self.keep_structure.get() and os.path.isdir(inp)
        copy_audio_fs = self.copy_audio_fs.get() and os.path.isdir(inp)

        # Resolve inputs
        tjas = list(list_tja_files(inp))
        if not tjas:
            messagebox.showinfo("No files", "No .tja files found at the selected input.")
            return

        self.txt_log.delete("1.0", "end")
        self.log(f"Found {len(tjas)} TJA file(s).")

        successes = 0
        errors = 0

        for tja_path in tjas:
            try:
                out_dir = os.path.join(out_root, os.path.relpath(os.path.dirname(tja_path), inp)) if keep_struct else out_root

                before = set(os.listdir(out_dir)) if os.path.isdir(out_dir) else set()

                kwargs = {
                    "allowed_versions": allowed_versions,
                    "allowed_levels": allowed_levels,      # additive filter
                    "skip_double": skip_double,
                    "allowed_branches": branches
                }

                wrote = tja_convert(tja_path, artist, creator, out_dir, **kwargs)

                after = set(os.listdir(out_dir)) if os.path.isdir(out_dir) else set()
                new_names = [n for n in sorted(after - before) if n.lower().endswith(".osu")]
                new_osu_files = [os.path.join(out_dir, n) for n in new_names]

                if wrote and new_osu_files:
                    successes += 1
                    self.log(f"OK: {os.path.basename(tja_path)} ({len(new_osu_files)} diff(s))")

                    # Copy audio into folder structure (only for converted charts)
                    if copy_audio_fs:
                        src_audio = _pick_audio_file(os.path.dirname(tja_path))
                        if src_audio:
                            os.makedirs(out_dir, exist_ok=True)
                            dst_audio = os.path.join(out_dir, os.path.basename(src_audio))
                            try:
                                if not os.path.exists(dst_audio):
                                    shutil.copy2(src_audio, dst_audio)
                            except Exception as e:
                                self.log(f"Warning: could not copy audio: {e}")

                    # Package .osz if requested
                    if export_osz:
                        _make_osz_for_single_tja(
                            out_dir=out_dir,
                            new_osu_files=new_osu_files,
                            input_audio_dir=os.path.dirname(tja_path),
                            copy_audio=copy_audio,
                            keep_osu_files=keep_osu
                        )
                else:
                    self.log(f"Filtered out: {os.path.basename(tja_path)}")
            except Exception as ex:
                errors += 1
                self.log(f"ERROR: {os.path.basename(tja_path)} -> {ex}")

        self.log(f"Done. Converted {successes} / {len(tjas)} file(s). Errors: {errors}")
        messagebox.showinfo("Conversion complete", f"Converted {successes}/{len(tjas)}. See log for details.")

if __name__ == "__main__":
    root = tk.Tk()
    App(root).mainloop()

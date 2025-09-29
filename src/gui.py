# src/gui.py

# --- Standardtní Importy ---
import threading
import os
import math
import traceback

# --- Importy třetích stran ---
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps, ImageDraw

# --- Moduly aplikace ---
from processing import process_image
from stl_generator import image_to_stl


class ReliefApp(tk.Tk):

    # --- 1. KONSTRUKTOR A INICIALIZACE (__init__) ---
    # Hlavní vstupní bod třídy. Deleguje zodpovědnost na specializované metody.

    def __init__(self):
        super().__init__()
        self.title("Image to STL Converter v2.0")
        self.geometry("1200x800")
        self.minsize(800, 600)

        self._initialize_variables()
        self._create_widgets()
        self._bind_events()

    # --- 2. SPRÁVA STAVU (_initialize_variables) ---
    # Definuje na jednom místě všechny proměnné, které si aplikace "pamatuje".
    # Speciální Tkinter proměnné (StringVar, DoubleVar), které jsou obousměrně propojeny s widgety (posuvníky, checkboxy).

    def _initialize_variables(self):
        """Inicializuje všechny stavové a Tkinter proměnné."""
        self.original_pil_image = None
        self.active_pil_image = None
        self.processed_pil_image = None
        self.tk_image = None
        self.current_selection_points = []
        self.is_drawing_shape = False
        self.zoom_level = 1.0
        self.view_offset_x = 0
        self.view_offset_y = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.debounce_timer = None

        self.selection_mode = tk.StringVar(value="Rectangle")
        self.model_width_var = tk.DoubleVar(value=100.0)
        self.base_height_var = tk.DoubleVar(value=2.0)
        self.model_height_var = tk.DoubleVar(value=4.0)
        self.smoothing_var = tk.DoubleVar(value=0.0)
        self.invert_colors_var = tk.BooleanVar(value=False)
        self.mirror_output_var = tk.BooleanVar(value=False)
        self.contrast_var = tk.DoubleVar(value=1.0)
        self.brightness_var = tk.DoubleVar(value=1.0)
        self.use_threshold_var = tk.BooleanVar(value=False)
        self.threshold_level_var = tk.IntVar(value=128)
        self.noise_reduction_var = tk.IntVar(value=0)
        self.dilate_var = tk.IntVar(value=0)
        self.erode_var = tk.IntVar(value=0)
        self.binary_format_var = tk.BooleanVar(value=True)
        self.use_stroke_var = tk.BooleanVar(value=False)
        self.stroke_thickness_var = tk.IntVar(value=3)
        self.invert_polygon_var = tk.BooleanVar(value=False)
        self.use_cutting_margin_var = tk.BooleanVar(value=False)
        self.export_relief_only_var = tk.BooleanVar(value=False)
        self.flat_bottom_var = tk.BooleanVar(value=False)

    # --- 3. TVORBA UŽIVATELSKÉHO ROZHRANÍ (_create_widgets) ---
    # Sestavení a rozmístění všech prvků.
    # Používá pomocné metody (např. _create_file_model_tab) pro udržení přehlednosti kódu.
    # Princip DRY (Don't Repeat Yourself) pomocí metod jako _create_slider_row pro opakující se prvky.

    def _create_widgets(self):
        self.configure(bg="#2e2e2e")
        style = ttk.Style(self)
        style.theme_use("clam")
        self.paned_window = tk.PanedWindow(
            self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg="#2e2e2e"
        )
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        canvas_frame = tk.Frame(self.paned_window, bg="#1e1e1e")
        self.preview_canvas = tk.Canvas(
            canvas_frame, bg="#1e1e1e", highlightthickness=0
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.paned_window.add(canvas_frame, width=800)
        controls_frame = tk.Frame(self.paned_window, bg="#2e2e2e")
        self.paned_window.add(controls_frame, width=400)
        self.notebook = ttk.Notebook(controls_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_file_model_tab()
        self._create_adjustments_tab()
        self._create_masking_tab()
        self._configure_styles(style)

    def _create_file_model_tab(self):
        tab = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(tab, text="File & Model")
        self.load_btn = ttk.Button(tab, text="Load Image", command=self.load_image)
        self.load_btn.pack(fill="x", padx=10, pady=10)
        self.file_label = ttk.Label(tab, text="No image selected", wraplength=350)
        self.file_label.pack(fill="x", padx=10, pady=(0, 10))
        model_frame = ttk.LabelFrame(tab, text="Model Settings")
        model_frame.pack(fill="x", padx=10, pady=10)
        model_frame.columnconfigure(1, weight=1)
        self._create_entry_slider_row(
            model_frame, 0, "Target Width (mm):", self.model_width_var, 10, 500
        )
        self._create_entry_slider_row(
            model_frame, 1, "Base Thickness (mm):", self.base_height_var, 0, 20
        )
        self._create_entry_slider_row(
            model_frame, 2, "Relief Height (mm):", self.model_height_var, 0, 50
        )
        export_frame = ttk.LabelFrame(tab, text="Advanced Export")
        export_frame.pack(fill="x", padx=10, pady=10)
        ttk.Checkbutton(
            export_frame,
            text="Create Cutting Margin (1mm)",
            variable=self.use_cutting_margin_var,
        ).pack(anchor="w", padx=5)
        ttk.Checkbutton(
            export_frame,
            text="Export as relief only (no base/walls)",
            variable=self.export_relief_only_var,
        ).pack(anchor="w", padx=5)
        ttk.Checkbutton(
            export_frame,
            text="Generate Flat Bottom",
            variable=self.flat_bottom_var,
        ).pack(anchor="w", padx=5)
        self.convert_btn = ttk.Button(
            tab,
            text="Convert to STL",
            command=self.start_conversion,
            state="disabled",
            style="Accent.TButton",
        )
        self.convert_btn.pack(fill="x", padx=10, pady=10, ipady=5)
        self.progress_var = tk.DoubleVar()
        self.progressbar = ttk.Progressbar(tab, variable=self.progress_var, maximum=100)
        self.progressbar.pack(fill="x", padx=10, pady=(0, 5))
        self.progress_label = ttk.Label(tab, text="")
        self.progress_label.pack(fill="x", padx=10, pady=(0, 10))

    def _create_adjustments_tab(self):
        tab = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(tab, text="Adjustments")
        photo_frame = ttk.LabelFrame(tab, text="Image Adjustments")
        photo_frame.pack(fill="x", padx=10, pady=10)
        self._create_slider_row(
            photo_frame, 0, "Contrast", self.contrast_var, 0.5, 3.0, 1.0
        )
        self._create_slider_row(
            photo_frame, 1, "Brightness", self.brightness_var, 0.5, 3.0, 1.0
        )
        self._create_slider_row(
            photo_frame,
            2,
            "Threshold",
            self.threshold_level_var,
            0,
            255,
            128,
            self.use_threshold_var,
        )
        self._create_slider_row(
            photo_frame, 3, "Smoothing", self.smoothing_var, 0, 5, 0.0
        )
        self._create_slider_row(
            photo_frame, 4, "Noise Reduction", self.noise_reduction_var, 0, 5, 0
        )
        shape_frame = ttk.LabelFrame(tab, text="Shape Operations")
        shape_frame.pack(fill="x", padx=10, pady=10)
        self._create_slider_row(
            shape_frame,
            0,
            "Stroke",
            self.stroke_thickness_var,
            1,
            20,
            3,
            self.use_stroke_var,
        )
        ttk.Label(shape_frame, text="Dilate/Erode:").grid(
            row=1, column=0, sticky="w", padx=5
        )
        de_frame = ttk.Frame(shape_frame)
        de_frame.grid(row=1, column=1, columnspan=2, sticky="ew")
        de_frame.columnconfigure(0, weight=1)
        de_frame.columnconfigure(1, weight=1)
        ttk.Scale(
            de_frame,
            from_=0,
            to=10,
            orient="horizontal",
            variable=self.dilate_var,
            command=self.trigger_update,
        ).pack(side="left", expand=True, fill="x")
        ttk.Scale(
            de_frame,
            from_=0,
            to=10,
            orient="horizontal",
            variable=self.erode_var,
            command=self.trigger_update,
        ).pack(side="left", expand=True, fill="x")
        misc_frame = ttk.LabelFrame(tab, text="Output Options")
        misc_frame.pack(fill="x", padx=10, pady=10)
        ttk.Checkbutton(
            misc_frame,
            text="Invert Colors (dark is high)",
            variable=self.invert_colors_var,
            command=self.trigger_update,
        ).pack(anchor="w", padx=5)
        ttk.Checkbutton(
            misc_frame,
            text="Mirror output (for molds/stamps)",
            variable=self.mirror_output_var,
        ).pack(anchor="w", padx=5)
        ttk.Checkbutton(
            misc_frame,
            text="Save as Binary STL (Recommended)",
            variable=self.binary_format_var,
        ).pack(anchor="w", padx=5)

    def _create_masking_tab(self):
        tab = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(tab, text="Masking Tools")
        sel_frame = ttk.LabelFrame(tab, text="Selection Tools")
        sel_frame.pack(fill="x", padx=10, pady=10)
        tool_frame = ttk.Frame(sel_frame)
        tool_frame.pack(fill="x", pady=5)
        ttk.Radiobutton(
            tool_frame,
            text="Rectangle",
            variable=self.selection_mode,
            value="Rectangle",
        ).pack(side="left", expand=True)
        ttk.Radiobutton(
            tool_frame, text="Polygon", variable=self.selection_mode, value="Polygon"
        ).pack(side="left", expand=True)
        ttk.Radiobutton(
            tool_frame, text="Hexagon", variable=self.selection_mode, value="Hexagon"
        ).pack(side="left", expand=True)
        ttk.Radiobutton(
            tool_frame, text="Heart", variable=self.selection_mode, value="Heart"
        ).pack(side="left", expand=True)
        self.apply_mask_btn = ttk.Button(
            sel_frame,
            text="Apply Shape as Mask",
            command=self.apply_mask,
            state="disabled",
        )
        self.apply_mask_btn.pack(fill="x", padx=5, pady=5)
        self.revert_mask_btn = ttk.Button(
            sel_frame, text="Revert Crop", command=self.revert_mask, state="disabled"
        )
        self.revert_mask_btn.pack(fill="x", padx=5, pady=(0, 5))
        ttk.Checkbutton(
            sel_frame,
            text="Invert Mask (Keep Outside)",
            variable=self.invert_polygon_var,
        ).pack(anchor="w", padx=5, pady=2)
        sel_actions_frame = ttk.Frame(sel_frame)
        sel_actions_frame.pack(fill="x", pady=5)
        ttk.Button(
            sel_actions_frame, text="Undo Last Point", command=self.undo_last_point
        ).pack(side="left", expand=True, fill="x", padx=(0, 2))
        ttk.Button(
            sel_actions_frame,
            text="Clear Current",
            command=self.clear_current_selection,
        ).pack(side="left", expand=True, fill="x", padx=(2, 0))
        ttk.Button(tab, text="Reset View & Zoom", command=self.reset_view).pack(
            fill="x", padx=10, pady=10
        )

    def _create_slider_row(
        self, parent, row, label, var, from_, to, default_val, check_var=None
    ):
        if check_var:
            ttk.Checkbutton(
                parent, text=label, variable=check_var, command=self.trigger_update
            ).grid(row=row, column=0, sticky="w", padx=5)
        else:
            ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=5)
        parent.columnconfigure(1, weight=1)
        ttk.Scale(
            parent,
            from_=from_,
            to=to,
            orient="horizontal",
            variable=var,
            command=self.trigger_update,
        ).grid(row=row, column=1, sticky="ew", padx=5)
        reset_cmd = lambda v=var, d=default_val: [v.set(d), self.trigger_update()]
        ttk.Button(parent, text="⟲", width=3, command=reset_cmd).grid(
            row=row, column=2, padx=(0, 5)
        )

    def _create_entry_slider_row(self, parent, row, label, var, from_, to):
        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky="w", padx=5, pady=2
        )
        widget_frame = ttk.Frame(parent)
        widget_frame.grid(row=row, column=1, columnspan=2, sticky="ew")
        widget_frame.columnconfigure(0, weight=1)
        scale = ttk.Scale(
            widget_frame, from_=from_, to=to, orient="horizontal", variable=var
        )
        scale.grid(row=0, column=0, sticky="ew")
        entry = ttk.Entry(widget_frame, textvariable=var, width=7)
        entry.grid(row=0, column=1, padx=5)
        var.trace_add("write", self.trigger_update_from_trace)

    def _configure_styles(self, style):
        style.configure("TFrame", background="#2e2e2e")
        style.configure(
            "TLabel", background="#2e2e2e", foreground="white", font=("Arial", 10)
        )
        style.configure(
            "TButton",
            background="#555",
            foreground="white",
            font=("Arial", 10),
            padding=5,
        )
        style.map("TButton", background=[("active", "#666")])
        style.configure(
            "Accent.TButton", background="#007acc", font=("Arial", 12, "bold")
        )
        style.map("Accent.TButton", background=[("active", "#005f9e")])
        style.configure("TRadiobutton", background="#2e2e2e", foreground="white")
        style.configure("TCheckbutton", background="#2e2e2e", foreground="white")
        style.configure(
            "TLabelframe", background="#2e2e2e", bordercolor="#777", padding=10
        )
        style.configure(
            "TLabelframe.Label",
            background="#2e2e2e",
            foreground="white",
            font=("Arial", 11),
        )
        style.configure("TNotebook", background="#2e2e2e", borderwidth=0)
        style.configure(
            "TNotebook.Tab", background="#555", foreground="white", padding=[10, 5]
        )
        style.map(
            "TNotebook.Tab", background=[("selected", "#007acc"), ("active", "#666")]
        )

    # --- 4. ZPRACOVÁNÍ UDÁLOSTÍ (EVENT HANDLING) ---
    # Metoda _bind_events propojí akce uživatele (klik, pohyb myši) s obslužnými funkcemi (on_press, on_drag).
    # Metody 'on_...' jsou pasivní funkce, které čekají na spuštění akcí uživatele.

    def _bind_events(self):
        self.preview_canvas.bind("<ButtonPress-1>", self.on_press)
        self.preview_canvas.bind("<B1-Motion>", self.on_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self.on_release)
        self.preview_canvas.bind("<Motion>", self.on_mouse_move)
        self.preview_canvas.bind("<ButtonPress-2>", self.on_pan_start)
        self.preview_canvas.bind("<B2-Motion>", self.on_pan_move)
        self.preview_canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.preview_canvas.bind("<Button-4>", self.on_mouse_wheel)
        self.preview_canvas.bind("<Button-5>", self.on_mouse_wheel)
        self.bind("<Configure>", self.trigger_update)

    def load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if not path:
            return
        try:
            with Image.open(path) as img:
                img = ImageOps.exif_transpose(img)
                if img.mode == "RGBA":
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    self.original_pil_image = bg
                else:
                    self.original_pil_image = img.copy()
            self.active_pil_image = self.original_pil_image.copy()
            self.revert_mask_btn.config(state="disabled")
            self.file_label.config(text=os.path.basename(path))
            self.convert_btn.config(state="normal")
            self.clear_current_selection()
            self.update_and_redraw()
            self.reset_view()
        except Exception as e:
            messagebox.showerror("Image Error", f"Could not load image: {e}")

    # --- 5. LOGIKA APLIKACE A PROPOJENÍ S BACKENDEM ---
    # Metoda 'update_and_redraw' je centrální bod pro aktualizaci náhledu obrázku na základě nastavení.
    # Využívá se "debouncing" (v metodě trigger_update), aby se předešlo zahlcení procesoru při rychlých změnách (např. rychlý pohyb posuvníku).
    # Konverze na STL běží ve vedlejším vlákně (threading.Thread), aby hlavní okno aplikace během výpočtu nezamrzlo.
    # Komunikace z vedlejšího vlákna zpět do hlavního (pro aktualizaci GUI) probíhá bezpečně pomocí metody 'self.after()'.

    def trigger_update(self, *args):
        if self.debounce_timer:
            self.after_cancel(self.debounce_timer)
        self.debounce_timer = self.after(150, self.update_and_redraw)

    def trigger_update_from_trace(self, *args):
        self.trigger_update()

    def update_and_redraw(self):
        if not self.active_pil_image:
            return
        self.processed_pil_image = process_image(
            self.active_pil_image,
            self.contrast_var.get(),
            self.brightness_var.get(),
            self.smoothing_var.get(),
            self.invert_colors_var.get(),
            self.use_threshold_var.get(),
            self.threshold_level_var.get(),
            self.dilate_var.get(),
            self.erode_var.get(),
            self.noise_reduction_var.get(),
            self.use_stroke_var.get(),
            self.stroke_thickness_var.get(),
        )
        self.redraw_canvas()

    def redraw_canvas(self):
        if not self.active_pil_image:
            self.preview_canvas.delete("all")
            return
        canvas_w, canvas_h = (
            self.preview_canvas.winfo_width(),
            self.preview_canvas.winfo_height(),
        )
        if canvas_w < 2 or canvas_h < 2:
            return
        if self.processed_pil_image:
            visible_img_x1 = int(self.view_offset_x)
            visible_img_y1 = int(self.view_offset_y)
            visible_img_x2 = int(self.view_offset_x + canvas_w / self.zoom_level)
            visible_img_y2 = int(self.view_offset_y + canvas_h / self.zoom_level)
            try:
                cropped_img = self.processed_pil_image.crop(
                    (visible_img_x1, visible_img_y1, visible_img_x2, visible_img_y2)
                )
                display_img = cropped_img.resize(
                    (canvas_w, canvas_h), Image.Resampling.LANCZOS
                )
                self.tk_image = ImageTk.PhotoImage(display_img)
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
            except Exception:
                pass
        if self.current_selection_points:
            image_points = self._get_final_shape_points()
            if len(image_points) > 1:
                canvas_points_to_draw = [
                    self.image_to_canvas_coords(x, y) for x, y in image_points
                ]
                self.preview_canvas.create_polygon(
                    canvas_points_to_draw, outline="cyan", fill="", width=2
                )

    def start_conversion(self):
        if not self.processed_pil_image:
            messagebox.showwarning(
                "Missing Image", "Please load and process an image first."
            )
            return
        stl_path = filedialog.asksaveasfilename(
            defaultextension=".stl", filetypes=[("STL Files", "*.stl")]
        )
        if not stl_path:
            return
        self.convert_btn.config(state="disabled")
        params = self.get_params_as_dict()
        thread = threading.Thread(
            target=self.run_conversion_thread,
            args=(self.processed_pil_image, stl_path, params),
        )
        thread.daemon = True
        thread.start()

    def get_params_as_dict(self):
        return {
            "model_width_mm": self.model_width_var.get(),
            "base_height": self.base_height_var.get(),
            "model_height": self.model_height_var.get(),
            "mirror_output": self.mirror_output_var.get(),
            "is_binary": self.binary_format_var.get(),
            "use_cutting_margin": self.use_cutting_margin_var.get(),
            "export_relief_only": self.export_relief_only_var.get(),
            "flat_bottom": self.flat_bottom_var.get(),
        }

    def run_conversion_thread(self, processed_image, stl_path, params):
        update_ui = lambda p: self.after(0, self._update_progress_ui, p)

        result = image_to_stl(processed_image, stl_path, params, update_ui)

        self.after(0, self.finish_conversion, result, stl_path)

    def finish_conversion(self, result, stl_path):
        if result is True:
            self.progress_label.config(text="Done!")
            messagebox.showinfo("Success", f"Model successfully saved to:\n{stl_path}")
        else:
            self.progress_label.config(text="Conversion failed.")
            self.progress_var.set(0)
            messagebox.showerror(
                "Conversion Error", f"Failed to generate STL file.\n\nError: {result}"
            )
        self.convert_btn.config(state="normal")

    # --- 6. POMOCNÉ METODY (UTILITY) ---

    def _update_progress_ui(self, percentage):
        self.progress_var.set(percentage)
        self.progress_label.config(text=f"{percentage:.0f}%")

    def on_mouse_wheel(self, event):
        if not self.original_pil_image:
            return
        zoom_factor = 0.9 if (event.num == 5 or event.delta < 0) else 1.1
        img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
        self.zoom_level *= zoom_factor
        self.zoom_level = max(0.1, min(self.zoom_level, 20))
        self.view_offset_x = img_x - (event.x / self.zoom_level)
        self.view_offset_y = img_y - (event.y / self.zoom_level)
        self.redraw_canvas()

    def on_pan_start(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def on_pan_move(self, event):
        if not self.original_pil_image:
            return
        dx = (event.x - self.pan_start_x) / self.zoom_level
        dy = (event.y - self.pan_start_y) / self.zoom_level
        self.view_offset_x -= dx
        self.view_offset_y -= dy
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.redraw_canvas()

    def reset_view(self):
        self.zoom_level = 1.0
        self.view_offset_x = 0
        self.view_offset_y = 0
        if self.original_pil_image:
            canvas_w, canvas_h = (
                self.preview_canvas.winfo_width(),
                self.preview_canvas.winfo_height(),
            )
            img_w, img_h = self.original_pil_image.size
            if img_w > 0 and img_h > 0:
                self.zoom_level = min(canvas_w / img_w, canvas_h / img_h)
                self.view_offset_x = (img_w - canvas_w / self.zoom_level) / 2
                self.view_offset_y = (img_h - canvas_h / self.zoom_level) / 2
        self.redraw_canvas()

    def canvas_to_image_coords(self, canvas_x, canvas_y):
        return (
            self.view_offset_x + (canvas_x / self.zoom_level),
            self.view_offset_y + (canvas_y / self.zoom_level),
        )

    def image_to_canvas_coords(self, img_x, img_y):
        return (
            (img_x - self.view_offset_x) * self.zoom_level,
            (img_y - self.view_offset_y) * self.zoom_level,
        )

    def on_press(self, event):
        if not self.active_pil_image:
            return
        img_coords = self.canvas_to_image_coords(event.x, event.y)
        mode = self.selection_mode.get()
        if mode == "Polygon":
            self.current_selection_points.append(img_coords)
        else:
            self.current_selection_points = [img_coords, img_coords]
        self.is_drawing_shape = True
        self.apply_mask_btn.config(state="disabled")

    def on_drag(self, event):
        if not self.is_drawing_shape or not self.current_selection_points:
            return
        self.current_selection_points[-1] = self.canvas_to_image_coords(
            event.x, event.y
        )
        self.redraw_canvas()

    def on_release(self, event):
        if not self.is_drawing_shape:
            return
        if self.selection_mode.get() != "Polygon":
            self.is_drawing_shape = False
        if len(self.current_selection_points) > 1:
            self.apply_mask_btn.config(state="normal")
        self.redraw_canvas()

    def on_mouse_move(self, event):
        if not self.is_drawing_shape or not self.current_selection_points:
            return
        mode = self.selection_mode.get()
        if mode in ["Hexagon", "Heart"]:
            self.current_selection_points[-1] = self.canvas_to_image_coords(
                event.x, event.y
            )
            self.redraw_canvas()

    def apply_mask(self):
        if not self.active_pil_image:
            return

        if len(self.current_selection_points) < 2:
            return
        image_points = self._get_final_shape_points()
        if len(image_points) < 3:
            return
        mask = Image.new("L", self.active_pil_image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.polygon(image_points, fill=255)
        if self.invert_polygon_var.get():
            mask = ImageOps.invert(mask)
        img_gray = self.active_pil_image.copy().convert("L")
        black_bg = Image.new("L", self.active_pil_image.size, 0)
        self.active_pil_image = Image.composite(img_gray, black_bg, mask)
        self.revert_mask_btn.config(state="normal")
        self.clear_current_selection()
        self.trigger_update()

    def revert_mask(self):
        if not self.original_pil_image:
            return
        self.active_pil_image = self.original_pil_image.copy()
        self.revert_mask_btn.config(state="disabled")
        self.trigger_update()

    def _get_final_shape_points(self):
        mode = self.selection_mode.get()
        points = self.current_selection_points
        if not points:
            return []

        if mode == "Rectangle" and len(points) >= 2:
            x1, y1 = points[0]
            x2, y2 = points[-1]
            return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]

        if mode in ["Hexagon", "Heart"] and len(points) >= 2:
            center_x, center_y = points[0]
            edge_x, edge_y = points[-1]
            dx, dy = edge_x - center_x, edge_y - center_y
            radius, angle_offset = math.sqrt(dx**2 + dy**2), math.atan2(dy, dx)
            final_points = []

            if mode == "Hexagon" and radius > 0:
                for i in range(6):
                    angle = (math.pi / 3 * i) + angle_offset
                    final_points.append(
                        (
                            center_x + radius * math.cos(angle),
                            center_y + radius * math.sin(angle),
                        )
                    )
            elif mode == "Heart" and radius > 0:
                for i in range(100):
                    t = 2 * math.pi * i / 100
                    x = center_x + radius * (16 * math.sin(t) ** 3) / 13
                    y = (
                        center_y
                        - radius
                        * (
                            13 * math.cos(t)
                            - 5 * math.cos(2 * t)
                            - 2 * math.cos(3 * t)
                            - math.cos(4 * t)
                        )
                        / 13
                    )
                    final_points.append((x, y))
            return final_points

        return points

    def undo_last_point(self):
        if self.current_selection_points:
            self.current_selection_points.pop()
            if not self.current_selection_points:
                self.apply_mask_btn.config(state="disabled")
                self.is_drawing_shape = False
            self.redraw_canvas()

    def clear_current_selection(self):
        self.current_selection_points = []
        self.apply_mask_btn.config(state="disabled")
        self.is_drawing_shape = False
        self.redraw_canvas()

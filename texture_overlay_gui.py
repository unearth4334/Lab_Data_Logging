#!/usr/bin/env python3
"""
Texture Overlay GUI (Tkinter + OpenCV)

Features
- Load a "texture source" image
- Extract a texture layer (frequency separation / high-pass) with tunable sliders
- Preview the extracted texture layer
- Load a "base" image
- Overlay the extracted texture onto the base with:
    - opacity slider
    - blend mode (multiply / overlay-like / add)
    - 4 draggable corners (manual perspective warp) to align the texture to the base
- Export a composited image (and/or the extracted texture)

Deps:
  pip install opencv-python pillow numpy
"""

import os
import math
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

import numpy as np
import cv2
from PIL import Image, ImageTk


# ---------------------------
# Image / texture processing
# ---------------------------

def cv_to_pil_rgb(cv_bgr: np.ndarray) -> Image.Image:
    rgb = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)

def pil_to_cv_bgr(pil_img: Image.Image) -> np.ndarray:
    rgb = np.array(pil_img.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

def clamp01(x: np.ndarray) -> np.ndarray:
    return np.clip(x, 0.0, 1.0)

def extract_texture_layer(
    src_bgr: np.ndarray,
    blur_sigma: float = 25.0,
    gain: float = 2.0,
    offset: float = 0.0,
    denoise: float = 0.0,
    use_clahe: bool = False,
    clahe_clip: float = 2.0,
    clahe_grid: int = 8,
    gray_mix: float = 0.0,
) -> np.ndarray:
    """
    Returns a texture layer as an 8-bit BGR image (visually centered around mid-gray).
    Implementation:
      - Convert to LAB to separate luminance
      - Optionally CLAHE on L
      - High-pass: L - GaussianBlur(L)
      - Gain + offset
      - Optional denoise (bilateral)
      - Re-embed into a neutral "texture map" (mid-gray + highpass)
    """
    src = src_bgr.copy()

    lab = cv2.cvtColor(src, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)

    if use_clahe:
        g = max(2, int(clahe_grid))
        clahe = cv2.createCLAHE(clipLimit=max(0.1, float(clahe_clip)), tileGridSize=(g, g))
        L = clahe.apply(L)

    Lf = L.astype(np.float32) / 255.0

    sigma = max(0.1, float(blur_sigma))
    # kernel size heuristic from sigma
    k = int(max(3, (sigma * 6) // 2 * 2 + 1))  # odd
    blur = cv2.GaussianBlur(Lf, (k, k), sigmaX=sigma, sigmaY=sigma, borderType=cv2.BORDER_REFLECT)

    hp = (Lf - blur)  # roughly [-0.5, 0.5] but typically smaller
    hp = hp * float(gain) + float(offset)

    # Optional denoise on high-pass (convert to 0..1 temporarily)
    tex = 0.5 + hp
    tex = clamp01(tex)

    if denoise > 0.0:
        # bilateral expects 0..255 uint8; denoise parameter controls d/sigmas
        d = int(max(3, min(25, denoise)))
        sig_c = float(10 + denoise * 3)
        sig_s = float(10 + denoise * 3)
        tex_u8 = (tex * 255.0).astype(np.uint8)
        tex_u8 = cv2.bilateralFilter(tex_u8, d=d, sigmaColor=sig_c, sigmaSpace=sig_s)
        tex = tex_u8.astype(np.float32) / 255.0

    # Optionally mix toward grayscale texture
    if gray_mix > 0.0:
        g = clamp01(tex)
        tex = (1.0 - gray_mix) * tex + gray_mix * g

    tex_u8 = (tex * 255.0).astype(np.uint8)
    # Make a neutral BGR texture map
    texture_bgr = cv2.merge([tex_u8, tex_u8, tex_u8])
    return texture_bgr


def blend_texture_over_base(base_bgr: np.ndarray, tex_bgr: np.ndarray, opacity: float, mode: str) -> np.ndarray:
    """
    base_bgr, tex_bgr: uint8 BGR, same size
    opacity: 0..1
    mode: "multiply", "overlay", "add"
    """
    b = base_bgr.astype(np.float32) / 255.0
    t = tex_bgr.astype(np.float32) / 255.0  # neutral around 0.5

    if mode == "multiply":
        # interpret texture as modulation around 0.5
        # map [0..1] -> [0..2] with 0.5 -> 1.0
        m = (t / 0.5)
        m = np.clip(m, 0.0, 2.0)
        out = b * m
    elif mode == "add":
        # add signed highpass around 0.5
        hp = (t - 0.5) * 2.0  # [-1..1]
        out = b + hp * 0.25   # conservative add
    else:
        # overlay-like: classic overlay formula on grayscale texture
        # Here texture is gray; treat it as blend layer
        out = np.empty_like(b)
        mask = b <= 0.5
        out[mask] = 2.0 * b[mask] * t[mask]
        out[~mask] = 1.0 - 2.0 * (1.0 - b[~mask]) * (1.0 - t[~mask])

    out = clamp01(out)
    out = (1.0 - opacity) * b + opacity * out
    out = clamp01(out)
    return (out * 255.0).astype(np.uint8)


# ---------------------------
# Display utilities
# ---------------------------

class CanvasImage:
    """
    Helper to draw an image on a Tk canvas with scaling.
    Keeps mapping between "image coordinates" and "canvas coordinates".
    """

    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.photo = None
        self.img_id = None

        self.cv_img = None  # BGR uint8
        self.disp_w = 1
        self.disp_h = 1
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

    def set_image(self, cv_bgr: np.ndarray):
        self.cv_img = cv_bgr

    def redraw(self):
        if self.cv_img is None:
            self.canvas.delete("all")
            return

        cw = max(1, self.canvas.winfo_width())
        ch = max(1, self.canvas.winfo_height())
        h, w = self.cv_img.shape[:2]

        # Fit to canvas
        s = min(cw / w, ch / h)
        self.scale = s
        self.disp_w = int(w * s)
        self.disp_h = int(h * s)
        self.offset_x = (cw - self.disp_w) // 2
        self.offset_y = (ch - self.disp_h) // 2

        disp = cv2.resize(self.cv_img, (self.disp_w, self.disp_h), interpolation=cv2.INTER_AREA)
        pil = cv_to_pil_rgb(disp)
        self.photo = ImageTk.PhotoImage(pil)

        self.canvas.delete("all")
        self.img_id = self.canvas.create_image(self.offset_x, self.offset_y, anchor="nw", image=self.photo)

    def img_to_canvas(self, x_img: float, y_img: float):
        x = self.offset_x + x_img * self.scale
        y = self.offset_y + y_img * self.scale
        return x, y

    def canvas_to_img(self, x_can: float, y_can: float):
        x = (x_can - self.offset_x) / self.scale
        y = (y_can - self.offset_y) / self.scale
        return x, y

    def in_image_bounds_canvas(self, x_can: float, y_can: float) -> bool:
        return (self.offset_x <= x_can <= self.offset_x + self.disp_w) and (self.offset_y <= y_can <= self.offset_y + self.disp_h)


# ---------------------------
# Main GUI
# ---------------------------

class TextureOverlayApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Texture Extract + Perspective Overlay Tool")
        self.geometry("1400x800")

        # Data
        self.src_tex_bgr = None          # original texture source
        self.extracted_tex_bgr = None    # extracted texture map (gray BGR)
        self.base_bgr = None             # base image
        self.composite_bgr = None        # base + warped texture

        self.warp_corners = None         # 4 points in base image coords: TL, TR, BR, BL
        self.drag_idx = None             # corner index being dragged

        # UI Vars
        self.var_blur = tk.DoubleVar(value=25.0)
        self.var_gain = tk.DoubleVar(value=2.0)
        self.var_offset = tk.DoubleVar(value=0.0)
        self.var_denoise = tk.DoubleVar(value=0.0)
        self.var_use_clahe = tk.BooleanVar(value=False)
        self.var_clahe_clip = tk.DoubleVar(value=2.0)
        self.var_clahe_grid = tk.IntVar(value=8)
        self.var_gray_mix = tk.DoubleVar(value=0.0)

        self.var_opacity = tk.DoubleVar(value=0.65)
        self.var_mode = tk.StringVar(value="multiply")

        # Layout
        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        root = ttk.Panedwindow(self, orient="horizontal")
        root.pack(fill="both", expand=True)

        # Left controls
        left = ttk.Frame(root, padding=10)
        root.add(left, weight=0)

        # Right view
        right = ttk.Frame(root, padding=10)
        root.add(right, weight=1)

        # --- Controls ---
        ttk.Label(left, text="1) Texture Source").pack(anchor="w", pady=(0, 4))
        row = ttk.Frame(left); row.pack(fill="x", pady=2)
        ttk.Button(row, text="Open Texture Image…", command=self.open_texture).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Save Extracted Texture…", command=self.save_extracted_texture).pack(side="left", padx=6)

        ttk.Separator(left).pack(fill="x", pady=8)

        ttk.Label(left, text="2) Texture Extraction").pack(anchor="w", pady=(0, 4))
        self._slider(left, "Blur sigma (illumination)", self.var_blur, 1, 120, self.on_params_changed)
        self._slider(left, "Gain (texture strength)", self.var_gain, 0.0, 8.0, self.on_params_changed, resolution=0.05)
        self._slider(left, "Offset", self.var_offset, -0.5, 0.5, self.on_params_changed, resolution=0.01)
        self._slider(left, "Denoise (bilateral)", self.var_denoise, 0.0, 25.0, self.on_params_changed, resolution=1.0)
        self._slider(left, "Gray mix", self.var_gray_mix, 0.0, 1.0, self.on_params_changed, resolution=0.01)

        chk = ttk.Checkbutton(left, text="Use CLAHE on luminance (boost local contrast)", variable=self.var_use_clahe, command=self.on_params_changed)
        chk.pack(anchor="w", pady=(6, 2))
        self._slider(left, "CLAHE clip", self.var_clahe_clip, 0.1, 8.0, self.on_params_changed, resolution=0.1)
        self._slider(left, "CLAHE grid", self.var_clahe_grid, 2, 16, self.on_params_changed, resolution=1)

        ttk.Separator(left).pack(fill="x", pady=8)

        ttk.Label(left, text="3) Base + Overlay").pack(anchor="w", pady=(0, 4))
        row2 = ttk.Frame(left); row2.pack(fill="x", pady=2)
        ttk.Button(row2, text="Open Base Image…", command=self.open_base).pack(side="left", fill="x", expand=True)
        ttk.Button(row2, text="Reset Corners", command=self.reset_corners).pack(side="left", padx=6)

        self._slider(left, "Opacity", self.var_opacity, 0.0, 1.0, self.on_params_changed, resolution=0.01)

        ttk.Label(left, text="Blend mode").pack(anchor="w", pady=(6, 2))
        modes = ttk.Combobox(left, textvariable=self.var_mode, values=["multiply", "overlay", "add"], state="readonly")
        modes.pack(fill="x")
        modes.bind("<<ComboboxSelected>>", lambda e: self.on_params_changed())

        ttk.Separator(left).pack(fill="x", pady=8)

        ttk.Button(left, text="Save Composite…", command=self.save_composite).pack(fill="x", pady=2)
        ttk.Label(left, text="Tip: Drag the 4 corner handles on the right view to align perspective.",
                  wraplength=300).pack(anchor="w", pady=(10, 0))

        # --- Viewer ---
        ttk.Label(right, text="Preview (base + warped texture) — drag corners").pack(anchor="w")
        self.canvas = tk.Canvas(right, bg="#222222", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, pady=(8, 0))

        self.viewer = CanvasImage(self.canvas)

    def _slider(self, parent, label, var, vmin, vmax, callback, resolution=1.0):
        ttk.Label(parent, text=label).pack(anchor="w", pady=(6, 2))
        s = ttk.Scale(parent, from_=vmin, to=vmax, variable=var, command=lambda _v: callback())
        s.pack(fill="x")
        # show value
        val = ttk.Label(parent, textvariable=tk.StringVar())
        val.pack(anchor="e")
        def refresh_label(*_):
            try:
                if isinstance(var.get(), float):
                    val.config(text=f"{var.get():.3f}")
                else:
                    val.config(text=f"{int(var.get())}")
            except Exception:
                pass
        var.trace_add("write", refresh_label)
        refresh_label()

        # resolution for IntVar-ish sliders: not native in ttk.Scale, so we quantize on callback
        if resolution != 1.0:
            # keep as-is; user can type exact values if they want (we’re not adding entry fields here)
            pass

        return s

    def _bind_events(self):
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    # ---------------------------
    # File I/O
    # ---------------------------

    def open_texture(self):
        path = filedialog.askopenfilename(
            title="Open texture source image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp"), ("All files", "*.*")]
        )
        if not path:
            return
        img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            messagebox.showerror("Error", "Could not open image.")
            return
        self.src_tex_bgr = img
        self.recompute_texture()
        self.on_params_changed()

    def open_base(self):
        path = filedialog.askopenfilename(
            title="Open base image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp"), ("All files", "*.*")]
        )
        if not path:
            return
        img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            messagebox.showerror("Error", "Could not open image.")
            return
        self.base_bgr = img
        self.reset_corners()
        self.on_params_changed()

    def save_extracted_texture(self):
        if self.extracted_tex_bgr is None:
            messagebox.showinfo("Nothing to save", "Extracted texture not available yet.")
            return
        path = filedialog.asksaveasfilename(
            title="Save extracted texture",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPG", "*.jpg *.jpeg"), ("TIFF", "*.tif *.tiff")]
        )
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        ok = cv2.imencode(ext if ext else ".png", self.extracted_tex_bgr)[1]
        ok.tofile(path)

    def save_composite(self):
        if self.composite_bgr is None:
            messagebox.showinfo("Nothing to save", "Composite not available yet.")
            return
        path = filedialog.asksaveasfilename(
            title="Save composite image",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPG", "*.jpg *.jpeg"), ("TIFF", "*.tif *.tiff")]
        )
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        ok = cv2.imencode(ext if ext else ".png", self.composite_bgr)[1]
        ok.tofile(path)

    # ---------------------------
    # Core compute
    # ---------------------------

    def recompute_texture(self):
        if self.src_tex_bgr is None:
            self.extracted_tex_bgr = None
            return
        self.extracted_tex_bgr = extract_texture_layer(
            self.src_tex_bgr,
            blur_sigma=self.var_blur.get(),
            gain=self.var_gain.get(),
            offset=self.var_offset.get(),
            denoise=self.var_denoise.get(),
            use_clahe=self.var_use_clahe.get(),
            clahe_clip=self.var_clahe_clip.get(),
            clahe_grid=self.var_clahe_grid.get(),
            gray_mix=self.var_gray_mix.get(),
        )

    def reset_corners(self):
        if self.base_bgr is None:
            self.warp_corners = None
            return
        h, w = self.base_bgr.shape[:2]
        margin = int(min(w, h) * 0.08)
        self.warp_corners = np.array([
            [margin, margin],           # TL
            [w - margin, margin],       # TR
            [w - margin, h - margin],   # BR
            [margin, h - margin],       # BL
        ], dtype=np.float32)
        self.redraw()

    def update_composite(self):
        """
        Composite = base + warped texture (warped from extracted texture image)
        Warp uses 4 corners on base (dst), and uses full texture image rect as src.
        """
        if self.base_bgr is None:
            self.composite_bgr = None
            return

        base = self.base_bgr

        if self.extracted_tex_bgr is None:
            self.composite_bgr = base
            return

        tex = self.extracted_tex_bgr

        hb, wb = base.shape[:2]
        ht, wt = tex.shape[:2]

        if self.warp_corners is None:
            self.reset_corners()

        # Perspective warp: src is entire texture rect
        src_pts = np.array([
            [0, 0],
            [wt - 1, 0],
            [wt - 1, ht - 1],
            [0, ht - 1],
        ], dtype=np.float32)

        dst_pts = self.warp_corners.astype(np.float32)

        H = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped_tex = cv2.warpPerspective(tex, H, (wb, hb), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

        # Blend
        opacity = float(self.var_opacity.get())
        mode = self.var_mode.get()
        self.composite_bgr = blend_texture_over_base(base, warped_tex, opacity=opacity, mode=mode)

    def on_params_changed(self):
        # Quantize the int-ish var
        try:
            self.var_clahe_grid.set(int(round(self.var_clahe_grid.get())))
        except Exception:
            pass

        if self.src_tex_bgr is not None:
            self.recompute_texture()
        self.update_composite()
        self.redraw()

    # ---------------------------
    # Drawing + corner handles
    # ---------------------------

    def redraw(self):
        # Decide what to show
        if self.base_bgr is not None:
            self.update_composite()
            self.viewer.set_image(self.composite_bgr if self.composite_bgr is not None else self.base_bgr)
        elif self.extracted_tex_bgr is not None:
            self.viewer.set_image(self.extracted_tex_bgr)
        elif self.src_tex_bgr is not None:
            self.viewer.set_image(self.src_tex_bgr)
        else:
            self.viewer.set_image(None)

        self.viewer.redraw()
        self._draw_handles()

    def _draw_handles(self):
        # handles only when base image is loaded
        if self.base_bgr is None or self.warp_corners is None or self.viewer.cv_img is None:
            return

        # Draw on top of the image
        r = 8
        pts = self.warp_corners
        # convert to canvas coords
        cpts = [self.viewer.img_to_canvas(float(x), float(y)) for x, y in pts]

        # polygon
        self.canvas.create_line(*cpts[0], *cpts[1], *cpts[2], *cpts[3], *cpts[0],
                                fill="#00ff88", width=2, tags="handles")

        # handles
        for i, (cx, cy) in enumerate(cpts):
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                    fill="#00ff88", outline="#003322", width=2,
                                    tags=("handles", f"h{i}"))
            self.canvas.create_text(cx, cy - 14, text=["TL", "TR", "BR", "BL"][i],
                                    fill="#00ff88", font=("TkDefaultFont", 10, "bold"),
                                    tags="handles")

    # ---------------------------
    # Mouse interaction
    # ---------------------------

    def _hit_test_handle(self, x_can: float, y_can: float, radius: float = 14.0):
        if self.base_bgr is None or self.warp_corners is None:
            return None
        # image coords of mouse
        if not self.viewer.in_image_bounds_canvas(x_can, y_can):
            return None
        x_img, y_img = self.viewer.canvas_to_img(x_can, y_can)
        pts = self.warp_corners
        for i, (px, py) in enumerate(pts):
            if (x_img - px) ** 2 + (y_img - py) ** 2 <= radius ** 2:
                return i
        return None

    def on_mouse_down(self, event):
        if self.base_bgr is None or self.warp_corners is None:
            return
        idx = self._hit_test_handle(event.x, event.y)
        self.drag_idx = idx

    def on_mouse_drag(self, event):
        if self.drag_idx is None or self.base_bgr is None or self.warp_corners is None:
            return
        if not self.viewer.in_image_bounds_canvas(event.x, event.y):
            return
        x_img, y_img = self.viewer.canvas_to_img(event.x, event.y)
        h, w = self.base_bgr.shape[:2]
        x_img = float(np.clip(x_img, 0, w - 1))
        y_img = float(np.clip(y_img, 0, h - 1))
        self.warp_corners[self.drag_idx] = [x_img, y_img]
        self.on_params_changed()

    def on_mouse_up(self, _event):
        self.drag_idx = None


def main():
    app = TextureOverlayApp()
    app.mainloop()


if __name__ == "__main__":
    main()

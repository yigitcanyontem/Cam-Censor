import cv2
import customtkinter as ctk
from PIL import Image, ImageTk
import threading
import time
import multiprocessing
from engine import FallDetectionEngine

class FallDetectionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Basic Setup ---
        self.title("Gizlilik Esaslı Düşme Takibi")
        self.geometry("1100x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- Engine & Variables ---
        self.engine = None
        self.cap = None
        self.is_running = False
        self.is_surveillance = False
        self.multi_caps = []
        self.multi_engines = []
        self.source_var = ctk.StringVar(value="Tarama Yapılıyor...")
        self.frame_count = 0
        self.available_cameras = []
        self.is_preloading = True

        # --- Layout (Grid) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="DÜŞME TARAYICI", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Source Selection
        self.source_label = ctk.CTkLabel(self.sidebar_frame, text="Giriş Kaynağı:", anchor="w")
        self.source_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        self.source_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Taranıyor..."],
                                                    variable=self.source_var, command=self.change_source)
        self.source_optionemenu.grid(row=2, column=0, padx=20, pady=(0, 20))

        # Floor Sensitivity Slider
        self.floor_label = ctk.CTkLabel(self.sidebar_frame, text="Zemin Hassasiyeti (Alt %):", anchor="w")
        self.floor_label.grid(row=4, column=0, padx=20, pady=(10, 0))
        self.floor_slider = ctk.CTkSlider(self.sidebar_frame, from_=0, to=100, number_of_steps=20, command=self.update_floor_sensitivity)
        self.floor_slider.set(70) # Default to 70% bottom
        self.floor_slider.grid(row=5, column=0, padx=20, pady=(0, 20))

        # Control Buttons
        self.start_button = ctk.CTkButton(self.sidebar_frame, text="TAKİBİ BAŞLAT", fg_color="green", hover_color="darkgreen", command=self.toggle_monitoring)
        self.start_button.grid(row=4, column=0, padx=20, pady=10)

        self.surveillance_button = ctk.CTkButton(self.sidebar_frame, text="GÖZETİM MODU (TÜMÜ)", fg_color="purple", hover_color="darkmagenta", command=self.toggle_surveillance)
        self.surveillance_button.grid(row=5, column=0, padx=20, pady=10)

        # Settings
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Görünüm:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Koyu", "Açık", "Sistem"],
                                                            command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(0, 20))

        # --- Main Viewport ---
        self.viewport_frame = ctk.CTkFrame(self, fg_color="black")
        self.viewport_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.viewport_frame.grid_rowconfigure(0, weight=1)
        self.viewport_frame.grid_columnconfigure(0, weight=1)

        self.video_label = ctk.CTkLabel(self.viewport_frame, text="GÖRÜNTÜ BEKLENİYOR...", font=ctk.CTkFont(size=24))
        self.video_label.grid(row=0, column=0)

        # Status Bar
        self.status_bar = ctk.CTkLabel(self, text="Durum: BEKLEMEDE", anchor="w", fg_color="transparent")
        self.status_bar.grid(row=1, column=1, padx=20, pady=(0, 10), sticky="ew")

        # Background Preloading
        self.after(100, self.start_preloading)

    def change_appearance_mode(self, mode):
        modes = {"Koyu": "Dark", "Açık": "Light", "Sistem": "System"}
        ctk.set_appearance_mode(modes.get(mode, "Dark"))

    def start_preloading(self):
        # 1. Start Camera Detection in Thread
        threading.Thread(target=self.init_camera_list, daemon=True).start()
        # 2. Start Engine/AI Loading in Thread
        threading.Thread(target=self.preload_engine, daemon=True).start()

    def preload_engine(self):
        if self.engine is None:
            self.after(0, lambda: self.status_bar.configure(text="Durum: YAPAY ZEKA MODELLERİ YÜKLENİYOR...", text_color="yellow"))
            self.engine = FallDetectionEngine()
            self.engine.set_floor_level(self.floor_slider.get())
            self.is_preloading = False
            self.after(0, lambda: self.status_bar.configure(text="Durum: MODELLER HAZIR", text_color="green"))
            self.after(2000, lambda: self.status_bar.configure(text="Durum: BEKLEMEDE", text_color="white"))

    def init_camera_list(self):
        cameras = self.detect_cameras()
        self.after(0, self.update_camera_menu, cameras)

    def update_camera_menu(self, cameras):
        self.available_cameras = cameras
        self.source_optionemenu.configure(values=cameras)
        if cameras:
            self.source_var.set(cameras[0])
        self.status_bar.configure(text="Durum: BEKLEMEDE", text_color="white")

    def change_source(self, source):
        if self.is_running:
            self.stop_feed()
            self.after(500, self.start_feed)
        else:
            self.video_label.configure(text="BAŞLATILMASI BEKLENİYOR...", image=None)

    def toggle_monitoring(self):
        if self.is_surveillance:
            self.stop_feed()
        
        if not self.is_running:
            if self.is_preloading:
                self.status_bar.configure(text="Durum: MODELLERİN YÜKLENMESİ BEKLENİYOR...", text_color="yellow")
                self.after(500, self.toggle_monitoring)
                return
            self.start_feed()
        else:
            self.stop_feed()

    def toggle_surveillance(self):
        if not self.is_running:
            if self.is_preloading:
                self.status_bar.configure(text="Durum: MODELLERİN YÜKLENMESİ BEKLENİYOR...", text_color="yellow")
                self.after(500, self.toggle_surveillance)
                return
            self.start_multi_feed()
        else:
            self.stop_feed()

    def detect_cameras(self):
        self.after(0, lambda: self.status_bar.configure(text="Durum: KAMERALAR TARANIYOR...", text_color="yellow"))
        available = []
        for i in range(4):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available.append(f"Kamera {i}")
                cap.release()
        return available if available else ["Kamera Bulunamadı"]

    def start_feed(self):
        # UI Setup for Single Feed
        for widget in self.viewport_frame.winfo_children():
            widget.destroy()
        self.video_label = ctk.CTkLabel(self.viewport_frame, text="GÖRÜNTÜ BEKLENİYOR...", font=ctk.CTkFont(size=24))
        self.video_label.grid(row=0, column=0)

        # Extract index from "Kamera X"
        try:
            source_str = self.source_var.get()
            source = int(source_str.split(" ")[1])
        except:
            source = 0
            
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not self.cap.isOpened():
            self.status_bar.configure(text=f"Durum: HATA (Kaynak bulunamadı: {source})", text_color="red")
            return

        self.is_running = True
        self.is_surveillance = False
        self.start_button.configure(text="TAKİBİ DURDUR", fg_color="red", hover_color="darkred")
        self.status_bar.configure(text="Durum: TAKİP AKTİF", text_color="cyan")
        self.engine.reset_tracker()
        self.engine.set_fps(self.cap.get(cv2.CAP_PROP_FPS))
        
        self.processing_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.processing_thread.start()

    def start_multi_feed(self):
        # UI Setup for Grid
        for widget in self.viewport_frame.winfo_children():
            widget.destroy()
            
        self.multi_caps = []
        self.multi_engines = []
        self.grid_labels = []
        
        cams = [int(c.split(" ")[1]) for c in self.available_cameras if "Kamera" in c]
        if not cams:
            self.status_bar.configure(text="Durum: HATA (Kamera bulunamadı)", text_color="red")
            return
            
        num_cams = len(cams)
        cols = 2 if num_cams > 1 else 1
        rows = (num_cams + 1) // 2
        
        self.viewport_frame.grid_columnconfigure((0, 1), weight=1)
        self.viewport_frame.grid_rowconfigure((0, 1), weight=1)

        for i, idx in enumerate(cams):
            cap = cv2.VideoCapture(idx)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            if cap.isOpened():
                self.multi_caps.append(cap)
                engine = FallDetectionEngine()
                engine.set_floor_level(self.floor_slider.get())
                engine.set_fps(cap.get(cv2.CAP_PROP_FPS))
                self.multi_engines.append(engine)
                
                r, c = divmod(i, cols)
                label = ctk.CTkLabel(self.viewport_frame, text=f"Kamera {idx} Bekleniyor...", fg_color="black")
                label.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                self.grid_labels.append(label)
        
        if not self.multi_caps:
            self.status_bar.configure(text="Durum: HATA (Kameralar açılamadı)", text_color="red")
            return
            
        self.is_running = True
        self.is_surveillance = True
        self.surveillance_button.configure(text="GÖZETİMİ DURDUR", fg_color="red", hover_color="darkred")
        self.status_bar.configure(text="Durum: GÖZETİM MODU AKTİF", text_color="cyan")
        
        for i in range(len(self.multi_caps)):
            t = threading.Thread(target=self.multi_video_loop, args=(i,), daemon=True)
            t.start()

    def stop_feed(self):
        self.is_running = False
        self.after(200, self._release_resources)

    def _release_resources(self):
        # Release Single Cap
        if self.cap:
            self.cap.release()
            self.cap = None
            
        # Release Multi Caps
        for cap in self.multi_caps:
            cap.release()
        self.multi_caps = []
        self.multi_engines = []
        
        self.is_surveillance = False
        self.start_button.configure(text="TAKİBİ BAŞLAT", fg_color="green", hover_color="darkgreen")
        self.surveillance_button.configure(text="GÖZETİM MODU (TÜMÜ)", fg_color="purple", hover_color="darkmagenta")
        self.status_bar.configure(text="Durum: BEKLEMEDE", text_color="white")
        
        # Reset Viewport if it was grid
        if len(self.viewport_frame.winfo_children()) > 1:
            for widget in self.viewport_frame.winfo_children():
                widget.destroy()
            self.video_label = ctk.CTkLabel(self.viewport_frame, text="TAKİP DURDURULDU", font=ctk.CTkFont(size=24))
            self.video_label.grid(row=0, column=0)
        else:
            self.video_label.configure(text="TAKİP DURDURULDU", image=None)

    def update_floor_sensitivity(self, value):
        if self.engine:
            self.engine.set_floor_level(value)
            self.status_bar.configure(text=f"Durum: Zemin Hassasiyeti %{int(value)} olarak ayarlandı")

    def video_loop(self):
        failed_frames = 0
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                failed_frames += 1
                if failed_frames > 30: # ~1 second of failure
                    self.after(0, lambda: self.status_bar.configure(text="Durum: VERİ BEKLENİYOR (Kamerayı Kontrol Edin)", text_color="yellow"))
                time.sleep(0.01)
                continue

            if failed_frames > 0:
                self.after(0, lambda: self.status_bar.configure(text="Durum: TAKİP AKTİF", text_color="cyan"))
                failed_frames = 0

            # Frame Processing
            self.frame_count += 1
            # We pass 'censor=privacy_enabled.get()' to the engine
            processed_frame, fall_detected = self.engine.process_frame(
                frame, 
                self.frame_count, 
                censor=True, # Privacy is always enabled
                draw_alert=True
            )
            
            display_frame = processed_frame
            
            # Update Status if Fall Detected
            if fall_detected:
                self.after(0, lambda: self.status_bar.configure(text="ALARM: DÜŞME ALGILANDI!", text_color="orange"))
            else:
                self.after(0, lambda: self.status_bar.configure(text="Durum: TAKİP AKTİF", text_color="cyan"))

            # Convert to RGB for Tkinter
            img_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            
            
            # Use CTkImage for scaling support
            w, h = self.viewport_frame.winfo_width(), self.viewport_frame.winfo_height()
            if w < 100 or h < 100:
                w, h = 640, 480 # Fallback
            
            ctk_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(w-40, h-40))

            # Update Label (GUI thread)
            self.after(0, self.update_video, ctk_img)
            
            # Control Frame Rate (mostly for file playback, but keep for stability)
            time.sleep(0.001) 

    def update_video(self, ctk_img):
        if self.is_running and not self.is_surveillance:
            self.video_label.configure(image=ctk_img, text="")

    def multi_video_loop(self, index):
        cap = self.multi_caps[index]
        engine = self.multi_engines[index]
        label = self.grid_labels[index]
        frame_count = 0
        
        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame_count += 1
            processed_frame, fall_detected = engine.process_frame(
                frame, 
                frame_count, 
                censor=True,
                draw_alert=True
            )
            
            img_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            
            # Grid scaling
            w = self.viewport_frame.winfo_width() // 2
            h = self.viewport_frame.winfo_height() // ((len(self.multi_caps) + 1) // 2)
            if w < 100 or h < 100: w, h = 320, 240
            
            ctk_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(w-10, h-10))
            self.after(0, lambda img=ctk_img, lbl=label: lbl.configure(image=img, text=""))
            
            time.sleep(0.001)

    def on_closing(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        for cap in self.multi_caps:
            cap.release()
        self.destroy()

if __name__ == "__main__":
    # Essential for PyInstaller + Multiprocessing (used internally by YOLO/OpenCV)
    multiprocessing.freeze_support()
    
    app = FallDetectionApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

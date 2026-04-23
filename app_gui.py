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
        self.title("Cam-Censor: Akıllı Gizlilik Koruması")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- Engine & Variables ---
        self.engine = None
        self.cap = None
        self.is_running = False
        self.is_surveillance = False
        self.is_simulation = False
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
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="CAM-CENSOR", font=ctk.CTkFont(size=24, weight="bold", family="Inter"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 5))
        
        self.subtitle_label = ctk.CTkLabel(self.sidebar_frame, text="7/24 Kesintisiz Güvenlik", font=ctk.CTkFont(size=12))
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # --- Control Card ---
        self.control_card = ctk.CTkFrame(self.sidebar_frame, fg_color="#2b2b2b", corner_radius=12)
        self.control_card.grid(row=2, column=0, padx=15, pady=10, sticky="ew")

        self.start_button = ctk.CTkButton(self.control_card, text="TAKİBİ BAŞLAT", fg_color="#2ecc71", hover_color="#27ae60", height=45, font=ctk.CTkFont(weight="bold"), command=self.toggle_monitoring)
        self.start_button.pack(padx=15, pady=(15, 10), fill="x")

        self.surveillance_button = ctk.CTkButton(self.control_card, text="GÖZETİM MODU (TÜMÜ)", fg_color="#9b59b6", hover_color="#8e44ad", height=45, font=ctk.CTkFont(weight="bold"), command=self.toggle_surveillance)
        self.surveillance_button.pack(padx=15, pady=(0, 15), fill="x")

        # --- Settings Card ---
        self.settings_card = ctk.CTkFrame(self.sidebar_frame, fg_color="#2b2b2b", corner_radius=12)
        self.settings_card.grid(row=3, column=0, padx=15, pady=10, sticky="ew")

        self.source_label = ctk.CTkLabel(self.settings_card, text="Giriş Kaynağı:", font=ctk.CTkFont(size=13, weight="bold"))
        self.source_label.pack(padx=15, pady=(15, 5), anchor="w")
        self.source_optionemenu = ctk.CTkOptionMenu(self.settings_card, values=["Taranıyor..."], variable=self.source_var, command=self.change_source)
        self.source_optionemenu.pack(padx=15, pady=(0, 15), fill="x")

        self.floor_label = ctk.CTkLabel(self.settings_card, text="Zemin Hassasiyeti:", font=ctk.CTkFont(size=13, weight="bold"))
        self.floor_label.pack(padx=15, pady=(5, 0), anchor="w")
        self.floor_slider = ctk.CTkSlider(self.settings_card, from_=0, to=100, number_of_steps=20, command=self.update_floor_sensitivity)
        self.floor_slider.set(70)
        self.floor_slider.pack(padx=15, pady=(5, 20), fill="x")

        # --- Appearance ---
        self.appearance_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.appearance_frame.grid(row=8, column=0, padx=15, pady=10, sticky="ew")
        
        self.appearance_mode_label = ctk.CTkLabel(self.appearance_frame, text="Görünüm:", font=ctk.CTkFont(size=12))
        self.appearance_mode_label.pack(side="left", padx=(5, 5))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.appearance_frame, values=["Koyu", "Açık", "Sistem"], width=120, command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.pack(side="left", fill="x", expand=True)

        self.sim_switch = ctk.CTkSwitch(self.sidebar_frame, text="Simülasyon Modu", command=self.toggle_simulation)
        self.sim_switch.grid(row=9, column=0, padx=15, pady=10, sticky="ew")

        # --- Tip Section ---
        self.tip_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="#3d3d3d", corner_radius=8)
        self.tip_frame.grid(row=10, column=0, padx=15, pady=20, sticky="s")
        
        self.tip_label = ctk.CTkLabel(self.tip_frame, text="KULLANIM REHBERİ:\n\n"
                                      "• Takibi Başlat: Seçili tek kamerayı izler.\n"
                                      "• Gözetim Modu: Tüm kameraları ızgara düzeninde aynı anda izler.\n"
                                      "• Simülasyon: Tek kamerayı test için 3 adetmiş gibi gösterir.\n"
                                      "• Zemin Hassasiyeti: Kameranın açısına göre düşme eşiğini belirler (%70 önerilir).", 
                                      wraplength=240, font=ctk.CTkFont(size=11), text_color="#bbbbbb", justify="left")
        self.tip_label.pack(padx=10, pady=10)

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

    def toggle_simulation(self):
        self.is_simulation = self.sim_switch.get()
        self.init_camera_list()

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
        # If in surveillance mode, stop it first
        if self.is_surveillance:
            self.stop_feed()
            # Wait a bit and start single feed
            self.after(300, self.toggle_monitoring)
            return

        if not self.is_running:
            if self.is_preloading:
                self.status_bar.configure(text="Durum: MODELLERİN YÜKLENMESİ BEKLENİYOR...", text_color="yellow")
                self.after(500, self.toggle_monitoring)
                return
            self.start_feed()
        else:
            self.stop_feed()

    def toggle_surveillance(self):
        # If in single monitoring mode, stop it first
        if self.is_running and not self.is_surveillance:
            self.stop_feed()
            # Wait a bit and start surveillance
            self.after(300, self.toggle_surveillance)
            return

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
        
        if self.is_simulation:
            return ["Kamera 0", "Kamera 1 (Sim)", "Kamera 2 (Sim)"]
            
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
            self.video_label.configure(text="KAMERA BULUNAMADI\nLütfen bağlantıları kontrol edip tekrar deneyin.", text_color="red")
            return
            
        num_cams = len(cams)
        cols = 2 if num_cams > 1 else 1
        rows = (num_cams + 1) // 2
        
        # If simulation, same index might repeat. We need separate captures.
        actual_indices = [int(str(idx).split(" ")[0]) for idx in cams]

        self.viewport_frame.grid_columnconfigure((0, 1), weight=1)
        self.viewport_frame.grid_rowconfigure((0, 1), weight=1)

        if self.is_simulation:
            # Simulation: Open index 0 once, create 3 engines
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                self.multi_caps.append(cap)
                for i in range(3):
                    engine = FallDetectionEngine()
                    engine.set_floor_level(self.floor_slider.get())
                    engine.set_fps(cap.get(cv2.CAP_PROP_FPS))
                    self.multi_engines.append(engine)
                    
                    r, c = divmod(i, cols)
                    label = ctk.CTkLabel(self.viewport_frame, text=f"Sim Kamera {i} Bekleniyor...", fg_color="black")
                    label.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                    self.grid_labels.append(label)
        else:
            # Real cameras
            for i, idx in enumerate(actual_indices):
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
        
        if self.is_simulation:
            t = threading.Thread(target=self.simulation_loop, daemon=True)
            t.start()
        else:
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
            
            # Draw Label on Frame
            source_idx = self.available_cameras[index].split(" ")[1]
            cv2.putText(img_rgb, f"KAMERA {source_idx}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
            
            img_pil = Image.fromarray(img_rgb)
            
            # Aspect Ratio aware scaling
            target_w = self.viewport_frame.winfo_width() // 2
            target_h = self.viewport_frame.winfo_height() // ((len(self.multi_caps) + 1) // 2)
            if target_w < 100 or target_h < 100: target_w, target_h = 320, 240
            
            orig_w, orig_h = img_pil.size
            aspect = orig_w / orig_h
            if target_w / target_h > aspect:
                new_h = target_h - 10
                new_w = int(new_h * aspect)
            else:
                new_w = target_w - 10
                new_h = int(new_w / aspect)
            
            ctk_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(new_w, new_h))
            self.after(0, lambda img=ctk_img, lbl=label: lbl.configure(image=img, text=""))
            
            time.sleep(0.001)

    def simulation_loop(self):
        cap = self.multi_caps[0]
        engines = self.multi_engines
        labels = self.grid_labels
        frame_count = 0
        
        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame_count += 1
            
            # For simulation, we process the same frame with multiple engines
            for i in range(len(engines)):
                # Copy frame to avoid engines interfering with each other's drawings
                f_copy = frame.copy()
                processed_frame, _ = engines[i].process_frame(
                    f_copy, frame_count, censor=True, draw_alert=True
                )
                
                img_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                cv2.putText(img_rgb, f"KAMERA {i} (SIM)", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
                
                img_pil = Image.fromarray(img_rgb)
                
                # Aspect Ratio aware scaling
                target_w = self.viewport_frame.winfo_width() // 2
                target_h = self.viewport_frame.winfo_height() // 2 # 2 cams or 3 cams simulation
                if target_w < 100 or target_h < 100: target_w, target_h = 320, 240
                
                orig_w, orig_h = img_pil.size
                aspect = orig_w / orig_h
                if target_w / target_h > aspect:
                    new_h = target_h - 10
                    new_w = int(new_h * aspect)
                else:
                    new_w = target_w - 10
                    new_h = int(new_w / aspect)
                
                ctk_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(new_w, new_h))
                # Use a specific lambda to capture local loop variables
                self.after(0, lambda img=ctk_img, lbl=labels[i]: lbl.configure(image=img, text=""))
            
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

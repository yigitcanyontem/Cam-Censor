import cv2
import os
import customtkinter as ctk
from PIL import Image, ImageTk
import threading
import time
import multiprocessing
import json
from engine import PrivacyEngine

class CamCensorApp(ctk.CTk):
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

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="CAM-CENSOR", font=ctk.CTkFont(size=26, weight="bold", family="Inter"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 5))
        
        self.subtitle_label = ctk.CTkLabel(self.sidebar_frame, text="Smart Privacy Vault", font=ctk.CTkFont(size=12, slant="italic"))
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # --- Control Card ---
        self.control_card = ctk.CTkFrame(self.sidebar_frame, fg_color="#2b2b2b", corner_radius=10)
        self.control_card.grid(row=2, column=0, padx=15, pady=10, sticky="ew")
        
        self.control_label = ctk.CTkLabel(self.control_card, text="KONTROL MERKEZİ", font=ctk.CTkFont(size=13, weight="bold"))
        self.control_label.pack(pady=(10, 5))
        
        self.monitoring_button = ctk.CTkButton(self.control_card, text="TAKİBİ BAŞLAT", command=self.toggle_monitoring, 
                                               fg_color="#1f538d", hover_color="#14375e", height=40)
        self.monitoring_button.pack(padx=15, pady=5, fill="x")
        
        self.surveillance_button = ctk.CTkButton(self.control_card, text="GÖZETİM MODU (TÜMÜ)", command=self.toggle_surveillance,
                                                 fg_color="#5e35b1", hover_color="#4527a0", height=40)
        self.surveillance_button.pack(padx=15, pady=(5, 15), fill="x")

        # --- Settings Card ---
        self.settings_card = ctk.CTkFrame(self.sidebar_frame, fg_color="#2b2b2b", corner_radius=12)
        self.settings_card.grid(row=3, column=0, padx=15, pady=10, sticky="ew")

        self.source_optionemenu = ctk.CTkOptionMenu(self.settings_card, values=["Taranıyor..."], variable=self.source_var, command=self.change_source)
        self.source_optionemenu.pack(padx=15, pady=(0, 10), fill="x")

        self.rtsp_label = ctk.CTkLabel(self.settings_card, text="IP/RTSP Kamera Ekle:", font=ctk.CTkFont(size=12))
        self.rtsp_label.pack(padx=15, pady=0, anchor="w")
        self.rtsp_entry = ctk.CTkEntry(self.settings_card, placeholder_text="rtsp://...", height=30)
        self.rtsp_entry.pack(padx=15, pady=5, fill="x")
        self.add_rtsp_button = ctk.CTkButton(self.settings_card, text="AĞDAN EKLE", command=self.add_rtsp_source, 
                                             fg_color="#34495e", hover_color="#2c3e50")
        self.add_rtsp_button.pack(padx=15, pady=5, fill="x")

        self.remove_rtsp_button = ctk.CTkButton(self.settings_card, text="SEÇİLİ KAYNAĞI SİL", command=self.remove_current_source, 
                                                fg_color="#c0392b", hover_color="#a93226")
        self.remove_rtsp_button.pack(padx=15, pady=(0, 15), fill="x")

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
                                      "• Simülasyon: Tek kamerayı test için 3 adetmiş gibi gösterir.", 
                                      wraplength=240, font=ctk.CTkFont(size=11), text_color="#bbbbbb", justify="left")
        self.tip_label.pack(padx=10, pady=10)

        # --- Main Layout (Header + Viewport) ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.dashboard_title = ctk.CTkLabel(self.main_container, text="CANLI GÖZETİM PANELİ", 
                                            font=ctk.CTkFont(size=28, weight="bold"), anchor="w")
        self.dashboard_title.grid(row=0, column=0, padx=10, pady=(0, 20), sticky="w")

        self.viewport_frame = ctk.CTkFrame(self.main_container, fg_color="black", corner_radius=15)
        self.viewport_frame.grid(row=1, column=0, sticky="nsew")
        self.viewport_frame.grid_rowconfigure(0, weight=1)
        self.viewport_frame.grid_columnconfigure(0, weight=1)

        self.video_label = ctk.CTkLabel(self.viewport_frame, text="GÖRÜNTÜ BEKLENİYOR...", font=ctk.CTkFont(size=24))
        self.video_label.grid(row=0, column=0)

        # Status Bar
        self.status_bar = ctk.CTkLabel(self, text="Durum: BEKLEMEDE", anchor="w", fg_color="transparent")
        self.status_bar.grid(row=1, column=1, padx=30, pady=(0, 15), sticky="ew")
        self.is_simulation = False
        self.config_path = "config.json"
        self.network_cameras = []
        
        # Load Existing Configuration
        self.load_config()
        
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
            self.engine = PrivacyEngine()
            self.is_preloading = False

    def init_camera_list(self):
        cameras = self.detect_cameras()
        
        # Add persistent network cameras
        for cam in self.network_cameras:
            if cam not in cameras:
                cameras.insert(0, cam)
                
        self.available_cameras = cameras
        self.after(0, self.update_camera_menu, cameras)

    def update_camera_menu(self, cameras):
        self.available_cameras = cameras
        self.source_optionemenu.configure(values=cameras)
        if cameras:
            self.source_var.set(cameras[0])

    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    self.network_cameras = config.get("network_cameras", [])
        except Exception as e:
            print(f"Error loading config: {e}")

    def save_config(self):
        try:
            config = {"network_cameras": self.network_cameras}
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

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
                self.after(500, self.toggle_surveillance)
                return
            self.start_multi_feed()
        else:
            self.stop_feed()

    def detect_cameras(self):
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

        source_name = self.source_var.get()
        
        # Decide index or URL
        if "Kamera" in source_name and len(source_name.split(" ")) > 1:
            try:
                source = int(source_name.split(" ")[1])
            except ValueError:
                source = source_name
        else:
            source = source_name

        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not self.cap.isOpened():
            return

        self.is_running = True
        self.is_surveillance = False
        self.monitoring_button.configure(text="TAKİBİ DURDUR", fg_color="red", hover_color="darkred")
        self.engine.set_fps(self.cap.get(cv2.CAP_PROP_FPS))
        
        self.processing_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.processing_thread.start()

    def start_multi_feed(self):
        self.stop_feed()
        
        # Filter simulation if active
        if self.is_simulation:
            cams = [0, 1, 2]
        else:
            cams = []
            for c in self.available_cameras:
                if "Kamera" in c and "Sim" not in c:
                    try:
                        cams.append(int(c.split(" ")[1]))
                    except:
                        pass
                elif c.startswith("rtsp://") or c.startswith("http://"):
                    cams.append(c)
        
        if not cams:
            self.video_label.configure(text="KAMERA BULUNAMADI\nLütfen bağlantıları kontrol edip tekrar deneyin.", text_color="red")
            return
            
        num_cams = len(cams)
        cols = 2 if num_cams > 1 else 1
        rows = (num_cams + 1) // 2
        
        # If simulation, same index might repeat. We need separate captures.

        self.viewport_frame.grid_columnconfigure((0, 1), weight=1)
        self.viewport_frame.grid_rowconfigure((0, 1), weight=1)

        if self.is_simulation:
            # Simulation: Open index 0 once, create 3 engines
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                self.multi_caps.append(cap)
                for i in range(3):
                    engine = PrivacyEngine()
                    engine.set_fps(cap.get(cv2.CAP_PROP_FPS))
                    self.multi_engines.append(engine)
                    
                    r, c = divmod(i, cols)
                    label = ctk.CTkLabel(self.viewport_frame, text=f"Sim Kamera {i} Bekleniyor...", fg_color="black")
                    label.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                    self.grid_labels.append(label)
        else:
            # Real cameras
            for i, source in enumerate(cams):
                cap = cv2.VideoCapture(source)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                if cap.isOpened():
                    self.multi_caps.append(cap)
                    engine = PrivacyEngine()
                    self.multi_engines.append(engine)
                    
                    r, c = divmod(i, cols)
                    label_text = f"Kamera {source}" if isinstance(source, int) else "IP Kamera"
                    label = ctk.CTkLabel(self.viewport_frame, text=f"{label_text} Bekleniyor...", fg_color="black")
                    label.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                    self.grid_labels.append(label)
        
        if not self.multi_caps:
            return
            
        self.is_running = True
        self.is_surveillance = True
        self.surveillance_button.configure(text="GÖZETİMİ DURDUR", fg_color="red", hover_color="darkred")
        
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
        self.monitoring_button.configure(text="TAKİBİ BAŞLAT", fg_color="#1f538d", hover_color="#14375e")
        self.surveillance_button.configure(text="GÖZETİM MODU (TÜMÜ)", fg_color="#5e35b1", hover_color="#4527a0")
        
        # Reset Viewport if it was grid
        if len(self.viewport_frame.winfo_children()) > 1:
            for widget in self.viewport_frame.winfo_children():
                widget.destroy()
            self.video_label = ctk.CTkLabel(self.viewport_frame, text="TAKİP DURDURULDU", font=ctk.CTkFont(size=24))
            self.video_label.grid(row=0, column=0)
        else:
            self.video_label.configure(text="TAKİP DURDURULDU", image=None)

    def update_camera_source(self, choice):
        self.status_bar.configure(text=f"Kaynak Değiştirildi: {choice}", text_color="white")

    def add_rtsp_source(self):
        url = self.rtsp_entry.get().strip()
        if url:
            if url not in self.network_cameras:
                self.network_cameras.insert(0, url)
                self.save_config()
                self.init_camera_list() # Refresh UI
                self.source_var.set(url)
                self.rtsp_entry.delete(0, 'end')
                self.status_bar.configure(text="IP Kamera Kaydedildi", text_color="green")
            else:
                self.status_bar.configure(text="Bu kaynak zaten kayıtlı", text_color="yellow")

    def remove_current_source(self):
        source = self.source_var.get()
        if source in self.network_cameras:
            self.network_cameras.remove(source)
            self.save_config()
            self.init_camera_list() # Refresh UI
            self.status_bar.configure(text="Kaynak Silindi", text_color="red")
        else:
            self.status_bar.configure(text="Sadece eklenen IP kameraları silebilirsiniz", text_color="yellow")

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
            # We pass 'censor=True' to the engine
            processed_frame, _ = self.engine.process_frame(
                frame, 
                self.frame_count, 
                censor=True # Privacy is always enabled
            )
            
            display_frame = processed_frame
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
    
    app = CamCensorApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

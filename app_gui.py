import cv2
import customtkinter as ctk
from PIL import Image, ImageTk
import threading
import time
from engine import FallDetectionEngine

class FallDetectionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Basic Setup ---
        self.title("Privacy-Safe Fall Monitoring")
        self.geometry("1100x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- Engine & Variables ---
        self.engine = None # Initialize on start for faster GUI launch
        self.cap = None
        self.is_running = False
        self.privacy_enabled = ctk.BooleanVar(value=True)
        self.source_var = ctk.StringVar(value="Camera")
        self.frame_count = 0

        # --- Layout (Grid) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="FALL SCANNER", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Source Selection
        self.source_label = ctk.CTkLabel(self.sidebar_frame, text="Input Source:", anchor="w")
        self.source_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        self.source_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Camera", "File (test.mp4)"],
                                                    variable=self.source_var, command=self.change_source)
        self.source_optionemenu.grid(row=2, column=0, padx=20, pady=(0, 20))

        # Privacy Toggle
        self.privacy_switch = ctk.CTkSwitch(self.sidebar_frame, text="Privacy Censorship", variable=self.privacy_enabled)
        self.privacy_switch.grid(row=3, column=0, padx=20, pady=10)

        # Floor Sensitivity Slider
        self.floor_label = ctk.CTkLabel(self.sidebar_frame, text="Floor Sensitivity (Bottom %):", anchor="w")
        self.floor_label.grid(row=4, column=0, padx=20, pady=(10, 0))
        self.floor_slider = ctk.CTkSlider(self.sidebar_frame, from_=0, to=100, number_of_steps=20, command=self.update_floor_sensitivity)
        self.floor_slider.set(70) # Default to 70% bottom
        self.floor_slider.grid(row=5, column=0, padx=20, pady=(0, 20))

        # Control Buttons
        self.start_button = ctk.CTkButton(self.sidebar_frame, text="START MONITORING", fg_color="green", hover_color="darkgreen", command=self.toggle_monitoring)
        self.start_button.grid(row=6, column=0, padx=20, pady=10)

        # Settings
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance:", anchor="w")
        self.appearance_mode_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"],
                                                            command=lambda m: ctk.set_appearance_mode(m))
        self.appearance_mode_optionemenu.grid(row=8, column=0, padx=20, pady=(0, 20))

        # --- Main Viewport ---
        self.viewport_frame = ctk.CTkFrame(self, fg_color="black")
        self.viewport_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.viewport_frame.grid_rowconfigure(0, weight=1)
        self.viewport_frame.grid_columnconfigure(0, weight=1)

        self.video_label = ctk.CTkLabel(self.viewport_frame, text="WAITING FOR FEED...", font=ctk.CTkFont(size=24))
        self.video_label.grid(row=0, column=0)

        # Status Bar
        self.status_bar = ctk.CTkLabel(self, text="Status: IDLE", anchor="w", fg_color="transparent")
        self.status_bar.grid(row=1, column=1, padx=20, pady=(0, 10), sticky="ew")

    def change_source(self, source):
        if self.is_running:
            self.stop_feed()
            self.toggle_monitoring()

    def toggle_monitoring(self):
        if not self.is_running:
            self.start_feed()
        else:
            self.stop_feed()

    def start_feed(self):
        source = 0 if self.source_var.get() == "Camera" else "test.mp4"
        
        # Load engine if not loaded yet
        if self.engine is None:
            self.status_bar.configure(text="Status: LOADING AI MODELS (Pose + Seg)...", text_color="yellow")
            self.update() # Force UI refresh
            self.engine = FallDetectionEngine()
            # Apply current slider value on load
            self.engine.set_floor_level(self.floor_slider.get())

        self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            self.status_bar.configure(text=f"Status: ERROR (Source not found: {source})", text_color="red")
            return

        self.is_running = True
        self.start_button.configure(text="STOP MONITORING", fg_color="red", hover_color="darkred")
        self.status_bar.configure(text="Status: MONITORING ACTIVE", text_color="cyan")
        self.engine.reset_tracker()
        self.engine.set_fps(self.cap.get(cv2.CAP_PROP_FPS))
        
        self.processing_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.processing_thread.start()

    def stop_feed(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.start_button.configure(text="START MONITORING", fg_color="green", hover_color="darkgreen")
        self.status_bar.configure(text="Status: IDLE", text_color="white")
        self.video_label.configure(text="FEED STOPPED", image=None)

    def update_floor_sensitivity(self, value):
        if self.engine:
            self.engine.set_floor_level(value)
            self.status_bar.configure(text=f"Status: Floor Sensitivity set to {int(value)}%")

    def video_loop(self):
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                if self.source_var.get() == "Camera":
                    time.sleep(0.01)
                    continue
                else:
                    self.is_running = False
                    self.after(0, self.stop_feed)
                    break

            # Frame Processing
            self.frame_count += 1
            # Run engine processing
            # We pass 'censor=privacy_enabled.get()' to the engine
            processed_frame, fall_detected = self.engine.process_frame(
                frame, 
                self.frame_count, 
                censor=self.privacy_enabled.get(),
                draw_alert=True
            )
            
            display_frame = processed_frame
            
            # Update Status if Fall Detected
            if fall_detected:
                self.after(0, lambda: self.status_bar.configure(text="ALERT: FALL DETECTED!", text_color="orange"))
            else:
                self.after(0, lambda: self.status_bar.configure(text="Status: MONITORING ACTIVE", text_color="cyan"))

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
            
            # Control Frame Rate for Video Files
            if self.source_var.get() != "Camera":
                time.sleep(1/max(1, self.engine.fps))

    def update_video(self, ctk_img):
        if self.is_running:
            self.video_label.configure(image=ctk_img, text="")
            # No need to keep explicit reference for ctk_img as it's handled internally usually,
            # but it doesn't hurt.

    def on_closing(self):
        self.stop_feed()
        self.destroy()

if __name__ == "__main__":
    app = FallDetectionApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

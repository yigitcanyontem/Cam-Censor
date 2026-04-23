import cv2
import numpy as np
from ultralytics import YOLO
import os
import sys
from utils import get_resource_path

class PrivacyEngine:
    def __init__(self):
        # Load Only Segmentation Model for Privacy
        self.seg_model = YOLO(get_resource_path('yolov8n-seg.pt'))
        
        # Performance optimization: cache result to avoid repeated creation
        self.last_results = None
        
    def set_fps(self, fps):
        pass

    def add_exclusion_zone(self, x1, y1, x2, y2):
        pass

    def process_frame(self, frame, frame_count, censor=True, draw_alert=False):
        # 1. Run Segmentation (Pixel-Perfect Silhouettes for Privacy)
        results = []
        if censor:
            results = self.seg_model.track(frame, conf=0.15, classes=[0], persist=True, verbose=False)
        
        # 2. Apply Censorship (Black Silhouettes)
        if censor:
            for r in results:
                if r.masks is not None:
                    for mask in r.masks.xy:
                        cv2.fillPoly(frame, [np.int32(mask)], (0, 0, 0))
                
        return frame, False

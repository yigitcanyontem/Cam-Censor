import cv2
import numpy as np
from ultralytics import YOLO
import os
import sys
from utils import get_resource_path

class FallDetectionEngine:
    def __init__(self, seg_model="yolov8n-seg.pt", pose_model="yolov8n.pt"):
        print("Loading SKELETAL Silhouette Architecture (Nano)...")
        self.seg_model = YOLO(get_resource_path(seg_model))
        self.pose_model = YOLO(get_resource_path(pose_model))
        self.fall_tracker = {}
        self.fps = 30.0
        
        # Safety Parameters
        self.floor_level = 100.0 
        self.exclusion_zones = []
        
    def reset_tracker(self):
        self.fall_tracker = {}

    def set_fps(self, fps):
        self.fps = fps if fps and fps > 0 else 30.0

    def set_floor_level(self, level):
        self.floor_level = level

    def add_exclusion_zone(self, x1, y1, x2, y2):
        self.exclusion_zones.append([x1, y1, x2, y2])

    def process_frame(self, frame, frame_count, conf=0.15, censor=True, draw_alert=True):
        # 1. Run Pose Tracking (Accuracy & Skeletal Silhouettes)
        pose_results = self.pose_model.track(frame, conf=conf, classes=[0], persist=True, verbose=False)
        
        # 2. Run Segmentation (Pixel-Perfect Silhouettes)
        seg_results = self.seg_model.track(frame, conf=0.01, classes=[0], persist=True, verbose=False)
        
        fall_detected = False
        FALL_FRAME_THRESHOLD = int(self.fps * 0.8)
        
        # --- Fall Analysis (Pose) ---
        for r in pose_results:
            if r.keypoints is not None and r.boxes.id is not None:
                track_ids = r.boxes.id.int().cpu().tolist()
                keypoints_data = r.keypoints.data.cpu().numpy()
                
                for track_id, kpts in zip(track_ids, keypoints_data):
                    lower_body_conf = (kpts[11][2] + kpts[12][2] + kpts[15][2] + kpts[16][2]) / 4
                    if lower_body_conf < 0.25:
                        self.fall_tracker[track_id] = 0 
                        continue
                    
                    shoulder_mid = (kpts[5][:2] + kpts[6][:2]) / 2
                    hip_mid = (kpts[11][:2] + kpts[12][:2]) / 2
                    ankle_mid = (kpts[15][:2] + kpts[16][:2]) / 2
                    
                    torso_vec = shoulder_mid - hip_mid
                    angle = np.abs(np.degrees(np.arctan2(torso_vec[1], torso_vec[0])))
                    is_horizontal = (angle < 45 or angle > 135)
                    
                    torso_len = np.linalg.norm(torso_vec)
                    head_ankle_dist = np.abs(shoulder_mid[1] - ankle_mid[1])
                    is_down = head_ankle_dist < (torso_len * 1.0)

                    y_bottom = max(kpts[:, 1])
                    y_threshold = (100 - self.floor_level) / 100 * frame.shape[0]
                    is_on_floor = y_bottom > y_threshold
                    
                    if is_horizontal and is_down and is_on_floor:
                        self.fall_tracker[track_id] = self.fall_tracker.get(track_id, 0) + 1
                        if self.fall_tracker[track_id] >= FALL_FRAME_THRESHOLD:
                            fall_detected = True
                    else:
                        self.fall_tracker[track_id] = 0
            
        # --- Privacy Censorship (Silhouettes ONLY - No Boxes) ---
        if censor:
            # 1. First, Draw PIXEL-PERFECT Silhouettes (from Seg)
            for r in seg_results:
                if r.masks is not None:
                    for mask in r.masks.xy:
                        cv2.fillPoly(frame, [np.int32(mask)], (0, 0, 0))
            
            # 2. Second, Draw SKELETAL Silhouettes (from Pose as backup)
            # This ensures that even if we can't find their outline (under a blanket),
            # we draw a human-shaped "blob" instead of a black box.
            for r in pose_results:
                if r.keypoints is not None:
                    keypoints_data = r.keypoints.data.cpu().numpy()
                    for kpts in keypoints_data:
                        # Draw thicker "skeleton" lines to hide the body
                        # Limbs (Shoulders, Hips, Knees, Ankles)
                        connections = [(5, 6), (5, 11), (6, 12), (11, 12), (5, 7), (7, 9), (6, 8), (8, 10), (11, 13), (13, 15), (12, 14), (14, 16)]
                        for f, t in connections:
                            if kpts[f][2] > 0.1 and kpts[t][2] > 0.1:
                                pt1 = (int(kpts[f][0]), int(kpts[f][1]))
                                pt2 = (int(kpts[t][0]), int(kpts[t][1]))
                                cv2.line(frame, pt1, pt2, (0, 0, 0), thickness=40)
                                
                        # Head / Identity Shield
                        if kpts[0][2] > 0.1:
                            center = (int(kpts[0][0]), int(kpts[0][1]))
                            cv2.circle(frame, center, 35, (0, 0, 0), -1)

        if draw_alert and fall_detected:
            if frame_count % int(self.fps // 2) < int(self.fps // 4):
                cv2.putText(frame, "EMERGENCY: FALL DETECTED!", (50, 100), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
                
        return frame, fall_detected

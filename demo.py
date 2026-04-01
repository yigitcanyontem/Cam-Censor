import cv2
import numpy as np
from ultralytics import YOLO

def process_video(input_path, output_path):
    print(f"Loading YOLO model...")
    # Load a pretrained YOLOv8n segmentation model
    model = YOLO("yolov8n-seg.pt")
    
    # Open the video file
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or fps is None:
        fps = 30.0 # fallback

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"Processing video: {input_path}")
    frame_count = 0
    
    # Dictionary to store how many consecutive frames a person is horizontal
    # Format: { track_id: consecutive_horizontal_frames }
    fall_tracker = {}
    
    # Threshold for triggering a fall alert (e.g. 1 second of being horizontal)
    FALL_FRAME_THRESHOLD = int(fps * 1.0)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Run YOLOv8 tracking on the frame (uses ByteTrack by default)
        # conf=0.08 threshold is super low to catch partially obscured people (e.g. on beds)
        # persist=True enables object tracking between frames
        # classes=[0] to detect only "person"
        results = model.track(frame, conf=0.08, classes=[0], persist=True, verbose=False)
        
        fall_detected = False
        
        # Iterate over each detection
        for r in results:
            # We need tracking IDs to consistently monitor individuals
            if r.boxes is not None and r.boxes.id is not None:
                track_ids = r.boxes.id.int().cpu().tolist()
                boxes = r.boxes.xyxy.cpu().tolist()
                
                # Check aspect ratio for each tracked person
                for track_id, box in zip(track_ids, boxes):
                    x1, y1, x2, y2 = box
                    box_width = x2 - x1
                    box_height = y2 - y1
                    
                    # Heuristic: If bounding box width is relatively large compared to height
                    # Person is horizontal or crouching. The 0.8 multiplier relaxes the strict width > height rule.
                    if box_width > box_height * 0.8:
                        if track_id not in fall_tracker:
                            fall_tracker[track_id] = 1
                        else:
                            fall_tracker[track_id] += 1
                            
                        # If horizontal for more than the threshold, trigger alert
                        if fall_tracker[track_id] >= FALL_FRAME_THRESHOLD:
                            fall_detected = True
                    else:
                        # Reset counter if they stand up
                        fall_tracker[track_id] = 0
            
            # Now handle the censorship using segmentation masks
            # We must do this AFTER checking for falls, otherwise we'd draw over them
            if r.masks is not None:
                for mask in r.masks.xy:
                    # Get the contour points from the segmentation mask
                    points = np.int32([mask])
                    # Draw a solid black polygon over the person's shape
                    cv2.fillPoly(frame, points, (0, 0, 0))
        
        # Draw a global visual alert on the video if any fall is occurring
        if fall_detected:
            # Draw a highly visible flashing text (red color in BGR is 0,0,255)
            if frame_count % int(fps // 2) < int(fps // 4): # flash effect every half second
                cv2.putText(frame, "EMERGENCY: FALL DETECTED!", (50, 100), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)

        # Write the censored frame
        out.write(frame)
        
        frame_count += 1
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames...")

    # Release everything
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"Finished processing! Saved to {output_path}")

if __name__ == "__main__":
    process_video("test.mp4", "censored_output.mp4")

import cv2
from engine import FallDetectionEngine

def run_test_footage(input_path="test.mp4", output_path="censored_output.mp4"):
    # Initialize the high-accuracy engine
    engine = FallDetectionEngine()
    
    print(f"Opening video file: {input_path}")
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: Could not open {input_path}")
        return

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    engine.set_fps(fps)

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"Processing with Pose-Enhanced Accuracy...")
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Use the engine for processing (Censorship: ON, Alert: ON)
        processed_frame, _ = engine.process_frame(frame, frame_count, censor=True, draw_alert=True)
        
        # Write to output
        out.write(processed_frame)
        
        frame_count += 1
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames...")

    # Release everything
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"Finished! Processed video saved to: {output_path}")

if __name__ == "__main__":
    run_test_footage()

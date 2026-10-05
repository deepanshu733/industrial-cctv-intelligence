import cv2

video_path = "videos/traffic.mov"

# Open the video
cap = cv2.VideoCapture(video_path)

# Check whether the video opened successfully
if not cap.isOpened():
    print("Error: Could not open video")
    exit()

# Get video FPS
fps = cap.get(cv2.CAP_PROP_FPS)
print("FPS:", fps)

# Calculate delay between frames
delay = int(1000 / fps)

# Read and display the video frame-by-frame
while True:
    ret, frame = cap.read()

    # Stop when there are no more frames
    if not ret:
        break

    # Display current frame
    cv2.imshow("CCTV Video", frame)

    # Press Q to quit
    if cv2.waitKey(delay) & 0xFF == ord("q"):
        break

# Release video and close windows
cap.release()
cv2.destroyAllWindows()
import cv2
import requests
import json
import time  # Import the time module for adding delay

ROBOFLOW_MODEL_URL = "https://detect.roboflow.com/zebracrossing-c8nt7/3?api_key=pO6es6Rk5b8VRMmGmRjV"
IMAGE_SIZE = 640
video_capture = cv2.VideoCapture(0)

# User-configurable base IP address
base_ip = "192.168.137.154"
EXTEND_TIME_URL = f"http://{base_ip}/extend_time"  # Construct the full URL
def trigger_timer_fn():
    # Trigger the extend time endpoint if "older" or "child" is detected with a delay


        print("Older person or child detected. Waiting for 5 seconds before triggering the request.")
        try:
            response = requests.get(EXTEND_TIME_URL)
            if response.status_code == 200:
                print("Timer extended successfully.")
            else:
                print("Failed to extend time. Response code:", response.status_code)
        except requests.RequestException as e:
            print("Error while making the request to extend time:", e)
            
        # time.sleep(5)  # Add a 5-second delay
    # response = requests.post(EXTEND_TIME_URL)
def detect_objects(frame):
    height, width, _ = frame.shape
    resized_frame = cv2.resize(frame, (IMAGE_SIZE, IMAGE_SIZE))
    encoded_image = cv2.imencode('.jpg', resized_frame)[1].tobytes()
    
    # Send the image to RoboFlow for detection
    response = requests.post(ROBOFLOW_MODEL_URL, files={"file": encoded_image})
    predictions = response.json().get("predictions", [])
    
    timer_trigger = False  # Flag to check if "older" or "child" is detected
    
    for prediction in predictions:
        if "class" not in prediction:
            continue
        label = prediction["class"]
        
        # Calculate bounding box coordinates
        x = int(prediction["x"] * width / IMAGE_SIZE)
        y = int(prediction["y"] * height / IMAGE_SIZE)
        w = int(prediction["width"] * width / IMAGE_SIZE)
        h = int(prediction["height"] * height / IMAGE_SIZE)

        # Apply size filter for distance-based classification consistency
        area = w * h
        if area > 50000:  
            label = "adult"  # If bounding box is large, assume closer and likely adult
        elif area < 20000:
            label = "older"  # If bounding box is small, assume farther and likely older

        # Check if "older" or "child" is detected
        if label == "older" or label == "child":
            timer_trigger = True
        else:
            timer_trigger = False
        # Draw bounding box and label
        cv2.rectangle(frame, (x - w // 2, y - h // 2), (x + w // 2, y + h // 2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x - w // 2, y - h // 2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

    
    return frame,timer_trigger

def main():
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
        
        # Run detection on each frame
        detected_frame , trigger_timer = detect_objects(frame)
        
        # Display the frame with detections
        cv2.imshow('Age Prediction System', detected_frame)
        if trigger_timer:
            trigger_timer_fn()
        # Exit loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
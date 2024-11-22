import argparse
import time
from pathlib import Path
import cv2
import torch
import torch.backends.cudnn as cudnn
from numpy import random
import numpy as np
import requests  # Import requests to send HTTP requests

import sys
sys.path.append(r"C:/Users/Sabarna/OneDrive/Desktop/Traffic-monitor/EV-detection/src/yolov7")

from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path
from utils.plots import plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized, TracedModel

# User-configurable base IP address
base_ip = "192.168.137.154"  # Change this IP as needed
EMERGENCY_VEHICLE_URL = f"http://{base_ip}/emergency_vehicle"  # URL for emergency vehicle detection

def send_emergency_vehicle_request():
    try:
        response = requests.get(EMERGENCY_VEHICLE_URL)
        if response.status_code == 200:
            print("Emergency vehicle detected: signal sent successfully")
        else:
            print("Failed to send emergency vehicle signal")
    except Exception as e:
        print(f"Error sending emergency vehicle signal: {e}")

def draw_text(img, text,
                font=cv2.FONT_HERSHEY_TRIPLEX,
                pos=(50, 50),
                font_scale=1,
                font_thickness=2,
                text_color=(0, 0, 255),
                text_color_bg=(51, 195, 236)
                ):
    x, y = pos
    text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
    text_w, text_h = text_size
    cv2.rectangle(img, pos, (x + text_w + 5, y + text_h + 5), text_color_bg, -1)
    cv2.putText(img, text, (x, y + text_h + font_scale - 1), font, font_scale, text_color, font_thickness)
    return text_size

def detect(source, weights, device, img_size, iou_thres, conf_thres):
    webcam = source.isnumeric()
    set_logging()
    device = select_device(device)
    half = device.type != 'cpu'  # half precision only supported on CUDA
    model = attempt_load(weights, map_location=device)
    stride = int(model.stride.max())
    imgsz = check_img_size(img_size, s=stride)

    if half:
        model.half()
        
    if webcam:
        view_img = check_imshow()
        cudnn.benchmark = True
        dataset = LoadStreams(source, img_size=imgsz, stride=stride)
    
    names = model.module.names if hasattr(model, 'module') else model.names
    colors = [[random.randint(0, 130) for _ in range(3)] for _ in names]

    if device.type != 'cpu':
        model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))
    old_img_w = old_img_h = img_size
    old_img_b = 1

    hsv_lower1 = np.array([0, 20, 225])
    hsv_upper1 = np.array([30, 255, 255])
    hsv_lower2 = np.array([160, 20, 225])
    hsv_upper2 = np.array([180, 255, 255])
    cut_height_fire = 11
    cut_height_police = 8
    cut_height_ambul = 5
    hsv_thres_fire = 0.07
    hsv_thres_police = 0.03
    hsv_thres_ambul = 0.01

    t0 = time.perf_counter()
    frame_count = 0
    for path, img, im0s, vid_cap in dataset:
        frame_count += 1
        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()
        img /= 255.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)
            
        t1 = time_synchronized()
        with torch.no_grad():
            pred = model(img)[0]
        pred = non_max_suppression(pred, conf_thres, iou_thres)
        
        for i, det in enumerate(pred):
            if webcam:
                p, s, im0, frame = path[i], '%g: ' % i, im0s[i].copy(), dataset.count
                
            p = Path(p)
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]
            if len(det):
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()
                
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "
                
                for *xyxy, conf, cls in reversed(det):
                    obj_class = names[int(cls)]
                    label = f'{obj_class} {conf:.2f}'
                    plot_one_box(xyxy, im0, label=label, color=colors[int(cls)], line_thickness=3)

                    if obj_class in ["Fire Engine", "Police Car", "Ambulance"]:
                        draw_text(im0, "Slow Down and Move Over for Emergency Vehicles")
                        send_emergency_vehicle_request()  # Send request if emergency vehicle detected

        cv2.imshow(str(p), im0)

    print(f'Done. ({time.perf_counter() - t0:.3f})')


if __name__ == '__main__':
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print(device)
    
    
    with torch.no_grad():
        # yolov7tiny-freezing28 IDEA: Use this lightweight model for this time because of limitations of test environment
        # detect("0", "./train-results/yolov7tiny-freezing28-normalcar/weights/best.pt", device, img_size=640, iou_thres=0.45, conf_thres=0.8)
        # iphone camera
        #detect("1", "./train-results/yolov7tiny-freezing28-normalcar/weights/best.pt", device, img_size=640, iou_thres=0.45, conf_thres=0.8)
        detect("0", "./train-results/yolov7tiny-freezing28-normalcar/weights/best.pt", device, img_size=640, iou_thres=0.45, conf_thres=0.8)

        # yolo7-freezing50
        # detect("0", "./train-results/yolov7-freezing50/weights/best.pt", device, img_size=640, iou_thres=0.45, conf_thres=0.8)
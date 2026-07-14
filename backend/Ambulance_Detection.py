#IP CAM

# import cv2
# from ultralytics import YOLO
# import requests
# import time
# import numpy as np
# import os
# from onvif import ONVIFCamera
# import zeep
# import urllib.parse
# import threading
# from flask import Flask, Response, render_template_string
# from queue import Queue, Empty
# import logging
# from collections import deque

# # Reduce logging overhead
# logging.getLogger('ultralytics').setLevel(logging.ERROR)
# logging.getLogger('werkzeug').setLevel(logging.ERROR)

# # --- Camera Configuration ---
# USERNAME = "admin"
# PASSWORD = "KJJLqbbE"
# CAMERA_IP = "10.200.16.43"
# PORT = 554
# ONVIF_PORT = 80

# # --- Detection Configuration ---
# AMBULANCE_MODEL_PATH = 'best.pt'
# VEHICLE_MODEL_PATH = 'yolov8s.pt'
# FIREBASE_URL = 'https://v2v-communication-d46c6-default-rtdb.firebaseio.com/traffic.json'

# VEHICLE_CLASSES = ['car', 'truck', 'bus', 'motorcycle', 'bicycle']

# def zeep_pythonvalue(self, xmlvalue):
#     return xmlvalue

# zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue

# def get_stream_uri(mycam, profile):
#     try:
#         media_service = mycam.create_media_service()
#         request = media_service.create_type('GetStreamUri')
#         request.ProfileToken = profile.token
#         request.StreamSetup = {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}
#         response = media_service.GetStreamUri(request)
#         return response.Uri
#     except Exception as e:
#         print(f"Error getting stream URI: {e}")
#         return None

# def get_camera_stream():
#     print(f"Connecting to ONVIF camera at {CAMERA_IP}:{ONVIF_PORT}...")
#     streaming_urls = []

#     try:
#         mycam = ONVIFCamera(CAMERA_IP, ONVIF_PORT, USERNAME, PASSWORD, '/onvif/device_service')
#         try:
#             device_info = mycam.devicemgmt.GetDeviceInformation()
#             print(f"✓ Successfully connected via ONVIF!")
#             print(f"Device: {device_info.Manufacturer} {device_info.Model}")
#         except Exception as e:
#             print(f"Could not get device info: {e}")

#         media_service = mycam.create_media_service()
#         profiles = media_service.GetProfiles()
#         print(f"Found {len(profiles)} ONVIF stream profiles")

#         for i, profile in enumerate(profiles):
#             stream_uri = get_stream_uri(mycam, profile)
#             if stream_uri:
#                 print(f"Profile {i+1}: {stream_uri}")
#                 streaming_urls.append(stream_uri)

#     except Exception as e:
#         print(f"ONVIF connection failed: {e}")
#         print("Will try RTSP URLs directly.")

#     encoded_password = urllib.parse.quote(PASSWORD)
#     rtsp_urls = [
#         f"rtsp://{USERNAME}:{encoded_password}@{CAMERA_IP}:{PORT}/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif",
#         f"rtsp://{USERNAME}:{encoded_password}@{CAMERA_IP}:{PORT}/cam/realmonitor?channel=1&subtype=0",
#         f"rtsp://{USERNAME}:{encoded_password}@{CAMERA_IP}:{PORT}/cam/realmonitor?channel=1&subtype=1",
#     ]
    
#     for url in rtsp_urls:
#         if url not in streaming_urls:
#             streaming_urls.append(url)

#     return streaming_urls

# def connect_to_camera(streaming_urls):
#     for url in streaming_urls:
#         print(f"Attempting to connect to: {url}")
#         # Highly optimized OpenCV settings for maximum performance
#         os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
#             "rtsp_transport;tcp|"
#             "buffer_size;512000|"
#             "max_delay;0|"
#             "fflags;nobuffer|"
#             "flags;low_delay|"
#             "probesize;32|"
#             "analyzeduration;0"
#         )
        
#         cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        
#         # Critical performance settings
#         cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)      # Minimal buffering for lowest latency
#         cap.set(cv2.CAP_PROP_FPS, 25)            # Higher FPS for smoother stream
#         cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set resolution explicitly
#         cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
#         if not cap.isOpened():
#             print("✗ Failed to open video stream with this URL")
#             continue

#         ret, frame = cap.read()
#         if not ret:
#             print("✗ Could not read frames from this URL")
#             cap.release()
#             continue

#         print("✓ Successfully connected to camera!")
#         print(f"Working URL: {url}")
#         return cap, url

#     return None, None

# # --- Load Models ---
# try:
#     ambulance_model = YOLO(AMBULANCE_MODEL_PATH)
#     vehicle_model = YOLO(VEHICLE_MODEL_PATH)
#     print("✓ Models loaded successfully")
# except Exception as e:
#     print(f"Error loading models: {e}")
#     exit()

# def send_to_firebase(data_payload):
#     try:
#         response = requests.patch(FIREBASE_URL, json=data_payload, timeout=3)
#         response.raise_for_status()
#         print(f"Successfully sent data: {data_payload}")
#     except requests.exceptions.RequestException as e:
#         print(f"Error sending data to Firebase: {e}")

# def apply_nms(boxes, scores, class_ids, iou_threshold=0.3):
#     if len(boxes) == 0:
#         return [], [], []
    
#     indices = cv2.dnn.NMSBoxes(boxes, scores, 0.0, iou_threshold)
    
#     if len(indices) > 0:
#         indices = indices.flatten()
#         return (
#             [boxes[i] for i in indices],
#             [scores[i] for i in indices],
#             [class_ids[i] for i in indices]
#         )
#     return [], [], []

# def detect_vehicles_enhanced(frame, model, conf_threshold=0.4):
#     results = model.predict(frame, conf=conf_threshold, verbose=False, imgsz=416)  # Smaller image size for speed
    
#     vehicles = []
    
#     if results and hasattr(results[0], 'boxes') and len(results[0].boxes) > 0:
#         boxes = results[0].boxes.xyxy.cpu().numpy()
#         confidences = results[0].boxes.conf.cpu().numpy()
#         class_ids = results[0].boxes.cls.cpu().numpy()
        
#         boxes_for_nms = []
#         scores_for_nms = []
#         class_ids_for_nms = []
        
#         for i, (box, conf, cls_id) in enumerate(zip(boxes, confidences, class_ids)):
#             cls_id = int(cls_id)
#             class_name = model.names[cls_id]
            
#             if class_name in VEHICLE_CLASSES:
#                 x1, y1, x2, y2 = map(int, box)
#                 boxes_for_nms.append([x1, y1, x2 - x1, y2 - y1])
#                 scores_for_nms.append(float(conf))
#                 class_ids_for_nms.append(cls_id)
        
#         if boxes_for_nms:
#             nms_boxes, nms_scores, nms_class_ids = apply_nms(
#                 boxes_for_nms, scores_for_nms, class_ids_for_nms, iou_threshold=0.3
#             )
            
#             min_box_area = 500  # Reduced threshold for better performance
            
#             for box, score, cls_id in zip(nms_boxes, nms_scores, nms_class_ids):
#                 x, y, w, h = box
#                 if w * h < min_box_area:
#                     continue
                
#                 vehicles.append({
#                     'bbox': (x, y, x + w, y + h),
#                     'confidence': score,
#                     'class': model.names[cls_id],
#                     'class_id': cls_id
#                 })
    
#     return vehicles

# class HighPerformanceFrameReader(threading.Thread):
#     """High-performance frame reader with minimal buffering"""
#     def __init__(self, cap):
#         super().__init__(daemon=True)
#         self.cap = cap
#         self.latest_frame = None
#         self.frame_lock = threading.RLock()
#         self.stopped = False
#         self.frame_ready = threading.Event()

#     def run(self):
#         while not self.stopped:
#             ret = self.cap.grab()  # Grab frame immediately
#             if ret:
#                 ret, frame = self.cap.retrieve()
#                 if ret:
#                     with self.frame_lock:
#                         self.latest_frame = frame
#                         self.frame_ready.set()
#             else:
#                 time.sleep(0.001)  # Minimal pause

#     def get_latest_frame(self):
#         if self.frame_ready.wait(timeout=0.1):  # Wait up to 100ms for frame
#             with self.frame_lock:
#                 if self.latest_frame is not None:
#                     return True, self.latest_frame.copy()
#         return False, None

#     def stop(self):
#         self.stopped = True

# class AmbulanceDetectorBuffer:
#     def __init__(self, size=3):  # Reduced buffer size for faster response
#         self.size = size
#         self.buffer = deque(maxlen=size)

#     def add_detection(self, detected):
#         self.buffer.append(detected)

#     def is_confirmed(self, min_confirmed=2):
#         return self.buffer.count(True) >= min_confirmed

# # --- Optimized Flask Setup ---
# app = Flask(__name__)

# class StreamFrameManager:
#     """High-performance frame manager for streaming"""
#     def __init__(self):
#         self.frame = None
#         self.lock = threading.RLock()
#         self.encoded_frame = None
#         self.frame_changed = False

# frame_manager = StreamFrameManager()

# # Pre-compiled JPEG encoding parameters for maximum speed
# JPEG_PARAMS = [
#     int(cv2.IMWRITE_JPEG_QUALITY), 75,
#     int(cv2.IMWRITE_JPEG_OPTIMIZE), 1,
#     int(cv2.IMWRITE_JPEG_PROGRESSIVE), 1,
#     int(cv2.IMWRITE_JPEG_RST_INTERVAL), 16
# ]

# def generate_frames():
#     while True:
#         with frame_manager.lock:
#             if frame_manager.encoded_frame is None:
#                 time.sleep(0.01)
#                 continue
            
#             frame_data = frame_manager.encoded_frame
        
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n\r\n')
        
#         time.sleep(0.033)  # ~30 FPS for web streaming

# @app.route('/video_feed')
# def video_feed():
#     return Response(generate_frames(),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')

# @app.route('/')
# def index():
#     return render_template_string('''
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>Live Video Stream</title>
#         <style>
#             body { 
#                 font-family: Arial, sans-serif; 
#                 margin: 0; 
#                 padding: 20px; 
#                 background: #1a1a1a; 
#                 color: white; 
#             }
#             img { 
#                 max-width: 100%; 
#                 height: auto; 
#                 border-radius: 8px; 
#                 box-shadow: 0 4px 8px rgba(0,0,0,0.3);
#             }
#             h1 { color: #4CAF50; }
#         </style>
#     </head>
#     <body>
#         <h1>🚗 Live Vehicle Detection Stream</h1>
#         <img src="{{ url_for('video_feed') }}" alt="Video Feed">
#         <p>High-performance real-time vehicle and ambulance detection</p>
#     </body>
#     </html>
#     ''')

# def run_flask():
#     app.run(host='0.0.0.0', port=5000, threaded=True, debug=False, use_reloader=False)

# # --- Optimized Detection Processor ---
# class OptimizedDetectionProcessor(threading.Thread):
#     """Ultra-fast detection processor"""
#     def __init__(self):
#         super().__init__(daemon=True)
#         self.frame_queue = Queue(maxsize=2)
#         self.result_queue = Queue(maxsize=2)
#         self.stopped = False

#     def add_frame(self, frame):
#         try:
#             # Clear old frames
#             while not self.frame_queue.empty():
#                 try:
#                     self.frame_queue.get_nowait()
#                 except Empty:
#                     break
#             self.frame_queue.put_nowait(frame)
#         except:
#             pass

#     def get_result(self):
#         try:
#             return self.result_queue.get_nowait()
#         except Empty:
#             return None

#     def run(self):
#         while not self.stopped:
#             try:
#                 frame = self.frame_queue.get(timeout=0.1)
                
#                 # Ultra-fast processing on very small frame
#                 small_frame = cv2.resize(frame, (480, 320))  # Smaller for speed
                
#                 # Vehicle detection
#                 detected_vehicles = detect_vehicles_enhanced(small_frame, vehicle_model, conf_threshold=0.2)
                
#                 # Ambulance detection
#                 ambulance_results = ambulance_model.predict(small_frame, conf=0.45, verbose=False, imgsz=320)
#                 ambulance_detected = False
#                 ambulance_boxes = []
                
#                 if ambulance_results and hasattr(ambulance_results[0], 'boxes') and len(ambulance_results[0].boxes) > 0:
#                     boxes = ambulance_results[0].boxes.xyxy.tolist()
#                     confidences = ambulance_results[0].boxes.conf.tolist()
#                     classes = ambulance_results[0].boxes.cls.tolist()
                    
#                     for i, box in enumerate(boxes):
#                         cls_id = int(classes[i])
#                         confidence = confidences[i]
#                         if ambulance_model.names[cls_id] == 'ambulance':
#                             ambulance_detected = True
#                             x1, y1, x2, y2 = map(int, box)
#                             w, h = x2 - x1, y2 - y1
#                             if w * h > 300:  # Lower threshold for small frame
#                                 ambulance_boxes.append({
#                                     'bbox': (x1, y1, x2, y2),
#                                     'confidence': confidence
#                                 })
                
#                 result = {
#                     'vehicles': detected_vehicles,
#                     'ambulance_detected': ambulance_detected,
#                     'ambulance_boxes': ambulance_boxes,
#                     'timestamp': time.time()
#                 }
                
#                 try:
#                     # Clear old results
#                     while not self.result_queue.empty():
#                         try:
#                             self.result_queue.get_nowait()
#                         except Empty:
#                             break
#                     self.result_queue.put_nowait(result)
#                 except:
#                     pass
                    
#             except Empty:
#                 continue

#     def stop(self):
#         self.stopped = True

# # --- Frame Encoder Thread ---
# class FrameEncoder(threading.Thread):
#     """Separate thread for JPEG encoding to not block main loop"""
#     def __init__(self):
#         super().__init__(daemon=True)
#         self.encode_queue = Queue(maxsize=2)
#         self.stopped = False

#     def add_frame(self, frame):
#         try:
#             # Clear old frames
#             while not self.encode_queue.empty():
#                 try:
#                     self.encode_queue.get_nowait()
#                 except Empty:
#                     break
#             self.encode_queue.put_nowait(frame)
#         except:
#             pass

#     def run(self):
#         while not self.stopped:
#             try:
#                 frame = self.encode_queue.get(timeout=0.1)
                
#                 # Fast JPEG encoding
#                 ret, encoded = cv2.imencode('.jpg', frame, JPEG_PARAMS)
#                 if ret:
#                     with frame_manager.lock:
#                         frame_manager.encoded_frame = encoded.tobytes()
                        
#             except Empty:
#                 continue

#     def stop(self):
#         self.stopped = True

# def draw_optimized_overlay(frame, vehicles, ambulance_detected, ambulance_boxes, scale_x, scale_y):
#     """Optimized drawing function"""
#     # Draw ambulance boxes first
#     if ambulance_detected and ambulance_boxes:
#         for amb_box in ambulance_boxes:
#             x1, y1, x2, y2 = amb_box['bbox']
#             confidence = amb_box['confidence']
            
#             # Scale coordinates
#             x1, y1 = int(x1 * scale_x), int(y1 * scale_y)
#             x2, y2 = int(x2 * scale_x), int(y2 * scale_y)
            
#             # Thick red box
#             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            
#             # Label with background
#             label = f"AMBULANCE ({confidence:.1f})"
#             (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
#             cv2.rectangle(frame, (x1, y1 - h - 5), (x1 + w, y1), (0, 0, 255), -1)
#             cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
#     # Draw vehicles
#     for vehicle in vehicles:
#         x1, y1, x2, y2 = vehicle['bbox']
#         x1, y1 = int(x1 * scale_x), int(y1 * scale_y)
#         x2, y2 = int(x2 * scale_x), int(y2 * scale_y)
#         confidence = vehicle['confidence']
#         class_name = vehicle['class']

#         color = (0, 255, 0) if class_name == 'car' else (255, 150, 0)
#         cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
#         cv2.putText(frame, f"{class_name} {confidence:.1f}", (x1, y1 - 5), 
#                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

# def main():
#     print("=== HIGH-PERFORMANCE Vehicle Detection System ===")
    
#     streaming_urls = get_camera_stream()
#     if not streaming_urls:
#         print("✗ No streaming URLs found. Exiting.")
#         return

#     cap, working_url = connect_to_camera(streaming_urls)
#     if cap is None:
#         print("✗ Could not connect to camera. Exiting.")
#         return

#     print("✓ Camera connected successfully!")
    
#     # Start optimized components
#     frame_reader = HighPerformanceFrameReader(cap)
#     frame_reader.start()
    
#     detection_processor = OptimizedDetectionProcessor()
#     detection_processor.start()
    
#     frame_encoder = FrameEncoder()
#     frame_encoder.start()

#     # Timing variables
#     last_firebase_update = time.time()
#     firebase_interval = 2.0
#     last_detection_time = time.time()
#     detection_interval = 0.2  # Reduced detection frequency for speed
    
#     # State variables
#     frame_count = 0
#     ambulance_buffer = AmbulanceDetectorBuffer(size=3)
    
#     current_vehicles = []
#     current_ambulance = False
#     current_ambulance_boxes = []

#     print("🚀 Starting high-performance processing loop...")
    
#     try:
#         while True:
#             ret, frame = frame_reader.get_latest_frame()
#             if not ret or frame is None:
#                 continue
            
#             frame_count += 1
#             current_time = time.time()
            
#             # Send frame for detection less frequently
#             if current_time - last_detection_time >= detection_interval:
#                 detection_processor.add_frame(frame)
#                 last_detection_time = current_time
            
#             # Get detection results
#             detection_result = detection_processor.get_result()
#             if detection_result:
#                 current_vehicles = detection_result['vehicles']
#                 current_ambulance_boxes = detection_result.get('ambulance_boxes', [])
#                 ambulance_buffer.add_detection(detection_result['ambulance_detected'])
#                 current_ambulance = ambulance_buffer.is_confirmed(min_confirmed=2)
            
#             # Prepare display frame with optimized drawing
#             display_frame = frame.copy()
            
#             # Calculate scaling factors once
#             scale_x = display_frame.shape[1] / 480
#             scale_y = display_frame.shape[0] / 320
            
#             # Draw optimized overlay
#             draw_optimized_overlay(display_frame, current_vehicles, current_ambulance, 
#                                  current_ambulance_boxes, scale_x, scale_y)
            
#             # Info overlay
#             vehicle_count = len(current_vehicles)
#             cv2.putText(display_frame, f"Vehicles: {vehicle_count} | FPS: {int(1/(time.time()-current_time+0.001))}", 
#                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
#             if current_ambulance:
#                 cv2.putText(display_frame, "🚨 AMBULANCE DETECTED", (10, 70),
#                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

#             # Send to encoder (non-blocking)
#             frame_encoder.add_frame(display_frame)

#             # Firebase update
#             if current_time - last_firebase_update >= firebase_interval:
#                 payload = {
#                     'ambulance': 1 if current_ambulance else 0,
#                     'vehicle_count': vehicle_count,
#                     'camera_status': 'connected',
#                     'fps': frame_count / (current_time - (current_time - firebase_interval))
#                 }
#                 threading.Thread(target=send_to_firebase, args=(payload,), daemon=True).start()
#                 last_firebase_update = current_time

#     except KeyboardInterrupt:
#         print("\n🛑 Interrupted by user")
    
#     finally:
#         frame_reader.stop()
#         detection_processor.stop()
#         frame_encoder.stop()
#         if cap:
#             cap.release()
#         cv2.destroyAllWindows()
#         send_to_firebase({
#             'ambulance': 0, 
#             'vehicle_count': 0, 
#             'camera_status': 'disconnected'
#         })
#         print("✓ Stream ended cleanly.")

# if __name__ == "__main__":
#     # Start Flask server
#     flask_thread = threading.Thread(target=run_flask, daemon=True)
#     flask_thread.start()
    
#     time.sleep(1)
#     print("🌐 Flask server started at http://0.0.0.0:5000")
    
#     # Run main detection loop
#     main()














#webcam

# import cv2
# from ultralytics import YOLO
# import requests
# import time
# import numpy as np
# import os
# import threading
# from flask import Flask, Response, render_template_string
# from queue import Queue, Empty
# import logging
# from collections import deque

# # Reduce logging overhead
# logging.getLogger('ultralytics').setLevel(logging.ERROR)
# logging.getLogger('werkzeug').setLevel(logging.ERROR)

# # --- Detection Configuration ---
# AMBULANCE_MODEL_PATH = 'best.pt'
# VEHICLE_MODEL_PATH = 'yolov8s.pt'
# FIREBASE_URL = 'https://v2v-communication-d46c6-default-rtdb.firebaseio.com/traffic.json'

# VEHICLE_CLASSES = ['car', 'truck', 'bus', 'motorcycle', 'bicycle']

# def connect_to_camera():
#     """Try to connect to USB camera first, then fall back to webcam"""
#     for index in [0]:  # Try external cameras first (1, 2), then built-in webcam (0)
#         print(f"Attempting to connect to camera index {index}...")
        
#         # Highly optimized OpenCV settings for maximum performance
#         cap = cv2.VideoCapture(index)
        
#         if cap.isOpened():
#             # Critical performance settings
#             cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)      # Minimal buffering for lowest latency
#             cap.set(cv2.CAP_PROP_FPS, 30)            # Higher FPS for smoother stream
#             cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set resolution explicitly
#             cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
#             ret, frame = cap.read()
#             if ret:
#                 if index == 1:
#                     camera_type = "Built-in Webcam"
#                 else:
#                     camera_type = f"USB Camera (index {index})"
                
#                 print(f"✓ Successfully connected to {camera_type}!")
                
#                 # Print camera resolution
#                 width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#                 height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#                 fps = cap.get(cv2.CAP_PROP_FPS)
#                 print(f"Camera resolution: {width}x{height} @ {fps:.1f}FPS")
                
#                 return cap, index, camera_type
            
#             cap.release()

#     print("✗ No working cameras found. Exiting.")
#     return None, None, None

# # --- Load Models ---
# try:
#     ambulance_model = YOLO(AMBULANCE_MODEL_PATH)
#     vehicle_model = YOLO(VEHICLE_MODEL_PATH)
#     print("✓ Models loaded successfully")
#     print("Ambulance Model Classes:", ambulance_model.names)
#     print("Vehicle Model Classes:", vehicle_model.names)
# except Exception as e:
#     print(f"Error loading models: {e}")
#     exit()

# def send_to_firebase(data_payload):
#     try:
#         response = requests.patch(FIREBASE_URL, json=data_payload, timeout=3)
#         response.raise_for_status()
#         print(f"Successfully sent data: {data_payload}")
#     except requests.exceptions.RequestException as e:
#         print(f"Error sending data to Firebase: {e}")

# def apply_nms(boxes, scores, class_ids, iou_threshold=0.3):
#     if len(boxes) == 0:
#         return [], [], []
    
#     indices = cv2.dnn.NMSBoxes(boxes, scores, 0.0, iou_threshold)
    
#     if len(indices) > 0:
#         indices = indices.flatten()
#         return (
#             [boxes[i] for i in indices],
#             [scores[i] for i in indices],
#             [class_ids[i] for i in indices]
#         )
#     return [], [], []

# def detect_vehicles_enhanced(frame, model, conf_threshold=0.4):
#     results = model.predict(frame, conf=conf_threshold, verbose=False, imgsz=416)  # Smaller image size for speed
    
#     vehicles = []
    
#     if results and hasattr(results[0], 'boxes') and len(results[0].boxes) > 0:
#         boxes = results[0].boxes.xyxy.cpu().numpy()
#         confidences = results[0].boxes.conf.cpu().numpy()
#         class_ids = results[0].boxes.cls.cpu().numpy()
        
#         boxes_for_nms = []
#         scores_for_nms = []
#         class_ids_for_nms = []
        
#         for i, (box, conf, cls_id) in enumerate(zip(boxes, confidences, class_ids)):
#             cls_id = int(cls_id)
#             class_name = model.names[cls_id]
            
#             if class_name in VEHICLE_CLASSES:
#                 x1, y1, x2, y2 = map(int, box)
#                 boxes_for_nms.append([x1, y1, x2 - x1, y2 - y1])
#                 scores_for_nms.append(float(conf))
#                 class_ids_for_nms.append(cls_id)
        
#         if boxes_for_nms:
#             nms_boxes, nms_scores, nms_class_ids = apply_nms(
#                 boxes_for_nms, scores_for_nms, class_ids_for_nms, iou_threshold=0.3
#             )
            
#             min_box_area = 500  # Reduced threshold for better performance
            
#             for box, score, cls_id in zip(nms_boxes, nms_scores, nms_class_ids):
#                 x, y, w, h = box
#                 if w * h < min_box_area:
#                     continue
                
#                 vehicles.append({
#                     'bbox': (x, y, x + w, y + h),
#                     'confidence': score,
#                     'class': model.names[cls_id],
#                     'class_id': cls_id
#                 })
    
#     return vehicles

# class HighPerformanceFrameReader(threading.Thread):
#     """High-performance frame reader with minimal buffering"""
#     def __init__(self, cap):
#         super().__init__(daemon=True)
#         self.cap = cap
#         self.latest_frame = None
#         self.frame_lock = threading.RLock()
#         self.stopped = False
#         self.frame_ready = threading.Event()

#     def run(self):
#         while not self.stopped:
#             ret = self.cap.grab()  # Grab frame immediately
#             if ret:
#                 ret, frame = self.cap.retrieve()
#                 if ret:
#                     with self.frame_lock:
#                         self.latest_frame = frame
#                         self.frame_ready.set()
#             else:
#                 time.sleep(0.001)  # Minimal pause

#     def get_latest_frame(self):
#         if self.frame_ready.wait(timeout=0.1):  # Wait up to 100ms for frame
#             with self.frame_lock:
#                 if self.latest_frame is not None:
#                     return True, self.latest_frame.copy()
#                 self.frame_ready.clear()
#         return False, None

#     def stop(self):
#         self.stopped = True

# class AmbulanceDetectorBuffer:
#     def __init__(self, size=3):  # Reduced buffer size for faster response
#         self.size = size
#         self.buffer = deque(maxlen=size)

#     def add_detection(self, detected):
#         self.buffer.append(detected)

#     def is_confirmed(self, min_confirmed=2):
#         return len(self.buffer) >= min_confirmed and self.buffer.count(True) >= min_confirmed

# # --- Optimized Flask Setup ---
# app = Flask(__name__)

# class StreamFrameManager:
#     """High-performance frame manager for streaming"""
#     def __init__(self):
#         self.frame = None
#         self.lock = threading.RLock()
#         self.encoded_frame = None
#         self.frame_changed = False

# frame_manager = StreamFrameManager()

# # Pre-compiled JPEG encoding parameters for maximum speed
# JPEG_PARAMS = [
#     int(cv2.IMWRITE_JPEG_QUALITY), 75,
#     int(cv2.IMWRITE_JPEG_OPTIMIZE), 1,
#     int(cv2.IMWRITE_JPEG_PROGRESSIVE), 1,
#     int(cv2.IMWRITE_JPEG_RST_INTERVAL), 16
# ]

# def generate_frames():
#     while True:
#         with frame_manager.lock:
#             if frame_manager.encoded_frame is None:
#                 time.sleep(0.01)
#                 continue
            
#             frame_data = frame_manager.encoded_frame
        
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n\r\n')
        
#         time.sleep(0.033)  # ~30 FPS for web streaming

# @app.route('/video_feed')
# def video_feed():
#     return Response(generate_frames(),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')

# @app.route('/')
# def index():
#     return render_template_string('''
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>Live Vehicle Detection</title>
#         <style>
#             body { 
#                 font-family: Arial, sans-serif; 
#                 margin: 0; 
#                 padding: 20px; 
#                 background: #1a1a1a; 
#                 color: white; 
#                 text-align: center;
#             }
#             .container {
#                 max-width: 1280px;
#                 margin: 0 auto;
#             }
#             .video-container {
#                 position: relative;
#                 overflow: hidden;
#                 border-radius: 8px;
#                 box-shadow: 0 4px 20px rgba(0,0,0,0.5);
#                 margin: 20px auto;
#                 background: #000;
#             }
#             img { 
#                 width: 100%;
#                 height: auto;
#                 display: block;
#             }
#             h1 { 
#                 color: #4CAF50; 
#                 margin-bottom: 30px;
#             }
#             .footer {
#                 margin-top: 20px;
#                 font-size: 14px;
#                 color: #aaa;
#             }
#         </style>
#     </head>
#     <body>
#         <div class="container">
#             <h1>🚗 Live Vehicle Detection Stream</h1>
#             <div class="video-container">
#                 <img src="{{ url_for('video_feed') }}" alt="Video Feed">
#             </div>
#             <p>High-performance real-time vehicle and ambulance detection</p>
#             <div class="footer">
#                 Vehicle detection using YOLOv8 and web streaming
#             </div>
#         </div>
#     </body>
#     </html>
#     ''')

# def run_flask():
#     app.run(host='0.0.0.0', port=5000, threaded=True, debug=False, use_reloader=False)

# # --- Optimized Detection Processor ---
# class OptimizedDetectionProcessor(threading.Thread):
#     """Ultra-fast detection processor"""
#     def __init__(self):
#         super().__init__(daemon=True)
#         self.frame_queue = Queue(maxsize=2)
#         self.result_queue = Queue(maxsize=2)
#         self.stopped = False

#     def add_frame(self, frame):
#         try:
#             # Clear old frames
#             while not self.frame_queue.empty():
#                 try:
#                     self.frame_queue.get_nowait()
#                 except Empty:
#                     break
#             self.frame_queue.put_nowait(frame)
#         except:
#             pass

#     def get_result(self):
#         try:
#             return self.result_queue.get_nowait()
#         except Empty:
#             return None

#     def run(self):
#         while not self.stopped:
#             try:
#                 frame = self.frame_queue.get(timeout=0.1)
                
#                 # Ultra-fast processing on very small frame
#                 small_frame = cv2.resize(frame, (480, 320))  # Smaller for speed
                
#                 # Vehicle detection
#                 detected_vehicles = detect_vehicles_enhanced(small_frame, vehicle_model, conf_threshold=0.2)
                
#                 # Ambulance detection
#                 ambulance_results = ambulance_model.predict(small_frame, conf=0.45, verbose=False, imgsz=320)
#                 ambulance_detected = False
#                 ambulance_boxes = []
                
#                 if ambulance_results and hasattr(ambulance_results[0], 'boxes') and len(ambulance_results[0].boxes) > 0:
#                     boxes = ambulance_results[0].boxes.xyxy.tolist()
#                     confidences = ambulance_results[0].boxes.conf.tolist()
#                     classes = ambulance_results[0].boxes.cls.tolist()
                    
#                     for i, box in enumerate(boxes):
#                         cls_id = int(classes[i])
#                         confidence = confidences[i]
#                         if ambulance_model.names[cls_id] == 'ambulance':
#                             ambulance_detected = True
#                             x1, y1, x2, y2 = map(int, box)
#                             w, h = x2 - x1, y2 - y1
#                             if w * h > 300:  # Lower threshold for small frame
#                                 ambulance_boxes.append({
#                                     'bbox': (x1, y1, x2, y2),
#                                     'confidence': confidence
#                                 })
                
#                 result = {
#                     'vehicles': detected_vehicles,
#                     'ambulance_detected': ambulance_detected,
#                     'ambulance_boxes': ambulance_boxes,
#                     'timestamp': time.time()
#                 }
                
#                 try:
#                     # Clear old results
#                     while not self.result_queue.empty():
#                         try:
#                             self.result_queue.get_nowait()
#                         except Empty:
#                             break
#                     self.result_queue.put_nowait(result)
#                 except:
#                     pass
                    
#             except Empty:
#                 continue

#     def stop(self):
#         self.stopped = True

# # --- Frame Encoder Thread ---
# class FrameEncoder(threading.Thread):
#     """Separate thread for JPEG encoding to not block main loop"""
#     def __init__(self):
#         super().__init__(daemon=True)
#         self.encode_queue = Queue(maxsize=2)
#         self.stopped = False

#     def add_frame(self, frame):
#         try:
#             # Clear old frames
#             while not self.encode_queue.empty():
#                 try:
#                     self.encode_queue.get_nowait()
#                 except Empty:
#                     break
#             self.encode_queue.put_nowait(frame)
#         except:
#             pass

#     def run(self):
#         while not self.stopped:
#             try:
#                 frame = self.encode_queue.get(timeout=0.1)
                
#                 # Fast JPEG encoding
#                 ret, encoded = cv2.imencode('.jpg', frame, JPEG_PARAMS)
#                 if ret:
#                     with frame_manager.lock:
#                         frame_manager.encoded_frame = encoded.tobytes()
                        
#             except Empty:
#                 continue

#     def stop(self):
#         self.stopped = True

# def draw_optimized_overlay(frame, vehicles, ambulance_detected, ambulance_boxes, scale_x, scale_y):
#     """Optimized drawing function"""
#     # Draw ambulance boxes first
#     if ambulance_detected and ambulance_boxes:
#         for amb_box in ambulance_boxes:
#             x1, y1, x2, y2 = amb_box['bbox']
#             confidence = amb_box['confidence']
            
#             # Scale coordinates
#             x1, y1 = int(x1 * scale_x), int(y1 * scale_y)
#             x2, y2 = int(x2 * scale_x), int(y2 * scale_y)
            
#             # Thick red box
#             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            
#             # Label with background
#             label = f"AMBULANCE ({confidence:.1f})"
#             (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
#             cv2.rectangle(frame, (x1, y1 - h - 5), (x1 + w, y1), (0, 0, 255), -1)
#             cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
#     # Draw vehicles
#     for vehicle in vehicles:
#         x1, y1, x2, y2 = vehicle['bbox']
#         x1, y1 = int(x1 * scale_x), int(y1 * scale_y)
#         x2, y2 = int(x2 * scale_x), int(y2 * scale_y)
#         confidence = vehicle['confidence']
#         class_name = vehicle['class']

#         color = (0, 255, 0) if class_name == 'car' else (255, 150, 0)
#         cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
#         cv2.putText(frame, f"{class_name} {confidence:.1f}", (x1, y1 - 5), 
#                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

# def main():
#     print("=== HIGH-PERFORMANCE Vehicle Detection System (USB/Webcam) ===")
    
#     # Connect to camera
#     cap, camera_index, camera_type = connect_to_camera()
#     if cap is None:
#         return

#     # Start optimized components
#     frame_reader = HighPerformanceFrameReader(cap)
#     frame_reader.start()
    
#     detection_processor = OptimizedDetectionProcessor()
#     detection_processor.start()
    
#     frame_encoder = FrameEncoder()
#     frame_encoder.start()

#     # Timing variables
#     last_firebase_update = time.time()
#     firebase_interval = 2.0
#     last_detection_time = time.time()
#     detection_interval = 0.2  # Reduced detection frequency for speed
    
#     # State variables
#     frame_count = 0
#     ambulance_buffer = AmbulanceDetectorBuffer(size=3)
    
#     current_vehicles = []
#     current_ambulance = False
#     current_ambulance_boxes = []
#     start_time = time.time()

#     print(f"🚀 Starting high-performance processing loop with {camera_type}...")
    
#     connection_errors = 0
#     max_connection_errors = 5
    
#     try:
#         while True:
#             ret, frame = frame_reader.get_latest_frame()
#             if not ret or frame is None:
#                 connection_errors += 1
#                 print(f"✗ Failed to get frame (attempt {connection_errors}/{max_connection_errors})")
#                 if connection_errors >= max_connection_errors:
#                     print("Too many connection errors. Attempting to reconnect...")
#                     frame_reader.stop()
#                     cap.release()
#                     cap, camera_index, camera_type = connect_to_camera()
#                     if cap is None:
#                         print("Failed to reconnect. Exiting.")
#                         break
#                     frame_reader = HighPerformanceFrameReader(cap)
#                     frame_reader.start()
#                     connection_errors = 0
#                 time.sleep(0.5)
#                 continue
            
#             # Reset connection error counter on successful frame
#             connection_errors = 0
            
#             frame_count += 1
#             current_time = time.time()
            
#             # Send frame for detection less frequently
#             if current_time - last_detection_time >= detection_interval:
#                 detection_processor.add_frame(frame)
#                 last_detection_time = current_time
            
#             # Get detection results
#             detection_result = detection_processor.get_result()
#             if detection_result:
#                 current_vehicles = detection_result['vehicles']
#                 current_ambulance_boxes = detection_result.get('ambulance_boxes', [])
#                 ambulance_buffer.add_detection(detection_result['ambulance_detected'])
#                 current_ambulance = ambulance_buffer.is_confirmed(min_confirmed=2)
            
#             # Prepare display frame with optimized drawing
#             display_frame = frame.copy()
            
#             # Calculate scaling factors once
#             scale_x = display_frame.shape[1] / 480
#             scale_y = display_frame.shape[0] / 320
            
#             # Draw optimized overlay
#             draw_optimized_overlay(display_frame, current_vehicles, current_ambulance, 
#                                  current_ambulance_boxes, scale_x, scale_y)
            
#             # Calculate FPS
#             elapsed_time = current_time - start_time
#             fps = frame_count / elapsed_time if elapsed_time > 0 else 0
            
#             # Info overlay
#             vehicle_count = len(current_vehicles)
#             cv2.putText(display_frame, f"Vehicles: {vehicle_count} | FPS: {int(fps)}", 
#                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
#             if current_ambulance:
#                 cv2.putText(display_frame, "AMBULANCE DETECTED", (10, 70),
#                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                           
#             cv2.putText(display_frame, f"Camera: {camera_type}", 
#                        (10, display_frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

#             # Send to encoder (non-blocking)
#             frame_encoder.add_frame(display_frame)
            
#             # Local display 
#             cv2.imshow("Vehicle Detection", cv2.resize(display_frame, (1280, 720)))
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break

#             # Firebase update
#             if current_time - last_firebase_update >= firebase_interval:
#                 payload = {
#                     'ambulance': 1 if current_ambulance else 0,
#                     'vehicle_count': vehicle_count,
#                     'camera_status': 'connected',
#                     'camera_type': camera_type,
#                     'fps': fps
#                 }
#                 threading.Thread(target=send_to_firebase, args=(payload,), daemon=True).start()
#                 last_firebase_update = current_time
#                 # Reset frame count for accurate FPS in next interval
#                 frame_count = 0
#                 start_time = current_time

#     except KeyboardInterrupt:
#         print("\nInterrupted by user")
    
#     finally:
#         frame_reader.stop()
#         detection_processor.stop()
#         frame_encoder.stop()
#         if cap:
#             cap.release()
#         cv2.destroyAllWindows()
#         send_to_firebase({
#             'ambulance': 0, 
#             'vehicle_count': 0, 
#             'camera_status': 'disconnected'
#         })
#         print("Stream ended cleanly.")

# if __name__ == "__main__":
#     # Start Flask server
#     flask_thread = threading.Thread(target=run_flask, daemon=True)
#     flask_thread.start()
    
#     time.sleep(1)
#     print("🌐 Flask server started at http://0.0.0.0:5000")
    
#     # Run main detection loop
#     main()



























import cv2
from ultralytics import YOLO
import requests
import time
import threading
from flask import Flask, Response, render_template_string, jsonify
from queue import Queue, Empty
import logging
from collections import deque

# Reduce logging overhead
logging.getLogger('ultralytics').setLevel(logging.ERROR)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# --- Detection Configuration ---
AMBULANCE_MODEL_PATH = 'best.pt'
FIREBASE_URL = 'https://v2v-communication-d46c6-default-rtdb.firebaseio.com/traffic.json'

# --- Detection Parameters ---
CONFIDENCE_THRESHOLD = 0.65
CONFIRMATION_FRAMES = 3
MIN_BOX_AREA = 800

def connect_to_camera():
    """Try to connect to USB camera first, then fall back to webcam"""
    for index in [1]:  # Try external cameras first (1, 2), then built-in webcam (0)
        print(f"Attempting to connect to camera index {index}...")
        
        cap = cv2.VideoCapture(index)
        
        if cap.isOpened():
            # Critical performance settings
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)      # Minimal buffering for lowest latency
            cap.set(cv2.CAP_PROP_FPS, 30)            # Higher FPS for smoother stream
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set resolution explicitly
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            ret, frame = cap.read()
            if ret:
                if index == 0:
                    camera_type = "Built-in Webcam"
                else:
                    camera_type = f"USB Camera (index {index})"
                
                print(f"✓ Successfully connected to {camera_type}!")
                
                # Print camera resolution
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                print(f"Camera resolution: {width}x{height} @ {fps:.1f}FPS")
                
                return cap, index, camera_type
            
            cap.release()

    print("✗ No working cameras found. Exiting.")
    return None, None, None

# --- Load Ambulance Model ---
try:
    ambulance_model = YOLO(AMBULANCE_MODEL_PATH)
    print("✓ Ambulance model loaded successfully")
    print("Ambulance Model Classes:", ambulance_model.names)
except Exception as e:
    print(f"Error loading ambulance model: {e}")
    exit()

def send_to_firebase(data_payload):
    try:
        response = requests.patch(FIREBASE_URL, json=data_payload, timeout=3)
        response.raise_for_status()
        print(f"Successfully sent data: {data_payload}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to Firebase: {e}")

class HighPerformanceFrameReader(threading.Thread):
    """High-performance frame reader with minimal buffering"""
    def __init__(self, cap):
        super().__init__(daemon=True)
        self.cap = cap
        self.latest_frame = None
        self.frame_lock = threading.RLock()
        self.stopped = False
        self.frame_ready = threading.Event()

    def run(self):
        while not self.stopped:
            ret = self.cap.grab()
            if ret:
                ret, frame = self.cap.retrieve()
                if ret:
                    with self.frame_lock:
                        self.latest_frame = frame
                        self.frame_ready.set()
            else:
                time.sleep(0.001)

    def get_latest_frame(self):
        if self.frame_ready.wait(timeout=0.1):
            with self.frame_lock:
                if self.latest_frame is not None:
                    frame_copy = self.latest_frame.copy()
                    self.frame_ready.clear()
                    return True, frame_copy
        return False, None

    def stop(self):
        self.stopped = True

class AmbulanceDetectorBuffer:
    """Buffer to hold ambulance detection status for last N frames with quality scoring"""
    def __init__(self, size=5):
        self.size = size
        self.buffer = deque(maxlen=size)
        self.confidence_buffer = deque(maxlen=size)
        self.area_buffer = deque(maxlen=size)

    def add_detection(self, detected, confidence=0, area=0):
        self.buffer.append(detected)
        self.confidence_buffer.append(confidence)
        self.area_buffer.append(area)

    def is_confirmed(self, min_confirmed=3, min_confidence=0.65):
        """Return True if ambulance detected in at least min_confirmed frames with good confidence"""
        if len(self.buffer) < min_confirmed:
            return False
            
        confirmed_count = 0
        for i, detected in enumerate(self.buffer):
            if detected and self.confidence_buffer[i] >= min_confidence:
                confirmed_count += 1
                
        return confirmed_count >= min_confirmed
        
    def get_quality_score(self):
        """Return a quality score (0-100) based on confidence and consistency"""
        if not self.buffer or not any(self.buffer):
            return 0
            
        # Average confidence of positive detections
        positive_confidences = [conf for i, conf in enumerate(self.confidence_buffer) if self
        .buffer[i]]
        avg_confidence = sum(positive_confidences) / max(1, len(positive_confidences))
        
        # Detection consistency
        consistency = self.buffer.count(True) / len(self.buffer)
        
        # Calculate score (70% confidence weight, 30% consistency weight)
        score = (avg_confidence * 70) + (consistency * 30)
        return min(100, int(score))

# --- Flask Setup ---
app = Flask(__name__)

class StreamFrameManager:
    """High-performance frame manager for streaming"""
    def __init__(self):
        self.lock = threading.RLock()
        self.encoded_frame = None

frame_manager = StreamFrameManager()

# Pre-compiled JPEG encoding parameters
JPEG_PARAMS = [
    int(cv2.IMWRITE_JPEG_QUALITY), 75,
    int(cv2.IMWRITE_JPEG_OPTIMIZE), 1,
    int(cv2.IMWRITE_JPEG_PROGRESSIVE), 1,
    int(cv2.IMWRITE_JPEG_RST_INTERVAL), 16
]

def generate_frames():
    while True:
        with frame_manager.lock:
            if frame_manager.encoded_frame is None:
                time.sleep(0.01)
                continue
            
            frame_data = frame_manager.encoded_frame
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n\r\n')
        
        time.sleep(0.033)  # ~30 FPS for web streaming

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ambulance Detection</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0; 
                padding: 20px; 
                background: #0d1117; 
                color: #e6edf3; 
                text-align: center;
            }
            .container {
                max-width: 1280px;
                margin: 0 auto;
            }
            .video-container {
                position: relative;
                overflow: hidden;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                margin: 20px auto;
                background: #000;
            }
            img { 
                width: 100%;
                height: auto;
                display: block;
            }
            h1 { 
                color: #58a6ff; 
                margin-bottom: 20px;
            }
            .status-container {
                background-color: #161b22;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }
            #status {
                font-size: 18px;
                margin: 0;
                font-weight: 500;
            }
            .ambulance-alert {
                background-color: #f85149;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                display: inline-block;
                border-radius: 5px;
                animation: pulse 1.5s infinite;
                margin-top: 10px;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            .footer {
                margin-top: 20px;
                font-size: 14px;
                color: #8b949e;
            }
            .stats {
                display: flex;
                justify-content: space-around;
                background-color: #161b22;
                padding: 10px;
                border-radius: 8px;
                margin-top: 20px;
            }
            .stat-box {
                text-align: center;
            }
            .stat-label {
                font-size: 14px;
                color: #8b949e;
            }
            .stat-value {
                font-size: 18px;
                font-weight: bold;
                color: #58a6ff;
            }
        </style>
        <script>
            // Check for ambulance status
            let ambulanceStatus = false;
            
            function updateStatus() {
                fetch('/status')
                    .then(response => response.json())
                    .then(data => {
                        const statusElement = document.getElementById('status');
                        const fpsElement = document.getElementById('fps-value');
                        
                        if (data.ambulance) {
                            statusElement.innerHTML = '<div class="ambulance-alert">🚨 AMBULANCE DETECTED 🚨</div>';
                            ambulanceStatus = true;
                        } else {
                            statusElement.textContent = 'No ambulance detected';
                            ambulanceStatus = false;
                        }
                        
                        // Update FPS
                        if (data.fps) {
                            fpsElement.textContent = data.fps;
                        }
                    })
                    .catch(error => console.error('Error fetching status:', error));
            }
            
            // Update status every second
            setInterval(updateStatus, 1000);
            
            // Initial update
            document.addEventListener('DOMContentLoaded', updateStatus);
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🚑 Ambulance Detection System</h1>
            <div class="video-container">
                <img src="{{ url_for('video_feed') }}" alt="Video Feed">
            </div>
            <div class="status-container">
                <p id="status">Initializing detection...</p>
            </div>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-label">FPS</div>
                    <div id="fps-value" class="stat-value">0</div>
                </div>
            </div>
            <div class="footer">
                Simplified Flask-only detection with bounding boxes
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/status')
def status():
    global current_ambulance, ambulance_quality_score, current_fps
    return {
        "ambulance": current_ambulance, 
        "confidence": ambulance_quality_score,
        "fps": int(current_fps)
    }

def run_flask():
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False, use_reloader=False)

# --- Optimized Detection Processor ---
class OptimizedDetectionProcessor(threading.Thread):
    """Improved detection processor with false positive reduction"""
    def __init__(self):
        super().__init__(daemon=True)
        self.frame_queue = Queue(maxsize=2)
        self.result_queue = Queue(maxsize=2)
        self.stopped = False
        # Track best area and confidence over time for hysteresis
        self.max_area = 0
        self.max_confidence = 0
        self.decay_factor = 0.9  # Decay factor for max values

    def add_frame(self, frame):
        try:
            # Clear old frames
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except Empty:
                    break
            self.frame_queue.put_nowait(frame)
        except:
            pass

    def get_result(self):
        try:
            return self.result_queue.get_nowait()
        except Empty:
            return None

    def run(self):
        while not self.stopped:
            try:
                frame = self.frame_queue.get(timeout=0.1)
                
                detections = []
                detection_confidences = []
                detection_areas = []
                best_confidence = 0
                best_area = 0
                
                # Detect at a single resolution for simplicity and speed
                resized_frame = cv2.resize(frame, (640, 480))
                
                # Run detection with confidence threshold
                results = ambulance_model.predict(
                    resized_frame, 
                    conf=CONFIDENCE_THRESHOLD, 
                    verbose=False
                )
                
                if results and hasattr(results[0], 'boxes') and len(results[0].boxes) > 0:
                    boxes = results[0].boxes.xyxy.tolist()
                    confidences = results[0].boxes.conf.tolist()
                    classes = results[0].boxes.cls.tolist()
                    
                    scale_x = frame.shape[1] / 640
                    scale_y = frame.shape[0] / 480
                    
                    for i, box in enumerate(boxes):
                        cls_id = int(classes[i])
                        confidence = confidences[i]
                        
                        if ambulance_model.names[cls_id] == 'ambulance':
                            x1, y1, x2, y2 = map(int, box)
                            w, h = x2 - x1, y2 - y1
                            area = w * h
                            
                            # Scale back to original frame size
                            x1, y1 = int(x1 * scale_x), int(y1 * scale_y)
                            x2, y2 = int(x2 * scale_x), int(y2 * scale_y)
                            
                            # Calculate area in original frame
                            w_orig = x2 - x1
                            h_orig = y2 - y1
                            area_orig = w_orig * h_orig
                            
                            if area_orig > MIN_BOX_AREA:
                                detections.append({
                                    'bbox': (x1, y1, x2, y2),
                                    'confidence': confidence,
                                    'area': area_orig
                                })
                                
                                detection_confidences.append(confidence)
                                detection_areas.append(area_orig)
                                
                                if confidence > best_confidence:
                                    best_confidence = confidence
                                
                                if area_orig > best_area:
                                    best_area = area_orig
                
                # Determine if ambulance is detected
                ambulance_detected = len(detections) > 0
                
                # Calculate confidence 
                avg_confidence = sum(detection_confidences) / max(1, len(detection_confidences))
                
                result = {
                    'ambulance_detected': ambulance_detected,
                    'ambulance_boxes': detections,
                    'confidence': avg_confidence,
                    'area': best_area,
                    'timestamp': time.time()
                }
                
                try:
                    # Clear old results
                    while not self.result_queue.empty():
                        try:
                            self.result_queue.get_nowait()
                        except Empty:
                            break
                    self.result_queue.put_nowait(result)
                except:
                    pass
                    
            except Empty:
                continue

    def stop(self):
        self.stopped = True

# --- Frame Encoder Thread ---
class FrameEncoder(threading.Thread):
    """Separate thread for JPEG encoding to not block main loop"""
    def __init__(self):
        super().__init__(daemon=True)
        self.encode_queue = Queue(maxsize=2)
        self.stopped = False

    def add_frame(self, frame):
        try:
            # Clear old frames
            while not self.encode_queue.empty():
                try:
                    self.encode_queue.get_nowait()
                except Empty:
                    break
            self.encode_queue.put_nowait(frame)
        except:
            pass

    def run(self):
        while not self.stopped:
            try:
                frame = self.encode_queue.get(timeout=0.1)
                
                # Fast JPEG encoding
                ret, encoded = cv2.imencode('.jpg', frame, JPEG_PARAMS)
                if ret:
                    with frame_manager.lock:
                        frame_manager.encoded_frame = encoded.tobytes()
                        
            except Empty:
                continue

    def stop(self):
        self.stopped = True

def draw_detection_boxes(frame, ambulance_boxes):
    """Draw only detection boxes and confidence values - simplified"""
    if ambulance_boxes:
        for amb_box in ambulance_boxes:
            x1, y1, x2, y2 = amb_box['bbox']
            confidence = amb_box['confidence']
            
            # Draw red box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # Label with confidence
            label = f"AMBULANCE ({confidence:.2f})"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - h - 5), (x1 + w, y1), (0, 0, 255), -1)
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

# Global variables for status tracking
current_ambulance = False
ambulance_quality_score = 0
current_fps = 0

def main():
    print("=== SIMPLIFIED FLASK AMBULANCE DETECTION SYSTEM ===")
    
    # Connect to camera
    cap, camera_index, camera_type = connect_to_camera()
    if cap is None:
        return

    # Start optimized components
    frame_reader = HighPerformanceFrameReader(cap)
    frame_reader.start()
    
    detection_processor = OptimizedDetectionProcessor()
    detection_processor.start()
    
    frame_encoder = FrameEncoder()
    frame_encoder.start()

    # Timing variables
    last_firebase_update = time.time()
    firebase_interval = 2.0
    last_detection_time = time.time()
    detection_interval = 0.25
    
    # State variables
    frame_count = 0
    fps_count = 0
    fps_timer = time.time()
    
    # Use buffer for detection stability
    ambulance_buffer = AmbulanceDetectorBuffer(size=5)
    
    global current_ambulance, ambulance_quality_score, current_fps
    current_ambulance_boxes = []

    print(f"🚀 Starting ambulance detection with {camera_type}...")
    print(f"Using confidence threshold: {CONFIDENCE_THRESHOLD}")
    
    connection_errors = 0
    max_connection_errors = 5
    
    try:
        while True:
            ret, frame = frame_reader.get_latest_frame()
            if not ret or frame is None:
                connection_errors += 1
                print(f"✗ Failed to get frame (attempt {connection_errors}/{max_connection_errors})")
                if connection_errors >= max_connection_errors:
                    print("Too many connection errors. Attempting to reconnect...")
                    frame_reader.stop()
                    cap.release()
                    cap, camera_index, camera_type = connect_to_camera()
                    if cap is None:
                        print("Failed to reconnect. Exiting.")
                        break
                    frame_reader = HighPerformanceFrameReader(cap)
                    frame_reader.start()
                    connection_errors = 0
                time.sleep(0.5)
                continue
            
            # Reset connection error counter on successful frame
            connection_errors = 0
            
            frame_count += 1
            fps_count += 1
            current_time = time.time()
            
            # Calculate FPS every second
            if current_time - fps_timer >= 1.0:
                current_fps = fps_count / (current_time - fps_timer)
                fps_count = 0
                fps_timer = current_time
            
            # Send frame for detection less frequently
            if current_time - last_detection_time >= detection_interval:
                detection_processor.add_frame(frame)
                last_detection_time = current_time
            
            # Get detection results
            detection_result = detection_processor.get_result()
            if detection_result:
                current_ambulance_boxes = detection_result.get('ambulance_boxes', [])
                
                # Get the best confidence
                best_conf = 0
                best_area = 0
                if current_ambulance_boxes:
                    for box in current_ambulance_boxes:
                        best_conf = max(best_conf, box['confidence'])
                        best_area = max(best_area, box['area'])
                
                # Add to buffer with confidence and area
                ambulance_buffer.add_detection(
                    detection_result['ambulance_detected'],
                    best_conf,
                    best_area
                )
                
                # Confirmation criteria
                current_ambulance = ambulance_buffer.is_confirmed(
                    min_confirmed=CONFIRMATION_FRAMES,
                    min_confidence=CONFIDENCE_THRESHOLD
                )
                
                # Get quality score
                ambulance_quality_score = ambulance_buffer.get_quality_score()
            
            # Create display frame
            display_frame = frame.copy()
            
            # Draw only detection boxes - simplified visualization
            draw_detection_boxes(display_frame, current_ambulance_boxes)
            
            # Send to encoder for web viewing
            frame_encoder.add_frame(display_frame)
            
            # Firebase update
            if current_time - last_firebase_update >= firebase_interval:
                payload = {
                    'ambulance': 1 if current_ambulance else 0
                }
                threading.Thread(target=send_to_firebase, args=(payload,), daemon=True).start()
                last_firebase_update = current_time

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        frame_reader.stop()
        detection_processor.stop()
        frame_encoder.stop()
        if cap:
            cap.release()
        send_to_firebase({
            'ambulance': 0,
        })
        print("Stream ended cleanly.")

if __name__ == "__main__":
    # Start Flask server
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    time.sleep(1)
    print("🌐 Flask server started at http://0.0.0.0:5000")
    
    # Run main detection loop
    main()
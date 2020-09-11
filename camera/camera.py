import numpy as np
import cv2
import threading
import time

class Camera:
    cap = None
    cameraId = 0
    size = (0,0)
    update_interval = 0.033
    pixel_to_direction_matrix = None

    frame_buffer = None
    loop_thread = None
    loop_flag = False

    #the unit of f must the same as the unit of cmos
    def __init__(self, cameraId=0, update_interval = 0.033, pixel_size=(1920, 1080), cmos=(0.00020, 0.00030), f=0.0005):
        super().__init__()
        self.cameraId = cameraId
        self.size = pixel_size
        self.update_interval = update_interval
        self.cap = cv2.VideoCapture(cameraId)
        dx = cmos[0] / pixel_size[0]
        dy = cmos[1] / pixel_size[1]
        u0 = pixel_size[0] / 2
        v0 = pixel_size[1] / 2
        fx = f / dy
        fy = f / dx
        self.pixel_to_direction_matrix = np.array([
            [       1/fx,          0, (-1)*u0/fx], 
            [          0,       1/fy, (-1)*v0/fy],
            [          0,          0,          1],
            [          0,          0,          0],
        ])
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, pixel_size[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, pixel_size[1])
        else:
            print("Cannot open camera")

    def __del__(self):
        self.cap.release()

    def start_camera_loop(self):
        self.loop_flag = True
        if self.loop_thread == None:
            self.loop_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.loop_thread.start()
        time.sleep(1)
        return True

    def pause_camera_loop(self):
        self.loop_flag = False

    def get_current_frame(self):
        return self.frame_buffer

    def _camera_loop(self):
        interval = self.update_interval
        while self.loop_flag :
            time_0 = time.time()
            ret, frame = self.cap.read()
            self.frame_buffer = frame

            if not ret:
                break

            time_1 = time.time()

            if time_1 - time_0 > interval:
                interval = 0
            else:
                time.sleep(interval - (time_1 - time_0) - 0.001)

    def get_pixel_direction(self, pixel_location=(0, 0)):
        #reference: https://blog.csdn.net/baidu_38172402/article/details/81949447
        pixel_np = np.array([pixel_location[0], pixel_location[1], 1])
        
        direction_np = np.dot(self.pixel_to_direction_matrix, pixel_np)[0:3]
        #x+:right
        #y+:down
        #z+:front
        direction_nomarlized = direction_np / np.sqrt((direction_np * direction_np).sum())
        
        #x+:right
        #y+:front
        #z+:top
        direction_nomarlized_converted = np.array([
            direction_nomarlized[0],
            direction_nomarlized[2],
            direction_nomarlized[1] * (-1),
        ])
        return direction_nomarlized_converted
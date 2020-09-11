import numpy as np
import cv2
import time
from PIL import Image

from yolo.yolo_v4 import YOLO
from camera.camera import Camera
from radar.radar import Radar
from utils.rectangle_drawer import RectangleDrawer, random_colors
from utils.coordinate import Coordinate3D, get_rotate_matrix


#yolo init
anchors = [8.0, 24.0, 8.0, 74.0, 13.0, 33.0, 20.0, 40.0, 23.0, 166.0, 24.0, 60.0, 39.0, 69.0, 61.0, 114.0, 100.0, 200.0]
anchors = np.array(anchors).reshape([-1, 3, 2])[::-1,:,:]
class_names = ["Car", "Van", 'Truck', 'Pedestrian', 'Person_sitting', 'Cyclist', 'Tram', 'Misc']
yolo = YOLO(anchors=anchors, class_names=class_names)

#camera init
camera = Camera('D:\\Project\\BarrierIdentificationWithMMW\\代码\\test_data\\video\\2020-09-02 16-48-36.mp4', pixel_size=(1280, 720))
camera_ratation = np.zeros((3), dtype=np.float)
camera_location = np.array((10, 10, 0.5), dtype=np.float)
camera2absolute_rotation_matrix = get_rotate_matrix(camera_ratation)

#coordinate
coordinate = Coordinate3D(actual_size=np.array((20, 20, 2)), ratio=np.array((100, 100, 100)))

#radar init
radar = Radar(coordinate, '.\\utils\\can\\ControlCAN.dll')

#loop start
camera.start_camera_loop()
radar.start_update_loop()

colors = random_colors(len(class_names))
drawer = RectangleDrawer(font_size=40)
i_frame = 0
t0 = time.time()
while True:
    frame = camera.get_current_frame()
    
    # 格式转变，BGRtoRGB
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # 转变成Image
    frame = Image.fromarray(np.uint8(frame))
    # 进行检测
    rectangle_class_names, rectangle_scores, rectangle_boxes = yolo.detect_image(frame)
    for i,c in enumerate(rectangle_class_names):
        center = ((rectangle_boxes[i][1] + rectangle_boxes[i][3]) / 2, (rectangle_boxes[i][0] + rectangle_boxes[i][2]) / 2)
        print(center)
        direction_in_camera = camera.get_pixel_direction(center)
        print(direction_in_camera)
        direction_abusolute = np.dot(camera2absolute_rotation_matrix, direction_in_camera)
        print(direction_abusolute)
        location_abusolute = coordinate.get_location_by_direction(camera_location, direction_abusolute)
        print(location_abusolute)
        if(location_abusolute is None):
            text = 'Type:{} Score:{:.2f}'.format(c, rectangle_scores[i])
        else:
            location_in_camera = location_abusolute - camera_location
            text = 'Type:{} Score:{:.2f} Location:{}'.format(c, rectangle_scores[i], (location_in_camera[0], location_in_camera[1]))
        frame = drawer.draw_rectangle(frame, box=rectangle_boxes[i], thickness=6, color=colors[class_names.index(c)], text=text, font_size=40)
    frame = np.array(frame)

    print('==================================')

    # RGBtoBGR满足opencv显示格式
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    cv2.imshow("video", frame)

    i_frame += 1

    if cv2.waitKey(1) == 27:
        break
    
t1 = time.time()
print('FPS', i_frame / (t1 - t0))







    

        
    



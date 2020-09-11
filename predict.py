#-------------------------------------#
#       对单张图片进行预测
#-------------------------------------#
from yolo.yolo_v4 import YOLO
from PIL import Image
import numpy as np

anchors = [8.0, 24.0, 8.0, 74.0, 13.0, 33.0, 20.0, 40.0, 23.0, 166.0, 24.0, 60.0, 39.0, 69.0, 61.0, 114.0, 100.0, 200.0]
anchors = np.array(anchors).reshape([-1, 3, 2])[::-1,:,:]
class_names = ["Car", "Van", 'Truck', 'Pedestrian', 'Person_sitting', 'Cyclist', 'Tram', 'Misc']

yolo = YOLO(anchors=anchors, class_names=class_names)

img = '.\\test_data\\img\\street.jpg'
try:
    image = Image.open(img)
except:
    print('Open Error! Try again!')
else:
    r_image = yolo.detect_image(image)
    r_image.show()
    

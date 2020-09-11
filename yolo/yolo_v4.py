import cv2
import numpy as np
import colorsys
import os
import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn
from PIL import Image,ImageFont, ImageDraw
from torch.autograd import Variable
from yolo.nets.yolo_v4_body import YoloBody
from utils.yolo_utils import non_max_suppression, bbox_iou, DecodeBox,letterbox_image,yolo_correct_boxes

class YOLO(object):
    #init
    def __init__(
        self, 
        model_path='.\\yolo\\model\\kitti.pth',
        anchors = [],
        class_names = [],
        model_image_size = (416, 416, 3),
        confidence = 0.8,
        cuda = True
    ):
        self.model_path = model_path
        self.anchors = anchors
        self.class_names = class_names
        self.model_image_size = model_image_size
        self.confidence = confidence
        self.cuda = cuda

        #init yolo net
        self.net = YoloBody(len(self.anchors[0]),len(self.class_names)).eval()

        #load model
        print('Loading weights from {} ....'.format(self.model_path))
        device = torch.device('cuda' if self.cuda else 'cpu')
        state_dict = torch.load(self.model_path, map_location=device)
        self.net.load_state_dict(state_dict)
        
        if self.cuda:
            os.environ['CUDA_VISIBLE_DEVICES'] = '0'
            self.net = nn.DataParallel(self.net)
            self.net = self.net.cuda()
    
        print('Finished!')

        self.yolo_decodes = []
        for i in range(3):
            self.yolo_decodes.append(DecodeBox(self.anchors[i], len(self.class_names),  (self.model_image_size[1], self.model_image_size[0])))

    #detect image
    def detect_image(self, image):
        image_shape = np.array(np.shape(image)[0:2])

        crop_img = np.array(letterbox_image(image, (self.model_image_size[0],self.model_image_size[1])))
        photo = np.array(crop_img,dtype = np.float32)
        photo /= 255.0
        photo = np.transpose(photo, (2, 0, 1))
        photo = photo.astype(np.float32)
        images = []
        images.append(photo)
        images = np.asarray(images)

        with torch.no_grad():
            images = torch.from_numpy(images)
            if self.cuda:
                images = images.cuda()
            outputs = self.net(images)

        output_list = []
        for i in range(3):
            output_list.append(self.yolo_decodes[i](outputs[i]))
        output = torch.cat(output_list, 1)
        batch_detections = non_max_suppression(output, len(self.class_names),
                                                conf_thres=self.confidence,
                                                nms_thres=0.3)
        try:
            batch_detections = batch_detections[0].cpu().numpy()
        except:
            return [], [], []
            
        top_index = batch_detections[:,4]*batch_detections[:,5] > self.confidence
        top_conf = batch_detections[top_index,4]*batch_detections[top_index,5]
        top_label = np.array(batch_detections[top_index,-1],np.int32)
        top_bboxes = np.array(batch_detections[top_index,:4])
        top_xmin, top_ymin, top_xmax, top_ymax = np.expand_dims(top_bboxes[:,0],-1),np.expand_dims(top_bboxes[:,1],-1),np.expand_dims(top_bboxes[:,2],-1),np.expand_dims(top_bboxes[:,3],-1)

        # 去掉灰条
        boxes = yolo_correct_boxes(top_ymin,top_xmin,top_ymax,top_xmax,np.array([self.model_image_size[0],self.model_image_size[1]]),image_shape)

        rectangle_class_names = []
        rectangle_scores = []
        rectangle_boxes = []

        for i, c in enumerate(top_label):      
            rectangle_class_names.append(self.class_names[c])
            rectangle_scores.append(top_conf[i])

            top, left, bottom, right = boxes[i]
            top = top - 5
            left = left - 5
            bottom = bottom + 5
            right = right + 5

            top = max(0, np.floor(top + 0.5).astype('int32'))
            left = max(0, np.floor(left + 0.5).astype('int32'))
            bottom = min(np.shape(image)[0], np.floor(bottom + 0.5).astype('int32'))
            right = min(np.shape(image)[1], np.floor(right + 0.5).astype('int32'))

            rectangle_boxes.append([top, left, bottom, right])
        # print(rectangle_class_names)
        # print(rectangle_scores)
        # print(rectangle_boxes)

        return rectangle_class_names, rectangle_scores, rectangle_boxes


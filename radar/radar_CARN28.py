import time
import threading
import numpy as np

from utils.error import Error
from utils.can.can_obj import CanFrame
from utils.can.const import MAX_DEVICES_IN_CHANNEL, DELTA_ADDRESS
from utils.can.canlyst_two import CanalystTwo

#mask
RW_MASK = 0b00000001

class Radar_CARN28:
    #------hardware------
    #device
    #can device
    can_device = None

    #channel id
    channel_id = 0

    #radar id
    radar_id = 0

    #message
    #message_id
    CONFIG_MESSAGE_ID = 0x201
    RADAR_RETURN_MESSAGE_ID = 0x202
    CLUSTER_LOCATION_MESSAGE_ID = 0x403
    CLUSTER_SHAPE_MESSAGE_ID = 0x404

    #dataType(name)
    RADAR_ID = 0b1
    VERSION = 0b10
    OUTPUT_MODE = 0b11
    OUTPUT_SWITCH = 0b100
    DETECTION_MODE = 0b101
    STATE = 0b110
    CAN_CONFIG = 0b111
    SAVE = 0b1111111

    #R/W
    R_CONST = 0
    W_CONST = 1

    #output mode
    POINT_MODE = 0
    CLUSTER_MODE = 1
    TRACE_MODE = 2
    IIRFILTER_MODE = 3

    #output switch
    STOP = 0
    START = 1

    #detection mode 
    SHORT_MODE = 1
    MIDDLE_MODE = 2

    #can config
    CAN_BAUD_CONFIG = 0
    CAN_FRAME_CONFIG = 1
    BAUD_250K = 1
    BAUD_500K = 2
    BAUD_1000K = 3
    STANDARD_FRAME = 1
    EXTEND_FRAME = 2

    #const
    CLUSTER_LOCATION_OFFSET = 32678

    #state
    output_mode = CLUSTER_MODE
    output_switch = START
    detection_mode = SHORT_MODE
    can_baud = BAUD_500K
    frame_type = STANDARD_FRAME

    #------software------
    #name
    UPDATE_INTERVAL = -1
    
    #state
    update_interval = 0.5
    loop_flag = False
    loop_thread = None

    #------coordinate------
    DEFAULT_HEIGHT = 0.2
    add_object = None
    del_object = None

    #objects
    objects = []#[object_id]

    def __init__(self, can_device=None, channel_id=0, radar_id=0, update_interval=0.5, add_object=None, del_object=None):
        super().__init__()
        self.can_device = can_device
        self.channel_id = channel_id
        self.radar_id = radar_id
        self.update_interval = update_interval
        self.add_object = add_object
        self.del_object = del_object

    def set_hardware(self, name=RADAR_ID, value=None):
        if(value == None):
            Error.handle_error('radar hardware set value error')
            return False

        #radar hardware related
        dataType_and_RW = name << 1 | self.W_CONST
        ret = 0
        config_message_id = self.CONFIG_MESSAGE_ID + self.radar_id * DELTA_ADDRESS
        if name == self.RADAR_ID:
            #radar_id: [dataType:0b1 + R/W:0/1, Value: radar_id]
            set_radar_id_message = CanFrame(config_message_id, [dataType_and_RW, value])
            if not value in range(MAX_DEVICES_IN_CHANNEL):
                Error.handle_error('radar set radar id value error')
                return False
            ret = self.can_device.transmit_message(self.channel_id, set_radar_id_message)
        elif name == self.OUTPUT_MODE:
            #output mode: [dataType:0b11 + R/W:0/1, PointOutput: stop:0 / start:1, ClusterOutput: stop:0 / start:1, TraceOutput: stop:0 / start:1, IIRFilterOutput: stop:0 / start:1, Reserve:0]
            set_output_mode_message = CanFrame(config_message_id, [dataType_and_RW, 0, 0, 0, 0, 0])
            output_mode = value
            if output_mode == self.POINT_MODE:
                set_output_mode_message.data[1] = 1
            elif output_mode == self.CLUSTER_MODE:
                set_output_mode_message.data[2] = 1
            elif output_mode == self.TRACE_MODE:
                set_output_mode_message.data[3] = 1
            elif output_mode == self.IIRFILTER_MODE:
                set_output_mode_message.data[4] = 1
            else:
                Error.handle_error('radar set output mode value error')
                return False
            ret = self.can_device.transmit_message(self.channel_id, set_output_mode_message)
        elif name == self.OUTPUT_SWITCH:
            #output switch: [dataType:0b100 + R/W:0/1, Value: stop:0 / start:1]
            if value != self.STOP and value != self.START:
                Error.handle_error('radar set output switch value error')
                return False
            set_output_switch_message = CanFrame(config_message_id, [dataType_and_RW, value])
            ret = self.can_device.transmit_message(self.channel_id, set_output_switch_message)
        elif name == self.DETECTION_MODE:
            #detection mode: [dataType:0b101 + R/W:0/1, Radar_Mode: short:1 / middle:2]
            if value != self.SHORT_MODE and value != self.MIDDLE_MODE:
                Error.handle_error('radar set detection mode value error')
                return False
            set_detection_mode_message = CanFrame(config_message_id, [dataType_and_RW, value])
            ret = self.can_device.transmit_message(self.channel_id, set_detection_mode_message)
        elif name == self.CAN_CONFIG:
            #can config: [dataType:0b111 + R/W:0/1, Baud: 250k:1 / 500k:2 / 1000k:3, Y/N:0/1, FrameType: standard:1, extend:2, Y/N:0/1]
            baud = value[self.CAN_BAUD_CONFIG]
            frame_type = value[self.CAN_FRAME_CONFIG]
            if baud != self.BAUD_250K and baud != self.BAUD_500K and baud != self.BAUD_1000K:
                Error.handle_error('radar set can config value error')
                return False
            if frame_type != self.STANDARD_FRAME and frame_type != self.EXTEND_FRAME:
                Error.handle_error('radar set can config value error')
                return False
            set_can_config_message = CanFrame(config_message_id, [dataType_and_RW, baud, 1, frame_type, 1])
            ret = self.can_device.transmit_message(self.channel_id, set_can_config_message)
        else:
            Error.handle_error('radar set name error')
            return False

        if not ret:
            Error.handle_error('radar hardware set error')
            return False

        time.sleep(0.5) #wait ack

        radar_return_message_id = self.RADAR_RETURN_MESSAGE_ID + self.radar_id * DELTA_ADDRESS
        ack = self.can_device.get_data_by_id(self.channel_id, radar_return_message_id)

        if len(ack) == 0:
            Error.handle_error('radar hardware set ack error')
            return False
        
        #type of ack is list canFrame
        #the length of ack should be 1, if not, choose the last(also leatest) one
        ack_data = ack[-1].data
        
        #ack_data: [dataType:0b110 + success:0/1, radar_id, detection_mode, output switch, point:0/1 + cluster:0/1 + trace:0/1 + iirFilter:0/1 + reserved, can_baud: + can_type]
        if ack_data[0] & RW_MASK == 1:
            if name == self.RADAR_ID:
                self.radar_id = value
            elif name == self.OUTPUT_MODE:
                self.output_mode = value
            elif name == self.OUTPUT_SWITCH:
                self.output_switch = value
            elif name == self.DETECTION_MODE:
                self.detection_mode = value
            elif name == self.CAN_CONFIG:
                self.can_baud = value[self.CAN_BAUD_CONFIG]
                self.frame_type = value[self.CAN_FRAME_CONFIG]
            else:#never come here
                return False
        else:
            Error.handle_error('radar hardware set error')
            return False

        return True

    def set_software(self, name=UPDATE_INTERVAL, value=None):
        if(value == None):
            Error.handle_error('radar software set value error')
            return False

        if name == self.UPDATE_INTERVAL:
            self.update_interval = value
            
        return True

    def save_hardware_state(self):
        set_save_message = CanFrame(CONFIG_MESSAGE_ID + self.radar_id * DELTA_ADDRESS, [self.SAVE << 1 | self.W_CONST, 0])
        ret = self.can_device.transmit_message(self.channel_id, set_save_message)
        if not ret:
            Error.handle_error('radar state save error')
            return False

        radar_return_message_id = self.RADAR_RETURN_MESSAGE_ID + self.radar_id * DELTA_ADDRESS
        ack = self.can_device.get_data_by_id(self.channel_id, radar_return_message_id)

        if len(ack) == 0:
            Error.handle_error('radar save ack error')
            return False

        ack_data = ack[-1].data

        if ack_data[0] & RW_MASK != 1:
            Error.handle_error('radar state save error')
            return False
        
        return True

    def start_update_loop(self):
        self.loop_flag = True
        self.can_device.start_receive_loop(self.channel_id)
        if(self.loop_thread == None):
            self.loop_thread = threading.Thread(target=self._update_loop, daemon=True)
        print('radar_carn28 loop start')
        self.loop_thread.start()

    def pause_update_loop(self):
        self.loop_flag = False
        self.can_device.pause_receive_loop(self.channel_id)

    def _update_loop(self):
        while self.loop_flag:
            #TODO 目前只实现了聚类检测
            if(self.output_mode == self.CLUSTER_MODE):
                self._cluster_update()
            time.sleep(self.update_interval)
        
    def _cluster_update(self):
        # print('cluster loop')
        cluster_location_message_id = self.CLUSTER_LOCATION_MESSAGE_ID + DELTA_ADDRESS * self.radar_id
        cluster_shape_message_id = self.CLUSTER_SHAPE_MESSAGE_ID + DELTA_ADDRESS * self.radar_id

        location_data = self.can_device.get_data_by_id(self.channel_id, cluster_location_message_id)
        shape_data = self.can_device.get_data_by_id(self.channel_id, cluster_shape_message_id)

        # Length of location data is the same as shape data. Their type is list of canframe
        # location: [total, index, location x, location x, location y, location y]
        # shape: [total, index, shape x, shape x, shape y, shape y]
        if(len(location_data) == 0):
            return

        total = location_data[-1].data[0]
        print('objects number: {}'.format(len(self.objects)))
        print('----------------------------------------------')
        if len(location_data) >= total: #在这种情况下，列表中的数据全部无用，需要清除后重新添加
            for i in self.objects:
                self.del_object(i)
            self.objects = []
            for i in range(total):
                location_frame = location_data[i + (len(location_data) - total)]
                shape_frame = shape_data[i + (len(shape_data) - total)]
                location_x = (location_frame.data[2] * 256 + location_frame.data[3] - self.CLUSTER_LOCATION_OFFSET) * 0.01 #unit: meter
                location_y = (location_frame.data[4] * 256 + location_frame.data[5] - self.CLUSTER_LOCATION_OFFSET) * 0.01 #unit: meter
                location = np.array([location_x, location_y, 0])
                shape_x = (shape_frame.data[2] * 256 + shape_frame.data[3]) * 0.01 * 10 #unit: meter
                shape_y = (shape_frame.data[4] * 256 + shape_frame.data[5]) * 0.01 * 10 #unit: meter
                shape = np.array([shape_x, shape_y, self.DEFAULT_HEIGHT])
                object_id = self.add_object(self.radar_id, location, shape)
                if object_id != -1:
                    self.objects.append(object_id)
        else:#在这种情况下，上一次update时的部分数据仍然有效
            for i in range(total):
                if(len(location_data) - (total - 1) >= i):
                    continue
                else:
                    location_frame = location_data[i + (len(location_data) - total)]
                    shape_frame = shape_data[i + (len(shape_data) - total)]
                    location_x = (location_frame.data[2] * 256 + location_frame.data[3] - self.CLUSTER_LOCATION_OFFSET) * 0.01 #unit: meter
                    location_y = (location_frame.data[4] * 256 + location_frame.data[5] - self.CLUSTER_LOCATION_OFFSET) * 0.01 #unit: meter
                    location = np.array([location_x, location_y, 0]) + self.location
                    shape_x = (shape_frame.data[2] * 256 + shape_frame.data[3]) * 0.01* 10 #unit: meter
                    shape_y = (shape_frame.data[4] * 256 + shape_frame.data[5]) * 0.01* 10 #unit: meter
                    shape = np.array([shape_x, shape_y, self.DEFAULT_HEIGHT])
                    object_id = self.coordinate.add_object(self.radar_id, location, shape)
                    if object_id != -1:
                        self.objects.append(object_id)


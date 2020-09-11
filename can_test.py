import time
import threading
import numpy as np

from utils.error import Error
from utils.can.can_obj import CanFrame
from utils.can.const import MAX_DEVICES_IN_CHANNEL, DELTA_ADDRESS
from utils.can.canlyst_two import CanalystTwo

class CanTest:
    #------hardware------
    #device
    #can device
    can_device = None

    #channel id
    channel_id = 1

    #message
    #message_id
    CLUSTER_LOCATION_MESSAGE_ID = 0x403
    CLUSTER_SHAPE_MESSAGE_ID = 0x404

    #state
    update_interval = 0.5
    loop_flag = False
    loop_thread = None

    def __init__(self, can_device=None, channel_id=1, file_name=''):
        super().__init__()
        self.can_device = can_device
        self.channel_id = channel_id
        self.messages = []
        with open(file_name) as f:
            self.messages = f.readlines()[1:]
        self.messages = self._parse_messages(self.messages)

    def start_send_loop(self):
        print('can test loop start')
        self.loop_flag = True
        if(self.loop_thread == None):
            self.loop_thread = threading.Thread(target=self._send_loop, daemon=True)
        self.loop_thread.start()

    def _send_loop(self):
        time_start = time.time()
        i = 0
        time_stamp_0 = self.messages[0].time_stamp
        while self.loop_flag:
            time_now = time.time()
            time.sleep(0.2)
            while (time_now - time_start > self.messages[i].time_stamp - time_stamp_0):
                self.can_device.transmit_message(self.channel_id, self.messages[i])
                i += 1
                # print(self.messages[i].time_stamp)

    def _parse_messages(self, messages):
        parsed_messages = []
        for message in  messages:
            data_list = message.split(' ')
            while True:
                try:
                    data_list.remove('')
                except:
                    break
            time_list = data_list[1].split(':')
            time_stamp = float(time_list[0]) * 3600 + float(time_list[1]) * 60 + float(time_list[2][0:-2])
            message_id = int(data_list[2], 16)
            data = []
            for item in data_list[6:-1]:
                data.append(int(item, 16))
            parsed_messages.append(CanFrame(message_id, data, time_stamp))
            # print(message_id, data, time_stamp)
        return parsed_messages


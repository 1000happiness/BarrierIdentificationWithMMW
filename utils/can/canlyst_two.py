import threading
import time
import copy
from ctypes import *

from utils.can.can_obj import CanFrame


#status
STATUS_OK = 1  #OK
STATUS_ERR = 0  #When can dll function return 0, it means something that can be resolved happened.
STATUS_EXIT = -1  #When can dll function return -1, it means something that can't be resolved happened.

#max error times
MAX_ERROR_TIMES = 5

#type
ubyte_3array = c_ubyte * 3
ubyte_8array = c_ubyte * 8

class VCI_INIT_CONFIG(Structure):
    _fields_ = [('acc_code', c_uint),
                ('acc_mask', c_uint),
                ('reserved', c_uint),
                ('filter', c_ubyte),
                ('timing0', c_ubyte),
                ('timing1', c_ubyte),
                ('mode', c_ubyte)
                ]

class VCI_CAN_OBJ(Structure):
    _fields_ = [('id', c_uint),
                ('time_stamp', c_uint),
                ('time_flag', c_ubyte),
                ('send_type', c_ubyte),
                ('remote_flag', c_ubyte),
                ('extern_flag', c_ubyte),
                ('data_length', c_ubyte),
                ('data', ubyte_8array),
                ('reserved', ubyte_3array)
                ]

vci_can_obj_array = VCI_CAN_OBJ * 2500

#baud map table
#baud map table for timing0
baud_map_table0 = {
    '125k': 0x03,
    '500k': 0x00,
}

#baud map table for timing1
baud_map_table1 = {
    '10k': 0x1C,
    '500k': 0x1C,
}

class CanalystTwo:
    #const
    VCI_USBCAN2 = 4 #DevType
    CH1 = 0 #can channel 1
    CH2 = 1  #can channel 2
    DATA_RESERVED = ubyte_3array(0, 0, 0)

    #dll
    can_dll = None

    #opened device
    n_device = 0

    #channel config
    channel_init_config = VCI_INIT_CONFIG(0x00000000, 0xFFFFFFFF, 0, 2, 0x00, 0x1C, 0)

    #channel in use flag
    channel_use_flag = [False, False]

    #message buffer
    message_buffer = [{},{}]
    transmit_vci_can_obj = VCI_CAN_OBJ(0, 0, 0, 1, 0, 0, 0, ubyte_8array(0,0,0,0,0,0,0,0), DATA_RESERVED) #send one frame one time
    receive_vci_can_obj_array = vci_can_obj_array() #receivce 2500 frames at most one time

    #receive thread
    channel_receive_threads = [None, None]

    def __init__(self, can_dll=None):
        super().__init__()

        self.can_dll = can_dll
        

    def __del__(self):
        self.close_device(self.n_device)       

    def open_device(self, n_device=0):
        self.n_device = n_device
        self.close_device(n_device)

        err_times = 0
        while (True):
            ret = self.can_dll.VCI_OpenDevice(self.VCI_USBCAN2, n_device, 0)
            if ret == STATUS_OK:
                return True
            elif ret == STATUS_ERR:
                err_times = err_times + 1
                if (not self._handle_error(err_times, 'VCI_OpenDevice error')):
                    return False
            elif ret == STATUS_EXIT:
                self._handle_exit('VCI_OpenDevice exit')
                return False
            else:
                self._handle_exit('VCI_OpenDevice ret value error')
                return False

        self.devices.append(n_device)
        
    def close_device(self, n_device=0):
        self.n_device = n_device
        err_times = 0
        while (True):
            ret = self.can_dll.VCI_CloseDevice(self.VCI_USBCAN2, self.n_device)
            if ret == STATUS_OK:
                return True
            elif ret == STATUS_ERR:
                return False
            elif ret == STATUS_EXIT:
                self._handle_exit('VCI_CloseDevice exit')
                return False
            else:
                self._handle_exit(err_times, 'VCI_CloseDevice ret value error')
                return False

    def init_channel(self, channel_id=CH1, baud0='500k', baud1='500k'):
        if (channel_id != self.CH1 and channel_id != self.CH2):
            print('channel id error\n')
            return False

        self.channel_init_config.timing0 = c_ubyte(
            baud_map_table0[baud0])
        self.channel_init_config.timing1 = c_ubyte(
            baud_map_table1[baud1])

        print(self.channel_init_config.timing0)

        err_times = 0
        while (True):
            ret = self.can_dll.VCI_InitCAN(self.VCI_USBCAN2, self.n_device, channel_id, byref(self.channel_init_config))
            if ret == STATUS_OK:
                break
            elif ret == STATUS_ERR:
                err_times = err_times + 1
                if (not self._handle_error(err_times, 'VCI_InitCAN error')):
                    return False
            elif ret == STATUS_EXIT:
                self._handle_exit('VCI_InitCAN error exit')
                return False
            else:
                self._handle_exit('VCI_InitCAN ret value error')
                return False

        err_times = 0
        while (True):
            ret = self.can_dll.VCI_StartCAN(self.VCI_USBCAN2, self.n_device, channel_id)
            if ret == STATUS_OK:
                break
            elif ret == STATUS_ERR:
                err_times = err_times + 1
                if (not self._handle_error(err_times, 'VCI_StartCAN error')):
                    return False
            elif ret == STATUS_EXIT:
                self._handle_exit('VCI_StartCAN error exit')
                return False
            else:
                self._handle_exit('VCI_StartCAN ret value error')
                return False

        return True

    def transmit_message(self, channel_id=CH1, can_frame=CanFrame()):
        if (channel_id != self.CH1 and channel_id != self.CH2):
            print('channel id error\n')
            return False

        self.transmit_vci_can_obj.id = can_frame.message_id
        self.transmit_vci_can_obj.data_length = len(can_frame.data)
        for i, item in enumerate(can_frame.data):
            # print(i, item)
            self.transmit_vci_can_obj.data[i] = c_ubyte(item)

        err_times = 0
        while (True):
            ret = self.can_dll.VCI_Transmit(self.VCI_USBCAN2, self.n_device, channel_id, byref(self.transmit_vci_can_obj), 1)
            if ret == STATUS_OK:
                break
            elif ret == STATUS_ERR:
                err_times = err_times + 1
                if (not self._handle_error(err_times, 'VCI_Transmit error')):
                    return False
            elif ret == STATUS_EXIT:
                self._handle_exit('VCI_Transmit error exit')
                return False
            else:
                self._handle_exit('VCI_Transmit ret value error')
                return False
        return True

    def start_receive_loop(self, channel_id=CH1):
        if (channel_id != self.CH1 and channel_id != self.CH2):
            print('channel id error\n')
            return False
        self.channel_use_flag[channel_id] = True

        if (self.channel_receive_threads[channel_id] == None):
            self.channel_receive_threads[channel_id] = threading.Thread(target=self._receive_loop, args=(channel_id,), daemon=True)
            self.channel_receive_threads[channel_id].start()
        else:
            self.channel_receive_threads[channel_id].start()
        
        return True

    def pause_receive_loop(self, channel_id=CH1):
        self.channel_use_flag[channel_id] = False

    def get_data_by_id(self, channel_id=CH1, message_id=None, flush=True):
        if message_id in self.message_buffer[channel_id]:
            data = copy.deepcopy(self.message_buffer[channel_id].get(message_id, None))
            if(flush):
                self.message_buffer[channel_id][message_id] = []
            return data
        else:
            return []
    
    def get_data(self, channel_id=CH1):
        return self.message_buffer[channel_id]

    def _receive_message(self, channel_id=CH1):
        err_times = 0
        while (True):
            ret = self.can_dll.VCI_Receive(self.VCI_USBCAN2, self.n_device, channel_id, byref(self.receive_vci_can_obj_array), 2500, 0)
            if ret > 0:
                for i in range(ret):
                    vci_can_obj = self.receive_vci_can_obj_array[i]
                    message_id = vci_can_obj.id
                    length = vci_can_obj.data_length
                    data = []
                    for k in range(length):
                        data.append(vci_can_obj.data[k])
                    time_stamp = vci_can_obj.time_stamp #time_interval = time_stamp * 0.1ms * 0.001s/ms
                    if(message_id in self.message_buffer[channel_id]):
                        self.message_buffer[channel_id][message_id].append(CanFrame(message_id, data, time_stamp))
                    else:
                        self.message_buffer[channel_id][message_id] = [CanFrame(message_id, data, time_stamp)]
                return ret
            elif ret == STATUS_ERR:
                return 0
            elif ret == STATUS_EXIT:
                self._handle_exit('VCI_Receive error exit')
                return -1

    def _receive_loop(self, channel_id=CH1):
        while (self.channel_use_flag[channel_id]):
            ret = self._receive_message(channel_id)
            time.sleep(0.03)

    def _handle_error(self, times, message):
        if (times < MAX_ERROR_TIMES):
            print(time.strftime('[%H:%M:%S] ', time.localtime()), '[%d times] ' % times, message)
            time.sleep(3)
            return True
        else:
            print(time.strftime('[%H:%M:%S] ', time.localtime()), '[%d times] ' % times, message)
            return False

    def _handle_exit(self, message):
        print(time.strftime('[%H:%M:%S] ', time.localtime()), message)
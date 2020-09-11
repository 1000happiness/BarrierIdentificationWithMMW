import numpy as np

from radar.radar_CARN28 import Radar_CARN28
from utils.dll_loader import DllLoader
from utils.coordinate import Coordinate3D
from utils.can.canlyst_two import CanalystTwo

#TODO
from can_test import CanTest

class Radar:
    #coordinate
    coordinate = None

    #can
    can_device = None

    #radars
    radars = {}

    #radar config
    radars_config = {}

    def __init__(self, 
        coordinate = Coordinate3D(actual_size=np.array((20, 20, 2)), ratio=np.array((100, 100, 100))), 
        dll_path = '.\\utils\\can\\ControlCAN.dll',
    ):
        super().__init__()
        self.coordinate = coordinate

        dll_loader = DllLoader(dll_path)
        can_dll = dll_loader.get_dll()

        self.can_device = CanalystTwo(can_dll)
        self.can_device.open_device(0)
        self.can_device.init_channel(CanalystTwo.CH1)

        radar_id = len(self.radars)
        self.radars_config[radar_id] = {
            'location': np.array((10, 10, 0.5)),
            'rotation': np.zeros((0, 0, 0))
        }
        
        self.radars[radar_id] = Radar_CARN28(self.can_device, CanalystTwo.CH1, radar_id, 0.5, self.coordinate_add_object, self.coordinate_del_object)

        #TODO test
        self.can_device.init_channel(CanalystTwo.CH2)
        self.can_test = CanTest(self.can_device, CanalystTwo.CH2, '.\\test_data\\can\\9.2.3.txt')

    def start_update_loop(self):
        for radar_id in self.radars:
            self.radars[radar_id].start_update_loop()
        self.can_test.start_send_loop()

    def pause_update_loop(self):
        self.radar_carn28.pause_update_loop()

    def get_location_by_direction(self, from_location=np.zeros((3)), direction=np.zeros((3))):
        return self.coordinate.get_location_by_direction(from_location, direction)

    def coordinate_add_object(self, radar_id, location, shape):
        location = location + self.radars_config[radar_id]['location']
        half_shape = shape / 2
        corners = [
            location + half_shape * np.array([-1, -1, -1]),
            location + half_shape * np.array([ 1, -1, -1]),
            location + half_shape * np.array([ 1,  1, -1]),
            location + half_shape * np.array([-1,  1, -1]),
            location + half_shape * np.array([-1, -1,  1]),
            location + half_shape * np.array([ 1, -1,  1]),
            location + half_shape * np.array([ 1,  1,  1]),
            location + half_shape * np.array([-1,  1,  1]),
        ]
        # print(corners)
        object_id = self.coordinate.add_object(corners)
        return object_id

    def coordinate_del_object(self, object_id):
        return self.coordinate.del_object(object_id)




        
                
    
    
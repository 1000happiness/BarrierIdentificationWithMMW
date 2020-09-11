import numpy as np
class Coordinate2D():
    #actual size
    actual_size = np.zeros((2))

    #ratio     
    ratio = np.zeros((2)) #np.size = actual_size * ratio

    #3D array
    coordinate_array = None

    #object list
    objects = {}#{id:corner}

    def __init__(self, actual_size=np.zeros((2)), ratio=np.zeros((2))):
        super().__init__()
        size_np = np.ceil(actual_size * ratio)
        size_np = (size_np[0], size_np[1])
        self.coordinate_array = np.array(size_np)

    def get_location_by_direction(self, from_location=np.zeros((2)), direction=np.zeros((2))):
        np_location = from_location * ratio
        np_direction = direction * ratio
        while self.coordinate_array.shape - np_location >= 0:
            np_location_floor = np.floor(np_location)
            object_id = self.coordinate_array[np_location_floor[0], np_location_floor[1]]
            if(object_id != 0):
                return (self.objects[object_id][0] + self.objects[object_id][2]) / 2 / self.ratio
        return np.array([-1,-1])                 

    def add_object(self, corners = [np.zeros((2)) * 4]):
        for corner in corners:
            if (corner - self.actual_size).any() > 0:
                return -1

        #TODO 此处理论上需要使用光栅化算法实现，暂时先使用简单的方式实现，改变整个矩形包围盒的值
        object_id = len(self.objects)

        min_np = corners[1]
        max_np = corners[3]

        self.coordinate_array[min_np[0]:max_np[0], min_np[1]:max_np[1]] = object_id
        
        self.objects[object_id] = corners

        return object_id

    def del_object(self, object_id=0):
        if not object_id in self.objects < 0:
            return -1

        #TODO 此处理论上需要使用光栅化算法实现，暂时先使用简单的方式实现，改变整个矩形包围盒的值
        min_np = self.objects[object_id][1]
        max_np = self.objects[object_id][3]

        self.coordinate_array[min_np[0]:max_np[0], min_np[1]:max_np[1]] = 0

        self.objects.pop(object_id)

        return object_id

#x+: right
#y+: front
#z+: top
class Coordinate3D():
    #actual size
    actual_size = np.zeros((3))

    #ratio     
    ratio = np.zeros((3)) #onp.shape = actual_size * ratio

    #3D array
    coordinate_array = np.zeros((1,1,1), dtype=np.int)

    #object list
    objects = {}#{id:(min_np,max_np)}

    def __init__(self, actual_size=np.zeros((3)), ratio=np.zeros((3))):
        super().__init__()
        self.actual_size = actual_size
        self.ratio = ratio
        size_np = actual_size * ratio
        self.coordinate_array = np.zeros((size_np[0], size_np[1], size_np[2]), dtype=np.int)

    def get_location_by_direction(self, from_location=np.zeros((3)), direction=np.zeros((3))):
        from_location_np = np.floor(from_location * self.ratio)
        print('search', from_location_np, direction)
        while (from_location_np - self.coordinate_array.shape < -10).all():
            # print('search', from_location_np, self.coordinate_array.shape, (from_location_np - self.coordinate_array.shape < -10).any())
            from_location_np_int = np.floor(from_location_np).astype(int)
            if(self.coordinate_array[from_location_np_int[0], from_location_np_int[1], from_location_np_int[2]] > 0):
                object_id = self.coordinate_array[from_location_np[0]][from_location_np[0]][from_location_np[0]]
                to_location_np = (self.objects[object_id][0] + self.objects[object_id][1]) / 2
                to_location = to_location_np / self.ratio
                return to_location
            from_location_np += direction * self.ratio / 10
        return None
        
    def add_object(self, corners=np.zeros((8, 3))):
        for corner in corners:
            if (corner - self.actual_size > 0).any():
                return -1

        
        min_np = np.floor(corners[0] * self.ratio).astype(int)
        max_np = np.floor(corners[6] * self.ratio).astype(int)

        object_id = len(self.objects)
        print('add', object_id, min_np, max_np)
        self.coordinate_array[min_np[0]:max_np[0], min_np[1]:max_np[1], min_np[2]:max_np[2]] = object_id
        
        self.objects[object_id] = corners

        return object_id

    def del_object(self, object_id=0):
        if not object_id in self.objects:
            return False

        corners = self.objects[object_id]
        min_np = np.floor(corners[0] * self.ratio).astype(int)
        max_np = np.floor(corners[6] * self.ratio).astype(int)
        print('del', object_id)
        self.coordinate_array[min_np[0]:max_np[0], min_np[1]:max_np[1], min_np[2]:max_np[2]] = 0

        self.objects.pop(object_id)

        return True

def get_rotate_matrix(rotation=np.zeros((3))):
    z_rotation_matrix = np.array([
        [np.cos(rotation[0]), (-1) * np.sin(rotation[0]), 0],
        [np.sin(rotation[0]), np.cos(rotation[0]), 0],
        [0, 0, 1]
    ])
    x_rotation_matrix = np.array([
        [1, 0, 0],
        [0, np.cos(rotation[1]), np.sin(rotation[1])],
        [0, (-1) * np.sin(rotation[1]), np.cos(rotation[1])]
        
    ])
    y_rotation_matrix = np.array([
        [np.cos(rotation[2]), 0, (-1) * np.sin(rotation[2])],
        [0, 1, 0],
        [np.sin(rotation[2]), 0, np.cos(rotation[2])]
    ])
    return np.dot(
        z_rotation_matrix,
        np.dot(
            x_rotation_matrix,
            y_rotation_matrix
        )
    )


        

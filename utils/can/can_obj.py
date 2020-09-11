class CanFrame():
    def __init__(self, message_id=0, data=[], time_stamp=0.0):
        super().__init__()
        self.message_id = message_id
        self.data = data
        self.time_stamp = time_stamp
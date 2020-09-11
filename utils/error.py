import time

class Error:
    def __init__(self):
        super().__init__()
    
    def handle_error(self, message):
        print(time.strftime('[%H:%M:%S]', time.localtime()), message)
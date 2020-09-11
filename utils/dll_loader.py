from ctypes import windll

class DllLoader:

    dll = None

    def __init__(self, dll_path=""):
        super().__init__()
        self.load_dll(dll_path)

    def load_dll(self, dll_dir=""):
        try:
            self.dll = windll.LoadLibrary(dll_dir)
        except OSError:
            print('{} dll load error'.format(dll_dir))
            return False
        else:
            return True

    def get_dll(self):
        return self.dll
            
    
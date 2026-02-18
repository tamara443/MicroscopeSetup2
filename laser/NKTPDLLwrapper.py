import ctypes
import os

class NKTPDLLWrapper:
    def __init__(self, dll_path, portname):
        self.dll = ctypes.CDLL(dll_path)
        self._set_argtypes_and_restypes()
        self.portname = portname.encode()

    def _set_argtypes_and_restypes(self):
        self.dll.registerWriteReadU16.argtypes = [ctypes.c_char_p, ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_ushort, ctypes.POINTER(ctypes.c_ushort), ctypes.c_short]
        self.dll.registerWriteReadU16.restype = ctypes.c_int
        self.dll.registerReadU16.argtypes = [ctypes.c_char_p, ctypes.c_ubyte, ctypes.c_ubyte, ctypes.POINTER(ctypes.c_ushort), ctypes.c_short]
        self.dll.registerReadU16.restype = ctypes.c_int

    def set_power_level(self, module_address, reg_id, power_level):
        dev_id = module_address
        power_level_write_value = ctypes.c_ushort(power_level)
        power_level_read_value = ctypes.c_ushort()
        index = -1
        result = self.dll.registerWriteReadU16(self.portname, dev_id, reg_id, power_level_write_value, ctypes.byref(power_level_read_value), index)
        return result

    def set_emission_state(self, module_address, reg_id, state):
        dev_id = module_address
        state_value = ctypes.c_ushort(state)
        read_value = ctypes.c_ushort()
        index = -1
        result = self.dll.registerWriteReadU16(
            self.portname, dev_id, reg_id, state_value,
            ctypes.byref(read_value), index
        )
        return result

    def read_register(self, module_address, reg_id, index):
        dev_id = module_address
        register_value = ctypes.c_ushort()
        result = self.dll.registerReadU16(self.portname, dev_id, reg_id, ctypes.byref(register_value), index)
        return result, register_value.value

    def write_register(self, module_address, reg_id, value, index):
        dev_id = module_address
        value_to_write = ctypes.c_ushort(value)
        value_read = ctypes.c_ushort()
        result = self.dll.registerWriteReadU16(
            self.portname, dev_id, reg_id, value_to_write,
            ctypes.byref(value_read), index
        )
        return result, value_read.value


# Example usage:
currDir = os.path.dirname(os.path.abspath(__file__))
dll_path = os.path.join(currDir, "NKTPDLL\\x64\\NKTPDLL.dll")
portname = 'COM3'
wrapper = NKTPDLLWrapper(dll_path, portname)

# Set power level
module_address = 0x0F
reg_id = 0x37
power_level = 200
result = wrapper.set_power_level(module_address, reg_id, power_level)
if result == 0:
    print(f"New power level set to: {power_level/10.0}%")
else:
    print("Error setting new power level")

# Read registers
module_address = 0x10
index = 0
register_ids = {'ND setpoint': 0x32, 'SWP setpoint': 0x33, 'LWP setpoint': 0x34, 'Monitor input': 0x13}

for register_name, reg_id in register_ids.items():
    result, register_value = wrapper.read_register(module_address, reg_id, index)
    if result == 0:
        print(f"{register_name}: {register_value/10.0}%")
    else:
        print(f"Error reading {register_name}: {result}")

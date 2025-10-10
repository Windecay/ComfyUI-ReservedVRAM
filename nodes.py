from typing import Any as any_type
from comfy import model_management

# 尝试导入pynvml库，如果没有安装则提供相应提示
try:
    import pynvml
    pynvml_installed = True
    pynvml.nvmlInit()
except ImportError:
    pynvml_installed = False
    print("警告：未安装pynvml库，auto选项将不可用。")

def get_gpu_memory_info():
    """获取GPU显存信息"""
    if not pynvml_installed:
        return None, None

    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        total = memory_info.total / (1024 * 1024 * 1024)  # 转换为GB
        used = memory_info.used / (1024 * 1024 * 1024)    # 转换为GB
        return total, used
    except Exception as e:
        print(f"获取GPU信息出错: {e}")
        return None, None

class AlwaysEqualProxy(str):
    def __eq__(self, _):
        return True

    def __ne__(self, _):
        return False
any_type = AlwaysEqualProxy("*")

class ReservedVRAMSetter:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "anything": (any_type, {}),
                "reserved": ("FLOAT", {
                    "default": 0.6,
                    "min": -2.0,
                    "step": 0.1,
                    "display": "reserved (GB)"
                }),
                "mode": (["manual", "auto"], {
                    "default": "auto",
                    "display": "Mode"
                })
            },
            "hidden": {"unique_id": "UNIQUE_ID", "extra_pnginfo": "EXTRA_PNGINFO"}
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("output",)
    OUTPUT_NODE = True
    FUNCTION = "set_vram"
    CATEGORY = "VRAM"

    def set_vram(self, anything, reserved, mode="auto", unique_id=None, extra_pnginfo=None):
        if mode == "auto":
            if pynvml_installed:
                total, used = get_gpu_memory_info()
                if total and used:
                    # 自动计算预留显存：使用当前已用显存+reserved设置值作为预留值
                    auto_reserved = used + reserved
                    auto_reserved = max(0, auto_reserved)  # 确保不小于0
                    model_management.EXTRA_RESERVED_VRAM = int(auto_reserved * 1024 * 1024 * 1024)
                    print(f'set EXTRA_RESERVED_VRAM={auto_reserved:.2f}GB (自动模式: 总显存={total:.2f}GB, 已用={used:.2f}GB)')
                else:
                    model_management.EXTRA_RESERVED_VRAM = int(reserved * 1024 * 1024 * 1024)
                    print(f'set EXTRA_RESERVED_VRAM={reserved}GB (自动模式失败，使用手动值)')
            else:
                model_management.EXTRA_RESERVED_VRAM = int(reserved * 1024 * 1024 * 1024)
                print(f'set EXTRA_RESERVED_VRAM={reserved}GB (pynvml未安装，auto选项不可用)')
        else:
            # 手动模式
            reserved = max(0, reserved)
            model_management.EXTRA_RESERVED_VRAM = int(reserved * 1024 * 1024 * 1024)
            print(f'set EXTRA_RESERVED_VRAM={reserved}GB (手动模式)')

        return (anything,)

NODE_CLASS_MAPPINGS = {
    "ReservedVRAMSetter": ReservedVRAMSetter
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "ReservedVRAMSetter": "Set Reserved VRAM(GB) ⚙️"
}
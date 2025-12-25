from typing import Any as any_type
from comfy import model_management
import random
import time
import gc

gpu_available = False
try:
    import pynvml
    try:
        pynvml.nvmlInit()
        gpu_available = True
        print("[ReservedVRAM]检测到GPU，启用GPU相关功能")
    except pynvml.NVMLError:
        print("[ReservedVRAM]GPU初始化失败，使用兼容模式")
except ImportError:
    print("[ReservedVRAM]未安装pynvml，使用无GPU兼容模式")

# 初始化随机状态
initial_random_state = random.getstate()
random.seed(time.time())
reserved_vram_random_state = random.getstate()
random.setstate(initial_random_state)

def get_gpu_memory_info():
    """获取GPU显存信息，如果没有GPU则返回模拟数据"""
    if not gpu_available:
        fake_total = 8.0  # GB
        fake_used = 2.0   # GB
        print("[ReservedVRAM]使用模拟GPU数据")
        return fake_total, fake_used

    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        total = memory_info.total / (1024 * 1024 * 1024)  # 转换为GB
        used = memory_info.used / (1024 * 1024 * 1024)    # 转换为GB
        return total, used
    except Exception as e:
        print(f"[ReservedVRAM]获取GPU信息出错，使用模拟数据: {e}")
        return 8.0, 2.0

def new_random_seed():
    """生成一个新的随机种子"""
    global reserved_vram_random_state
    prev_random_state = random.getstate()
    random.setstate(reserved_vram_random_state)
    seed = random.randint(1, 1125899906842624)
    reserved_vram_random_state = random.getstate()
    random.setstate(prev_random_state)
    return seed

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
                "reserved": ("FLOAT", {
                    "default": 0.6,
                    "min": -2.0,
                    "step": 0.1,
                    "display": "reserved (GB)"
                }),
                "mode": (["manual", "auto"], {
                    "default": "auto",
                    "display": "Mode"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": -1,
                    "max": 1125899906842624
                }),
                "auto_max_reserved": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "step": 0.1,
                    "display": "Auto Max Reserved (GB, 0=no limit)"
                }),
                "clean_gpu_before": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "anything": (any_type, {})
            },
            "hidden": {"unique_id": "UNIQUE_ID", "extra_pnginfo": "EXTRA_PNGINFO"}
        }

    RETURN_TYPES = (any_type, "INT", "FLOAT")
    RETURN_NAMES = ("output", "SEED", "Reserved(GB)")
    OUTPUT_NODE = True
    FUNCTION = "set_vram"
    CATEGORY = "VRAM"

    @classmethod
    def IS_CHANGED(cls, seed=0, **kwargs):
        """当使用特殊种子值时强制更新"""
        if seed == -1:
            return new_random_seed()
        return seed

    def cleanGPUUsedForce(self):
        """强制清理GPU显存，如果没有GPU则跳过"""
        if gpu_available:
            gc.collect()
            model_management.unload_all_models()
            model_management.soft_empty_cache()
            print("[ReservedVRAM]GPU显存清理完成")
        else:
            print("[ReservedVRAM]无GPU环境，跳过显存清理")

    def set_vram(self, reserved, mode="auto", seed=0, auto_max_reserved=0.0, clean_gpu_before=True, anything=None, unique_id=None, extra_pnginfo=None):
        # 前置清理
        if clean_gpu_before:
            print("[ReservedVRAM]执行前置GPU显存清理...")
            self.cleanGPUUsedForce()

        final_reserved_vram = 0.0
        
        # 统一的VRAM设置逻辑
        def set_extra_vram(gb_value):
            """设置EXTRA_RESERVED_VRAM的辅助函数"""
            if gpu_available:
                model_management.EXTRA_RESERVED_VRAM = int(gb_value * 1024 * 1024 * 1024)
            else:
                print("[ReservedVRAM]无GPU环境，跳过实际VRAM设置")

        if mode == "auto":
            total, used = get_gpu_memory_info()
            if total is not None and used is not None:
                auto_reserved = max(0, used + reserved)  # 确保不小于0
                
                # 应用最大限制
                if auto_max_reserved > 0:
                    auto_reserved = min(auto_reserved, auto_max_reserved)
                
                gpu_status = "模拟数据" if not gpu_available else "实际GPU"
                limit_info = f", 最大限制值{auto_max_reserved:.2f}GB" if auto_max_reserved > 0 else ""
                print(f'[ReservedVRAM]set EXTRA_RESERVED_VRAM={auto_reserved:.2f}GB (自动模式: {gpu_status}总显存={total:.2f}GB, 已用={used:.2f}GB{limit_info})')
                
                set_extra_vram(auto_reserved)
                final_reserved_vram = round(auto_reserved, 2)
            else:
                # 备用方案：使用手动值
                set_extra_vram(reserved)
                print(f'[ReservedVRAM]set EXTRA_RESERVED_VRAM={reserved}GB (自动模式失败，使用手动值)')
                final_reserved_vram = round(reserved, 2)
        else:
            # 手动模式
            manual_reserved = max(0, reserved)
            set_extra_vram(manual_reserved)
            print(f'[ReservedVRAM]set EXTRA_RESERVED_VRAM={manual_reserved}GB (手动模式)')
            final_reserved_vram = round(manual_reserved, 2)

        from comfy_execution.graph import ExecutionBlocker
        output_value = anything if anything is not None else ExecutionBlocker(None)

        return (output_value, seed, final_reserved_vram)

NODE_CLASS_MAPPINGS = {
    "ReservedVRAMSetter": ReservedVRAMSetter
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "ReservedVRAMSetter": "Set Reserved VRAM(GB) ⚙️"
}


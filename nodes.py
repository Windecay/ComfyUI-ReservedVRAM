from typing import Any as any_type
from comfy import model_management
import random
import time
import gc
# 尝试导入pynvml库，如果没有安装则提供相应提示
try:
    import pynvml
    try:
        pynvml.nvmlInit()
        pynvml_installed = True
    except Exception as e:
        pynvml_installed = False
        pynvml = None
        print("[ReservedVRAM]警告：pynvml可导入但NVML初始化失败，auto选项将不可用。")
        print(f"[ReservedVRAM]NVML初始化失败: {e}")
except ImportError:
    pynvml_installed = False
    pynvml = None
    print("[ReservedVRAM]警告：未安装pynvml库，auto选项将不可用。")

# 初始化随机状态
initial_random_state = random.getstate()
random.seed(time.time())
reserved_vram_random_state = random.getstate()
random.setstate(initial_random_state)

def get_gpu_memory_info():
    """获取GPU显存信息"""
    if pynvml_installed and pynvml is not None:
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            total = memory_info.total / (1024 * 1024 * 1024)
            used = memory_info.used / (1024 * 1024 * 1024)
            return total, used
        except Exception as e:
            print(f"[ReservedVRAM]获取GPU信息出错(NVML): {e}")

    try:
        import torch

        if (
            hasattr(torch, "cuda")
            and torch.cuda.is_available()
            and hasattr(torch.cuda, "mem_get_info")
        ):
            free, total = torch.cuda.mem_get_info()
            total_gb = total / (1024 * 1024 * 1024)
            used_gb = (total - free) / (1024 * 1024 * 1024)
            return total_gb, used_gb
    except Exception as e:
        print(f"[ReservedVRAM]获取GPU信息出错(torch): {e}")

    return None, None

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
        """强制清理GPU显存"""
        gc.collect()
        model_management.unload_all_models()
        model_management.soft_empty_cache()

    def set_vram(self, reserved, mode="auto", seed=0, auto_max_reserved=0.0, clean_gpu_before=True, anything=None, unique_id=None, extra_pnginfo=None):
        # 如果启用了前置清理显存，则执行清理操作
        if clean_gpu_before:
            print("[ReservedVRAM]执行前置GPU显存清理...")
            self.cleanGPUUsedForce()
            print("[ReservedVRAM]GPU显存清理完成")

        final_reserved_vram = 0.0

        if mode == "auto":
            total, used = get_gpu_memory_info()
            if total is not None and used is not None:
                auto_reserved = used + reserved
                auto_reserved = max(0, auto_reserved)
                if auto_max_reserved > 0:
                    auto_reserved = min(auto_reserved, auto_max_reserved)
                    print(f'[ReservedVRAM]set EXTRA_RESERVED_VRAM={auto_reserved:.2f}GB (自动模式: 总显存={total:.2f}GB, 已用={used:.2f}GB, 最大限制值{auto_max_reserved:.2f}GB)')
                else:
                    print(f'[ReservedVRAM]set EXTRA_RESERVED_VRAM={auto_reserved:.2f}GB (自动模式: 总显存={total:.2f}GB, 已用={used:.2f}GB)')
                model_management.EXTRA_RESERVED_VRAM = int(auto_reserved * 1024 * 1024 * 1024)
                final_reserved_vram = round(auto_reserved, 2)
            else:
                manual_reserved = max(0, reserved)
                model_management.EXTRA_RESERVED_VRAM = int(manual_reserved * 1024 * 1024 * 1024)
                print(f'[ReservedVRAM]set EXTRA_RESERVED_VRAM={manual_reserved}GB (自动模式不可用，使用手动值)')
                final_reserved_vram = round(manual_reserved, 2)
        else:
            # 手动模式
            reserved = max(0, reserved)
            model_management.EXTRA_RESERVED_VRAM = int(reserved * 1024 * 1024 * 1024)
            print(f'[ReservedVRAM]set EXTRA_RESERVED_VRAM={reserved}GB (手动模式)，忽略最大限制值')
            final_reserved_vram = round(reserved, 2)

        from comfy_execution.graph import ExecutionBlocker
        output_value = anything if anything is not None else ExecutionBlocker(None)

        return (output_value, seed, final_reserved_vram)

NODE_CLASS_MAPPINGS = {
    "ReservedVRAMSetter": ReservedVRAMSetter
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "ReservedVRAMSetter": "Set Reserved VRAM(GB) ⚙️"
}

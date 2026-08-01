# 06 — P3 RTX 4070 SUPER与ComfyUI

GPU用于faster-whisper CUDA、ComfyUI图片、2–4秒B-roll、Real-ESRGAN和NVENC；扩散视频不是主成片依赖。

从预检发现ComfyUI进程、8188、路径、Python、custom_nodes和models，写COMFYUI_DISCOVERY。

只允许一个重任务：WHISPER_GPU、COMFY_IMAGE、COMFY_VIDEO或UPSCALE，使用数据库锁/文件锁，记录峰值显存、模型、workflow和回退。

模型写`models.approved.yaml`：来源、版本、许可证、大小、SHA、量化、显存、workflow和结果；新增总量≤30GB；未批准不下载/加载/装节点。

白名单workflow：cover_background、vertical_illustration、pig_style_asset、remove_background、upscale、short_broll_2s_low_vram。每个有输入Schema、输出、超时、VRAM、fallback和哈希。

OOM：清缓存→降分辨率/帧→低显存→静态图→Remotion，最多两次。

Benchmark记录Whisper、1024图、2秒B-roll、放大、NVENC/CPU、显存、温度、大小。P3 gate要求CUDA/CPU、白名单、OOM回退、预算、角色一致和不并发。

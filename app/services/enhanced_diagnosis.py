"""增强的GPU环境诊断模块"""

import logging
from typing import Dict, Any, Tuple, List
from ..config import AiPlatformConfig

logger = logging.getLogger(__name__)

class EnhancedGpuDiagnosis:
    """增强的GPU诊断工具"""
    
    def __init__(self, ssh_manager):
        self.ssh_manager = ssh_manager
    
    def enhanced_gpu_diagnosis(self, server_config) -> Dict[str, Any]:
        """增强的GPU环境诊断"""
        diagnosis = {
            "gpu_available": False,
            "gpu_details": {},
            "pytorch_details": {},
            "cuda_details": {},
            "errors": [],
            "suggestions": [],
            "debug_info": []
        }
        
        try:
            # 1. 检查硬件GPU
            gpu_hardware_ok = self._check_gpu_hardware(server_config, diagnosis)
            
            # 2. 检查CUDA运行时
            cuda_runtime_ok = self._check_cuda_runtime(server_config, diagnosis)
            
            # 3. 检查Python环境
            python_envs = self._check_python_environments(server_config, diagnosis)
            
            # 4. 检查PyTorch CUDA支持
            pytorch_cuda_ok = self._check_pytorch_cuda(server_config, diagnosis, python_envs)
            
            # 5. 综合判断GPU可用性
            diagnosis["gpu_available"] = gpu_hardware_ok and pytorch_cuda_ok
            
            # 6. 生成诊断建议
            self._generate_suggestions(diagnosis, gpu_hardware_ok, cuda_runtime_ok, pytorch_cuda_ok)
            
        except Exception as e:
            logger.error(f"GPU诊断过程出错: {e}")
            diagnosis["errors"].append(f"诊断过程异常: {str(e)}")
        
        return diagnosis
    
    def _check_gpu_hardware(self, server_config, diagnosis: Dict[str, Any]) -> bool:
        """检查GPU硬件"""
        diagnosis["debug_info"].append("开始检查GPU硬件...")
        
        # 检查nvidia-smi
        exit_code, stdout, stderr = self.ssh_manager.execute_command(
            server_config, "nvidia-smi --query-gpu=index,name,driver_version,memory.total --format=csv,noheader", 
            timeout=15
        )
        
        if exit_code == 0 and stdout.strip():
            gpu_info = []
            for line in stdout.strip().split('\n'):
                if line.strip():
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 4:
                        gpu_info.append({
                            "index": parts[0],
                            "name": parts[1],
                            "driver_version": parts[2],
                            "memory_total": parts[3]
                        })
            
            diagnosis["gpu_details"]["hardware_gpus"] = gpu_info
            diagnosis["gpu_details"]["gpu_count"] = len(gpu_info)
            diagnosis["debug_info"].append(f"检测到 {len(gpu_info)} 个GPU设备")
            return True
        else:
            diagnosis["errors"].append("nvidia-smi不可用")
            diagnosis["debug_info"].append(f"nvidia-smi执行失败: exit_code={exit_code}, stderr={stderr}")
            return False
    
    def _check_cuda_runtime(self, server_config, diagnosis: Dict[str, Any]) -> bool:
        """检查CUDA运行时环境"""
        diagnosis["debug_info"].append("开始检查CUDA运行时...")
        
        # 检查CUDA版本
        exit_code, stdout, _ = self.ssh_manager.execute_command(
            server_config, "nvidia-smi | grep 'CUDA Version' | sed 's/.*CUDA Version: \\([0-9.]*\\).*/\\1/'", 
            timeout=10
        )
        
        if exit_code == 0 and stdout.strip():
            diagnosis["cuda_details"]["driver_cuda_version"] = stdout.strip()
            diagnosis["debug_info"].append(f"CUDA驱动版本: {stdout.strip()}")
        
        # 检查CUDA运行时库
        exit_code, stdout, _ = self.ssh_manager.execute_command(
            server_config, "ls /usr/local/cuda*/lib64/libcudart.so* 2>/dev/null | head -1", 
            timeout=5
        )
        
        if exit_code == 0 and stdout.strip():
            diagnosis["cuda_details"]["runtime_library"] = stdout.strip()
            diagnosis["debug_info"].append(f"CUDA运行时库: {stdout.strip()}")
            return True
        else:
            diagnosis["debug_info"].append("CUDA运行时库未找到")
            return False
    
    def _check_python_environments(self, server_config, diagnosis: Dict[str, Any]) -> List[str]:
        """检查Python环境"""
        diagnosis["debug_info"].append("开始检查Python环境...")
        
        python_envs = []
        
        for python_exe in ["python", "python3", "/usr/bin/python3", "/usr/local/bin/python3"]:
            exit_code, stdout, _ = self.ssh_manager.execute_command(
                server_config, f"which {python_exe} && {python_exe} --version", 
                timeout=5
            )
            
            if exit_code == 0:
                python_envs.append(python_exe)
                diagnosis["debug_info"].append(f"找到Python环境: {python_exe}")
        
        if not python_envs:
            diagnosis["errors"].append("未找到可用的Python环境")
        
        return python_envs
    
    def _check_pytorch_cuda(self, server_config, diagnosis: Dict[str, Any], python_envs: List[str]) -> bool:
        """检查PyTorch CUDA支持"""
        diagnosis["debug_info"].append("开始检查PyTorch CUDA支持...")
        
        pytorch_results = {}
        
        for python_exe in python_envs:
            result = self._test_pytorch_in_env(server_config, python_exe)
            pytorch_results[python_exe] = result
            
            if result["pytorch_installed"]:
                diagnosis["debug_info"].append(f"{python_exe}: PyTorch {result.get('version', 'unknown')}")
                
                if result["cuda_available"]:
                    diagnosis["debug_info"].append(f"{python_exe}: CUDA支持可用 (GPU数量: {result.get('gpu_count', 0)})")
                    diagnosis["pytorch_details"]["working_python"] = python_exe
                    diagnosis["pytorch_details"]["pytorch_version"] = result.get("version")
                    diagnosis["pytorch_details"]["cuda_version"] = result.get("cuda_version")
                    diagnosis["pytorch_details"]["gpu_count"] = result.get("gpu_count")
                    return True
                else:
                    diagnosis["debug_info"].append(f"{python_exe}: CUDA支持不可用")
            else:
                diagnosis["debug_info"].append(f"{python_exe}: PyTorch未安装")
        
        diagnosis["pytorch_details"]["all_environments"] = pytorch_results
        return False
    
    def _test_pytorch_in_env(self, server_config, python_exe: str) -> Dict[str, Any]:
        """在指定Python环境中测试PyTorch"""
        result = {
            "pytorch_installed": False,
            "cuda_available": False,
            "version": None,
            "cuda_version": None,
            "gpu_count": 0,
            "error": None
        }
        
        # 测试PyTorch安装和CUDA支持
        test_cmd = f"""
{python_exe} -c "
import torch
print(f'PYTORCH_VERSION={{torch.__version__}}')
print(f'CUDA_AVAILABLE={{torch.cuda.is_available()}}')
print(f'CUDA_VERSION={{torch.version.cuda if torch.version.cuda else \"None\"}}')
print(f'GPU_COUNT={{torch.cuda.device_count()}}')
" 2>/dev/null
        """.strip()
        
        exit_code, stdout, stderr = self.ssh_manager.execute_command(
            server_config, test_cmd, timeout=20
        )
        
        if exit_code == 0 and stdout:
            result["pytorch_installed"] = True
            
            for line in stdout.strip().split('\n'):
                if 'PYTORCH_VERSION=' in line:
                    result["version"] = line.split('=')[1]
                elif 'CUDA_AVAILABLE=' in line:
                    result["cuda_available"] = 'True' in line
                elif 'CUDA_VERSION=' in line:
                    cuda_ver = line.split('=')[1]
                    result["cuda_version"] = cuda_ver if cuda_ver != "None" else None
                elif 'GPU_COUNT=' in line:
                    try:
                        result["gpu_count"] = int(line.split('=')[1])
                    except ValueError:
                        result["gpu_count"] = 0
        else:
            result["error"] = stderr if stderr else "导入失败"
        
        return result
    
    def _generate_suggestions(self, diagnosis: Dict[str, Any], gpu_hardware_ok: bool, 
                            cuda_runtime_ok: bool, pytorch_cuda_ok: bool):
        """生成诊断建议"""
        if not gpu_hardware_ok:
            diagnosis["suggestions"].extend([
                "检查NVIDIA驱动是否正确安装",
                "运行 'nvidia-smi' 确认GPU硬件可访问",
                "可能需要重启服务器或重新加载驱动模块"
            ])
        
        if gpu_hardware_ok and not cuda_runtime_ok:
            diagnosis["suggestions"].extend([
                "安装CUDA Toolkit",
                "确保CUDA运行时库路径正确",
                "检查LD_LIBRARY_PATH环境变量"
            ])
        
        if gpu_hardware_ok and not pytorch_cuda_ok:
            pytorch_details = diagnosis.get("pytorch_details", {})
            all_envs = pytorch_details.get("all_environments", {})
            
            has_pytorch_cpu = any(env["pytorch_installed"] and not env["cuda_available"] 
                                for env in all_envs.values())
            
            if has_pytorch_cpu:
                diagnosis["suggestions"].extend([
                    "当前安装的是CPU版本的PyTorch",
                    "卸载CPU版本: pip uninstall torch torchvision torchaudio",
                    "安装GPU版本: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                ])
            else:
                diagnosis["suggestions"].extend([
                    "安装支持CUDA的PyTorch",
                    "运行: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                ])
        
        if diagnosis["gpu_available"]:
            working_python = diagnosis.get("pytorch_details", {}).get("working_python")
            if working_python:
                diagnosis["suggestions"].append(f"GPU环境正常，建议使用 {working_python} 运行VLLM") 
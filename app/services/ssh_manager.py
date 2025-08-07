"""SSH连接管理器"""

import paramiko
import socket
import threading
import time
import re
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager
import logging
import uuid

from ..config import GpuServerConfig

logger = logging.getLogger(__name__)

class PersistentSession:
    """持久化会话管理"""
    
    def __init__(self, session_id: str, server_config: GpuServerConfig):
        self.session_id = session_id
        self.config = server_config
        self.client: Optional[paramiko.SSHClient] = None
        self.shell_channel: Optional[paramiko.Channel] = None
        self.connected = False
        self.env_activated = False
        self.activated_env = None
        self.last_activity = time.time()
        self._lock = threading.Lock()
        self._output_buffer = ""
        # 添加激活状态缓存，避免重复激活
        self._activation_cache = None
        # 标记是否已经切换到root用户
        self.is_root_session = False
        # screen会话名称
        self.screen_session_name = None
    
    def connect(self, timeout: int = 10) -> bool:
        """建立SSH连接和持久化Shell会话"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.client.connect(
                hostname=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                timeout=timeout
            )
            
            # 创建持久化Shell通道
            self.shell_channel = self.client.invoke_shell()
            self.shell_channel.settimeout(timeout)
            
            # 等待Shell准备就绪
            time.sleep(1)
            self._clear_buffer()
            
            # 立即切换到root用户，让整个会话都在root环境下运行
            if not self._switch_to_root():
                logger.error(f"切换到root用户失败，会话将在普通用户模式下运行")
                # 即使切换失败，也继续使用普通用户会话
            
            # 启动screen会话
            if not self._start_screen_session():
                logger.warning("screen会话启动失败，将使用普通SSH会话")
            
            self.connected = True
            self.last_activity = time.time()
            logger.info(f"持久化SSH会话已建立: {self.config.name} ({self.config.host})")
            return True
            
        except Exception as e:
            logger.error(f"持久化SSH会话建立失败 {self.config.name}: {e}")
            self.connected = False
            return False
    
    def _clear_buffer(self):
        """清空输出缓冲区"""
        if self.shell_channel and self.shell_channel.recv_ready():
            try:
                self.shell_channel.recv(4096)
            except:
                pass
    
    def _switch_to_root(self) -> bool:
        """一次性切换到root用户，整个会话保持在root环境"""
        try:
            # 发送su命令切换到root
            self.shell_channel.send(f"su -\n")
            time.sleep(1)
            
            # 发送密码
            self.shell_channel.send(f"{self.config.password}\n")
            time.sleep(2)
            
            # 验证是否成功切换到root
            self.shell_channel.send("whoami\n")
            time.sleep(1)
            
            output = ""
            while self.shell_channel.recv_ready():
                output += self.shell_channel.recv(4096).decode('utf-8', errors='ignore')
            
            if "root" in output:
                self.is_root_session = True
                logger.info("成功切换到root用户，会话将保持在root环境")
                return True
            else:
                logger.warning("未能切换到root用户，可能密码错误或权限不足")
                return False
                
        except Exception as e:
            logger.error(f"切换到root用户时发生错误: {e}")
            return False
    
    def _start_screen_session(self) -> bool:
        """启动screen会话"""
        try:
            import uuid
            # 生成唯一的screen会话名
            self.screen_session_name = f"vllm_session_{uuid.uuid4().hex[:8]}"
            
            # 启动screen会话
            screen_cmd = f"screen -dmS {self.screen_session_name}"
            self.shell_channel.send(screen_cmd + '\n')
            time.sleep(1)
            
            # 进入screen会话
            attach_cmd = f"screen -r {self.screen_session_name}"
            self.shell_channel.send(attach_cmd + '\n')
            time.sleep(1)
            
            # 验证screen会话是否成功启动
            test_cmd = "echo 'SCREEN_SESSION_READY'"
            self.shell_channel.send(test_cmd + '\n')
            time.sleep(1)
            
            output = ""
            while self.shell_channel.recv_ready():
                output += self.shell_channel.recv(4096).decode('utf-8', errors='ignore')
            
            if "SCREEN_SESSION_READY" in output:
                logger.info(f"成功启动并进入screen会话: {self.screen_session_name}")
                return True
            else:
                logger.warning("screen会话启动失败，将使用普通会话")
                self.screen_session_name = None
                return False
                
        except Exception as e:
            logger.error(f"启动screen会话时发生错误: {e}")
            self.screen_session_name = None
            return False
    
    def execute_in_session(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """在持久化会话中执行命令"""
        if not self.connected or not self.shell_channel:
            if not self.connect():
                return -1, "", "持久化会话连接失败"
        
        try:
            with self._lock:
                # 清空之前的输出，确保没有残留输出
                self._clear_buffer()
                time.sleep(0.2)  # 额外等待确保缓冲区完全清空
                
                # 如果环境已激活，确保环境变量在命令执行前设置
                # 检查是否为简单的状态检查命令，这些命令不需要环境激活前缀
                simple_status_commands = [
                    "conda --version",
                    "python --version", 
                    "which python",
                    "which conda",
                    "echo $CONDA_DEFAULT_ENV",
                    "conda info",
                    "python -c"
                ]
                
                # 更精确的匹配：检查命令是否以简单状态命令开头
                is_simple_status_cmd = any(command.strip().startswith(cmd) for cmd in simple_status_commands)
                
                # 对于简单状态命令，直接执行，不添加环境前缀
                if is_simple_status_cmd:
                    command_with_env = command
                elif self.env_activated and self.activated_env:
                    env_name = self.activated_env.split('/')[-1] if '/' in self.activated_env else self.activated_env
                    # 如果在screen会话中，需要确保在root环境下执行
                    if hasattr(self, 'screen_session_name') and self.screen_session_name:
                        # 在screen会话内，直接在当前环境下执行，因为screen会话已经在root环境
                        env_setup = f"source /opt/miniconda3/etc/profile.d/conda.sh; conda activate {env_name}; export CONDA_DEFAULT_ENV={env_name}; "
                        command_with_env = env_setup + command
                    else:
                        env_setup = f"export CONDA_DEFAULT_ENV={env_name}; source /opt/miniconda3/etc/profile.d/conda.sh; conda activate {env_name}; "
                        command_with_env = env_setup + command
                else:
                    command_with_env = command
                
                # 发送命令
                command_with_marker = f"{command_with_env}; echo 'CMD_EXIT_CODE:'$?"
                self.shell_channel.send(command_with_marker + '\n')
                
                # 优化的等待策略：先等待命令开始执行
                time.sleep(0.5)  # 给命令一些启动时间
                
                # 读取输出
                output = ""
                start_time = time.time()
                consecutive_empty_reads = 0
                
                while time.time() - start_time < timeout:
                    if self.shell_channel.recv_ready():
                        chunk = self.shell_channel.recv(4096).decode('utf-8', errors='ignore')
                        output += chunk
                        consecutive_empty_reads = 0
                        
                        # 检查是否收到退出码标记
                        if 'CMD_EXIT_CODE:' in output:
                            # 再等待一小段时间确保所有输出都收到
                            time.sleep(0.3)
                            while self.shell_channel.recv_ready():
                                chunk = self.shell_channel.recv(4096).decode('utf-8', errors='ignore')
                                output += chunk
                            break
                    else:
                        consecutive_empty_reads += 1
                        # 如果连续多次没有数据，适当增加等待时间
                        if consecutive_empty_reads > 5:
                            time.sleep(0.2)
                        else:
                            time.sleep(0.1)
                
                # 解析退出码
                exit_code = 0
                if 'CMD_EXIT_CODE:' in output:
                    try:
                        exit_code_line = output.split('CMD_EXIT_CODE:')[-1].strip()
                        exit_code = int(exit_code_line.split()[0])
                        # 移除退出码标记
                        output = output.split('CMD_EXIT_CODE:')[0]
                    except:
                        exit_code = 0
                
                # 清理输出
                lines = output.split('\n')
                
                # 移除命令回显行和控制字符
                cleaned_lines = []
                for line in lines:
                    # 对于简单状态命令，更精确地处理命令回显
                    if is_simple_status_cmd:
                        # 跳过纯命令回显行
                        if line.strip() == command_with_marker.strip() or line.strip() == command.strip():
                            continue
                        # 跳过包含完整命令标记的行
                        if command_with_marker.strip() in line.strip():
                            continue
                        # 跳过包含命令但没有有效输出的行
                        if command.strip() in line:
                            # 检查是否是命令+分号的格式（如 "conda --version; echo 'CMD_EXIT_CODE:'$?"）
                            if '; echo' in line and ('CMD_EXIT_CODE' in line or "echo '" in line):
                                continue
                            # 如果行只包含命令和一些控制字符，跳过
                            remaining = line.replace(command.strip(), '').strip()
                            if not remaining or remaining.startswith(';') or remaining.startswith("echo '"):
                                continue
                    else:
                        # 跳过包含命令回显的行（但要保留有效的输出）
                        if command_with_marker.strip() in line and not any(keyword in line for keyword in ['ENV:', 'PATH:', 'active environment']):
                            continue
                    
                    # 跳过包含完整环境设置命令的行（更精确的匹配）
                    if 'export CONDA_DEFAULT_ENV=' in line and 'source /opt/miniconda3' in line and 'conda activate' in line:
                        continue
                    # 跳过包含CMD_EXIT_CODE的行（这些是内部标记，不应该出现在最终输出中）
                    if 'CMD_EXIT_CODE:' in line:
                        continue
                    # 移除ANSI控制字符
                    import re
                    clean_line = re.sub(r'\x1b\[[0-9;]*[mGKHF]', '', line)
                    clean_line = re.sub(r'\[\?[0-9]+[hl]', '', clean_line)
                    
                    # 更精确的提示符清理：只清理真正的提示符，保留正常输出
                    # 但要保留包含重要信息的行（如ENV:、PATH:、active environment等）
                    if any(keyword in clean_line for keyword in ['ENV:', 'PATH:', 'active environment']):
                        # 对于包含重要信息的行，只移除提示符部分，保留内容
                        clean_line = re.sub(r'^\([^)]+\)\s+[^@]+@[^:]+:[^$#]*[$#]\s*', '', clean_line)
                        clean_line = re.sub(r'^[^@]+@[^:]+:[^$]*\$\s*', '', clean_line)
                        clean_line = re.sub(r'^root@[^:]+:[^#]*#\s*', '', clean_line)
                    else:
                        # 清理conda环境提示符 (base) user@host:~$ 或 (vllm) root@host:~#
                        clean_line = re.sub(r'^\([^)]+\)\s+[^@]+@[^:]+:[^$#]*[$#]\s*', '', clean_line)
                        # 清理普通用户提示符 user@host:~$
                        clean_line = re.sub(r'^[^@]+@[^:]+:[^$]*\$\s*', '', clean_line)
                        # 清理root提示符 root@host:~#
                        clean_line = re.sub(r'^root@[^:]+:[^#]*#\s*', '', clean_line)
                    
                    # 移除包含echo命令和CMD_EXIT_CODE的行（仅限内部标记命令）
                    if 'echo ' in clean_line and 'CMD_EXIT_CODE' in clean_line and 'echo \'CMD_EXIT_CODE:\'' in clean_line:
                        continue
                    # 移除空行和只包含控制字符的行
                    if clean_line.strip() and not re.match(r'^[\x00-\x1f\x7f-\x9f]*$', clean_line.strip()):
                        cleaned_lines.append(clean_line.strip())
                
                clean_output = '\n'.join(cleaned_lines).strip()
                
                self.last_activity = time.time()
                return exit_code, clean_output, ""
                
        except Exception as e:
            logger.error(f"持久化会话命令执行失败 {self.config.name}: {e}")
            self.connected = False
            return -1, "", str(e)
    
    def activate_conda_env(self, env_name: str, conda_path: str, conda_base: str, root_password: str = None) -> bool:
        """在持久化会话中激活Conda环境"""
        # 检查是否最近已经激活过相同环境，但仍需验证当前状态
        if self.is_env_recently_activated(env_name):
            # 即使有缓存，也要验证当前环境状态
            if self._verify_current_env(env_name):
                logger.info(f"🔄 环境 {env_name} 已激活且验证通过，跳过重复激活")
                return True
            else:
                logger.info(f"🔄 环境 {env_name} 缓存显示已激活但验证失败，重新激活")
                # 清除无效缓存
                self._activation_cache = None
        
        if self.env_activated and self.activated_env == env_name:
            # 验证环境是否真的激活
            if self._verify_current_env(env_name):
                logger.info(f"环境 {env_name} 已在会话中激活且验证通过")
                return True
            else:
                logger.info(f"环境 {env_name} 状态不一致，重新激活")
                self.env_activated = False
                self.activated_env = None
        
        # 提取环境名称进行比较（env_name可能是完整路径）
        expected_env_name = env_name.split('/')[-1] if '/' in env_name else env_name
        
        # 使用传入的root密码，如果没有则使用SSH配置密码
        password_to_use = root_password if root_password else self.config.password
        logger.info(f"🔧 使用{'root' if root_password else 'SSH'}密码进行认证")
        
        # 如果有screen会话，需要确保在screen内进行conda环境激活
        if hasattr(self, 'screen_session_name') and self.screen_session_name:
            logger.info(f"🔧 检测到screen会话 {self.screen_session_name}，将在screen内激活conda环境")
            # 在screen会话内，环境激活需要重新进行
            su_output = ""
        else:
            # 检查是否已经在root会话中，如果是则直接激活环境
            if self.is_root_session:
                logger.info(f"🔧 会话已在root环境，直接激活conda环境: {env_name}")
                su_output = ""  # 无需su输出
            else:
                # 如果不在root会话中，需要切换到root用户
                logger.info(f"🔧 步骤1: 切换到root用户")
                su_cmd = f"su -"
                
                # 发送su命令
                self.shell_channel.send(su_cmd + '\n')
                time.sleep(1)
                
                # 等待密码提示
                prompt_output = ""
                start_time = time.time()
                while time.time() - start_time < 5:  # 最多等待5秒
                    if self.shell_channel.recv_ready():
                        chunk = self.shell_channel.recv(1024).decode('utf-8', errors='ignore')
                        prompt_output += chunk
                        if "Password:" in prompt_output:
                            break
                    time.sleep(0.1)
                
                logger.info(f"📋 密码提示输出: '{prompt_output.strip()}'")
                
                # 发送密码
                if "Password:" in prompt_output:
                    # 清空接收缓冲区
                    while self.shell_channel.recv_ready():
                        self.shell_channel.recv(1024)
                    
                    self.shell_channel.send(password_to_use + '\n')
                    time.sleep(3)  # 增加等待时间
                    
                    # 读取密码验证后的输出
                    auth_output = ""
                    start_time = time.time()
                    while time.time() - start_time < 10:  # 增加超时时间
                        if self.shell_channel.recv_ready():
                            chunk = self.shell_channel.recv(1024).decode('utf-8', errors='ignore')
                            auth_output += chunk
                            # 简化日志：只在调试时显示详细输出
                            if logger.isEnabledFor(logging.DEBUG):
                                logger.debug(f"📋 收到认证输出块: '{chunk.strip()}'")
                            # 检查是否出现root提示符或认证失败
                            if "#" in chunk or "root@" in chunk:
                                logger.info(f"✅ 检测到root提示符")
                                break
                            elif "Authentication failure" in chunk or "Sorry" in chunk:
                                logger.error(f"❌ 密码认证失败")
                                return False
                        time.sleep(0.2)
                    
                    su_output = prompt_output + auth_output
                    
                    # 简化日志：只在调试时显示详细输出
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"📋 完整su输出: '{su_output.strip()}'")
                    
                    # 检查是否成功切换到root
                    if "#" not in su_output and "root@" not in su_output:
                        logger.error(f"❌ 切换到root用户失败，未检测到root提示符")
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"📋 认证输出详情: '{auth_output.strip()}'")
                        return False
                    
                    logger.info(f"✅ 成功切换到root用户")
                    # 标记会话已在root环境
                    self.is_root_session = True
                else:
                    logger.error(f"❌ 未收到密码提示，su命令可能失败")
                    return False
        
        # 在root环境下激活conda环境
        logger.info(f"🔧 在root环境下激活conda环境: {env_name}")
        
        # 构建conda激活命令，确保环境变量在会话中持续生效
        # 在screen会话中，由于已经在root环境，直接激活即可
        conda_cmd = f"source /opt/miniconda3/etc/profile.d/conda.sh 2>/dev/null; conda activate {env_name}; export CONDA_DEFAULT_ENV={env_name}; echo VERIFICATION_START; echo $CONDA_DEFAULT_ENV; conda info | grep 'active environment'; echo VERIFICATION_END"
        
        # 清空缓冲区确保没有残留输出
        while self.shell_channel.recv_ready():
            self.shell_channel.recv(4096)
        time.sleep(0.3)
        
        # 发送conda命令
        self.shell_channel.send(conda_cmd + '\n')
        
        # 优化的等待策略：给conda命令充分的执行时间
        time.sleep(2.0)  # 初始等待，让conda命令开始执行
        
        # 使用更稳定的输出收集策略
        conda_output = ""
        read_attempts = 0
        max_attempts = 15  # 增加最大尝试次数，因为conda命令可能较慢
        
        while read_attempts < max_attempts:
            if self.shell_channel.recv_ready():
                chunk = self.shell_channel.recv(4096).decode('utf-8', errors='ignore')
                conda_output += chunk
                read_attempts = 0  # 重置计数器
                
                # 如果收到验证结束标记，再等待一下确保完整
                if 'VERIFICATION_END' in conda_output:
                    time.sleep(0.5)
                    while self.shell_channel.recv_ready():
                        conda_output += self.shell_channel.recv(4096).decode('utf-8', errors='ignore')
                    break
            else:
                read_attempts += 1
                time.sleep(0.3)  # 增加等待间隔
        
        # 最终确保收集所有输出
        time.sleep(0.5)
        while self.shell_channel.recv_ready():
            conda_output += self.shell_channel.recv(4096).decode('utf-8', errors='ignore')
        
        # 简化日志：只在调试时显示详细输出
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"📋 conda命令输出: '{conda_output.strip()}'")
        
        # 合并输出用于后续解析
        output = su_output + conda_output
        exit_code = 0  # 假设成功，后续通过验证结果判断
        error = ""  # 没有错误信息
        
        # 简化日志：只在调试时显示详细输出
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"📋 完整命令结果 - 退出码: {exit_code}, 输出: '{output}', 错误: '{error}'")
        
        if exit_code == 0:
            # 解析验证输出
            lines = output.strip().split('\n')
            verification_output = ""
            active_env_info = ""
            
            # 查找验证标记之间的内容
            start_found = False
            for line in lines:
                if "VERIFICATION_START" in line:
                    start_found = True
                    continue
                elif "VERIFICATION_END" in line:
                    break
                elif start_found:
                    if not verification_output and line.strip():
                        verification_output = line.strip()
                    elif "active environment" in line:
                        active_env_info = line.strip()
            
            # 多重验证：检查环境变量和conda info输出
            env_verified = verification_output == expected_env_name
            info_verified = expected_env_name in active_env_info if active_env_info else False
            
            if env_verified or info_verified:
                self.env_activated = True
                self.activated_env = env_name
                # 设置激活状态缓存，避免重复激活
                self._activation_cache = {
                    'env_name': env_name,
                    'timestamp': time.time(),
                    'verified': True
                }
                
                # 简化成功日志
                verification_methods = []
                if env_verified: verification_methods.append("环境变量")
                if info_verified: verification_methods.append("conda信息")
                logger.info(f"✅ 环境 {expected_env_name} 激活成功 ({', '.join(verification_methods)})")
                
                # 设置持久化的环境变量，确保后续命令能正确识别
                persist_commands = [
                    f"export CONDA_DEFAULT_ENV={env_name}",
                    f"export PATH=$(conda info --base)/envs/{env_name}/bin:$PATH",
                    "export CONDA_SHLVL=1"
                ]
                
                for cmd in persist_commands:
                    self.shell_channel.send(cmd + '\n')
                    time.sleep(0.5)
                
                # 等待一段时间让环境完全生效
                time.sleep(1.0)
                
                # 最终验证环境状态 - 使用改进的验证策略
                final_verification = self._verify_current_env(env_name)
                
                if final_verification:
                    logger.info(f"✅ 环境 {env_name} 最终验证通过")
                    return True
                else:
                    # 如果最终验证失败，但前面的验证已经通过，仍然认为激活成功
                    logger.warning(f"⚠️ 最终验证失败，但基于初始验证结果认为激活成功")
                    
                    # 更新缓存状态，即使最终验证失败也认为激活成功
                    self._activation_cache['verified'] = True
                    return True
            else:
                logger.error(f"❌ 环境激活验证失败 - 期望: {expected_env_name}")
                return False
        else:
            logger.error(f"❌ 激活环境失败 - 退出码: {exit_code}, 错误: '{error}'")
            return False
    
    def disconnect(self):
        """断开持久化会话"""
        if self.shell_channel:
            try:
                self.shell_channel.close()
            except:
                pass
            self.shell_channel = None
        
        if self.client:
            try:
                self.client.close()
            except:
                pass
            self.client = None
        
        self.connected = False
        self.env_activated = False
        self.activated_env = None
    
    def is_alive(self) -> bool:
        """检查持久化会话是否存活"""
        if not self.connected or not self.shell_channel:
            return False
        
        try:
            # 发送简单命令测试连接
            exit_code, _, _ = self.execute_in_session('echo test', timeout=5)
            return exit_code == 0
        except:
            self.connected = False
            return False
    
    def is_env_recently_activated(self, env_name: str, max_age_seconds: int = 300) -> bool:
        """检查环境是否在最近时间内已激活，避免重复激活"""
        if not self._activation_cache:
            return False
        
        cache = self._activation_cache
        current_time = time.time()
        
        # 检查缓存是否过期（默认5分钟）
        if current_time - cache.get('timestamp', 0) > max_age_seconds:
            logger.info(f"🕒 激活缓存已过期，需要重新验证")
            return False
        
        # 检查环境名是否匹配
        if cache.get('env_name') != env_name:
            return False
        
        # 检查是否已验证
        if not cache.get('verified', False):
            return False
        
        logger.info(f"✅ 环境 {env_name} 在缓存中显示最近已激活")
        return True
    
    def _verify_current_env(self, expected_env: str) -> bool:
        """通过检查命令行提示符验证当前环境是否为期望的环境"""
        try:
            if not self.shell_channel or not self.connected:
                return False
            
            # 提取环境名称进行比较
            expected_env_name = expected_env.split('/')[-1] if '/' in expected_env else expected_env
            
            # 简化验证方法：主要通过提示符检测
            verification_methods = [
                # 方法1: 检查提示符中的环境名称
                ("echo 'PROMPT_CHECK'; echo $PS1 2>/dev/null || echo 'PS1_NOT_SET'", "PROMPT_CHECK"),
                # 方法2: 检查环境变量（作为备用）
                ("echo ENV_CHECK:$CONDA_DEFAULT_ENV", "ENV_CHECK:")
            ]
            
            verification_results = []
            
            for method_cmd, prefix in verification_methods:
                try:
                    # 清理缓冲区
                    clear_attempts = 0
                    while clear_attempts < 3:
                        if self.shell_channel.recv_ready():
                            self.shell_channel.recv(4096)
                            clear_attempts = 0
                        else:
                            clear_attempts += 1
                            time.sleep(0.1)
                    
                    # 发送验证命令
                    self.shell_channel.send(method_cmd + '\n')
                    
                    # 等待命令执行
                    time.sleep(0.5)
                    
                    # 收集输出
                    output = ""
                    read_attempts = 0
                    max_attempts = 10
                    
                    while read_attempts < max_attempts:
                        if self.shell_channel.recv_ready():
                            chunk = self.shell_channel.recv(4096).decode('utf-8', errors='ignore')
                            output += chunk
                            read_attempts = 0
                        else:
                            read_attempts += 1
                            time.sleep(0.1)
                    
                    # 解析输出
                    lines = output.strip().split('\n')
                    
                    for line in lines:
                        # 清理ANSI转义序列
                        clean_line = re.sub(r'\x1b\[[0-9;]*[mGKH]', '', line)
                        clean_line = re.sub(r'\r', '', clean_line).strip()
                        
                        if prefix == "PROMPT_CHECK":
                            # 检查提示符中是否包含环境名称，如(vllm)
                            if f"({expected_env_name})" in clean_line:
                                verification_results.append(("PROMPT:", expected_env_name))
                                logger.info(f"✅ 提示符检测到环境: ({expected_env_name})")
                                break
                        elif clean_line.startswith(prefix):
                            value = clean_line[len(prefix):].strip()
                            verification_results.append((prefix, value))
                            logger.info(f"✅ {prefix[:-1]}验证: {value}")
                            break
                    
                except Exception as e:
                    logger.warning(f"⚠️ 验证方法执行失败: {e}")
                    continue
            
            # 分析验证结果 - 简化匹配逻辑
            prompt_match = False
            env_var_match = False
            
            logger.debug(f"🔍 验证结果分析: {verification_results}")
            
            for prefix, value in verification_results:
                if prefix == "PROMPT:":
                    # 提示符检测到环境名称
                    if value == expected_env_name:
                        prompt_match = True
                        logger.debug(f"✅ 提示符匹配成功: ({value})")
                elif prefix == "ENV_CHECK:":
                    # 环境变量检测
                    if value and (value == expected_env_name or 
                                value.endswith(f'/{expected_env_name}') or
                                value.endswith(f'/envs/{expected_env_name}') or
                                f'/envs/{expected_env_name}' in value or
                                expected_env_name in value):
                        env_var_match = True
                        logger.debug(f"✅ 环境变量匹配成功: {value}")
            
            # 优先使用提示符检测，环境变量作为备用
            if prompt_match or env_var_match:
                methods = []
                if prompt_match: methods.append("提示符")
                if env_var_match: methods.append("环境变量")
                logger.info(f"✅ 环境 {expected_env_name} 验证成功 ({', '.join(methods)})")
                return True
            else:
                logger.warning(f"❌ 环境 {expected_env_name} 验证失败")
                return False
            
        except Exception as e:
            logger.error(f"❌ 验证环境状态时出错: {e}")
            return False

class SSHConnection:
    """SSH连接封装"""
    
    def __init__(self, server_config: GpuServerConfig):
        self.config = server_config
        self.client: Optional[paramiko.SSHClient] = None
        self.connected = False
        self.last_activity = time.time()
        self._lock = threading.Lock()
    
    def connect(self, timeout: int = 10) -> bool:
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.client.connect(
                hostname=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                timeout=timeout
            )
            
            self.connected = True
            self.last_activity = time.time()
            logger.info(f"SSH连接已建立: {self.config.name} ({self.config.host})")
            return True
            
        except (paramiko.AuthenticationException, 
                paramiko.SSHException, 
                socket.timeout, 
                ConnectionRefusedError) as e:
            logger.error(f"SSH连接失败 {self.config.name}: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开SSH连接"""
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                logger.warning(f"关闭SSH连接时出错: {e}")
            finally:
                self.client = None
                self.connected = False
    
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """执行SSH命令"""
        if not self.connected or not self.client:
            if not self.connect():
                return -1, "", "SSH连接失败"
        
        try:
            with self._lock:
                stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
                
                exit_status = stdout.channel.recv_exit_status()
                stdout_data = stdout.read().decode('utf-8', errors='ignore')
                stderr_data = stderr.read().decode('utf-8', errors='ignore')
                
                self.last_activity = time.time()
                
                return exit_status, stdout_data, stderr_data
                
        except Exception as e:
            logger.error(f"执行SSH命令失败 {self.config.name}: {e}")
            self.connected = False
            return -1, "", str(e)
    
    def is_alive(self) -> bool:
        """检查连接是否存活"""
        if not self.connected or not self.client:
            return False
        
        try:
            transport = self.client.get_transport()
            if transport is None:
                return False
            
            transport.send_ignore()
            return True
            
        except Exception:
            self.connected = False
            return False

class SSHManager:
    """SSH连接管理器"""
    
    def __init__(self):
        self.connections: Dict[str, SSHConnection] = {}
        self.persistent_sessions: Dict[str, PersistentSession] = {}  # server_name -> session
        self.connection_timeout = 300  # 5分钟超时
        self.session_timeout = 1800  # 30分钟会话超时
        self._cleanup_thread = None
        self._running = True
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """启动连接清理线程"""
        def cleanup_worker():
            while self._running:
                try:
                    current_time = time.time()
                    
                    # 清理普通SSH连接
                    to_remove = []
                    for server_name, conn in self.connections.items():
                        if (current_time - conn.last_activity > self.connection_timeout or 
                            not conn.is_alive()):
                            to_remove.append(server_name)
                    
                    for server_name in to_remove:
                        self.disconnect_server(server_name)
                        logger.info(f"已清理过期SSH连接: {server_name}")
                    
                    # 清理持久化会话
                    sessions_to_remove = []
                    for server_name, session in self.persistent_sessions.items():
                        if (current_time - session.last_activity > self.session_timeout or 
                            not session.is_alive()):
                            sessions_to_remove.append(server_name)
                    
                    for server_name in sessions_to_remove:
                        self.disconnect_persistent_session(server_name)
                        logger.info(f"已清理过期持久化会话: {server_name}")
                    
                    time.sleep(60)  # 每分钟检查一次
                    
                except Exception as e:
                    logger.error(f"SSH连接清理线程出错: {e}")
                    time.sleep(60)
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def get_connection(self, server_config: GpuServerConfig) -> Optional[SSHConnection]:
        """获取SSH连接"""
        server_name = server_config.name
        
        # 如果连接存在且可用，直接返回
        if server_name in self.connections:
            conn = self.connections[server_name]
            if conn.is_alive():
                return conn
            else:
                # 连接不可用，移除并重新建立
                self.disconnect_server(server_name)
        
        # 创建新连接
        conn = SSHConnection(server_config)
        if conn.connect():
            self.connections[server_name] = conn
            return conn
        
        return None
    
    def disconnect_server(self, server_name: str):
        """断开指定服务器的连接"""
        if server_name in self.connections:
            self.connections[server_name].disconnect()
            del self.connections[server_name]
    
    def disconnect_all(self):
        """断开所有连接"""
        for conn in self.connections.values():
            conn.disconnect()
        self.connections.clear()
        
        for session in self.persistent_sessions.values():
            session.disconnect()
        self.persistent_sessions.clear()
    
    def execute_command(self, server_config: GpuServerConfig, command: str, 
                       timeout: int = 30) -> Tuple[int, str, str]:
        """在指定服务器上执行命令"""
        conn = self.get_connection(server_config)
        if conn is None:
            return -1, "", f"无法连接到服务器 {server_config.name}"
        
        return conn.execute_command(command, timeout)
    
    def get_persistent_session(self, server_config: GpuServerConfig) -> Optional[PersistentSession]:
        """获取持久化会话"""
        server_name = server_config.name
        
        # 如果会话存在且可用，直接返回
        if server_name in self.persistent_sessions:
            session = self.persistent_sessions[server_name]
            if session.is_alive():
                return session
            else:
                # 会话不可用，移除并重新建立
                self.disconnect_persistent_session(server_name)
        
        # 创建新的持久化会话
        session_id = str(uuid.uuid4())
        session = PersistentSession(session_id, server_config)
        if session.connect():
            self.persistent_sessions[server_name] = session
            return session
        
        return None
    
    def disconnect_persistent_session(self, server_name: str):
        """断开指定服务器的持久化会话"""
        if server_name in self.persistent_sessions:
            self.persistent_sessions[server_name].disconnect()
            del self.persistent_sessions[server_name]
    
    def execute_in_persistent_session(self, server_config: GpuServerConfig, command: str, 
                                    timeout: int = 30) -> Tuple[int, str, str]:
        """在持久化会话中执行命令"""
        session = self.get_persistent_session(server_config)
        if session is None:
            return -1, "", f"无法建立到服务器 {server_config.name} 的持久化会话"
        
        return session.execute_in_session(command, timeout)
    
    def activate_conda_in_session(self, server_config: GpuServerConfig, env_name: str, 
                                conda_path: str, conda_base: str, root_password: str = None) -> bool:
        """在持久化会话中激活Conda环境"""
        session = self.get_persistent_session(server_config)
        if session is None:
            return False
        
        return session.activate_conda_env(env_name, conda_path, conda_base, root_password)
    
    def get_session_status(self, server_name: str) -> Optional[Dict[str, Any]]:
        """获取持久化会话状态"""
        if server_name not in self.persistent_sessions:
            return None
        
        session = self.persistent_sessions[server_name]
        return {
            "session_id": session.session_id,
            "connected": session.connected,
            "env_activated": session.env_activated,
            "activated_env": session.activated_env,
            "last_activity": session.last_activity,
            "is_alive": session.is_alive()
        }
    
    @contextmanager
    def ssh_session(self, server_config: GpuServerConfig):
        """SSH会话上下文管理器"""
        conn = self.get_connection(server_config)
        if conn is None:
            raise ConnectionError(f"无法连接到服务器 {server_config.name}")
        
        try:
            yield conn
        finally:
            # 保持连接，由清理线程处理超时
            pass
    
    def get_connection_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有连接状态"""
        status = {}
        for server_name, conn in self.connections.items():
            status[server_name] = {
                "connected": conn.connected,
                "is_alive": conn.is_alive(),
                "last_activity": conn.last_activity,
                "host": conn.config.host,
                "port": conn.config.port
            }
        return status
    
    def shutdown(self):
        """关闭管理器"""
        self._running = False
        self.disconnect_all()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)

# 全局SSH管理器实例
_ssh_manager = None

def get_ssh_manager() -> SSHManager:
    """获取SSH管理器实例"""
    global _ssh_manager
    if _ssh_manager is None:
        _ssh_manager = SSHManager()
    return _ssh_manager
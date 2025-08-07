"""页面模块初始化文件"""

from .system_monitor import system_monitor_page
from .dashboard import dashboard_page
from .developer_tools import developer_tools_page
from .terminal import terminal_page
from .vllm_management_page import vllm_management_page

__all__ = [
    'system_monitor_page',
    'dashboard_page', 
    'developer_tools_page',
    'terminal_page',
    'vllm_management_page'
] 
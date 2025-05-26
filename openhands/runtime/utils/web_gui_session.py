import os
import subprocess
import logging
import signal
import time
import threading
from typing import Optional, Dict, Any
from pathlib import Path

from openhands.core.logger import openhands_logger as logger


class GuiSessionStatus:
    """GUI会话状态枚举"""
    STOPPED = 'stopped'
    STARTING = 'starting'
    RUNNING = 'running'
    STOPPING = 'stopping'
    ERROR = 'error'


class WebGuiSession:
    """Web GUI会话管理器
    
    参考BashSession的设计模式，提供GUI扩展的同步启动和关闭功能。
    所有操作都在GUI_HOME环境变量指定的目录中进行。
    """
    
    # GUI服务默认端口
    VNC_PORT = 5900
    NOVNC_PORT = 6080
    DISPLAY_NUM = 1
    
    # GUI服务进程名称映射
    SERVICE_PROCESSES = {
        'xvfb': 'Xvfb',
        'x11vnc': 'x11vnc',
        'novnc': 'novnc_proxy',
        'mutter': 'mutter',
        'tint2': 'tint2'
    }
    
    def __init__(
        self,
        gui_home: str = '',
        display_num: int = 1,
        width: int = 1024,
        height: int = 768,
        vnc_port: int = 5900,
        novnc_port: int = 6080,
    ):
        """初始化GUI会话管理器
        
        Args:
            gui_home: GUI主目录，默认从环境变量GUI_HOME读取
            display_num: X11显示编号
            width: 屏幕宽度
            height: 屏幕高度
            vnc_port: VNC服务端口
            novnc_port: noVNC Web端口
        """
        self.gui_home = gui_home or os.environ.get('GUI_HOME', '/home/openhands')
        self.display_num = display_num
        self.width = width
        self.height = height
        self.vnc_port = vnc_port
        self.novnc_port = novnc_port
        
        # 设置环境变量
        self.env_vars = {
            'DISPLAY': f':{self.display_num}',
            'DISPLAY_NUM': str(self.display_num),
            'WIDTH': str(self.width),
            'HEIGHT': str(self.height),
            'GUI_HOME': self.gui_home,
        }
        
        # 会话状态
        self.status = GuiSessionStatus.STOPPED
        self.processes: Dict[str, subprocess.Popen] = {}
        self._initialized = False
        self._closed = False
        
        # 锁用于线程安全
        self.lock = threading.Lock()
        
        logger.debug(f'GuiSession initialized with GUI_HOME: {self.gui_home}')

    @property
    def initialized(self) -> bool:
        """检查会话是否已初始化"""
        return self._initialized

    @property
    def is_running(self) -> bool:
        """检查GUI服务是否正在运行"""
        return self.status == GuiSessionStatus.RUNNING

    def _get_script_path(self, script_name: str) -> str:
        """获取GUI扩展脚本的完整路径"""
        return os.path.join(self.gui_home, script_name)

    def _run_script(self, script_name: str, check_output: bool = True) -> Optional[str]:
        """运行GUI扩展脚本
        
        Args:
            script_name: 脚本名称
            check_output: 是否检查输出
            
        Returns:
            脚本输出（如果check_output为True）
        """
        script_path = self._get_script_path(script_name)
        
        if not os.path.exists(script_path):
            raise FileNotFoundError(f'GUI script not found: {script_path}')
        
        if not os.access(script_path, os.X_OK):
            raise PermissionError(f'GUI script not executable: {script_path}')
        
        logger.debug(f'Running GUI script: {script_path}')
        
        try:
            # 创建完整的环境变量
            env = os.environ.copy()
            env.update(self.env_vars)
            
            if check_output:
                result = subprocess.run(
                    [script_path],
                    cwd=self.gui_home,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                output = result.stdout.strip()
                logger.debug(f'Script {script_name} output: {output}')
                return output
            else:
                # 不等待输出，在后台启动
                subprocess.Popen(
                    [script_path],
                    cwd=self.gui_home,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return None
                
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            logger.error(f'Script {script_name} failed with code {e.returncode}: {error_msg}')
            raise RuntimeError(f'Script {script_name} execution failed: {error_msg}')
        except Exception as e:
            logger.error(f'Error running script {script_name}: {e}')
            raise

    def _check_service_running(self, service_name: str) -> bool:
        """检查特定服务是否正在运行"""
        process_name = self.SERVICE_PROCESSES.get(service_name)
        if not process_name:
            return False
        
        try:
            # 使用pgrep检查进程
            result = subprocess.run(
                ['pgrep', '-f', process_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except Exception:
            return False

    def _wait_for_service(self, service_name: str, timeout: int = 30) -> bool:
        """等待服务启动"""
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            if self._check_service_running(service_name):
                logger.debug(f'Service {service_name} is now running')
                return True
            time.sleep(0.5)
        
        logger.warning(f'Service {service_name} failed to start within {timeout} seconds')
        return False

    def _check_port_listening(self, port: int) -> bool:
        """检查端口是否在监听"""
        try:
            result = subprocess.run(
                ['netstat', '-tuln'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout
                return f':{port}' in output
            return False
        except Exception:
            return False

    def start(self) -> bool:
        """启动GUI扩展服务
        
        Returns:
            启动是否成功
        """
        with self.lock:
            if self.status == GuiSessionStatus.RUNNING:
                logger.info('GUI services are already running')
                return True
            
            if self.status == GuiSessionStatus.STARTING:
                logger.info('GUI services are already starting')
                return False
            
            try:
                self.status = GuiSessionStatus.STARTING
                logger.info('Starting GUI extension services...')
                
                # 检查GUI_HOME目录是否存在
                if not os.path.exists(self.gui_home):
                    raise FileNotFoundError(f'GUI_HOME directory not found: {self.gui_home}')
                
                # 启动核心GUI服务（Xvfb, VNC, 窗口管理器等）
                logger.debug('Starting core GUI services')
                self._run_script('start_all.sh', check_output=False)
                
                # 等待核心服务启动
                services_to_check = ['xvfb', 'x11vnc', 'mutter', 'tint2']
                for service in services_to_check:
                    if not self._wait_for_service(service, timeout=15):
                        raise RuntimeError(f'Failed to start {service} service')
                
                # 启动noVNC Web服务
                logger.debug('Starting noVNC web service')
                self._run_script('novnc_startup.sh', check_output=False)
                
                # 等待noVNC端口可用
                if not self._wait_for_port(self.novnc_port, timeout=10):
                    raise RuntimeError(f'noVNC web service failed to start on port {self.novnc_port}')
                
                self.status = GuiSessionStatus.RUNNING
                self._initialized = True
                
                logger.info(f'GUI extension services started successfully')
                logger.info(f'VNC server: localhost:{self.vnc_port}')
                logger.info(f'Web interface: http://localhost:{self.novnc_port}')
                
                return True
                
            except Exception as e:
                self.status = GuiSessionStatus.ERROR
                logger.error(f'Failed to start GUI services: {e}')
                
                # 尝试清理已启动的服务
                self._force_stop_services()
                return False

    def _wait_for_port(self, port: int, timeout: int = 30) -> bool:
        """等待端口开始监听"""
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            if self._check_port_listening(port):
                logger.debug(f'Port {port} is now listening')
                return True
            time.sleep(0.5)
        
        logger.warning(f'Port {port} failed to start listening within {timeout} seconds')
        return False

    def stop(self, force: bool = False) -> bool:
        """停止GUI扩展服务
        
        Args:
            force: 是否强制停止
            
        Returns:
            停止是否成功
        """
        with self.lock:
            if self.status == GuiSessionStatus.STOPPED:
                logger.info('GUI services are already stopped')
                return True
            
            if self.status == GuiSessionStatus.STOPPING:
                logger.info('GUI services are already stopping')
                return False
            
            try:
                self.status = GuiSessionStatus.STOPPING
                logger.info('Stopping GUI extension services...')
                
                if force:
                    # 强制停止
                    self._force_stop_services()
                else:
                    # 优雅停止
                    self._graceful_stop_services()
                
                self.status = GuiSessionStatus.STOPPED
                self._initialized = False
                
                logger.info('GUI extension services stopped successfully')
                return True
                
            except Exception as e:
                self.status = GuiSessionStatus.ERROR
                logger.error(f'Failed to stop GUI services: {e}')
                return False

    def _graceful_stop_services(self) -> None:
        """优雅地停止GUI服务"""
        try:
            # 使用close_all.sh脚本优雅停止
            if os.path.exists(self._get_script_path('close_all.sh')):
                logger.debug('Using close_all.sh for graceful shutdown')
                self._run_script('close_all.sh', check_output=False)
                
                # 等待服务停止
                time.sleep(3)
                
                # 验证服务是否已停止
                still_running = []
                for service in self.SERVICE_PROCESSES.keys():
                    if self._check_service_running(service):
                        still_running.append(service)
                
                if still_running:
                    logger.warning(f'Some services still running: {still_running}')
                    self._force_stop_services()
            else:
                # 如果没有close_all.sh脚本，则强制停止
                self._force_stop_services()
                
        except Exception as e:
            logger.error(f'Error during graceful shutdown: {e}')
            self._force_stop_services()

    def _force_stop_services(self) -> None:
        """强制停止GUI服务"""
        try:
            # 使用force_stop.sh脚本强制停止
            if os.path.exists(self._get_script_path('force_stop.sh')):
                logger.debug('Using force_stop.sh for forced shutdown')
                self._run_script('force_stop.sh', check_output=False)
            else:
                # 手动强制停止各个服务
                logger.debug('Manually force stopping GUI services')
                for service, process_name in self.SERVICE_PROCESSES.items():
                    self._kill_process(process_name)
                
                # 清理锁文件
                self._cleanup_lock_files()
                
        except Exception as e:
            logger.error(f'Error during forced shutdown: {e}')

    def _kill_process(self, process_pattern: str) -> None:
        """杀死匹配模式的进程"""
        try:
            # 使用pkill强制杀死进程
            subprocess.run(
                ['pkill', '-9', '-f', process_pattern],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.debug(f'Force killed processes matching: {process_pattern}')
        except Exception:
            pass  # 忽略错误，因为进程可能已经不存在

    def _cleanup_lock_files(self) -> None:
        """清理锁文件和临时文件"""
        try:
            # 清理X11锁文件
            lock_file = f'/tmp/.X{self.display_num}-lock'
            if os.path.exists(lock_file):
                os.remove(lock_file)
                logger.debug(f'Removed lock file: {lock_file}')
            
            # 清理临时日志文件
            temp_files = [
                '/tmp/x11vnc_stderr.log',
                '/tmp/mutter_stderr.log', 
                '/tmp/tint2_stderr.log',
                '/tmp/novnc.log'
            ]
            
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f'Removed temp file: {temp_file}')
                    
        except Exception as e:
            logger.warning(f'Error cleaning up lock files: {e}')

    def restart(self) -> bool:
        """重启GUI扩展服务
        
        Returns:
            重启是否成功
        """
        logger.info('Restarting GUI extension services...')
        
        # 先停止服务
        stop_success = self.stop(force=True)
        if not stop_success:
            logger.error('Failed to stop GUI services for restart')
            return False
        
        # 等待一下确保完全停止
        time.sleep(2)
        
        # 再启动服务
        start_success = self.start()
        if start_success:
            logger.info('GUI extension services restarted successfully')
        else:
            logger.error('Failed to restart GUI services')
        
        return start_success

    def get_status(self) -> Dict[str, Any]:
        """获取GUI服务状态信息
        
        Returns:
            包含状态信息的字典
        """
        status_info = {
            'status': self.status,
            'initialized': self._initialized,
            'gui_home': self.gui_home,
            'display': self.env_vars['DISPLAY'],
            'ports': {
                'vnc': self.vnc_port,
                'novnc': self.novnc_port
            },
            'services': {}
        }
        
        # 检查各个服务的运行状态
        for service in self.SERVICE_PROCESSES.keys():
            status_info['services'][service] = self._check_service_running(service)
        
        # 检查端口状态
        status_info['ports']['vnc_listening'] = self._check_port_listening(self.vnc_port)
        status_info['ports']['novnc_listening'] = self._check_port_listening(self.novnc_port)
        
        return status_info

    def close(self) -> None:
        """关闭方法，用于清理资源"""
        if self._closed:
            return
        
        # 如果还在运行，先停止
        if self.status == GuiSessionStatus.RUNNING:
            try:
                self.stop(force=True)
            except Exception as e:
                logger.error(f'Error during close: {e}')
        
        self._closed = True
        logger.debug('GUI session closed')

    def __del__(self) -> None:
        """析构函数，确保资源被清理"""
        self.close()

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop(force=True)


# 便利函数
def start_gui_session(gui_home: Optional[str] = None, **kwargs) -> WebGuiSession:
    """启动GUI会话的便利函数
    
    Args:
        gui_home: GUI主目录
        **kwargs: 其他参数传递给WebGuiSession
        
    Returns:
        已启动的WebGuiSession实例
    """
    session = WebGuiSession(gui_home=gui_home, **kwargs)
    success = session.start()
    if not success:
        raise RuntimeError('Failed to start GUI session')
    return session


def stop_gui_session(session: WebGuiSession, force: bool = False) -> bool:
    """停止GUI会话的便利函数
    
    Args:
        session: GUI会话实例
        force: 是否强制停止
        
    Returns:
        停止是否成功
    """
    return session.stop(force=force)
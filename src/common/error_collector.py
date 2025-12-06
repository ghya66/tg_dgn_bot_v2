"""
错误收集器
用于收集和分析生产环境中的错误

改进：
- 启动时自动从文件加载历史错误
- 每次收集错误后异步写入文件（防止进程重启丢失数据）
- 使用线程池执行文件IO，避免阻塞主线程
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
import json
import traceback
import atexit

logger = logging.getLogger(__name__)


class ErrorCollector:
    """错误收集器 - 支持持久化存储"""

    def __init__(self, max_errors: int = 100, auto_save_interval: int = 60,
                 filename: str = "error_log.json", auto_load: bool = True):
        """
        初始化错误收集器

        Args:
            max_errors: 最大保存错误数
            auto_save_interval: 自动保存间隔（秒），默认60秒
            filename: 持久化文件名
            auto_load: 是否启动时自动加载历史数据
        """
        self.errors: List[Dict[str, Any]] = []
        self.max_errors = max_errors
        self.auto_save_interval = auto_save_interval
        self.error_counts = defaultdict(int)  # 错误类型计数
        self.last_save_time = datetime.now()
        self.filename = filename
        self._dirty = False  # 是否有未保存的更改
        self._lock = threading.Lock()  # 线程安全锁
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="error_collector")

        # 启动时自动加载历史数据
        if auto_load:
            self.load_from_file(filename)

        # 注册退出时保存
        atexit.register(self._save_on_exit)
        
    def _save_on_exit(self):
        """进程退出时同步保存数据"""
        if self._dirty:
            try:
                self._do_save_to_file(self.filename)
                logger.info("ErrorCollector: saved errors on exit")
            except Exception as e:
                logger.error(f"ErrorCollector: failed to save on exit: {e}")
        # 关闭线程池
        self._executor.shutdown(wait=False)

    def _async_save(self):
        """异步保存到文件（在后台线程中执行）"""
        if not self._dirty:
            return

        try:
            self._executor.submit(self._do_save_to_file, self.filename)
        except Exception as e:
            logger.warning(f"Failed to submit async save: {e}")

    def collect(self,
                error_type: str,
                message: str,
                context: Optional[Dict] = None,
                exception: Optional[Exception] = None) -> None:
        """
        收集错误

        Args:
            error_type: 错误类型
            message: 错误消息
            context: 上下文信息
            exception: 异常对象
        """
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": message,
            "context": context or {}
        }

        # 如果有异常对象，记录堆栈
        if exception:
            error_info["traceback"] = traceback.format_exc()
            error_info["exception_class"] = type(exception).__name__

        with self._lock:
            # 添加到错误列表
            self.errors.append(error_info)

            # 更新错误计数
            self.error_counts[error_type] += 1

            # 限制错误数量
            if len(self.errors) > self.max_errors:
                self.errors = self.errors[-self.max_errors:]

            # 标记有未保存的更改
            self._dirty = True

        # 记录到日志
        logger.error(f"[{error_type}] {message}")

        # 检查是否需要自动保存（异步）
        if (datetime.now() - self.last_save_time).seconds > self.auto_save_interval:
            self._async_save()
            self.last_save_time = datetime.now()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取错误摘要
        
        Returns:
            错误摘要信息
        """
        if not self.errors:
            return {
                "total": 0,
                "types": {},
                "recent": [],
                "status": "healthy"
            }
        
        # 计算时间范围
        oldest_error = datetime.fromisoformat(self.errors[0]["timestamp"])
        newest_error = datetime.fromisoformat(self.errors[-1]["timestamp"])
        time_range = newest_error - oldest_error
        
        # 计算错误率
        error_rate = len(self.errors) / max(time_range.total_seconds() / 3600, 1)  # 每小时错误数
        
        # 判断健康状态
        if error_rate > 10:
            status = "critical"
        elif error_rate > 5:
            status = "warning"
        else:
            status = "normal"
        
        return {
            "total": len(self.errors),
            "types": dict(self.error_counts),
            "recent": self.errors[-10:],  # 最近10个错误
            "error_rate": round(error_rate, 2),
            "time_range": str(time_range),
            "status": status,
            "most_common": self._get_most_common_errors()
        }
    
    def _get_most_common_errors(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        获取最常见的错误
        
        Args:
            top_n: 返回前N个
            
        Returns:
            最常见错误列表
        """
        sorted_errors = sorted(
            self.error_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [
            {"type": error_type, "count": count}
            for error_type, count in sorted_errors[:top_n]
        ]
    
    def get_errors_by_type(self, error_type: str) -> List[Dict[str, Any]]:
        """
        获取特定类型的错误
        
        Args:
            error_type: 错误类型
            
        Returns:
            错误列表
        """
        return [
            error for error in self.errors
            if error["type"] == error_type
        ]
    
    def get_errors_in_timerange(self, 
                                hours: int = 1) -> List[Dict[str, Any]]:
        """
        获取指定时间范围内的错误
        
        Args:
            hours: 小时数
            
        Returns:
            错误列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            error for error in self.errors
            if datetime.fromisoformat(error["timestamp"]) > cutoff_time
        ]
    
    def clear_old_errors(self, days: int = 7) -> int:
        """
        清理旧错误
        
        Args:
            days: 保留天数
            
        Returns:
            清理的错误数
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        original_count = len(self.errors)
        
        self.errors = [
            error for error in self.errors
            if datetime.fromisoformat(error["timestamp"]) > cutoff_time
        ]
        
        removed_count = original_count - len(self.errors)
        if removed_count > 0:
            logger.info(f"Cleared {removed_count} old errors")
        
        return removed_count
    
    def _do_save_to_file(self, filename: str) -> bool:
        """
        实际执行文件保存（线程安全）

        Args:
            filename: 文件名

        Returns:
            是否成功
        """
        try:
            # 创建logs目录
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            # 复制数据（避免锁定太久）
            with self._lock:
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "error_counts": dict(self.error_counts),
                    "errors": list(self.errors)
                }
                self._dirty = False

            # 保存文件（不持有锁）
            filepath = log_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Errors saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save errors: {e}")
            with self._lock:
                self._dirty = True  # 保存失败，重新标记为脏
            return False

    def save_to_file(self, filename: Optional[str] = None) -> bool:
        """
        同步保存错误到文件

        Args:
            filename: 文件名（可选，默认使用实例的filename）

        Returns:
            是否成功
        """
        target_file = filename or self.filename
        result = self._do_save_to_file(target_file)
        if result:
            self.last_save_time = datetime.now()
        return result
    
    def load_from_file(self, filename: Optional[str] = None) -> bool:
        """
        从文件加载错误

        Args:
            filename: 文件名（可选，默认使用实例的filename）

        Returns:
            是否成功
        """
        try:
            target_file = filename or self.filename
            filepath = Path("logs") / target_file
            if not filepath.exists():
                logger.debug(f"Error log file not found: {filepath}")
                return False

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with self._lock:
                self.errors = data.get("errors", [])

                # 重建错误计数（优先使用文件中保存的计数）
                saved_counts = data.get("error_counts", {})
                self.error_counts.clear()
                if saved_counts:
                    for k, v in saved_counts.items():
                        self.error_counts[k] = v
                else:
                    # 兼容旧格式：从错误列表重建
                    for error in self.errors:
                        self.error_counts[error["type"]] += 1

                self._dirty = False

            logger.info(f"Loaded {len(self.errors)} errors from {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to load errors: {e}")
            return False


# 全局错误收集器实例
error_collector = ErrorCollector()


def collect_error(error_type: str, 
                 message: str, 
                 context: Optional[Dict] = None,
                 exception: Optional[Exception] = None) -> None:
    """
    便捷函数：收集错误到全局收集器
    
    Args:
        error_type: 错误类型
        message: 错误消息
        context: 上下文信息
        exception: 异常对象
    """
    error_collector.collect(error_type, message, context, exception)

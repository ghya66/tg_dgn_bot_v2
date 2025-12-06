"""
结构化日志配置模块

功能：
- 支持 JSON 格式化日志（生产环境）
- 支持人类可读格式（开发环境）
- 自动添加 trace_id 关联同一请求的日志
- 支持日志级别配置
"""

import logging
import json
import sys
import uuid
import contextvars
from datetime import datetime
from typing import Optional

# 上下文变量：存储当前请求的 trace_id
_trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'trace_id', default=None
)


def get_trace_id() -> Optional[str]:
    """获取当前请求的 trace_id"""
    return _trace_id_var.get()


def set_trace_id(trace_id: Optional[str] = None) -> str:
    """设置当前请求的 trace_id，如果未提供则自动生成"""
    if trace_id is None:
        trace_id = str(uuid.uuid4())[:8]  # 使用短 UUID
    _trace_id_var.set(trace_id)
    return trace_id


def clear_trace_id():
    """清除当前请求的 trace_id"""
    _trace_id_var.set(None)


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加 trace_id（如果存在）
        trace_id = get_trace_id()
        if trace_id:
            log_data["trace_id"] = trace_id
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class HumanReadableFormatter(logging.Formatter):
    """人类可读格式化器（带 trace_id）"""
    
    def format(self, record: logging.LogRecord) -> str:
        trace_id = get_trace_id()
        trace_prefix = f"[{trace_id}] " if trace_id else ""
        
        # 基础格式
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        base_msg = f"{timestamp} - {record.name} - {record.levelname} - {trace_prefix}{record.getMessage()}"
        
        # 添加异常信息
        if record.exc_info:
            base_msg += "\n" + self.formatException(record.exc_info)
        
        return base_msg


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[str] = None
):
    """
    配置日志系统
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: 是否使用 JSON 格式（生产环境推荐）
        log_file: 日志文件路径（可选）
    """
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 选择格式化器
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = HumanReadableFormatter()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if log_file:
        from pathlib import Path
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # 降低第三方库的日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    return root_logger


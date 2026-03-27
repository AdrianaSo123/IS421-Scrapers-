import logging
import logging.handlers
import os
import time
from functools import wraps
from typing import Callable, Any

# Configure standard file logging for the MCP server safely using absolute resolution
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
LOG_FILE = os.path.join(DATA_DIR, "mcp_server.log")

logger = logging.getLogger("mcp_server")
logger.setLevel(logging.INFO)

if not logger.handlers:
    rfh = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5*1024*1024, backupCount=2
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s'
    )
    rfh.setFormatter(formatter)
    logger.addHandler(rfh)

def mcp_tool_wrapper(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        tool_name = func.__name__
        logger.info(f"Triggered tool '{tool_name}' with kwargs: {kwargs}")
        
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            
            # Fix 11: Always unconditionally stamp observability metrics if dealing with a ToolResponse
            if hasattr(result, 'execution_time_ms'):
                setattr(result, 'execution_time_ms', duration)
            if hasattr(result, 'source'):
                setattr(result, 'source', tool_name)
                
            success = getattr(result, 'success', True)
            logger.info(f"Completed tool '{tool_name}' in {duration:.2f}ms | success={success}")
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"Failed tool '{tool_name}' in {duration:.2f}ms | error={str(e)}", exc_info=True)
            
            from .schema import ToolResponse
            # Fix 1: strict ToolResponse invariants where success=False enforces data=None
            return ToolResponse(
                success=False,
                data=None, 
                error="Internal server error occurred",
                execution_time_ms=duration,
                source=tool_name
            )

    return wrapper

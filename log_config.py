# log_config.py
from loguru import logger
import sys

# 配置日志
def setup_logger():
    logger.remove()  # 移除默认配置

    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> {message}",
        level="INFO",
        colorize=True
    )

    # 文件输出（所有日志写入同一个文件）
    logger.add(
        "running_log.log",
        format="{time:YYYY-MM-DD HH:mm:ss} {message}",
        level="INFO",
        rotation="10 MB",  # 按大小分割
        retention="30 days",  # 保留30天
        encoding="utf-8"
    )


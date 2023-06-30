#!/usr/bin/env python

# 导入必要的模块
import os
import sys

# 检查脚本是否作为主程序执行
if __name__ == '__main__':
    # 设置 Django 的配置文件路径
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'StockTrading.settings')

    try:
        # 尝试导入 Django 的管理模块
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # 如果导入失败，抛出 ImportError 异常
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # 使用命令行参数执行 Django 程序
    execute_from_command_line(sys.argv)
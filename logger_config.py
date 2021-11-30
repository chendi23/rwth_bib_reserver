# -*- coding: utf-8 -*-
"""
@Time : 2021/09/28 18:10 下午
@Auth : zcd_zhendeshuai
@File : logger_config.py
@IDE  : PyCharm

"""
import logging
import os

def get_logger(log_file):
    log_dir = os.path.split(log_file)[0]
    if not log_dir.strip():
        log_dir = os.getcwd()
        print(log_dir)
    elif not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logger = logging.getLogger(log_file)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

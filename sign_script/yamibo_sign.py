#!/usr/bin/env python3
"""
百合会论坛自动签到脚本
基于 YamiboReaderPro 项目的签到逻辑实现
"""

import os
import sys
import re
import time
import json
import logging
from datetime import datetime
from typing import Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 常量配置
BASE_URL = "https://bbs.yamibo.com"
SIGN_URL_TEMPLATE = "{}/plugin.php?id=zqlj_sign&sign={}"
FORMHASH_URLS = [
    "{}/home.php?mod=space&do=profile&mobile=2",
    "{}/home.php?mod=spacecp&ac=credit&mobile=2",
    "{}/plugin.php?id=zqlj_sign&mobile=2",
]

# User-Agent
UA = "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36"


class YamiboSignIn:
    """百合会论坛签到类"""

    def __init__(self, cookie: str):
        """
        初始化签到实例
        :param cookie: 百合会论坛的登录 Cookie 字符串
        """
        self.cookie = cookie
        self.session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 设置请求头
        self.session.headers.update({
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cookie": cookie,
            "Referer": BASE_URL,
        })

    def _extract_formhash(self, html: str) -> Optional[str]:
        """
        从 HTML 中提取 formhash
        :param html: 页面 HTML 内容
        :return: formhash 值或 None
        """
        # 尝试多种正则匹配模式
        patterns = [
            r'name="formhash"\s+value="([^"]+)"',
            r'formhash=([a-zA-Z0-9]{8})',
            r'formhash["\']?\s*[:=]\s*["\']?([a-zA-Z0-9]{8})',
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                formhash = match.group(1)
                logger.info(f"成功提取 formhash: {formhash}")
                return formhash

        logger.error("无法从 HTML 中提取 formhash")
        return None

    def _get_formhash(self) -> Tuple[bool, Optional[str]]:
        """
        获取 formhash，尝试多个 URL
        :return: (是否成功, formhash 值)
        """
        for url_template in FORMHASH_URLS:
            url = url_template.format(BASE_URL)
            logger.info(f"正在获取 formhash: {url}")

            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                # 检查是否已登录
                if "登录" in response.text and "用户名" in response.text:
                    logger.warning(f"{url} - Cookie 可能已失效或未登录")
                    continue

                formhash = self._extract_formhash(response.text)
                if formhash:
                    return True, formhash
                else:
                    logger.warning(f"{url} - 未找到 formhash，尝试下一个 URL")

            except requests.exceptions.RequestException as e:
                logger.warning(f"{url} - 网络错误: {e}")
                continue
            except Exception as e:
                logger.warning(f"{url} - 错误: {e}")
                continue

        logger.error("所有 URL 都无法获取 formhash")
        return False, None

    def _parse_sign_result(self, html: str) -> Tuple[bool, str]:
        """
        解析签到结果
        :param html: 签到响应 HTML
        :return: (是否成功, 结果消息)
        """
        # 已签到的情况
        if "已经打过卡了" in html or "今日已打卡" in html or "重复操作" in html:
            return True, "今日已打卡"

        # 签到成功的情况
        if "打卡成功" in html or "成功" in html or "获得了" in html:
            # 尝试提取奖励信息
            reward_match = re.search(r'获得了\s*([^<]+)', html)
            if reward_match:
                return True, f"签到成功，获得奖励: {reward_match.group(1).strip()}"
            return True, "签到成功"

        # 检查是否需要登录
        if "登录" in html and ("用户名" in html or "密码" in html):
            return False, "需要登录，Cookie 可能已失效"

        # 检查是否有错误信息
        error_match = re.search(r'<div[^>]*messagecontent[^>]*>(.*?)</div>', html, re.DOTALL)
        if error_match:
            error_msg = re.sub(r'<[^>]+>', '', error_match.group(1)).strip()
            return False, f"签到失败: {error_msg}"

        # 未知结果
        logger.warning(f"无法识别的响应内容，长度: {len(html)}")
        return False, "未知结果，请检查日志"

    def sign_in(self) -> Tuple[bool, str]:
        """
        执行签到
        :return: (是否成功, 结果消息)
        """
        logger.info("=" * 50)
        logger.info("开始执行百合会论坛签到")
        logger.info("=" * 50)

        # 1. 获取 formhash
        success, formhash = self._get_formhash()
        if not success or not formhash:
            return False, "获取 formhash 失败"

        # 2. 执行签到请求
        sign_url = SIGN_URL_TEMPLATE.format(BASE_URL, formhash)
        logger.info(f"正在发送签到请求: {sign_url}")

        try:
            response = self.session.get(sign_url, timeout=30)
            response.raise_for_status()

            # 3. 解析结果
            success, message = self._parse_sign_result(response.text)

            if success:
                logger.info(f"签到结果: {message}")
            else:
                logger.error(f"签到结果: {message}")

            return success, message

        except requests.exceptions.RequestException as e:
            logger.error(f"签到请求失败: {e}")
            return False, f"网络错误: {e}"
        except Exception as e:
            logger.error(f"签到时发生未知错误: {e}")
            return False, f"未知错误: {e}"

    def close(self):
        """关闭会话"""
        self.session.close()


def load_cookie_from_env() -> Optional[str]:
    """从环境变量加载 Cookie"""
    cookie = os.environ.get("YAMIBO_COOKIE")
    if cookie:
        logger.info("已从环境变量加载 Cookie")
        return cookie
    return None


def load_cookie_from_file(filepath: str) -> Optional[str]:
    """从文件加载 Cookie"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            cookie = f.read().strip()
            if cookie:
                logger.info(f"已从文件加载 Cookie: {filepath}")
                return cookie
    except FileNotFoundError:
        logger.error(f"Cookie 文件不存在: {filepath}")
    except Exception as e:
        logger.error(f"读取 Cookie 文件失败: {e}")
    return None


def main():
    """主函数"""
    # 获取 Cookie
    cookie = load_cookie_from_env()

    if not cookie:
        # 尝试从文件加载（用于本地测试）
        cookie_file = os.environ.get("COOKIE_FILE", "cookie.txt")
        cookie = load_cookie_from_file(cookie_file)

    if not cookie:
        logger.error("未找到 Cookie，请设置 YAMIBO_COOKIE 环境变量或创建 cookie.txt 文件")
        sys.exit(1)

    # 执行签到
    signer = YamiboSignIn(cookie)
    try:
        success, message = signer.sign_in()

        # 输出结果（用于 GitHub Actions）
        result = {
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

        # 设置 GitHub Actions 输出（使用环境文件）
        if os.environ.get("GITHUB_ACTIONS") == "true":
            # 使用 GITHUB_OUTPUT 环境文件
            github_output = os.environ.get("GITHUB_OUTPUT")
            if github_output:
                with open(github_output, "a") as f:
                    f.write(f"result={json.dumps(result)}\n")
            if success:
                print(f"::notice::签到成功 - {message}")
            else:
                print(f"::warning::签到失败 - {message}")

        # 退出码
        sys.exit(0 if success else 1)

    finally:
        signer.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Archive Bot 自动签到脚本

支持 EH-ArBot 和 Archive-at-Home 两种协议，支持多账号配置。
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

import requests
import yaml


# ==================== 日志配置 ====================

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ==================== 常量定义 ====================

DEFAULT_ADDRESSES = {
    "ehArBot": "https://eh-arc-api.mhdy.icu",
    "archiveAtHome": "https://api.archive-at-home.org/jhentai",
}

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "JHenTai-ArchiveBot-GitHubAction/1.0",
}


# ==================== 工具函数 ====================

def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    log.debug(f"配置文件加载成功: {config_path}")
    return config or {}


def check_balance_eh_ar_bot(api_address: str, api_key: str) -> Optional[int]:
    """查询 EH-ArBot 余额，返回 GP 或 None"""
    url = f"{api_address}/balance"
    log.info(f"[EH-ArBot] Checking balance...")
    try:
        resp = requests.post(url, headers=HEADERS, json={"apikey": api_key}, timeout=30)
        data = resp.json()
        if data.get("code") == 0:
            balance_data = data.get("data", {})
            gp = balance_data.get("GP") or balance_data.get("gp")
            log.info(f"[EH-ArBot] Balance: {gp} GP")
            return gp
        else:
            log.warning(f"[EH-ArBot] Balance check failed: code={data.get('code')}, msg={data.get('msg')}")
    except Exception as e:
        log.error(f"[EH-ArBot] Balance check exception: {e}")
    return None


def check_in_eh_ar_bot(api_address: str, api_key: str) -> bool:
    """EH-ArBot 签到"""
    url = f"{api_address}/checkin"
    log.info(f"[EH-ArBot] POST {url}")
    try:
        resp = requests.post(url, headers=HEADERS, json={"apikey": api_key}, timeout=30)
        data = resp.json()
        code = data.get("code")
        if code == 0:
            checkin_data = data.get("data", {})
            get_gp = checkin_data.get("get_GP") or "?"
            current_gp = checkin_data.get("current_GP") or "?"
            log.info(f"[EH-ArBot] Check-in success! Got {get_gp} GP, current {current_gp} GP")
            return True
        elif code == 7:
            log.warning(f"[EH-ArBot] Already checked in today.")
            return True
        else:
            log.error(f"[EH-ArBot] Check-in failed: code={code}, msg={data.get('msg')}")
    except Exception as e:
        log.error(f"[EH-ArBot] Check-in exception: {e}")
    return False


def check_balance_archive_at_home(api_address: str, api_key: str) -> Optional[int]:
    """查询 Archive-at-Home 余额，返回 GP 或 None"""
    url = f"{api_address}/api/v1/me/balance"
    log.info(f"[Archive-at-Home] Checking balance...")
    try:
        resp = requests.get(
            url,
            headers={
                **HEADERS,
                "Authorization": f"Bearer {api_key}",
                "X-Client": "app/jhentai",
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            gp = data.get("GP") or data.get("gp") or data.get("balance")
            log.info(f"[Archive-at-Home] Balance: {gp} GP")
            return gp
        else:
            log.warning(f"[Archive-at-Home] Balance check failed: status={resp.status_code}, body={resp.text}")
    except Exception as e:
        log.error(f"[Archive-at-Home] Balance check exception: {e}")
    return None


def check_in_archive_at_home(api_address: str, api_key: str) -> bool:
    """Archive-at-Home 签到"""
    url = f"{api_address}/api/v1/me/checkin"
    log.info(f"[Archive-at-Home] POST {url}")
    try:
        resp = requests.post(
            url,
            headers={
                **HEADERS,
                "Authorization": f"Bearer {api_key}",
                "X-Client": "app/jhentai",
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            reward = data.get("reward") or "?"
            balance = data.get("balance") or "?"
            log.info(f"[Archive-at-Home] Check-in success! Got {reward} GP, current {balance} GP")
            return True
        elif resp.status_code == 409:
            log.warning(f"[Archive-at-Home] Already checked in today.")
            return True
        else:
            log.error(f"[Archive-at-Home] Check-in failed: status={resp.status_code}, body={resp.text}")
    except Exception as e:
        log.error(f"[Archive-at-Home] Check-in exception: {e}")
    return False


def process_account(account_config: dict, index: int) -> bool:
    """处理单个账号签到"""
    bot_type = (account_config.get("bot_type") or account_config.get("type") or "ehArBot").strip()
    api_address = (account_config.get("api_address") or "").strip()
    api_key = (account_config.get("api_key") or account_config.get("apikey") or "").strip()

    if not api_key:
        log.warning(f"Account {index + 1} missing api_key, skipping.")
        return False

    if not api_address:
        api_address = DEFAULT_ADDRESSES.get(bot_type, DEFAULT_ADDRESSES["ehArBot"])

    api_address = api_address.rstrip("/")
    bot_type_lower = bot_type.lower()

    log.info(f"========== Account {index + 1} [{bot_type}] ==========")

    if bot_type_lower in ("eharbot", "eh_ar_bot"):
        check_balance_eh_ar_bot(api_address, api_key)
        return check_in_eh_ar_bot(api_address, api_key)
    elif bot_type_lower in ("archiveathome", "archive_at_home"):
        check_balance_archive_at_home(api_address, api_key)
        return check_in_archive_at_home(api_address, api_key)
    else:
        log.error(f"Account {index + 1} unknown bot_type: {bot_type}")
        return False


def main():
    config = load_config()
    archive_config = config.get("archive_bot")

    if not archive_config:
        log.warning("No 'archive_bot' config found in config.yaml. Skipping.")
        sys.exit(0)

    # 支持单账号 dict 或多账号 list
    accounts: list[dict] = []
    if isinstance(archive_config, list):
        accounts = archive_config
    elif isinstance(archive_config, dict):
        accounts = [archive_config]
    else:
        log.error("'archive_bot' config must be a dict or list of dicts.")
        sys.exit(1)

    if not accounts:
        log.warning("No archive bot accounts configured.")
        sys.exit(0)

    log.info(f"Starting Archive Bot daily check-in for {len(accounts)} account(s)...")

    all_success = True
    for i, account in enumerate(accounts):
        try:
            ok = process_account(account, i)
            if not ok:
                all_success = False
        except Exception as e:
            log.error(f"Account {i + 1} unexpected exception: {e}")
            all_success = False

    if all_success:
        log.info("All accounts checked in successfully.")
        sys.exit(0)
    else:
        log.error("Some accounts failed to check in.")
        sys.exit(1)


if __name__ == "__main__":
    main()

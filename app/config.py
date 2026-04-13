from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Set


def _parse_int_set(value: str | None) -> Set[int]:
    if not value:
        return set()
    result: Set[int] = set()
    for item in value.split(','):
        item = item.strip()
        if not item:
            continue
        result.add(int(item))
    return result


@dataclass(slots=True)
class Settings:
    telegram_bot_token: str
    google_sheet_id: str
    google_service_account_json: str
    admin_ids: Set[int]
    announce_chat_id: Optional[int]
    timezone: str = 'Asia/Ho_Chi_Minh'
    employee_sheet_name: str = '月度計算'
    settings_sheet_name: str = '設定總覽'
    ranking_sheet_name: str = '排行榜'
    binding_sheet_name: str = 'Telegram綁定'

    @classmethod
    def from_env(cls) -> 'Settings':
        token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
        sheet_id = os.getenv('GOOGLE_SHEET_ID', '').strip()
        service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '').strip()
        admin_ids = _parse_int_set(os.getenv('ADMIN_IDS'))
        announce_chat_id_raw = os.getenv('ANNOUNCE_CHAT_ID', '').strip()
        announce_chat_id = int(announce_chat_id_raw) if announce_chat_id_raw else None

        missing = []
        if not token:
            missing.append('TELEGRAM_BOT_TOKEN')
        if not sheet_id:
            missing.append('GOOGLE_SHEET_ID')
        if not service_account_json:
            missing.append('GOOGLE_SERVICE_ACCOUNT_JSON')
        if missing:
            raise RuntimeError(f'缺少必要環境變數: {", ".join(missing)}')

        return cls(
            telegram_bot_token=token,
            google_sheet_id=sheet_id,
            google_service_account_json=service_account_json,
            admin_ids=admin_ids,
            announce_chat_id=announce_chat_id,
        )

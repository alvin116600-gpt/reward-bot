from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

from .config import Settings
from .formatter import format_currency, format_percent

logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
]


@dataclass(slots=True)
class EmployeeRecord:
    name: str
    direct_count: float
    team_count: float
    direct_weight: float
    team_weight: float
    direct_ratio: float
    team_ratio: float
    direct_income: float
    team_income: float
    penalty: float
    violation_count: float
    actual_take_home: float
    company_recovery: float
    status: str
    rank: int


class RewardPenaltySheetService:
    def __init__(self, settings: Settings) -> None:
        creds_info = json.loads(settings.google_service_account_json)
        credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        client = gspread.authorize(credentials)
        self.settings = settings
        self.spreadsheet = client.open_by_key(settings.google_sheet_id)

    def _worksheet(self, title: str):
        return self.spreadsheet.worksheet(title)

    def get_employee_names(self) -> List[str]:
        ws = self._worksheet(self.settings.employee_sheet_name)
        names = ws.col_values(1)[1:]
        return [name.strip() for name in names if str(name).strip()]

    def get_employee_map(self) -> Dict[str, EmployeeRecord]:
        ws = self._worksheet(self.settings.employee_sheet_name)
        rows = ws.get('A2:Q200', value_render_option='UNFORMATTED_VALUE')
        records: Dict[str, EmployeeRecord] = {}
        for row in rows:
            padded = list(row) + [''] * (17 - len(row))
            name = str(padded[0]).strip()
            if not name:
                continue
            records[name] = EmployeeRecord(
                name=name,
                direct_count=_n(padded[1]),
                team_count=_n(padded[2]),
                direct_weight=_n(padded[3]),
                team_weight=_n(padded[4]),
                direct_ratio=_n(padded[5]),
                team_ratio=_n(padded[6]),
                direct_income=_n(padded[11]),
                team_income=_n(padded[12]),
                penalty=_n(padded[9]),
                violation_count=_n(padded[10]),
                actual_take_home=_n(padded[13]),
                company_recovery=_n(padded[14]),
                status=str(padded[15] or '').strip() or '正常',
                rank=int(_n(padded[16]) or 0),
            )
        return records

    def get_employee_record(self, employee_name: str) -> Optional[EmployeeRecord]:
        return self.get_employee_map().get(employee_name)

    def get_pool_update_text(self) -> str:
        ws = self._worksheet(self.settings.settings_sheet_name)
        data = ws.get('B7:B16', value_render_option='UNFORMATTED_VALUE')
        values = [row[0] if row else 0 for row in data]
        padded = values + [0] * (10 - len(values))

        return (
            '📊 今日獎池 / Quỹ thưởng hôm nay\n'
            '━━━━━━━━━━━━━━━━━━\n\n'
            '💰 直推獎池 / Quỹ trực tiếp\n\n'
            '本月獎池總金額\n'
            'Tổng quỹ tháng này\n'
            f'{format_currency(padded[0])}\n\n'
            '本月可發放總額\n'
            'Tổng số có thể phát tháng này\n'
            f'{format_currency(padded[1])}\n\n'
            '本日新增獎金\n'
            'Thưởng tăng thêm hôm nay\n'
            f'{format_currency(padded[6])}\n\n'
            '本日開放比例\n'
            'Tỷ lệ mở hôm nay\n'
            f'{format_percent(padded[7])}\n\n'
            '━━━━━━━━━━━━━━━━━━\n\n'
            '👥 團隊獎池 / Quỹ đội nhóm\n\n'
            '本月獎池總金額\n'
            'Tổng quỹ tháng này\n'
            f'{format_currency(padded[2])}\n\n'
            '本月可發放總額\n'
            'Tổng số có thể phát tháng này\n'
            f'{format_currency(padded[3])}\n\n'
            '本日新增獎金\n'
            'Thưởng tăng thêm hôm nay\n'
            f'{format_currency(padded[8])}\n\n'
            '本日開放比例\n'
            'Tỷ lệ mở hôm nay\n'
            f'{format_percent(padded[9])}'
        )

    def get_ranking_text(self, limit: int = 10) -> str:
        ws = self._worksheet(self.settings.ranking_sheet_name)
        rows = ws.get(f'A4:D{3 + limit}', value_render_option='UNFORMATTED_VALUE')
        lines = ['🏆 排行榜 / Bảng xếp hạng', '━━━━━━━━━━━━━━━━━━']
        found = False
        for row in rows:
            if len(row) < 4:
                continue
            rank, badge, name, amount = row[:4]
            if not str(name).strip():
                continue
            found = True
            label = str(badge).strip() or f'{int(_n(rank) or 0)}.'
            lines.append(f'{label} {name}\n{format_currency(amount)}')
        if not found:
            lines.append('目前沒有可顯示的排行資料。\nHiện chưa có dữ liệu xếp hạng để hiển thị.')
        return '\n\n'.join(lines)

    def get_bound_employee_name(self, telegram_user_id: int) -> Optional[str]:
        try:
            ws = self._worksheet(self.settings.binding_sheet_name)
        except WorksheetNotFound:
            return None

        rows = ws.get('A2:B500', value_render_option='UNFORMATTED_VALUE')
        for row in rows:
            if len(row) < 2:
                continue
            name = str(row[0]).strip()
            user_id = str(row[1]).strip()
            if not name or not user_id:
                continue
            if user_id == str(telegram_user_id):
                return name
        return None

    def format_weight_message(self, employee_name: str) -> str:
        record = self.get_employee_record(employee_name)
        if not record:
            return f'找不到員工：{employee_name}\nKhông tìm thấy nhân viên: {employee_name}'
        return (
            f'👤 {record.name}\n'
            '━━━━━━━━━━━━━━━━━━\n\n'
            '👥 直推人數\n'
            'Số người trực tiếp\n'
            f'{int(record.direct_count)}\n\n'
            '👥 團隊人數\n'
            'Số người đội nhóm\n'
            f'{int(record.team_count)}\n\n'
            '⚖️ 直推權重\n'
            'Trọng số trực tiếp\n'
            f'{int(record.direct_weight)}\n\n'
            '⚖️ 團隊權重\n'
            'Trọng số đội nhóm\n'
            f'{int(record.team_weight)}\n\n'
            '📊 直推比例\n'
            'Tỷ lệ trực tiếp\n'
            f'{format_percent(record.direct_ratio)}\n\n'
            '📊 團隊比例\n'
            'Tỷ lệ đội nhóm\n'
            f'{format_percent(record.team_ratio)}'
        )

    def format_bonus_message(self, employee_name: str) -> str:
        record = self.get_employee_record(employee_name)
        if not record:
            return f'找不到員工：{employee_name}\nKhông tìm thấy nhân viên: {employee_name}'
        return (
            f'👤 {record.name}\n'
            '━━━━━━━━━━━━━━━━━━\n\n'
            '💰 直推收益\n'
            'Thu nhập trực tiếp\n'
            f'{format_currency(record.direct_income)}\n\n'
            '💰 團隊收益\n'
            'Thu nhập đội nhóm\n'
            f'{format_currency(record.team_income)}\n\n'
            '🚫 違規扣款\n'
            'Khấu trừ vi phạm\n'
            f'{format_currency(record.penalty)}\n\n'
            '⚠️ 違規次數\n'
            'Số lần vi phạm\n'
            f'{int(record.violation_count)}\n\n'
            '💰 實際到手\n'
            'Thực nhận\n'
            f'{format_currency(record.actual_take_home)}\n\n'
            '📌 狀態\n'
            'Trạng thái\n'
            f'{record.status}'
        )


def _n(value: object) -> float:
    if value is None or value == '':
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(',', '')
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        logger.warning('無法轉成數字: %s', value)
        return 0.0

from __future__ import annotations

import logging
from typing import Iterable, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import Settings
from .sheets import RewardPenaltySheetService

logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BTN_WEIGHT = '查詢權重'
BTN_BONUS = '獎金查詢'
BTN_RANKING = '排行榜'
BTN_POOL = '今日獎池'
BTN_POOL_UPDATE = '獎池更新'

CALLBACK_WEIGHT = 'weight'
CALLBACK_BONUS = 'bonus'


def main() -> None:
    settings = Settings.from_env()
    sheet_service = RewardPenaltySheetService(settings)

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data['settings'] = settings
    app.bot_data['sheet_service'] = sheet_service

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('pool_update', pool_update_command))
    app.add_handler(CommandHandler('ranking', ranking_command))
    app.add_handler(CallbackQueryHandler(employee_callback_handler, pattern=r'^(weight|bonus):'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    logger.info('獎懲機器人已啟動')
    app.run_polling(allowed_updates=Update.ALL_TYPES)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        '歡迎使用獎懲機器人\nChào mừng bạn sử dụng bot thưởng phạt\n\n請選擇下方功能按鈕\nVui lòng chọn nút chức năng bên dưới',
        reply_markup=main_menu_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data['settings']
    admin_hint = ''
    if update.effective_user and update.effective_user.id in settings.admin_ids:
        admin_hint = (
            '\n\n管理員可使用：/pool_update 或直接輸入「獎池更新」'
            '\nQuản trị viên có thể dùng: /pool_update hoặc nhập trực tiếp "Cập nhật quỹ thưởng hôm nay"'
        )
    await update.effective_message.reply_text(
        '功能說明 / Hướng dẫn chức năng\n'
        '1. 查詢權重：查看員工直推/團隊人數、權重與比例\n'
        '   Tra trọng số: xem số người trực tiếp/đội nhóm, trọng số và tỷ lệ\n'
        '2. 獎金查詢：查看直推收益、團隊收益、違規扣款、實際到手\n'
        '   Tra thưởng: xem thu nhập trực tiếp, thu nhập đội nhóm, khấu trừ vi phạm và thực nhận\n'
        '3. 排行榜：查看依實際到手排序的員工排名\n'
        '   Bảng xếp hạng: xem xếp hạng theo thực nhận\n'
        '4. 今日獎池：查看最新獎池公告\n'
        '   Quỹ thưởng hôm nay: xem thông báo quỹ thưởng mới nhất'
        f'{admin_hint}'
    )


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or '').strip()
    if text == BTN_WEIGHT:
        await send_employee_picker(update, context, CALLBACK_WEIGHT)
        return
    if text == BTN_BONUS:
        await send_employee_picker(update, context, CALLBACK_BONUS)
        return
    if text == BTN_RANKING:
        await ranking_command(update, context)
        return
    if text == BTN_POOL:
        await send_pool_text(update, context, is_admin_trigger=False)
        return
    if text == BTN_POOL_UPDATE:
        await send_pool_text(update, context, is_admin_trigger=True)
        return

    await update.effective_message.reply_text(
        '請直接點選下方功能按鈕。\nVui lòng bấm trực tiếp các nút chức năng bên dưới。',
        reply_markup=main_menu_keyboard(),
    )


async def send_employee_picker(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    service: RewardPenaltySheetService = context.application.bot_data['sheet_service']
    bound_name = service.get_bound_employee_name(update.effective_user.id) if update.effective_user else None

    if bound_name:
        text = service.format_weight_message(bound_name) if action == CALLBACK_WEIGHT else service.format_bonus_message(bound_name)
        await update.effective_message.reply_text(text)
        return

    names = service.get_employee_names()
    if not names:
        await update.effective_message.reply_text('目前報表中沒有員工名單。\nHiện chưa có danh sách nhân viên trong báo cáo.')
        return

    keyboard = build_employee_keyboard(names, action)
    title = (
        '請選擇要查詢權重的員工：\nVui lòng chọn nhân viên cần tra trọng số:'
        if action == CALLBACK_WEIGHT
        else '請選擇要查詢獎金的員工：\nVui lòng chọn nhân viên cần tra thưởng:'
    )
    await update.effective_message.reply_text(title, reply_markup=keyboard)


async def employee_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    assert query is not None
    await query.answer()

    service: RewardPenaltySheetService = context.application.bot_data['sheet_service']
    raw = query.data or ''
    action, employee_name = raw.split(':', 1)
    employee_name = employee_name.strip()

    bound_name = service.get_bound_employee_name(query.from_user.id)
    if bound_name and bound_name != employee_name:
        await query.edit_message_text(
            f'你目前只可查詢綁定員工：{bound_name}\nHiện tại bạn chỉ có thể tra nhân viên đã liên kết: {bound_name}'
        )
        return

    text = service.format_weight_message(employee_name) if action == CALLBACK_WEIGHT else service.format_bonus_message(employee_name)
    await query.edit_message_text(text)


async def ranking_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: RewardPenaltySheetService = context.application.bot_data['sheet_service']
    text = service.get_ranking_text(limit=10)
    await update.effective_message.reply_text(text)


async def pool_update_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_pool_text(update, context, is_admin_trigger=True)


async def send_pool_text(update: Update, context: ContextTypes.DEFAULT_TYPE, is_admin_trigger: bool) -> None:
    service: RewardPenaltySheetService = context.application.bot_data['sheet_service']
    settings: Settings = context.application.bot_data['settings']
    user_id = update.effective_user.id if update.effective_user else 0
    text = service.get_pool_update_text()

    if is_admin_trigger:
        if user_id not in settings.admin_ids:
            await update.effective_message.reply_text(
                '只有管理員可以使用「獎池更新」。\nChỉ quản trị viên mới có thể dùng "Cập nhật quỹ thưởng hôm nay".'
            )
            return
        await update.effective_message.reply_text(text)
        if settings.announce_chat_id and update.effective_chat and update.effective_chat.id != settings.announce_chat_id:
            await context.bot.send_message(chat_id=settings.announce_chat_id, text=text)
            await update.effective_message.reply_text('已同步發送到公告群。\nĐã đồng bộ gửi đến nhóm thông báo.')
        return

    await update.effective_message.reply_text(text)


def build_employee_keyboard(names: Iterable[str], action: str) -> InlineKeyboardMarkup:
    buttons: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []
    for name in names:
        row.append(InlineKeyboardButton(str(name), callback_data=f'{action}:{name}'))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [BTN_WEIGHT, BTN_BONUS],
        [BTN_RANKING, BTN_POOL],
        [BTN_POOL_UPDATE],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


if __name__ == '__main__':
    main()

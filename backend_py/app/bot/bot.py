import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from aiogram import Bot, Dispatcher, html, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import func

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.tender import Tender, Keyword, TenderKeywordMatch, SystemSetting
from app.models.log import ParserLog
from app.models.telegram_channel import TelegramChannel
from app.models.admin import Admin
from app.models.winner import Winner
from app.models.monitored_company import MonitoredCompany
from app.utils.inn import normalize_inn
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

# --- Localization ---
I18N = {
    "ru": {
        "menu_keywords": "📋 Ключевые слова",
        "menu_stats": "📊 Статистика",
        "menu_recent": "🆕 Последние тендеры",
        "menu_archive": "📁 Архив",
        "menu_winners": "🏆 Победители",
        "menu_channels": "📺 Каналы",
        "menu_settings": "⚙️ Настройки",
        "menu_add_kw": "➕ Добавить слово",
        "menu_help": "🆘 Помощь",
        "menu_search": "🔍 Поиск",
        "welcome": "👋 <b>Добро пожаловать в Tender Intelligence Platform!</b>\n\nСистема мониторинга тендеров готова к работе.\nИспользуйте кнопку ниже для получения справки по командам.",
        "help_title": "📂 <b>СПИСОК КОМАНД</b>\n\n",
        "help_search_cat": "<b>Мониторинг и поиск:</b>\n",
        "help_check_inn": "• <code>/check_inn [ИНН]</code> — Анализ компании и поиск её тендеров.\n",
        "help_add_company": "• <code>/add_company [ИНН]</code> — Добавить компанию в список для Excel.\n",
        "help_companies": "• <code>/companies</code> — Список отслеживаемых компаний.\n",
        "help_check_lot": "• <code>/check_lot [ID]</code> — Полная информация о лоте Uzex (с контактами).\n",
        "help_search_btn": "• 🔍 <b>Поиск</b> — Интерактивный поиск по ИНН.\n\n",
        "help_kw_cat": "<b>Управление ключевыми словами:</b>\n",
        "help_add_kw": "• ➕ <b>Добавить слово</b> — Добавление фразы в поиск или черный список.\n",
        "help_kw_list": "• 📋 <b>Ключевые слова</b> — Список активных слов и исключений.\n\n",
        "help_sys_cat": "<b>Системные настройки:</b>\n",
        "help_settings": "• ⚙️ <b>Настройки</b> — Управление источниками, экспортом и фильтрами.\n",
        "help_stats": "• 📊 <b>Статистика</b> — Статистика работы парсеров за 7 дней.\n",
        "help_login": "• <code>/login</code> — Авторизация администратора.\n\n",
        "help_integrations": "<b>Интеграции:</b>\n• Авто-экспорт в Google Sheets включен.\n• CRM-интеграция активна.\n",
        "settings_title": "⚙️ <b>Настройки системы</b>",
        "btn_sources": "🔌 Источники (Сайты)",
        "btn_export": "📊 Экспорт (Google Sheets)",
        "btn_blacklist": "🚫 Черный список",
        "btn_status": "⚙️ Статус системы",
        "btn_lang": "🌐 Til / Язык",
        "btn_back": "⬅️ Назад",
        "lang_select": "<b>Выберите язык интерфейса / Tilni tanlang:</b>",
        "searching_inn": "🔎 <b>Ищу тендеры и контакты для ИНН {inn}...</b>\nЭто может занять 10-15 секунд.",
        "searching_lot": "🔎 <b>Ищу подробные данные по лоту № {id}...</b>\nЭто может занять 10-15 секунд.",
        "inn_results_title": "🔍 <b>ТЕНДЕРЫ КОМПАНИИ (ИНН: {inn})</b>\n",
        "found_count": "Найдено: <b>{count}</b> тендер(ов)\n",
        "lot_title": "📦 <b>ТЕНДЕР (ЛОТ № {id})</b>\n",
        "tender_obj": "📍 <b>Объект:</b>",
        "tender_org": "🏢 <b>Заказчик:</b>",
        "tender_inn_label": "🆔 <b>ИНН:</b>",
        "tender_sum": "💰 <b>Сумма:</b>",
        "tender_reg": "📍 <b>Регион:</b>",
        "tender_lang": "🌐 <b>Язык:</b>",
        "tender_phone": "📞 <b>Телефоны:</b>",
        "tender_email": "📧 <b>Email:</b>",
        "tender_addr": "📍 <b>Адрес:</b>",
        "tender_pay": "💳 <b>Оплата:</b>",
        "tender_open": "Открыть на сайте",
        "dossier_title": "🏢 <b>ДОСЬЕ КОМПАНИИ (ИНН: {inn})</b>\n",
        "dossier_company": "🏢 <b>Компания:</b>",
        "dossier_dir": "👤 <b>Директор:</b>",
        "dossier_act": "🏗 <b>Деятельность:</b>",
        "not_found_db": "📭 <b>Тендеров с ИНН {inn} не найдено в базе.</b>\nПоказываю досье компании...",
        "lot_not_found": "❌ <b>Лот № {id} не найден</b> или данные недоступны.",
        "kw_menu_title": "<b>📋 Настройки фильтрации:</b>\n",
        "kw_search_list": "🔍 <b>Поиск тендеров по:</b>\n",
        "kw_black_list": "🚫 <b>Черный список (Исключить):</b>\n",
        "kw_empty": "📭 Списки пусты. Добавьте слова через «➕ Добавить слово».",
        "kw_del_hint": "<i>Чтобы удалить слово, используйте команду:</i>\n<code>/del [слово]</code>",
        "kw_added": "✅ Слово <code>{phrase}</code> обновлено и добавлено {type}!",
        "kw_active": "⚠️ Слово <code>{phrase}</code> уже активно в этом списке.",
        "kw_success": "✨ <b>Готово!</b>\nСлово <code>{phrase}</code> добавлено {type}.",
        "last_title": "<b>🆕 Свежие находки:</b>\n",
        "stats_title": "<b>📊 Аналитика мониторинга</b>\n",
        "stats_today": "📈 За сегодня: <b>{count} тендеров</b>\n",
        "stats_week": "📅 За неделю: <b>{count} тендеров</b>\n",
        "stats_kw": "🔑 В работе слов: <b>{count}</b>\n\n",
        "stats_updated": "<i>Обновлено: {time}</i>",
        "btn_open_short": "Открыть",
        "winners_empty": "📬 <b>База победителей пока пуста.</b>\nКак только тендеры начнут завершаться, здесь появится рейтинг конкурентов.",
        "winners_title": "<b>🏆 ТОП-10 КОНКУРЕНТОВ (ПОБЕДИТЕЛЕЙ):</b>\n",
        "btn_cancel": "❌ Отмена",
        "sources_title": "🔌 <b>Управление источниками</b>",
        "sources_hint": "Нажмите на источник, чтобы включить или выключить его:",
        "source_enabled": "включен",
        "source_disabled": "выключен",
        "bl_empty": "<b>🚫 Черный список пуст.</b>\nДобавьте слова-исключения через «➕ Добавить слово».",
        "bl_title": "<b>🚫 Черный список (Исключения):</b>\n\n",
        "exp_title": "📊 <b>Настройки экспорта</b>",
        "exp_hint": "Google Sheets — новые тендеры по ключам. Excel — только компании-победители (g'oliblar).",
        "exp_gs_status": "Экспорт в Google Sheets:",
        "exp_gs_enabled": "АВТО-ЭКСПОРТ ВКЛЮЧЕН ✅",
        "exp_gs_disabled": "АВТО-ЭКСПОРТ ВЫКЛЮЧЕН ❌",
        "exp_excel_daily": "🏆 Голиблар — сегодня (Excel)",
        "exp_excel_weekly": "🏆 Голиблар — неделя (Excel)",
        "exp_excel_monthly": "🏆 Голиблар — месяц (Excel)",
        "exp_excel_all": "🏆 Все голибы (Excel)",
        "exp_excel_start": "⏳ <b>Excel ({label})...</b>\nЗагрузка победителей с etender",
        "exp_excel_empty": "📭 Победителей за этот период не найдено.",
        "exp_excel_done": "✅ <b>Excel готов</b>\n🏆 Компаний-победителей: {count}\n🌐 Сделок в etender: {api}",
        "add_company_prompt": "📝 Введите ИНН компании (9 цифр).\nПример: <code>/add_company 305886617</code>",
        "add_company_ok": "✅ Компания добавлена в список:\n<b>{name}</b>\nINN: <code>{inn}</code>",
        "add_company_invalid": "❌ Неверный ИНН. Нужно 9 цифр (STIR).",
        "add_company_exists": "ℹ️ Компания с INN <code>{inn}</code> уже в списке.",
        "companies_empty": "📭 Список компаний пуст.\nДобавьте: <code>/add_company ИНН</code>",
        "companies_list_title": "🏢 <b>Отслеживаемые компании ({count}):</b>\n\n",
        "auth_private": "🔒 <b>Система приватна.</b>",
        "auth_success": "🔓 <b>Доступ разрешен!</b>\nДобро пожаловать в панель управления.",
        "auth_fail": "❌ <b>Ошибка:</b> Неверный пароль.",
        "kw_add_input": "📝 <b>Введите новое ключевое слово или фразу:</b>\n\nНапример: <code>строительство склада</code>\n\n<i>Я буду искать тендеры, где встречается это слово.</i>",
        "kw_type_select": "📝 Фраза: <code>{phrase}</code>\n\nВыберите тип:",
        "kw_type_search": "🔍 Список поиска",
        "kw_type_black": "🚫 Черный список",
        "del_err": "❌ <b>Ошибка:</b> укажите слово для удаления.\nПример: <code>/del бетон</code>",
        "del_success": "✅ Слово <code>{phrase}</code> удалено из мониторинга.",
        "del_not_found": "⚠️ Слово <code>{phrase}</code> не найдено в списке активных.",
        "arch_date_hint": "Введите команду: /date ДД.ММ",
        "tender_inn_label_short": "ИНН",
        "err_export": "❌ <b>Ошибка при экспорте:</b> {e}",
        "btn_open_short": "Открыть",
        "auth_login_prompt": "🔑 Введите пароль после команды.\nПример: <code>/login ваш_пароль</code>",
        "auth_admin_success": "🔓 <b>Доступ разрешен!</b>\nТеперь вы являетесь администратором системы.",
        "auth_already_logged": "✅ Вы уже авторизованы.",
        "btn_back_both": "⬅️ Назад / Orqaga",
        "arch_today": "📅 Сегодня",
        "arch_yesterday": "📅 Вчера",
        "arch_3days": "📅 За 3 дня",
        "arch_by_date": "🔍 По дате (введите /date 14.05)",
        "arch_export_excel": "📊 Экспорт в Excel",
        "winners_footer": "<i>Данные собраны на основе завершенных тендеров по вашим ключевым словам.</i>",
        "check_inn_prompt": "🔍 Введите ИНН или Номер Лота для проверки.\nПример: <code>/check_inn 482418</code>",
        "tender_sum": "💰 <b>Сумма:</b>",
        "tender_reg": "📍 <b>Регион:</b>",
        "tender_lang": "🌐 <b>Язык:</b>",
        "tender_phone": "📞 <b>Телефоны:</b>",
        "tender_email": "📧 <b>Email:</b>",
        "tender_addr": "📍 <b>Адрес:</b>",
        "tender_pay": "💳 <b>Условия оплаты:</b>",
        "tender_open": "Открыть на сайте",
        "tender_obj": "📍 <b>Объект:</b>",
        "tender_org": "🏢 <b>Заказчик:</b>",
        "tender_inn_label": "🆔 <b>ИНН:</b>",
        "tender_inn_organizer": "🆔 <b>ИНН Заказчика:</b>",
        "tender_contacts_label": "📞 <b>Контакты:</b>",
        "tender_deposit": "💸 <b>Задаток:</b>",
        "tender_desc": "📝 <b>Описание:</b>",
        "tender_source_label": "<i>Источник: etender.uzex.uz</i>",
        "lot_title": "📦 <b>ТЕНДЕР (ЛОТ № {id})</b>\n",
        "searching_inn": "🔎 <b>Ищу тендеры по ИНН {inn}...</b>\nЭто может занять 10-15 секунд.",
        "searching_lot": "🔎 <b>Ищу лот № {id}...</b>\nЭто может занять 10-15 секунд.",
        "inn_results_title": "🔍 <b>ТЕНДЕРЫ КОМПАНИИ (ИНН: {inn})</b>\n",
        "found_count": "Найдено: <b>{count}</b> тендеров\n",
        "not_found_db": "📭 <b>В базе не найдено тендеров по ИНН {inn}.</b>\nПоказываю досье компании...",
        "lot_not_found": "❌ <b>Лот № {id} не найден.</b>",
        "err_lot_search": "❌ Ошибка при поиске лота: {e}",
        "err_search": "❌ Ошибка при поиске: {e}",
        "company_name_placeholder": "Компания {inn}",
        "lang_changed_msg": "✅ Til o'zgartirildi / Язык изменен",
        "exp_settings_title": "<b>📊 Настройки экспорта</b>\n\nУправляйте автоматической выгрузкой в Google Sheets:",
        "exp_gs_toggle_off": "Авто-экспорт выключен",
        "exp_gs_toggle_on": "Авто-экспорт включен",
        "chan_list_empty": "🔍 <b>Список каналов пуст.</b>\nДобавьте канал, нажав кнопку ниже или прислав username (например @tashkent_news).",
        "chan_add_btn": "➕ Добавить канал",
        "chan_title": "<b>📺 Мониторинг каналов:</b>",
        "chan_del_hint": "<i>Используйте /del_chan [username] для удаления.</i>",
        "chan_add_more": "➕ Добавить еще",
        "chan_add_prompt": "📝 <b>Введите username или ссылку на канал:</b>\n\nНапример: <code>@tashkent_news</code> или <code>https://t.me/energy_uz</code>",
        "chan_cancel": "🚫 Отменено.",
        "chan_exists": "⚠️ Канал <code>{username}</code> уже в списке.",
        "chan_added_success": "✅ Канал <code>{username}</code> добавлен в мониторинг!",
        "chan_del_prompt": "❌ Укажите username. Пример: <code>/del_chan @news</code>",
        "chan_del_success": "✅ Канал <code>{username}</code> удален.",
        "chan_not_found": "⚠️ Канал не найден.",
        "arch_menu_title": "<b>📁 Архив тендеров</b>\nВыберите период для просмотра:",
        "arch_export_title": "<b>📊 Excel: все тендеры UZEX</b>\n6 колонок: гolib, INN, тендер, сумма, viloyat, telefon",
        "arch_label_today": "Сегодня",
        "arch_label_yesterday": "Вчера",
        "arch_label_3days": "Последние 3 дня",
        "arch_empty_period": "📭 В архиве за <b>{label}</b> ничего не найдено.",
        "arch_results_title": "<b>📁 Архив: {label} (Топ-10)</b>",
        "arch_price_request": "По запросу",
        "arch_link": "Открыть",
        "date_prompt": "❌ Введите дату. Пример: <code>/date 14.05</code>",
        "date_not_found": "📭 За <b>{date_str}</b> тендеров не найдено.",
        "date_results_title": "<b>📁 Результаты за {date_str}:</b>",
        "date_invalid_fmt": "❌ Неверный формат даты. Используйте: <code>ДД.ММ</code> (например 14.05)",
        "lot_searching": "🔎 <b>Ищу лот № {lot_id}...</b>",
        "lot_not_found_fallback": "ℹ️ Лот не найден. Пробую найти компанию по ИНН {lot_id}...",
        "lot_not_found_err": "❌ <b>Лот № {lot_id} не найден.</b>",
        "tender_inn_organizer": "🆔 <b>ИНН Заказчика:</b>",
        "tender_contacts_label": "📞 <b>Контакты (Aloqa):</b>",
        "not_specified": "Не указан",
        "status_platform": "<b>⚙️ Состояние платформы</b>",
        "status_mon": "📡 Мониторинг:",
        "status_mon_active": "🟢 Активен",
        "status_db_label": "🗄 База данных:",
        "status_db_online": "🟢 Online",
        "status_last_update": "🕒 Последнее обновление:",
        "status_parser_label": "📝 Статус парсера:",
        "status_found_lots": "📥 Найдено лотов:",
        "kw_interrupted": "⚠️ Добавление слова прервано.",
        "winners_count_label": "Побед:",
        "winners_times_label": "раз",
        "tender_status": "🟢 <b>Статус:</b>",
        "tender_reg_order": "📋 <b>Оформление:</b>",
        "tender_deadline": "📅 <b>Срок размещения:</b>",
        "tender_files": "📎 <b>Файлы:</b>",
        "lot_winner_header": "🏆 <b>ПОБЕДИТЕЛЬ ТЕНДЕРА</b>",
        "lot_winner_name": "🏢 <b>Компания:</b>",
        "lot_winner_inn": "🆔 <b>ИНН победителя:</b>",
        "lot_winner_sum": "💰 <b>Сумма победы:</b>",
        "lot_winner_phone": "📞 <b>Телефон:</b>",
        "lot_winner_not_found": "🏆 <i>Победитель по этому лоту пока не найден в etender (DealsList).</i>",
    },
    "uz": {
        "menu_keywords": "📋 Kalit so'zlar",
        "menu_stats": "📊 Statistika",
        "menu_recent": "🆕 So'nggi tenderlar",
        "menu_archive": "📁 Arxiv",
        "menu_winners": "🏆 G'oliblar",
        "menu_channels": "📺 Kanallar",
        "menu_settings": "⚙️ Sozlamalar",
        "menu_add_kw": "➕ So'z qo'shish",
        "menu_help": "🆘 Yordam",
        "menu_search": "🔍 Qidiruv",
        "welcome": "👋 <b>Tender Intelligence Platform-ga xush kelibsiz!</b>\n\nTender monitoringi tizimi ishga tayyor.\nBuyruqlar bo'yicha ma'lumot olish uchun quyidagi tugmani bosing.",
        "help_title": "📂 <b>BUYRUQLAR RO'YXATI</b>\n\n",
        "help_search_cat": "<b>Monitoring va qidiruv:</b>\n",
        "help_check_inn": "• <code>/check_inn [INN]</code> — Kompaniya tahlili va uning tenderlarini qidirish.\n",
        "help_add_company": "• <code>/add_company [INN]</code> — Excel ro'yxatiga kompaniya qo'shish.\n",
        "help_companies": "• <code>/companies</code> — Kuzatiladigan kompaniyalar ro'yxati.\n",
        "help_check_lot": "• <code>/check_lot [ID]</code> — Uzex loti haqida to'liq ma'lumot (kontaktlar bilan).\n",
        "help_search_btn": "• 🔍 <b>Qidiruv</b> — INN bo'yicha interaktiv qidiruv.\n\n",
        "help_kw_cat": "<b>Kalit so'zlarni boshqarish:</b>\n",
        "help_add_kw": "• ➕ <b>So'z qo'shish</b> — Qidiruvga yoki qora ro'yxatga so'z qo'shish.\n",
        "help_kw_list": "• 📋 <b>Kalit so'zlar</b> — Faol so'zlar va istisnolar ro'yxati.\n\n",
        "help_sys_cat": "<b>Tizim sozalamalari:</b>\n",
        "help_settings": "• ⚙️ <b>Sozlamalar</b> — Manbalar, eksport va filtrlarni boshqarish.\n",
        "help_stats": "• 📊 <b>Statistika</b> — Parserlarning 7 kunlik ish statistikasi.\n",
        "help_login": "• <code>/login</code> — Administrator avtorizatsiyasi.\n\n",
        "help_integrations": "<b>Integratsiyalar:</b>\n• Google Sheets-ga avto-eksport yoqilgan.\n• CRM integratsiyasi faol.\n",
        "settings_title": "⚙️ <b>Tizim sozlamalari</b>",
        "btn_sources": "🔌 Manbalar (Saytlar)",
        "btn_export": "📊 Eksport (Google Sheets)",
        "btn_blacklist": "🚫 Qora ro'yxat",
        "btn_status": "⚙️ Tizim holati",
        "btn_lang": "🌐 Til / Язык",
        "btn_back": "⬅️ Orqaga",
        "lang_select": "<b>Tilni tanlang / Выберите язык интерфейса:</b>",
        "searching_inn": "🔎 <b>INN {inn} bo'yicha tender va kontaktlar qidirilmoqda...</b>\nBu 10-15 soniya vaqt olishi mumkin.",
        "searching_lot": "🔎 <b>Loyiha № {id} bo'yicha ma'lumot qidirilmoqda...</b>\nBu 10-15 soniya vaqt olishi mumkin.",
        "inn_results_title": "🔍 <b>KOMPANIYA TENDERLARI (INN: {inn})</b>\n",
        "found_count": "Topildi: <b>{count}</b> ta tender\n",
        "lot_title": "📦 <b>TENDER (LOYIHA № {id})</b>\n",
        "tender_obj": "📍 <b>Obyekt:</b>",
        "tender_org": "🏢 <b>Buyurtmachi:</b>",
        "tender_inn_label": "🆔 <b>STIR (INN):</b>",
        "tender_sum": "💰 <b>Summa:</b>",
        "tender_reg": "📍 <b>Hudud:</b>",
        "tender_lang": "🌐 <b>Til:</b>",
        "tender_phone": "📞 <b>Telefonlar:</b>",
        "tender_email": "📧 <b>Email:</b>",
        "tender_addr": "📍 <b>Manzil:</b>",
        "tender_pay": "💳 <b>To'lov shartlari:</b>",
        "tender_open": "Saytda ochish",
        "dossier_title": "🏢 <b>KOMPANIYA DOSYESI (INN: {inn})</b>\n",
        "dossier_company": "🏢 <b>Kompaniya:</b>",
        "dossier_dir": "👤 <b>Direktor:</b>",
        "dossier_act": "🏗 <b>Faoliyat:</b>",
        "not_found_db": "📭 <b>Bazada INN {inn} bo'yicha tenderlar topilmadi.</b>\nKompaniya dosyesini ko'rsataman...",
        "lot_not_found": "❌ <b>Loyiha № {id} topilmadi</b> yoki ma'lumot yo'q.",
        "kw_menu_title": "<b>📋 Filtrlash sozlamalari:</b>\n",
        "kw_search_list": "🔍 <b>Tenderlarni qidirish:</b>\n",
        "kw_black_list": "🚫 <b>Qora ro'yxat (Istisnolar):</b>\n",
        "kw_empty": "📭 Ro'yxatlar bo'sh. «➕ So'z qo'shish» orqali so'zlar qo'shing.",
        "kw_del_hint": "<i>So'zni o'chirish uchun buyruqdan foydalaning:</i>\n<code>/del [so'z]</code>",
        "kw_added": "✅ <code>{phrase}</code> so'zi yangilandi va {type}ga qo'shildi!",
        "kw_active": "⚠️ <code>{phrase}</code> so'zi ushbu ro'yxatda allaqachon faol.",
        "kw_success": "✨ <b>Tayyor!</b>\n<code>{phrase}</code> so'zi {type}ga qo'shildi.",
        "last_title": "<b>🆕 Yangi topilganlar:</b>\n",
        "stats_title": "<b>📊 Monitoring tahlili</b>\n",
        "stats_today": "📈 Bugun: <b>{count} ta tender</b>\n",
        "stats_week": "📅 Hafta davomida: <b>{count} ta tender</b>\n",
        "stats_kw": "🔑 Faol so'zlar: <b>{count}</b>\n\n",
        "stats_updated": "<i>Yangilandi: {time}</i>",
        "btn_open_short": "Ochish",
        "winners_empty": "📬 <b>G'oliblar bazasi hozircha bo'sh.</b>\nTenderlar yakunlanishi bilan bu yerda raqobatchilar reytingi paydo bo'ladi.",
        "winners_title": "<b>🏆 TOP-10 RAQOBATCHILAR (G'OLIBLAR):</b>\n",
        "btn_cancel": "❌ Bekor qilish",
        "sources_title": "🔌 <b>Manbalarni boshqarish</b>",
        "sources_hint": "Yoqish yoki o'chirish uchun manbani bosing:",
        "source_enabled": "yoqildi",
        "source_disabled": "o'chirildi",
        "bl_empty": "<b>🚫 Qora ro'yxat bo'sh.</b>\n«➕ So'z qo'shish» orqali istisnolarni qo'shing.",
        "bl_title": "<b>🚫 Qora ro'yxat (Istisnolar):</b>\n\n",
        "exp_title": "📊 <b>Eksport sozlamalari</b>",
        "exp_hint": "Google Sheets — kalit so'zli tenderlar. Excel — faqat g'olib kompaniyalar.",
        "exp_gs_status": "Google Sheets-ga eksport:",
        "exp_gs_enabled": "AVTO-EKSPORT YOQILGAN ✅",
        "exp_gs_disabled": "AVTO-EKSPORT O'CHIRILGAN ❌",
        "exp_excel_daily": "🏆 G'oliblar — bugun (Excel)",
        "exp_excel_weekly": "🏆 G'oliblar — hafta (Excel)",
        "exp_excel_monthly": "🏆 G'oliblar — oy (Excel)",
        "exp_excel_all": "🏆 Barcha g'oliblar (Excel)",
        "exp_excel_start": "⏳ <b>Excel ({label})...</b>\nEtender g'oliblari yuklanmoqda",
        "exp_excel_empty": "📭 Bu davrda g'oliblar topilmadi.",
        "exp_excel_done": "✅ <b>Excel tayyor</b>\n🏆 G'olib kompaniyalar: {count}\n🌐 Bitimlar: {api}",
        "add_company_prompt": "📝 Kompaniya INN kiriting (9 raqam).\nMasalan: <code>/add_company 305886617</code>",
        "add_company_ok": "✅ Ro'yxatga qo'shildi:\n<b>{name}</b>\nINN: <code>{inn}</code>",
        "add_company_invalid": "❌ Noto'g'ri INN. 9 raqam kerak (STIR).",
        "add_company_exists": "ℹ️ INN <code>{inn}</code> allaqachon ro'yxatda.",
        "companies_empty": "📭 Kompaniyalar yo'q.\n<code>/add_company INN</code> bilan qo'shing.",
        "companies_list_title": "🏢 <b>Kuzatiladigan kompaniyalar ({count}):</b>\n\n",
        "auth_private": "🔒 <b>Tizim shaxsiy.</b>",
        "auth_success": "🔓 <b>Ruxsat berildi!</b>\nBoshqaruv paneliga xush kelibsiz.",
        "auth_fail": "❌ <b>Xato:</b> Noto'g'ri parol.",
        "kw_add_input": "📝 <b>Yangi kalit so'z yoki iborani kiriting:</b>\n\nMasalan: <code>sklad qurilishi</code>\n\n<i>Men ushbu so'z uchraydigan tenderlarni qidiraman.</i>",
        "kw_type_select": "📝 Ibora: <code>{phrase}</code>\n\nTurini tanlang:",
        "kw_type_search": "🔍 Qidiruv ro'yxati",
        "kw_type_black": "🚫 Qora ro'yxat",
        "del_err": "❌ <b>Xato:</b> o'chirish uchun so'zni ko'rsating.\nMasalan: <code>/del beton</code>",
        "del_success": "✅ <code>{phrase}</code> so'zi monitoringdan o'chirildi.",
        "del_not_found": "⚠️ <code>{phrase}</code> so'zi faol ro'yxatda topilmadi.",
        "arch_date_hint": "Buyruqni kiriting: /date KK.OO",
        "tender_inn_label_short": "STIR",
        "err_export": "❌ <b>Eksportda xatolik:</b> {e}",
        "btn_open_short": "Ochish",
        "auth_login_prompt": "🔑 Buyruqdan keyin parolni kiriting.\nMasalan: <code>/login sizning_parolingiz</code>",
        "auth_admin_success": "🔓 <b>Ruxsat berildi!</b>\nEndi siz tizim administratorisiz.",
        "auth_already_logged": "✅ Siz allaqachon avtorizatsiyadan o'tgansiz.",
        "btn_back_both": "⬅️ Orqaga / Назад",
        "arch_today": "📅 Bugun",
        "arch_yesterday": "📅 Kecha",
        "arch_3days": "📅 3 kunlik",
        "arch_by_date": "🔍 Sana bo'yicha (/date 14.05 kiriting)",
        "arch_export_excel": "📊 Excel-ga eksport",
        "winners_footer": "<i>Ma'lumotlar sizning kalit so'zlaringiz asosida yakunlangan tenderlardan yig'ilgan.</i>",
        "check_inn_prompt": "🔍 Tekshirish uchun INN yoki Loyiha raqamini kiriting.\nMasalan: <code>/check_inn 482418</code>",
        "check_inn_prompt": "🔍 Tekshirish uchun INN yoki Loyiha raqamini kiriting.\nMasalan: <code>/check_inn 482418</code>",
        "tender_deposit": "💸 <b>Zakolat:</b>",
        "tender_desc": "📝 <b>Tavsif:</b>",
        "tender_source_label": "<i>Manba: etender.uzex.uz</i>",
        "err_lot_search": "❌ Loyihani qidirishda xatolik: {e}",
        "err_search": "❌ Qidiruvda xatolik: {e}",
        "company_name_placeholder": "Kompaniya {inn}",
        "lang_changed_msg": "✅ Til o'zgartirildi / Язык изменен",
        "exp_settings_title": "<b>📊 Eksport sozlamalari</b>\n\nGoogle Sheets-ga avtomatik yuklashni boshqaring:",
        "exp_gs_toggle_off": "Avto-eksport o'chirildi",
        "exp_gs_toggle_on": "Avto-eksport yoqildi",
        "chan_list_empty": "🔍 <b>Kanallar ro'yxati bo'sh.</b>\nQuyidagi tugmani bosib yoki username yuborib kanal qo'shing (masalan @tashkent_news).",
        "chan_add_btn": "➕ Kanal qo'shish",
        "chan_title": "<b>📺 Kanallar monitoringi:</b>",
        "chan_del_hint": "<i>O'chirish uchun /del_chan [username] buyrug'idan foydalaning.</i>",
        "chan_add_more": "➕ Yana qo'shish",
        "chan_add_prompt": "📝 <b>Kanal username yoki havolasini kiriting:</b>\n\nMasalan: <code>@tashkent_news</code> yoki <code>https://t.me/energy_uz</code>",
        "chan_cancel": "🚫 Bekor qilindi.",
        "chan_exists": "⚠️ <code>{username}</code> kanali allaqachon ro'yxatda bor.",
        "chan_added_success": "✅ <code>{username}</code> kanali monitoringga qo'shildi!",
        "chan_del_prompt": "❌ Usernameni ko'rsating. Masalan: <code>/del_chan @news</code>",
        "chan_del_success": "✅ <code>{username}</code> kanali o'chirildi.",
        "chan_not_found": "⚠️ Kanal topilmadi.",
        "arch_menu_title": "<b>📁 Tenderlar arxivi</b>\nKo'rish uchun davrni tanlang:",
        "arch_export_title": "<b>📊 Excel: barcha UZEX tenderlar</b>\n6 ustun: g'olib, INN, tender, summa, viloyat, telefon",
        "arch_label_today": "Bugun",
        "arch_label_yesterday": "Kecha",
        "arch_label_3days": "Oxirgi 3 kun",
        "arch_empty_period": "📭 <b>{label}</b> uchun arxivda hech narsa topilmadi.",
        "arch_results_title": "<b>📁 Arxiv: {label} (Top-10)</b>",
        "arch_price_request": "So'rov bo'yicha",
        "arch_link": "Ochish",
        "date_prompt": "❌ Sanani kiriting. Masalan: <code>/date 14.05</code>",
        "date_not_found": "📭 <b>{date_str}</b> uchun tenderlar topilmadi.",
        "date_results_title": "<b>📁 {date_str} uchun natijalar:</b>",
        "date_invalid_fmt": "❌ Sana formati noto'g'ri. <code>KK.OO</code> formatidan foydalaning (masalan 14.05)",
        "lot_searching": "🔎 <b>Loyiha № {lot_id} qidirilmoqda...</b>",
        "lot_not_found_fallback": "ℹ️ Loyiha topilmadi. INN {lot_id} bo'yicha kompaniyani qidirib ko'raman...",
        "lot_not_found_err": "❌ <b>Loyiha № {lot_id} topilmadi.</b>",
        "tender_inn_organizer": "🆔 <b>Buyurtmachi STIR (INN):</b>",
        "tender_contacts_label": "📞 <b>Kontaktlar (Aloqa):</b>",
        "not_specified": "Ko'rsatilmagan",
        "status_platform": "<b>⚙️ Platforma holati</b>",
        "status_mon": "📡 Monitoring:",
        "status_mon_active": "🟢 Faol",
        "status_db_label": "🗄 Ma'lumotlar bazasi:",
        "status_db_online": "🟢 Online",
        "status_last_update": "🕒 So'nggi yangilanish:",
        "status_parser_label": "📝 Parser holati:",
        "status_found_lots": "📥 Topilgan loyihalar:",
        "kw_interrupted": "⚠️ So'z qo'shish to'xtatildi.",
        "winners_count_label": "G'alabalar:",
        "winners_times_label": "marta",
        "tender_status": "🟢 <b>Holat:</b>",
        "tender_reg_order": "📋 <b>Rasmiylashtirish tartibi:</b>",
        "tender_deadline": "📅 <b>Joylashtirish muddati:</b>",
        "tender_files": "📎 <b>Fayllar:</b>",
        "lot_winner_header": "🏆 <b>TENDER G'OLIBI</b>",
        "lot_winner_name": "🏢 <b>Korxona:</b>",
        "lot_winner_inn": "🆔 <b>G'olib STIR:</b>",
        "lot_winner_sum": "💰 <b>Yutgan summa:</b>",
        "lot_winner_phone": "📞 <b>Telefon:</b>",
        "lot_winner_not_found": "🏆 <i>Bu loyiha bo'yicha g'olib etender (DealsList) da topilmadi.</i>",
    }
}

def get_lang(db):
    setting = db.query(SystemSetting).filter(SystemSetting.key == "system_language").first()
    return setting.value if setting else "ru"

def translate(db, key):
    lang = get_lang(db)
    return I18N.get(lang, I18N["ru"]).get(key, key)

# --- Security Middleware ---
class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)
        
        # 1. Allow ONLY /login for non-admins. 
        # Even /start is restricted to prevent information leakage.
        is_login_attempt = event.text and event.text.startswith("/login")
        
        db = SessionLocal()
        try:
            admin = db.query(Admin).filter(Admin.telegram_id == event.from_user.id).first()
            if admin:
                return await handler(event, data)
            
            if is_login_attempt:
                return await handler(event, data)
            
            # For everyone else - silence or minimal response
            await event.answer(translate(db, "auth_private"), parse_mode="HTML")
            return
        finally:
            db.close()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- States ---
class AddKeywordForm(StatesGroup):
    waiting_for_phrase = State()
    waiting_for_type = State()

class AddChannelForm(StatesGroup):
    waiting_for_username = State()

dp = Dispatcher()
dp.message.middleware(AuthMiddleware())
#67 XD
# --- Keyboards ---
# ... (rest unchanged)

# --- Auth Handler ---

@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    db = SessionLocal()
    try:
        await message.answer(
            translate(db, "welcome"),
            parse_mode="HTML",
            reply_markup=get_main_menu(db)
        )
        await cmd_help(message)
    finally:
        db.close()

@dp.message(Command("login"))
async def cmd_login(message: Message, command: CommandObject) -> None:
    # Secret password (can be moved to .env)
    SECRET_PASSWORD = "tender2026"
    db = SessionLocal()
    try:
        if not command.args:
            await message.answer(translate(db, "auth_login_prompt"), parse_mode="HTML")
            return
        
        if command.args.strip() == SECRET_PASSWORD:
            existing = db.query(Admin).filter(Admin.telegram_id == message.from_user.id).first()
            if not existing:
                new_admin = Admin(telegram_id=message.from_user.id, username=message.from_user.username)
                db.add(new_admin)
                db.commit()
                await message.answer(translate(db, "auth_admin_success"), parse_mode="HTML", reply_markup=get_main_menu(db))
            else:
                await message.answer(translate(db, "auth_already_logged"), reply_markup=get_main_menu(db))
        else:
            await message.answer(translate(db, "auth_invalid_password"), parse_mode="HTML")
    finally:
        db.close()

def get_main_menu(db=None):
    if not db:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
        
    try:
        kb = [
            [KeyboardButton(text=translate(db, "menu_keywords")), KeyboardButton(text=translate(db, "menu_stats"))],
            [KeyboardButton(text=translate(db, "menu_recent")), KeyboardButton(text=translate(db, "menu_archive"))],
            [KeyboardButton(text=translate(db, "menu_winners")), KeyboardButton(text=translate(db, "menu_channels"))],
            [KeyboardButton(text=translate(db, "menu_settings")), KeyboardButton(text=translate(db, "menu_add_kw"))],
            [KeyboardButton(text=translate(db, "menu_help"))]
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    finally:
        if close_db:
            db.close()

def get_settings_kb(db):
    kb = [
        [InlineKeyboardButton(text=translate(db, "btn_sources"), callback_data="set_sources")],
        [InlineKeyboardButton(text=translate(db, "btn_export"), callback_data="set_export")],
        [InlineKeyboardButton(text=translate(db, "btn_blacklist"), callback_data="set_blacklist")],
        [InlineKeyboardButton(text=translate(db, "btn_status"), callback_data="set_status")],
        [InlineKeyboardButton(text=translate(db, "btn_lang"), callback_data="set_lang")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_lang_kb(db):
    kb = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text=translate(db, "btn_back_both"), callback_data="set_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_sources_kb(db):
    sources = ["UZEX_ETENDER", "XARID_UZEX", "TENDER_MC", "E_AUKSION"]
    kb = []
    for s in sources:
        setting = db.query(SystemSetting).filter(SystemSetting.key == f"source_{s.lower()}").first()
        is_on = setting.value.lower() == "true" if setting else True
        icon = "✅" if is_on else "❌"
        kb.append([InlineKeyboardButton(text=f"{icon} {s}", callback_data=f"toggle_src_{s}")])
    kb.append([InlineKeyboardButton(text=translate(db, "btn_back"), callback_data="set_back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_export_kb(db):
    setting = db.query(SystemSetting).filter(SystemSetting.key == "export_google_sheets").first()
    is_on = setting.value.lower() == "true" if setting else settings.GOOGLE_SHEETS_AUTO_EXPORT
    status_text = translate(db, "exp_gs_enabled") if is_on else translate(db, "exp_gs_disabled")
    
    kb = [
        [InlineKeyboardButton(text=f"{translate(db, 'exp_gs_status')} {status_text}", callback_data="toggle_exp_gs")],
        [InlineKeyboardButton(text=translate(db, "exp_excel_daily"), callback_data="export_daily")],
        [InlineKeyboardButton(text=translate(db, "exp_excel_weekly"), callback_data="export_weekly")],
        [InlineKeyboardButton(text=translate(db, "exp_excel_monthly"), callback_data="export_monthly")],
        [InlineKeyboardButton(text=translate(db, "exp_excel_all"), callback_data="export_all")],
        [InlineKeyboardButton(text=translate(db, "btn_back"), callback_data="set_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_keyword_type_kb(db=None):
    if not db: db = SessionLocal()
    kb = [
        [InlineKeyboardButton(text=translate(db, "kw_type_search"), callback_data="kw_type_search")],
        [InlineKeyboardButton(text=translate(db, "kw_type_black"), callback_data="kw_type_black")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_archive_kb(db):
    kb = [
        [InlineKeyboardButton(text=translate(db, "arch_today"), callback_data="arch_today")],
        [InlineKeyboardButton(text=translate(db, "arch_yesterday"), callback_data="arch_yesterday")],
        [InlineKeyboardButton(text=translate(db, "arch_3days"), callback_data="arch_3days")],
        [InlineKeyboardButton(text=translate(db, "arch_by_date"), callback_data="arch_hint")],
        [InlineKeyboardButton(text=translate(db, "arch_export_excel"), callback_data="arch_export")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_cancel_kb(db=None):
    if not db: db = SessionLocal()
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=translate(db, "btn_cancel"))]],
        resize_keyboard=True
    )

# --- Handlers ---

async def _append_lot_winner_section(
    db,
    text: str,
    data: dict,
    trade_id: int | None,
    db_tender: Tender | None = None,
) -> str:
    """If lot is finalized, append winner block from DealsList."""
    if not trade_id:
        return text
    from app.services.lot_winner_lookup import (
        is_lot_finalized,
        lookup_winner_for_trade,
        format_winner_amount,
    )

    status_id = data.get("status_id")
    if status_id is not None:
        try:
            status_id = int(status_id)
        except (TypeError, ValueError):
            status_id = None

    if not is_lot_finalized(data.get("status"), status_id):
        deal_st = data.get("deal_status")
        if not deal_st or not is_lot_finalized(str(deal_st), None):
            return text

    winner = await lookup_winner_for_trade(trade_id, db_tender)
    text += "\n━━━━━━━━━━━━━━━━━━\n"
    if winner:
        text += f"{translate(db, 'lot_winner_header')}\n\n"
        text += f"{translate(db, 'lot_winner_name')} {winner['company_name']}\n"
        if winner.get("inn"):
            text += f"{translate(db, 'lot_winner_inn')} <code>{winner['inn']}</code>\n"
        if winner.get("amount"):
            text += (
                f"{translate(db, 'lot_winner_sum')} "
                f"<code>{format_winner_amount(winner['amount'])}</code>\n"
            )
        phone = winner.get("phone")
        if phone:
            p = str(phone).strip()
            if p.isdigit() and len(p) == 9:
                p = f"+998 {p}"
            elif p.isdigit() and len(p) == 12 and p.startswith("998"):
                p = f"+{p}"
            text += f"{translate(db, 'lot_winner_phone')} {p}\n"
    else:
        text += f"{translate(db, 'lot_winner_not_found')}\n"
    text += "\n"
    return text


@dp.message(F.text.in_({"🏆 Победители", "🏆 G'oliblar"}))
async def cmd_winners_leaderboard(message: Message) -> None:
    db = SessionLocal()
    try:
        # Get top 10 winners by count of tenders won
        from sqlalchemy import func
        top_winners = db.query(
            Winner.company_name,
            Winner.company_inn,
            func.count(Winner.id).label('win_count')
        ).group_by(
            Winner.company_name,
            Winner.company_inn
        ).order_by(
            func.count(Winner.id).desc()
        ).limit(10).all()

        if not top_winners:
            await message.answer(translate(db, "winners_empty"), parse_mode="HTML")
            return

        text = translate(db, "winners_title")
        text += "━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, w in enumerate(top_winners, 1):
            inn_str = f" ({translate(db, 'tender_inn_label_short')}: {w.company_inn})" if w.company_inn else ""
            text += f"{i}. <b>{w.company_name}</b>{inn_str}\n"
            text += f"   └ {translate(db, 'winners_count_label')} <code>{w.win_count}</code>\n\n"
        
        text += translate(db, "winners_footer")
        
        await message.answer(text, parse_mode="HTML")
    finally:
        db.close()

@dp.message(Command("add_company"))
async def cmd_add_company(message: Message, command: CommandObject) -> None:
    db = SessionLocal()
    try:
        if not command.args:
            await message.answer(translate(db, "add_company_prompt"), parse_mode="HTML")
            return
        inn = normalize_inn(command.args.split()[0])
        if len(inn) != 9 or not inn.isdigit():
            await message.answer(translate(db, "add_company_invalid"), parse_mode="HTML")
            return
        name = " ".join(command.args.split()[1:]).strip() or None
        existing = db.query(MonitoredCompany).filter(MonitoredCompany.company_inn == inn).first()
        if existing:
            if name and not existing.company_name:
                existing.company_name = name
                db.commit()
            await message.answer(
                translate(db, "add_company_exists").format(inn=inn),
                parse_mode="HTML",
            )
            return
        profile = db.query(Winner).filter(Winner.company_inn == inn).first()
        if not name and profile:
            name = profile.company_name
        db.add(MonitoredCompany(company_inn=inn, company_name=name))
        db.commit()
        display = name or translate(db, "company_name_placeholder").format(inn=inn)
        await message.answer(
            translate(db, "add_company_ok").format(name=display, inn=inn),
            parse_mode="HTML",
        )
    except Exception as e:
        db.rollback()
        await message.answer(translate(db, "err_search").format(e=e))
    finally:
        db.close()


@dp.message(Command("companies"))
async def cmd_companies(message: Message) -> None:
    db = SessionLocal()
    try:
        items = (
            db.query(MonitoredCompany)
            .order_by(MonitoredCompany.created_at.desc())
            .limit(50)
            .all()
        )
        if not items:
            await message.answer(translate(db, "companies_empty"), parse_mode="HTML")
            return
        text = translate(db, "companies_list_title").format(count=len(items))
        for i, c in enumerate(items, 1):
            name = c.company_name or translate(db, "company_name_placeholder").format(inn=c.company_inn)
            text += f"{i}. <b>{name}</b>\n   INN: <code>{c.company_inn}</code>\n"
        await message.answer(text, parse_mode="HTML")
    finally:
        db.close()


@dp.message(Command("check_inn"))
async def cmd_check_inn(message: Message, command: CommandObject) -> None:
    db = SessionLocal()
    try:
        if not command.args:
            await message.answer(translate(db, "check_inn_prompt"), parse_mode="HTML")
            return
        
        query = command.args.strip()
        
        # Lot ID: short number or 14-digit display_no (same resolver as Excel export)
        from app.utils.uzex_trade_id import resolve_uzex_trade_id

        if query.isdigit() and (len(query) < 9 or len(query) >= 12):
            resolved = resolve_uzex_trade_id(query)
            search_id = str(resolved) if resolved is not None else query
                
            await message.answer(translate(db, "searching_lot").format(id=search_id), parse_mode="HTML")
            
            # 0. Сначала проверяем нашу локальную базу данных (для любых источников: xarid, etender, tender.mc, e-auksion)
            db_tender = db.query(Tender).filter(
                (Tender.external_id == search_id) | 
                (Tender.url.like(f"%/{search_id}%")) | 
                (Tender.url.like(f"%={search_id}%"))
            ).first()
            
            db_data = {}
            if db_tender:
                db_data = {
                    "source": db_tender.source,
                    "id": db_tender.external_id or search_id,
                    "title": db_tender.title,
                    "amount": db_tender.amount,
                    "region": db_tender.region,
                    "organizer": db_tender.organizer_name,
                    "organizer_inn": db_tender.organizer_inn,
                    "phone": db_tender.organizer_phone,
                    "email": db_tender.organizer_email,
                    "url": db_tender.url,
                }
            
            from app.services.lot_search_service import get_lot_search_service
            search_service = get_lot_search_service()
            
            # 1. Пробуем API (только для UZEX etender)
            api_data = await search_service.search_lot_everywhere(search_id)
            
            # 2. Пробуем скрапер только как резерв (только для UZEX etender)
            scraper_data = None
            if not api_data and (not db_tender or db_tender.source == "UZEX"):
                try:
                    scraper_data = await search_service.get_detailed_lot_info(search_id)
                except Exception:
                    pass
            
            # Объединяем данные: API имеет приоритет, затем скрапер, затем локальная БД
            if not api_data and not scraper_data and not db_data:
                await message.answer(translate(db, "lot_not_found").format(id=query), parse_mode="HTML")
                return
            
            # Мержим
            data = {}
            if db_data:
                data.update(db_data)
            if scraper_data:
                for key, val in scraper_data.items():
                    if val:
                        data[key] = val
            if api_data:
                for key, val in api_data.items():
                    if val:
                        data[key] = val
            
            # Форматирование телефона
            phone = data.get('phone') or translate(db, 'not_specified')
            if phone != translate(db, 'not_specified'):
                if phone.isdigit() and len(phone) == 9:
                    phone = f"+998 {phone}"
                elif phone.isdigit() and len(phone) == 12 and phone.startswith('998'):
                    phone = f"+{phone}"

            # Обогащение данных по ИНН заказчика
            organizer_data = None
            if data.get('organizer_inn'):
                try:
                    from app.services.company_enrichment_service import get_company_enrichment_service
                    enricher = get_company_enrichment_service()
                    organizer_data = await enricher.enrich_company(data['organizer_inn'], data.get('organizer') or translate(db, "tender_org").split()[-1])
                except Exception:
                    pass

            # Собираем все телефоны
            phones = []
            if phone and phone != translate(db, 'not_specified'):
                phones.append(phone)
            if organizer_data and organizer_data.phone_numbers:
                for p in organizer_data.phone_numbers:
                    fmt_p = f"+998 {p}" if (p.isdigit() and len(p) == 9) else p
                    if fmt_p not in phones:
                        phones.append(fmt_p)

            # Форматирование суммы
            amount_str = translate(db, "arch_price_request")
            raw_amount = data.get('amount')
            if raw_amount:
                try:
                    clean = "".join(c for c in str(raw_amount) if c.isdigit() or c == '.')
                    if clean:
                        amount_str = f"{float(clean):,.0f} UZS"
                except (ValueError, TypeError):
                    amount_str = str(raw_amount)

            # Адрес
            address = data.get('organizer_address') or (organizer_data.legal_address if organizer_data else None) or translate(db, 'not_specified')
            
            # Email
            email = data.get('email') or (', '.join(organizer_data.email_addresses) if organizer_data and organizer_data.email_addresses else None) or translate(db, 'not_specified')

            # --- Формируем сообщение ---
            text = translate(db, "lot_title").format(id=query)
            text += "━━━━━━━━━━━━━━━━━━\n\n"
            
            # Основная информация
            text += f"{translate(db, 'tender_obj')} {data.get('title') or '---'}\n"
            text += f"{translate(db, 'tender_org')} {data.get('organizer') or '---'}\n"
            text += f"{translate(db, 'tender_inn_label')} <code>{data.get('organizer_inn') or '---'}</code>\n"
            text += f"{translate(db, 'tender_sum')} <code>{amount_str}</code>\n"
            text += f"{translate(db, 'tender_reg')} {data.get('region') or '---'}\n"
            if data.get('languages'):
                text += f"{translate(db, 'tender_lang')} {data['languages']}\n"
            if data.get('status'):
                text += f"{translate(db, 'tender_status')} {data['status']}\n"
            text += "\n"
            
            # Контакты
            text += f"{translate(db, 'tender_phone')} {', '.join(phones) if phones else translate(db, 'not_specified')}\n"
            text += f"{translate(db, 'tender_email')} {email}\n"
            text += f"{translate(db, 'tender_addr')} {address}\n\n"
            
            # Условия
            text += f"{translate(db, 'tender_pay')} {data.get('payment_terms') or translate(db, 'not_specified')}\n"
            text += f"{translate(db, 'tender_deposit')} {data.get('deposit') or translate(db, 'not_specified')}\n"
            if data.get('registration_order'):
                text += f"{translate(db, 'tender_reg_order')} {data['registration_order']}\n"
            if data.get('placement_deadline'):
                text += f"{translate(db, 'tender_deadline')} {data['placement_deadline']}\n"
            text += "\n"
            
            # Описание (если есть)
            if data.get('extra_info'):
                desc_text = str(data['extra_info'])[:500]
                text += f"{translate(db, 'tender_desc')}\n<i>{desc_text}...</i>\n\n"

            trade_id = resolve_uzex_trade_id(search_id, data.get("url"))
            text = await _append_lot_winner_section(
                db, text, data, trade_id, db_tender
            )
            
            text += f"{translate(db, 'tender_source_label')}\n"
            text += f"🔗 <a href='{data.get('url')}'>{translate(db, 'tender_open')}</a>"
            
            await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
            return

        # Otherwise treat as INN
        inn = query
        await message.answer(translate(db, "searching_inn").format(inn=inn), parse_mode="HTML")
        
        # 1. Поиск тендеров по ИНН заказчика в базе данных
        tenders = db.query(Tender).filter(Tender.organizer_inn == inn).order_by(Tender.created_at.desc()).limit(5).all()
        
        # 2. Если в БД нет, пробуем UZEX API — ищем среди активных тендеров
        if not tenders:
            try:
                from app.clients.uzex_etender_api import UzexEtenderApiClient
                api = UzexEtenderApiClient()
                
                # Ищем в основных категориях: 1 (Тендер), 2 (Отбор)
                all_matching = []
                for type_id in [1, 2]:
                    try:
                        items = api.trade_list(type_id=type_id, from_=1, to=200, system_id=0)
                        if items:
                            matching = [it for it in items if it.seller_tin and str(it.seller_tin) == inn]
                            all_matching.extend(matching)
                    except Exception:
                        continue
                
                if all_matching:
                    from app.services.lot_search_service import get_lot_search_service
                    search_service = get_lot_search_service()
                    
                    for match_item in all_matching[:3]:
                        try:
                            api_data = await search_service.search_lot_everywhere(str(match_item.id))
                            scraper_data = None
                            if not api_data:
                                try:
                                    scraper_data = await search_service.get_detailed_lot_info(str(match_item.id))
                                except Exception:
                                    pass
                            
                            data = {}
                            if api_data:
                                data.update(api_data)
                            if scraper_data:
                                for key, val in scraper_data.items():
                                    if val and not data.get(key):
                                        data[key] = val
                            
                            if data.get('title'):
                                await _send_tender_detail(message, data, str(match_item.id))
                        except Exception:
                            pass
                    
                    # Также показать досье компании
                    await _send_company_dossier(message, inn)
                    api.close()
                    return
                api.close()
            except Exception:
                pass
        
        if tenders:
            text = translate(db, "inn_results_title").format(inn=inn)
            text += translate(db, "found_count").format(count=len(tenders))
            text += "━━━━━━━━━━━━━━━━━━\n\n"
            
            for i, tender in enumerate(tenders, 1):
                # Форматирование суммы
                amount_str = "По запросу"
                if tender.amount:
                    try:
                        clean = "".join(c for c in str(tender.amount) if c.isdigit() or c == '.')
                        if clean:
                            amount_str = f"{float(clean):,.0f} UZS"
                    except (ValueError, TypeError):
                        amount_str = tender.amount
                
                # Форматирование телефона
                phone = tender.organizer_phone or translate(db, 'not_specified')
                if phone != translate(db, 'not_specified') and phone.isdigit() and len(phone) == 9:
                    phone = f"+998 {phone}"
                
                text += f"<b>📦 {i}. {tender.title[:80]}</b>\n"
                text += f"{translate(db, 'tender_org')} {tender.organizer_name or '---'}\n"
                text += f"{translate(db, 'tender_sum')} <code>{amount_str}</code>\n"
                text += f"{translate(db, 'tender_reg')} {tender.region or '---'}\n"
                text += f"{translate(db, 'tender_phone')} {phone}\n"
                text += f"{translate(db, 'tender_email')} {tender.organizer_email or '---'}\n"
                text += f"🔗 <a href='{tender.url}'>{translate(db, 'tender_open')}</a>\n\n"
            
            await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
            
            # Также показываем досье компании
            await _send_company_dossier(message, inn)
        else:
            # 4. Нет тендеров — показать только досье
            await message.answer(translate(db, "not_found_db").format(inn=inn), parse_mode="HTML")
            await _send_company_dossier(message, inn, db)
    except Exception as e:
        await message.answer(translate(db, "err_search").format(e=e))
    finally:
        db.close()


async def _send_tender_detail(
    message: Message,
    data: dict,
    lot_id: str,
    db=None,
    db_tender: Tender | None = None,
):
    if not db: db = SessionLocal()
    """Отправить подробную информацию о тендере"""
    phone = data.get('phone') or '---'
    if phone != '---':
        if phone.isdigit() and len(phone) == 9:
            phone = f"+998 {phone}"
        elif phone.isdigit() and len(phone) == 12 and phone.startswith('998'):
            phone = f"+{phone}"

    amount_str = "---"
    raw_amount = data.get('amount')
    if raw_amount:
        try:
            clean = "".join(c for c in str(raw_amount) if c.isdigit() or c == '.')
            if clean:
                amount_str = f"{float(clean):,.0f} UZS"
        except (ValueError, TypeError):
            amount_str = str(raw_amount)

    text = translate(db, "lot_title").format(id=lot_id)
    text += "━━━━━━━━━━━━━━━━━━\n\n"
    text += f"{translate(db, 'tender_obj')} {data.get('title') or '---'}\n"
    text += f"{translate(db, 'tender_org')} {data.get('organizer') or '---'}\n"
    text += f"{translate(db, 'tender_inn_label')} <code>{data.get('organizer_inn') or '---'}</code>\n"
    text += f"{translate(db, 'tender_sum')} <code>{amount_str}</code>\n"
    text += f"{translate(db, 'tender_reg')} {data.get('region') or '---'}\n"
    if data.get('languages'):
        text += f"{translate(db, 'tender_lang')} {data['languages']}\n"
    if data.get('status'):
        text += f"{translate(db, 'tender_status')} {data['status']}\n"
    text += "\n"
    
    text += f"{translate(db, 'tender_phone')} {phone}\n"
    text += f"{translate(db, 'tender_email')} {data.get('email') or translate(db, 'not_specified')}\n"
    text += f"{translate(db, 'tender_addr')} {data.get('organizer_address') or translate(db, 'not_specified')}\n\n"
    
    text += f"{translate(db, 'tender_pay')} {data.get('payment_terms') or translate(db, 'not_specified')}\n"
    if data.get('registration_order'):
        text += f"{translate(db, 'tender_reg_order')} {data['registration_order']}\n"
    if data.get('placement_deadline'):
        text += f"{translate(db, 'tender_deadline')} {data['placement_deadline']}\n"
    text += "\n"

    from app.utils.uzex_trade_id import resolve_uzex_trade_id
    trade_id = resolve_uzex_trade_id(lot_id, data.get("url"))
    text = await _append_lot_winner_section(db, text, data, trade_id, db_tender)
    
    text += f"{translate(db, 'tender_source_label')}\n"
    text += f"🔗 <a href='{data.get('url')}'>{translate(db, 'tender_open')}</a>"
    
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

async def _send_company_dossier(message: Message, inn: str, db=None):
    if not db: db = SessionLocal()
    """Отправить досье компании по ИНН"""
    try:
        from app.services.company_enrichment_service import get_company_enrichment_service
        enricher = get_company_enrichment_service()
        from app.utils.inn import is_generic_company_label

        data = await enricher.enrich_company(inn)
        await enricher.upsert_enriched_data(data)
        display_name = data.company_name
        if is_generic_company_label(display_name, inn):
            from app.services.company_enrichment_service import lookup_company_name_in_db
            display_name = lookup_company_name_in_db(inn) or display_name

        text = translate(db, "dossier_title").format(inn=inn)
        text += "━━━━━━━━━━━━━━━━━━\n\n"
        text += f"{translate(db, 'dossier_company')} {display_name}\n"
        text += f"{translate(db, 'dossier_dir')} {data.director_name or '---'}\n"
        
        formatted_phones = []
        if data.phone_numbers:
            for p in data.phone_numbers:
                if p.isdigit() and len(p) == 9:
                    formatted_phones.append(f"+998 {p}")
                else:
                    formatted_phones.append(p)
        
        text += f"{translate(db, 'tender_phone')} {', '.join(formatted_phones) if formatted_phones else '---'}\n"
        text += f"{translate(db, 'tender_email')} {', '.join(data.email_addresses) if data.email_addresses else '---'}\n"
        text += f"{translate(db, 'tender_addr')} {data.legal_address or '---'}\n"
        text += f"{translate(db, 'dossier_act')} {', '.join(data.business_activities) if data.business_activities else '---'}\n\n"
        
        await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        import logging
        logging.error(f"Error sending dossier: {e}")

@dp.message(F.text.in_({"⚙️ Настройки", "⚙️ Sozlamalar"}))
async def cmd_settings(message: Message) -> None:
    db = SessionLocal()
    try:
        await message.answer(
            translate(db, "settings_title"),
            parse_mode="HTML",
            reply_markup=get_settings_kb(db)
        )
    finally:
        db.close()

@dp.callback_query(F.data == "set_back")
async def back_to_settings(callback: CallbackQuery) -> None:
    db = SessionLocal()
    try:
        await callback.message.edit_text(
            translate(db, "settings_title"),
            parse_mode="HTML",
            reply_markup=get_settings_kb(db)
        )
    finally:
        db.close()

@dp.callback_query(F.data == "set_lang")
async def show_lang_settings(callback: CallbackQuery):
    db = SessionLocal()
    try:
        await callback.message.edit_text(
            translate(db, "lang_select"),
            parse_mode="HTML",
            reply_markup=get_lang_kb(db)
        )
    finally:
        db.close()
    await callback.answer()

@dp.callback_query(F.data.startswith("lang_"))
async def process_lang_toggle(callback: CallbackQuery):
    lang_code = callback.data.split("_")[1]
    db = SessionLocal()
    try:
        setting = db.query(SystemSetting).filter(SystemSetting.key == "system_language").first()
        if not setting:
            setting = SystemSetting(key="system_language", value=lang_code)
            db.add(setting)
        else:
            setting.value = lang_code
        db.commit()
        
        lang_msg = "✅ Til o'zgartirildi / Язык изменен"
        await callback.message.edit_text(
            lang_msg,
            reply_markup=get_settings_kb(db)
        )
        await callback.message.answer(
            translate(db, "welcome"),
            parse_mode="HTML",
            reply_markup=get_main_menu(db)
        )
    finally:
        db.close()
    await callback.answer()

@dp.callback_query(F.data == "set_sources")
async def show_sources_settings(callback: CallbackQuery) -> None:
    db = SessionLocal()
    try:
        text = f"{translate(db, 'sources_title')}\n\n{translate(db, 'sources_hint')}"
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_sources_kb(db)
        )
    finally:
        db.close()

@dp.callback_query(F.data == "set_export")
async def show_export_settings(callback: CallbackQuery) -> None:
    db = SessionLocal()
    try:
        await callback.message.edit_text(
            translate(db, "exp_settings_title"),
            parse_mode="HTML",
            reply_markup=get_export_kb(db)
        )
    finally:
        db.close()

@dp.callback_query(F.data == "set_blacklist")
async def show_blacklist_settings(callback: CallbackQuery) -> None:
    db = SessionLocal()
    try:
        blacklist = db.query(Keyword).filter(Keyword.is_blacklist == True).all()
        if not blacklist:
            text = translate(db, "bl_empty")
        else:
            text = translate(db, "bl_title")
            for i, kw in enumerate(blacklist, 1):
                text += f"{i}. <code>{kw.phrase}</code>\n"
            text += f"\n{translate(db, 'kw_del_hint')}"
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=translate(db, "btn_back"), callback_data="set_back")]]))
    finally:
        db.close()

@dp.callback_query(F.data == "set_status")
async def show_status_settings(callback: CallbackQuery) -> None:
    await cmd_status(callback.message)
    await callback.answer()

@dp.callback_query(F.data.startswith("toggle_src_"))
async def toggle_source(callback: CallbackQuery) -> None:
    source_name = callback.data.replace("toggle_src_", "")
    db = SessionLocal()
    try:
        key = f"source_{source_name.lower()}"
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not setting:
            setting = SystemSetting(key=key, value="true", description=f"Enable/Disable {source_name}")
            db.add(setting)
        
        current = setting.value.lower() == "true"
        setting.value = "false" if current else "true"
        db.commit()
        
        await callback.message.edit_reply_markup(reply_markup=get_sources_kb(db))
        status = translate(db, "source_disabled") if current else translate(db, "source_enabled")
        await callback.answer(f"{source_name} {status}")
    finally:
        db.close()

@dp.callback_query(F.data == "toggle_exp_gs")
async def toggle_export_gs(callback: CallbackQuery) -> None:
    db = SessionLocal()
    try:
        key = "export_google_sheets"
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not setting:
            setting = SystemSetting(key=key, value=str(settings.GOOGLE_SHEETS_AUTO_EXPORT).lower(), description="Google Sheets Auto-Export")
            db.add(setting)
        
        current = setting.value.lower() == "true"
        setting.value = "false" if current else "true"
        db.commit()
        
        await callback.message.edit_reply_markup(reply_markup=get_export_kb(db))
        status = translate(db, "exp_gs_toggle_off") if current else translate(db, "exp_gs_toggle_on")
        await callback.answer(status)
    finally:
        db.close()


@dp.message(F.text.in_({"📺 Каналы", "📺 Kanallar"}))
async def cmd_channels(message: Message) -> None:
    db = SessionLocal()
    try:
        channels = db.query(TelegramChannel).filter(TelegramChannel.is_active == True).all()
        if not channels:
            await message.answer(
                translate(db, "chan_list_empty"),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=translate(db, "chan_add_btn"), callback_data="add_chan")]])
            )
            return

        text = translate(db, "chan_title") + "\n"
        text += "━━━━━━━━━━━━━━━━━━\n\n"
        for i, chan in enumerate(channels, 1):
            text += f"{i}. <code>{chan.username}</code>\n"
        
        text += f"\n{translate(db, 'chan_del_hint')}"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=translate(db, "chan_add_more"), callback_data="add_chan")]])
        await message.answer(text, parse_mode="HTML", reply_markup=kb)
    finally:
        db.close()


@dp.callback_query(F.data == "add_chan")
async def ask_add_channel(callback: CallbackQuery, state: FSMContext) -> None:
    db = SessionLocal()
    try:
        await state.set_state(AddChannelForm.waiting_for_username)
        await callback.message.answer(
            translate(db, "chan_add_prompt"),
            parse_mode="HTML",
            reply_markup=get_cancel_kb(db)
        )
    finally:
        db.close()
    await callback.answer()


@dp.message(AddChannelForm.waiting_for_username)
async def process_add_channel(message: Message, state: FSMContext) -> None:
    db = SessionLocal()
    try:
        if message.text == translate(db, "btn_cancel"):
            await state.clear()
            await message.answer(translate(db, "chan_cancel"), reply_markup=get_main_menu(db))
            return
        
        username = message.text.strip().replace("https://t.me/", "@")
        if not username.startswith("@"):
            username = "@" + username
            
        existing = db.query(TelegramChannel).filter(TelegramChannel.username.ilike(username)).first()
        if existing:
            await message.answer(translate(db, "chan_exists").format(username=username), parse_mode="HTML")
        else:
            new_chan = TelegramChannel(username=username, is_active=True)
            db.add(new_chan)
            db.commit()
            await message.answer(translate(db, "chan_added_success").format(username=username), parse_mode="HTML")
        
        await state.clear()
        await message.answer(translate(db, "menu_search") + ":", reply_markup=get_main_menu(db), parse_mode="HTML")
    finally:
        db.close()


@dp.message(Command("del_chan"))
async def cmd_del_chan(message: Message, command: CommandObject) -> None:
    db = SessionLocal()
    try:
        if not command.args:
            await message.answer(translate(db, "chan_del_prompt"), parse_mode="HTML")
            return
        
        username = command.args.strip()
        if not username.startswith("@"): username = "@" + username
        
        chan = db.query(TelegramChannel).filter(TelegramChannel.username.ilike(username)).first()
        if chan:
            db.delete(chan)
            db.commit()
            await message.answer(translate(db, "chan_del_success").format(username=username), parse_mode="HTML")
        else:
            await message.answer(translate(db, "chan_not_found"), parse_mode="HTML")
    finally:
        db.close()

@dp.message(F.text.in_({"📁 Архив", "📁 Arxiv"}))
async def cmd_archive_menu(message: Message) -> None:
    db = SessionLocal()
    try:
        await message.answer(
            translate(db, "arch_menu_title"),
            parse_mode="HTML",
            reply_markup=get_archive_kb(db)
        )
    finally:
        db.close()


@dp.callback_query(F.data == "arch_export")
async def show_export_menu(callback: CallbackQuery) -> None:
    db = SessionLocal()
    try:
        kb = [
            [InlineKeyboardButton(text=translate(db, "exp_excel_daily"), callback_data="export_daily")],
            [InlineKeyboardButton(text=translate(db, "exp_excel_weekly"), callback_data="export_weekly")],
            [InlineKeyboardButton(text=translate(db, "exp_excel_monthly"), callback_data="export_monthly")],
            [InlineKeyboardButton(text=translate(db, "exp_excel_all"), callback_data="export_all")],
            [InlineKeyboardButton(text=translate(db, "btn_back"), callback_data="arch_back")],
        ]
        await callback.message.edit_text(
            translate(db, "arch_export_title"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
    finally:
        db.close()


@dp.callback_query(F.data == "arch_back")
async def back_to_archive(callback: CallbackQuery) -> None:
    db = SessionLocal()
    try:
        await callback.message.edit_text(
            translate(db, "arch_menu_title"),
            parse_mode="HTML",
            reply_markup=get_archive_kb(db)
        )
    finally:
        db.close()


@dp.callback_query(F.data.startswith("arch_"))
async def process_archive_call(callback: CallbackQuery) -> None:
    db = SessionLocal()
    try:
        period = callback.data.split("_")[1]
        if period == "hint":
            await callback.answer(translate(db, "arch_date_hint"), show_alert=True)
            return
        now = datetime.now(timezone.utc)
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if period == "today":
            label = translate(db, "arch_label_today")
        elif period == "yesterday":
            start_date = start_date - timedelta(days=1)
            end_date = start_date + timedelta(days=1)
            label = translate(db, "arch_label_yesterday")
        elif period == "3days":
            start_date = start_date - timedelta(days=3)
            label = translate(db, "arch_label_3days")
        else:
            await callback.answer()
            return

        query = db.query(Tender).filter(Tender.created_at >= start_date)
        if period == "yesterday":
            query = query.filter(Tender.created_at < end_date)
            
        tenders = query.order_by(Tender.created_at.desc()).limit(10).all()
        
        if not tenders:
            await callback.message.edit_text(translate(db, "arch_empty_period").format(label=label), parse_mode="HTML")
            return

        text = f"{translate(db, 'arch_results_title').format(label=label)}\n━━━━━━━━━━━━━━━━━━\n\n"
        for tender in tenders:
            amount_str = translate(db, "arch_price_request")
            if tender.amount:
                try:
                    amount_val = float(tender.amount.replace(',', ''))
                    amount_str = f"{amount_val:,.0f} UZS"
                except:
                    amount_str = tender.amount
            text += f"📍 {tender.title[:60]}...\n💰 <code>{amount_str}</code> | <a href='{tender.url}'>{translate(db, 'arch_link')}</a>\n\n"
        
        await callback.message.edit_text(text, parse_mode="HTML", disable_web_page_preview=True)
    finally:
        db.close()


@dp.callback_query(F.data.startswith("export_"))
async def process_excel_export(callback: CallbackQuery) -> None:
    import time

    period = callback.data.split("_", 1)[1]
    db = SessionLocal()
    status_msg = None
    try:
        labels = {
            "daily": translate(db, "stats_today").split(":")[0],
            "weekly": translate(db, "stats_week").split(":")[0],
            "monthly": "Месяц" if get_lang(db) == "ru" else "Oy",
            "all": "Barchasi" if get_lang(db) == "uz" else "Все",
        }
        label = labels.get(period, period)

        await callback.answer()
        header = translate(db, "exp_excel_start").format(label=label)
        status_msg = await callback.message.answer(header, parse_mode="HTML")

        from app.services.winners_excel_export_service import WinnersExcelExportService

        last_edit = 0.0

        async def on_progress(detail: str) -> None:
            nonlocal last_edit
            now = time.monotonic()
            if now - last_edit < 3.5:
                return
            last_edit = now
            try:
                await status_msg.edit_text(
                    f"{header}\n\n{detail}",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        if period == "all":
            excel_data, filename, count, winners, api_filled = (
                await WinnersExcelExportService.build_all_winners_export(
                    on_progress=on_progress,
                )
            )
        else:
            excel_data, filename, count, winners, api_filled = (
                await WinnersExcelExportService.build_period_export(
                    period,
                    on_progress=on_progress,
                )
            )

        if not excel_data or count == 0:
            await status_msg.edit_text(translate(db, "exp_excel_empty"))
            return

        file = BufferedInputFile(excel_data, filename=filename)
        await callback.message.answer_document(
            file,
            caption=translate(db, "exp_excel_done").format(
                count=count, api=api_filled
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        if status_msg:
            await status_msg.edit_text(translate(db, "err_export").format(e=e), parse_mode="HTML")
        else:
            await callback.message.answer(translate(db, "err_export").format(e=e), parse_mode="HTML")
    finally:
        db.close()
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass


@dp.message(Command("date"))
async def cmd_date_search(message: Message, command: CommandObject) -> None:
    db = SessionLocal()
    try:
        if not command.args:
            await message.answer(translate(db, "date_prompt"), parse_mode="HTML")
            return
        
        date_str = command.args.strip()
        day, month = map(int, date_str.split('.'))
        year = datetime.now().year
        search_date = datetime(year, month, day)
        next_day = search_date + timedelta(days=1)
        
        tenders = db.query(Tender).filter(Tender.created_at >= search_date, Tender.created_at < next_day).limit(10).all()
        
        if not tenders:
            await message.answer(translate(db, "date_not_found").format(date_str=date_str), parse_mode="HTML")
            return

        text = f"{translate(db, 'date_results_title').format(date_str=date_str)}\n━━━━━━━━━━━━━━━━━━\n\n"
        for tender in tenders:
            text += f"📍 {tender.title[:60]}...\n🔗 <a href='{tender.url}'>{translate(db, 'arch_link')}</a>\n\n"
        
        await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception:
        await message.answer(translate(db, "date_invalid_fmt"))
    finally:
        db.close()




# --- Lot Search Handler ---
@dp.message(F.text.regexp(r'^\d+$'))
async def handle_lot_search(message: Message) -> None:
    db = SessionLocal()
    try:
        lot_id = message.text.strip()
        
        if len(lot_id) < 4:
            return
            
        await message.answer(translate(db, "lot_searching").format(lot_id=lot_id), parse_mode="HTML")
        
        from app.services.lot_search_service import get_lot_search_service
        search_service = get_lot_search_service()
        
        try:
            lot_data = await search_service.search_lot_everywhere(lot_id)
            
            if not lot_data:
                # If not a lot, maybe it's an INN? Let's try enrichment as fallback
                if len(lot_id) in [9, 14]:
                    await message.answer(translate(db, "lot_not_found_fallback").format(lot_id=lot_id))
                    return
                await message.answer(translate(db, "lot_not_found_err").format(lot_id=lot_id), parse_mode="HTML")
                return
                
            text = (
                f"<b>[{lot_data['source']}] | ID: {lot_data['id']}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"📦 {translate(db, 'tender_obj')} {lot_data['title']}\n"
                f"🏢 {translate(db, 'tender_org')} {lot_data['organizer']}\n"
                f"{translate(db, 'tender_inn_organizer')} <code>{lot_data['organizer_inn'] or '---'}</code>\n"
                f"💰 {translate(db, 'tender_sum')} <code>{lot_data['amount']}</code>\n"
                f"📍 {translate(db, 'tender_reg')} {lot_data['region'] or 'Узбекистан'}\n\n"
                
                f"💳 {translate(db, 'tender_pay')} {lot_data['payment_terms']}\n"
                f"{translate(db, 'tender_deposit')} {lot_data['deposit']}\n\n"
                
                f"{translate(db, 'tender_contacts_label')}\n"
                f"   └ {('+998 ' + lot_data['phone']) if (lot_data['phone'] and lot_data['phone'].isdigit() and len(lot_data['phone']) == 9) else (lot_data['phone'] or translate(db, 'not_specified'))}\n"
                f"   └ {lot_data['email'] or translate(db, 'not_specified')}\n\n"
                
                f"🔗 <a href='{lot_data['url']}'>{translate(db, 'tender_open')}</a>"
            )
            
            await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
            
        except Exception as e:
            await message.answer(translate(db, "err_search").format(e=e))
    finally:
        db.close()

@dp.message(F.text.in_({"📋 Ключевые слова", "📋 Kalit so'zlar"}))
@dp.message(Command("keywords"))
async def cmd_keywords(message: Message) -> None:
    db = SessionLocal()
    try:
        keywords = db.query(Keyword).filter(Keyword.is_active == True, Keyword.is_blacklist == False).all()
        blacklist = db.query(Keyword).filter(Keyword.is_active == True, Keyword.is_blacklist == True).all()
        
        text = translate(db, "kw_menu_title")
        text += "━━━━━━━━━━━━━━━━━━\n\n"
        
        if keywords:
            text += translate(db, "kw_search_list")
            for i, kw in enumerate(keywords, 1):
                text += f"{i}. <code>{kw.phrase}</code>\n"
            text += "\n"
        
        if blacklist:
            text += translate(db, "kw_black_list")
            for i, kw in enumerate(blacklist, 1):
                text += f"{i}. <code>{kw.phrase}</code>\n"
            text += "\n"
            
        if not keywords and not blacklist:
            text += translate(db, "kw_empty")
        else:
            text += translate(db, "kw_del_hint")
        
        await message.answer(text, parse_mode="HTML")
    finally:
        db.close()


@dp.message(Command("del"))
async def cmd_del(message: Message, command: CommandObject) -> None:
    db = SessionLocal()
    try:
        if not command.args:
            await message.answer(translate(db, "del_err"), parse_mode="HTML")
            return
        
        phrase = command.args.strip()
        kw = db.query(Keyword).filter(Keyword.phrase.ilike(phrase)).first()
        if kw:
            db.delete(kw)
            db.commit()
            await message.answer(translate(db, "del_success").format(phrase=phrase), parse_mode="HTML")
        else:
            await message.answer(translate(db, "del_not_found").format(phrase=phrase), parse_mode="HTML")
    finally:
        db.close()


@dp.message(F.text.in_({"📊 Статистика", "📊 Statistika"}))
@dp.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        count_today = db.query(Tender).filter(Tender.created_at >= today_start).count()
        count_week = db.query(Tender).filter(Tender.created_at >= week_start).count()
        total_keywords = db.query(Keyword).filter(Keyword.is_active == True).count()

        text = translate(db, "stats_title")
        text += "━━━━━━━━━━━━━━━━━━\n\n"
        text += translate(db, "stats_today").format(count=count_today)
        text += translate(db, "stats_week").format(count=count_week)
        text += translate(db, "stats_kw").format(count=total_keywords)
        text += translate(db, "stats_updated").format(time=datetime.now().strftime('%H:%M:%S'))
        
        await message.answer(text, parse_mode="HTML")
    finally:
        db.close()


@dp.message(F.text.in_({"🆕 Последние тендеры", "🆕 So'nggi tenderlar"}))
@dp.message(Command("last"))
async def cmd_last(message: Message) -> None:
    db = SessionLocal()
    try:
        tenders = db.query(Tender).order_by(Tender.created_at.desc()).limit(5).all()
        if not tenders:
            await message.answer(translate(db, "kw_empty"), parse_mode="HTML")
            return

        text = translate(db, "last_title")
        text += "━━━━━━━━━━━━━━━━━━\n\n"
        for t_obj in tenders:
            amount_str = "---"
            if t_obj.amount:
                try:
                    amount_val = float(str(t_obj.amount).replace(',', ''))
                    amount_str = f"{amount_val:,.0f} UZS"
                except:
                    amount_str = str(t_obj.amount)

            text += f"📍 <b>{t_obj.title[:70]}...</b>\n"
            text += f"💰 <code>{amount_str}</code> | 🔗 <a href='{t_obj.url}'>{translate(db, 'btn_open_short')}</a>\n\n"
        
        await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
    finally:
        db.close()


@dp.message(Command("help"))
@dp.message(F.text.in_({"🆘 Помощь", "🆘 Yordam"}))
async def cmd_help(message: Message) -> None:
    db = SessionLocal()
    try:
        text = translate(db, "help_title")
        text += translate(db, "help_search_cat")
        text += translate(db, "help_check_inn")
        text += translate(db, "help_add_company")
        text += translate(db, "help_companies")
        text += translate(db, "help_check_lot")
        text += translate(db, "help_search_btn")
        text += translate(db, "help_kw_cat")
        text += translate(db, "help_add_kw")
        text += translate(db, "help_kw_list")
        text += translate(db, "help_sys_cat")
        text += translate(db, "help_settings")
        text += translate(db, "help_stats")
        text += translate(db, "help_login")
        text += translate(db, "help_integrations")
        
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu(db))
    finally:
        db.close()


@dp.message(F.text.in_({"➕ Добавить слово", "➕ So'z qo'shish"}))
async def ask_add_keyword(message: Message, state: FSMContext) -> None:
    db = SessionLocal()
    try:
        await state.set_state(AddKeywordForm.waiting_for_phrase)
        await message.answer(
            translate(db, "kw_add_input"),
            parse_mode="HTML",
            reply_markup=get_cancel_kb(db)
        )
    finally:
        db.close()


@dp.message(AddKeywordForm.waiting_for_phrase, F.text == "❌ Отмена")
async def cancel_add(message: Message, state: FSMContext) -> None:
    db = SessionLocal()
    try:
        await state.clear()
        await message.answer(translate(db, "btn_back"), reply_markup=get_main_menu(db), parse_mode="HTML")
    finally:
        db.close()


@dp.message(AddKeywordForm.waiting_for_phrase)
async def process_form_keyword_phrase(message: Message, state: FSMContext) -> None:
    db = SessionLocal()
    try:
        if message.text.startswith('/'):
            await state.clear()
            await message.answer(translate(db, "kw_interrupted"), reply_markup=get_main_menu(db), parse_mode="HTML")
            return
        
        phrase = message.text.strip()
        await state.update_data(phrase=phrase)
        await state.set_state(AddKeywordForm.waiting_for_type)
        
        await message.answer(
            translate(db, "kw_type_select").format(phrase=phrase),
            parse_mode="HTML",
            reply_markup=get_keyword_type_kb(db)
        )
    finally:
        db.close()

@dp.callback_query(AddKeywordForm.waiting_for_type, F.data.startswith("kw_type_"))
async def process_keyword_type(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    phrase = data.get("phrase")
    is_blacklist = callback.data == "kw_type_black"
    
    await process_add_keyword(callback.message, phrase, is_blacklist)
    await state.clear()
    db = SessionLocal()
    try:
        await callback.message.answer(translate(db, "menu_search") + ":", reply_markup=get_main_menu(db), parse_mode="HTML")
    finally:
        db.close()
    await callback.answer()


@dp.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject) -> None:
    db = SessionLocal()
    try:
        if not command.args:
            await message.answer(translate(db, "del_err"), parse_mode="HTML")
            return
        
        await process_add_keyword(message, command.args.strip())
    finally:
        db.close()


async def process_add_keyword(message: Message, phrase: str, is_blacklist: bool = False):
    db = SessionLocal()
    try:
        existing = db.query(Keyword).filter(Keyword.phrase.ilike(phrase)).first()
        type_str = translate(db, "menu_keywords") if not is_blacklist else translate(db, "btn_blacklist")
        
        if existing:
            if not existing.is_active or existing.is_blacklist != is_blacklist:
                existing.is_active = True
                existing.is_blacklist = is_blacklist
                db.commit()
                await message.answer(translate(db, "kw_added").format(phrase=phrase, type=type_str), parse_mode="HTML")
            else:
                await message.answer(translate(db, "kw_active").format(phrase=phrase), parse_mode="HTML")
            return

        new_kw = Keyword(phrase=phrase, is_active=True, is_blacklist=is_blacklist)
        db.add(new_kw)
        db.commit()
        
        await message.answer(translate(db, "kw_success").format(phrase=phrase, type=type_str), parse_mode="HTML")
    finally:
        db.close()


@dp.message(Command("test_winners"))
async def cmd_test_winners(message: Message) -> None:
    db = SessionLocal()
    try:
        # Демо-данные для примера
        demo_winners = [
            {"name": "OOO 'BUILDING PRO'", "inn": "301234567", "wins": 15},
            {"name": "OOO 'AGRO CLUSTER'", "inn": "205443322", "wins": 12},
            {"name": "OOO 'CONSTRUCTION PLUS'", "inn": "309876543", "wins": 8},
        ]
        
        text = translate(db, "winners_title")
        text += "━━━━━━━━━━━━━━━━━━\n\n"
        for i, w in enumerate(demo_winners, 1):
            text += f"{i}. <b>{w['name']}</b>\n"
            text += f"   └ INN: <code>{w['inn']}</code> | {translate(db, 'winners_count_label')} <b>{w['wins']}</b> {translate(db, 'winners_times_label')}\n\n"
        
        await message.answer(text, parse_mode="HTML")
    finally:
        db.close()


@dp.message(Command("test_report"))
async def cmd_test_report(message: Message) -> None:
    db = SessionLocal()
    try:
        msg = (
            f"✅ <b>TEST REPORT</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🌐 <b>{translate(db, 'tender_org').split()[-1]}:</b> <b>DEMO_UZEX</b>\n"
            f"📥 {translate(db, 'found_count').strip()}: <b>3</b>\n"
            f"⏩ {translate(db, 'source_disabled').capitalize()}: 97\n"
            f"📦 {translate(db, 'menu_stats').split()[-1]}: 100\n"
            f"🕒 {translate(db, 'status_last_update').split()[-1]} {datetime.now().strftime('%H:%M:%S')}"
        )
        await message.answer(msg, parse_mode="HTML")
    finally:
        db.close()


@dp.message(F.text.in_({"⚙️ Статус системы", "⚙️ Tizim holati"}))
@dp.message(Command("status"))
async def cmd_status(message: Message) -> None:
    db = SessionLocal()
    try:
        last_log = db.query(ParserLog).order_by(ParserLog.started_at.desc()).first()
        
        text = f"{translate(db, 'status_platform')}\n"
        text += "━━━━━━━━━━━━━━━━━━\n\n"
        text += f"{translate(db, 'status_mon')} {translate(db, 'status_mon_active')}\n"
        text += f"{translate(db, 'status_db_label')} {translate(db, 'status_db_online')}\n\n"
        
        if last_log:
            time_str = last_log.started_at.strftime("%H:%M:%S %d.%m")
            text += f"{translate(db, 'status_last_update')} <code>{time_str}</code>\n"
            text += f"{translate(db, 'status_parser_label')} <b>{last_log.status.upper()}</b>\n"
            if last_log.items_found:
                text += f"{translate(db, 'status_found_lots')} <b>{last_log.items_found}</b>"
        
        await message.answer(text, parse_mode="HTML")
    finally:
        db.close()


def main() -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is empty")
        raise RuntimeError("TELEGRAM_BOT_TOKEN is empty")

    if settings.TELEGRAM_PROXY_URL:
        from aiogram.client.session.aiohttp import AiohttpSession
        session = AiohttpSession(proxy=settings.TELEGRAM_PROXY_URL)
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, session=session)
    else:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    logger.info("Starting bot polling...")

    async def runner() -> None:
        await dp.start_polling(bot)

    asyncio.run(runner())


if __name__ == "__main__":
    main()

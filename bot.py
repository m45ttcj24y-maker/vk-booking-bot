import vk_api
import time
import json
import os
import threading
from datetime import datetime, timedelta
from config import GROUP_TOKEN, GROUP_ID

vk = vk_api.VkApi(token=GROUP_TOKEN).get_api()
BOT_ID = int(GROUP_ID)
BUSINESS_ID = str(GROUP_ID)

# ========== ФАЙЛЫ ==========
DATA_FOLDER = f"data_{BUSINESS_ID}"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

SETTINGS_FILE = f"{DATA_FOLDER}/settings.json"
SERVICES_FILE = f"{DATA_FOLDER}/services.json"
BOOKINGS_FILE = f"{DATA_FOLDER}/bookings.json"

def load_json(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Загружаем данные
settings = load_json(SETTINGS_FILE)
services = load_json(SERVICES_FILE)
bookings = load_json(BOOKINGS_FILE)

# Настройки по умолчанию
if not settings:
    settings = {
        "business_name": "Мой бизнес",
        "address": "",
        "phone": "",
        "work_hours": "10:00 - 19:00",
        "reminder_enabled": True,
        "reminder_minutes": 60,
        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_json(SETTINGS_FILE, settings)

if not services:
    services = []
    save_json(SERVICES_FILE, services)

if not bookings:
    bookings = []
    save_json(BOOKINGS_FILE, bookings)

# ========== ФУНКЦИЯ ОТПРАВКИ ==========
def send(user_id, text, kb=None, photo=None):
    try:
        if photo:
            vk.messages.send(user_id=user_id, message=text, attachment=photo, random_id=int(time.time()*1000))
        elif kb:
            vk.messages.send(user_id=user_id, message=text, keyboard=json.dumps(kb), random_id=int(time.time()*1000))
        else:
            vk.messages.send(user_id=user_id, message=text, random_id=int(time.time()*1000))
    except Exception as e:
        print(f"Ошибка: {e}")

# ========== НАПОМИНАНИЯ ==========
def reminder_checker():
    while True:
        try:
            current_bookings = load_json(BOOKINGS_FILE)
            for booking in current_bookings:
                if booking.get('reminded', False):
                    continue
                if booking.get('status') != 'confirmed':
                    continue
                try:
                    booking_time = datetime.strptime(booking['datetime'], "%Y-%m-%d %H:%M")
                    diff_minutes = (booking_time - datetime.now()).total_seconds() / 60
                    reminder_minutes = settings.get('reminder_minutes', 60)
                    if settings.get('reminder_enabled', True) and 0 < diff_minutes <= reminder_minutes:
                        reminder_text = f"🔔 НАПОМИНАНИЕ 🔔\n\nВы записаны на:\n📋 {booking['service']}\n📅 {booking['datetime']}\n🏢 {settings.get('business_name', 'Бизнес')}\n\nЖдем вас!"
                        send(booking['client_id'], reminder_text)
                        booking['reminded'] = True
                        save_json(BOOKINGS_FILE, current_bookings)
                        print(f"📨 Напоминание отправлено")
                except:
                    pass
            time.sleep(60)
        except:
            time.sleep(60)

reminder_thread = threading.Thread(target=reminder_checker, daemon=True)
reminder_thread.start()

# ========== КНОПКИ ==========

# 1. ГЛАВНОЕ МЕНЮ (КЛИЕНТ)
def main_menu():
    return {
        "buttons": [
            [{"action": {"type": "text", "label": "📋 Услуги и цены"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "📅 Записаться"}, "color": "positive"}],
            [{"action": {"type": "text", "label": "📝 Мои записи"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "ℹ️ О нас"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "⚙️ Настройки"}, "color": "secondary"}]
        ],
        "inline": False
    }

# 2. МЕНЮ УСЛУГ
def services_menu():
    buttons = []
    for s in services:
        buttons.append([{"action": {"type": "text", "label": f"📋 {s['name']} - {s['price']}₽"}, "color": "primary"}])
    buttons.append([{"action": {"type": "text", "label": "🔙 Назад"}, "color": "negative"}])
    return {"buttons": buttons, "inline": False}

# 3. МЕНЮ ДАТ (7 дней)
def date_menu():
    buttons = []
    row = []
    today = datetime.now()
    for i in range(7):
        date = today + timedelta(days=i)
        day_name = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"][date.weekday()]
        label = f"{date.day:02d}.{date.month:02d} ({day_name})"
        row.append({"action": {"type": "text", "label": label}, "color": "primary"})
        if len(row) == 2 or i == 6:
            buttons.append(row)
            row = []
    buttons.append([{"action": {"type": "text", "label": "🔙 Назад"}, "color": "negative"}])
    return {"buttons": buttons, "inline": False}

# 4. МЕНЮ ВРЕМЕНИ
def time_menu():
    hours = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"]
    buttons = []
    row = []
    for i, h in enumerate(hours):
        row.append({"action": {"type": "text", "label": h}, "color": "primary"})
        if len(row) == 3 or i == len(hours)-1:
            buttons.append(row)
            row = []
    buttons.append([{"action": {"type": "text", "label": "🔙 Назад"}, "color": "negative"}])
    return {"buttons": buttons, "inline": False}

# 5. МЕНЮ НАСТРОЕК (ВЛАДЕЛЕЦ)
def settings_menu():
    return {
        "buttons": [
            [{"action": {"type": "text", "label": "📝 Название бизнеса"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "📍 Адрес и телефон"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "⏰ Часы работы"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "➕ Добавить услугу"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "✏️ Удалить услугу"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "📋 Все записи"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "🔔 Напоминания"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "🔙 Назад"}, "color": "negative"}]
        ],
        "inline": False
    }

# 6. МЕНЮ УДАЛЕНИЯ УСЛУГ
def delete_service_menu():
    buttons = []
    for s in services:
        buttons.append([{"action": {"type": "text", "label": f"❌ {s['name']}"}, "color": "secondary"}])
    buttons.append([{"action": {"type": "text", "label": "🔙 Назад"}, "color": "negative"}])
    return {"buttons": buttons, "inline": False}

# 7. МЕНЮ НАПОМИНАНИЙ
def reminder_menu():
    status = "ВКЛ" if settings.get('reminder_enabled', True) else "ВЫКЛ"
    return {
        "buttons": [
            [{"action": {"type": "text", "label": f"🔔 {'Выключить' if settings.get('reminder_enabled', True) else 'Включить'} напоминания"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "⏰ За сколько минут"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "🔙 Назад"}, "color": "negative"}]
        ],
        "inline": False
    }

# 8. КНОПКИ ДЛЯ ЗАПИСЕЙ КЛИЕНТА
def my_bookings_menu(bookings_list):
    buttons = []
    for i, b in enumerate(bookings_list):
        if b['status'] == 'pending':
            buttons.append([{"action": {"type": "text", "label": f"❌ Отменить #{i+1}"}, "color": "negative"}])
    buttons.append([{"action": {"type": "text", "label": "🔙 Назад"}, "color": "secondary"}])
    return {"buttons": buttons, "inline": False}

# 9. КНОПКИ ДЛЯ ПОДТВЕРЖДЕНИЯ ЗАПИСИ (ВЛАДЕЛЕЦ)
def confirm_booking_menu(booking_num):
    return {
        "buttons": [
            [{"action": {"type": "text", "label": f"✅ Подтвердить #{booking_num}"}, "color": "positive"}],
            [{"action": {"type": "text", "label": f"❌ Отменить #{booking_num}"}, "color": "negative"}],
            [{"action": {"type": "text", "label": "🔙 Назад"}, "color": "secondary"}]
        ],
        "inline": True
    }

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_client_bookings(client_id):
    return [b for b in bookings if b['client_id'] == client_id]

def cancel_booking(client_id, booking_idx):
    for i, b in enumerate(bookings):
        if b['client_id'] == client_id and i == booking_idx:
            bookings.pop(i)
            save_json(BOOKINGS_FILE, bookings)
            send(client_id, f"❌ Запись на {b['service']} ({b['datetime']}) ОТМЕНЕНА!", main_menu())
            send(BOT_ID, f"❌ Клиент отменил запись!\n\nУслуга: {b['service']}\nВремя: {b['datetime']}")
            return True
    return False

print("=" * 50)
print(f"✅ БОТ ЗАПУЩЕН")
print(f"🏢 {settings.get('business_name', 'Мой бизнес')}")
print(f"📁 Папка данных: {DATA_FOLDER}")
print("=" * 50)

last_msg_id = {}
user_step = {}
user_service = {}
user_date = {}

while True:
    try:
        dialogs = vk.messages.getConversations(count=20, group_id=GROUP_ID)
        
        for dialog in dialogs['items']:
            uid = dialog['conversation']['peer']['id']
            
            if uid == BOT_ID:
                continue
            
            history = vk.messages.getHistory(user_id=uid, count=1, group_id=GROUP_ID)
            
            if history['items']:
                msg = history['items'][0]
                current_id = msg['id']
                text = msg['text'].strip()
                
                # Пропускаем сообщения от бота
                if text.startswith("✅") or text.startswith("🔔") or text.startswith("❌") or text.startswith("📋") or text.startswith("📍") or text.startswith("⏰") or "Бот работает" in text:
                    continue
                
                if uid in last_msg_id and last_msg_id[uid] >= current_id:
                    continue
                
                last_msg_id[uid] = current_id
                print(f"\n📩 {uid}: {text}")
                
                # ========== ОБРАБОТКА ШАГОВ ==========
                
                # Шаг: Ожидание названия бизнеса
                if user_step.get(uid) == "change_name":
                    if text and text != "🔙 Назад":
                        settings['business_name'] = text
                        save_json(SETTINGS_FILE, settings)
                        send(uid, f"✅ Название изменено на: {text}", settings_menu())
                    user_step.pop(uid, None)
                    continue
                
                # Шаг: Ожидание адреса и телефона
                if user_step.get(uid) == "change_contacts":
                    if text and text != "🔙 Назад":
                        try:
                            parts = text.split("|")
                            if len(parts) >= 2:
                                settings['address'] = parts[0].strip()
                                settings['phone'] = parts[1].strip()
                                save_json(SETTINGS_FILE, settings)
                                send(uid, f"✅ Контакты обновлены!\n📍 {settings['address']}\n📞 {settings['phone']}", settings_menu())
                            else:
                                send(uid, "❌ Формат: Адрес|Телефон", settings_menu())
                        except:
                            send(uid, "❌ Ошибка! Формат: Адрес|Телефон", settings_menu())
                    user_step.pop(uid, None)
                    continue
                
                # Шаг: Ожидание часов работы
                if user_step.get(uid) == "change_hours":
                    if text and text != "🔙 Назад":
                        settings['work_hours'] = text
                        save_json(SETTINGS_FILE, settings)
                        send(uid, f"✅ Часы работы: {text}", settings_menu())
                    user_step.pop(uid, None)
                    continue
                
                # Шаг: Ожидание добавления услуги
                if user_step.get(uid) == "add_service":
                    if text and text != "🔙 Назад":
                        try:
                            parts = text.split("|")
                            if len(parts) >= 3:
                                new_service = {
                                    "name": parts[0].strip(),
                                    "price": int(parts[1]),
                                    "duration": int(parts[2])
                                }
                                services.append(new_service)
                                save_json(SERVICES_FILE, services)
                                send(uid, f"✅ Услуга '{new_service['name']}' добавлена!\nЦена: {new_service['price']}₽\nВремя: {new_service['duration']} мин", settings_menu())
                            else:
                                send(uid, "❌ ФОРМАТ: Название|Цена|Время\n\nПример:\nМаникюр|1200|60", settings_menu())
                        except:
                            send(uid, "❌ ОШИБКА!\n\nПример: Маникюр|1200|60", settings_menu())
                    user_step.pop(uid, None)
                    continue
                
                # Шаг: Ожидание удаления услуги
                if user_step.get(uid) == "delete_service":
                    if text and text != "🔙 Назад":
                        service_name = text.replace("❌ ", "").strip()
                        for i, s in enumerate(services):
                            if s['name'] == service_name:
                                services.pop(i)
                                save_json(SERVICES_FILE, services)
                                send(uid, f"✅ Услуга '{service_name}' удалена!", settings_menu())
                                break
                    user_step.pop(uid, None)
                    continue
                
                # Шаг: Ожидание минут для напоминания
                if user_step.get(uid) == "set_reminder_minutes":
                    if text and text != "🔙 Назад":
                        try:
                            minutes = int(text)
                            if 10 <= minutes <= 1440:
                                settings['reminder_minutes'] = minutes
                                save_json(SETTINGS_FILE, settings)
                                send(uid, f"✅ Напоминания будут приходить за {minutes} минут до записи!", reminder_menu())
                            else:
                                send(uid, "❌ Введите число от 10 до 1440", reminder_menu())
                        except:
                            send(uid, "❌ Введите число минут!\n\nПример: 60", reminder_menu())
                    user_step.pop(uid, None)
                    continue
                
                # ========== КЛИЕНТЫ ==========
                
                # Шаг: Выбор времени
                if user_step.get(uid) == "waiting_time":
                    if text in ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"]:
                        selected_date = user_date.get(uid, datetime.now().strftime("%Y-%m-%d"))
                        booking = {
                            "client_id": uid,
                            "service": user_service.get(uid, "Неизвестно"),
                            "datetime": f"{selected_date} {text}",
                            "status": "pending",
                            "reminded": False,
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        bookings.append(booking)
                        save_json(BOOKINGS_FILE, bookings)
                        
                        send(uid, f"✅ ЗАПИСЬ СОЗДАНА!\n\n📋 {booking['service']}\n📅 {booking['datetime']}\n🏢 {settings.get('business_name', 'Бизнес')}\n\nОжидайте подтверждения.", main_menu())
                        send(BOT_ID, f"🆕 НОВАЯ ЗАПИСЬ!\n\n📋 {booking['service']}\n📅 {booking['datetime']}\n👤 Клиент: {uid}")
                        
                        user_step.pop(uid, None)
                        user_service.pop(uid, None)
                        user_date.pop(uid, None)
                    else:
                        send(uid, "❌ Выберите время из кнопок:", time_menu())
                    continue
                
                # Шаг: Выбор даты
                if user_step.get(uid) == "waiting_date":
                    today = datetime.now()
                    found = False
                    for i in range(7):
                        date = today + timedelta(days=i)
                        day_name = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"][date.weekday()]
                        label = f"{date.day:02d}.{date.month:02d} ({day_name})"
                        if label == text:
                            user_date[uid] = date.strftime("%Y-%m-%d")
                            found = True
                            break
                    if found:
                        user_step[uid] = "waiting_time"
                        send(uid, "✅ ВЫБЕРИТЕ ВРЕМЯ:", time_menu())
                    else:
                        send(uid, "❌ Выберите дату из кнопок:", date_menu())
                    continue
                
                # Шаг: Выбор услуги
                if user_step.get(uid) == "waiting_service":
                    selected = None
                    for s in services:
                        if text.startswith(f"📋 {s['name']} - {s['price']}₽"):
                            selected = s
                            break
                    if selected:
                        user_service[uid] = selected['name']
                        user_step[uid] = "waiting_date"
                        send(uid, "📅 ВЫБЕРИТЕ ДАТУ:", date_menu())
                    else:
                        send(uid, "❌ Выберите услугу из кнопок:", services_menu())
                    continue
                
                # ========== ОСНОВНЫЕ КОМАНДЫ ==========
                
                # Назад
                if text == "🔙 Назад":
                    user_step.pop(uid, None)
                    user_service.pop(uid, None)
                    user_date.pop(uid, None)
                    send(uid, f"🔹 {settings.get('business_name', 'ГЛАВНОЕ МЕНЮ')}", main_menu())
                    continue
                
                # Главное меню (клиент)
                if text.lower() in ["меню", "привет", "начать", "старт"]:
                    send(uid, f"🔹 {settings.get('business_name', 'ДОБРО ПОЖАЛОВАТЬ')} 🔹\n\nВыберите действие:", main_menu())
                    continue
                
                # 📋 Услуги и цены
                if text == "📋 Услуги и цены":
                    if not services:
                        send(uid, "❌ УСЛУГИ ЕЩЕ НЕ ДОБАВЛЕНЫ\n\nЗагляните позже!", main_menu())
                    else:
                        txt = f"💰 {settings.get('business_name', 'УСЛУГИ')} 💰\n\n"
                        for s in services:
                            txt += f"📋 {s['name']} — {s['price']}₽ ({s['duration']} мин)\n"
                        send(uid, txt, main_menu())
                
                # 📅 Записаться
                if text == "📅 Записаться":
                    if not services:
                        send(uid, "❌ УСЛУГИ ЕЩЕ НЕ ДОБАВЛЕНЫ\n\nЗагляните позже!", main_menu())
                    else:
                        user_step[uid] = "waiting_service"
                        send(uid, "💅 ВЫБЕРИТЕ УСЛУГУ:", services_menu())
                
                # 📝 Мои записи
                if text == "📝 Мои записи":
                    client_bookings = get_client_bookings(uid)
                    if not client_bookings:
                        send(uid, "📭 У ВАС НЕТ АКТИВНЫХ ЗАПИСЕЙ", main_menu())
                    else:
                        txt = "📋 ВАШИ ЗАПИСИ:\n\n"
                        for i, b in enumerate(client_bookings, 1):
                            status = "⏳ Ожидает" if b['status'] == 'pending' else "✅ Подтверждено"
                            reminded = "🔔" if b.get('reminded', False) else ""
                            txt += f"{i}. {b['service']}\n   📅 {b['datetime']}\n   {status} {reminded}\n\n"
                        send(uid, txt, my_bookings_menu(client_bookings))
                
                # ❌ Отменить запись
                if text.startswith("❌ Отменить #"):
                    try:
                        num = int(text.split("#")[1])
                        if cancel_booking(uid, num-1):
                            send(uid, "✅ ЗАПИСЬ ОТМЕНЕНА!", main_menu())
                        else:
                            send(uid, "❌ ЗАПИСЬ НЕ НАЙДЕНА", main_menu())
                    except:
                        send(uid, "❌ ОШИБКА ОТМЕНЫ", main_menu())
                    continue
                
                # ℹ️ О нас
                if text == "ℹ️ О нас":
                    info = f"🏢 {settings.get('business_name', 'Бизнес')}\n\n📍 {settings.get('address', 'Адрес не указан')}\n📞 {settings.get('phone', 'Телефон не указан')}\n⏰ {settings.get('work_hours', '10:00 - 19:00')}"
                    send(uid, info, main_menu())
                
                # ⚙️ Настройки (только для владельца)
                if text == "⚙️ Настройки":
                    if uid == BOT_ID:
                        send(uid, "⚙️ НАСТРОЙКИ БИЗНЕСА", settings_menu())
                    else:
                        send(uid, "⛔ ЭТОТ РАЗДЕЛ ТОЛЬКО ДЛЯ ВЛАДЕЛЬЦА БИЗНЕСА", main_menu())
                
                # ========== ВЛАДЕЛЕЦ БИЗНЕСА (UID = BOT_ID) ==========
                
                if uid == BOT_ID:
                    
                    # 📝 Название бизнеса
                    if text == "📝 Название бизнеса":
                        user_step[uid] = "change_name"
                        send(uid, f"📝 Введите новое название (сейчас: {settings.get('business_name', 'Мой бизнес')}):", settings_menu())
                    
                    # 📍 Адрес и телефон
                    if text == "📍 Адрес и телефон":
                        user_step[uid] = "change_contacts"
                        current_addr = settings.get('address', 'не указан')
                        current_phone = settings.get('phone', 'не указан')
                        send(uid, f"📍 ТЕКУЩИЕ КОНТАКТЫ:\nАдрес: {current_addr}\nТелефон: {current_phone}\n\nВведите новые в формате:\nАдрес|Телефон\n\nПример:\nул. Ленина 10|+7(999)123-45-67", settings_menu())
                    
                    # ⏰ Часы работы
                    if text == "⏰ Часы работы":
                        user_step[uid] = "change_hours"
                        send(uid, f"⏰ ТЕКУЩИЕ ЧАСЫ: {settings.get('work_hours', '10:00 - 19:00')}\n\nВведите новые часы работы:\nПример: 09:00 - 21:00", settings_menu())
                    
                    # ➕ Добавить услугу
                    if text == "➕ Добавить услугу":
                        user_step[uid] = "add_service"
                        send(uid, "➕ ДОБАВЛЕНИЕ УСЛУГИ\n\nВведите в формате:\nНАЗВАНИЕ|ЦЕНА|ВРЕМЯ\n\nПримеры:\nМаникюр|1200|60\nРемонт двигателя|5000|120\nКонсультация врача|2500|60", settings_menu())
                    
                    # ✏️ Удалить услугу
                    if text == "✏️ Удалить услугу":
                        if not services:
                            send(uid, "❌ НЕТ УСЛУГ ДЛЯ УДАЛЕНИЯ", settings_menu())
                        else:
                            txt = "🗑 ВЫБЕРИТЕ УСЛУГУ ДЛЯ УДАЛЕНИЯ:\n\n"
                            for s in services:
                                txt += f"• {s['name']} — {s['price']}₽\n"
                            send(uid, txt, delete_service_menu())
                            user_step[uid] = "delete_service"
                    
                    # 📋 Все записи
                    if text == "📋 Все записи":
                        if not bookings:
                            send(uid, "📭 НЕТ ЗАПИСЕЙ", settings_menu())
                        else:
                            send(uid, f"📋 ВСЕ ЗАПИСИ ({len(bookings)}):\n")
                            for i, b in enumerate(bookings, 1):
                                status = "⏳ Ожидает" if b['status'] == 'pending' else "✅ Подтверждено"
                                reminded = "🔔" if b.get('reminded', False) else ""
                                send(uid, f"{i}. {b['service']}\n   📅 {b['datetime']}\n   {status} {reminded}\n   👤 Клиент: {b['client_id']}")
                                if b['status'] == 'pending':
                                    send(uid, f"➡️ ДЕЙСТВИЯ С ЗАПИСЬЮ #{i}:", confirm_booking_menu(i))
                    
                    # 🔔 Напоминания
                    if text == "🔔 Напоминания":
                        send(uid, f"🔔 НАСТРОЙКИ НАПОМИНАНИЙ 🔔\n\nТекущий статус: {'ВКЛЮЧЕНЫ' if settings.get('reminder_enabled', True) else 'ВЫКЛЮЧЕНЫ'}\nПриходят за {settings.get('reminder_minutes', 60)} минут до записи", reminder_menu())
                    
                    # Включить/Выключить напоминания
                    if text == f"🔔 {'Выключить' if settings.get('reminder_enabled', True) else 'Включить'} напоминания":
                        settings['reminder_enabled'] = not settings.get('reminder_enabled', True)
                        save_json(SETTINGS_FILE, settings)
                        status = "ВКЛЮЧЕНЫ" if settings['reminder_enabled'] else "ВЫКЛЮЧЕНЫ"
                        send(uid, f"✅ НАПОМИНАНИЯ {status}!", reminder_menu())
                    
                    # ⏰ За сколько минут
                    if text == "⏰ За сколько минут":
                        user_step[uid] = "set_reminder_minutes"
                        send(uid, f"⏰ ТЕКУЩЕЕ ЗНАЧЕНИЕ: {settings.get('reminder_minutes', 60)} минут\n\nВведите новое значение (от 10 до 1440 минут):\n\nПримеры:\n60 - за час\n30 - за полчаса\n120 - за 2 часа", reminder_menu())
                    
                    # ✅ Подтвердить запись
                    if text.startswith("✅ Подтвердить #"):
                        try:
                            num = int(text.split("#")[1])
                            if 0 <= num-1 < len(bookings):
                                bookings[num-1]['status'] = 'confirmed'
                                save_json(BOOKINGS_FILE, bookings)
                                b = bookings[num-1]
                                send(uid, f"✅ ЗАПИСЬ ПОДТВЕРЖДЕНА!\n\n{b['service']}\n{b['datetime']}", settings_menu())
                                send(b['client_id'], f"✅ ВАША ЗАПИСЬ ПОДТВЕРЖДЕНА!\n\n📋 {b['service']}\n📅 {b['datetime']}\n🏢 {settings.get('business_name', 'Бизнес')}\n\nЖдем вас!")
                        except:
                            send(uid, "❌ ОШИБКА ПОДТВЕРЖДЕНИЯ", settings_menu())
                    
                    # ❌ Отменить запись (владелец)
                    if text.startswith("❌ Отменить #"):
                        try:
                            num = int(text.split("#")[1])
                            if 0 <= num-1 < len(bookings):
                                b = bookings.pop(num-1)
                                save_json(BOOKINGS_FILE, bookings)
                                send(uid, f"❌ ЗАПИСЬ ОТМЕНЕНА!\n\n{b['service']}\n{b['datetime']}", settings_menu())
                                send(b['client_id'], f"❌ ВАША ЗАПИСЬ ОТМЕНЕНА!\n\n📋 {b['service']}\n📅 {b['datetime']}\n🏢 {settings.get('business_name', 'Бизнес')}\n\nПриносим извинения!")
                        except:
                            send(uid, "❌ ОШИБКА ОТМЕНЫ", settings_menu())
        
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\n❌ БОТ ОСТАНОВЛЕН")
        break
    except Exception as e:
        print(f"ОШИБКА: {e}")
        time.sleep(5)

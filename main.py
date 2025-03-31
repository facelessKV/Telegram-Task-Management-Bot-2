import logging
import sqlite3
import datetime
import asyncio
from typing import Dict, Any, Optional, List, Tuple

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from config import BOT_TOKEN  # Создайте файл config.py с вашим токеном

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler()

# Состояния для FSM (Finite State Machine)
class TaskForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_project = State()
    waiting_for_priority = State()
    waiting_for_deadline = State()
    waiting_for_assignee = State()

class UpdateTaskForm(StatesGroup):
    waiting_for_task_id = State()
    waiting_for_field = State()
    waiting_for_new_value = State()
    
class CompleteTaskForm(StatesGroup):
    waiting_for_task_id = State()

# Инициализация базы данных
def init_db():
    """Инициализация базы данных SQLite с необходимыми таблицами"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    # Создание таблицы проектов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT
    )
    ''')
    
    # Создание таблицы пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER NOT NULL UNIQUE,
        username TEXT,
        first_name TEXT,
        last_name TEXT
    )
    ''')
    
    # Создание таблицы задач
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        project_id INTEGER,
        creator_id INTEGER NOT NULL,
        assignee_id INTEGER,
        priority TEXT CHECK(priority IN ('Низкий', 'Средний', 'Высокий')),
        deadline TEXT,
        status TEXT DEFAULT 'Активная' CHECK(status IN ('Активная', 'Выполнена')),
        created_at TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects (id),
        FOREIGN KEY (creator_id) REFERENCES users (id),
        FOREIGN KEY (assignee_id) REFERENCES users (id)
    )
    ''')
    
    # Вставка тестового проекта, если его еще нет
    cursor.execute('SELECT COUNT(*) FROM projects')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO projects (name, description) VALUES (?, ?)', 
                      ('Основной проект', 'Проект по умолчанию для всех задач'))
    
    conn.commit()
    conn.close()
    
    logger.info("База данных инициализирована")

# Функции для работы с базой данных
def register_user(message: Message) -> int:
    """Регистрация пользователя в базе данных, если его еще нет"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if not result:
        cursor.execute(
            'INSERT INTO users (telegram_id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
            (user_id, username, first_name, last_name)
        )
        conn.commit()
        user_db_id = cursor.lastrowid
    else:
        user_db_id = result[0]
    
    conn.close()
    return user_db_id

def add_task_to_db(task_data: Dict[str, Any]) -> int:
    """Добавление новой задачи в базу данных"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO tasks (name, description, project_id, creator_id, assignee_id, priority, deadline, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        task_data['name'],
        task_data['description'],
        task_data['project_id'],
        task_data['creator_id'],
        task_data['assignee_id'],
        task_data['priority'],
        task_data['deadline'],
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_projects() -> List[Tuple[int, str]]:
    """Получение списка проектов из базы данных"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name FROM projects')
    projects = cursor.fetchall()
    
    conn.close()
    return projects

def get_users() -> List[Tuple]:
    """Получение списка пользователей из базы данных"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, telegram_id, username, first_name, last_name FROM users')
    users = cursor.fetchall()
    
    conn.close()
    return users

def get_user_tasks(user_id: int, show_completed: bool = False) -> List[Tuple]:
    """Получение списка задач пользователя"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    if show_completed:
        cursor.execute('''
        SELECT t.id, t.name, t.description, p.name, t.priority, t.deadline, t.status,
               u.username as creator, a.username as assignee
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.id
        LEFT JOIN users u ON t.creator_id = u.id
        LEFT JOIN users a ON t.assignee_id = a.id
        WHERE t.creator_id = ? OR t.assignee_id = ?
        ORDER BY 
            CASE t.status 
                WHEN 'Активная' THEN 0 
                WHEN 'Выполнена' THEN 1 
            END,
            CASE t.priority 
                WHEN 'Высокий' THEN 0 
                WHEN 'Средний' THEN 1 
                WHEN 'Низкий' THEN 2 
            END,
            t.deadline
        ''', (user_id, user_id))
    else:
        cursor.execute('''
        SELECT t.id, t.name, t.description, p.name, t.priority, t.deadline, t.status,
               u.username as creator, a.username as assignee
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.id
        LEFT JOIN users u ON t.creator_id = u.id
        LEFT JOIN users a ON t.assignee_id = a.id
        WHERE (t.creator_id = ? OR t.assignee_id = ?) AND t.status = 'Активная'
        ORDER BY 
            CASE t.priority 
                WHEN 'Высокий' THEN 0 
                WHEN 'Средний' THEN 1 
                WHEN 'Низкий' THEN 2 
            END,
            t.deadline
        ''', (user_id, user_id))
    
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def get_task_by_id(task_id: int) -> Optional[Tuple]:
    """Получение задачи по её ID"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT t.id, t.name, t.description, p.name, t.priority, t.deadline, t.status,
           u.username as creator, a.username as assignee, t.creator_id, t.assignee_id
    FROM tasks t
    LEFT JOIN projects p ON t.project_id = p.id
    LEFT JOIN users u ON t.creator_id = u.id
    LEFT JOIN users a ON t.assignee_id = a.id
    WHERE t.id = ?
    ''', (task_id,))
    
    task = cursor.fetchone()
    conn.close()
    return task

def update_task_status(task_id: int, status: str) -> None:
    """Обновление статуса задачи"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
    
    conn.commit()
    conn.close()

def update_task_field(task_id: int, field: str, value: str) -> None:
    """Обновление поля задачи"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    cursor.execute(f'UPDATE tasks SET {field} = ? WHERE id = ?', (value, task_id))
    
    conn.commit()
    conn.close()

# Обработчики команд
@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start - приветствие и регистрация пользователя"""
    user_id = register_user(message)
    await message.answer(
        f"Привет, {message.from_user.first_name}! Я бот для управления задачами.\n\n"
        f"Основные команды:\n"
        f"/add_task - добавить новую задачу\n"
        f"/list_tasks - просмотреть список задач\n"
        f"/update_task - обновить задачу\n"
        f"/complete_task - отметить задачу как выполненную"
    )

@dp.message(Command("add_task"))
async def cmd_add_task(message: Message, state: FSMContext) -> None:
    """Обработчик команды /add_task - начало создания новой задачи"""
    await state.set_state(TaskForm.waiting_for_name)
    await message.answer("Введите название задачи:")

@dp.message(TaskForm.waiting_for_name)
async def process_task_name(message: Message, state: FSMContext) -> None:
    """Обработка ввода названия задачи"""
    await state.update_data(name=message.text, creator_id=register_user(message))
    await state.set_state(TaskForm.waiting_for_description)
    await message.answer("Введите описание задачи:")

@dp.message(TaskForm.waiting_for_description)
async def process_task_description(message: Message, state: FSMContext) -> None:
    """Обработка ввода описания задачи"""
    await state.update_data(description=message.text)
    
    # Получение списка проектов
    projects = get_projects()
    
    # Создание клавиатуры для выбора проекта
    buttons = []
    for project_id, project_name in projects:
        buttons.append([InlineKeyboardButton(text=project_name, callback_data=f"project_{project_id}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await state.set_state(TaskForm.waiting_for_project)
    await message.answer("Выберите проект:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('project_'), TaskForm.waiting_for_project)
async def process_project_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора проекта"""
    await callback.answer()
    project_id = int(callback.data.split('_')[1])
    
    await state.update_data(project_id=project_id)
    
    # Создание клавиатуры для выбора приоритета
    buttons = []
    for priority in ["Низкий", "Средний", "Высокий"]:
        buttons.append([InlineKeyboardButton(text=priority, callback_data=f"priority_{priority}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await state.set_state(TaskForm.waiting_for_priority)
    await callback.message.answer("Выберите приоритет:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('priority_'), TaskForm.waiting_for_priority)
async def process_priority_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора приоритета"""
    await callback.answer()
    priority = callback.data.split('_')[1]
    
    await state.update_data(priority=priority)
    
    await state.set_state(TaskForm.waiting_for_deadline)
    await callback.message.answer(
        "Введите дедлайн в формате ГГГГ-ММ-ДД ЧЧ:ММ\nНапример: 2025-04-15 15:00"
    )

@dp.message(TaskForm.waiting_for_deadline)
async def process_deadline(message: Message, state: FSMContext) -> None:
    """Обработка ввода дедлайна"""
    try:
        deadline = datetime.datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        
        await state.update_data(deadline=message.text)
        
        # Получение списка пользователей
        users = get_users()
        
        # Создание клавиатуры для выбора исполнителя
        buttons = []
        for user_id, telegram_id, username, first_name, last_name in users:
            display_name = username or f"{first_name} {last_name}".strip()
            buttons.append([InlineKeyboardButton(text=display_name, callback_data=f"user_{user_id}")])
        
        # Добавим возможность назначить задачу себе по умолчанию
        buttons.append([InlineKeyboardButton(text="Я сам", callback_data="user_self")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await state.set_state(TaskForm.waiting_for_assignee)
        await message.answer("Выберите исполнителя:", reply_markup=keyboard)
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, используйте формат ГГГГ-ММ-ДД ЧЧ:ММ")

@dp.callback_query(lambda c: c.data.startswith('user_'), TaskForm.waiting_for_assignee)
async def process_assignee_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора исполнителя"""
    await callback.answer()
    user_data = callback.data.split('_')[1]
    
    data = await state.get_data()
    
    if user_data == "self":
        data['assignee_id'] = data['creator_id']
    else:
        data['assignee_id'] = int(user_data)
    
    # Добавление задачи в базу данных
    task_id = add_task_to_db(data)
    
    # Планирование напоминания, если указан дедлайн
    if 'deadline' in data:
        deadline = datetime.datetime.strptime(data['deadline'], '%Y-%m-%d %H:%M')
        reminder_time = deadline - datetime.timedelta(hours=24)  # Напоминание за 24 часа
        
        if reminder_time > datetime.datetime.now():
            scheduler.add_job(
                send_reminder,
                trigger=DateTrigger(run_date=reminder_time),
                args=[task_id],
                id=f"reminder_{task_id}"
            )
    
    await state.clear()
    await callback.message.answer(f"Задача успешно добавлена с ID: {task_id}")

@dp.message(Command("list_tasks"))
async def cmd_list_tasks(message: Message) -> None:
    """Обработчик команды /list_tasks - просмотр списка задач"""
    user_id = register_user(message)
    tasks = get_user_tasks(user_id)
    
    if not tasks:
        await message.answer("У вас нет активных задач.")
        return
    
    response = "📋 Ваши активные задачи:\n\n"
    for task in tasks:
        task_id, name, description, project, priority, deadline, status, creator, assignee = task
        
        # Определение эмодзи для приоритета
        priority_emoji = {
            "Низкий": "🟢",
            "Средний": "🟡",
            "Высокий": "🔴"
        }.get(priority, "")
        
        response += f"ID: {task_id}\n"
        response += f"📌 {name}\n"
        response += f"📝 {description[:50]}...\n" if len(description) > 50 else f"📝 {description}\n"
        response += f"📁 Проект: {project}\n"
        response += f"{priority_emoji} Приоритет: {priority}\n"
        
        if deadline:
            deadline_date = datetime.datetime.strptime(deadline, '%Y-%m-%d %H:%M')
            days_left = (deadline_date - datetime.datetime.now()).days
            deadline_str = f"⏰ Дедлайн: {deadline}"
            if days_left < 0:
                deadline_str += " (просрочено!)"
            elif days_left == 0:
                deadline_str += " (сегодня!)"
            deadline_str += "\n"
            response += deadline_str
        
        response += f"👤 Создатель: {creator}\n"
        response += f"👥 Исполнитель: {assignee}\n"
        response += "\n"
    
    # Добавляем кнопку для просмотра завершенных задач
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Показать завершенные задачи", callback_data="show_completed")]]
    )
    
    await message.answer(response, reply_markup=keyboard)

@dp.callback_query(F.data == "show_completed")
async def process_show_completed(callback: CallbackQuery) -> None:
    """Обработка запроса на просмотр завершенных задач"""
    await callback.answer()
    user_id = register_user(callback.message)
    tasks = get_user_tasks(user_id, show_completed=True)
    
    completed_tasks = [task for task in tasks if task[6] == 'Выполнена']
    
    if not completed_tasks:
        await callback.message.answer(
            "У вас нет завершенных задач."
        )
        return
    
    response = "✅ Ваши завершенные задачи:\n\n"
    for task in completed_tasks:
        task_id, name, description, project, priority, deadline, status, creator, assignee = task
        
        response += f"ID: {task_id}\n"
        response += f"📌 {name}\n"
        response += f"📝 {description[:50]}...\n" if len(description) > 50 else f"📝 {description}\n"
        response += f"📁 Проект: {project}\n"
        response += f"👤 Создатель: {creator}\n"
        response += f"👥 Исполнитель: {assignee}\n"
        response += "\n"
    
    await callback.message.answer(response)

@dp.message(Command("complete_task"))
async def cmd_complete_task(message: Message, state: FSMContext) -> None:
    """Обработчик команды /complete_task - отметка задачи как выполненной"""
    await state.set_state(CompleteTaskForm.waiting_for_task_id)
    await message.answer("Введите ID задачи, которую хотите отметить как выполненную:")

@dp.message(CompleteTaskForm.waiting_for_task_id, lambda message: message.text.isdigit())
async def process_task_complete_id(message: Message, state: FSMContext) -> None:
    """Обработка ввода ID задачи для отметки как выполненной"""
    task_id = int(message.text)
    task = get_task_by_id(task_id)
    
    if not task:
        await message.answer(f"Задача с ID {task_id} не найдена.")
        await state.clear()
        return
    
    # Проверяем, является ли пользователь создателем или исполнителем задачи
    user_id = register_user(message)
    creator_id, assignee_id = task[9], task[10]
    
    if user_id != creator_id and user_id != assignee_id:
        await message.answer("Вы не можете изменить эту задачу, так как не являетесь её создателем или исполнителем.")
        await state.clear()
        return
    
    if task[6] == 'Выполнена':
        await message.answer("Эта задача уже отмечена как выполненная.")
        await state.clear()
        return
    
    update_task_status(task_id, 'Выполнена')
    
    # Если задача была с напоминанием, удаляем его
    scheduler_job_id = f"reminder_{task_id}"
    if scheduler.get_job(scheduler_job_id):
        scheduler.remove_job(scheduler_job_id)
    
    await message.answer(f"Задача с ID {task_id} отмечена как выполненная! 🎉")
    await state.clear()

@dp.message(Command("update_task"))
async def cmd_update_task(message: Message, state: FSMContext) -> None:
    """Обработчик команды /update_task - обновление задачи"""
    await state.set_state(UpdateTaskForm.waiting_for_task_id)
    await message.answer("Введите ID задачи, которую хотите обновить:")

@dp.message(UpdateTaskForm.waiting_for_task_id)
async def process_update_task_id(message: Message, state: FSMContext) -> None:
    """Обработка ввода ID задачи для обновления"""
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите числовой ID задачи.")
        return
    
    task_id = int(message.text)
    task = get_task_by_id(task_id)
    
    if not task:
        await message.answer(f"Задача с ID {task_id} не найдена.")
        await state.clear()
        return
    
    # Проверяем, является ли пользователь создателем или исполнителем задачи
    user_id = register_user(message)
    creator_id, assignee_id = task[9], task[10]
    
    if user_id != creator_id and user_id != assignee_id:
        await message.answer("Вы не можете изменить эту задачу, так как не являетесь её создателем или исполнителем.")
        await state.clear()
        return
    
    await state.update_data(task_id=task_id)
    
    # Создание клавиатуры для выбора поля для обновления
    fields = [
        ("name", "Название"),
        ("description", "Описание"),
        ("priority", "Приоритет"),
        ("deadline", "Дедлайн")
    ]
    
    buttons = []
    for field_key, field_name in fields:
        buttons.append([InlineKeyboardButton(text=field_name, callback_data=f"field_{field_key}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await state.set_state(UpdateTaskForm.waiting_for_field)
    await message.answer(
        f"Выберите поле для обновления для задачи '{task[1]}':", 
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith('field_'), UpdateTaskForm.waiting_for_field)
async def process_field_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора поля для обновления"""
    await callback.answer()
    field = callback.data.split('_')[1]
    
    await state.update_data(field=field)
    
    if field == 'priority':
        buttons = []
        for priority in ["Низкий", "Средний", "Высокий"]:
            buttons.append([InlineKeyboardButton(text=priority, callback_data=f"value_{priority}")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await state.set_state(UpdateTaskForm.waiting_for_new_value)
        await callback.message.answer(
            "Выберите новый приоритет:", 
            reply_markup=keyboard
        )
    else:
        await state.set_state(UpdateTaskForm.waiting_for_new_value)
        field_names = {
            "name": "название",
            "description": "описание",
            "deadline": "дедлайн (в формате ГГГГ-ММ-ДД ЧЧ:ММ)"
        }
        await callback.message.answer(
            f"Введите новое {field_names.get(field, field)}:"
        )

@dp.callback_query(lambda c: c.data.startswith('value_'), UpdateTaskForm.waiting_for_new_value)
async def process_priority_value(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора нового приоритета"""
    await callback.answer()
    value = callback.data.split('_')[1]
    
    data = await state.get_data()
    task_id = data['task_id']
    field = data['field']
    
    update_task_field(task_id, field, value)
    
    await state.clear()
    await callback.message.answer(
        f"Приоритет задачи обновлен на: {value}"
    )

@dp.message(UpdateTaskForm.waiting_for_new_value)
async def process_new_value(message: Message, state: FSMContext) -> None:
    """Обработка ввода нового значения для поля задачи"""
    data = await state.get_data()
    task_id = data['task_id']
    field = data['field']
    value = message.text
    
    if field == 'deadline':
        try:
            deadline = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M')
        except ValueError:
            await message.answer("Неверный формат даты. Пожалуйста, используйте формат ГГГГ-ММ-ДД ЧЧ:ММ")
            return
    
    update_task_field(task_id, field, value)
    
    # Если обновили дедлайн, обновляем напоминание
    if field == 'deadline':
        scheduler_job_id = f"reminder_{task_id}"
        if scheduler.get_job(scheduler_job_id):
            scheduler.remove_job(scheduler_job_id)
        
        deadline = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M')
        reminder_time = deadline - datetime.timedelta(hours=24)  # Напоминание за 24 часа
        
        if reminder_time > datetime.datetime.now():
            scheduler.add_job(
                send_reminder,
                trigger=DateTrigger(run_date=reminder_time),
                args=[task_id],
                id=scheduler_job_id
            )
    
    await state.clear()
    field_names = {
        "name": "Название",
        "description": "Описание",
        "deadline": "Дедлайн"
    }
    await message.answer(f"{field_names.get(field, field.capitalize())} задачи обновлено.")

async def send_reminder(task_id: int) -> None:
    """Отправка напоминания о дедлайне задачи"""
    task = get_task_by_id(task_id)
    if not task or task[6] == 'Выполнена':
        return
    
    task_id, name, description, project, priority, deadline, status, creator, assignee, creator_id, assignee_id = task
    
    if assignee_id:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('SELECT telegram_id FROM users WHERE id = ?', (assignee_id,))
        assignee_telegram_id = cursor.fetchone()[0]
        conn.close()
        
        await bot.send_message(
            assignee_telegram_id,
            f"⚠️ Напоминание! ⚠️\n\n"
            f"У задачи '{name}' (ID: {task_id}) дедлайн через 24 часа: {deadline}\n\n"
            f"Приоритет: {priority}\n"
            f"Проект: {project}"
        )

# Функция для запуска бота
async def main() -> None:
    """Главная функция для запуска бота"""
    # Инициализация БД
    init_db()
    
    # Запуск планировщика
    scheduler.start()
    
    # Запуск бота
    await dp.start_polling(bot)
    
if __name__ == '__main__':
    asyncio.run(main())
import requests
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from bs4 import BeautifulSoup
from config import TOKEN
from aiogram import Bot, Dispatcher, executor, types


# пишу бота для телеги, с выкладкой на хероку
# все готово к отправке на хероку, в будущем надо добавить инлайн клавиатуру

def get_html(url):
    """ получаем html страницу с ссылки"""
    headers = {'user-agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    html = response.text
    return html


def get_weather(message):
    """ получаем погоду на день"""
    url = f'https://sinoptik.com.ru/погода-{message.text.lower()}'
    soup = BeautifulSoup(get_html(url), 'html.parser')
    try:
        temp = soup.find('div', class_='weather__article_main_temp').get_text(strip=True)
        description = soup.find('div', class_='weather__article_description-text').get_text(strip=True)
        result = f'Температура воздуха сейчас {temp}\n{description}'
    except:
        #result = f'Город "{message.text}" не найден. Скорее всего вы сделали опечатку'
        result = [f'Город "{message.text}" не найден.', "Скорее всего вы сделали опечатку"]
    return result


def get_weather_week(message):
    """ получаем погоду на следущие 6 дней"""
    url = f'https://sinoptik.com.ru/погода-{message.text.lower()}'
    soup = BeautifulSoup(get_html(url), 'html.parser')
    try:
        temps = soup.find('div', class_='weather__content_tabs clearfix').find_all('div', class_='weather__content_tab')
        days = []
        for temp in temps:
            try:
                day_week = temp.find('p', class_='weather__content_tab-day').get_text(strip=True)
                day_month = temp.find('p', class_='weather__content_tab-month').get_text(strip=True)
                date = temp.find('p', class_='weather__content_tab-date day_red').get_text(strip=True)
                t_min = temp.find('div', class_='min').get_text(strip=True)
                t_max = temp.find('div', class_='max').get_text(strip=True)
                result = f'{day_week} {date} {day_month}. {t_min}, {t_max}'
                days.append(result)
            except:
                pass
        return days
    except:
        result = ["Не удалось получить данные по запросу:", f'"{message.text}"']
        return result


storage = MemoryStorage()


class Weather(StatesGroup):
    command1 = State()
    command2 = State()


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)


# выводим приветствие при вводе команды старт
@dp.message_handler(commands=['start'])
async def hello_user(message: types.Message):
    await message.answer(f'Привет {message.from_user.username}!'
                         f'\nРад, что ты мной пользуешься! Для вызова помощи введи или нажми /help')


# вызываем помощь - краткое описане действия для пользователя
@dp.message_handler(commands=['help'])
async def hello_user(message: types.Message):
    await message.answer('Доступные команды:\n'
                         '/get_weather - выдает температуру воздуха и описание погоды;\n'
                         '/get_weather_6_days - выдает прогноз на ближайшие 6 дней.')


# активация первого состояния
@dp.message_handler(commands=['get_weather'], state=None)
async def get_answer(message: types.Message):
    await message.answer('Просто вводи город или населенный пункт:')
    # активируем состояние 1
    await Weather.command1.set()


# выполняем команду1 первого состояния, выводим температуру и описание погоды
@dp.message_handler(state=Weather.command1)
async def get_answer(message: types.Message, state: FSMContext):
    today = get_weather(message)
    # если кол-во элементов не равно двум, выводим и завершаем состояние
    if len(today) != 2:
        await message.answer(today)
        # завершаем состояние
        await state.finish()
    else:
        await message.answer(' '.join(today))


# активация второго состояния
@dp.message_handler(commands=['get_weather_6_days'])
async def get_answer(message: types.Message):
    await message.answer('Просто вводи город или населенный пункт:')
    # активируем состояние 2
    await Weather.command2.set()


# выполняем команду2 второго состояния, выводим прогноз погоды на следующие 6 дней
@dp.message_handler(state=Weather.command2)
async def get_answer(message: types.Message, state: FSMContext):
    days = get_weather_week(message)
    # если кол-во элементов больше двух, выводим и завершаем состояние
    if len(days) > 2:
        await message.answer('Прогноз на последующие 6 дней:')
        for day in days:
            await message.answer(day)
        # завершаем состояние
        await state.finish()
    else:
        await message.answer(' '.join(days))


# отлавливаем любое сообщение не попавшие в обработку
@dp.message_handler()
async def echo_message(message: types.Message):
    await message.answer('Вы не выбрали команду. Я не знаю, что вы хотите')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
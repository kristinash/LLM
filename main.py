import telebot
import requests
import jsons
from Class_ModelResponse import ModelResponse

API_TOKEN = ''
bot = telebot.TeleBot(API_TOKEN)

user_contexts = {}

def get_user_context(user_id):
    if user_id not in user_contexts:
        user_contexts[user_id] = []
    return user_contexts[user_id]

def add_user_message(user_id, message):
    context = get_user_context(user_id)
    context.append({"role": "user", "content": message})

def add_assistant_message(user_id, message):
    context = get_user_context(user_id)
    context.append({"role": "assistant", "content": message})

def clear_context(user_id):
    if user_id in user_contexts:
        user_contexts[user_id] = []

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очистить историю диалога\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_id = message.from_user.id
    clear_context(user_id)
    bot.reply_to(message, "История диалога очищена!")


@bot.message_handler(commands=['model'])
def send_model_name(message):
    response = requests.get('http://10.33.0.2:1234/v1/models')

    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"Используемая модель: {model_name}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_message = message.text
    
    add_user_message(user_id, user_message)
    
    context = get_user_context(user_id)
    
    request = {
        "messages": context
    }
    
    response = requests.post(
        'http://10.33.0.2:1234/v1/chat/completions',
        json=request
    )

    if response.status_code == 200:
        model_response = jsons.loads(response.text, ModelResponse)
        add_assistant_message(user_id, model_response.choices[0].message.content)    
        bot.reply_to(message, model_response.choices[0].message.content)
    else:
        if context and context[-1]["role"] == "user":
            context.pop()
        bot.reply_to(message, 'Произошла ошибка при обращении к модели.')
        
if __name__ == '__main__':
    bot.polling(none_stop=True)

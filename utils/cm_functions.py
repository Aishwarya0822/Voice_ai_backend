import re
from fuzzywuzzy import fuzz
def appointment_gpt(user_message: str) -> str:
    user_message = user_message.lower().strip()
 
    def similar(msg, pattern, threshold=70):

        return fuzz.partial_ratio(msg, pattern.lower()) >= threshold
 
    # Basic greetings

    if any(similar(user_message, greet) for greet in ["hi", "hello", "hey"]):

        return "Hi there! How can I assist you today?"

    # Booking intents (broader matching)

    elif any(word in user_message for word in ["book", "appointment", "schedule"]):

        if "dental" in user_message:

            return "Got it. Could you please provide your phone number so I can proceed with the booking?"

        return "Sure! Which type of doctor would you like to book an appointment with?"
    
    

    elif "i am not available" in user_message or "can you check availability around"  in user_message or "4:00 p.m" in user_message:

        return "Sure. Let me check... there is a slot available at 5 . Does that work for you?"
    
    elif "sure its" in user_message or any(char.isdigit() for char in user_message):

        return "Thank you. Dr. Michael has an available slot tomorrow at 2 o'clock. Would that time work for you?"
    
    

    elif any(word in user_message for word in ["yes"," that sounds perfect", "okay"]):      

        return "Great! Your appointment with Dr. Michael has been successfully booked for tomorrow at 5 o'clock.. Thank you for choosing our clinic. Have a nice day!!"
 
    return "I'm sorry, could you please repeat that?"

from fuzzywuzzy import fuzz
import re


context = {}  # example; make sure it's defined globally or passed in

def insurance_gpt(user_message: str) -> str:

    user_message = user_message.lower().strip()

    # Normalize message by removing punctuation and spaces
    clean_msg = user_message.replace(".", "").replace(" ", "")

    # 2️⃣ Claim status inquiry
    if any(word in user_message for word in ["hi", "hello", " status of my claim", "check claim", "claim status"]):
        context["last_intent"] = "claim_status"
        return "Of course! Could you please provide your policy number so I can locate your insurance details?"
    
    elif any(word in user_message.lower() for word in ["fine", "thanks", "thank you", "okay", "ok"]):
        return "You're welcome! Feel free to reach out anytime for insurance help."

    # 3️⃣ Policy number provided — handle all variations (P.O.B., P O B, pob)
    elif "mypolicynumberispob2025" in clean_msg or "mypolicynumberispob2020" in clean_msg:
        context["insurance_provider"] = "startcare health insurance"
        return "Thank you! I have found your StartCare Health Insurance policy. Could you also share your claim number to check the status of that claim?"

    elif re.search(r'\bclm\s*\d{3,}\b', user_message):
        return "I found your claim details. It is  currently being processed and should be completed within 3 to 5 business days."

    elif any(word in user_message for word in ["when will i get my refund", "refund"]) :
        context["last_intent"] = "refund_timeline"
        return "Most approved claims are paid within 2 working days after processing."

    # 9️⃣ Goodbye
    

    # 🔟 Default fallback
    return "I'm sorry, could you please clarify your insurance question?"

def appointment_gpt_ru(user_message: str) -> str:
    user_message = user_message.lower().strip()

    def similar(msg, pattern, threshold=70):
        return fuzz.partial_ratio(msg, pattern.lower()) >= threshold

    # 1️⃣ Greeting
    if any(similar(user_message, greet) for greet in ["привет", "здравствуйте", "добрый день"]):
        return "Привет! Как я могу вам помочь сегодня?"

    # 2️⃣ If message contains digits → treat as phone number FIRST
    if any(char.isdigit() for char in user_message):
        return "Спасибо! У доктора Михаила есть свободное время завтра в 14:00. Вам подходит это время?"

    # 3️⃣ Booking intents
    if any(word in user_message for word in ["стоматолог", "зуб", "зубной"]):
        return "Понятно. Можете предоставить ваш номер телефона?"

    # 3️⃣ Booking intent
    if any(word in user_message for word in ["записать", "запись", "прием", "врач"]):
        return "Конечно! К какому врачу вы хотели бы записаться?"

    # 4️⃣ Confirm appointment
    if any(word in user_message for word in ["да", "подходит", "хорошо", "отлично"]):
        return "Отлично! Ваша запись к доктору Михаилу успешно забронирована на завтра в 14:00. Спасибо за выбор нашей клиники!"

    # 5️⃣ Default
    return "Извините, не могли бы вы повторить?"


# Add these functions to utils/cm_functions.py

# def appointment_gpt_ru(user_message: str) -> str:
#     user_message = user_message.lower().strip()
    
#     def similar(msg, pattern, threshold=70):
#         return fuzz.partial_ratio(msg, pattern.lower()) >= threshold
    
#     # Russian greetings
#     if any(similar(user_message, greet) for greet in ["привет", "здравствуйте", "добрый день"]):
#         return "Привет! Как я могу вам помочь сегодня?"
    
#     # Booking intents in Russian
#     elif any(word in user_message for word in ["записать", "запись", "прием", "врач"]):
#         if "стоматолог" in user_message or "зубной" in user_message:
#             return "Понятно. Можете предоставить ваш номер телефона для записи?"
#         return "Конечно! К какому врачу вы хотели бы записаться?"
    
#     elif "не могу" in user_message or "проверить время" in user_message:
#         return "Спасибо. У доктора Майкла есть свободное время завтра в 2 часа. Вам подходит это время?"
    
#     elif any(char.isdigit() for char in user_message):
#         return "Спасибо. У доктора Михаила есть свободное время завтра в 14:00. Вам подходит это время?"
    
#     elif any(word in user_message for word in ["да", "подходит", "хорошо", "отлично"]):
#         return "Отлично! Ваша запись к доктору Михаилу успешно забронирована на завтра в 17:00. Спасибо за выбор нашей клиники!"
    
#     return "Извините, не могли бы вы повторить?"

def insurance_gpt_ru(user_message: str) -> str:
    user_message = user_message.lower().strip()
    
    # Russian insurance responses
    if any(word in user_message for word in ["привет", "здравствуйте", "статус", "заявка", "страховка"]):
        return "Конечно! Можете предоставить номер вашего полиса, чтобы я мог найти ваши страховые данные?"
    
    elif any(word in user_message for word in ["спасибо", "хорошо", "понятно"]):
        return "Пожалуйста! Обращайтесь в любое время за помощью по страхованию."
    
    elif "полис" in user_message or any(char.isdigit() for char in user_message):
        return "Спасибо! Я нашел ваш полис StartCare Health Insurance. Можете также предоставить номер заявки для проверки статуса?"
    
    elif "возврат" in user_message or "когда получу" in user_message:
        return "Большинство одобренных заявок оплачиваются в течение 2 рабочих дней после обработки."
    
    return "Извините, не могли бы вы уточнить ваш вопрос по страхованию?"

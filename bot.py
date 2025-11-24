import requests
import time
import random

BOT_TOKEN = "8412470812:AAHnUPlm-QugWpF1okOEqNatXmgV0ETcpm0"
ADMIN_ID = 6365371142

API = f"https://api.telegram.org/bot{BOT_TOKEN}/"

bot_state = {
    "random_active": False,
    "total_users_needed": 0,
    "winners_count": 0,
    "collected": []
}

admin_step = {}

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = reply_markup
    try:
        requests.post(API + "sendMessage", json=data, timeout=5)
    except:
        pass

def get_updates(offset=None):
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        return requests.get(API + "getUpdates", params=params, timeout=35).json()
    except:
        return {"result": []}

def keyboard_yes_no():
    return {
        "inline_keyboard": [
            [{"text": "Ha", "callback_data": "yes"}],
            [{"text": "Yo'q", "callback_data": "no"}]
        ]
    }

def keyboard_confirm():
    return {
        "inline_keyboard": [
            [{"text": "Randomni boshlash", "callback_data": "confirm"}]
        ]
    }

def finish_random():
    users = bot_state["collected"]
    winners_count = bot_state["winners_count"]

    if len(users) == 0:
        send_message(ADMIN_ID, "❌ Hech kim ishtirok etmadi.")
        return

    winners = random.sample(users, winners_count)
    result = "🎉 RANDOM NATIJALARI\n\n"
    result += f"Jami ishtirokchilar: {len(users)} ta\n"
    result += f"G‘oliblar soni: {winners_count} ta\n\n"

    for i, w in enumerate(winners, 1):
        result += f"{i}. ID: {w['id']}\n"
        result += f"👤 tg://user?id={w['user_id']}\n\n"
        send_message(w["user_id"], "🎉 Tabriklaymiz! Siz g‘olibsiz!")

    send_message(ADMIN_ID, result)

    bot_state["random_active"] = False
    bot_state["collected"] = []
    bot_state["total_users_needed"] = 0
    bot_state["winners_count"] = 0

def process_admin_message(uid, text):
    step = admin_step.get(uid)
    if step == "total":
        if not text.isdigit():
            send_message(uid, "Faqat raqam kiriting!")
            return
        bot_state["total_users_needed"] = int(text)
        admin_step[uid] = "winners"
        send_message(uid, "Nechi g‘olib bo‘ladi?")
        return

    if step == "winners":
        if not text.isdigit():
            send_message(uid, "Faqat raqam kiriting!")
            return
        count = int(text)
        if count <= 0 or count > bot_state["total_users_needed"]:
            send_message(uid, f"G‘oliblar soni 1 dan {bot_state['total_users_needed']} gacha bo‘lsin!")
            return

        bot_state["winners_count"] = count
        admin_step[uid] = None
        send_message(uid, "Randomni boshlaymizmi?", reply_markup=keyboard_confirm())
        return

def process_user_id(msg):
    uid = msg["from"]["id"]
    text = msg.get("text", "").strip()

    if not bot_state["random_active"]:
        send_message(uid, "Random hozir ochiq emas!")
        return

    if not text.isdigit() or len(text) != 10:
        send_message(uid, "❌ 10 xonali ID yuboring!")
        return

    if any(u["id"] == text for u in bot_state["collected"]):
        send_message(uid, "Bu ID allaqachon kiritilgan!")
        return

    bot_state["collected"].append({"id": text, "user_id": uid})
    send_message(uid, "ID qabul qilindi!")

    remaining = bot_state["total_users_needed"] - len(bot_state["collected"])
    send_message(ADMIN_ID, f"Yangi ID: {text}\nQolgan: {remaining} ta")

    if len(bot_state["collected"]) >= bot_state["total_users_needed"]:
        finish_random()

def main():
    print("Bot 24/7 ishlayapti...")
    offset = None

    while True:
        try:
            updates = get_updates(offset)
            if "result" in updates:
                for update in updates["result"]:
                    offset = update["update_id"] + 1

                    if "callback_query" in update:
                        cq = update["callback_query"]
                        data = cq["data"]
                        uid = cq["from"]["id"]

                        if uid != ADMIN_ID:
                            send_message(uid, "Siz admin emassiz!")
                            continue

                        if data == "yes":
                            admin_step[uid] = "total"
                            send_message(uid, "Necha ID qabul qilinsin?")
                        elif data == "no":
                            send_message(uid, "Bekor qilindi.")
                        elif data == "confirm":
                            bot_state["random_active"] = True
                            send_message(uid, "Random boshlandi!")
                        continue

                    if "message" in update:
                        msg = update["message"]
                        uid = msg["from"]["id"]
                        text = msg.get("text", "")

                        if text == "/admin" and uid == ADMIN_ID:
                            send_message(uid, "Random boshlansinmi?", reply_markup=keyboard_yes_no())
                            continue

                        if uid == ADMIN_ID and admin_step.get(uid):
                            process_admin_message(uid, text)
                            continue

                        if text == "/start":
                            if bot_state["random_active"]:
                                send_message(uid, "Random ochiq! 10 xonali ID yuboring.")
                            else:
                                send_message(uid, "Random hozir ochiq emas.")
                            continue

                        if text.isdigit():
                            process_user_id(msg)

        except Exception as e:
            print("Xatolik:", e)
            time.sleep(1)

main()

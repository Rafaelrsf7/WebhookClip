from flask import Flask, request
from telegram import Bot
import requests
import os

app = Flask(__name__)

BOT_TOKEN = "7312735659:AAE4C-c-xh1IErvkFhKaSFkbHhTAn2WGvZE"
MP_ACCESS_TOKEN = "APP_USR-3712929109671947-060720-58dc7923aeaf32120a0bd25e0944c473-2481986951"
bot = Bot(token=BOT_TOKEN)

GRUPO_IDS = {
    "2c938084973e109501974cfeace805d0": -4933824491,  # Ruyter
    "2c938084974b28cf01974cfb5e7c008b": -4815652822,  # Nathan
    "2c938084974b28cf01974cf4823f0088": -4886568001,  # Zanolini
    "2c938084974b28cf01974cff2ed1008d": [             # pacote completo
        -4933824491,
        -4815652822,
        -4886568001
    ]
}

@app.route("/webhook", methods=["POST"])
def receber():
    data = request.get_json()

    if data.get("type") == "authorization":
        auth_id = data.get("data", {}).get("id")
        if not auth_id:
            return {"status": "sem id"}, 400

        try:
            # Consultar a autorização na API do Mercado Pago
            headers = {
                "Authorization": f"Bearer {MP_ACCESS_TOKEN}"
            }
            url = f"https://api.mercadopago.com/preapproval/{auth_id}"
            r = requests.get(url, headers=headers)
            info = r.json()

            plan_id = info.get("preapproval_plan_id")
            chat_id = info.get("external_reference")

            if not plan_id or not chat_id:
                return {"status": "dados incompletos"}, 400

            chat_id = int(chat_id)
            grupos = GRUPO_IDS.get(plan_id)

            if not grupos:
                bot.send_message(chat_id=chat_id, text="Plano não reconhecido. Contate o suporte.")
                return {"status": "plano desconhecido"}, 200

            if isinstance(grupos, list):
                for group_id in grupos:
                    invite_link = bot.create_chat_invite_link(
                        chat_id=group_id,
                        expire_date=None,
                        member_limit=1
                    )
                    bot.send_message(chat_id=chat_id, text=f"Acesse seu grupo VIP: {invite_link.invite_link}")
            else:
                invite_link = bot.create_chat_invite_link(
                    chat_id=grupos,
                    expire_date=None,
                    member_limit=1
                )
                bot.send_message(chat_id=chat_id, text=f"Acesse seu grupo VIP: {invite_link.invite_link}")

            return {"status": "ok"}, 200

        except Exception as e:
            return {"status": "erro", "detalhe": str(e)}, 500

    return {"status": "ignorado"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
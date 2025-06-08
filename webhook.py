# WEBHOOK.PY - Render.com
from flask import Flask, request
import telegram
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telegram.Bot(token=BOT_TOKEN)

# Mapeamento de planos para grupos (com os chat_id reais)
planos_para_grupos = {
    "2c938084973e109501974cfeace805d0": [-4933824491],  # Ruyter
    "2c938084974b28cf01974cfb5e7c008b": [-4815652822],  # Nathan
    "2c938084974b28cf01974cf4823f0088": [-4886568001],  # Zanolini
    "2c938084974b28cf01974cff2ed1008d": [               # Pacote completo
        -4933824491,
        -4815652822,
        -4886568001
    ]
}

@app.route("/webhook", methods=["POST"])
def receber_webhook():
    data = request.json
    chat_id = request.args.get("chat_id", type=int)

    if data.get("type") == "subscription_authorized_payment" and chat_id:
        plano_id = data.get("data", {}).get("preapproval_plan_id")
        grupos = planos_para_grupos.get(plano_id, [])

        for grupo in grupos:
            try:
                invite = bot.create_chat_invite_link(chat_id=grupo, member_limit=1)
                bot.send_message(chat_id, f"✅ Pagamento confirmado!\nAcesse o grupo: {invite.invite_link}")
            except Exception as e:
                print(f"Erro ao enviar convite: {e}")

    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

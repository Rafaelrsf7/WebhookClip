from flask import Flask, request
from telegram import Bot
import requests
import os

app = Flask(__name__)

# Configurar via variáveis de ambiente no Render ou EC2
BOT_TOKEN = os.getenv("BOT_TOKEN", "7312735659:AAE4C-c-xh1IErvkFhKaSFkbHhTAn2WGvZE")
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "APP_USR-3712929109671947-060720-58dc7923aeaf32120a0bd25e0944c473-2481986951")

bot = Bot(token=BOT_TOKEN)

# Mapeia título do item de pagamento para chat_id dos grupos ou lista de grupos
GROUP_IDS = {
    "Plano Ruyter": -4933824491,
    "Plano Nathan": -4815652822,
    "Plano Zanolini": -4886568001,
    "Plano Completo": [
        -4933824491,
        -4815652822,
        -4886568001
    ]
}

@app.route("/webhook", methods=["POST"])
def receber():
    payload = request.get_json()

    print("📥 PAYLOAD RECEBIDO:", payload)

    # Tratar apenas eventos de pagamento
    if payload.get("type") == "payment":
        payment_id = payload.get("data", {}).get("id")
        if not payment_id:
            return {"status": "missing_payment_id"}, 400

        # Consultar detalhes do pagamento
        headers = {
            "Authorization": f"Bearer {MP_ACCESS_TOKEN}"
        }
        resp = requests.get(f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=headers)
        if resp.status_code != 200:
            return {"status": "mp_api_error", "code": resp.status_code}, 500

        info = resp.json()
        # Verificar se aprovado
        if info.get("status") != "approved":
            return {"status": "payment_not_approved"}, 200

        # Extrair chat_id do cliente
        external_ref = info.get("external_reference")
        if not external_ref:
            return {"status": "no_external_reference"}, 400

        try:
            chat_id = int(external_ref)
        except ValueError:
            return {"status": "invalid_external_reference"}, 400

        # Determinar o plano pelo título do item
        items = info.get("additional_info", {}).get("items", [])
        if not items:
            return {"status": "no_items"}, 400

        plan_title = items[0].get("title")
        group = GROUP_IDS.get(plan_title)
        if not group:
            bot.send_message(chat_id=chat_id, text="Plano não reconhecido. Contate suporte.")
            return {"status": "unknown_plan"}, 200

        # Gerar e enviar link de convite único
        if isinstance(group, list):
            for gid in group:
                invite = bot.create_chat_invite_link(chat_id=gid, member_limit=1)
                bot.send_message(chat_id=chat_id, text=f"Acesse seu grupo VIP: {invite.invite_link}")
        else:
            invite = bot.create_chat_invite_link(chat_id=group, member_limit=1)
            bot.send_message(chat_id=chat_id, text=f"Acesse seu grupo VIP: {invite.invite_link}")

        return {"status": "ok"}, 200

    # Ignorar outros eventos
    return {"status": "ignored"}, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

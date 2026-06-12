"""
Smoke test de neonize (API sync).

Uso (desde la raíz del repo):
    python -m bot_wa.smoke_test

Primer arranque: imprime un QR en la terminal. Escanealo desde el WhatsApp
del número dedicado (Settings → Linked Devices → Link a Device). La sesión
queda en bot_wa/session/store.db y los reinicios siguientes no piden QR.

Una vez conectado, mandale "ping" desde otro chat → debe responder "pong".
"""

import logging
from pathlib import Path

from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv, PairStatusEv

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("smoke")

SESSION_DIR = Path(__file__).parent / "session"
SESSION_DIR.mkdir(exist_ok=True)
DB_PATH = SESSION_DIR / "store.db"

client = NewClient(str(DB_PATH))


@client.event(ConnectedEv)
def on_connected(_client, _event):
    log.info("✅ Conectado a WhatsApp")


@client.event(PairStatusEv)
def on_pair(_client, event):
    log.info(f"📱 Paired como: {event.ID.User}")


@client.event(MessageEv)
def on_message(c, message):
    chat = message.Info.MessageSource.Chat
    sender = message.Info.MessageSource.Sender

    text = (
        message.Message.conversation
        or (message.Message.extendedTextMessage.text if message.Message.extendedTextMessage else "")
        or ""
    ).strip().lower()

    log.info(
        f"msg from sender={sender.User}@{sender.Server} "
        f"chat={chat.User}@{chat.Server} text={text!r} from_me={message.Info.MessageSource.IsFromMe}"
    )

    if message.Info.MessageSource.IsFromMe:
        return

    if text == "ping":
        try:
            c.send_message(chat, "pong")
            log.info(f"✅ pong enviado a {chat.User}@{chat.Server}")
        except Exception as e:
            log.exception(f"❌ send_message falló: {e}")


if __name__ == "__main__":
    client.connect()

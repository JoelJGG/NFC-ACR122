import time
import json
import os
from smartcard.System import readers
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.Exceptions import CardConnectionException
from smartcard.util import toHexString

GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALIAS_FILE = os.path.join(BASE_DIR, "aliases.json")



def load_aliases(path=ALIAS_FILE):
    print("📁 Buscando aliases en:", path)

    if not os.path.exists(path):
        print("❌ El archivo NO existe.")
        return {}

    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        aliases = {str(k).upper(): str(v) for k, v in data.items()}
        print(f"✅ Aliases cargados OK: {len(aliases)}")
        return aliases

    except Exception as e:
        print("❌ Error leyendo/parsing aliases.json:", repr(e))
        return {}



def save_aliases(aliases, path=ALIAS_FILE):
    # Guardado “bonito” y estable
    with open(path, "w", encoding="utf-8") as f:
        json.dump(aliases, f, ensure_ascii=False, indent=2, sort_keys=True)


def read_uid(card_connection):
    """Lee UID usando la conexión ya abierta. Devuelve string HEX o None."""
    try:
        data, sw1, sw2 = card_connection.transmit(GET_UID_APDU)
        if (sw1, sw2) == (0x90, 0x00) and data:
            return toHexString(data).replace(" ", "").upper()
        return None
    except Exception:
        return None


class Observer(CardObserver):
    def __init__(self, aliases):
        super().__init__()
        self.aliases = aliases

    def register_uid_if_needed(self, uid):
        if uid in self.aliases:
            return self.aliases[uid]

        print(f"\n🆕 UID nueva detectada: {uid}")
        name = input("Asigna un nombre para esta UID (ENTER para 'Desconocido'): ").strip()
        if not name:
            name = "Desconocido"

        self.aliases[uid] = name
        save_aliases(self.aliases)
        print(f"✅ Guardado: {uid} = {name}\n")
        return name

    def update(self, observable, actions):
        added, removed = actions

        for card in added:
            reader_name = getattr(card.reader, "name", str(card.reader))

            try:
                conn = card.createConnection()
                conn.connect()
                uid = read_uid(conn)

                if uid:
                    alias = self.register_uid_if_needed(uid)
                    print(f"[INSERT] {reader_name}  UID={uid}  Nombre={alias}")
                else:
                    print(f"[INSERT] {reader_name}  (UID no disponible)")
            except CardConnectionException:
                print(f"[INSERT] {reader_name}  (no pude conectar)")
            except Exception as e:
                print(f"[INSERT] {reader_name}  (error: {e})")

        for card in removed:
            reader_name = getattr(card.reader, "name", str(card.reader))
            print(f"[REMOVE] {reader_name}")


def main():
    aliases = load_aliases()
    if aliases:
        print(f"📦 Aliases cargados: {len(aliases)} (desde {ALIAS_FILE})")
    else:
        print(f"📦 Sin aliases previos (se crearán en {ALIAS_FILE})")

    r = readers()
    if len(r) < 1:
        print("⚠️ No veo lectores conectados.")
        return

    print("Lectores detectados:")
    for i, rd in enumerate(r, 1):
        print(f"  {i}. {rd}")

    monitor = CardMonitor()
    observer = Observer(aliases)
    monitor.addObserver(observer)

    print("\nEscuchando eventos (insert/remove) por lector... Ctrl+C para salir.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        monitor.deleteObserver(observer)


if __name__ == "__main__":
    main()

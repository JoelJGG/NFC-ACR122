import time
import json
import os

from smartcard.System import readers
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.Exceptions import CardConnectionException
from smartcard.util import toHexString

from writeConditions import writeValor

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

        # Mapa por ATR para emparejar INSERT/REMOVE
        # key = (reader_name, tuple(card.atr))
        self.present = {}

        # Fallback si el ATR no empareja: última tarjeta conocida por lector
        # key = reader_name
        self.last_by_reader = {}

    def get_alias(self, uid: str) -> str:
        """Devuelve alias si existe, si no 'Desconocido' (SIN guardar nada)."""
        if not uid:
            return "Desconocido"
        return self.aliases.get(uid.upper(), "Desconocido")

    def update(self, observable, actions):
        added, removed = actions

        # ---------- INSERT ----------
        for card in added:
            reader_name = getattr(card.reader, "name", str(card.reader))

            try:
                conn = card.createConnection()
                conn.connect()
                uid = read_uid(conn)

                if uid:
                    alias = self.get_alias(uid)
                    print(f"[INSERT] {reader_name}  UID={uid}  Nombre={alias}")

                    atr_key = (reader_name, tuple(card.atr))
                    info = {"uid": uid, "alias": alias, "atr": toHexString(card.atr)}

                    self.present[atr_key] = info
                    self.last_by_reader[reader_name] = info
                else:
                    print(f"[INSERT] {reader_name}  (UID no disponible)")

            except CardConnectionException:
                print(f"[INSERT] {reader_name}  (no pude conectar)")
            except Exception as e:
                print(f"[INSERT] {reader_name}  (error: {e})")

        # ---------- REMOVE (TU TRIGGER) ----------
        for card in removed:
            reader_name = getattr(card.reader, "name", str(card.reader))
            atr_key = (reader_name, tuple(card.atr))

            info = self.present.pop(atr_key, None)

            # Fallback: si no coincide por ATR, usa la última por lector
            if info is None:
                info = self.last_by_reader.get(reader_name)

            if info:
                uid = info["uid"]
                alias = info["alias"]
                print(f"[REMOVE] {reader_name}  UID={uid}  Nombre={alias}")

                # ✅ TRIGGER: se disparará AL QUITAR la tarjeta
                try:
                    writeValor(alias)
                    print(f"📝 XML actualizado con: {alias}")
                except Exception as e:
                    print(f"📝 Error escribiendo XML: {e}")
            else:
                print(f"[REMOVE] {reader_name}  (tarjeta desconocida)")


def main():
    aliases = load_aliases()
    if aliases:
        print(f"📦 Aliases cargados: {len(aliases)} (desde {ALIAS_FILE})")
    else:
        print(f"📦 Sin aliases previos (no se crearán nuevos)")

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

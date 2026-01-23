import time
from smartcard.System import readers
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.Exceptions import CardConnectionException
from smartcard.util import toHexString

GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]


def read_uid(card_connection):
    """Lee UID usando la conexión ya abierta. Devuelve string HEX o None."""
    try:
        data, sw1, sw2 = card_connection.transmit(GET_UID_APDU)
        if (sw1, sw2) == (0x90, 0x00) and data:
            return toHexString(data).replace(" ", "")
        return None
    except Exception:
        return None


class Observer(CardObserver):
    def update(self, observable, actions):
        added, removed = actions

        for card in added:
            reader_name = getattr(card.reader, "name", str(card.reader))

            try:
                conn = card.createConnection()
                conn.connect()
                uid = read_uid(conn)
                if uid:
                    print(f"[INSERT] {reader_name}  UID={uid}")
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
    r = readers()
    if len(r) < 2:
        print("⚠️ Veo menos de 2 lectores. Conecta 2 (o más) y vuelve a ejecutar.")
        print("Lectores detectados:", r)
        return

    print("Lectores detectados:")
    for i, rd in enumerate(r, 1):
        print(f"  {i}. {rd}")

    monitor = CardMonitor()
    observer = Observer()
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

import xml.etree.ElementTree as ET
import os
import time

WINDOWS_PATH = r"C:/admira/conditions/biomax.xml"
LINUX_PATH = "/opt/Admira/share/conditions/biomax.xml"

# 🔥 variable global: recuerda el último valor escrito
_last_valor_guardado = None

def writeValor(texto: str, path: str = None, condition_id: str = "4"):
    """
    Escribe en el XML SOLO si el valor es diferente al último valor guardado (en memoria).
    - No lee el XML para comparar
    - Mucho más rápido
    Devuelve True si escribió, False si no.
    """
    global _last_valor_guardado

    nuevo = str(texto)

    # ✅ si es igual al último guardado, no hacemos nada
    if _last_valor_guardado == nuevo:
        return False

    if path is None:
        path = WINDOWS_PATH if os.name == "nt" else LINUX_PATH

    tree = ET.parse(path)
    root = tree.getroot()

    # 1) Si el root ES <condition>, úsalo
    if root.tag == "condition":
        condition = root
    else:
        # 2) Si no, busca un <condition> en cualquier parte
        condition = root.find(".//condition")
        if condition is None:
            raise ValueError("No se encontró ningún tag <condition> en el XML")

    # Buscar <value> dentro de condition (directo o anidado)
    value = condition.find("value") or condition.find(".//value")
    if value is None:
        raise ValueError("No se encontró ningún tag <value> dentro de <condition>")

    value.text = nuevo
    condition.set("id", str(condition_id))
    condition.set("tstamp", str(int(time.time())))

    tree.write(path, encoding="utf-8", xml_declaration=True)

    # ✅ actualizamos el último valor escrito
    _last_valor_guardado = nuevo
    return True

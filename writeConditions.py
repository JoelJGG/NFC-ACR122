import xml.etree.ElementTree as ET
import os
import time

WINDOWS_PATH = r"C:/admira/conditions/biomax.xml"
LINUX_PATH = "/opt/Admira/share/conditions/biomax.xml"

def writeValor(texto: str, path: str = None, condition_id: str = "4"):
    """
    Escribe 'texto' en <value>, actualiza id y tstamp, y guarda el XML.
    Soporta XML donde el root ya es <condition> o donde hay <condition> anidados.
    """

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

    value.text = str(texto)

    condition.set("id", str(condition_id))
    condition.set("tstamp", str(int(time.time())))

    tree.write(path, encoding="utf-8", xml_declaration=True)
    return True

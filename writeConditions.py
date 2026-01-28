import xml.etree.ElementTree as ET
import os
import time

# Windows path: 'C:/admira/conditions/biomax.xml'
# Ubuntu path: '/opt/Admira/share/conditions/biomax.xml'

WINDOWS_PATH = "C:/admira/conditions/biomax.xml"
LINUX_PATH = "/opt/Admira/share/conditions/biomax.xml"


def writeValor(texto: str, path: str = None):
    """
    Escribe el texto en el tag <value> dentro del XML biomax.xml,
    actualiza id y tstamp, y guarda el archivo.
    """

    # Elegir ruta automáticamente si no se pasa
    if path is None:
        path = WINDOWS_PATH if os.name == "nt" else LINUX_PATH

    # Cargar XML
    tree = ET.parse(path)
    root = tree.getroot()

    # Buscar <condition>
    condition = root.find("condition")
    if condition is None:
        raise ValueError("No se encontró el tag <condition> en el XML")

    # Buscar <value> dentro de condition
    value = condition.find("value")
    if value is None:
        raise ValueError("No se encontró el tag <value> dentro de <condition>")

    # Modificar contenido
    value.text = str(texto)

    # Modificar atributos
    condition.set("id", "4")
    condition.set("tstamp", str(int(time.time())))

    # Guardar XML
    tree.write(path, encoding="utf-8", xml_declaration=True)

    return True

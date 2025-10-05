import cv2
import numpy as np
from PIL import Image


def process_image(
    pil_image: Image.Image,
    contrast: float,
    brightness: float,
    smoothing: float,
    invert_colors: bool,
    use_threshold: bool,
    threshold_level: int,
    dilate: int,
    erode: int,
    noise_reduction: int,
    use_stroke: bool,
    stroke_thickness: int,
    use_artistic_smoothing: bool,
    artistic_smoothing_strength: float,
) -> Image.Image:
    """
    Aplikuje sekvenci operací pro zpracování obrazu na vstupní obrázek.
    Vrací zpracovaný obrázek ve formátu PIL.
    """
    # Zkontroluje, zda byl poskytnut platný obrázek, jinak vrátí prázdný obrázek.
    if not pil_image:
        return Image.new("L", (100, 100), 0)

    # Převede obrázek PIL na 8-bitové pole NumPy v odstínech šedi.
    arr = np.array(pil_image.convert("L"), dtype=np.uint8)

    # Provede tonální úpravy na 32-bitovém poli s plovoucí desetinnou čárkou, aby se zabránilo ořezání hodnot.
    arr_float = arr.astype(np.float32)

    # Aplikuje úpravu jasu pomocí násobení.
    if brightness != 1.0:
        arr_float *= brightness

    # Aplikuje úpravu kontrastu.
    if contrast != 1.0:
        arr_float = 128 + contrast * (arr_float - 128)

    # Ořízne hodnoty zpět do platného 8-bitového rozsahu (0-255) a převede datový typ.
    arr = np.clip(arr_float, 0, 255).astype(np.uint8)

    # Aplikuje binární prahování, pokud je povoleno.
    if use_threshold:
        _, arr = cv2.threshold(arr, threshold_level, 255, cv2.THRESH_BINARY)

    # Vzájemně se vylučující blok: buď se aplikuje obtažení, nebo morfologické operace.
    if use_stroke:
        # Vytvoří binární zdrojový obrázek, pokud již neexistuje z prahování.
        binary_src = (
            arr if use_threshold else cv2.threshold(arr, 127, 255, cv2.THRESH_BINARY)[1]
        )
        # Najde kontury v binárním obrázku.
        contours, _ = cv2.findContours(
            binary_src, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        # Vykreslí nalezené kontury na nový černý obrázek.
        arr = np.zeros_like(arr)
        cv2.drawContours(arr, contours, -1, 255, thickness=int(stroke_thickness))
    else:
        # Aplikuje dilataci pro rozšíření bílých oblastí.
        if dilate > 0:
            kernel_d = np.ones((2 * dilate + 1, 2 * dilate + 1), np.uint8)
            arr = cv2.dilate(arr, kernel_d, iterations=1)
        # Aplikuje erozi pro zúžení bílých oblastí.
        if erode > 0:
            kernel_e = np.ones((2 * erode + 1, 2 * erode + 1), np.uint8)
            arr = cv2.erode(arr, kernel_e, iterations=1)

    # Aplikuje mediánový filtr pro odstranění šumu typu "sůl a pepř".
    if noise_reduction > 0:
        noise_k_size = 2 * noise_reduction + 1
        arr = cv2.medianBlur(arr, noise_k_size)

    # Aplikuje standardní Gaussovský filtr pro jemné rozmazání.
    if smoothing > 0.0:
        k_size = int(smoothing * 2) * 2 + 1
        arr = cv2.GaussianBlur(arr, (k_size, k_size), 0)

    # Aplikuje bilaterální filtr pro inteligentní vyhlazení, které zachovává hrany.
    if use_artistic_smoothing and artistic_smoothing_strength > 0:
        # Převede hodnotu posuvníku (0-100) na parametr sigma pro filtr.
        sigma_val = int(artistic_smoothing_strength * 1.5)
        # Průměr okolí pixelu; 9 je dobrá výchozí hodnota.
        diameter = 9
        arr = cv2.bilateralFilter(arr, diameter, sigma_val, sigma_val)

    # Invertuje hodnoty jasu, pokud je povoleno.
    if invert_colors:
        arr = 255 - arr

    # Převede finální pole NumPy zpět na obrázkový formát PIL.
    return Image.fromarray(arr)

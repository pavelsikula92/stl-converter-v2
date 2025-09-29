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
) -> Image.Image:

    # --- 1. VSTUP A PŘÍPRAVA ---
    # Pokud na vstupu není žádný obrázek, vrátí se malý černý čtverec a aplikace nespadne.
    # Převod na grayscale (mód "L" - Luminance), pro výškovou mapu je podstatná pouze černobílá/šedá.
    # Konverze z obrázkového formátu PIL na matematickou mřížku čísel (NumPy pole).
    # Změna datového typu na float32 (desetinná čísla) pro zachování detailu.

    if not pil_image:
        return Image.new("L", (100, 100), 0)

    arr = np.array(pil_image.convert("L"), dtype=np.uint8)
    arr_float = arr.astype(np.float32)

    # --- 2. TONÁLNÍ ÚPRAVY (JAS A KONTRAST) ---
    # Aplikace jasu: Vynásobení hodnot všech pixelů.
    # Aplikace kontrastu: roztahuje nebo stlačuje rozdíly mezi světlými a tmavými tóny okolo středu (128).
    # Ořezání hodnot (clipping): Zajistí, že všechny hodnoty pixelů zůstanou v platném rozsahu 0-255 po předchozích úpravách.
    # Převod zpět na 8-bitová celá čísla pro další operace v OpenCV.

    if brightness != 1.0:
        arr_float *= brightness
    if contrast != 1.0:
        arr_float = 128 + contrast * (arr_float - 128)

    arr = np.clip(arr_float, 0, 255).astype(np.uint8)

    # --- 3. PRAHOVÁNÍ (THRESHOLDING) ---
    # Pokud je prahování aktivní, převede obrázek na čistě černobílý. Vše pod prahem je černé (0), vše nad ním je bílé (255).

    if use_threshold:
        _, arr = cv2.threshold(arr, threshold_level, 255, cv2.THRESH_BINARY)

    # --- 4. MORFOLOGICKÉ A TVAROVÉ OPERACE ---
    # Buď se provede obtažení (stroke), nebo eroze/dilatace. Tyto operace se vzájemně vylučují.
    # Pokud je aktivní obtažení (stroke):
    # Vytvoření dočasného binárního obrázku, pokud ještě neexistuje z kroku prahování.
    # Nalezení všech vnějších obrysů (kontur) tvarů v obrázku.
    # Vytvoření nového, prázdného (černého) obrázku.
    # Vykreslení nalezených obrysů danou tloušťkou na černý podklad.
    # Pokud se neprovádí obtažení:
    # Dilatace: "Ztuční" nebo "rozšíří" bílé oblasti v obrázku.
    # Eroze: "Ztenčí" nebo "zúží" bílé oblasti v obrázku.

    if use_stroke:
        binary_src = (
            arr if use_threshold else cv2.threshold(arr, 127, 255, cv2.THRESH_BINARY)[1]
        )
        contours, _ = cv2.findContours(
            binary_src, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        arr = np.zeros_like(arr)
        cv2.drawContours(arr, contours, -1, 255, thickness=int(stroke_thickness))
    else:
        if dilate > 0:
            kernel_d = np.ones((2 * dilate + 1, 2 * dilate + 1), np.uint8)
            arr = cv2.dilate(arr, kernel_d, iterations=1)
        if erode > 0:
            kernel_e = np.ones((2 * erode + 1, 2 * erode + 1), np.uint8)
            arr = cv2.erode(arr, kernel_e, iterations=1)

    # --- 5. ČIŠTĚNÍ A ZJEMNĚNÍ (FILTRY) ---
    # Redukce šumu: Aplikuje mediánový filtr, který efektivně odstraňuje šum (relikty).
    # Zjemnění/Rozmazání: Gaussovský filtr pro zjemnění hran a odstranění jemných detailů.

    if noise_reduction > 0:
        k_size = 2 * noise_reduction + 1
        arr = cv2.medianBlur(arr, k_size)
    if smoothing > 0.0:
        arr = cv2.GaussianBlur(arr, (0, 0), sigmaX=smoothing, sigmaY=smoothing)

        # --- 6. FINÁLNÍ ÚPRAVY A VÝSTUP ---
    # Inverze barev: Pokud je aktivní, obrátí hodnoty (černá se stane bílou a naopak).
    # Převod finálního NumPy pole zpět na obrázkový formát PIL, který je vrácen jako výstup funkce.

    if invert_colors:
        arr = 255 - arr

    return Image.fromarray(arr)

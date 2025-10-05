import numpy as np
import pyvista as pv
import traceback
from PIL import Image, ImageOps


# Hlavní funkce pro konverzi obrázku na STL.
# Vstupem je zpracovaný PIL obrázek a slovník s parametry.
# Výstupem je buď True (úspěch), nebo objekt výjimky (chyba).


def image_to_stl(processed_pil_image, stl_path, params, progress_callback):
    """
    Konvertuje zpracovaný obrázek na optimalizovaný STL soubor pomocí PyVista.
    Tato verze používá robustní architekturu s lineární přípravou dat.
    """
    try:
        # --- KROK 1: PŘÍPRAVA VSTUPNÍCH DAT ---
        progress_callback(5)
        # Nastavení maximálního rozměru obrázku pro zpracování.
        MAX_DIMENSION = 800
        img = processed_pil_image.copy()

        # Zmenšení obrázku, pokud přesahuje maximální rozměr, pro optimalizaci výkonu.
        if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

        # Aplikace zrcadlení, pokud je vyžadováno.
        if params.get("mirror_output", False):
            img = ImageOps.mirror(img)

        # Převod obrázku na NumPy pole a normalizace hodnot jasu (0-255) na rozsah (0.0-1.0).
        pixel_data = np.array(img).astype(np.float32)
        # Základní logika je nastavena tak, že tmavší barva znamená vyšší bod (1.0 - ...).
        normalized_heights = 1.0 - (pixel_data / 255.0)

        img_width, img_height = img.size
        # Kontrola, zda obrázek není příliš malý pro generování.
        if img_width < 2 or img_height < 2:
            raise ValueError("Obrázek je pro konverzi příliš malý.")

        # Načtení parametrů modelu (cílové rozměry v mm) ze slovníku `params`.
        model_width_mm = params["model_width_mm"]
        base_height = params["base_height"]
        model_height = params["model_height"]
        # Výpočet měřítka pro převod pixelových souřadnic na reálné jednotky (milimetry).
        scale_factor = model_width_mm / img_width

        progress_callback(20)

        # Zpracování speciálního případu pro export pouze 2.5D povrchu (bez tloušťky).

        if params.get("export_relief_only", False):
            print("Exportuji pouze 2.5D reliéf bez tloušťky.")

            # Vytvoření mračna bodů a následně 2D povrchu pomocí Delaunayovy triangulace.

            x = np.arange(img_width) * scale_factor
            y = np.arange(img_height) * scale_factor
            xx, yy = np.meshgrid(x, y)
            zz = base_height + (normalized_heights * model_height)
            points = np.vstack((xx.ravel(), yy.ravel(), zz.ravel())).T
            surface = pv.PolyData(points).delaunay_2d()
            progress_callback(70)
            # Zjednodušení (decimace) 2D povrchu pro snížení počtu polygonů.
            simplified_surface = surface.decimate(0.98)
            # Uložení zjednodušeného povrchu a ukončení funkce.
            simplified_surface.save(stl_path, binary=True)
            progress_callback(100)
            return True

        # --- LOGIKA PRO VŠECHNY PEVNÉ MODELY ---
        # Vytvoření mřížky XY souřadnic pro horní (reliéf) a spodní (podstava) plochu.

        x = np.arange(img_width) * scale_factor
        y = np.arange(img_height) * scale_factor

        # Pokud je aktivní volba "cutting margin", spodní mřížka se rozšíří o daný okraj.

        if params.get("use_cutting_margin", False):
            margin = 1.0
            x = np.linspace(np.min(x) - margin, np.max(x) + margin, img_width)
            y = np.linspace(np.min(y) - margin, np.max(y) + margin, img_height)

        xx, yy = np.meshgrid(x, y)
        # Výpočet Z souřadnic pro horní plochu na základě výškové mapy.
        zz_top = base_height + (normalized_heights * model_height)
        # Nastavení Z souřadnic pro spodní plochu na konstantní nulu.
        zz_base = np.zeros_like(zz_top)

        # Vytvoření 3D objemové mřížky (StructuredGrid) ze dvou vrstev bodů (spodní a horní).
        grid = pv.StructuredGrid()
        grid.dimensions = [img_width, img_height, 2]

        bottom_points = np.vstack((xx.ravel(), yy.ravel(), zz_base.ravel())).T
        top_points = np.vstack((xx.ravel(), yy.ravel(), zz_top.ravel())).T
        grid.points = np.vstack([bottom_points, top_points])
        progress_callback(70)

        # Extrakce vnějšího povrchu z objemové mřížky. Tímto krokem vznikne vodotěsné 3D těleso.
        print("Vytvářím 3D těleso z objemové mřížky...")
        # Převod povrchu na síť trojúhelníků (pojistka pro maximální kompatibilitu).
        solid_mesh = grid.extract_surface().triangulate()
        print(f"Model vytvořen s {solid_mesh.n_cells} trojúhelníky.")

        progress_callback(90)
        print("Ukládám finální STL soubor...")

        # Finální vyčištění geometrie (sloučení duplicitních bodů) a uložení do binárního STL souboru.
        solid_mesh = solid_mesh.clean()
        if solid_mesh is None:
            raise ValueError("Chyba: Výsledná síť je None a nelze ji uložit jako STL.")
        solid_mesh.save(stl_path, binary=True)

        progress_callback(100)
        return True

    # Zachycení jakékoliv výjimky během procesu, výpis kompletního tracebacku do konzole a vrácení objektu chyby.
    except Exception as e:
        print("!!! CHYBA BĚHEM GENERACE STL !!!")
        traceback.print_exc()
        return e

import numpy as np
import pyvista as pv
import traceback
from PIL import Image, ImageOps


def image_to_stl(processed_pil_image, stl_path, params, progress_callback):
    """
    Konvertuje zpracovaný obrázek na optimalizovaný STL soubor pomocí PyVista.
    Implementuje robustní generování plné podstavy pomocí booleovských operací.
    """
    try:
        # 1. PŘÍPRAVA DAT A VYTVOŘENÍ MRAČNA BODŮ
        # Pojistka, která zmenší příliš velké obrázky na maximální rozměr, aby se předešlo problémům s pamětí.
        # Data z obrázku jsou převedena na normalizované výšky (0.0 až 1.0) a přepočítána na reálné souřadnice v milimetrech.
        # Ze souřadnicových mřížek (xx, yy, zz) je vytvořena jedna datová struktura: mračno bodů (point cloud), což je seznam nespojených [x, y, z] souřadnic.

        progress_callback(5)
        MAX_DIMENSION = 800
        img = processed_pil_image.copy()

        if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

        if params.get("mirror_output", False):
            img = ImageOps.mirror(img)

        pixel_data = np.array(img).astype(np.float32)
        normalized_heights = pixel_data / 255.0

        img_width, img_height = img.size
        if img_width < 2 or img_height < 2:
            raise ValueError("Obrázek je příliš malý.")

        model_width_mm = params["model_width_mm"]
        base_height = params["base_height"]
        model_height = params["model_height"]
        scale_factor = model_width_mm / img_width

        progress_callback(20)
        x = np.arange(img_width) * scale_factor
        y = np.arange(img_height) * scale_factor
        xx, yy = np.meshgrid(x, y)
        zz = base_height + (normalized_heights * model_height)

        points = np.vstack((xx.ravel(), yy.ravel(), zz.ravel())).T
        cloud = pv.PolyData(points)
        surface = cloud.delaunay_2d()
        progress_callback(40)

        # --- 2. VYTVOŘENÍ A ZJEDNODUŠENÍ POVRCHU ---
        # Mračno bodů je načteno do datové struktury PyVista (PolyData).
        # Pomocí Delaunayovy triangulace je z nesouvislých bodů vytvořen souvislý povrch (síť trojúhelníků).
        # Pomocí decimace je povrch zjednodušen. Většina (zde 98 %) trojúhelníků je odstraněna, přičemž jsou zachovány důležité detaily a hrany.

        target_reduction = 0.98
        print(f"Počet trojúhelníků PŘED: {surface.n_cells}")
        simplified_surface = surface.decimate(target_reduction)
        print(f"Počet trojúhelníků PO:   {simplified_surface.n_cells}")
        progress_callback(70)

        # --- 3. VYTVOŘENÍ FINÁLNÍHO 3D TĚLESA (LOGICKÉ VĚTVENÍ) ---
        # Program se rozhoduje, jaký typ 3D tělesa vytvořit, na základě voleb v GUI.

        solid_mesh = None
        if params.get("export_relief_only", False):
            print("Exportuji pouze 2.5D reliéf bez tloušťky.")
            solid_mesh = simplified_surface

        # Varianta "Flat bottom"
        # Vytvoří se tenká skořepina z reliéfu, aby měla objem pro booleovskou operaci.
        # Vypočítá se půdorys modelu, případně zvětšený o řezný okraj (cutting margin).
        # Vytvoří se kvádr podstavy, který je záměrně o kousek vyšší, aby zaručil robustní objemový průnik s reliéfem.
        # Kvádr podstavy se převede na síť trojúhelníků, což je podmínka pro booleovskou operaci.
        # Pomocí booleovské operace "union" se reliéf a podstava spojí do jednoho vodotěsného 3D tělesa.

        elif params.get("flat_bottom", False):
            print("Generuji model s rovnou spodní plochou...")
            relief_shell = simplified_surface.extrude([0, 0, -0.01], capping=True)

            bounds = list(simplified_surface.bounds)

            if params.get("use_cutting_margin", False):
                print("Přidávám 1mm okraj k podstavě...")
                margin = 1.0
                bounds[0] -= margin
                bounds[1] += margin
                bounds[2] -= margin
                bounds[3] += margin

            # Vytvoření záměrného přesahu pro robustní booleovskou operaci
            overlap = model_height * 0.05  # 5% přesah
            base_box_bounds = [
                bounds[0],
                bounds[1],
                bounds[2],
                bounds[3],
                0,
                base_height + overlap,
            ]
            base_box = pv.Box(bounds=base_box_bounds)

            print("Provádím booleovskou operaci 'union'...")
            solid_mesh = relief_shell.boolean_union(base_box.triangulate())

        # Použije se jednoduché "vytažení" (extrude) povrchu směrem dolů. Rychlé, ale vytváří negativní reliéf na spodní straně.

        else:  # Výchozí chování
            print("Generuji model s negativním reliéfem na spodní ploše...")
            solid_mesh = simplified_surface.extrude([0, 0, -base_height], capping=True)

        # --- 4. FINALIZACE A ULOŽENÍ ---
        # Výsledný 3D model je "vyčištěn", aby se odstranily případné geometrické vady po komplexních operacích.
        # Hotový a vyčištěný model se uloží do binárního STL souboru.

        progress_callback(90)
        print("Ukládám finální, optimalizovaný STL soubor...")

        if isinstance(solid_mesh, pv.PolyData):
            solid_mesh.clean(inplace=True)

        solid_mesh.save(stl_path, binary=True)

        progress_callback(100)
        return True

    # --- 5. ZPRACOVÁNÍ CHYB (ERROR HANDLING) ---
    # Celá funkce je obalena v bloku try...except. Pokud jakákoliv operace selže,
    # aplikace nespadne, ale zachytí chybu, vypíše detaily do terminálu a zobrazí chybovou hlášku v GUI.

    except Exception as e:
        print("!!! CHYBA BĚHEM GENERACE STL POMOCÍ PYVISTA !!!")
        traceback.print_exc()
        return e

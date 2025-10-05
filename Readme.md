For English scroll down

Jednoduchá, ale výkonná desktopová aplikace v Pythonu pro převod 2D obrázků na 3D modely (reliéfy) ve formátu STL, připravené pro 3D tisk. Aplikace nabízí širokou škálu úprav obrazu v reálném čase a pokročilé možnosti generování 3D modelu.

Klíčové Funkce
Interaktivní Náhled: Načtení a okamžitý náhled obrázku s podporou plynulého zoomu a posouvání.


Úpravy Obrazu:
Jas, kontrast a vyhlazování (Gaussian Blur).
Redukce šumu (Median Blur) pro čištění nekvalitních předloh.
Prahování (Thresholding) pro převod na čistě černobílý obraz.
Morfologické Operace:
Dilatace a eroze pro ztučnění nebo ztenčení detailů.
"Obtažení" (Stroke) pro vytvoření modelu pouze z hran původních tvarů.

Pokročilý Export STL:
Standardní model s inverzním reliéfem na spodní straně.
Model s dokonale rovnou podstavou (generováno pomocí robustních booleovských operací).
Možnost přidat řezný okraj (rámeček/podstavec) k rovné podstavě.
Export pouze jako 2.5D reliéf bez tloušťky.


Flexibilita Výstupu:
Inverze barev pro snadnou tvorbu pozitivních modelů (bílá je vysoká) i negativních forem (černá je vysoká).
Zrcadlení výstupu.


Nástroje pro Maskování: 
Ořez obrázku na základní tvary (obdélník, mnohoúhelník atd.).


Technologie
Python 3
Tkinter (ttk.Style) pro moderní a multiplatformní GUI.
Pillow (PIL) pro základní manipulaci s obrázky.
NumPy a OpenCV pro rychlé a efektivní zpracování obrazu.
PyVista pro robustní generování, optimalizaci a ukládání 3D meshe.

Instalace a Spuštění
Naklonuj repozitář:

Bash

git clone https://github.com/pavelsikula92/stl-converter-v2.git
cd stl-converter-v2

Vytvoř a aktivuj virtuální prostředí:
Bash
Vytvoření
python -m venv .venv

Aktivace (Windows)
.venv\Scripts\activate

Aktivace (Linux/macOS)
source .venv/bin/activate

Nainstaluj závislosti:
Bash
pip install -r requirements.txt

Spusť aplikaci:
Bash
python src/main.py


Použití
Po spuštění klikni na "Load Image" a vyber obrázek.
V záložkách "Adjustments" a "Masking Tools" uprav obrázek do požadované podoby. Náhled se aktualizuje v reálném čase.
V záložce "File & Model" nastav cílové rozměry modelu a pokročilé exportní volby.
Klikni na "Convert to STL" a vyber, kam se má finální soubor uložit.

Doporučené Postupy a Příklady Použití
Kombinací pokročilých voleb můžete dosáhnout různých typů modelů. Zde jsou nejčastější scénáře:

1. Standardní 3D Reliéf (jako mince nebo plaketa)
Cíl: Pevný 3D objekt s hladkým reliéfem a rovnou zadní stranou.

Generate Flat Bottom: Zapnuto

Artistic Smoothing: Zapnuto (Síla Strength podle potřeby, např. 50-75)

Invert Height (light is high): Vypnuto (výchozí stav, tmavá je vysoká)

Výsledek: Toto je nejběžnější použití. Flat Bottom zajistí pevnou podstavu. Artistic Smoothing vytvoří kvalitní, hladký povrch se zachováním hran, podobně jako komerční nástroje.

2. Vytvoření Formy (negativ)
Cíl: Vytvořit model, který může sloužit jako forma pro odlévání.

Generate Flat Bottom: Zapnuto

Invert Height (light is high): Zapnuto

Mirror output: Zapnuto (většinou doporučeno)

Artistic Smoothing: Zapnuto

Výsledek: Klíčem je Invert Height, které z "vystouplého" udělá "prohloubený" model. Mirror output je potřeba, aby výsledný odlitek nebyl zrcadlově obrácený.

3. Reliéf s Rámečkem / Podstavcem
Cíl: Reliéf umístěný na podstavě, která ho mírně přesahuje.

Generate Flat Bottom: Zapnuto

Add Cutting Margin: Zapnuto

Artistic Smoothing: Zapnuto

Výsledek: Kombinace Flat Bottom a Cutting Margin vytvoří model, kde podstava přesahuje reliéf o 1 mm na každé straně. Ideální pro vytvoření čistého okraje nebo pro další opracování.

4. Rychlý "Pixelovaný" Náhled
Cíl: Okamžité vygenerování modelu bez pokročilého vyhlazování.

Artistic Smoothing: Vypnuto

Gaussian Smoothing: 0

Noise Reduction: 0

Výsledek: Vypnutím všech vyhlazovacích filtrů získáte "surový", doslovný převod pixelů na výšku. Generování je bleskové, ale výsledek je vizuálně "zubatý". Hodí se pro rychlé testy.




English


Image to STL Converter v2.0
A simple yet powerful desktop application built in Python for converting 2D images into 3D models (reliefs) in STL format, ready for 3D printing. The application offers a wide range of real-time image adjustments and advanced 3D model generation options.

Key Features
Interactive Preview: Load and instantly preview your image with support for smooth zooming and panning.

Image Adjustments:
Brightness, contrast, and smoothing (Gaussian Blur).
Noise reduction (Median Blur) for cleaning up low-quality source images.
Thresholding to convert the image to pure black and white.
Morphological Operations:
Dilate and Erode to thicken or thin details.
Stroke to create a model based only on the edges of the original shapes.


Advanced STL Export:
Standard model with an inverse relief on the bottom side.
Model with a perfectly flat base (generated using robust boolean operations).
Option to add a cutting margin (a frame/pedestal) to the flat base.
Export as a 2.5D relief only, with no thickness.


Output Flexibility:
Invert colors for easy creation of positive models (white is high) and negative molds (black is high).
Mirror the final output.


Masking Tools:
Crop the image to basic shapes (rectangle, polygon, etc.).


Technology
Python 3
Tkinter (ttk.Style) for a modern and cross-platform GUI.
Pillow (PIL) for basic image manipulation.
NumPy & OpenCV for fast and efficient image processing.
PyVista for robust 3D mesh generation, optimization, and saving.

Installation and Usage

Clone the repository:
Bash
git clone https://github.com/pavelsikula92/stl-converter-v2.git
cd stl-converter-v2


Create and activate a virtual environment:
Bash
Create
python -m venv .venv

Activate(Windows)
.venv\Scripts\activate

Activate (Linux/macOS)
source .venv/bin/activate


Install dependencies:
Bash
pip install -r requirements.txt


Run the application:
Bash
python src/main.py


How to Use
After launching, click "Load Image" and select an image file.
In the "Adjustments" and "Masking Tools" tabs, edit the image to your desired appearance. The preview will update in real-time.
In the "File & Model" tab, set the target dimensions for your model and configure the advanced export options.
Click "Convert to STL" and choose where to save the final file.

Recommended Workflows and Usage Examples

By combining the advanced options, you can achieve different types of models. Here are the most common scenarios:

1. Standard 3D Relief (like a coin or plaque)
Goal: A solid 3D object with a smooth relief and a flat back.

Generate Flat Bottom: Enabled

Artistic Smoothing: Enabled (set Strength as needed, e.g., 50-75)

Invert Height (light is high): Disabled (default state, dark is high)

Result: This is the most common use case. Flat Bottom ensures a solid base. Artistic Smoothing creates a high-quality, smooth surface while preserving edges, similar to commercial tools.

2. Creating a Mold (Negative)
Goal: Create a model that can be used as a mold for casting.

Generate Flat Bottom: Enabled

Invert Height (light is high): Enabled

Mirror output: Enabled (usually recommended)

Artistic Smoothing: Enabled

Result: The key is Invert Height, which turns a "raised" model into a "recessed" one. Mirror output is often needed so that the final cast is not a mirror image.

3. Relief with a Frame / Pedestal
Goal: A relief placed on a base that is slightly larger than the relief itself.

Generate Flat Bottom: Enabled

Add Cutting Margin: Enabled

Artistic Smoothing: Enabled

Result: The combination of Flat Bottom and Add Cutting Margin creates a model where the base extends beyond the relief by 1mm on each side. Ideal for creating a clean border or for further processing.

4. Quick "Pixelated" Preview
Goal: Instantly generate a model without advanced smoothing.

Artistic Smoothing: Disabled

Gaussian Smoothing: 0

Noise Reduction: 0

Result: By disabling all smoothing filters, you get a "raw," literal translation of pixels to height. The generation is lightning-fast, but the result is visually "jagged." This is useful for quick tests.

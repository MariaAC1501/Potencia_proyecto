"""Download the published UW IEEE118 diagram and make an explicitly annotated crop."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'escenario1_assets'
URL = 'https://labs.ece.uw.edu/pstca/pf118/118bus6.tif'
PAGE = 'https://labs.ece.uw.edu/pstca/pf118/pg_tca118bus.htm'


def main():
    ASSETS.mkdir(exist_ok=True)
    original = ASSETS / 'IEEE118_unifilar_UW.tif'
    if not original.exists():
        original.write_bytes(urlopen(URL, timeout=30).read())
    with Image.open(original) as source:
        image = source.convert('RGB')
    image.save(ASSETS / 'IEEE118_unifilar_UW.png')
    box = (1300, 1000, 2350, 2850)
    crop = image.crop(box)
    crop.save(ASSETS / 'unifilar_region_26_30.png')
    overlay = Image.new('RGBA', crop.size)
    draw = ImageDraw.Draw(overlay)
    # Endpoints verified against bus26 TannrsCk V1 / bus30 Sorenson V1 in UW CDF.
    path = [(550,1660),(550,1700),(345,1700),(345,1080),(200,360),(200,265)]
    draw.line(path, fill=(232,75,25,140), width=16)
    font_path = Path('C:/Windows/Fonts/arial.ttf')
    font = ImageFont.truetype(str(font_path), 29) if font_path.exists() else ImageFont.load_default(size=29)
    small = ImageFont.truetype(str(font_path), 24) if font_path.exists() else ImageFont.load_default(size=24)
    for point, origin, text in [((200,265),(440,420),'30 - Sorenson 345 kV'),
                                ((550,1660),(600,1580),'26 - Tanners Creek\n345 kV')]:
        x,y = origin
        bounds = draw.multiline_textbbox((x,y), text, font=font)
        draw.rectangle((bounds[0]-10,bounds[1]-10,bounds[2]+10,bounds[3]+10), fill=(255,249,229,245))
        draw.multiline_text(origin, text, font=font, fill=(139,40,0,255), spacing=5)
        px,py = point
        draw.ellipse((px-23,py-23,px+23,py+23), outline=(210,55,0,255), width=6)
        draw.line([point, origin], fill=(210,55,0,255), width=4)
    draw.rectangle((5,4,1045,55), fill=(255,249,229,245))
    draw.text((18,12),'Recorte UW / AEP + anotaciones propias: salida de linea 26-30',font=small,fill=(139,40,0,255))
    Image.alpha_composite(crop.convert('RGBA'), overlay).convert('RGB').save(ASSETS / 'unifilar_region_26_30_anotado.png')
    metadata = {'source_url':URL,'source_page':PAGE,
        'citation':'R. Christie, University of Washington, Power Systems Test Case Archive, mayo de 1993. Diagrama AEP diciembre de 1962.',
        'sha256_tif':hashlib.sha256(original.read_bytes()).hexdigest(),
        'crop_original_pixels':box,'annotation':'Resaltado y etiquetas propios; original conservado sin modificaciones.',
        'bus26':'TannrsCk V1 / Tanners Creek 345 kV','bus30':'Sorenson V1 / Sorenson 345 kV',
        'identity_check':'UW ieee118cdf.txt filas26 y30; kV en IEEE118.xlsx. Cruces sin barra no son nuevos nodos.'}
    (ASSETS / 'fuente_unifilar.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Unifilar publicado y recorte anotado listos en escenario1_assets/.')


if __name__ == '__main__':
    main()

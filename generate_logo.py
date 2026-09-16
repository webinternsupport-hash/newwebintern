import os
from PIL import Image, ImageDraw, ImageFont

def create_brand_logo():
    width, height = 900, 260
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw circular emblem background
    draw.ellipse([20, 20, 220, 220], fill='#0F172A', outline='#2563EB', width=8)
    
    try:
        font_lg = ImageFont.truetype('arialbd.ttf', 68)
        font_sm = ImageFont.truetype('arial.ttf', 24)
        font_icon = ImageFont.truetype('arialbd.ttf', 96)
    except Exception:
        font_lg = font_sm = font_icon = ImageFont.load_default()
        
    # Draw emblem icon text 'W'
    draw.text((120, 115), 'W', fill='#3B82F6', font=font_icon, anchor='mm')
    
    # Draw brand typography
    draw.text((250, 65), 'WEB INTERN', fill='#0F172A', font=font_lg)
    draw.text((252, 145), 'VIRTUAL ACADEMIC PLATFORM', fill='#2563EB', font=font_sm)
    
    out_path = os.path.join(os.path.dirname(__file__), 'static', 'assets', 'webintern_brand_logo.png')
    img.save(out_path)
    print(f"Saved custom brand logo to: {out_path}")

if __name__ == '__main__':
    create_brand_logo()

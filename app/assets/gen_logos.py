from PIL import Image
import base64, io, os

assets = r'C:\Users\39329\Desktop\CinePosto\Frontend\assets'
size = (80, 80)

for name, varname in [('post.jpg', 'LOGO_POST'), ('the space.jpg', 'LOGO_SPACE'), ('uci.png', 'LOGO_UCI')]:
    img = Image.open(os.path.join(assets, name)).convert('RGBA')
    img.thumbnail(size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode()
    uri = f'data:image/png;base64,{b64}'
    outpath = os.path.join(assets, f'{varname.lower()}.txt')
    with open(outpath, 'w') as f:
        f.write(uri)
    print(f'{varname}: {len(uri)} chars')

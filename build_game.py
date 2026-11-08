import base64
from pathlib import Path
from PIL import Image, ImageFilter
from collections import deque

def make_sprite(in_path, out_path):
    img = Image.open(in_path).convert("RGBA")
    w, h = img.size
    px = img.load()
    mask = Image.new("L", (w, h), 0)
    mp = mask.load()

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if y < h * 0.13 or y > h * 0.755 or x < w * 0.19 or x > w * 0.86:
                continue

            # Exclude bright white/grey gaps between arms and torso (y: 0.36..0.50)
            in_arm_gap = ((w * 0.30 <= x <= w * 0.385) or (w * 0.615 <= x <= w * 0.70)) and (h * 0.35 <= y <= h * 0.50)
            if in_arm_gap and (r > 165 and g > 165 and b > 155 and abs(r - b) < 35):
                continue

            cloud_cx, cloud_cy = w * 0.52, h * 0.585
            cloud_rx, cloud_ry = w * 0.325, h * 0.165
            in_cloud = ((x - cloud_cx) / cloud_rx) ** 2 + ((y - cloud_cy) / cloud_ry) ** 2 <= 1.08
            in_body = (w * 0.28 <= x <= w * 0.75) and (h * 0.13 <= y <= h * 0.58)
            in_staff = (w * 0.30 <= x <= w * 0.46) and (h * 0.18 <= y <= h * 0.34) and (r > b + 40 and r > 100)
            in_kanji = (w * 0.53 <= x <= w * 0.63) and (h * 0.35 <= y <= h * 0.44)
            in_boots_or_wrists = (
                ((w * 0.26 <= x <= w * 0.36 or w * 0.65 <= x <= w * 0.76) and (h * 0.45 <= y <= h * 0.52))
                or ((w * 0.40 <= x <= w * 0.66) and (h * 0.52 <= y <= h * 0.61))
            )

            if not (in_cloud or in_body or in_staff):
                continue

            is_warm = (r > b + 24 and g > b - 8 and r > 80) or (r > 185 and g > 145 and b < 155)
            is_dark_hair_or_cloth = (r < 95 and g < 105 and b < 145) or (b > r + 15 and b < 165 and in_boots_or_wrists)
            is_green_tree = (g > r + 6 and g > b + 10 and y > h * 0.60)
            is_sky_or_dome = (b >= r - 14 and (r > 90 or g > 95 or b > 110)) and not (in_kanji or in_boots_or_wrists)

            if in_staff or in_kanji or in_boots_or_wrists:
                mp[x, y] = 255
            elif is_warm and not is_green_tree:
                mp[x, y] = 255
            elif in_body and is_dark_hair_or_cloth and not is_sky_or_dome:
                if y < h * 0.29 and not (w * 0.41 <= x <= w * 0.58):
                    continue
                mp[x, y] = 255

    visited = [[False]*w for _ in range(h)]
    clean_mask = Image.new("L", (w, h), 0)
    cmp = clean_mask.load()
    for y in range(h):
        for x in range(w):
            if mp[x, y] > 0 and not visited[y][x]:
                q = deque([(x, y)])
                visited[y][x] = True
                comp = [(x, y)]
                while q:
                    cx, cy = q.popleft()
                    for dx, dy in ((-1,0),(1,0),(0,-1),(0,1)):
                        nx, ny = cx+dx, cy+dy
                        if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and mp[nx, ny] > 0:
                            visited[ny][nx] = True
                            q.append((nx, ny))
                            comp.append((nx, ny))
                if len(comp) > 800:
                    for cx, cy in comp:
                        cmp[cx, cy] = 255

    clean_mask = clean_mask.filter(ImageFilter.MedianFilter(5))
    clean_mask = clean_mask.filter(ImageFilter.GaussianBlur(2.0))

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(img, (0, 0), clean_mask)
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    ratio = 280.0 / out.height
    out = out.resize((int(out.width * ratio), 280), Image.LANCZOS)
    out.save(out_path, optimize=True)
    return base64.b64encode(Path(out_path).read_bytes()).decode("ascii")

b64_pai = make_sprite("/home/ubuntu/bot/downloads/photo_49.jpg", "/home/ubuntu/jogo-nuvem-voadora/pai_sprite.png")
b64_filho = make_sprite("/home/ubuntu/bot/downloads/photo_50.jpg", "/home/ubuntu/jogo-nuvem-voadora/filho_sprite.png")
print("Sprites encoded:", len(b64_pai), len(b64_filho))

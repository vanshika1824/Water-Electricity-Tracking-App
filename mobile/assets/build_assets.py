"""
Script to generate high-resolution branding assets for AquaWatt:
1. logo_droplet.png: Aqua water droplet with lightning bolt emblem.
2. logo_droplet_white.png: Light pale-mint / aqua version for dark teal sidebar.
3. bg_water.png: Calm light aqua-teal liquid surface backdrop.
4. bg_welcome.png: Rich deep ocean-teal botanical water backdrop.
"""

import math
import os
from PIL import Image, ImageDraw, ImageFilter

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))

def create_droplet_icon(filename: str, primary_color=(57, 213, 208), bolt_color=(255, 255, 255), size=(512, 512)):
    # Render at 4x resolution for anti-aliasing
    scale = 4
    w, h = size[0] * scale, size[1] * scale
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = w / 2, h / 2

    # Draw droplet using Bézier / poly points
    # Top tip at (cx, cy - 0.40*h)
    # Bottom circle centered at (cx, cy + 0.10*h) with radius 0.32*h
    tip_y = cy - 0.38 * h
    bottom_cy = cy + 0.08 * h
    r = 0.30 * h

    points = []
    # Right curve from tip to bottom circle
    steps = 60
    for i in range(steps + 1):
        t = i / steps
        # Angle from ~-60 deg to +120 deg
        angle = -math.pi / 2.8 + t * (math.pi + 2 * math.pi / 2.8)
        px = cx + r * math.cos(angle)
        py = bottom_cy + r * math.sin(angle)
        if py >= tip_y:
            points.append((px, py))

    # Construct clean polygon
    poly = [(cx, tip_y)]
    for i in range(steps + 1):
        angle = math.radians(-35 + i * (250 / steps))
        poly.append((cx + r * math.cos(angle), bottom_cy + r * math.sin(angle)))
    poly.append((cx, tip_y))

    # Draw outer glow
    glow_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    glow_draw.polygon(poly, fill=(*primary_color, 160))
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=18 * scale))
    img.paste(glow_img, (0, 0), glow_img)

    # Draw main droplet body with gradient emulation
    draw.polygon(poly, fill=(*primary_color, 255))

    # Inner specular highlight (top left crescent)
    hi_poly = []
    hi_r = r * 0.78
    for i in range(30):
        angle = math.radians(140 + i * (90 / 30))
        hi_poly.append((cx - 15 * scale + hi_r * math.cos(angle), bottom_cy - 15 * scale + hi_r * math.sin(angle)))
    hi_poly.append((cx - 20 * scale, tip_y + 60 * scale))
    draw.polygon(hi_poly, fill=(255, 255, 255, 75))

    # Lightning Bolt Points (centered inside droplet)
    # Scaled to fit comfortably inside droplet
    bolt = [
        (cx + 15 * scale, cy - 130 * scale),   # top right start
        (cx - 55 * scale, cy + 10 * scale),    # mid left
        (cx - 5 * scale,  cy + 10 * scale),    # mid inner
        (cx - 35 * scale, cy + 150 * scale),   # bottom left tip
        (cx + 60 * scale, cy - 15 * scale),    # mid right outer
        (cx + 10 * scale, cy - 15 * scale),    # mid right inner
    ]
    # Draw subtle bolt shadow for contrast
    bolt_shadow = [(x + 4 * scale, y + 4 * scale) for x, y in bolt]
    draw.polygon(bolt_shadow, fill=(6, 78, 90, 140))
    # Draw bolt
    draw.polygon(bolt, fill=(*bolt_color, 255))

    # Downsample with high-quality Lanczos anti-aliasing
    final_img = img.resize(size, Image.Resampling.LANCZOS)
    final_img.save(os.path.join(ASSETS_DIR, filename), "PNG")
    print(f"Created {filename}")


def create_water_background(filename: str, size=(1280, 800), is_dark=False):
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if is_dark:
        # Deep ocean teal to darker teal gradient (#064E5A -> #03252C)
        top_color = (6, 78, 90)
        bot_color = (3, 37, 44)
    else:
        # Calm light aqua surface (#E4F9F6 -> #C6F1EC)
        top_color = (228, 249, 246)
        bot_color = (198, 241, 236)

    # Vertical gradient
    for y in range(h):
        factor = y / float(h)
        r = int(top_color[0] + factor * (bot_color[0] - top_color[0]))
        g = int(top_color[1] + factor * (bot_color[1] - top_color[1]))
        b = int(top_color[2] + factor * (bot_color[2] - top_color[2]))
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

    # Add soft organic fluid waves / caustics
    wave_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    w_draw = ImageDraw.Draw(wave_layer)

    if is_dark:
        wave_color1 = (57, 213, 208, 38)
        wave_color2 = (8, 61, 74, 120)
        wave_color3 = (80, 230, 220, 25)
    else:
        wave_color1 = (57, 213, 208, 55)
        wave_color2 = (255, 255, 255, 80)
        wave_color3 = (180, 245, 240, 70)

    # Wave 1
    points1 = [(0, h)]
    for x in range(0, w + 20, 20):
        y = h * 0.65 + math.sin(x * 0.005) * (h * 0.12) + math.cos(x * 0.008) * (h * 0.06)
        points1.append((x, y))
    points1.append((w, h))
    w_draw.polygon(points1, fill=wave_color1)

    # Wave 2
    points2 = [(0, h)]
    for x in range(0, w + 20, 20):
        y = h * 0.78 + math.cos(x * 0.006) * (h * 0.10) - math.sin(x * 0.004) * (h * 0.05)
        points2.append((x, y))
    points2.append((w, h))
    w_draw.polygon(points2, fill=wave_color2)

    # Soft ambient glow circles (caustic light)
    if is_dark:
        w_draw.ellipse([w * 0.7, -h * 0.2, w * 1.3, h * 0.6], fill=(57, 213, 208, 45))
        w_draw.ellipse([-w * 0.2, h * 0.5, w * 0.5, h * 1.3], fill=(8, 61, 74, 90))
    else:
        w_draw.ellipse([w * 0.6, -h * 0.3, w * 1.2, h * 0.5], fill=(255, 255, 255, 110))
        w_draw.ellipse([-w * 0.1, h * 0.4, w * 0.4, h * 1.2], fill=(57, 213, 208, 40))

    wave_layer = wave_layer.filter(ImageFilter.GaussianBlur(radius=25))
    img = Image.alpha_composite(img, wave_layer)

    img.save(os.path.join(ASSETS_DIR, filename), "PNG")
    print(f"Created {filename}")


if __name__ == "__main__":
    create_droplet_icon("logo_droplet.png", primary_color=(57, 213, 208), bolt_color=(255, 255, 255))
    create_droplet_icon("logo_droplet_white.png", primary_color=(217, 247, 242), bolt_color=(6, 78, 90))
    create_water_background("bg_water.png", is_dark=False)
    create_water_background("bg_welcome.png", is_dark=True)

"""
中秋祝福动画视频生成器
画面：夜空 + 月亮升起 + 灯笼飘动 + 粒子 + 祝福文字
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import os

W, H = 1080, 1920  # 竖版 9:16
FPS = 30
DURATION = 30
TOTAL_FRAMES = FPS * DURATION

# ========== 工具函数 ==========

def lerp(a, b, t):
    return a + (b - a) * t

def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)

def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def load_font(size, bold=True):
    """加载中文字体"""
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    # 找系统中任意 CJK 字体
    import subprocess
    try:
        result = subprocess.run(["fc-list", ":lang=zh", "-f", "%{file}\n"], capture_output=True, text=True)
        fonts = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        if fonts:
            return ImageFont.truetype(fonts[0], size)
    except:
        pass
    return ImageFont.load_default()

# ========== 场景元素绘制 ==========

def draw_night_sky(draw, t):
    """渐变夜空背景"""
    # 深蓝到紫黑渐变
    top_color = (10, 12, 40)
    mid_color = (30, 20, 60)
    bot_color = (50, 30, 70)
    for y in range(H):
        ratio = y / H
        if ratio < 0.5:
            r = lerp(top_color[0], mid_color[0], ratio * 2)
            g = lerp(top_color[1], mid_color[1], ratio * 2)
            b = lerp(top_color[2], mid_color[2], ratio * 2)
        else:
            r = lerp(mid_color[0], bot_color[0], (ratio - 0.5) * 2)
            g = lerp(mid_color[1], bot_color[1], (ratio - 0.5) * 2)
            b = lerp(mid_color[2], bot_color[2], (ratio - 0.5) * 2)
        draw.line([(0, y), (W, y)], fill=(int(r), int(g), int(b)))

def draw_stars(img, t, stars):
    """闪烁星星"""
    draw = ImageDraw.Draw(img, "RGBA")
    for s in stars:
        twinkle = 0.5 + 0.5 * math.sin(t * 2 * math.pi * s["speed"] + s["phase"])
        alpha = int(150 + 105 * twinkle)
        size = s["size"] * (0.7 + 0.3 * twinkle)
        x, y = s["x"], s["y"]
        draw.ellipse([x - size, y - size, x + size, y + size],
                     fill=(255, 255, 220, alpha))

def draw_moon(img, t):
    """月亮从底部升起到中上部"""
    # 升起动画：0~40% 时间从底部升到目标位置
    rise_t = min(t / 0.4, 1.0) if t < 0.4 else 1.0
    rise_t = ease_out_cubic(rise_t)
    
    moon_r = 180
    target_y = 400
    start_y = H + moon_r
    cx = W // 2
    cy = lerp(start_y, target_y, rise_t)
    
    # 月光晕（多层）
    for i in range(6, 0, -1):
        halo_r = moon_r + i * 40
        halo_alpha = int(15 * (7 - i) / 6)
        halo = Image.new("RGBA", (halo_r * 2, halo_r * 2), (0, 0, 0, 0))
        hd = ImageDraw.Draw(halo)
        hd.ellipse([0, 0, halo_r * 2, halo_r * 2], fill=(255, 240, 200, halo_alpha))
        halo = halo.filter(ImageFilter.GaussianBlur(30))
        img.paste(halo, (int(cx - halo_r), int(cy - halo_r)), halo)
    
    # 月亮本体（带纹理感）
    moon = Image.new("RGBA", (moon_r * 2, moon_r * 2), (0, 0, 0, 0))
    md = ImageDraw.Draw(moon)
    # 主体
    md.ellipse([0, 0, moon_r * 2, moon_r * 2], fill=(255, 245, 220))
    # 月海阴影（暗斑）
    md.ellipse([moon_r * 0.5, moon_r * 0.6, moon_r * 1.3, moon_r * 1.4],
               fill=(235, 220, 190))
    md.ellipse([moon_r * 1.1, moon_r * 0.4, moon_r * 1.7, moon_r * 1.0],
               fill=(240, 225, 195))
    md.ellipse([moon_r * 0.3, moon_r * 1.2, moon_r * 0.9, moon_r * 1.7],
               fill=(238, 222, 192))
    # 高光
    md.ellipse([moon_r * 0.6, moon_r * 0.3, moon_r * 1.2, moon_r * 0.9],
               fill=(255, 252, 240))
    
    img.paste(moon, (int(cx - moon_r), int(cy - moon_r)), moon)
    return cy  # 返回月亮 y 坐标

def draw_lanterns(img, t, lanterns):
    """飘动的灯笼"""
    for lan in lanterns:
        # 摆动
        sway = math.sin(t * 2 * math.pi * lan["sway_speed"] + lan["phase"]) * 30
        x = lan["x"] + sway
        y = lan["y"] + math.sin(t * 2 * math.pi * lan["sway_speed"] * 0.7 + lan["phase"]) * 15
        
        lw, lh = lan["size"]
        # 灯笼绳
        draw = ImageDraw.Draw(img, "RGBA")
        draw.line([(x, 0), (x, y - lh // 2)], fill=(80, 50, 30, 180), width=2)
        
        # 灯笼光晕
        halo = Image.new("RGBA", (lw * 3, lh * 3), (0, 0, 0, 0))
        hd = ImageDraw.Draw(halo)
        hd.ellipse([0, 0, lw * 3, lh * 3], fill=(255, 150, 50, 40))
        halo = halo.filter(ImageFilter.GaussianBlur(20))
        img.paste(halo, (int(x - lw * 1.5), int(y - lh * 1.5)), halo)
        
        # 灯笼本体（椭圆）
        draw.ellipse([x - lw // 2, y - lh // 2, x + lw // 2, y + lh // 2],
                     fill=(200, 40, 30))
        # 灯笼内光
        draw.ellipse([x - lw // 2 + 8, y - lh // 2 + 8, x + lw // 2 - 8, y + lh // 2 - 8],
                     fill=(255, 120, 40))
        # 灯笼条纹
        draw.line([(x - lw // 2, y), (x + lw // 2, y)], fill=(150, 30, 20), width=2)
        # 顶部和底部装饰
        draw.rectangle([x - 10, y - lh // 2 - 4, x + 10, y - lh // 2], fill=(100, 60, 30))
        draw.rectangle([x - 10, y + lh // 2, x + 10, y + lh // 2 + 4], fill=(100, 60, 30))
        # 流苏
        draw.line([(x, y + lh // 2 + 4), (x, y + lh // 2 + 20)], fill=(220, 180, 30), width=3)

def draw_particles(img, t, particles):
    """金色粒子飞舞"""
    draw = ImageDraw.Draw(img, "RGBA")
    for p in particles:
        # 粒子上升 + 漂移
        px = p["x"] + math.sin(t * 2 * math.pi * p["drift_speed"] + p["phase"]) * 40
        py = p["y"] - (t * p["rise_speed"] * 200) % H
        if py < 0:
            py += H
        size = p["size"]
        alpha = int(p["alpha"] * (0.6 + 0.4 * math.sin(t * 3 + p["phase"])))
        # 发光粒子
        for r in range(3, 0, -1):
            a = alpha // (r * 2)
            draw.ellipse([px - size * r, py - size * r, px + size * r, py + size * r],
                         fill=(255, 215, 100, a))

def draw_clouds(img, t):
    """远处淡云"""
    draw = ImageDraw.Draw(img, "RGBA")
    for i in range(3):
        cx = (W * (0.2 + i * 0.3) + t * 10) % (W + 400) - 200
        cy = 250 + i * 80
        for j in range(5):
            ox = j * 50 - 100
            oy = math.sin(j) * 15
            r = 60 + j * 5
            draw.ellipse([cx + ox - r, cy + oy - r * 0.5, cx + ox + r, cy + oy + r * 0.5],
                         fill=(80, 70, 110, 40))

def draw_text_sequence(img, t, fonts):
    """分阶段显示文字"""
    draw = ImageDraw.Draw(img, "RGBA")
    
    # 阶段1 (3-8s): "中秋" 大字渐显
    if 3 <= t <= 8:
        local_t = (t - 3) / 5
        alpha = int(255 * ease_in_out(min(local_t * 2, 1.0)))
        if local_t > 0.7:
            alpha = int(255 * (1 - (local_t - 0.7) / 0.3 * 0.3))
        font = fonts["huge"]
        text = "中 秋"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (W - tw) // 2
        y = 900
        # 文字阴影
        draw.text((x + 4, y + 4), text, font=font, fill=(0, 0, 0, alpha // 2))
        draw.text((x, y), text, font=font, fill=(255, 220, 100, alpha))
    
    # 阶段2 (8-14s): "月圆人团圆"
    if 8 <= t <= 14:
        local_t = (t - 8) / 6
        alpha = int(255 * ease_in_out(min(local_t * 2, 1.0)))
        if local_t > 0.7:
            alpha = int(255 * (1 - (local_t - 0.7) / 0.3 * 0.3))
        font = fonts["big"]
        text = "月圆人团圆"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        y = 950
        draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, alpha // 2))
        draw.text((x, y), text, font=font, fill=(255, 230, 150, alpha))
    
    # 阶段3 (14-22s): 祝福语
    if 14 <= t <= 22:
        local_t = (t - 14) / 8
        alpha = int(255 * ease_in_out(min(local_t * 2, 1.0)))
        if local_t > 0.7:
            alpha = int(255 * (1 - (local_t - 0.7) / 0.3 * 0.3))
        font = fonts["mid"]
        lines = ["花好月圆夜", "千里共婵娟", "愿君安康 福 满 中 秋"]
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x = (W - tw) // 2
            y = 850 + i * 120
            draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, alpha // 2))
            draw.text((x, y), line, font=font, fill=(255, 240, 180, alpha))
    
    # 阶段4 (22-30s): 最终祝福
    if 22 <= t <= 30:
        local_t = (t - 22) / 8
        alpha = int(255 * ease_in_out(min(local_t * 1.5, 1.0)))
        font = fonts["big"]
        text = "中秋快乐"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        y = 880
        # 脉冲效果
        pulse = 1 + 0.05 * math.sin(t * 3)
        draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, alpha // 2))
        draw.text((x, y), text, font=font, fill=(255, 200, 80, alpha))
        
        # 副标题
        font2 = fonts["small"]
        sub = "Mid-Autumn Festival"
        bbox2 = draw.textbbox((0, 0), sub, font=font2)
        tw2 = bbox2[2] - bbox2[0]
        x2 = (W - tw2) // 2
        y2 = y + 180
        draw.text((x2, y2), sub, font=font2, fill=(200, 200, 220, alpha))

# ========== 预生成数据 ==========

def gen_stars(n=80):
    return [{
        "x": np.random.randint(0, W),
        "y": np.random.randint(0, H // 2),
        "size": np.random.uniform(1, 3),
        "speed": np.random.uniform(0.5, 2),
        "phase": np.random.uniform(0, math.pi * 2),
    } for _ in range(n)]

def gen_lanterns(n=6):
    return [{
        "x": np.random.randint(150, W - 150),
        "y": np.random.randint(200, 600),
        "size": (np.random.randint(80, 110), np.random.randint(100, 130)),
        "sway_speed": np.random.uniform(0.2, 0.5),
        "phase": np.random.uniform(0, math.pi * 2),
    } for _ in range(n)]

def gen_particles(n=40):
    return [{
        "x": np.random.randint(0, W),
        "y": np.random.randint(0, H),
        "size": np.random.uniform(2, 5),
        "rise_speed": np.random.uniform(0.3, 0.8),
        "drift_speed": np.random.uniform(0.3, 0.7),
        "phase": np.random.uniform(0, math.pi * 2),
        "alpha": np.random.randint(100, 200),
    } for _ in range(n)]

# ========== 主渲染 ==========

def render_frame(t, stars, lanterns, particles, fonts):
    img = Image.new("RGB", (W, H), (10, 12, 40))
    draw = ImageDraw.Draw(img)
    
    # 1. 夜空背景
    draw_night_sky(draw, t)
    
    # 2. 星星
    draw_stars(img, t, stars)
    
    # 3. 远云
    draw_clouds(img, t)
    
    # 4. 月亮
    draw_moon(img, t)
    
    # 5. 灯笼
    draw_lanterns(img, t, lanterns)
    
    # 6. 粒子
    draw_particles(img, t, particles)
    
    # 7. 文字
    draw_text_sequence(img, t, fonts)
    
    return np.array(img)

def main():
    print("初始化场景...")
    np.random.seed(42)
    stars = gen_stars()
    lanterns = gen_lanterns()
    particles = gen_particles()
    
    fonts = {
        "huge": load_font(180, True),
        "big": load_font(120, True),
        "mid": load_font(80, True),
        "small": load_font(48, False),
    }
    
    # 用 moviepy 逐帧渲染
    from moviepy import ImageSequenceClip
    
    print(f"开始渲染 {TOTAL_FRAMES} 帧 ({DURATION}秒 @ {FPS}fps)...")
    frames = []
    for i in range(TOTAL_FRAMES):
        t = i / FPS
        frame = render_frame(t, stars, lanterns, particles, fonts)
        frames.append(frame)
        if (i + 1) % 30 == 0:
            print(f"  已渲染 {i+1}/{TOTAL_FRAMES} 帧 ({(i+1)/FPS:.1f}s)")
    
    print("合成视频...")
    clip = ImageSequenceClip(frames, fps=FPS)
    
    output = "/workspace/中秋祝福.mp4"
    clip.write_videofile(output, fps=FPS, codec="libx264",
                         preset="medium", threads=4, logger="bar")
    clip.close()
    print(f"完成！输出：{output}")

if __name__ == "__main__":
    main()

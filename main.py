import pygame
import random
import sys
import os

# =========================================================
# 0) 基準路徑：一律用 main.py 所在資料夾當基準（解決 VSCode/cwd 找不到檔）
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# =========================================================
# 1) 字型：避免中文亂碼（同樣用 BASE_DIR）
# =========================================================
def load_font(size: int) -> pygame.font.Font:
    local_candidates = [
        os.path.join(BASE_DIR, "assets", "NotoSansTC-Regular.otf"),
        os.path.join(BASE_DIR, "assets", "NotoSansTC-Regular.ttf"),
        os.path.join(BASE_DIR, "assets", "NotoSansCJKtc-Regular.otf"),
        os.path.join(BASE_DIR, "assets", "NotoSansCJKtc-Regular.ttf"),
    ]
    for p in local_candidates:
        if os.path.exists(p):
            try:
                return pygame.font.Font(p, size)
            except Exception:
                pass

    sys_candidates = [
        "Microsoft JhengHei",
        "Microsoft JhengHei UI",
        "微軟正黑體",
        "PingFang TC",
        "Heiti TC",
        "SimHei",
        "WenQuanYi Zen Hei",
        "Noto Sans CJK TC",
        "Noto Sans TC",
        "Arial Unicode MS",
    ]
    for name in sys_candidates:
        path = pygame.font.match_font(name)
        if path:
            try:
                return pygame.font.Font(path, size)
            except Exception:
                pass

    return pygame.font.Font(None, size)


# =========================================================
# 2) 初始化（音效：pre_init -> init，並保留容錯）
# =========================================================
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

SOUND_ENABLED = True
try:
    pygame.mixer.init()
    pygame.mixer.set_num_channels(32)  # 自動連射不會一直覆蓋同一個聲道
except Exception as e:
    SOUND_ENABLED = False
    print("[AUDIO] mixer.init FAILED:", e)

WIDTH, HEIGHT = 480, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("天際防衛戰")
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 60, 60)
PURPLE = (170, 80, 255)
CYAN = (0, 220, 255)
ORANGE = (255, 170, 0)
GREEN = (0, 210, 120)
BLUE = (80, 160, 255)

font = load_font(24)
small_font = load_font(18)
big_font = load_font(44)
title_font = load_font(52)


# =========================================================
# 3) 音效載入：強制用 BASE_DIR 絕對路徑 + 啟動時印出載入結果
#    支援放置位置：
#      - 專案根目錄：BASE_DIR/shoot.wav
#      - assets/sfx/：BASE_DIR/assets/sfx/shoot.wav
#      - assets/：BASE_DIR/assets/shoot.wav
# =========================================================
def _sfx_path(filename: str) -> str | None:
    candidates = [
        os.path.join(BASE_DIR, "assets", "sfx", filename),
        os.path.join(BASE_DIR, "assets", filename),
        os.path.join(BASE_DIR, filename),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def load_sfx(filename: str, volume: float = 0.6):
    if not SOUND_ENABLED:
        return None
    p = _sfx_path(filename)
    if not p:
        return None
    try:
        s = pygame.mixer.Sound(p)
        s.set_volume(volume)
        return s
    except Exception as e:
        print(f"[AUDIO] LOAD FAIL {filename}: {e}")
        return None

def play_sfx(snd):
    if snd is not None:
        try:
            snd.play()
        except Exception:
            pass

SFX_SHOOT  = load_sfx("shoot.wav",    volume=0.35)
SFX_HIT    = load_sfx("hit.wav",      volume=0.45)
SFX_PICKUP = load_sfx("pickup.wav",   volume=0.55)
SFX_BOSS   = load_sfx("boss.wav",     volume=0.55)
SFX_OVER   = load_sfx("gameover.wav", volume=0.65)
SFX_WIN    = load_sfx("win.wav",      volume=0.65)

print("[AUDIO] SOUND_ENABLED =", SOUND_ENABLED)
print("[AUDIO] mixer.get_init() =", pygame.mixer.get_init())
print("[AUDIO] shoot =", "OK" if SFX_SHOOT else "None")
print("[AUDIO] hit   =", "OK" if SFX_HIT else "None")
print("[AUDIO] pickup=", "OK" if SFX_PICKUP else "None")
print("[AUDIO] boss  =", "OK" if SFX_BOSS else "None")
print("[AUDIO] over  =", "OK" if SFX_OVER else "None")
print("[AUDIO] win   =", "OK" if SFX_WIN else "None")

#（可選）啟動測試音：如果你有 boss.wav，程式啟動會先播一下用來確認「真的有聲」
if SOUND_ENABLED and SFX_BOSS is not None:
    SFX_BOSS.play()


# =========================================================
# 4) 參數：五關卡 / Boss / 道具 / Boss 模式
# =========================================================
LEVEL_SCORE_TARGETS = {1: 200, 2: 450, 4: 900}
LEVEL_TIME_LIMIT = {1: 45, 2: 50, 3: 60, 4: 55, 5: 70}

ENEMY_SETTINGS = {
    1: {"count": 5, "speed_min": 1, "speed_max": 3},
    2: {"count": 6, "speed_min": 2, "speed_max": 4},
    4: {"count": 7, "speed_min": 2, "speed_max": 5},
}

MID_BOSS_HP = 150
BIG_BOSS_HP = 320
BOSS_BULLET_DAMAGE_MID = 8
BOSS_BULLET_DAMAGE_BIG = 10

POWERUP_DROP_CHANCE = 0.18
RAPID_DURATION_MS = 6000
SPREAD_DURATION_MS = 6000

# Boss 固定掉落：每損失 15% 一顆（共 6 顆）
BOSS_DROP_THRESHOLDS = [0.85, 0.70, 0.55, 0.40, 0.25, 0.10]

# Boss 攻擊模式切換
BOSS_MODE_SWITCH_MIN_MS = 2200
BOSS_MODE_SWITCH_MAX_MS = 3800

MID_MODE_DELAY = {"spray": 950, "burst": 240, "snipe": 520}
BIG_MODE_DELAY = {"fan": 650, "ring": 900, "burst": 220}


# =========================================================
# 5) 背景與封面特效
# =========================================================
def draw_vertical_gradient(surface, top_color, bottom_color):
    w, h = surface.get_size()
    for y in range(h):
        t = y / (h - 1)
        r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (w, y))

def draw_glow_text(text, fnt, x, y, main_color, glow_color=(0, 220, 255), glow_layers=6):
    base = fnt.render(text, True, main_color)
    for i in range(glow_layers, 0, -1):
        alpha = max(30, 210 - i * 30)
        glow = fnt.render(text, True, glow_color)
        glow_surf = pygame.Surface(glow.get_size(), pygame.SRCALPHA)
        glow_surf.blit(glow, (0, 0))
        glow_surf.set_alpha(alpha)
        screen.blit(glow_surf, (x - i, y))
        screen.blit(glow_surf, (x + i, y))
        screen.blit(glow_surf, (x, y - i))
        screen.blit(glow_surf, (x, y + i))
    screen.blit(base, (x, y))

def init_menu_particles(count=60):
    particles = []
    for _ in range(count):
        particles.append({
            "x": random.randint(0, WIDTH),
            "y": random.randint(0, HEIGHT),
            "r": random.choice([1, 1, 2]),
            "spd": random.uniform(0.2, 0.9),
            "a": random.randint(80, 200)
        })
    return particles

def update_and_draw_particles(particles):
    for p in particles:
        p["y"] += p["spd"]
        if p["y"] > HEIGHT:
            p["y"] = -5
            p["x"] = random.randint(0, WIDTH)
            p["spd"] = random.uniform(0.2, 0.9)
            p["a"] = random.randint(80, 200)
        star = pygame.Surface((p["r"] * 2 + 2, p["r"] * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(star, (255, 255, 255, p["a"]), (p["r"] + 1, p["r"] + 1), p["r"])
        screen.blit(star, (p["x"], p["y"]))

def draw_shadow_rect(x, y, w, h, radius=16, shadow_offset=6, shadow_alpha=120):
    shadow = pygame.Surface((w + shadow_offset * 2, h + shadow_offset * 2), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, shadow_alpha),
                     (shadow_offset, shadow_offset, w, h), border_radius=radius)
    screen.blit(shadow, (x - shadow_offset, y - shadow_offset))

def draw_button_fancy(rect, text, hover):
    scale = 1.05 if hover else 1.0
    w = int(rect.width * scale)
    h = int(rect.height * scale)
    x = rect.centerx - w // 2
    y = rect.centery - h // 2

    base_color = (40, 140, 100)
    hover_color = (60, 180, 120)
    color = hover_color if hover else base_color

    glow = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
    pygame.draw.rect(glow, (80, 220, 160, 80 if hover else 40),
                     (10, 10, w, h), border_radius=14)
    screen.blit(glow, (x - 10, y - 10))

    pygame.draw.rect(screen, color, (x, y, w, h), border_radius=14)
    pygame.draw.rect(screen, (220, 220, 220), (x, y, w, h), 2, border_radius=14)

    t = font.render(text, True, WHITE)
    screen.blit(t, (x + w // 2 - t.get_width() // 2, y + h // 2 - t.get_height() // 2))
    return pygame.Rect(x, y, w, h)

def draw_click_ripple(ripples):
    for r in list(ripples):
        r["radius"] += 6
        r["alpha"] -= 10
        if r["alpha"] <= 0:
            ripples.remove(r)
            continue
        surf = pygame.Surface((r["radius"] * 2 + 2, r["radius"] * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 255, 255, r["alpha"]),
                           (r["radius"] + 1, r["radius"] + 1), r["radius"], width=2)
        screen.blit(surf, (r["x"] - r["radius"], r["y"] - r["radius"]))

def wrap_text(text: str, fnt: pygame.font.Font, max_width: int):
    chars = list(text)
    lines, cur = [], ""
    for ch in chars:
        test = cur + ch
        if fnt.size(test)[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines

def draw_boss_background(menu_particles):
    draw_vertical_gradient(screen, (4, 6, 14), (10, 12, 26))
    update_and_draw_particles(menu_particles)

    w, h = screen.get_size()
    vignette = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(18):
        alpha = int(10 + i * 6)
        pygame.draw.rect(vignette, (0, 0, 0, alpha),
                         (i * 8, i * 10, w - i * 16, h - i * 20),
                         border_radius=26)
    screen.blit(vignette, (0, 0))

    scan = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, 4):
        pygame.draw.line(scan, (0, 0, 0, 18), (0, y), (w, y))
    screen.blit(scan, (0, 0))

def draw_boss_stage_tint(boss_kind: str):
    w, h = screen.get_size()
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((40, 90, 180, 30) if boss_kind == "mid" else (180, 60, 40, 32))
    screen.blit(overlay, (0, 0))


# =========================================================
# 6) 造型：戰鬥機 / 尾焰 / 怪物 / Boss / 果實
# =========================================================
def make_fighter_surface(w=60, h=48):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    body = [(w // 2, 4), (8, h - 10), (w - 8, h - 10)]
    pygame.draw.polygon(surf, CYAN, body)
    pygame.draw.ellipse(surf, (40, 40, 40), (w // 2 - 8, 14, 16, 18))

    left_wing = [(12, h - 16), (2, h - 6), (18, h - 6)]
    right_wing = [(w - 12, h - 16), (w - 2, h - 6), (w - 18, h - 6)]
    pygame.draw.polygon(surf, (30, 160, 190), left_wing)
    pygame.draw.polygon(surf, (30, 160, 190), right_wing)

    tail = [(w // 2 - 10, h - 18), (w // 2, h - 28), (w // 2 + 10, h - 18)]
    pygame.draw.polygon(surf, (20, 120, 150), tail)
    pygame.draw.polygon(surf, (0, 120, 150), body, 2)
    return surf

def draw_engine_flame(surf, w, h, strong=False):
    cx = w // 2
    base_y = h - 8
    flame_len = random.randint(10, 16) if strong else random.randint(6, 12)
    flame_color = ORANGE if strong else (255, 210, 0)
    inner_color = WHITE
    outer = [(cx, base_y + flame_len), (cx - 6, base_y), (cx + 6, base_y)]
    pygame.draw.polygon(surf, flame_color, outer)
    inner = [(cx, base_y + max(4, flame_len - 4)), (cx - 3, base_y + 1), (cx + 3, base_y + 1)]
    pygame.draw.polygon(surf, inner_color, inner)

def make_monster_surface(kind: str, size=40):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    if kind == "devil":
        pygame.draw.circle(surf, RED, (cx, cy), size // 2 - 2)
        pygame.draw.polygon(surf, PURPLE, [(10, 10), (4, 2), (14, 6)])
        pygame.draw.polygon(surf, PURPLE, [(size - 10, 10), (size - 4, 2), (size - 14, 6)])
        pygame.draw.circle(surf, WHITE, (cx - 8, cy - 3), 6)
        pygame.draw.circle(surf, WHITE, (cx + 8, cy - 3), 6)
        pygame.draw.circle(surf, BLACK, (cx - 6, cy - 2), 2)
        pygame.draw.circle(surf, BLACK, (cx + 6, cy - 2), 2)
    elif kind == "alien":
        pygame.draw.polygon(surf, (200, 90, 255), [(cx, 3), (size - 3, cy), (cx, size - 3), (3, cy)])
        pygame.draw.circle(surf, WHITE, (cx, cy), 8)
        pygame.draw.circle(surf, BLACK, (cx, cy), 3)
    else:
        pygame.draw.rect(surf, BLUE, (4, 4, size - 8, size - 8), border_radius=6)
        pygame.draw.circle(surf, WHITE, (cx - 8, cy - 4), 5)
        pygame.draw.circle(surf, WHITE, (cx + 8, cy - 4), 5)
        pygame.draw.circle(surf, BLACK, (cx - 8, cy - 4), 2)
        pygame.draw.circle(surf, BLACK, (cx + 8, cy - 4), 2)
    return surf

def make_boss_surface(kind: str, w=160, h=90):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if kind == "mid":
        main, edge, core = (170, 60, 210), (90, 20, 120), (255, 220, 0)
    else:
        main, edge, core = (210, 60, 60), (120, 20, 20), (0, 220, 255)

    pygame.draw.rect(surf, main, (10, 20, w - 20, h - 30), border_radius=18)
    pygame.draw.rect(surf, edge, (10, 20, w - 20, h - 30), 3, border_radius=18)
    pygame.draw.polygon(surf, main, [(10, 45), (0, 70), (35, 62)])
    pygame.draw.polygon(surf, main, [(w - 10, 45), (w, 70), (w - 35, 62)])

    pygame.draw.circle(surf, WHITE, (w // 2 - 22, 45), 10)
    pygame.draw.circle(surf, WHITE, (w // 2 + 22, 45), 10)
    pygame.draw.circle(surf, BLACK, (w // 2 - 20, 45), 4)
    pygame.draw.circle(surf, BLACK, (w // 2 + 20, 45), 4)

    pygame.draw.circle(surf, core, (w // 2, 58), 10)
    pygame.draw.circle(surf, WHITE, (w // 2, 58), 4)
    return surf

def make_fruit_surface(kind: str, size=22):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    if kind == "heal":
        pygame.draw.circle(surf, GREEN, (cx, cy), size // 2 - 2)
        pygame.draw.rect(surf, WHITE, (cx - 2, cy - 6, 4, 12), border_radius=2)
        pygame.draw.rect(surf, WHITE, (cx - 6, cy - 2, 12, 4), border_radius=2)
    elif kind == "rapid":
        pygame.draw.circle(surf, ORANGE, (cx, cy), size // 2 - 2)
        pygame.draw.circle(surf, (255, 230, 200), (cx - 3, cy - 3), 3)
    else:
        pygame.draw.circle(surf, PURPLE, (cx, cy), size // 2 - 2)
        pygame.draw.polygon(surf, (230, 200, 255), [(cx, 4), (cx + 4, cy), (cx, size - 4), (cx - 4, cy)])
    return surf


# =========================================================
# 7) Sprite：玩家/子彈/敵人/果實/Boss
# =========================================================
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.w, self.h = 60, 48
        self.base_image = make_fighter_surface(self.w, self.h)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 60))

        self.speed = 8
        self.hp = 100
        self.hp_max = 100

        self.last_shot = 0
        self.base_shoot_delay = 120
        self.shoot_delay = self.base_shoot_delay

        self.last_flame_toggle = 0
        self.flame_on = True

        self.rapid_until = 0
        self.spread_until = 0

        # 控制射擊音效不要太密：每 4 發播一次
        self.shot_count = 0

    def reset_for_new_game(self):
        self.rect.center = (WIDTH // 2, HEIGHT - 60)
        self.hp = self.hp_max
        self.last_shot = 0
        self.shoot_delay = self.base_shoot_delay
        self.rapid_until = 0
        self.spread_until = 0
        self.shot_count = 0

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed

        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, WIDTH)
        self.rect.top = max(self.rect.top, 0)
        self.rect.bottom = min(self.rect.bottom, HEIGHT)

        now = pygame.time.get_ticks()
        if now - self.last_flame_toggle >= 80:
            self.last_flame_toggle = now
            self.flame_on = not self.flame_on

        if now <= self.rapid_until:
            self.shoot_delay = max(50, self.base_shoot_delay // 2)
        else:
            self.shoot_delay = self.base_shoot_delay

        center = self.rect.center
        self.image = self.base_image.copy()
        draw_engine_flame(self.image, self.w, self.h, strong=self.flame_on)
        self.rect = self.image.get_rect(center=center)

    def can_fire(self) -> bool:
        now = pygame.time.get_ticks()
        return (now - self.last_shot) >= self.shoot_delay

    def mark_fired(self):
        self.last_shot = pygame.time.get_ticks()

    def has_spread(self) -> bool:
        return pygame.time.get_ticks() <= self.spread_until


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vx=0, vy=-12):
        super().__init__()
        self.image = pygame.Surface((6, 14), pygame.SRCALPHA)
        pygame.draw.rect(self.image, YELLOW, (0, 0, 6, 14), border_radius=3)
        pygame.draw.rect(self.image, WHITE, (2, 2, 2, 6), border_radius=1)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx, self.vy = vx, vy

    def update(self, *args):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, speed_min, speed_max):
        super().__init__()
        self.kind = random.choice(["devil", "alien", "bot"])
        self.image = make_monster_surface(self.kind, 40)
        self.rect = self.image.get_rect()
        self.speed_min = speed_min
        self.speed_max = speed_max
        self.reset()

    def reset(self):
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(-420, -40)
        self.speed_y = random.randrange(self.speed_min, self.speed_max)

    def update(self, *args):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT:
            self.reset()


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, kind: str, x: int, y: int):
        super().__init__()
        self.kind = kind
        self.image = make_fruit_surface(kind, 22)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = 3

    def update(self, *args):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT:
            self.kill()


class Boss(pygame.sprite.Sprite):
    def __init__(self, boss_kind: str, hp: int):
        super().__init__()
        self.boss_kind = boss_kind  # "mid" or "big"
        self.image = make_boss_surface(boss_kind, 160, 90)
        self.rect = self.image.get_rect(center=(WIDTH // 2, 110))
        self.max_hp = hp
        self.hp = hp

        self.vx = 3 if boss_kind == "mid" else 4
        self.last_shot = 0

        self.attack_mode = "spray" if boss_kind == "mid" else "fan"
        self.mode_until = pygame.time.get_ticks() + random.randint(BOSS_MODE_SWITCH_MIN_MS, BOSS_MODE_SWITCH_MAX_MS)
        self.burst_left = 0

        self.drop_flags = {thr: False for thr in BOSS_DROP_THRESHOLDS}

    def update(self, *args):
        self.rect.x += self.vx
        if self.rect.left <= 10 or self.rect.right >= WIDTH - 10:
            self.vx *= -1

        now = pygame.time.get_ticks()
        if now >= self.mode_until:
            if self.boss_kind == "mid":
                self.attack_mode = random.choice(["spray", "burst", "snipe"])
            else:
                self.attack_mode = random.choice(["fan", "ring", "burst"])

            if self.attack_mode == "burst":
                self.burst_left = 10 if self.boss_kind == "mid" else 14

            self.mode_until = now + random.randint(BOSS_MODE_SWITCH_MIN_MS, BOSS_MODE_SWITCH_MAX_MS)

    def current_shot_delay(self) -> int:
        return MID_MODE_DELAY[self.attack_mode] if self.boss_kind == "mid" else BIG_MODE_DELAY[self.attack_mode]

    def can_shoot(self):
        now = pygame.time.get_ticks()
        return (now - self.last_shot) >= self.current_shot_delay()

    def mark_shot(self):
        self.last_shot = pygame.time.get_ticks()


class BossBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vx=0, vy=7):
        super().__init__()
        self.image = pygame.Surface((8, 14), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255, 120, 120), (0, 0, 8, 14), border_radius=3)
        pygame.draw.rect(self.image, WHITE, (3, 3, 2, 5), border_radius=1)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx, self.vy = vx, vy

    def update(self, *args):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.top > HEIGHT or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()


# =========================================================
# 8) Boss 血條（只用圖）
# =========================================================
def draw_boss_hp_bar(boss: Boss):
    bar_w = WIDTH - 40
    bar_h = 10
    x, y = 20, 66
    pygame.draw.rect(screen, (60, 60, 60), (x, y, bar_w, bar_h), border_radius=6)
    pygame.draw.rect(screen, (220, 220, 220), (x, y, bar_w, bar_h), 2, border_radius=6)

    ratio = 0 if boss.max_hp <= 0 else max(0.0, min(1.0, boss.hp / boss.max_hp))
    fill_w = int((bar_w - 4) * ratio)
    fill_color = (80, 160, 255) if boss.boss_kind == "mid" else (255, 120, 80)
    pygame.draw.rect(screen, fill_color, (x + 2, y + 2, fill_w, bar_h - 4), border_radius=6)


# =========================================================
# 9) 群組 / 狀態 / 按鈕
# =========================================================
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
powerups = pygame.sprite.Group()
boss_group = pygame.sprite.Group()
boss_bullets = pygame.sprite.Group()

player = Player()
all_sprites.add(player)

menu_particles = init_menu_particles(60)
menu_ripples = []

state = "MENU"  # MENU -> COUNTDOWN -> PLAY -> CLEAR -> WIN / GAMEOVER
score = 0
level = 1
mode = "LEVEL"
level_start_ms = pygame.time.get_ticks()
level_time_limit = LEVEL_TIME_LIMIT[level]

message_text = ""
message_until = 0

countdown_start_ms = 0
COUNTDOWN_SECONDS = 3

start_button = pygame.Rect(WIDTH // 2 - 110, HEIGHT - 150, 220, 54)
back_button = pygame.Rect(WIDTH // 2 - 110, HEIGHT // 2 + 40, 220, 54)


# =========================================================
# 10) 遊戲流程函式
# =========================================================
def clear_groups_for_new_level():
    for g in (enemies, bullets, powerups, boss_group, boss_bullets):
        for s in list(g):
            s.kill()

def spawn_level_enemies(lv: int):
    settings = ENEMY_SETTINGS.get(lv)
    if not settings:
        return
    for _ in range(settings["count"]):
        e = Enemy(settings["speed_min"], settings["speed_max"])
        all_sprites.add(e)
        enemies.add(e)

def start_level(lv: int):
    global level, mode, level_start_ms, level_time_limit
    level = lv
    mode = "LEVEL"
    level_start_ms = pygame.time.get_ticks()
    level_time_limit = LEVEL_TIME_LIMIT[level]

    clear_groups_for_new_level()

    if level == 3:
        mode = "BOSS"
        b = Boss("mid", MID_BOSS_HP)
        all_sprites.add(b)
        boss_group.add(b)
        play_sfx(SFX_BOSS)
    elif level == 5:
        mode = "BOSS"
        b = Boss("big", BIG_BOSS_HP)
        all_sprites.add(b)
        boss_group.add(b)
        play_sfx(SFX_BOSS)
    else:
        spawn_level_enemies(level)

def remaining_time_sec() -> int:
    elapsed = (pygame.time.get_ticks() - level_start_ms) // 1000
    return max(0, level_time_limit - elapsed)

def maybe_drop_powerup(x: int, y: int, force: bool = False):
    if not force:
        if random.random() > POWERUP_DROP_CHANCE:
            return
        # 前兩關：紫色 spread 機率下降一點點
        if level in (1, 2):
            kind = random.choices(["heal", "rapid", "spread"], weights=[40, 35, 25], k=1)[0]
        else:
            kind = random.choices(["heal", "rapid", "spread"], weights=[34, 33, 33], k=1)[0]
    else:
        # Boss 固定掉落：偏向 heal 一點點
        kind = random.choices(["heal", "rapid", "spread"], weights=[45, 30, 25], k=1)[0]

    p = PowerUp(kind, x, y)
    all_sprites.add(p)
    powerups.add(p)

def apply_powerup(kind: str):
    now = pygame.time.get_ticks()
    if kind == "heal":
        player.hp = min(player.hp_max, player.hp + 25)
    elif kind == "rapid":
        player.rapid_until = max(player.rapid_until, now + RAPID_DURATION_MS)
    elif kind == "spread":
        player.spread_until = max(player.spread_until, now + SPREAD_DURATION_MS)

def spawn_player_bullets():
    if not player.can_fire():
        return
    player.mark_fired()

    # 射擊音效：避免太密，改為每 4 發播一次（更像連射音效）
    player.shot_count += 1
    if player.shot_count % 4 == 0:
        play_sfx(SFX_SHOOT)

    x, y = player.rect.centerx, player.rect.top
    if player.has_spread():
        for vx in (-3, 0, 3):
            b = Bullet(x, y, vx=vx, vy=-12)
            all_sprites.add(b)
            bullets.add(b)
    else:
        b = Bullet(x, y, vx=0, vy=-12)
        all_sprites.add(b)
        bullets.add(b)

def boss_check_and_drop(boss: Boss):
    ratio = boss.hp / boss.max_hp if boss.max_hp > 0 else 0
    for thr in BOSS_DROP_THRESHOLDS:
        if ratio <= thr and (boss.drop_flags.get(thr) is False):
            boss.drop_flags[thr] = True
            maybe_drop_powerup(boss.rect.centerx, boss.rect.centery, force=True)

def set_gameover():
    global state
    if state != "GAMEOVER":
        play_sfx(SFX_OVER)
    player.hp = 0
    state = "GAMEOVER"

def new_game():
    global score, level, mode, message_text, message_until
    score = 0
    level = 1
    mode = "LEVEL"
    player.reset_for_new_game()
    clear_groups_for_new_level()
    message_text = ""
    message_until = 0


# =========================================================
# 11) 主迴圈
# =========================================================
running = True
while running:
    clock.tick(60)

    mouse_pos = pygame.mouse.get_pos()
    mouse_down = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_down = True

    keys = pygame.key.get_pressed()

    # -------------------------
    # MENU
    # -------------------------
    if state == "MENU":
        draw_vertical_gradient(screen, (6, 8, 20), (14, 18, 38))
        update_and_draw_particles(menu_particles)

        title_text = "天際防衛戰"
        title_w = title_font.size(title_text)[0]
        draw_glow_text(title_text, title_font, WIDTH // 2 - title_w // 2, 58,
                       main_color=(40, 240, 255), glow_color=(0, 180, 255), glow_layers=7)

        demo = make_fighter_surface(86, 68)
        demo2 = demo.copy()
        draw_engine_flame(demo2, 86, 68, strong=True)
        screen.blit(demo2, (WIDTH // 2 - demo2.get_width() // 2, 128))

        panel_w = WIDTH - 70
        panel_h = 235
        panel_x = (WIDTH - panel_w) // 2
        panel_y = 215

        draw_shadow_rect(panel_x, panel_y, panel_w, panel_h, radius=16, shadow_offset=7, shadow_alpha=140)
        pygame.draw.rect(screen, (18, 18, 30), (panel_x, panel_y, panel_w, panel_h), border_radius=16)
        pygame.draw.rect(screen, (70, 80, 110), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=16)

        rules = [
            "規則簡介：",
            "1) 移動：WASD 或 方向鍵",
            "2) 射擊：自動射擊（無需按鍵）",
            "3) 一般關(1/2/4)：打怪 +10 分，達標過關",
            "4) Boss 關(3/5)：擊倒 Boss 才能過關",
            "5) 每關限時：時間到或 HP=0 即失敗",
            "6) 果實：Heal(+25) / Rapid(6s) / Spread(6s)",
            "7) Boss 每損失 15% 血量固定掉果實",
            "   85 / 70 / 55 / 40 / 25 / 10 %",
        ]

        text_x = panel_x + 18
        text_y = panel_y + 16
        max_text_w = panel_w - 36
        cy = text_y
        bottom_limit = panel_y + panel_h - 18
        for line in rules:
            for seg in wrap_text(line, small_font, max_text_w):
                t = small_font.render(seg, True, (190, 195, 210))
                if cy + t.get_height() > bottom_limit:
                    break
                screen.blit(t, (text_x, cy))
                cy += t.get_height() + 6

        start_button.y = panel_y + panel_h + 20
        start_button.x = WIDTH // 2 - start_button.width // 2

        hover = start_button.collidepoint(mouse_pos)
        fancy_rect = draw_button_fancy(start_button, "開始遊戲", hover)

        draw_click_ripple(menu_ripples)

        tip = small_font.render("點擊開始後，倒數 3 秒進入遊戲", True, (150, 160, 180))
        screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, fancy_rect.bottom + 14))

        pygame.display.flip()

        if mouse_down and fancy_rect.collidepoint(mouse_pos):
            menu_ripples.append({"x": mouse_pos[0], "y": mouse_pos[1], "radius": 6, "alpha": 180})
            new_game()
            state = "COUNTDOWN"
            countdown_start_ms = pygame.time.get_ticks()
        continue

    # -------------------------
    # COUNTDOWN
    # -------------------------
    if state == "COUNTDOWN":
        all_sprites.update(keys)

        draw_vertical_gradient(screen, (6, 8, 20), (14, 18, 38))
        update_and_draw_particles(menu_particles)
        all_sprites.draw(screen)

        elapsed = (pygame.time.get_ticks() - countdown_start_ms) // 1000
        left = COUNTDOWN_SECONDS - elapsed

        hud1 = font.render(f"Score: {score}  HP: {max(0, player.hp)}", True, WHITE)
        screen.blit(hud1, (10, 10))

        if left <= 0:
            start_level(1)
            state = "PLAY"
        else:
            txt = title_font.render(str(left), True, YELLOW)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 70))
            sub = small_font.render("準備開始…", True, (160, 170, 190))
            screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 6))

        pygame.display.flip()
        continue

    # -------------------------
    # PLAY
    # -------------------------
    if state == "PLAY":
        if remaining_time_sec() <= 0:
            set_gameover()

        spawn_player_bullets()
        all_sprites.update(keys)

        if mode == "LEVEL":
            hit_map = pygame.sprite.groupcollide(enemies, bullets, True, True)
            if hit_map:
                play_sfx(SFX_HIT)

            for enemy in hit_map:
                score += 10
                if level in (1, 2, 4):
                    maybe_drop_powerup(enemy.rect.centerx, enemy.rect.centery, force=False)
                st = ENEMY_SETTINGS[level]
                e = Enemy(st["speed_min"], st["speed_max"])
                all_sprites.add(e)
                enemies.add(e)

            hits = pygame.sprite.spritecollide(player, enemies, True)
            for _ in hits:
                player.hp -= 20
                if player.hp <= 0:
                    set_gameover()
                    break
                st = ENEMY_SETTINGS[level]
                e = Enemy(st["speed_min"], st["speed_max"])
                all_sprites.add(e)
                enemies.add(e)

            got = pygame.sprite.spritecollide(player, powerups, True)
            if got:
                play_sfx(SFX_PICKUP)
            for p in got:
                apply_powerup(p.kind)

            target = LEVEL_SCORE_TARGETS.get(level, None)
            if target is not None and score >= target:
                state = "CLEAR"
                message_text = f"LEVEL {level} CLEAR!"
                message_until = pygame.time.get_ticks() + 1200

        elif mode == "BOSS":
            # Boss 射擊（依模式）
            for boss in boss_group:
                if boss.can_shoot():
                    boss.mark_shot()
                    x = boss.rect.centerx
                    y = boss.rect.bottom - 8

                    if boss.boss_kind == "mid":
                        if boss.attack_mode == "spray":
                            for vx in (-2, 0, 2):
                                bb = BossBullet(x, y, vx=vx, vy=7)
                                all_sprites.add(bb); boss_bullets.add(bb)
                        elif boss.attack_mode == "snipe":
                            bb = BossBullet(x, y, vx=0, vy=10)
                            all_sprites.add(bb); boss_bullets.add(bb)
                        elif boss.attack_mode == "burst":
                            if boss.burst_left > 0:
                                boss.burst_left -= 1
                                vx = random.choice([-1, 0, 1])
                                bb = BossBullet(x, y, vx=vx, vy=8)
                                all_sprites.add(bb); boss_bullets.add(bb)
                            else:
                                boss.attack_mode = "spray"

                    else:
                        if boss.attack_mode == "fan":
                            for vx in (-3, -1, 0, 1, 3):
                                bb = BossBullet(x, y, vx=vx, vy=7)
                                all_sprites.add(bb); boss_bullets.add(bb)
                        elif boss.attack_mode == "ring":
                            for vx in (-5, -3, -1, 0, 1, 3, 5):
                                bb = BossBullet(x, y, vx=vx, vy=random.choice([6, 7, 8]))
                                all_sprites.add(bb); boss_bullets.add(bb)
                        elif boss.attack_mode == "burst":
                            if boss.burst_left > 0:
                                boss.burst_left -= 1
                                for vx in (-2, 0, 2):
                                    bb = BossBullet(x, y, vx=vx, vy=8)
                                    all_sprites.add(bb); boss_bullets.add(bb)
                            else:
                                boss.attack_mode = "fan"

            # 子彈打 Boss
            if len(boss_group) > 0:
                boss = next(iter(boss_group))
                boss_hits = pygame.sprite.spritecollide(boss, bullets, True)
                if boss_hits:
                    play_sfx(SFX_HIT)
                    boss.hp -= 2 * len(boss_hits)
                    boss_check_and_drop(boss)
                    if boss.hp <= 0:
                        boss.kill()
                        state = "CLEAR"
                        message_text = f"BOSS DEFEATED! (L{level})"
                        message_until = pygame.time.get_ticks() + 1400

            # Boss 子彈打玩家
            bb_hits = pygame.sprite.spritecollide(player, boss_bullets, True)
            for _ in bb_hits:
                player.hp -= (BOSS_BULLET_DAMAGE_MID if level == 3 else BOSS_BULLET_DAMAGE_BIG)
                if player.hp <= 0:
                    set_gameover()
                    break

            got = pygame.sprite.spritecollide(player, powerups, True)
            if got:
                play_sfx(SFX_PICKUP)
            for p in got:
                apply_powerup(p.kind)

    # -------------------------
    # CLEAR
    # -------------------------
    if state == "CLEAR":
        if pygame.time.get_ticks() >= message_until:
            if level < 5:
                start_level(level + 1)
                state = "PLAY"
            else:
                play_sfx(SFX_WIN)
                state = "WIN"
                message_text = "YOU WIN!"
                message_until = pygame.time.get_ticks() + 2500

    # =====================================================
    # DRAW
    # =====================================================
    if mode == "BOSS":
        draw_boss_background(menu_particles)
    else:
        draw_vertical_gradient(screen, (6, 8, 20), (14, 18, 38))
        update_and_draw_particles(menu_particles)

    all_sprites.draw(screen)

    if mode == "BOSS" and len(boss_group) > 0:
        draw_boss_stage_tint(next(iter(boss_group)).boss_kind)

    hud1 = font.render(f"Score: {score}  HP: {max(0, player.hp)}", True, WHITE)
    screen.blit(hud1, (10, 10))

    if state not in ("GAMEOVER", "WIN"):
        time_left = remaining_time_sec()
        hud2 = small_font.render(f"LEVEL: {level}  Time: {time_left}s", True, (170, 175, 190))
        screen.blit(hud2, (10, 38))

    if state in ("PLAY", "CLEAR") and mode == "BOSS" and len(boss_group) > 0:
        draw_boss_hp_bar(next(iter(boss_group)))

    now = pygame.time.get_ticks()
    if state in ("CLEAR", "WIN") and now < message_until:
        msg = big_font.render(message_text, True, YELLOW)
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 40))

    if state == "GAMEOVER":
        msg = big_font.render("GAME OVER", True, RED)
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 40))
        hover = back_button.collidepoint(mouse_pos)
        btn = draw_button_fancy(back_button, "回到封面", hover)
        if mouse_down and btn.collidepoint(mouse_pos):
            state = "MENU"

    if state == "WIN":
        msg = big_font.render("YOU WIN!", True, YELLOW)
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 40))
        hover = back_button.collidepoint(mouse_pos)
        btn = draw_button_fancy(back_button, "回到封面", hover)
        if mouse_down and btn.collidepoint(mouse_pos):
            state = "MENU"

    pygame.display.flip()

pygame.quit()
sys.exit()

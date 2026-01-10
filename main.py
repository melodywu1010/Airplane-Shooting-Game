import pygame
import random
import sys
import os

# ======================
# 0) 字型：解決中文亂碼（最重要）
# ======================
def load_font(size: int) -> pygame.font.Font:
    """
    優先載入專案內字型 assets/NotoSansTC-Regular.otf（推薦做法，最穩）
    若沒有字型檔，則嘗試系統中文字型（Windows/macOS/Linux）
    最後才退回 pygame 預設字型（可能會中文亂碼）
    """
    # 1) 專案內字型（最推薦）
    local_candidates = [
        os.path.join("assets", "NotoSansTC-Regular.otf"),
        os.path.join("assets", "NotoSansTC-Regular.ttf"),
        os.path.join("assets", "NotoSansCJKtc-Regular.otf"),
        os.path.join("assets", "msjh.ttc"),  # 你若自行放微軟正黑體也可
    ]
    for p in local_candidates:
        if os.path.exists(p):
            try:
                return pygame.font.Font(p, size)
            except Exception:
                pass

    # 2) 系統字型名稱（依常見程度排序）
    # Windows: Microsoft JhengHei / 微軟正黑體
    # macOS: PingFang TC / Heiti TC
    # Linux: Noto Sans CJK TC
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

    # 3) 最後 fallback（可能中文仍亂碼）
    return pygame.font.Font(None, size)

# ======================
# 1) 初始化
# ======================
pygame.init()
WIDTH, HEIGHT = 480, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("天際防衛戰")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
DARK_BG = (10, 10, 18)

YELLOW = (255, 255, 0)
RED = (255, 60, 60)
PURPLE = (170, 80, 255)
CYAN = (0, 220, 255)
ORANGE = (255, 170, 0)
GREEN = (0, 210, 120)
BLUE = (80, 160, 255)

# Fonts (use Chinese-safe loader)
font = load_font(24)
small_font = load_font(18)
big_font = load_font(44)
title_font = load_font(52)

# ======================
# 2) 關卡 / 道具 / Boss 參數
# ======================
LEVEL_SCORE_TARGETS = {
    1: 200,
    2: 450,
    4: 900,
}

LEVEL_TIME_LIMIT = {
    1: 45,
    2: 50,
    3: 60,
    4: 55,
    5: 70,
}

ENEMY_SETTINGS = {
    1: {"count": 5, "speed_min": 1, "speed_max": 3},
    2: {"count": 6, "speed_min": 2, "speed_max": 4},
    4: {"count": 7, "speed_min": 2, "speed_max": 5},
}

# Boss 設定（第3關：稍微變難一點點）
MID_BOSS_HP = 150   # 原 140 -> 150
BIG_BOSS_HP = 320

# 技能果實
POWERUP_DROP_CHANCE = 0.18
POWERUP_TYPES = ["heal", "rapid", "spread"]
RAPID_DURATION_MS = 6000
SPREAD_DURATION_MS = 6000

# Boss 掉落：每 15% 血量掉一顆（85/70/55/40/25/10）
BOSS_DROP_THRESHOLDS = [0.85, 0.70, 0.55, 0.40, 0.25, 0.10]

# Boss 子彈傷害（第3關稍微變難）
BOSS_BULLET_DAMAGE_MID = 8   # 原 7 -> 8
BOSS_BULLET_DAMAGE_BIG = 10

# ======================
# 3) 造型：戰鬥機 / 尾焰 / 怪物 / Boss / 果實
# ======================
def make_fighter_surface(w=60, h=48):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    body = [(w // 2, 4), (8, h - 10), (w - 8, h - 10)]
    pygame.draw.polygon(surf, CYAN, body)
    pygame.draw.ellipse(surf, (40, 40, 40), (w//2 - 8, 14, 16, 18))

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
        pygame.draw.circle(surf, RED, (cx, cy), size//2 - 2)
        pygame.draw.polygon(surf, PURPLE, [(10, 10), (4, 2), (14, 6)])
        pygame.draw.polygon(surf, PURPLE, [(size-10, 10), (size-4, 2), (size-14, 6)])
        pygame.draw.circle(surf, WHITE, (cx - 8, cy - 3), 6)
        pygame.draw.circle(surf, WHITE, (cx + 8, cy - 3), 6)
        pygame.draw.circle(surf, BLACK, (cx - 6, cy - 2), 2)
        pygame.draw.circle(surf, BLACK, (cx + 6, cy - 2), 2)

    elif kind == "alien":
        pygame.draw.polygon(surf, (200, 90, 255), [(cx, 3), (size-3, cy), (cx, size-3), (3, cy)])
        pygame.draw.circle(surf, WHITE, (cx, cy), 8)
        pygame.draw.circle(surf, BLACK, (cx, cy), 3)

    else:  # bot
        pygame.draw.rect(surf, BLUE, (4, 4, size-8, size-8), border_radius=6)
        pygame.draw.circle(surf, WHITE, (cx - 8, cy - 4), 5)
        pygame.draw.circle(surf, WHITE, (cx + 8, cy - 4), 5)
        pygame.draw.circle(surf, BLACK, (cx - 8, cy - 4), 2)
        pygame.draw.circle(surf, BLACK, (cx + 8, cy - 4), 2)

    return surf

def make_boss_surface(kind: str, w=160, h=90):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if kind == "mid":
        main = (170, 60, 210)
        edge = (90, 20, 120)
        core = (255, 220, 0)
    else:
        main = (210, 60, 60)
        edge = (120, 20, 20)
        core = (0, 220, 255)

    pygame.draw.rect(surf, main, (10, 20, w-20, h-30), border_radius=18)
    pygame.draw.rect(surf, edge, (10, 20, w-20, h-30), 3, border_radius=18)
    pygame.draw.polygon(surf, main, [(10, 45), (0, 70), (35, 62)])
    pygame.draw.polygon(surf, main, [(w-10, 45), (w, 70), (w-35, 62)])

    pygame.draw.circle(surf, WHITE, (w//2 - 22, 45), 10)
    pygame.draw.circle(surf, WHITE, (w//2 + 22, 45), 10)
    pygame.draw.circle(surf, BLACK, (w//2 - 20, 45), 4)
    pygame.draw.circle(surf, BLACK, (w//2 + 20, 45), 4)

    pygame.draw.circle(surf, core, (w//2, 58), 10)
    pygame.draw.circle(surf, WHITE, (w//2, 58), 4)
    return surf

def make_fruit_surface(kind: str, size=22):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    if kind == "heal":
        pygame.draw.circle(surf, GREEN, (cx, cy), size//2 - 2)
        pygame.draw.rect(surf, WHITE, (cx-2, cy-6, 4, 12), border_radius=2)
        pygame.draw.rect(surf, WHITE, (cx-6, cy-2, 12, 4), border_radius=2)
    elif kind == "rapid":
        pygame.draw.circle(surf, ORANGE, (cx, cy), size//2 - 2)
        pygame.draw.circle(surf, (255, 230, 200), (cx-3, cy-3), 3)
    else:  # spread
        pygame.draw.circle(surf, PURPLE, (cx, cy), size//2 - 2)
        pygame.draw.polygon(surf, (230, 200, 255), [(cx, 4), (cx+4, cy), (cx, size-4), (cx-4, cy)])
    return surf

# ======================
# 4) Sprite 類別
# ======================
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.w, self.h = 60, 48
        self.base_image = make_fighter_surface(self.w, self.h)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(WIDTH//2, HEIGHT-60))

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

    def reset_for_new_game(self):
        self.rect.center = (WIDTH//2, HEIGHT-60)
        self.hp = self.hp_max
        self.last_shot = 0
        self.shoot_delay = self.base_shoot_delay
        self.rapid_until = 0
        self.spread_until = 0

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
        self.vx = vx
        self.vy = vy

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
        self.rect = self.image.get_rect(center=(WIDTH//2, 110))
        self.max_hp = hp
        self.hp = hp

        self.vx = 3 if boss_kind == "mid" else 4

        self.last_shot = 0
        # 第3關稍微變難：射擊間隔略快
        self.shot_delay = 950 if boss_kind == "mid" else 650  # 原 mid 1000 -> 950

        self.drop_flags = {thr: False for thr in BOSS_DROP_THRESHOLDS}

    def update(self, *args):
        self.rect.x += self.vx
        if self.rect.left <= 10 or self.rect.right >= WIDTH - 10:
            self.vx *= -1

    def can_shoot(self):
        now = pygame.time.get_ticks()
        return (now - self.last_shot) >= self.shot_delay

    def mark_shot(self):
        self.last_shot = pygame.time.get_ticks()

class BossBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vx=0, vy=7):
        super().__init__()
        self.image = pygame.Surface((8, 14), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255, 120, 120), (0, 0, 8, 14), border_radius=3)
        pygame.draw.rect(self.image, WHITE, (3, 3, 2, 5), border_radius=1)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = vx
        self.vy = vy

    def update(self, *args):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.top > HEIGHT or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

# ======================
# 5) 群組與狀態
# ======================
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
powerups = pygame.sprite.Group()
boss_group = pygame.sprite.Group()
boss_bullets = pygame.sprite.Group()

player = Player()
all_sprites.add(player)

# 狀態：MENU -> COUNTDOWN -> PLAY -> CLEAR -> WIN / GAMEOVER
state = "MENU"

score = 0
level = 1
mode = "LEVEL"
level_start_ms = pygame.time.get_ticks()
level_time_limit = LEVEL_TIME_LIMIT[level]

message_until = 0
message_text = ""

# 倒數
countdown_start_ms = 0
COUNTDOWN_SECONDS = 3

# ======================
# 6) 遊戲流程函式
# ======================
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
    elif level == 5:
        mode = "BOSS"
        b = Boss("big", BIG_BOSS_HP)
        all_sprites.add(b)
        boss_group.add(b)
    else:
        spawn_level_enemies(level)

def remaining_time_sec() -> int:
    elapsed = (pygame.time.get_ticks() - level_start_ms) // 1000
    return max(0, level_time_limit - elapsed)

def maybe_drop_powerup(x: int, y: int, force: bool = False):
    if not force:
        if random.random() > POWERUP_DROP_CHANCE:
            return
        kind = random.choice(POWERUP_TYPES)
    else:
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

    x = player.rect.centerx
    y = player.rect.top

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
    if boss.max_hp <= 0:
        return
    ratio = boss.hp / boss.max_hp
    for thr in BOSS_DROP_THRESHOLDS:
        if ratio <= thr and (boss.drop_flags.get(thr) is False):
            boss.drop_flags[thr] = True
            maybe_drop_powerup(boss.rect.centerx, boss.rect.centery, force=True)

def set_gameover():
    global state
    player.hp = 0
    state = "GAMEOVER"

def new_game():
    global score, level, message_text, message_until
    score = 0
    level = 1
    player.reset_for_new_game()
    clear_groups_for_new_level()
    message_text = ""
    message_until = 0

# ======================
# 7) UI：按鈕
# ======================
start_button = pygame.Rect(WIDTH//2 - 110, HEIGHT - 150, 220, 54)
back_button = pygame.Rect(WIDTH//2 - 110, HEIGHT//2 + 40, 220, 54)  # GameOver/Win 回封面

def draw_button(rect: pygame.Rect, text: str, hover: bool):
    color = (60, 180, 120) if hover else (40, 140, 100)
    pygame.draw.rect(screen, color, rect, border_radius=12)
    pygame.draw.rect(screen, (220, 220, 220), rect, 2, border_radius=12)
    t = font.render(text, True, WHITE)
    screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))

def draw_rules_block(x: int, y: int):
    rules = [
        "規則簡介：",
        "1) 移動：WASD 或 方向鍵",
        "2) 射擊：自動射擊（無需按鍵）",
        "3) 一般關(1/2/4)：打怪 +10 分，達標過關",
        "4) Boss 關(3/5)：擊倒 Boss 才能過關",
        "5) 每關限時，時間到或 HP=0 即失敗",
        "6) 果實：Heal(+25) / Rapid(6s) / Spread(6s)",
        "7) Boss 每損失 15% 血量固定掉果實",
        "   (85/70/55/40/25/10%)",
    ]
    cy = y
    for s in rules:
        t = small_font.render(s, True, GRAY)
        screen.blit(t, (x, cy))
        cy += t.get_height() + 4

# ======================
# 8) 主迴圈
# ======================
running = True
while running:
    clock.tick(60)

    mouse_pos = pygame.mouse.get_pos()
    mouse_down = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # 任何畫面 ESC 離開
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_down = True

    keys = pygame.key.get_pressed()

    # ======================
    # MENU（封面/規則/開始）
    # ======================
    if state == "MENU":
        screen.fill(DARK_BG)

        title = title_font.render("天際防衛戰", True, CYAN)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 70))

        demo = make_fighter_surface(80, 64)
        demo2 = demo.copy()
        draw_engine_flame(demo2, 80, 64, strong=True)
        screen.blit(demo2, (WIDTH//2 - demo2.get_width()//2, 140))

        draw_rules_block(40, 230)

        hover = start_button.collidepoint(mouse_pos)
        draw_button(start_button, "開始遊戲", hover)

        tip = small_font.render("點擊開始後，倒數 3 秒進入遊戲", True, GRAY)
        screen.blit(tip, (WIDTH//2 - tip.get_width()//2, HEIGHT - 70))

        pygame.display.flip()

        if mouse_down and start_button.collidepoint(mouse_pos):
            new_game()
            state = "COUNTDOWN"
            countdown_start_ms = pygame.time.get_ticks()
            # 倒數時不啟動關卡計時，等倒數完才 start_level(1)

        continue

    # ======================
    # COUNTDOWN（倒數 3 秒）
    # ======================
    if state == "COUNTDOWN":
        all_sprites.update(keys)

        screen.fill(DARK_BG)
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
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 60))
            sub = small_font.render("準備開始…", True, GRAY)
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 10))

        pygame.display.flip()
        continue

    # ======================
    # PLAY（正式遊戲）
    # ======================
    if state == "PLAY":
        if mode in ("LEVEL", "BOSS") and remaining_time_sec() <= 0:
            state = "GAMEOVER"

        if mode in ("LEVEL", "BOSS"):
            spawn_player_bullets()

        all_sprites.update(keys)

        if mode == "LEVEL":
            hit_map = pygame.sprite.groupcollide(enemies, bullets, True, True)
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
            for p in got:
                apply_powerup(p.kind)

            target = LEVEL_SCORE_TARGETS.get(level, None)
            if target is not None and score >= target:
                state = "CLEAR"
                message_text = f"LEVEL {level} CLEAR!"
                message_until = pygame.time.get_ticks() + 1200

        elif mode == "BOSS":
            for boss in boss_group:
                if boss.can_shoot():
                    boss.mark_shot()
                    x = boss.rect.centerx
                    y = boss.rect.bottom - 8
                    vxs = (-2, 0, 2) if boss.boss_kind == "mid" else (-3, -1, 0, 1, 3)
                    for vx in vxs:
                        bb = BossBullet(x, y, vx=vx, vy=7)
                        all_sprites.add(bb)
                        boss_bullets.add(bb)

            if len(boss_group) > 0:
                boss = next(iter(boss_group))
                boss_hits = pygame.sprite.spritecollide(boss, bullets, True)
                if boss_hits:
                    boss.hp -= 2 * len(boss_hits)
                    boss_check_and_drop(boss)
                    if boss.hp <= 0:
                        boss.kill()
                        state = "CLEAR"
                        message_text = f"BOSS DEFEATED! (L{level})"
                        message_until = pygame.time.get_ticks() + 1400

            bb_hits = pygame.sprite.spritecollide(player, boss_bullets, True)
            for _ in bb_hits:
                if level == 3:
                    player.hp -= BOSS_BULLET_DAMAGE_MID
                else:
                    player.hp -= BOSS_BULLET_DAMAGE_BIG
                if player.hp <= 0:
                    set_gameover()
                    break

            got = pygame.sprite.spritecollide(player, powerups, True)
            for p in got:
                apply_powerup(p.kind)

    # ======================
    # CLEAR（過關提示）
    # ======================
    if state == "CLEAR":
        if pygame.time.get_ticks() >= message_until:
            if level < 5:
                start_level(level + 1)
                state = "PLAY"
            else:
                state = "WIN"
                message_text = "YOU WIN!"
                message_until = pygame.time.get_ticks() + 2500

    # ======================
    # 繪製（PLAY / CLEAR / WIN / GAMEOVER）
    # ======================
    screen.fill(DARK_BG)
    all_sprites.draw(screen)

    # HUD
    hud1 = font.render(f"Score: {score}  HP: {max(0, player.hp)}", True, WHITE)
    screen.blit(hud1, (10, 10))

    if state not in ("GAMEOVER", "WIN"):
        time_left = remaining_time_sec()
        hud2 = small_font.render(f"LEVEL: {level}  Time: {time_left}s", True, GRAY)
        screen.blit(hud2, (10, 38))

    now = pygame.time.get_ticks()

    if state in ("CLEAR", "WIN") and now < message_until:
        msg = big_font.render(message_text, True, YELLOW)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 40))

    # GameOver/Win：回到封面按鈕
    if state == "GAMEOVER":
        msg = big_font.render("GAME OVER", True, RED)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 40))

        hover = back_button.collidepoint(mouse_pos)
        draw_button(back_button, "回到封面", hover)

        if mouse_down and back_button.collidepoint(mouse_pos):
            state = "MENU"

    if state == "WIN":
        msg = big_font.render("YOU WIN!", True, YELLOW)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 40))

        hover = back_button.collidepoint(mouse_pos)
        draw_button(back_button, "回到封面", hover)

        if mouse_down and back_button.collidepoint(mouse_pos):
            state = "MENU"

    pygame.display.flip()

pygame.quit()
sys.exit()

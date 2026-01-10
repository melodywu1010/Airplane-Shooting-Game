import pygame
import random
import sys
from dataclasses import dataclass

# ======================
# 1) 初始化與設定
# ======================
pygame.init()
WIDTH, HEIGHT = 480, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("噴射機打怪 - 大門檻 + 散射限時 + New Game+")
clock = pygame.time.Clock()

# 顏色
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

font = pygame.font.SysFont("arial", 24)
small_font = pygame.font.SysFont("arial", 18)
big_font = pygame.font.SysFont("arial", 44)

# ======================
# 2) 分數門檻（差距拉大） + New Game+ 門檻提升
# ======================
BASE_THRESHOLDS = [400, 1000, 1800]      # Level2/Level3/BOSS（差距更大）
NG_THRESHOLD_BONUS = 600                 # 每次 NG+，門檻整體增加 600（你可改 400/800）

def thresholds_for_run(ng_plus: int):
    bonus = ng_plus * NG_THRESHOLD_BONUS
    return [t + bonus for t in BASE_THRESHOLDS]

def get_level(score: int, th):
    # th = [to_level2, to_level3, to_boss]
    if score >= th[2]:
        return 4
    if score >= th[1]:
        return 3
    if score >= th[0]:
        return 2
    return 1

# 散射時間：Level2=3秒，Level3=5秒，其餘=8秒（可改）
def spread_duration_ms_by_level(level_now: int) -> int:
    if level_now == 2:
        return 3000
    if level_now == 3:
        return 5000
    return 8000

@dataclass(frozen=True)
class LevelCfg:
    enemy_count: int
    speed_min: int
    speed_max: int
    spawn_y_min: int
    spawn_y_max: int
    drop_enabled: bool
    drop_rate: float

# 注意：這是「基礎」難度，NG+ 會再做加成
BASE_LEVEL_CONFIG = {
    1: LevelCfg(enemy_count=5, speed_min=1, speed_max=3, spawn_y_min=-340, spawn_y_max=-40, drop_enabled=False, drop_rate=0.00),
    2: LevelCfg(enemy_count=6, speed_min=2, speed_max=4, spawn_y_min=-380, spawn_y_max=-40, drop_enabled=True,  drop_rate=0.25),
    3: LevelCfg(enemy_count=7, speed_min=2, speed_max=5, spawn_y_min=-420, spawn_y_max=-40, drop_enabled=True,  drop_rate=0.30),
    4: LevelCfg(enemy_count=8, speed_min=3, speed_max=6, spawn_y_min=-460, spawn_y_max=-40, drop_enabled=True,  drop_rate=0.35),
}

def cfg_with_ng_plus(base_cfg: LevelCfg, ng_plus: int) -> LevelCfg:
    # NG+ 難度加成：怪物數量 +ng、速度 +ng、掉落率 + 0.02*ng（上限 0.60）
    return LevelCfg(
        enemy_count=base_cfg.enemy_count + min(3, ng_plus),  # 避免太爆，最多 +3
        speed_min=base_cfg.speed_min + min(3, ng_plus),
        speed_max=base_cfg.speed_max + min(3, ng_plus),
        spawn_y_min=base_cfg.spawn_y_min,
        spawn_y_max=base_cfg.spawn_y_max,
        drop_enabled=base_cfg.drop_enabled,
        drop_rate=min(0.60, base_cfg.drop_rate + 0.02 * ng_plus),
    )

# ======================
# 3) 造型：戰鬥機、怪物、果實、Boss
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
    inner_color = (255, 255, 255)
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
        pygame.draw.arc(surf, BLACK, (cx-10, cy+2, 20, 16), 3.4, 5.8, 2)

    elif kind == "alien":
        pygame.draw.polygon(surf, (200, 90, 255), [(cx, 3), (size-3, cy), (cx, size-3), (3, cy)])
        pygame.draw.polygon(surf, (120, 40, 180), [(cx, 3), (size-3, cy), (cx, size-3), (3, cy)], 2)
        pygame.draw.circle(surf, WHITE, (cx, cy), 8)
        pygame.draw.circle(surf, BLACK, (cx, cy), 3)
        pygame.draw.line(surf, BLACK, (cx-10, cy+10), (cx+10, cy+10), 2)

    else:  # bot
        pygame.draw.rect(surf, BLUE, (4, 4, size-8, size-8), border_radius=6)
        pygame.draw.rect(surf, (30, 80, 180), (4, 4, size-8, size-8), 2, border_radius=6)
        pygame.draw.circle(surf, WHITE, (cx - 8, cy - 4), 5)
        pygame.draw.circle(surf, WHITE, (cx + 8, cy - 4), 5)
        pygame.draw.circle(surf, BLACK, (cx - 8, cy - 4), 2)
        pygame.draw.circle(surf, BLACK, (cx + 8, cy - 4), 2)
        pygame.draw.rect(surf, BLACK, (cx - 12, cy + 8, 24, 4), border_radius=2)

    return surf

def make_fruit_surface(kind: str, size=22):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    if kind == "rapid":
        pygame.draw.circle(surf, ORANGE, (cx, cy), size//2 - 2)
        pygame.draw.circle(surf, (255, 230, 200), (cx-3, cy-3), 3)
        pygame.draw.line(surf, (30, 120, 30), (cx, 2), (cx-3, 6), 2)

    elif kind == "spread":
        pygame.draw.circle(surf, PURPLE, (cx, cy), size//2 - 2)
        pygame.draw.polygon(surf, (230, 200, 255), [(cx, 4), (cx+4, cy), (cx, size-4), (cx-4, cy)])
        pygame.draw.line(surf, (30, 120, 30), (cx, 2), (cx+3, 6), 2)

    else:  # heal
        pygame.draw.circle(surf, GREEN, (cx, cy), size//2 - 2)
        pygame.draw.rect(surf, WHITE, (cx-2, cy-6, 4, 12), border_radius=2)
        pygame.draw.rect(surf, WHITE, (cx-6, cy-2, 12, 4), border_radius=2)

    return surf

def make_boss_surface(w=160, h=90):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, (200, 50, 50), (10, 20, w-20, h-30), border_radius=18)
    pygame.draw.rect(surf, (120, 20, 20), (10, 20, w-20, h-30), 3, border_radius=18)
    pygame.draw.polygon(surf, (170, 40, 40), [(10, 45), (0, 70), (35, 62)])
    pygame.draw.polygon(surf, (170, 40, 40), [(w-10, 45), (w, 70), (w-35, 62)])
    pygame.draw.circle(surf, WHITE, (w//2 - 22, 45), 10)
    pygame.draw.circle(surf, WHITE, (w//2 + 22, 45), 10)
    pygame.draw.circle(surf, BLACK, (w//2 - 20, 45), 4)
    pygame.draw.circle(surf, BLACK, (w//2 + 20, 45), 4)
    pygame.draw.circle(surf, (255, 200, 0), (w//2, 58), 10)
    pygame.draw.circle(surf, (255, 255, 255), (w//2, 58), 4)
    return surf

# ======================
# 4) 遊戲物件
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

        # 自動射擊
        self.last_shot = 0
        self.base_shoot_delay = 120
        self.shoot_delay = self.base_shoot_delay

        # 尾焰
        self.last_flame_toggle = 0
        self.flame_on = True

        # 技能（限時）
        self.rapid_until = 0
        self.spread_until = 0
        self.spread_level = 0  # 0/1/2（單/三/五）

    def reset_for_new_run(self):
        self.rect.center = (WIDTH//2, HEIGHT-60)
        self.hp = self.hp_max
        self.last_shot = 0
        self.shoot_delay = self.base_shoot_delay
        self.rapid_until = 0
        self.spread_until = 0
        self.spread_level = 0

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

        # 尾焰
        if now - self.last_flame_toggle >= 80:
            self.last_flame_toggle = now
            self.flame_on = not self.flame_on

        # 技能到期
        if now > self.rapid_until:
            self.shoot_delay = self.base_shoot_delay
        else:
            self.shoot_delay = max(50, self.base_shoot_delay // 2)

        if now > self.spread_until:
            self.spread_level = 0

        # 重畫
        center = self.rect.center
        self.image = self.base_image.copy()
        draw_engine_flame(self.image, self.w, self.h, strong=self.flame_on)
        self.rect = self.image.get_rect(center=center)

    def can_fire(self) -> bool:
        now = pygame.time.get_ticks()
        return (now - self.last_shot) >= self.shoot_delay

    def mark_fired(self):
        self.last_shot = pygame.time.get_ticks()


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vx=0, vy=-12):
        super().__init__()
        self.image = pygame.Surface((6, 14), pygame.SRCALPHA)
        pygame.draw.rect(self.image, YELLOW, (0, 0, 6, 14), border_radius=3)
        pygame.draw.rect(self.image, (255, 255, 255), (2, 2, 2, 6), border_radius=1)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = vx
        self.vy = vy

    def update(self, *args):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, cfg: LevelCfg, kind: str):
        super().__init__()
        self.kind = kind
        self.image = make_monster_surface(kind, 40)
        self.rect = self.image.get_rect()
        self.cfg = cfg
        self.reset()

    def reset(self):
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(self.cfg.spawn_y_min, self.cfg.spawn_y_max)
        self.speed_y = random.randrange(self.cfg.speed_min, self.cfg.speed_max)

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
    def __init__(self, ng_plus: int):
        super().__init__()
        self.image = make_boss_surface(160, 90)
        self.rect = self.image.get_rect(center=(WIDTH//2, 110))

        # NG+ 強化 Boss：血量更高、射得更快
        self.max_hp = 260 + ng_plus * 60
        self.hp = self.max_hp

        self.vx = 3 + min(3, ng_plus)
        self.last_shot = 0
        self.base_shot_delay = 650
        self.shot_delay = max(350, self.base_shot_delay - ng_plus * 60)

    def update(self, *args):
        self.rect.x += self.vx
        if self.rect.left <= 10 or self.rect.right >= WIDTH - 10:
            self.vx *= -1

        # 低血量更快
        if self.hp <= self.max_hp * 0.5:
            self.shot_delay = max(260, self.shot_delay - 10)
        if self.hp <= self.max_hp * 0.25:
            self.shot_delay = max(220, self.shot_delay - 10)

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
        pygame.draw.rect(self.image, (255, 255, 255), (3, 3, 2, 5), border_radius=1)
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
boss_bullets = pygame.sprite.Group()
boss_group = pygame.sprite.Group()

player = Player()
all_sprites.add(player)

# 全域狀態
ng_plus = 0                 # 0=第一輪，1=NG+1...
score = 0
game_mode = "PLAY"          # PLAY / BOSS / WIN
level = 1
cfg = None
th = thresholds_for_run(ng_plus)

# UI 提示
level_up_flash_until = 0
skill_hint_until = 0
win_until = 0

def pick_enemy_kind(level_now: int) -> str:
    if level_now == 1:
        return random.choice(["devil", "bot"])
    if level_now == 2:
        return random.choice(["devil", "bot", "alien"])
    return random.choice(["devil", "bot", "alien", "alien"])

def rebuild_enemies(new_cfg: LevelCfg, level_now: int):
    for e in list(enemies):
        e.kill()
    for _ in range(new_cfg.enemy_count):
        kind = pick_enemy_kind(level_now)
        e = Enemy(new_cfg, kind)
        all_sprites.add(e)
        enemies.add(e)

def clear_combat_objects():
    # 清掉敵人/子彈/掉落/ Boss 子彈 / Boss
    for g in (enemies, bullets, powerups, boss_bullets, boss_group):
        for s in list(g):
            s.kill()

def spawn_player_bullets():
    if not player.can_fire():
        return
    player.mark_fired()

    x = player.rect.centerx
    y = player.rect.top
    spread = min(player.spread_level, 2)

    if spread == 0:
        b = Bullet(x, y, vx=0, vy=-12)
        all_sprites.add(b); bullets.add(b)
    elif spread == 1:
        for vx in (-3, 0, 3):
            b = Bullet(x, y, vx=vx, vy=-12)
            all_sprites.add(b); bullets.add(b)
    else:
        for vx in (-4, -2, 0, 2, 4):
            b = Bullet(x, y, vx=vx, vy=-12)
            all_sprites.add(b); bullets.add(b)

def maybe_drop_powerup(enemy: Enemy, level_cfg: LevelCfg):
    if not level_cfg.drop_enabled:
        return
    if random.random() > level_cfg.drop_rate:
        return

    if enemy.kind == "devil":
        kind = random.choices(["heal", "rapid", "spread"], weights=[45, 40, 15], k=1)[0]
    elif enemy.kind == "bot":
        kind = random.choices(["spread", "rapid", "heal"], weights=[45, 35, 20], k=1)[0]
    else:
        kind = random.choices(["rapid", "spread", "heal"], weights=[45, 40, 15], k=1)[0]

    p = PowerUp(kind, enemy.rect.centerx, enemy.rect.centery)
    all_sprites.add(p)
    powerups.add(p)

def apply_powerup(kind: str, level_now: int):
    now = pygame.time.get_ticks()

    if kind == "heal":
        player.hp = min(player.hp_max, player.hp + 25)

    elif kind == "rapid":
        # 6 秒射速加倍
        player.rapid_until = max(player.rapid_until, now + 6000)

    elif kind == "spread":
        # 散射等級 + 持續時間依關卡調整（Level2=3秒，Level3=5秒）
        player.spread_level = random.choice([1, 2])  # 3發或5發
        dur = spread_duration_ms_by_level(level_now)
        player.spread_until = max(player.spread_until, now + dur)

def enter_boss_mode():
    global game_mode
    game_mode = "BOSS"
    # 清掉一般怪物，但保留玩家/玩家子彈（讓戰鬥不中斷）
    for e in list(enemies):
        e.kill()

    boss = Boss(ng_plus)
    all_sprites.add(boss)
    boss_group.add(boss)

def boss_shoot(boss: Boss):
    if not boss.can_shoot():
        return
    boss.mark_shot()

    x = boss.rect.centerx
    y = boss.rect.bottom - 10

    # NG+ 讓彈幕更密：第 2 輪起改成 5 發
    if ng_plus >= 1:
        vxs = (-3, -1, 0, 1, 3)
    else:
        vxs = (-2, 0, 2)

    for vx in vxs:
        bb = BossBullet(x, y, vx=vx, vy=7)
        all_sprites.add(bb)
        boss_bullets.add(bb)

def start_new_run():
    """YOU WIN 後進入 New Game+：提高難度，並重新開始流程。"""
    global ng_plus, score, game_mode, level, cfg, th, level_up_flash_until, skill_hint_until

    ng_plus += 1
    score = 0
    game_mode = "PLAY"

    # 新門檻
    th = thresholds_for_run(ng_plus)

    # 重置玩家
    player.reset_for_new_run()

    # 清戰場並重建 level1
    clear_combat_objects()

    level = 1
    base_cfg = BASE_LEVEL_CONFIG[level]
    cfg = cfg_with_ng_plus(base_cfg, ng_plus)
    rebuild_enemies(cfg, level)

    # 顯示提示
    level_up_flash_until = pygame.time.get_ticks() + 1600
    skill_hint_until = 0  # 進 Level2 才提示

# 第一次開局初始化
base_cfg = BASE_LEVEL_CONFIG[level]
cfg = cfg_with_ng_plus(base_cfg, ng_plus)
rebuild_enemies(cfg, level)

# ======================
# 6) 主迴圈
# ======================
running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    keys = pygame.key.get_pressed()

    # 自動射擊（PLAY/BOSS 都射）
    spawn_player_bullets()

    # 更新所有物件
    all_sprites.update(keys)

    now = pygame.time.get_ticks()

    # ----------------------
    # PLAY：一般怪物流程
    # ----------------------
    if game_mode == "PLAY":
        # 子彈打怪
        hit_map = pygame.sprite.groupcollide(enemies, bullets, True, True)
        for enemy in hit_map:
            score += 10
            maybe_drop_powerup(enemy, cfg)

            kind = pick_enemy_kind(level)
            e = Enemy(cfg, kind)
            all_sprites.add(e)
            enemies.add(e)

        # 怪物撞玩家
        hits = pygame.sprite.spritecollide(player, enemies, True)
        for _ in hits:
            player.hp -= 20
            kind = pick_enemy_kind(level)
            e = Enemy(cfg, kind)
            all_sprites.add(e)
            enemies.add(e)
            if player.hp <= 0:
                running = False

        # 吃果實
        got = pygame.sprite.spritecollide(player, powerups, True)
        for p in got:
            apply_powerup(p.kind, level)

        # 關卡升級（依新的大門檻 th）
        new_level = get_level(score, th)
        if new_level != level:
            level = new_level
            base_cfg = BASE_LEVEL_CONFIG[level]
            cfg = cfg_with_ng_plus(base_cfg, ng_plus)
            rebuild_enemies(cfg, level)
            level_up_flash_until = now + 1400

            if level == 2:
                skill_hint_until = now + 2500

        # 進入 Boss（到達 th[2]）
        if score >= th[2]:
            enter_boss_mode()
            level_up_flash_until = now + 1600

    # ----------------------
    # BOSS：Boss 戰
    # ----------------------
    elif game_mode == "BOSS":
        # Boss 射擊
        for boss in boss_group:
            boss_shoot(boss)

        # 玩家子彈打 Boss
        if len(boss_group) > 0:
            boss = next(iter(boss_group))
            boss_hits = pygame.sprite.spritecollide(boss, bullets, True)
            if boss_hits:
                boss.hp -= 2 * len(boss_hits)
                if boss.hp <= 0:
                    boss.kill()
                    game_mode = "WIN"
                    win_until = now + 2000  # 顯示 YOU WIN 2 秒

        # Boss 子彈打玩家
        bb_hits = pygame.sprite.spritecollide(player, boss_bullets, True)
        for _ in bb_hits:
            player.hp -= 10
            if player.hp <= 0:
                running = False

        #（可選）Boss 戰仍可吃到先前掉落
        got = pygame.sprite.spritecollide(player, powerups, True)
        for p in got:
            apply_powerup(p.kind, level)

    # ----------------------
    # WIN：過關 -> New Game+
    # ----------------------
    elif game_mode == "WIN":
        if now >= win_until:
            start_new_run()

    # ======================
    # 繪製 HUD
    # ======================
    screen.fill(DARK_BG)
    all_sprites.draw(screen)

    # 顯示門檻（PLAY 才需要）
    if game_mode == "PLAY":
        if level == 1:
            target = th[0]
        elif level == 2:
            target = th[1]
        elif level == 3:
            target = th[2]  # 到 Boss
        else:
            target = "BOSS"
    else:
        target = "—"

    rapid_left = max(0, (player.rapid_until - now) // 1000)
    spread_left = max(0, (player.spread_until - now) // 1000)

    hud1 = font.render(f"Score: {score}   HP: {player.hp}", True, WHITE)

    mode_text = f"MODE: {game_mode}  |  NG+ {ng_plus}"
    if game_mode == "BOSS" and len(boss_group) > 0:
        boss = next(iter(boss_group))
        mode_text += f"  |  BOSS HP: {max(0, boss.hp)}/{boss.max_hp}"
    hud2 = small_font.render(f"LEVEL: {level}   Next: {target}   {mode_text}", True, GRAY)

    hud3 = small_font.render(
        f"Rapid: {('ON ' + str(rapid_left)+'s') if rapid_left > 0 else 'OFF'}   "
        f"Spread: {('Lv'+str(player.spread_level)+' '+str(spread_left)+'s') if spread_left > 0 else 'OFF'}",
        True,
        GRAY
    )
    hud4 = small_font.render("Auto Fire ON | Move: WASD/Arrows | ESC: Quit", True, GRAY)

    screen.blit(hud1, (10, 10))
    screen.blit(hud2, (10, 38))
    screen.blit(hud3, (10, 58))
    screen.blit(hud4, (10, 78))

    # 提示
    if now < level_up_flash_until:
        msg = big_font.render("LEVEL UP!", True, YELLOW)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 70))

    if now < skill_hint_until:
        msg = small_font.render("Skills unlocked! Fruits drop now. Spread time depends on Level.", True, YELLOW)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))

    if game_mode == "WIN":
        win = big_font.render("YOU WIN!", True, YELLOW)
        screen.blit(win, (WIDTH//2 - win.get_width()//2, HEIGHT//2 - 20))
        ngmsg = small_font.render("Next: New Game+ (harder)...", True, GRAY)
        screen.blit(ngmsg, (WIDTH//2 - ngmsg.get_width()//2, HEIGHT//2 + 30))

    pygame.display.flip()

# GAME OVER
screen.fill(DARK_BG)
game_over_text = big_font.render("GAME OVER", True, RED)
final_score_text = font.render(f"Final Score: {score}   (NG+ {ng_plus})", True, WHITE)
screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 60))
screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2))
pygame.display.flip()

pygame.time.wait(2500)
pygame.quit()
sys.exit()

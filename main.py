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
pygame.display.set_caption("噴射機打怪 - 關卡(250/500/750) + 技能果實 + 多怪物")
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
# 2) 關卡規則
# ======================
LEVEL_THRESHOLDS = [250, 500, 750]  # 250/500/750
# level: 1..4
def get_level(score: int) -> int:
    if score >= LEVEL_THRESHOLDS[2]:
        return 4
    if score >= LEVEL_THRESHOLDS[1]:
        return 3
    if score >= LEVEL_THRESHOLDS[0]:
        return 2
    return 1

@dataclass(frozen=True)
class LevelCfg:
    enemy_count: int
    speed_min: int
    speed_max: int
    spawn_y_min: int
    spawn_y_max: int
    drop_enabled: bool
    drop_rate: float  # 0~1

LEVEL_CONFIG = {
    1: LevelCfg(enemy_count=5, speed_min=1, speed_max=3, spawn_y_min=-340, spawn_y_max=-40, drop_enabled=False, drop_rate=0.00),
    2: LevelCfg(enemy_count=6, speed_min=2, speed_max=4, spawn_y_min=-380, spawn_y_max=-40, drop_enabled=True,  drop_rate=0.25),
    3: LevelCfg(enemy_count=7, speed_min=2, speed_max=5, spawn_y_min=-420, spawn_y_max=-40, drop_enabled=True,  drop_rate=0.30),
    4: LevelCfg(enemy_count=8, speed_min=3, speed_max=6, spawn_y_min=-460, spawn_y_max=-40, drop_enabled=True,  drop_rate=0.35),
}

# ======================
# 3) 造型：戰鬥機、怪物、果實
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

# 三種怪物造型：圓形惡魔 / 菱形外星 / 方塊機械
def make_monster_surface(kind: str, size=40):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    if kind == "devil":  # 紅色圓形 + 角
        pygame.draw.circle(surf, RED, (cx, cy), size//2 - 2)
        pygame.draw.polygon(surf, PURPLE, [(10, 10), (4, 2), (14, 6)])
        pygame.draw.polygon(surf, PURPLE, [(size-10, 10), (size-4, 2), (size-14, 6)])
        # eyes
        pygame.draw.circle(surf, WHITE, (cx - 8, cy - 3), 6)
        pygame.draw.circle(surf, WHITE, (cx + 8, cy - 3), 6)
        pygame.draw.circle(surf, BLACK, (cx - 6, cy - 2), 2)
        pygame.draw.circle(surf, BLACK, (cx + 6, cy - 2), 2)
        pygame.draw.arc(surf, BLACK, (cx-10, cy+2, 20, 16), 3.4, 5.8, 2)

    elif kind == "alien":  # 紫色菱形 + 單眼
        pygame.draw.polygon(surf, (200, 90, 255), [(cx, 3), (size-3, cy), (cx, size-3), (3, cy)])
        pygame.draw.polygon(surf, (120, 40, 180), [(cx, 3), (size-3, cy), (cx, size-3), (3, cy)], 2)
        pygame.draw.circle(surf, WHITE, (cx, cy), 8)
        pygame.draw.circle(surf, BLACK, (cx, cy), 3)
        pygame.draw.line(surf, BLACK, (cx-10, cy+10), (cx+10, cy+10), 2)

    else:  # "bot": 藍色機械方塊 + 口條
        pygame.draw.rect(surf, BLUE, (4, 4, size-8, size-8), border_radius=6)
        pygame.draw.rect(surf, (30, 80, 180), (4, 4, size-8, size-8), 2, border_radius=6)
        pygame.draw.circle(surf, WHITE, (cx - 8, cy - 4), 5)
        pygame.draw.circle(surf, WHITE, (cx + 8, cy - 4), 5)
        pygame.draw.circle(surf, BLACK, (cx - 8, cy - 4), 2)
        pygame.draw.circle(surf, BLACK, (cx + 8, cy - 4), 2)
        pygame.draw.rect(surf, BLACK, (cx - 12, cy + 8, 24, 4), border_radius=2)

    return surf

# 果實造型：三種技能果實
def make_fruit_surface(kind: str, size=22):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    if kind == "rapid":  # 橘色果實：射速提升（暫時）
        pygame.draw.circle(surf, ORANGE, (cx, cy), size//2 - 2)
        pygame.draw.circle(surf, (255, 230, 200), (cx-3, cy-3), 3)
        pygame.draw.line(surf, (30, 120, 30), (cx, 2), (cx-3, 6), 2)

    elif kind == "spread":  # 紫色果實：散射等級 +1（較偏永久）
        pygame.draw.circle(surf, PURPLE, (cx, cy), size//2 - 2)
        pygame.draw.polygon(surf, (230, 200, 255), [(cx, 4), (cx+4, cy), (cx, size-4), (cx-4, cy)])
        pygame.draw.line(surf, (30, 120, 30), (cx, 2), (cx+3, 6), 2)

    else:  # "heal" 綠色果實：回血
        pygame.draw.circle(surf, GREEN, (cx, cy), size//2 - 2)
        pygame.draw.rect(surf, WHITE, (cx-2, cy-6, 4, 12), border_radius=2)
        pygame.draw.rect(surf, WHITE, (cx-6, cy-2, 12, 4), border_radius=2)

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

        # 技能狀態
        self.spread_level = 0          # 散射等級（0=單發，1=三發，2=五發）
        self.rapid_until = 0           # 射速加倍的到期時間（毫秒）

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

        # 尾焰動畫
        now = pygame.time.get_ticks()
        if now - self.last_flame_toggle >= 80:
            self.last_flame_toggle = now
            self.flame_on = not self.flame_on

        # 射速技能是否仍有效
        if now <= self.rapid_until:
            self.shoot_delay = max(50, self.base_shoot_delay // 2)
        else:
            self.shoot_delay = self.base_shoot_delay

        # 重畫本幀戰機 + 尾焰
        center = self.rect.center
        self.image = self.base_image.copy()
        draw_engine_flame(self.image, self.w, self.h, strong=self.flame_on)
        self.rect = self.image.get_rect(center=center)

    def try_shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            return True
        return False


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
        self.apply_config(cfg)
        self.reset()

    def apply_config(self, cfg: LevelCfg):
        self.cfg = cfg

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


# ======================
# 5) 初始化群組
# ======================
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
powerups = pygame.sprite.Group()

player = Player()
all_sprites.add(player)

score = 0
level = get_level(score)
cfg = LEVEL_CONFIG[level]

level_up_flash_until = 0  # 顯示 LEVEL UP
skill_hint_until = 0      # Level 2 開啟技能提示

# 怪物類型池（隨著關卡增加更多種類的出現機率）
def pick_enemy_kind(level_now: int) -> str:
    if level_now == 1:
        return random.choice(["devil", "bot"])
    if level_now == 2:
        return random.choice(["devil", "bot", "alien"])
    if level_now >= 3:
        # 高關卡讓 alien 多一點
        return random.choice(["devil", "bot", "alien", "alien"])
    return "devil"

def rebuild_enemies(new_cfg: LevelCfg):
    for e in list(enemies):
        e.kill()
    for _ in range(new_cfg.enemy_count):
        kind = pick_enemy_kind(level)
        e = Enemy(new_cfg, kind)
        all_sprites.add(e)
        enemies.add(e)

rebuild_enemies(cfg)

def spawn_bullets_by_skill():
    """依玩家技能生成子彈：自動射擊 + 散射等級"""
    if not player.try_shoot():
        return

    # spread_level: 0=1發, 1=3發, 2=5發（封頂）
    spread = min(player.spread_level, 2)

    # 基準子彈生成位置
    x = player.rect.centerx
    y = player.rect.top

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
    """Level 2 起，怪物被打死可能掉技能果實"""
    if not level_cfg.drop_enabled:
        return
    if random.random() > level_cfg.drop_rate:
        return

    # 不同怪物掉不同傾向（更像遊戲設計）
    # devil：偏 heal / rapid
    # bot：偏 spread
    # alien：偏 rapid / spread
    if enemy.kind == "devil":
        kind = random.choices(["heal", "rapid", "spread"], weights=[45, 40, 15], k=1)[0]
    elif enemy.kind == "bot":
        kind = random.choices(["spread", "rapid", "heal"], weights=[55, 30, 15], k=1)[0]
    else:  # alien
        kind = random.choices(["rapid", "spread", "heal"], weights=[45, 40, 15], k=1)[0]

    p = PowerUp(kind, enemy.rect.centerx, enemy.rect.centery)
    all_sprites.add(p)
    powerups.add(p)

def apply_powerup(kind: str):
    """吃到果實後的技能效果"""
    now = pygame.time.get_ticks()

    if kind == "heal":
        player.hp = min(player.hp_max, player.hp + 25)

    elif kind == "rapid":
        # 射速加倍 6 秒
        player.rapid_until = max(player.rapid_until, now + 6000)

    elif kind == "spread":
        # 散射等級 +1（偏永久，封頂 2）
        player.spread_level = min(2, player.spread_level + 1)

# ======================
# 6) 主迴圈
# ======================
running = True
while running:
    clock.tick(60)

    # 事件：離開
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    keys = pygame.key.get_pressed()

    # 自動射擊（依技能決定單發/散射）
    spawn_bullets_by_skill()

    # 更新
    all_sprites.update(keys)

    # 子彈打怪
    hit_map = pygame.sprite.groupcollide(enemies, bullets, True, True)
    for enemy in hit_map:
        score += 10
        maybe_drop_powerup(enemy, cfg)

        # 補怪（同關卡設定）
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

    # 吃到技能果實
    got = pygame.sprite.spritecollide(player, powerups, True)
    for p in got:
        apply_powerup(p.kind)

    # 關卡升級：250/500/750
    new_level = get_level(score)
    if new_level != level:
        level = new_level
        cfg = LEVEL_CONFIG[level]
        rebuild_enemies(cfg)
        level_up_flash_until = pygame.time.get_ticks() + 1400

        # Level 2 開始提示：技能啟用
        if level == 2:
            skill_hint_until = pygame.time.get_ticks() + 2500

    # HUD
    screen.fill(DARK_BG)
    all_sprites.draw(screen)

    # 下一個門檻顯示
    if level == 1:
        target = LEVEL_THRESHOLDS[0]
    elif level == 2:
        target = LEVEL_THRESHOLDS[1]
    elif level == 3:
        target = LEVEL_THRESHOLDS[2]
    else:
        target = "—"

    hud1 = font.render(f"Score: {score}   HP: {player.hp}", True, WHITE)
    hud2 = small_font.render(
        f"LEVEL: {level}   Next: {target}   Enemies: {cfg.enemy_count}   Drop: {'ON' if cfg.drop_enabled else 'OFF'}",
        True,
        GRAY
    )
    hud3 = small_font.render(
        f"Skills: Spread={player.spread_level}  Rapid={'ON' if pygame.time.get_ticks() <= player.rapid_until else 'OFF'}",
        True,
        GRAY
    )
    hud4 = small_font.render("Auto Fire ON | Move: WASD/Arrows | ESC: Quit", True, GRAY)

    screen.blit(hud1, (10, 10))
    screen.blit(hud2, (10, 38))
    screen.blit(hud3, (10, 58))
    screen.blit(hud4, (10, 78))

    # LEVEL UP 顯示
    now = pygame.time.get_ticks()
    if now < level_up_flash_until:
        msg = big_font.render("LEVEL UP!", True, YELLOW)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 60))

    # Level 2 技能啟用提示
    if now < skill_hint_until:
        msg = small_font.render("Skills unlocked! Monsters may drop fruits (Rapid/Spread/Heal).", True, YELLOW)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))

    pygame.display.flip()

# Game Over
screen.fill(DARK_BG)
game_over_text = big_font.render("GAME OVER", True, RED)
final_score_text = font.render(f"Final Score: {score}", True, WHITE)
screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 60))
screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2))
pygame.display.flip()

pygame.time.wait(2500)
pygame.quit()
sys.exit()

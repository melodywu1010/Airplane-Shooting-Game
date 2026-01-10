import pygame
import random
import sys

# ======================
# 1) 初始化
# ======================
pygame.init()
WIDTH, HEIGHT = 480, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Jet Shooter - 5 Levels + Timer + PowerUps (Boss Drops 15%)")
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

font = pygame.font.SysFont("arial", 24)
small_font = pygame.font.SysFont("arial", 18)
big_font = pygame.font.SysFont("arial", 44)

# ======================
# 2) 關卡設定（五關）
# ======================
# 一般關用分數過關；第3與第5為 Boss 關（打倒 Boss 過關）
LEVEL_SCORE_TARGETS = {
    1: 200,
    2: 450,
    4: 900,
}

# 每關限時（秒）
LEVEL_TIME_LIMIT = {
    1: 45,
    2: 50,
    3: 60,
    4: 55,
    5: 70,
}

# 一般怪物參數（每關）
ENEMY_SETTINGS = {
    1: {"count": 5, "speed_min": 1, "speed_max": 3},
    2: {"count": 6, "speed_min": 2, "speed_max": 4},
    4: {"count": 7, "speed_min": 2, "speed_max": 5},
}

# Boss 設定（第3關降難度）
MID_BOSS_HP = 140   # 原 180 -> 140
BIG_BOSS_HP = 320

# 技能果實（基本版）
POWERUP_DROP_CHANCE = 0.18  # 一般怪物死亡後掉落機率
POWERUP_TYPES = ["heal", "rapid", "spread"]
RAPID_DURATION_MS = 6000
SPREAD_DURATION_MS = 6000

# Boss 掉落：每 15% 血量掉一顆（85/70/55/40/25/10）
BOSS_DROP_THRESHOLDS = [0.85, 0.70, 0.55, 0.40, 0.25, 0.10]

# Boss 子彈傷害（第3關降低）
BOSS_BULLET_DAMAGE_MID = 7    # 原 10 -> 7
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

        # Auto fire base
        self.last_shot = 0
        self.base_shoot_delay = 120
        self.shoot_delay = self.base_shoot_delay

        # Flame animation
        self.last_flame_toggle = 0
        self.flame_on = True

        # PowerUp timed effects
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

        # flame toggle
        if now - self.last_flame_toggle >= 80:
            self.last_flame_toggle = now
            self.flame_on = not self.flame_on

        # rapid effect
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
        # 第3關降難度：中Boss射擊間隔變慢
        self.shot_delay = 1000 if boss_kind == "mid" else 650

        # Boss 掉落狀態：每個門檻只掉一次
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
# 5) 遊戲流程：關卡初始化/切換
# ======================
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
powerups = pygame.sprite.Group()
boss_group = pygame.sprite.Group()
boss_bullets = pygame.sprite.Group()

player = Player()
all_sprites.add(player)

score = 0
level = 1
mode = "LEVEL"  # LEVEL / BOSS / CLEAR / GAMEOVER / WIN
level_start_ms = pygame.time.get_ticks()
level_time_limit = LEVEL_TIME_LIMIT[level]

message_until = 0
message_text = ""

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
    """掉落技能果實。force=True 用於 Boss 固定掉落。"""
    if not force:
        if random.random() > POWERUP_DROP_CHANCE:
            return
        kind = random.choice(POWERUP_TYPES)
    else:
        # Boss 固定掉落：偏向 heal，降低Boss戰挫折感
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
    """自動射擊：一般=單發；Spread=三連發"""
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
    """Boss 血量到達門檻時固定掉落果實（每 15% 一顆）。"""
    if boss.max_hp <= 0:
        return
    ratio = boss.hp / boss.max_hp
    for thr in BOSS_DROP_THRESHOLDS:
        if ratio <= thr and (boss.drop_flags.get(thr) is False):
            boss.drop_flags[thr] = True
            maybe_drop_powerup(boss.rect.centerx, boss.rect.centery, force=True)

def set_gameover():
    global mode
    player.hp = 0
    mode = "GAMEOVER"

# 開始第一關
start_level(1)

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

    # timer check
    if mode in ("LEVEL", "BOSS") and remaining_time_sec() <= 0:
        mode = "GAMEOVER"

    # auto fire（GameOver/Win 不射）
    if mode in ("LEVEL", "BOSS"):
        spawn_player_bullets()

    # update（GameOver/Win 仍可更新做畫面穩定，但不影響玩法）
    all_sprites.update(keys)

    # collisions
    if mode == "LEVEL":
        hit_map = pygame.sprite.groupcollide(enemies, bullets, True, True)
        for enemy in hit_map:
            score += 10
            # 一般關卡（1/2/4）怪物死亡可能掉落
            if level in (1, 2, 4):
                maybe_drop_powerup(enemy.rect.centerx, enemy.rect.centery, force=False)

            # respawn
            st = ENEMY_SETTINGS[level]
            e = Enemy(st["speed_min"], st["speed_max"])
            all_sprites.add(e)
            enemies.add(e)

        # enemy hit player
        hits = pygame.sprite.spritecollide(player, enemies, True)
        for _ in hits:
            player.hp -= 20
            if player.hp <= 0:
                set_gameover()
                break
            else:
                st = ENEMY_SETTINGS[level]
                e = Enemy(st["speed_min"], st["speed_max"])
                all_sprites.add(e)
                enemies.add(e)

        # eat powerups
        got = pygame.sprite.spritecollide(player, powerups, True)
        for p in got:
            apply_powerup(p.kind)

        # clear by score
        target = LEVEL_SCORE_TARGETS.get(level, None)
        if target is not None and score >= target:
            mode = "CLEAR"
            message_text = f"LEVEL {level} CLEAR!"
            message_until = pygame.time.get_ticks() + 1200

    elif mode == "BOSS":
        # boss shoot
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

        # player bullets hit boss
        if len(boss_group) > 0:
            boss = next(iter(boss_group))
            boss_hits = pygame.sprite.spritecollide(boss, bullets, True)
            if boss_hits:
                boss.hp -= 2 * len(boss_hits)

                # Boss 掉落檢查（在扣血後檢查門檻）
                boss_check_and_drop(boss)

                if boss.hp <= 0:
                    boss.kill()
                    mode = "CLEAR"
                    message_text = f"BOSS DEFEATED! (L{level})"
                    message_until = pygame.time.get_ticks() + 1400

        # boss bullets hit player
        bb_hits = pygame.sprite.spritecollide(player, boss_bullets, True)
        for _ in bb_hits:
            if level == 3:
                player.hp -= BOSS_BULLET_DAMAGE_MID
            else:
                player.hp -= BOSS_BULLET_DAMAGE_BIG

            if player.hp <= 0:
                set_gameover()
                break

        # eat powerups
        got = pygame.sprite.spritecollide(player, powerups, True)
        for p in got:
            apply_powerup(p.kind)

    # clear -> next level
    if mode == "CLEAR":
        if pygame.time.get_ticks() >= message_until:
            if level < 5:
                start_level(level + 1)
            else:
                mode = "WIN"
                message_text = "YOU WIN!"
                message_until = pygame.time.get_ticks() + 2500

    # draw
    screen.fill(DARK_BG)
    all_sprites.draw(screen)

    # ============= HUD（只留指定內容） =============
    hud1 = font.render(f"Score: {score}  HP: {max(0, player.hp)}", True, WHITE)
    screen.blit(hud1, (10, 10))

    # GAMEOVER 時不顯示 Time（只顯示 Score/HP）
    if mode != "GAMEOVER":
        time_left = remaining_time_sec()
        hud2 = small_font.render(f"LEVEL: {level}  Time: {time_left}s", True, GRAY)
        screen.blit(hud2, (10, 38))
    # ===============================================

    # messages
    now = pygame.time.get_ticks()
    if mode in ("CLEAR", "WIN") and now < message_until:
        msg = big_font.render(message_text, True, YELLOW)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 40))

    if mode == "GAMEOVER":
        msg = big_font.render("GAME OVER", True, RED)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 40))

    pygame.display.flip()

    # end after WIN display
    if mode == "WIN" and pygame.time.get_ticks() >= message_until:
        running = False

pygame.quit()
sys.exit()

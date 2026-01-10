import pygame
import random
import sys

# --- 1. 初始化與設定 ---
pygame.init()
WIDTH, HEIGHT = 480, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("噴射機打怪專題 - 自動射擊版（尾焰動畫 / WASD修正）")
clock = pygame.time.Clock()

# 顏色與字體
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
YELLOW = (255, 255, 0)
RED = (255, 60, 60)
PURPLE = (170, 80, 255)
CYAN = (0, 220, 255)

font = pygame.font.SysFont("arial", 24)
small_font = pygame.font.SysFont("arial", 18)
big_font = pygame.font.SysFont("arial", 48)


# --- 2. 造型繪製：戰鬥機 / 怪物（透明底） ---

def make_fighter_surface(w=60, h=48):
    """用幾何圖形畫出戰鬥機（透明底）"""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # 機身（三角）
    body = [(w // 2, 4), (8, h - 10), (w - 8, h - 10)]
    pygame.draw.polygon(surf, CYAN, body)

    # 座艙
    pygame.draw.ellipse(surf, (40, 40, 40), (w//2 - 8, 14, 16, 18))

    # 左右機翼
    left_wing = [(12, h - 16), (2, h - 6), (18, h - 6)]
    right_wing = [(w - 12, h - 16), (w - 2, h - 6), (w - 18, h - 6)]
    pygame.draw.polygon(surf, (30, 160, 190), left_wing)
    pygame.draw.polygon(surf, (30, 160, 190), right_wing)

    # 尾翼
    tail = [(w // 2 - 10, h - 18), (w // 2, h - 28), (w // 2 + 10, h - 18)]
    pygame.draw.polygon(surf, (20, 120, 150), tail)

    # 外框
    pygame.draw.polygon(surf, (0, 120, 150), body, 2)

    return surf


def draw_engine_flame(surf, w, h, strong=False):
    """在戰鬥機尾部畫尾焰（閃爍/長短變化）"""
    cx = w // 2
    base_y = h - 8  # 接近機尾
    # 隨機火焰長度（strong 代表更長）
    flame_len = random.randint(10, 16) if strong else random.randint(6, 12)

    # 火焰主體（橘黃）
    flame_color = (255, 170, 0) if strong else (255, 210, 0)
    inner_color = (255, 255, 255)

    # 外焰（三角）
    outer = [(cx, base_y + flame_len), (cx - 6, base_y), (cx + 6, base_y)]
    pygame.draw.polygon(surf, flame_color, outer)

    # 內焰（小一點）
    inner = [(cx, base_y + max(4, flame_len - 4)), (cx - 3, base_y + 1), (cx + 3, base_y + 1)]
    pygame.draw.polygon(surf, inner_color, inner)


def make_monster_surface(w=40, h=40):
    """怪物（紅色主體 + 眼睛）"""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # 身體（圓）
    pygame.draw.circle(surf, RED, (w // 2, h // 2), min(w, h)//2 - 2)

    # 角
    pygame.draw.polygon(surf, PURPLE, [(10, 10), (4, 2), (14, 6)])
    pygame.draw.polygon(surf, PURPLE, [(w-10, 10), (w-4, 2), (w-14, 6)])

    # 眼睛
    pygame.draw.circle(surf, WHITE, (w // 2 - 8, h // 2 - 3), 6)
    pygame.draw.circle(surf, WHITE, (w // 2 + 8, h // 2 - 3), 6)
    pygame.draw.circle(surf, BLACK, (w // 2 - 6, h // 2 - 2), 2)
    pygame.draw.circle(surf, BLACK, (w // 2 + 6, h // 2 - 2), 2)

    # 嘴巴
    pygame.draw.arc(surf, BLACK, (w//2 - 10, h//2 + 2, 20, 16), 3.4, 5.8, 2)

    return surf


# --- 3. 類別定義 ---

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.w, self.h = 60, 48
        self.base_image = make_fighter_surface(self.w, self.h)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 12

        self.speed = 8
        self.hp = 100

        # 自動射擊冷卻（毫秒）
        self.last_shot = 0
        self.shoot_delay = 120  # 90~200 可自行調

        # 尾焰動畫
        self.last_flame_toggle = 0
        self.flame_on = True

    def update(self, keys):
        # WASD + 方向鍵（穩定：由主迴圈傳 keys 進來）
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed

        # 邊界限制
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, WIDTH)
        self.rect.top = max(self.rect.top, 0)
        self.rect.bottom = min(self.rect.bottom, HEIGHT)

        # 尾焰動畫更新（每 80ms 閃爍一次）
        now = pygame.time.get_ticks()
        if now - self.last_flame_toggle >= 80:
            self.last_flame_toggle = now
            self.flame_on = not self.flame_on

        # 重新生成本幀圖像（避免越畫越髒）
        center = self.rect.center
        self.image = self.base_image.copy()
        if self.flame_on:
            draw_engine_flame(self.image, self.w, self.h, strong=True)
        else:
            # 也可以在 off 時畫短焰，視覺更順
            draw_engine_flame(self.image, self.w, self.h, strong=False)

        self.rect = self.image.get_rect(center=center)

    def try_shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            return Bullet(self.rect.centerx, self.rect.top)
        return None


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((6, 14), pygame.SRCALPHA)
        pygame.draw.rect(self.image, YELLOW, (0, 0, 6, 14), border_radius=3)
        pygame.draw.rect(self.image, (255, 255, 255), (2, 2, 2, 6), border_radius=1)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed_y = -12

    def update(self, *args):
        self.rect.y += self.speed_y
        if self.rect.bottom < 0:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = make_monster_surface(40, 40)
        self.rect = self.image.get_rect()
        self.reset()

    def reset(self):
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(-300, -40)
        self.speed_y = random.randrange(1,3)

    def update(self, *args):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT:
            self.reset()


# --- 4. 建立群組與初始化 ---
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()

player = Player()
all_sprites.add(player)

ENEMY_COUNT = 5
for _ in range(ENEMY_COUNT):
    e = Enemy()
    all_sprites.add(e)
    enemies.add(e)

score = 0


def spawn_bullet():
    bullet = player.try_shoot()
    if bullet:
        all_sprites.add(bullet)
        bullets.add(bullet)


# --- 5. 遊戲主迴圈 ---
running = True
while running:
    clock.tick(60)

    # 事件（只處理離開）
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # 取得按鍵狀態（統一在主迴圈做，避免 WASD 當機）
    keys = pygame.key.get_pressed()

    # 自動射擊
    spawn_bullet()

    # 更新（把 keys 傳給所有 sprite；只有 Player 用得到，其他會忽略）
    all_sprites.update(keys)

    # 碰撞：子彈打到怪物
    hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
    for _ in hits:
        score += 10
        e = Enemy()
        all_sprites.add(e)
        enemies.add(e)

    # 碰撞：怪物撞到戰鬥機
    hits = pygame.sprite.spritecollide(player, enemies, True)
    for _ in hits:
        player.hp -= 20
        e = Enemy()
        all_sprites.add(e)
        enemies.add(e)
        if player.hp <= 0:
            running = False

    # 繪製
    screen.fill((10, 10, 18))
    all_sprites.draw(screen)

    hud1 = font.render(f"Score: {score}   HP: {player.hp}", True, WHITE)
    hud2 = small_font.render(
        f"Auto Fire ON | ShootDelay(ms): {player.shoot_delay} | Move: WASD/Arrows",
        True,
        GRAY
    )
    hud3 = small_font.render("ESC: Quit", True, GRAY)

    screen.blit(hud1, (10, 10))
    screen.blit(hud2, (10, 40))
    screen.blit(hud3, (10, 62))

    pygame.display.flip()

# --- 6. Game Over ---
screen.fill((10, 10, 18))
game_over_text = big_font.render("GAME OVER", True, RED)
final_score_text = font.render(f"Final Score: {score}", True, WHITE)

screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 60))
screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2))
pygame.display.flip()

pygame.time.wait(2500)
pygame.quit()
sys.exit()

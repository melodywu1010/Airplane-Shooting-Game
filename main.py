import pygame
import random
import sys

# --- 1. 初始化與設定 ---
pygame.init()
WIDTH, HEIGHT = 480, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("噴射機打怪專題 - 自動射擊版（戰鬥機&怪物）")
clock = pygame.time.Clock()

# 顏色與字體
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
DARK_GRAY = (90, 90, 90)
YELLOW = (255, 255, 0)
RED = (255, 60, 60)
PURPLE = (170, 80, 255)
CYAN = (0, 220, 255)

font = pygame.font.SysFont("arial", 24)
small_font = pygame.font.SysFont("arial", 18)
big_font = pygame.font.SysFont("arial", 48)


# --- 2. 造型繪製：戰鬥機 / 怪物（取代方塊） ---

def make_fighter_surface(w=60, h=48):
    """用幾何圖形畫出戰鬥機（透明底）"""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # 機身（主三角）
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

    # 邊框線（增加銳利感）
    pygame.draw.polygon(surf, (0, 120, 150), body, 2)

    return surf


def make_monster_surface(w=40, h=40):
    """用幾何圖形畫出怪物（紅色主體 + 眼睛）"""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # 身體（圓形）
    pygame.draw.circle(surf, RED, (w // 2, h // 2), min(w, h)//2 - 2)

    # 角/刺
    pygame.draw.polygon(surf, PURPLE, [(10, 10), (4, 2), (14, 6)])
    pygame.draw.polygon(surf, PURPLE, [(w-10, 10), (w-4, 2), (w-14, 6)])

    # 眼睛（白底 + 黑瞳）
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
        self.image = make_fighter_surface(60, 48)
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 12

        self.speed = 8
        self.hp = 100

        # 自動射擊冷卻（毫秒）
        self.last_shot = 0
        self.shoot_delay = 120  # 越小射越快（建議 90~200）

    def update(self):
        pygame.event.pump()
        keys = pygame.key.get_pressed()

        # WASD + 方向鍵
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

    def update(self):
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
        self.rect.y = random.randrange(-180, -40)
        self.speed_y = random.randrange(2, 6)

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT:
            self.reset()


# --- 4. 建立群組與初始化 ---
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()

player = Player()
all_sprites.add(player)

ENEMY_COUNT = 8
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

    # 自動射擊
    spawn_bullet()

    # 更新
    all_sprites.update()

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
    screen.fill((10, 10, 18))  # 深色背景
    all_sprites.draw(screen)

    focused = pygame.key.get_focused()
    hud1 = font.render(f"Score: {score}   HP: {player.hp}", True, WHITE)
    hud2 = small_font.render(
        f"Auto Fire ON | Focused: {focused} | ShootDelay(ms): {player.shoot_delay}",
        True,
        GRAY
    )
    hud3 = small_font.render("Move: WASD or Arrow Keys | ESC: Quit", True, GRAY)

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

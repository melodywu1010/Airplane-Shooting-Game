import pygame
import random
import sys

# --- 1. 初始化與設定 ---
pygame.init()
WIDTH, HEIGHT = 480, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("噴射機打怪專題 - 自動射擊版")
clock = pygame.time.Clock()

# 顏色與字體
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (180, 180, 180)

font = pygame.font.SysFont("arial", 24)
small_font = pygame.font.SysFont("arial", 18)
big_font = pygame.font.SysFont("arial", 48)


# --- 2. 類別定義 ---

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 40))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 10

        self.speed = 8
        self.hp = 100

        # 自動射擊冷卻（毫秒）：越小射越快
        self.last_shot = 0
        self.shoot_delay = 120  # 建議 90~200，自行調整

    def update(self):
        # 確保鍵盤狀態更新
        pygame.event.pump()
        keys = pygame.key.get_pressed()

        # 支援方向鍵與 WASD
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed

        # 邊界限制
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT

    def try_shoot(self):
        """回傳 Bullet 或 None（用冷卻控制自動連射）"""
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            return Bullet(self.rect.centerx, self.rect.top)
        return None


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 12))
        self.image.fill(YELLOW)
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
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.reset()

    def reset(self):
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-150, -40)
        self.speed_y = random.randrange(2, 6)

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT:
            self.reset()


# --- 3. 建立群組與初始化 ---
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
    """自動嘗試生成子彈（受冷卻控制）"""
    bullet = player.try_shoot()
    if bullet:
        all_sprites.add(bullet)
        bullets.add(bullet)


# --- 4. 遊戲主迴圈 ---
running = True
while running:
    clock.tick(60)

    # (A) 事件處理（只處理 QUIT/ESC）
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # (B) 自動射擊：每幀都呼叫，但會由冷卻控制射速
    spawn_bullet()

    # (C) 更新
    all_sprites.update()

    # (D) 碰撞判定
    # 1) 子彈打到敵人：敵人消失、加分、補一隻
    hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
    for _ in hits:
        score += 10
        e = Enemy()
        all_sprites.add(e)
        enemies.add(e)

    # 2) 敵人撞到玩家：扣血、敵人消失、補一隻
    hits = pygame.sprite.spritecollide(player, enemies, True)
    for _ in hits:
        player.hp -= 20
        e = Enemy()
        all_sprites.add(e)
        enemies.add(e)

        if player.hp <= 0:
            running = False

    # (E) 繪製
    screen.fill((0, 0, 0))
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

# --- 5. 遊戲結束畫面 ---
screen.fill((0, 0, 0))
game_over_text = big_font.render("GAME OVER", True, RED)
final_score_text = font.render(f"Final Score: {score}", True, WHITE)

screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 60))
screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2))
pygame.display.flip()

pygame.time.wait(2500)
pygame.quit()
sys.exit()

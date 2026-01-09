import pygame
import random

# 初始化
pygame.init()
WIDTH, HEIGHT = 480, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("噴射機打怪專題")
clock = pygame.time.Clock()

# 顏色定義
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# 玩家類別
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 40))
        self.image.fill((0, 255, 0)) # 暫時用綠色方塊代表飛機
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 10
        self.speed_x = 8

    def update(self):
        # 鍵盤操控
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed_x
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed_x
        
        # 邊界限制
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > WIDTH: self.rect.right = WIDTH

# 遊戲主迴圈
all_sprites = pygame.sprite.Group()
player = Player()
all_sprites.add(player)

running = True
while running:
    # 1. 處理輸入
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 2. 更新數據
    all_sprites.update()

    # 3. 繪製畫面
    screen.fill((0, 0, 0)) # 背景塗黑
    all_sprites.draw(screen) # 畫出所有角色
    pygame.display.flip() # 顯示出來
pygame.quit()
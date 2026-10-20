import pygame
import random
import sys
import math

# ======================
# CONFIG
# ======================
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 700
CELL_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // CELL_SIZE
GRID_HEIGHT = (WINDOW_HEIGHT - 80) // CELL_SIZE   # leave space for HUD

FPS = 60

# Colors
BLACK = (8, 8, 15)
DARK = (18, 18, 30)
WHITE = (240, 240, 255)
GREEN = (0, 255, 120)
DARK_GREEN = (0, 180, 80)
RED = (255, 60, 80)
GOLD = (255, 215, 0)
PURPLE = (160, 80, 255)
CYAN = (0, 220, 255)
GRAY = (60, 60, 90)
LIGHT_GRAY = (120, 120, 160)

# ======================
# HELPER FUNCTIONS
# ======================
def draw_rounded_rect(surface, color, rect, radius=8, border=0, border_color=None):
    x, y, w, h = rect
    pygame.draw.rect(surface, color, (x + radius, y, w - 2*radius, h))
    pygame.draw.rect(surface, color, (x, y + radius, w, h - 2*radius))
    pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius)
    if border and border_color:
        pygame.draw.rect(surface, border_color, (x + radius, y, w - 2*radius, border))
        pygame.draw.rect(surface, border_color, (x + radius, y + h - border, w - 2*radius, border))
        pygame.draw.rect(surface, border_color, (x, y + radius, border, h - 2*radius))
        pygame.draw.rect(surface, border_color, (x + w - border, y + radius, border, h - 2*radius))

def draw_glow(surface, pos, color, radius, intensity=3):
    for i in range(intensity, 0, -1):
        alpha = 40 // i
        s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, alpha), (radius, radius), radius // i + 4)
        surface.blit(s, (pos[0] - radius, pos[1] - radius))

# ======================
# PARTICLE SYSTEM
# ======================
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.life = random.randint(20, 40)
        self.size = random.randint(3, 7)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size = max(1, self.size - 0.1)

    def draw(self, surface):
        if self.life > 0:
            alpha = min(255, self.life * 6)
            s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
            surface.blit(s, (self.x - self.size, self.y - self.size))

# ======================
# BUTTON CLASS
# ======================
class Button:
    def __init__(self, x, y, w, h, text, color=GREEN, hover_color=CYAN):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface, font):
        color = self.hover_color if self.is_hovered else self.color
        draw_rounded_rect(surface, color, self.rect, radius=12)
        draw_rounded_rect(surface, (0, 0, 0), self.rect.inflate(-6, -6), radius=10)
        draw_rounded_rect(surface, color, self.rect.inflate(-10, -10), radius=8)

        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

# ======================
# MAIN GAME CLASS
# ======================
class DJCobra:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("DJ Cobra")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_large = pygame.font.SysFont("arial", 56, bold=True)
        self.font_medium = pygame.font.SysFont("arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("arial", 24)
        self.font_tiny = pygame.font.SysFont("arial", 18)

        # Game states
        self.state = "menu"          # menu, mode, level, playing, pause, gameover
        self.mode = "classic"       # classic, speed, wrap
        self.level = 1

        self.particles = []
        self.high_score = 0

        self.create_buttons()
        self.reset_game()

    def create_buttons(self):
        # Main Menu
        self.btn_play = Button(250, 280, 300, 55, "PLAY")
        self.btn_modes = Button(250, 350, 300, 55, "SELECT MODE")
        self.btn_quit = Button(250, 420, 300, 55, "QUIT", RED, (255, 100, 100))

        # Mode Select
        self.btn_classic = Button(200, 220, 400, 55, "CLASSIC MODE")
        self.btn_speed = Button(200, 290, 400, 55, "SPEED MODE")
        self.btn_wrap = Button(200, 360, 400, 55, "WRAP MODE")
        self.btn_back = Button(250, 480, 300, 50, "BACK", GRAY, LIGHT_GRAY)

        # Level Select
        self.level_buttons = []
        for i in range(5):
            self.level_buttons.append(
                Button(250, 180 + i * 70, 300, 55, f"LEVEL {i+1}")
            )

    def reset_game(self):
        start_x = GRID_WIDTH // 2
        start_y = GRID_HEIGHT // 2
        self.snake = [(start_x, start_y), (start_x-1, start_y), (start_x-2, start_y)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = self.spawn_food()
        self.score = 0
        self.game_over = False
        self.move_timer = 0
        self.base_speed = max(4, 12 - self.level)   # higher level = faster
        self.current_speed = self.base_speed
        self.obstacles = self.generate_obstacles()
        self.particles = []

    def generate_obstacles(self):
        obs = []
        if self.level >= 3:
            count = (self.level - 2) * 4
            for _ in range(count):
                while True:
                    x = random.randint(2, GRID_WIDTH - 3)
                    y = random.randint(2, GRID_HEIGHT - 3)
                    if (x, y) not in self.snake and (x, y) != self.food:
                        obs.append((x, y))
                        break
        return obs

    def spawn_food(self):
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in self.snake and (x, y) not in getattr(self, 'obstacles', []):
                return (x, y)

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Menu navigation
            if self.state == "menu":
                self.btn_play.check_hover(mouse_pos)
                self.btn_modes.check_hover(mouse_pos)
                self.btn_quit.check_hover(mouse_pos)

                if self.btn_play.is_clicked(mouse_pos, event):
                    self.state = "level"
                elif self.btn_modes.is_clicked(mouse_pos, event):
                    self.state = "mode"
                elif self.btn_quit.is_clicked(mouse_pos, event):
                    pygame.quit()
                    sys.exit()

            elif self.state == "mode":
                self.btn_classic.check_hover(mouse_pos)
                self.btn_speed.check_hover(mouse_pos)
                self.btn_wrap.check_hover(mouse_pos)
                self.btn_back.check_hover(mouse_pos)

                if self.btn_classic.is_clicked(mouse_pos, event):
                    self.mode = "classic"
                    self.state = "menu"
                elif self.btn_speed.is_clicked(mouse_pos, event):
                    self.mode = "speed"
                    self.state = "menu"
                elif self.btn_wrap.is_clicked(mouse_pos, event):
                    self.mode = "wrap"
                    self.state = "menu"
                elif self.btn_back.is_clicked(mouse_pos, event):
                    self.state = "menu"

            elif self.state == "level":
                self.btn_back.check_hover(mouse_pos)
                for i, btn in enumerate(self.level_buttons):
                    btn.check_hover(mouse_pos)
                    if btn.is_clicked(mouse_pos, event):
                        self.level = i + 1
                        self.reset_game()
                        self.state = "playing"

                if self.btn_back.is_clicked(mouse_pos, event):
                    self.state = "menu"

            elif self.state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP and self.direction != (0, 1):
                        self.next_direction = (0, -1)
                    elif event.key == pygame.K_DOWN and self.direction != (0, -1):
                        self.next_direction = (0, 1)
                    elif event.key == pygame.K_LEFT and self.direction != (1, 0):
                        self.next_direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT and self.direction != (-1, 0):
                        self.next_direction = (1, 0)
                    elif event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                        self.state = "pause"

            elif self.state == "pause":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                        self.state = "playing"
                    elif event.key == pygame.K_q:
                        self.state = "menu"

            elif self.state == "gameover":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.state = "playing"
                    elif event.key == pygame.K_m:
                        self.state = "menu"

    def update(self):
        if self.state != "playing":
            return

        self.move_timer += 1
        if self.move_timer < self.current_speed:
            return
        self.move_timer = 0

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # Wrap mode
        if self.mode == "wrap":
            new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)
        else:
            # Wall collision
            if not (0 <= new_head[0] < GRID_WIDTH and 0 <= new_head[1] < GRID_HEIGHT):
                self.game_over = True
                self.state = "gameover"
                if self.score > self.high_score:
                    self.high_score = self.score
                return

        # Self / Obstacle collision
        if new_head in self.snake or new_head in self.obstacles:
            self.game_over = True
            self.state = "gameover"
            if self.score > self.high_score:
                self.high_score = self.score
            return

        self.snake.insert(0, new_head)

        # Eat food
        if new_head == self.food:
            self.score += 10 * self.level
            # Particles
            fx = self.food[0] * CELL_SIZE + CELL_SIZE // 2
            fy = self.food[1] * CELL_SIZE + CELL_SIZE // 2 + 80
            for _ in range(18):
                self.particles.append(Particle(fx, fy, random.choice([GOLD, RED, CYAN])))
            self.food = self.spawn_food()

            # Speed mode acceleration
            if self.mode == "speed" and self.current_speed > 3:
                self.current_speed = max(3, self.current_speed - 0.4)
        else:
            self.snake.pop()

        # Update particles
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

    def draw_background(self):
        self.screen.fill(BLACK)
        # Subtle grid
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(self.screen, (25, 25, 45), (x, 80), (x, WINDOW_HEIGHT), 1)
        for y in range(80, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(self.screen, (25, 25, 45), (0, y), (WINDOW_WIDTH, y), 1)

    def draw_snake(self):
        for i, (x, y) in enumerate(self.snake):
            px = x * CELL_SIZE
            py = y * CELL_SIZE + 80
            color = GREEN if i == 0 else DARK_GREEN

            # Glow on head
            if i == 0:
                draw_glow(self.screen, (px + CELL_SIZE//2, py + CELL_SIZE//2), GREEN, 18)

            draw_rounded_rect(self.screen, color, (px+1, py+1, CELL_SIZE-2, CELL_SIZE-2), radius=6)

            # Eyes on head
            if i == 0:
                eye_offset = 4
                if self.direction == (1, 0):   # right
                    pygame.draw.circle(self.screen, WHITE, (px + 14, py + 6), 3)
                    pygame.draw.circle(self.screen, WHITE, (px + 14, py + 14), 3)
                    pygame.draw.circle(self.screen, BLACK, (px + 15, py + 6), 1)
                    pygame.draw.circle(self.screen, BLACK, (px + 15, py + 14), 1)
                elif self.direction == (-1, 0):  # left
                    pygame.draw.circle(self.screen, WHITE, (px + 6, py + 6), 3)
                    pygame.draw.circle(self.screen, WHITE, (px + 6, py + 14), 3)
                    pygame.draw.circle(self.screen, BLACK, (px + 5, py + 6), 1)
                    pygame.draw.circle(self.screen, BLACK, (px + 5, py + 14), 1)
                elif self.direction == (0, -1):  # up
                    pygame.draw.circle(self.screen, WHITE, (px + 6, py + 6), 3)
                    pygame.draw.circle(self.screen, WHITE, (px + 14, py + 6), 3)
                    pygame.draw.circle(self.screen, BLACK, (px + 6, py + 5), 1)
                    pygame.draw.circle(self.screen, BLACK, (px + 14, py + 5), 1)
                else:  # down
                    pygame.draw.circle(self.screen, WHITE, (px + 6, py + 14), 3)
                    pygame.draw.circle(self.screen, WHITE, (px + 14, py + 14), 3)
                    pygame.draw.circle(self.screen, BLACK, (px + 6, py + 15), 1)
                    pygame.draw.circle(self.screen, BLACK, (px + 14, py + 15), 1)

    def draw_food(self):
        fx = self.food[0] * CELL_SIZE
        fy = self.food[1] * CELL_SIZE + 80
        draw_glow(self.screen, (fx + CELL_SIZE//2, fy + CELL_SIZE//2), RED, 16)
        draw_rounded_rect(self.screen, RED, (fx+2, fy+2, CELL_SIZE-4, CELL_SIZE-4), radius=8)
        # Shine
        pygame.draw.circle(self.screen, (255, 180, 180), (fx + 7, fy + 7), 3)

    def draw_obstacles(self):
        for ox, oy in self.obstacles:
            px = ox * CELL_SIZE
            py = oy * CELL_SIZE + 80
            draw_rounded_rect(self.screen, PURPLE, (px+1, py+1, CELL_SIZE-2, CELL_SIZE-2), radius=5)
            pygame.draw.line(self.screen, (100, 40, 160), (px+4, py+4), (px+CELL_SIZE-5, py+CELL_SIZE-5), 2)
            pygame.draw.line(self.screen, (100, 40, 160), (px+CELL_SIZE-5, py+4), (px+4, py+CELL_SIZE-5), 2)

    def draw_hud(self):
        pygame.draw.rect(self.screen, DARK, (0, 0, WINDOW_WIDTH, 80))
        pygame.draw.line(self.screen, CYAN, (0, 80), (WINDOW_WIDTH, 80), 2)

        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        mode_text = self.font_small.render(f"Mode: {self.mode.upper()}", True, CYAN)
        level_text = self.font_small.render(f"Level: {self.level}", True, GOLD)
        high_text = self.font_small.render(f"High: {self.high_score}", True, GREEN)

        self.screen.blit(score_text, (20, 20))
        self.screen.blit(mode_text, (280, 15))
        self.screen.blit(level_text, (280, 42))
        self.screen.blit(high_text, (520, 25))

    def draw_menu(self):
        self.screen.fill(BLACK)

        # Title with glow
        title = self.font_large.render("DJ COBRA", True, GREEN)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 120))
        draw_glow(self.screen, title_rect.center, GREEN, 40, intensity=4)
        self.screen.blit(title, title_rect)

        subtitle = self.font_small.render("High Graphics Edition", True, CYAN)
        self.screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_WIDTH//2, 180)))

        self.btn_play.draw(self.screen, self.font_medium)
        self.btn_modes.draw(self.screen, self.font_medium)
        self.btn_quit.draw(self.screen, self.font_medium)

        mode_info = self.font_tiny.render(f"Current Mode: {self.mode.upper()}", True, LIGHT_GRAY)
        self.screen.blit(mode_info, mode_info.get_rect(center=(WINDOW_WIDTH//2, 520)))

    def draw_mode_select(self):
        self.screen.fill(BLACK)
        title = self.font_medium.render("SELECT MODE", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH//2, 100)))

        self.btn_classic.draw(self.screen, self.font_medium)
        self.btn_speed.draw(self.screen, self.font_medium)
        self.btn_wrap.draw(self.screen, self.font_medium)
        self.btn_back.draw(self.screen, self.font_small)

        # Descriptions
        descs = [
            "Classic  -  Normal walls & speed",
            "Speed    -  Gets faster as you eat",
            "Wrap     -  Snake wraps around edges"
        ]
        for i, d in enumerate(descs):
            t = self.font_tiny.render(d, True, LIGHT_GRAY)
            self.screen.blit(t, (220, 230 + i*70))

    def draw_level_select(self):
        self.screen.fill(BLACK)
        title = self.font_medium.render("SELECT LEVEL", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH//2, 80)))

        for btn in self.level_buttons:
            btn.draw(self.screen, self.font_medium)

        self.btn_back.draw(self.screen, self.font_small)

        info = self.font_tiny.render("Higher levels = faster + more obstacles", True, LIGHT_GRAY)
        self.screen.blit(info, info.get_rect(center=(WINDOW_WIDTH//2, 560)))

    def draw_pause(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        text = self.font_large.render("PAUSED", True, CYAN)
        self.screen.blit(text, text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 40)))

        info = self.font_small.render("P / ESC = Resume     Q = Main Menu", True, WHITE)
        self.screen.blit(info, info.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 30)))

    def draw_gameover(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        text = self.font_large.render("GAME OVER", True, RED)
        self.screen.blit(text, text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 80)))

        score_t = self.font_medium.render(f"Score: {self.score}", True, GOLD)
        self.screen.blit(score_t, score_t.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 10)))

        high_t = self.font_small.render(f"High Score: {self.high_score}", True, GREEN)
        self.screen.blit(high_t, high_t.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 40)))

        info = self.font_small.render("R = Restart     M = Main Menu", True, WHITE)
        self.screen.blit(info, info.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 100)))

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "mode":
            self.draw_mode_select()
        elif self.state == "level":
            self.draw_level_select()
        elif self.state in ("playing", "pause", "gameover"):
            self.draw_background()
            self.draw_obstacles()
            self.draw_snake()
            self.draw_food()
            for p in self.particles:
                p.draw(self.screen)
            self.draw_hud()

            if self.state == "pause":
                self.draw_pause()
            elif self.state == "gameover":
                self.draw_gameover()

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

# ======================
# START
# ======================
if __name__ == "__main__":
    game = DJCobra()
    game.run()
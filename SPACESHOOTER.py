import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)

# Define colors for health and power bars
HEALTH_GREEN = (0, 255, 0)
HEALTH_RED = (255, 0, 0)
POWER_YELLOW = (255, 215, 0)
POWER_RED = (255, 0, 0)

# Player
class Player:
    def __init__(self, game):
        self.game = game
        self.width = 40
        self.height = 45
        self.x = WIDTH // 2 - self.width // 2
        self.ground_level = HEIGHT - 35
        self.y = self.ground_level - self.height
        self.speed = game.config["player_speed"]
        self.double_shoot = False
        self.double_shoot_time = 0
        self.penetrating_bullets = False
        self.penetrating_bullets_time = 0
        self.shield_active = False
        self.shield_time = 0
        self.shield_duration = game.config["shield_duration"]
        self.lives = game.config["player_lives"]
        self.health = 100
        self.power = 100
        self.power_regen_rate = 0.5 # ADJUST TO SLOW POWER REGEN (LOWER = SLOWER)
        self.shoot_cost = 20 # ADJUST TO SET ENERGY COST PER SHOT (LOWER = LESS)
        self.shoot_cooldown = 0
        self.shoot_delay = game.config["player_shoot_cooldown"]
        self.shoot_delay_full = game.config["player_shoot_cooldown"]
        self.shoot_delay_low = game.config["player_shoot_cooldown_low"]
        self.respawn_shield_time = 0
        self.respawn_shield_duration = game.respawn_shield_duration  # Use the respawn shield duration from the game config
        self.max_health = 100
        self.max_power = 100
        
    def draw(self):
        # Platform
        pygame.draw.rect(screen, WHITE, (self.x, self.y + self.height - 10, self.width, 10))
        # Main body
        body_color = YELLOW if self.penetrating_bullets else WHITE
        pygame.draw.rect(screen, body_color, (self.x + 5, self.y + 20, self.width - 10, self.height - 30))
        # Triangle top(s)
        pygame.draw.polygon(screen, body_color, [
            (self.x + self.width // 2, self.y),
            (self.x + 10, self.y + 20),
            (self.x + self.width - 10, self.y + 20)
        ])
        if self.double_shoot:
            pygame.draw.polygon(screen, body_color, [
                (self.x + 5, self.y + 10),
                (self.x + 15, self.y + 25),
                (self.x + 25, self.y + 10)
            ])
            pygame.draw.polygon(screen, body_color, [
                (self.x + self.width - 5, self.y + 10),
                (self.x + self.width - 15, self.y + 25),
                (self.x + self.width - 25, self.y + 10)
            ])
        if self.shield_active or self.respawn_shield_time > 0:
            shield_color = (0, 0, 255) if self.shield_active else (0, 255, 255)
            pygame.draw.circle(screen, shield_color, 
                               (self.x + self.width // 2, self.y + self.height // 2), 
                               max(self.width, self.height) // 2 + 5, 2)
                               
    def move(self, dx):
        self.x += dx
        self.x = max(0, min(self.x, WIDTH - self.width))

    def regenerate_health(self):
        if self.health < 100:
            self.health = min(100, self.health + 0.05)

    def regenerate_power(self):
        if self.power < self.max_power:
            self.power = min(self.max_power, self.power + self.power_regen_rate)

    def update_power_ups(self):
        if self.shield_active:
            self.shield_time -= 1
            if self.shield_time <= 0:
                self.shield_active = False

        if self.double_shoot:
            self.double_shoot_time -= 1
            if self.double_shoot_time <= 0:
                self.double_shoot = False

        if self.penetrating_bullets:
            self.penetrating_bullets_time -= 1
            if self.penetrating_bullets_time <= 0:
                self.penetrating_bullets = False

    def can_shoot(self):
        return self.power >= self.shoot_cost and self.shoot_cooldown <= 0

    def shoot(self):
        if self.can_shoot():
            self.power -= self.shoot_cost
            self.shoot_cooldown = self.shoot_delay if self.power >= self.max_power / 2 else self.shoot_delay * 1.5
            return True
        return False

    def update(self):
        if self.shield_active:
            self.shield_time -= 1
            if self.shield_time <= 0:
                self.shield_active = False

        if self.double_shoot:
            self.double_shoot_time -= 1
            if self.double_shoot_time <= 0:
                self.double_shoot = False

        if self.penetrating_bullets:
            self.penetrating_bullets_time -= 1
            if self.penetrating_bullets_time <= 0:
                self.penetrating_bullets = False

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        # Handle respawn shield time
        if self.respawn_shield_time > 0:
            self.respawn_shield_time -= 1

        self.regenerate_power()
        
    def regenerate_power(self):
        if self.power < self.max_power:
            self.power = min(self.max_power, self.power + self.power_regen_rate)
            
    def activate_shield(self):
        self.shield_active = True
        self.shield_time = self.shield_duration

    def respawn(self):
        self.x = WIDTH // 2 - self.width // 2
        self.y = self.ground_level - self.height
        self.health = self.max_health
        self.power = self.max_power
        self.respawn_shield_time = self.respawn_shield_duration
        
# Bullet
class Bullet:
    def __init__(self, x, y, penetrating=False):
        self.x = x
        self.y = y
        self.speed = 5
        self.penetrating = penetrating

    def move(self):
        self.y -= self.speed

    def draw(self):
        color = YELLOW if self.penetrating else WHITE
        pygame.draw.rect(screen, color, (self.x, self.y, 3, 10))

# Enemy
class Enemy:
    def __init__(self, x, y, wave, game):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.move_counter = 0
        self.move_delay = 40
        self.step_size = 4
        self.direction = 1
        self.shoot_cooldown = random.randint(60, 180)
        self.color = self.get_color(wave, game.enemy_colors)
        self.eye_color = self.get_eye_color(wave, game.eye_colors)
        self.base_speed = 1
        self.speed_multiplier = 1
        
    def get_color(self, wave, colors):
        color_index = (wave - 1) % len(colors)
        return colors[color_index]

    def get_eye_color(self, wave, colors):
        eye_color_index = ((wave - 1) // len(colors)) % len(colors)
        return colors[eye_color_index]

    def move(self):
        self.move_counter += self.base_speed * self.speed_multiplier
        if self.move_counter >= self.move_delay:
            self.move_counter = 0
            self.x += self.step_size * self.direction * self.speed_multiplier

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y + 10, self.width, self.height - 10))
        pygame.draw.polygon(screen, self.color, [
            (self.x, self.y + 10),
            (self.x + self.width // 2, self.y),
            (self.x + self.width, self.y + 10)
        ])
        pygame.draw.circle(screen, self.eye_color, (self.x + 7, self.y + 15), 3)
        pygame.draw.circle(screen, self.eye_color, (self.x + self.width - 7, self.y + 15), 3)

    def can_shoot(self):
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = random.randint(120, 240)  # Reset cooldown
            return True
        self.shoot_cooldown -= 1
        return False

    def shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = random.randint(120, 240)  # Random cooldown between 2-4 seconds
            return True
        self.shoot_cooldown = max(0, self.shoot_cooldown - 1)
        return False

class SpecialEnemy:
    def __init__(self, game):
        self.game = game
        self.width = 60
        self.height = 40
        self.x = -self.width
        self.y = 50
        self.speed = 2
        self.health = 30  # Increased health to make it a bit tougher
        self.shoot_cooldown = 0
        self.movement_pattern = self.generate_movement_pattern()
        self.current_move = 0

    def take_damage(self, damage):
        self.health -= damage
        return self.health <= 0
        
    def generate_movement_pattern(self):
        pattern = []
        current_pos = 0
        while current_pos < 80:
            max_target = min(80, current_pos + 50)
            min_target = max(20, current_pos + 10)
            if max_target <= min_target:
                break
            target = random.randint(min_target, max_target)
            pattern.append((target, random.randint(30, 90)))  # (target_percent, pause_frames)
            current_pos = target
        pattern.append((110, 0))  # Exit screen
        return pattern

    def move(self):
        if self.current_move >= len(self.movement_pattern):
            return False

        target_percent, pause = self.movement_pattern[self.current_move]
        target_x = (WIDTH * target_percent // 100) - self.width // 2

        if pause > 0:
            self.movement_pattern[self.current_move] = (target_percent, pause - 1)
        elif abs(self.x - target_x) > self.speed:
            self.x += self.speed if target_x > self.x else -self.speed
        else:
            self.current_move += 1

        return self.x < WIDTH + self.width

    def shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = random.randint(90, 150)  # Shoot every 1.5 to 2.5 seconds
            angle = math.atan2(self.game.player.y - self.y, self.game.player.x - self.x)
            return [EnemyBullet(self.x + self.width // 2, self.y + self.height,
                                math.cos(angle) * 3, math.sin(angle) * 3)]
        self.shoot_cooldown = max(0, self.shoot_cooldown - 1)
        return []

    def draw(self):
        pygame.draw.ellipse(screen, (150, 150, 150), (self.x, self.y + self.height // 2, self.width, self.height // 2))
        pygame.draw.arc(screen, (200, 200, 200), (self.x, self.y, self.width, self.height), math.pi, 2 * math.pi, 5)
        for i in range(3):
            x = self.x + (i + 1) * self.width // 4
            y = self.y + self.height // 2
            pygame.draw.circle(screen, (255, 255, 0), (x, y), 5)

class EnemyBullet:
    def __init__(self, x, y, dx=0, dy=2):
        self.x = x
        self.y = y
        self.speed_x = dx
        self.speed_y = dy
        self.width = 6
        self.height = 15

    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y

    def draw(self):
        pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y, self.width, self.height))

# Power-up
class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 1
        self.type = random.choice(["double_shoot", "penetrating", "shield"])

    def move(self):
        self.y += self.speed

    def draw(self):
        if self.type == "double_shoot":
            pygame.draw.polygon(screen, GREEN, [
                (self.x, self.y), (self.x + 10, self.y + 20), (self.x + 20, self.y)
            ])
        elif self.type == "penetrating":
            pygame.draw.rect(screen, YELLOW, (self.x, self.y, 20, 20))
        else:  # shield
            pygame.draw.circle(screen, BLUE, (self.x + 10, self.y + 10), 10, 2)

    def update(self):
        self.move()
        
# Explosion
class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 1
        self.max_size = 20
        self.growth_speed = 0.5

    def update(self):
        self.size += self.growth_speed

    def draw(self):
        pygame.draw.circle(screen, RED, (self.x, self.y), int(self.size), 1)

class ExtraLifePowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 2
        self.width = 20
        self.height = 20
        self.lifetime = 5 * 60  # 5 seconds at 60 FPS
        self.collected = False
        self.collection_time = 0
        self.ground_level = HEIGHT - 40  # Adjust this value as needed

    def move(self):
        if self.y < self.ground_level:
            self.y += self.speed
        else:
            self.y = self.ground_level

    def draw(self):
        if not self.collected:
            pygame.draw.rect(screen, (0, 255, 0), (self.x, self.y, self.width, self.height))
            text = game.font.render("1UP", True, (255, 255, 255))
            screen.blit(text, (self.x, self.y))
        else:
            text = game.font.render("1UP", True, (0, 255, 0))
            screen.blit(text, (self.x, self.y - self.collection_time))

    def update(self):
        if self.collected:
            self.collection_time += 1
        else:
            self.move()
            if self.y == self.ground_level:
                self.lifetime -= 1

# Game states
class GameState:
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2

# Game
class Game:
    def __init__(self):
        # Game Configuration
        self.config = {
            
            # Player settings
            "player_speed": 5,
            "player_shoot_cooldown": 15,
            "player_shoot_cooldown_low": 25,
            "player_lives": 3,

            # Enemy settings
            "enemy_step_size": 4,
            "enemy_base_speed": 2, # increase to speed up alien marching
            "enemy_move_delay": 40,
            "enemy_speed_multiplier_group": 3,
            "enemy_speed_multiplier_last": 4,
            
            # Power-up durations (in seconds)
            "shield_duration": 30,
            "double_shoot_duration": 20,
            "penetrating_duration": 10,
            
            # Game speed
            "fps": 60
        }
        
        # Convert power-up durations to frames
        for key in ["shield_duration", "double_shoot_duration", "penetrating_duration"]:
            self.config[key] *= self.config["fps"]

        # Add power_up_durations to the game configuration
        self.power_up_durations = {
            "double_shoot": self.config["double_shoot_duration"],
            "penetrating": self.config["penetrating_duration"],
            "shield": self.config["shield_duration"]
        }

        # Set respawn shield duration separately
        self.respawn_shield_duration = 5 * self.config["fps"]  # Adjust this value as needed (e.g., 10 seconds)

        self.player = Player(self)
        self.bullets = []
        self.enemies = []
        self.enemy_bullets = []
        self.powerups = []
        self.explosions = []
        self.score = 0
        self.state = GameState.MENU
        self.font = pygame.font.Font(None, 36)
        self.wave = 1
        self.enemies_speed_increased = False
        self.calculate_enemy_step_size()
        self.paused = False
        self.power_up_icons = self.create_power_up_icons()
        self.special_enemy = None
        self.special_enemy_timer = 0
        # Define enemy body and eye colors
        self.enemy_colors = [RED, GREEN, PURPLE, ORANGE, BLUE, YELLOW]
        self.eye_colors = [WHITE, YELLOW, CYAN, MAGENTA, GREEN, RED]
        
    def show_message(self, message, duration=2000):
        message_text = self.font.render(message, True, WHITE)
        screen.blit(message_text, (WIDTH // 2 - message_text.get_width() // 2, HEIGHT // 2 - message_text.get_height() // 2))
        pygame.display.flip()
        pygame.time.delay(duration)  # Delay to show the message for the specified duration

    def start_game(self):
        self.wave = 1
        self.state = GameState.PLAYING
        self.spawn_wave()

    def calculate_enemy_step_size(self):
        play_area_width = WIDTH - 60  # Subtracting 60 to give some margin
        self.enemy_step_size = play_area_width // 20

    def increase_difficulty(self):
        for enemy in self.enemies:
            enemy.base_speed *= 1.1  # Increase base speed by 10% every wave
        self.enemy_step_size *= 1.1  # Increase step size by 10% every wave

    def spawn_wave(self):
        # Clear the screen and all current objects
        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.explosions = []

        # Ensure the screen is cleared
        screen.fill(BLACK)
        pygame.display.flip()

        # Show wave number if the game is already playing
        if self.state == GameState.PLAYING:
            self.show_wave_indicator()

        enemy_width = 30
        enemy_height = 30
        group_width = 3 * enemy_width
        group_spacing = 2 * enemy_width
        start_x = (WIDTH - (3 * group_width + 2 * group_spacing)) // 2

        for group in range(3):
            for row in range(3):
                for col in range(3):
                    x = start_x + group * (group_width + group_spacing) + col * (enemy_width + 10)
                    y = 50 + row * (enemy_height + 10)
                    new_enemy = Enemy(x, y, self.wave, self)  # Pass the game object
                    self.enemies.append(new_enemy)

        self.enemies_speed_increased = False

    def show_wave_indicator(self):
        wave_text = self.font.render(f"Wave {self.wave}", True, WHITE)
        screen.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, HEIGHT // 2 - wave_text.get_height() // 2))
        pygame.display.flip()
        pygame.time.delay(2000)  # Delay to show the wave number for 2 seconds

    def handle_collisions(self):
        for bullet in self.enemy_bullets[:]:
            if (self.player.x < bullet.x < self.player.x + self.player.width and
                self.player.y < bullet.y < self.player.y + self.player.height):
                if not self.player.shield_active and self.player.respawn_shield_time <= 0:
                    self.player.health -= 35
                    self.enemy_bullets.remove(bullet)
                    if self.player.health <= 0:
                        self.player.lives -= 1
                        self.player.health = 100
                        if self.player.lives > 0:
                            self.show_message("Life Lost!")
                            self.player.respawn()
                        else:
                            self.show_message("Game Over!")
                            self.state = GameState.GAME_OVER
                else:
                    self.enemy_bullets.remove(bullet)

        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if (enemy.x < bullet.x < enemy.x + enemy.width and
                    enemy.y < bullet.y < enemy.y + enemy.height):
                    self.enemies.remove(enemy)
                    if not bullet.penetrating:
                        self.bullets.remove(bullet)
                    self.score += 10
                    self.explosions.append(Explosion(enemy.x + enemy.width // 2, enemy.y + enemy.height // 2))
                    if random.random() < 0.1:
                        self.powerups.append(PowerUp(enemy.x + enemy.width // 2, enemy.y + enemy.height // 2))
                    break

        for powerup in self.powerups[:]:
            if isinstance(powerup, PowerUp):
                if (self.player.x < powerup.x < self.player.x + self.player.width and
                    self.player.y < powerup.y < self.player.y + self.player.height):
                    if powerup.type == "double_shoot":
                        self.player.double_shoot = True
                        self.player.double_shoot_time = self.power_up_durations["double_shoot"]
                    elif powerup.type == "penetrating":
                        self.player.penetrating_bullets = True
                        self.player.penetrating_bullets_time = self.power_up_durations["penetrating"]
                    elif powerup.type == "shield":
                        self.player.activate_shield()
                    self.powerups.remove(powerup)
            elif isinstance(powerup, ExtraLifePowerUp):
                if not powerup.collected and self.player.y < powerup.y + powerup.height and \
                     self.player.x < powerup.x + powerup.width and \
                     self.player.x + self.player.width > powerup.x:
                    powerup.collected = True
                    self.player.lives += 1

        for bullet in self.enemy_bullets[:]:  # Does this block stay or get removed?!
            if (self.player.x < bullet.x < self.player.x + self.player.width and
                self.player.y < bullet.y < self.player.y + self.player.height):
                if not self.player.shield_active:
                    self.player.health -= 35
                    if self.player.health <= 0:
                        self.player.lives -= 1
                        self.player.health = 100
                        if self.player.lives <= 0:
                            self.show_message("Game Over!")
                            self.state = GameState.GAME_OVER
                        else:
                            self.show_message("Life Lost!")
                            self.player.respawn()
                self.enemy_bullets.remove(bullet)

        for enemy in self.enemies:
            if enemy.y + enemy.height >= self.player.y:
                self.show_message("Game Over!")
                self.state = GameState.GAME_OVER

        # Handle collisions with special enemy
        if self.special_enemy:
            for bullet in self.bullets[:]:
                if (self.special_enemy.x < bullet.x < self.special_enemy.x + self.special_enemy.width and
                    self.special_enemy.y < bullet.y < self.special_enemy.y + self.special_enemy.height):
                    if self.special_enemy.take_damage(10):  # One shot kill
                        self.score += 100
                        self.explosions.append(Explosion(self.special_enemy.x + self.special_enemy.width // 2,
                                                         self.special_enemy.y + self.special_enemy.height // 2))
                        self.powerups.append(ExtraLifePowerUp(self.special_enemy.x + self.special_enemy.width // 2,
                                                              self.special_enemy.y + self.special_enemy.height))
                        self.special_enemy = None
                    self.bullets.remove(bullet)
                    break

    def draw(self):
        screen.fill(BLACK)
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.player.draw()
            for bullet in self.bullets:
                bullet.draw()
            for enemy in self.enemies:
                enemy.draw()
            for bullet in self.enemy_bullets:
                bullet.draw()
            for powerup in self.powerups:
                powerup.draw()
            for explosion in self.explosions:
                explosion.draw()
            if self.special_enemy:
                self.special_enemy.draw()
            self.draw_hud()
            if self.paused:
                self.draw_pause_screen()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        pygame.display.flip()
            
    def draw_menu(self):
        title = self.font.render("Space Shooter", True, WHITE)
        start = self.font.render("Press SPACE to start", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
        screen.blit(start, (WIDTH // 2 - start.get_width() // 2, HEIGHT // 2))


    def create_power_up_icons(self):
        icon_size = 20
        icons = {}
        
        # Double shoot icon
        double_shoot_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        pygame.draw.rect(double_shoot_surf, (0, 255, 0), (0, 0, 5, 20))
        pygame.draw.rect(double_shoot_surf, (0, 255, 0), (15, 0, 5, 20))
        icons["double_shoot"] = double_shoot_surf

        # Penetrating icon
        penetrating_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        pygame.draw.rect(penetrating_surf, (255, 255, 0), (8, 0, 4, 20))
        pygame.draw.polygon(penetrating_surf, (255, 255, 0), [(0, 20), (10, 10), (20, 20)])
        icons["penetrating"] = penetrating_surf

        # Shield icon
        shield_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        pygame.draw.arc(shield_surf, (0, 191, 255), (0, 0, 20, 20), 0.5, 5.8, 2)
        icons["shield"] = shield_surf

        return icons

    def draw_hud(self):
        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        # Draw wave
        wave_text = self.font.render(f"Wave: {self.wave}", True, WHITE)
        screen.blit(wave_text, (WIDTH - wave_text.get_width() - 10, 10))

        # Draw lives
        lives_icon = pygame.Surface((20, 20))  # Create a small surface for the ship icon
        pygame.draw.rect(lives_icon, WHITE, (0, 10, 20, 10))  # Draw a simple ship shape
        pygame.draw.polygon(lives_icon, WHITE, [(0, 10), (10, 0), (20, 10)])
        lives_text = self.font.render(f"{self.player.lives} x", True, WHITE)
        screen.blit(lives_text, (WIDTH - lives_text.get_width() - 35, HEIGHT - 30))
        screen.blit(lives_icon, (WIDTH - 30, HEIGHT - 30))

        # Draw health bar
        health_bar_width = 200
        health_bar_height = 20
        health_bar_x = (WIDTH - health_bar_width) // 2
        health_bar_y = 10
        health_percentage = self.player.health / self.player.max_health
        pygame.draw.rect(screen, HEALTH_RED, (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, HEALTH_GREEN, (health_bar_x, health_bar_y, int(health_bar_width * health_percentage), health_bar_height))
        
        health_text = self.font.render("HEALTH", True, WHITE)
        screen.blit(health_text, (health_bar_x + (health_bar_width - health_text.get_width()) // 2, health_bar_y + (health_bar_height - health_text.get_height()) // 2))

        # Draw power bar
        power_bar_width = 150
        power_bar_height = 10
        power_bar_x = 10
        power_bar_y = HEIGHT - power_bar_height - 10
        power_percentage = self.player.power / self.player.max_power
        pygame.draw.rect(screen, POWER_RED, (power_bar_x, power_bar_y, power_bar_width, power_bar_height))
        power_width = int(power_bar_width * power_percentage)
        power_surface = pygame.Surface((power_width, power_bar_height))
        for x in range(power_width):
            color = pygame.Color(POWER_RED[0], POWER_RED[1], POWER_RED[2])
            color.r = int(POWER_RED[0] + (POWER_YELLOW[0] - POWER_RED[0]) * (x / power_bar_width))
            color.g = int(POWER_RED[1] + (POWER_YELLOW[1] - POWER_RED[1]) * (x / power_bar_width))
            color.b = int(POWER_RED[2] + (POWER_YELLOW[2] - POWER_RED[2]) * (x / power_bar_width))
            pygame.draw.line(power_surface, color, (x, 0), (x, power_bar_height))
        screen.blit(power_surface, (power_bar_x, power_bar_y))

        # Draw power-up icons and timers
        power_up_y = 90
        for power_up, duration in [("shield", self.player.shield_time),
                                   ("double_shoot", self.player.double_shoot_time),
                                   ("penetrating", self.player.penetrating_bullets_time)]:
            if duration > 0:
                icon = self.power_up_icons[power_up]
                timer_text = f"{duration // 60:02d}s"
                timer_surface = self.font.render(timer_text, True, WHITE)
                total_width = timer_surface.get_width() + icon.get_width() + 5
                screen.blit(timer_surface, (WIDTH - total_width - 10, power_up_y))
                screen.blit(icon, (WIDTH - icon.get_width() - 10, power_up_y))
                power_up_y += 30

    def draw_power_up_timers(self):
        if self.player.shield_active:
            shield_text = self.font.render(f"Shield: {self.player.shield_time // 60}s", True, BLUE)
            screen.blit(shield_text, (WIDTH // 2 - shield_text.get_width() // 2, 10))
        if self.player.double_shoot:
            double_shoot_text = self.font.render(f"Double Shoot: {self.player.double_shoot_time // 60}s", True, GREEN)
            screen.blit(double_shoot_text, (WIDTH // 2 - double_shoot_text.get_width() // 2, 40))
        if self.player.penetrating_bullets:
            penetrating_text = self.font.render(f"Penetrating: {self.player.penetrating_bullets_time // 60}s", True, YELLOW)
            screen.blit(penetrating_text, (WIDTH // 2 - penetrating_text.get_width() // 2, 70))

    def draw_game_over(self):
        game_over = self.font.render("Game Over", True, WHITE)
        score = self.font.render(f"Final Score: {self.score}", True, WHITE)
        restart = self.font.render("Press R to restart", True, WHITE)
        screen.blit(game_over, (WIDTH // 2 - game_over.get_width() // 2, HEIGHT // 3))
        screen.blit(score, (WIDTH // 2 - score.get_width() // 2, HEIGHT // 2))
        screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, 2 * HEIGHT // 3))

    def draw_pause_screen(self):
        pause_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pause_surface.fill((0, 0, 0, 128))
        screen.blit(pause_surface, (0, 0))
        pause_text = self.font.render("PAUSED", True, WHITE)
        screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - pause_text.get_height() // 2))

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.state == GameState.MENU:
                        self.start_game()  # Start the game at wave 1
                    elif event.key == pygame.K_r and self.state == GameState.GAME_OVER:
                        self.__init__()
                    elif event.key == pygame.K_m or event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused

            if self.state == GameState.PLAYING and not self.paused:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.player.move(-self.player.speed)
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.player.move(self.player.speed)
                if keys[pygame.K_SPACE]:
                    self.try_shoot()

                self.player.update()
                self.update_game_objects()
                self.handle_collisions()

                if not self.enemies:
                    self.wave += 1
                    self.increase_difficulty()  # Increase difficulty before spawning the next wave
                    self.spawn_wave()

            self.draw()
            clock.tick(60)

        pygame.quit()

    def increase_difficulty(self):
        for enemy in self.enemies:
            enemy.base_speed *= 1.1  # Increase base speed by 10% every 5 waves
        self.enemy_step_size *= 1.1  # Increase step size by 10% every 5 waves
        
    def try_shoot(self):
        if self.player.shoot():
            if self.player.double_shoot:
                self.bullets.append(Bullet(self.player.x + 10, self.player.y, self.player.penetrating_bullets))
                self.bullets.append(Bullet(self.player.x + self.player.width - 10, self.player.y, self.player.penetrating_bullets))
            else:
                self.bullets.append(Bullet(self.player.x + self.player.width // 2, self.player.y, self.player.penetrating_bullets))

    def update_game_objects(self):
        if self.paused:
            return
            
        # Update player
        self.player.update()
        
        # Handle player shooting
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.try_shoot()
        
        # Update player bullets
        for bullet in self.bullets[:]:
            bullet.move()
            if bullet.y < 0:
                self.bullets.remove(bullet)

        # Update enemy movement
        move_group = False
        if self.enemies:
            rightmost_x = max(enemy.x for enemy in self.enemies)
            leftmost_x = min(enemy.x for enemy in self.enemies)
            lowest_y = max(enemy.y for enemy in self.enemies)
            
            # Check if enemies should speed up
            if len(self.enemies) == 1 and not self.enemies_speed_increased:
                self.enemies[0].speed_multiplier = self.config["enemy_speed_multiplier_last"]
                self.enemies_speed_increased = True
            elif lowest_y >= HEIGHT - 4 * self.enemies[0].height and not self.enemies_speed_increased:
                for enemy in self.enemies:
                    enemy.speed_multiplier = self.config["enemy_speed_multiplier_group"]
                self.enemies_speed_increased = True
            
            if (rightmost_x + self.enemies[0].width >= WIDTH and self.enemies[0].direction == 1) or \
               (leftmost_x <= 0 and self.enemies[0].direction == -1):
                move_group = True
            
            if move_group:
                for enemy in self.enemies:
                    enemy.direction *= -1
                    enemy.y += enemy.height
                    enemy.move_counter = 0
            else:
                for enemy in self.enemies:
                    enemy.move()

            # Check if enemies reach the player
            if lowest_y + self.enemies[0].height >= self.player.y - self.enemies[0].height:  # Allow one more row
                self.player.lives -= 1
                self.reset_wave()
                if self.player.lives <= 0:
                    self.state = GameState.GAME_OVER
        else:
            # Handle the case when there are no enemies
            self.wave += 1
            self.spawn_wave()

        # Update enemy bullets
        for enemy in self.enemies:
            if enemy.can_shoot() and len(self.enemy_bullets) < 3:
                new_bullet = EnemyBullet(enemy.x + enemy.width // 2, enemy.y + enemy.height)
                self.enemy_bullets.append(new_bullet)

        # Update special enemy
        if self.special_enemy:
            if not self.special_enemy.move():
                self.special_enemy = None
            else:
                bullets = self.special_enemy.shoot()
                self.enemy_bullets.extend(bullets)
        else:
            self.special_enemy_timer += 1
            if self.special_enemy_timer >= 600:  # Spawn every 10 seconds
                self.special_enemy = SpecialEnemy(self)
                self.special_enemy_timer = 0

        # Move enemy bullets
        for bullet in self.enemy_bullets[:]:
            bullet.move()
            if bullet.y > HEIGHT:
                self.enemy_bullets.remove(bullet)

        # Update powerups
        for powerup in self.powerups[:]:
            powerup.update()
            if isinstance(powerup, ExtraLifePowerUp):
                if powerup.lifetime <= 0 or powerup.collection_time > 60:
                    self.powerups.remove(powerup)
                elif not powerup.collected and self.player.y < powerup.y + powerup.height and \
                     self.player.x < powerup.x + powerup.width and \
                     self.player.x + self.player.width > powerup.x:
                    powerup.collected = True
                    self.player.lives += 1
            else:
                if powerup.y > HEIGHT:
                    self.powerups.remove(powerup)

        # Update explosions
        for explosion in self.explosions[:]:
            explosion.update()
            if explosion.size > explosion.max_size:
                self.explosions.remove(explosion)

    def reset_wave(self):
        self.player.respawn()
        self.enemies.clear()
        self.enemy_bullets.clear()
        self.bullets.clear()
        self.powerups.clear()
        self.enemies_speed_increased = False
        self.spawn_wave()
        print(f"Wave {self.wave} reset. Enemy speeds reset to normal.")
        
    def increase_difficulty(self):
        for enemy in self.enemies:
            enemy.base_speed *= 1.1  # Increase base speed by 10% every 5 waves
        self.enemy_step_size *= 1.1  # Increase step size by 10% every 5 waves

if __name__ == "__main__":
    game = Game()
    game.run()
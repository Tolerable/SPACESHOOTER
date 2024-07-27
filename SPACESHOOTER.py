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
        self.power_regen_rate = 0.5  # ADJUST TO SLOW POWER REGEN (LOWER = SLOWER)
        self.shoot_cost = 20  # ADJUST TO SET ENERGY COST PER SHOT (LOWER = LESS)
        self.shoot_cooldown = 0
        self.shoot_delay = game.config["player_shoot_cooldown"]
        self.shoot_delay_full = game.config["player_shoot_cooldown"]
        self.shoot_delay_low = game.config["player_shoot_cooldown_low"]
        self.respawn_shield_time = 0
        self.respawn_shield_duration = game.respawn_shield_duration  # Use the respawn shield duration from the game config
        self.max_health = 100
        self.max_power = 100
        self.god_mode = False  # Add god_mode attribute

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
        if self.shield_active or self.respawn_shield_time > 0 or self.god_mode:
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
        if self.god_mode:
            self.shield_time = float('inf')  # Infinite shield time for god mode

    def deactivate_shield(self):
        self.shield_active = False
        self.shield_time = 0

    def respawn(self):
        self.x = WIDTH // 2 - self.width // 2
        self.y = self.ground_level - self.height
        self.health = self.max_health
        self.power = self.max_power
        self.respawn_shield_time = self.respawn_shield_duration

    def take_damage(self, amount):
        if not self.shield_active and self.respawn_shield_time <= 0:
            self.health -= amount
            if self.health <= 0:
                self.lives -= 1
                self.health = self.max_health
                if self.lives > 0:
                    self.respawn()
                else:
                    return True  # Game over
        return False

    def collides_with(self, other):
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)

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
        if random.random() < 0.2:  # Adjust the probability as needed
            return EnemyBullet(self.x + self.width // 2, self.y + self.height)
        return None

class SpecialEnemy:
    def __init__(self, game):
        self.game = game
        self.width = 60
        self.height = 40
        self.x = -self.width
        self.y = 50
        self.speed = 2
        self.health = 30
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

class Boss:
    def __init__(self, x, y, health, game):
        self.x = x
        self.y = y
        self.health = health
        self.game = game
        self.parts = [
            {"x": x - 20, "y": y, "hit_points": 3},
            {"x": x, "y": y, "hit_points": 3},
            {"x": x + 20, "y": y, "hit_points": 3},
            # Add more parts as needed
        ]
        self.core_exposed = False
        self.core_health = 10
        self.direction = 1

    def move(self):
        self.x += self.direction * 2  # Boss moves left and right
        if self.x < 0 or self.x > WIDTH:
            self.direction *= -1

    def attack(self):
        # Logic for shooting lasers or using tentacles
        if random.random() < 0.05:  # 5% chance to shoot
            return EnemyBullet(self.x, self.y + 10)
        return None

    def take_damage(self, part_index):
        self.parts[part_index]["hit_points"] -= 1
        if all(part["hit_points"] <= 0 for part in self.parts):
            self.core_exposed = True

    def take_core_damage(self):
        if self.core_exposed:
            self.core_health -= 1
            if self.core_health <= 0:
                self.die()

    def die(self):
        # Logic for boss defeat
        self.game.score += 500
        self.game.boss = None

    def draw(self):
        # Draw the boss and its parts
        for part in self.parts:
            color = RED if part["hit_points"] > 0 else BLACK
            pygame.draw.rect(screen, color, (part["x"], part["y"], 20, 20))
        if self.core_exposed:
            pygame.draw.circle(screen, YELLOW, (self.x, self.y), 10)

class BonusWave:
    def __init__(self, game):
        self.game = game
        self.enemies = self.create_bonus_wave_enemies()
        self.launch_cooldown = 120  # Time between launches
        self.launch_timer = self.launch_cooldown
        self.detached_enemies = []
        self.flock_bullets = []  # New list for flock enemy bullets

    def create_bonus_wave_enemies(self):
        enemies = []
        formation = [
            (0, 0), (1, 0), (0.5, 1),
            (-1, 1), (1.5, 1), (-0.5, 2), (2, 2)
        ]
        for flock in range(2):
            for (dx, dy) in formation:
                x = WIDTH // 4 * (flock + 1) + dx * 40
                y = 50 + dy * 40
                enemy = FlyingFlockEnemy(x, y, self.game.wave, self.game)
                enemies.append(enemy)
        return enemies

    def update(self):
        self.launch_timer -= 1
        if self.launch_timer <= 0 and len(self.detached_enemies) < 3:
            self.launch_timer = self.launch_cooldown
            self.launch_enemy()

        for enemy in self.enemies[:]:
            enemy.update()

        for enemy in self.detached_enemies[:]:
            enemy.update()
            if not enemy.flying_down:
                self.detached_enemies.remove(enemy)
                self.enemies.append(enemy)
                
        for enemy in self.enemies + self.detached_enemies:
            bullet = enemy.shoot()
            if bullet:
                self.flock_bullets.append(bullet)

        for bullet in self.flock_bullets[:]:
            bullet.move()
            if (bullet.x < 0 or bullet.x > WIDTH or
                bullet.y < 0 or bullet.y > HEIGHT):
                self.flock_bullets.remove(bullet)

    def launch_enemy(self):
        if self.enemies:
            launching_enemy = random.choice(self.enemies)
            launching_enemy.detach()
            self.enemies.remove(launching_enemy)
            self.detached_enemies.append(launching_enemy)

    def draw(self):
        for enemy in self.enemies + self.detached_enemies:
            enemy.draw()

        for bullet in self.flock_bullets:
            bullet.draw()

    def handle_collisions(self):
        for bullet in self.game.bullets[:]:
            for enemy in self.enemies + self.detached_enemies:
                if enemy.collides_with(bullet):
                    self.game.bullets.remove(bullet)
                    if enemy.take_damage(1):  # Changed from 1 to 2
                        if enemy in self.enemies:
                            self.enemies.remove(enemy)
                        else:
                            self.detached_enemies.remove(enemy)
                        self.game.score += 10
                    break
                    
        for bullet in self.flock_bullets[:]:
            if self.game.player.collides_with(bullet):
                self.game.player.take_damage(35)  # Use the same damage as in other waves
                self.flock_bullets.remove(bullet)
                
        # Add collision check for player and enemies
        for enemy in self.detached_enemies:
            if self.game.player.collides_with(enemy):
                self.game.player.take_damage(35)  # Use the same damage as in other waves
                enemy.reset_position()  # Reset enemy position after collision
                    
    def is_complete(self):
        return not (self.enemies or self.detached_enemies)

class BonusEnemy:
    def __init__(self, x, y, game):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.color = YELLOW
        self.game = game
        self.is_detached = False
        self.detached_move_counter = 0

    def move(self):
        if not self.is_detached:
            self.y += 0.5 * math.sin(pygame.time.get_ticks() / 1000.0)

    def update_detached(self):
        if self.is_detached:
            self.detached_move_counter += 1
            self.x += 5 * math.cos(self.detached_move_counter / 20.0)
            self.y += 5 * math.sin(self.detached_move_counter / 20.0)

            if self.detached_move_counter > 100:
                self.is_detached = False
                self.detached_move_counter = 0

    def draw(self):
        pygame.draw.rect(self.game.screen, self.color, (self.x, self.y, self.width, self.height))

    def special_attack(self):
        pass

class FlyingFlockEnemy(Enemy):
    def __init__(self, x, y, wave, game):
        super().__init__(x, y, wave, game)
        self.base_x = x
        self.base_y = y
        self.flying_down = False
        self.bomb_cooldown = random.randint(60, 180)
        self.health = 2
        self.game = game

    def shoot(self):
        if self.bomb_cooldown <= 0:
            self.bomb_cooldown = random.randint(240, 480)  # Reset cooldown
            angle = math.atan2(self.game.player.y - self.y, self.game.player.x - self.x)
            angle += random.uniform(-0.2, 0.2)  # Add some randomness to the angle
            speed = random.uniform(3, 5)  # Randomize bullet speed
            return FlockEnemyBullet(self.x + self.width // 2, self.y + self.height,
                                    math.cos(angle) * speed, math.sin(angle) * speed)
        self.bomb_cooldown -= 1
        return None
        
    def collides_with(self, bullet):
        return self.x < bullet.x < self.x + self.width and self.y < bullet.y < self.y + self.height

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.game.explosions.append(Explosion(self.x + self.width // 2, self.y + self.height // 2))
            return True  # Indicates the enemy is destroyed
        return False  # Indicates the enemy is still alive

    def reset_position(self):
        self.x = self.base_x
        self.y = self.base_y
        self.flying_down = False

    def move_as_group(self):
        self.x += self.direction * self.base_speed
        if self.x < 0 or self.x + self.width > WIDTH:
            self.direction *= -1

    def move_detached(self):
        if self.flying_down:
            self.y += self.base_speed * 2
            if self.y > HEIGHT:
                self.reset_position()
                self.flying_down = False

    def update(self):
        if not self.flying_down:
            self.move_as_group()
        else:
            self.move_detached()

    def detach(self):
        self.flying_down = True

    def draw(self):
        super().draw()
        if self.flying_down:
            bullet = self.shoot()
            if bullet:
                self.game.enemy_bullets.append(bullet)

class FlockEnemyBullet:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.width = 6
        self.height = 6

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self):
        pygame.draw.rect(screen, (255, 0, 0), (int(self.x), int(self.y), self.width, self.height))

# Game states
class GameState:
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2

# Game
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.god_mode = False
        self.font = pygame.font.Font(None, 36)
        self.enemy_shoot_frequency = 0.02  # Base frequency for enemy shooting

        # Game Configuration
        self.config = {
            # Player settings
            "player_speed": 5,
            "player_shoot_cooldown": 15,
            "player_shoot_cooldown_low": 25,
            "player_lives": 3,
            # Enemy settings
            "enemy_step_size": 4,
            "enemy_base_speed": 2,  # increase to speed up alien marching
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
        self.wave = 1
        self.enemies_speed_increased = False
        self.calculate_enemy_step_size()
        self.paused = False
        self.power_up_icons = self.create_power_up_icons()
        self.special_enemy = None
        self.special_enemy_timer = 0
        self.enemy_colors = [RED, GREEN, PURPLE, ORANGE, BLUE, YELLOW]
        self.eye_colors = [WHITE, YELLOW, CYAN, MAGENTA, GREEN, RED]
        self.boss = None
        self.bonus_wave = None

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
                    elif event.key == pygame.K_g:
                        self.toggle_god_mode()
                    elif event.key in range(pygame.K_0, pygame.K_9 + 1):
                        self.jump_to_wave(event.key - pygame.K_0)  # Correct method name

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

                if not self.enemies and (not hasattr(self, 'bonus_wave') or self.bonus_wave is None or self.bonus_wave.is_complete()):
                    self.wave += 1
                    self.increase_difficulty()  # Increase difficulty before spawning the next wave
                    if self.wave % 5 == 0:
                        self.spawn_bonus_wave()
                    else:
                        self.spawn_wave()

            self.draw()
            clock.tick(60)

        pygame.quit()

    def toggle_god_mode(self):
        self.god_mode = not self.god_mode
        if self.god_mode:
            self.player.shield_active = True  # Activate shield
            self.player.shield_time = float('inf')  # Make shield last indefinitely
            self.show_message("GOD MODE ACTIVATED", 1000)
        else:
            self.player.shield_active = False  # Deactivate shield
            self.player.shield_time = 0  # Remove shield time
            self.show_message("GOD MODE DEACTIVATED", 1000)

    def jump_to_wave(self, wave):
        self.wave = wave
        self.reset_wave()
        if self.wave % 5 == 0:
            self.spawn_bonus_wave()
        else:
            self.spawn_wave()
        self.show_wave_indicator()
        self.player.shield_active = False
        self.player.shield_time = 0
        self.player.respawn_shield_time = 0
        self.player.x = WIDTH // 2 - self.player.width // 2
        self.player.y = self.player.ground_level - self.player.height
        self.player.health = self.player.max_health

    def show_message(self, message, duration=2000):
        message_text = self.font.render(message, True, WHITE)
        self.screen.blit(message_text, (WIDTH // 2 - message_text.get_width() // 2, HEIGHT // 2 - message_text.get_height() // 2))
        pygame.display.flip()
        pygame.time.delay(duration)

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
        self.clear_wave()
        self.screen.fill(BLACK)
        pygame.display.flip()

        if self.state == GameState.PLAYING:
            self.show_wave_indicator()

        if self.wave % 10 == 0:
            self.spawn_boss_wave()
        elif self.wave % 5 == 0:
            self.spawn_bonus_wave()
        else:
            self.spawn_regular_wave()

        self.enemies_speed_increased = False
        self.state = GameState.PLAYING

    def clear_wave(self):
        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.explosions = []

    def spawn_regular_wave(self):
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
                    new_enemy = Enemy(x, y, self.wave, self)
                    self.enemies.append(new_enemy)

    def spawn_bonus_wave(self):
        self.bonus_wave = BonusWave(self)

    def spawn_boss_wave(self):
        self.clear_wave()
        self.screen.fill(BLACK)
        pygame.display.flip()

        if self.state == GameState.PLAYING:
            self.show_wave_indicator()

        # Spawning boss enemy
        self.boss = Boss(WIDTH // 2, 50, 100, self)
        self.enemies.append(self.boss)

        self.enemies_speed_increased = False
        self.state = GameState.PLAYING
        
    def show_wave_indicator(self):
        wave_text = self.font.render(f"Wave {self.wave}", True, WHITE)
        self.screen.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, HEIGHT // 2 - wave_text.get_height() // 2))
        pygame.display.flip()
        pygame.time.delay(2000)

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
                     self.player.x < powerup.x + self.player.width and \
                     self.player.x + self.player.width > powerup.x:
                    powerup.collected = True
                    self.player.lives += 1

        for enemy in self.enemies:
            if enemy.y + enemy.height >= self.player.y:
                self.show_message("Game Over!")
                self.state = GameState.GAME_OVER

        if self.special_enemy:
            for bullet in self.bullets[:]:
                if (self.special_enemy.x < bullet.x < self.special_enemy.x + self.special_enemy.width and
                    self.special_enemy.y < bullet.y < self.special_enemy.y + self.special_enemy.height):
                    if self.special_enemy.take_damage(10):
                        self.score += 100
                        self.explosions.append(Explosion(self.special_enemy.x + self.special_enemy.width // 2,
                                                         self.special_enemy.y + self.special_enemy.height // 2))
                        self.powerups.append(ExtraLifePowerUp(self.special_enemy.x + self.special_enemy.width // 2,
                                                              self.special_enemy.y + self.special_enemy.height))
                        self.special_enemy = None
                    self.bullets.remove(bullet)
                    break

    def draw(self):
        self.screen.fill(BLACK)
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
            if hasattr(self, 'bonus_wave') and self.bonus_wave:
                self.bonus_wave.draw()
            self.draw_hud()
            if self.paused:
                self.draw_pause_screen()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        pygame.display.flip()

    def draw_menu(self):
        title = self.font.render("Space Shooter", True, WHITE)
        start = self.font.render("Press SPACE to start", True, WHITE)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
        self.screen.blit(start, (WIDTH // 2 - start.get_width() // 2, HEIGHT // 2))

    def create_power_up_icons(self):
        icon_size = 20
        icons = {}

        double_shoot_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        pygame.draw.rect(double_shoot_surf, (0, 255, 0), (0, 0, 5, 20))
        pygame.draw.rect(double_shoot_surf, (0, 255, 0), (15, 0, 5, 20))
        icons["double_shoot"] = double_shoot_surf

        penetrating_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        pygame.draw.rect(penetrating_surf, (255, 255, 0), (8, 0, 4, 20))
        pygame.draw.polygon(penetrating_surf, (255, 255, 0), [(0, 20), (10, 10), (20, 20)])
        icons["penetrating"] = penetrating_surf

        shield_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        pygame.draw.arc(shield_surf, (0, 191, 255), (0, 0, 20, 20), 0.5, 5.8, 2)
        icons["shield"] = shield_surf

        return icons

    def draw_hud(self):
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        wave_text = self.font.render(f"Wave: {self.wave}", True, WHITE)
        self.screen.blit(wave_text, (WIDTH - wave_text.get_width() - 10, 10))

        lives_icon = pygame.Surface((20, 20))
        pygame.draw.rect(lives_icon, WHITE, (0, 10, 20, 10))
        pygame.draw.polygon(lives_icon, WHITE, [(0, 10), (10, 0), (20, 10)])
        lives_text = self.font.render(f"{self.player.lives} x", True, WHITE)
        self.screen.blit(lives_text, (WIDTH - lives_text.get_width() - 35, HEIGHT - 30))
        self.screen.blit(lives_icon, (WIDTH - 30, HEIGHT - 30))

        health_bar_width = 200
        health_bar_height = 20
        health_bar_x = (WIDTH - health_bar_width) // 2
        health_bar_y = 10
        health_percentage = self.player.health / self.player.max_health
        pygame.draw.rect(self.screen, HEALTH_RED, (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        pygame.draw.rect(self.screen, HEALTH_GREEN, (health_bar_x, health_bar_y, int(health_bar_width * health_percentage), health_bar_height))

        health_text = self.font.render("HEALTH", True, WHITE)
        self.screen.blit(health_text, (health_bar_x + (health_bar_width - health_text.get_width()) // 2, health_bar_y + (health_bar_height - health_text.get_height()) // 2))

        power_bar_width = 150
        power_bar_height = 10
        power_bar_x = 10
        power_bar_y = HEIGHT - power_bar_height - 10
        power_percentage = self.player.power / self.player.max_power
        pygame.draw.rect(self.screen, POWER_RED, (power_bar_x, power_bar_y, power_bar_width, power_bar_height))
        power_width = int(power_bar_width * power_percentage)
        power_surface = pygame.Surface((power_width, power_bar_height))
        for x in range(power_width):
            color = pygame.Color(POWER_RED[0], POWER_RED[1], POWER_RED[2])
            color.r = int(POWER_RED[0] + (POWER_YELLOW[0] - POWER_RED[0]) * (x / power_bar_width))
            color.g = int(POWER_RED[1] + (POWER_YELLOW[1] - POWER_RED[1]) * (x / power_bar_width))
            color.b = int(POWER_RED[2] + (POWER_YELLOW[2] - POWER_RED[2]) * (x / power_bar_width))
            pygame.draw.line(power_surface, color, (x, 0), (x, power_bar_height))
        self.screen.blit(power_surface, (power_bar_x, power_bar_y))

        power_up_y = 90
        for power_up, duration in [("shield", self.player.shield_time),
                                   ("double_shoot", self.player.double_shoot_time),
                                   ("penetrating", self.player.penetrating_bullets_time)]:
            if duration > 0 and not math.isnan(duration):
                icon = self.power_up_icons[power_up]
                try:
                    timer_text = f"{int(duration // 60):02d}s"
                except ValueError:
                    timer_text = "00s"
                timer_surface = self.font.render(timer_text, True, WHITE)
                total_width = timer_surface.get_width() + icon.get_width() + 5
                self.screen.blit(timer_surface, (WIDTH - total_width - 10, power_up_y))
                self.screen.blit(icon, (WIDTH - icon.get_width() - 10, power_up_y))
                power_up_y += 30

    def draw_power_up_timers(self):
        if self.player.shield_active:
            shield_text = self.font.render(f"Shield: {self.player.shield_time // 60}s", True, BLUE)
            self.screen.blit(shield_text, (WIDTH // 2 - shield_text.get_width() // 2, 10))
        if self.player.double_shoot:
            double_shoot_text = self.font.render(f"Double Shoot: {self.player.double_shoot_time // 60}s", True, GREEN)
            self.screen.blit(double_shoot_text, (WIDTH // 2 - double_shoot_text.get_width() // 2, 40))
        if self.player.penetrating_bullets:
            penetrating_text = self.font.render(f"Penetrating: {self.player.penetrating_bullets_time // 60}s", True, YELLOW)
            self.screen.blit(penetrating_text, (WIDTH // 2 - penetrating_text.get_width() // 2, 70))

    def draw_game_over(self):
        game_over = self.font.render("Game Over", True, WHITE)
        score = self.font.render(f"Final Score: {self.score}", True, WHITE)
        restart = self.font.render("Press R to restart", True, WHITE)
        self.screen.blit(game_over, (WIDTH // 2 - game_over.get_width() // 2, HEIGHT // 3))
        self.screen.blit(score, (WIDTH // 2 - score.get_width() // 2, HEIGHT // 2))
        self.screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, 2 * HEIGHT // 3))

    def draw_pause_screen(self):
        pause_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pause_surface.fill((0, 0, 0, 128))
        self.screen.blit(pause_surface, (0, 0))
        pause_text = self.font.render("PAUSED", True, WHITE)
        self.screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - pause_text.get_height() // 2))

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

        self.player.update()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.try_shoot()

        for bullet in self.bullets[:]:
            bullet.move()
            if bullet.y < 0:
                self.bullets.remove(bullet)

        move_group = False
        if self.enemies:
            rightmost_x = max(enemy.x for enemy in self.enemies)
            leftmost_x = min(enemy.x for enemy in self.enemies)
            lowest_y = max(enemy.y for enemy in self.enemies)

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

            if lowest_y + self.enemies[0].height >= self.player.y - self.enemies[0].height:
                self.player.lives -= 1
                self.reset_wave()
                if self.player.lives <= 0:
                    self.state = GameState.GAME_OVER
        else:
            if not hasattr(self, 'bonus_wave') or self.bonus_wave is None or self.bonus_wave.is_complete():
                self.wave += 1
                if self.wave % 5 == 0:
                    self.spawn_bonus_wave()
                else:
                    self.spawn_wave()

        for enemy in self.enemies:
            if enemy.can_shoot() and len(self.enemy_bullets) < 3:
                new_bullet = enemy.shoot()
                if new_bullet:
                    self.enemy_bullets.append(new_bullet)
            if isinstance(enemy, FlyingFlockEnemy):
                special_bullet = enemy.special_attack()
                if special_bullet:
                    self.enemy_bullets.append(special_bullet)

        if self.wave % 5 != 0:
            if self.special_enemy:
                if not self.special_enemy.move():
                    self.special_enemy = None
                else:
                    bullets = self.special_enemy.shoot()
                    self.enemy_bullets.extend(bullets)
            else:
                self.special_enemy_timer += 1
                if self.special_enemy_timer >= 900:
                    self.special_enemy = SpecialEnemy(self)
                    self.special_enemy_timer = 0

        for bullet in self.enemy_bullets[:]:
            bullet.move()
            if bullet.y > HEIGHT:
                self.enemy_bullets.remove(bullet)

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

        for explosion in self.explosions[:]:
            explosion.update()
            if explosion.size > explosion.max_size:
                self.explosions.remove(explosion)

        if hasattr(self, 'bonus_wave') and self.bonus_wave:
            self.bonus_wave.update()
            self.bonus_wave.handle_collisions()  # Ensure handle_collisions is called

    def start_game(self):
        self.wave = 1
        self.state = GameState.PLAYING
        self.spawn_wave()

    def reset_wave(self):
        self.player.respawn()
        self.enemies.clear()
        self.enemy_bullets.clear()
        self.bullets.clear()
        self.powerups.clear()
        self.enemies_speed_increased = False
        self.spawn_wave()
        print(f"Wave {self.wave} reset. Enemy speeds reset to normal.")

if __name__ == "__main__":
    game = Game()
    game.run()


import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 50)
BROWN = (139, 69, 19)
SKIN = (255, 220, 177)
ORANGE = (255, 165, 0)

# Create display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hero's Mission - FPS")
clock = pygame.time.Clock()

# Game states
MISSION = "mission"
DEATH = "death"
TIMESKIP = "timeskip"
ENDING = "ending"

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.speed = 4
        self.health = 100
        self.max_health = 100
        self.weapon = "gun"  # "gun" or "knife"
        self.shoot_cooldown = 0
        self.camera_distance = 150
        self.camera_height = 80
        
    def move(self, keys, walls, enemies):
        old_x, old_y = self.x, self.y
        
        # Strafe movement (fixed directions)
        if keys[pygame.K_w]:  # Forward
            self.y -= self.speed
        if keys[pygame.K_s]:  # Backward
            self.y += self.speed
        if keys[pygame.K_a]:  # Left
            self.x -= self.speed
        if keys[pygame.K_d]:  # Right
            self.x += self.speed
            
        # Check wall collision
        for wall in walls:
            if self.check_collision(wall):
                self.x, self.y = old_x, old_y
                break
                
        self.shoot_cooldown = max(0, self.shoot_cooldown - 1)
                
    def check_collision(self, rect):
        player_rect = pygame.Rect(self.x - 15, self.y - 15, 30, 30)
        return player_rect.colliderect(rect)
        
    def rotate(self, mouse_dx):
        self.angle += mouse_dx * 0.003
        
    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0
            
    def switch_weapon(self):
        if self.weapon == "gun":
            self.weapon = "knife"
        else:
            self.weapon = "gun"
            
    def can_shoot(self):
        return self.shoot_cooldown == 0

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 60
        self.max_health = 60
        self.speed = 1.2
        self.shoot_timer = 0
        self.shoot_cooldown = 90
        
    def update(self, player_x, player_y, walls):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 200:
            old_x, old_y = self.x, self.y
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
            
            # Check wall collision for enemies
            enemy_rect = pygame.Rect(self.x - 15, self.y - 15, 30, 30)
            for wall in walls:
                if enemy_rect.colliderect(wall):
                    self.x, self.y = old_x, old_y
                    break
            
        self.shoot_timer += 1
        
    def get_angle_to_player(self, player_x, player_y):
        return math.atan2(player_y - self.y, player_x - self.x)

class Hostage:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.saved = False

class Bullet:
    def __init__(self, x, y, angle, friendly=True):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 12
        self.friendly = friendly
        self.active = True
        
    def update(self, walls):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        
        # Check wall collision
        bullet_rect = pygame.Rect(self.x - 3, self.y - 3, 6, 6)
        for wall in walls:
            if bullet_rect.colliderect(wall):
                self.active = False
                return
        
    def is_off_map(self):
        return self.x < -100 or self.x > 900 or self.y < -100 or self.y > 700

class Game:
    def __init__(self):
        self.state = MISSION
        self.player = Player(100, 300)
        self.enemies = [
            Enemy(600, 200),
            Enemy(700, 400),
            Enemy(650, 150),
            Enemy(500, 480),
            Enemy(550, 300)
        ]
        self.hostages = [
            Hostage(680, 300),
            Hostage(720, 320),
            Hostage(650, 280)
        ]
        self.bullets = []
        self.walls = [
            pygame.Rect(250, 150, 20, 300),
            pygame.Rect(400, 200, 150, 20),
            pygame.Rect(550, 350, 20, 150),
            pygame.Rect(200, 450, 200, 20)
        ]
        self.hostages_saved = 0
        self.timeskip_timer = 0
        self.ending_timer = 0
        self.death_timer = 0
        self.head_turn_angle = 0
        self.slow_motion = False
        self.slow_motion_timer = 0
        
    def handle_mission(self, keys, mouse_dx, mouse_click):
        # Player movement and rotation
        self.player.move(keys, self.walls, self.enemies)
        self.player.rotate(mouse_dx)
        
        # Check if player died
        if self.player.health <= 0:
            self.state = DEATH
            return
        
        # Weapon switching with Q
        if keys[pygame.K_q]:
            if not hasattr(self, 'weapon_switch_cooldown'):
                self.weapon_switch_cooldown = 0
            if self.weapon_switch_cooldown == 0:
                self.player.switch_weapon()
                self.weapon_switch_cooldown = 20
        
        if hasattr(self, 'weapon_switch_cooldown'):
            self.weapon_switch_cooldown = max(0, self.weapon_switch_cooldown - 1)
        
        # Shooting or melee
        if mouse_click and self.player.can_shoot():
            if self.player.weapon == "gun":
                # Calculate muzzle position (in front of player)
                muzzle_offset = 25
                muzzle_x = self.player.x + math.cos(self.player.angle) * muzzle_offset
                muzzle_y = self.player.y + math.sin(self.player.angle) * muzzle_offset
                
                bullet = Bullet(muzzle_x, muzzle_y, self.player.angle)
                self.bullets.append(bullet)
                self.player.shoot_cooldown = 15
                
                # Activate slow motion briefly
                self.slow_motion = True
                self.slow_motion_timer = 20
            else:  # knife
                # Melee attack - check enemies in front
                for enemy in self.enemies[:]:
                    dx = enemy.x - self.player.x
                    dy = enemy.y - self.player.y
                    dist = math.sqrt(dx**2 + dy**2)
                    angle_to_enemy = math.atan2(dy, dx)
                    angle_diff = abs(angle_to_enemy - self.player.angle)
                    
                    # Normalize angle difference
                    while angle_diff > math.pi:
                        angle_diff -= 2 * math.pi
                    angle_diff = abs(angle_diff)
                    
                    if dist < 60 and angle_diff < 0.5:  # Close and in front
                        enemy.health -= 50
                        if enemy.health <= 0:
                            self.enemies.remove(enemy)
                        self.player.shoot_cooldown = 30
                        break
        
        # Update slow motion
        if self.slow_motion:
            self.slow_motion_timer -= 1
            if self.slow_motion_timer <= 0:
                self.slow_motion = False
        
        # Bullet speed modifier based on slow motion
        bullet_updates = 1 if not self.slow_motion else 1
        
        # Update bullets
        for _ in range(bullet_updates):
            for bullet in self.bullets[:]:
                if not bullet.active:
                    self.bullets.remove(bullet)
                    continue
                    
                bullet.update(self.walls)
                
                if bullet.is_off_map():
                    self.bullets.remove(bullet)
                    continue
                    
                # Check bullet collisions
                if bullet.friendly:
                    for enemy in self.enemies[:]:
                        dist = math.sqrt((bullet.x - enemy.x)**2 + (bullet.y - enemy.y)**2)
                        if dist < 20:
                            enemy.health -= 30
                            if bullet in self.bullets:
                                self.bullets.remove(bullet)
                            if enemy.health <= 0:
                                self.enemies.remove(enemy)
                            break
                else:
                    dist = math.sqrt((bullet.x - self.player.x)**2 + (bullet.y - self.player.y)**2)
                    if dist < 20:
                        self.player.take_damage(15)
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        
        # Update enemies
        for enemy in self.enemies:
            enemy.update(self.player.x, self.player.y, self.walls)
            
            # Enemy shooting - check line of sight
            if enemy.shoot_timer > enemy.shoot_cooldown:
                if self.has_line_of_sight(enemy.x, enemy.y, self.player.x, self.player.y):
                    angle = enemy.get_angle_to_player(self.player.x, self.player.y)
                    angle += random.uniform(-0.15, 0.15)
                    self.bullets.append(Bullet(enemy.x, enemy.y, angle, friendly=False))
                    enemy.shoot_timer = 0
                    
        # Check hostage rescue
        for hostage in self.hostages:
            if not hostage.saved:
                dist = math.sqrt((self.player.x - hostage.x)**2 + (self.player.y - hostage.y)**2)
                if dist < 50 and len(self.enemies) == 0:
                    hostage.saved = True
                    self.hostages_saved += 1
                    
        # Check mission complete
        if self.hostages_saved >= len(self.hostages):
            self.state = TIMESKIP
    
    def has_line_of_sight(self, x1, y1, x2, y2):
        """Check if there's a clear line between two points"""
        steps = 20
        for i in range(steps):
            t = i / steps
            check_x = x1 + (x2 - x1) * t
            check_y = y1 + (y2 - y1) * t
            
            check_rect = pygame.Rect(check_x - 2, check_y - 2, 4, 4)
            for wall in self.walls:
                if check_rect.colliderect(wall):
                    return False
        return True
            
    def draw_human(self, screen, x, y, scale, color, facing_angle=0):
        """Draw a simple human figure"""
        # Head
        pygame.draw.circle(screen, SKIN, (int(x), int(y - 15 * scale)), int(8 * scale))
        
        # Body
        pygame.draw.rect(screen, color, 
                        (int(x - 6 * scale), int(y - 7 * scale), 
                         int(12 * scale), int(20 * scale)))
        
        # Arms
        pygame.draw.rect(screen, SKIN, 
                        (int(x - 12 * scale), int(y - 5 * scale), 
                         int(5 * scale), int(12 * scale)))
        pygame.draw.rect(screen, SKIN, 
                        (int(x + 7 * scale), int(y - 5 * scale), 
                         int(5 * scale), int(12 * scale)))
        
        # Legs
        pygame.draw.rect(screen, BROWN, 
                        (int(x - 6 * scale), int(y + 13 * scale), 
                         int(5 * scale), int(15 * scale)))
        pygame.draw.rect(screen, BROWN, 
                        (int(x + 1 * scale), int(y + 13 * scale), 
                         int(5 * scale), int(15 * scale)))
            
    def draw_fps_view(self):
        # Dramatic sunset/dusk sky with gradient
        for i in range(HEIGHT // 2):
            ratio = i / (HEIGHT // 2)
            if not self.slow_motion:
                r = int(255 * (1 - ratio * 0.5))
                g = int(140 * (1 - ratio * 0.7))
                b = int(50 + 150 * ratio)
            else:
                r = int(200 * (1 - ratio * 0.5))
                g = int(100 * (1 - ratio * 0.7))
                b = int(150 + 50 * ratio)
            pygame.draw.line(screen, (r, g, b), (0, i), (WIDTH, i))
        
        # Dramatic ground with shadows
        for i in range(HEIGHT // 2, HEIGHT):
            ratio = (i - HEIGHT // 2) / (HEIGHT // 2)
            if not self.slow_motion:
                gray_val = int(40 + ratio * 30)
                pygame.draw.line(screen, (gray_val, gray_val + 10, gray_val), (0, i), (WIDTH, i))
            else:
                gray_val = int(30 + ratio * 20)
                pygame.draw.line(screen, (gray_val, gray_val, gray_val + 30), (0, i), (WIDTH, i))
        
        # Add dramatic fog/atmosphere particles
        if not self.slow_motion:
            for _ in range(15):
                fog_x = random.randint(0, WIDTH)
                fog_y = random.randint(0, HEIGHT // 2)
                fog_size = random.randint(30, 80)
                fog_surface = pygame.Surface((fog_size, fog_size), pygame.SRCALPHA)
                pygame.draw.circle(fog_surface, (255, 255, 255, 20), (fog_size // 2, fog_size // 2), fog_size // 2)
                screen.blit(fog_surface, (fog_x, fog_y))
        
        # Slow motion effect overlay
        if self.slow_motion:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(30)
            overlay.fill((100, 100, 255))
            screen.blit(overlay, (0, 0))
        
        # Sort entities by distance for proper rendering
        entities = []
        
        # Add walls
        for wall in self.walls:
            wall_center_x = wall.x + wall.width // 2
            wall_center_y = wall.y + wall.height // 2
            dist = math.sqrt((wall_center_x - self.player.x)**2 + 
                           (wall_center_y - self.player.y)**2)
            entities.append(('wall', wall, dist))
        
        # Add player (for third person view)
        entities.append(('player', self.player, 0))
        
        # Add bullets
        for bullet in self.bullets:
            dist = math.sqrt((bullet.x - self.player.x)**2 + 
                           (bullet.y - self.player.y)**2)
            entities.append(('bullet', bullet, dist))
        
        # Add enemies
        for enemy in self.enemies:
            dist = math.sqrt((enemy.x - self.player.x)**2 + 
                           (enemy.y - self.player.y)**2)
            entities.append(('enemy', enemy, dist))
            
        # Add hostages
        for hostage in self.hostages:
            if not hostage.saved:
                dist = math.sqrt((hostage.x - self.player.x)**2 + 
                               (hostage.y - self.player.y)**2)
                entities.append(('hostage', hostage, dist))
        
        # Sort by distance (furthest first)
        entities.sort(key=lambda e: e[2], reverse=True)
        
        # Draw entities
        for entity_type, entity, dist in entities:
            if entity_type == 'wall':
                self.draw_wall_3pv(entity)
            elif entity_type == 'player':
                self.draw_player_3pv(entity)
            elif entity_type == 'bullet':
                self.draw_bullet_3pv(entity)
            elif entity_type == 'enemy':
                self.draw_enemy_3pv(entity)
            elif entity_type == 'hostage':
                self.draw_hostage_3pv(entity)
                
    def draw_player_3pv(self, player):
        """Draw player in third person view"""
        # Calculate camera position behind player
        cam_x = player.x - math.cos(player.angle) * player.camera_distance
        cam_y = player.y - math.sin(player.angle) * player.camera_distance
        
        # Calculate screen position
        screen_x = WIDTH // 2
        screen_y = HEIGHT // 2 + 50
        
        # Draw player
        self.draw_human(screen, screen_x, screen_y, 1.5, BLUE)
        
        # Draw weapon in hand
        if player.weapon == "gun":
            gun_x = screen_x + 15
            gun_y = screen_y
            pygame.draw.rect(screen, BLACK, (gun_x, gun_y - 5, 30, 8))
            pygame.draw.rect(screen, GRAY, (gun_x + 25, gun_y - 10, 8, 18))
        else:
            knife_x = screen_x + 18
            knife_y = screen_y - 10
            pygame.draw.polygon(screen, GRAY, [
                (knife_x, knife_y),
                (knife_x + 5, knife_y + 20),
                (knife_x + 8, knife_y + 20),
                (knife_x + 13, knife_y)
            ])
    
    def draw_bullet_3pv(self, bullet):
        """Draw bullets in 3D space for third person"""
        # Calculate relative position from player
        rel_x = bullet.x - self.player.x
        rel_y = bullet.y - self.player.y
        
        # Rotate relative to camera angle
        cam_angle = self.player.angle + math.pi
        rotated_x = rel_x * math.cos(-cam_angle) - rel_y * math.sin(-cam_angle)
        rotated_y = rel_x * math.sin(-cam_angle) + rel_y * math.cos(-cam_angle)
        
        # Apply perspective
        distance = math.sqrt(rel_x**2 + rel_y**2)
        if distance > 0:
            perspective = 200 / (distance + 50)
            screen_x = WIDTH // 2 + int(rotated_x * perspective)
            screen_y = HEIGHT // 2 + int(rotated_y * perspective * 0.5)
            
            if 0 < screen_x < WIDTH and 0 < screen_y < HEIGHT:
                bullet_color = ORANGE if bullet.friendly else RED
                bullet_size = max(int(8 * perspective), 3)
                pygame.draw.circle(screen, bullet_color, (screen_x, screen_y), bullet_size)
                
                # Bullet trail in slow motion
                if self.slow_motion:
                    trail_length = 20
                    trail_angle = bullet.angle - cam_angle
                    trail_x = screen_x - int(math.cos(trail_angle) * trail_length)
                    trail_y = screen_y - int(math.sin(trail_angle) * trail_length * 0.5)
                    pygame.draw.line(screen, bullet_color, (screen_x, screen_y), 
                                   (trail_x, trail_y), max(2, bullet_size // 2))
                
    def draw_wall_3pv(self, wall):
        """Draw walls in third person perspective"""
        # Calculate relative position from player
        rel_x = wall.x - self.player.x
        rel_y = wall.y - self.player.y
        
        cam_angle = self.player.angle + math.pi
        rotated_x = rel_x * math.cos(-cam_angle) - rel_y * math.sin(-cam_angle)
        rotated_y = rel_x * math.sin(-cam_angle) + rel_y * math.cos(-cam_angle)
        
        distance = math.sqrt(rel_x**2 + rel_y**2)
        if distance > 0 and distance < 500:
            perspective = 200 / (distance + 50)
            screen_x = WIDTH // 2 + int(rotated_x * perspective)
            screen_y = HEIGHT // 2 + int(rotated_y * perspective * 0.5)
            
            wall_width = int(wall.width * perspective)
            wall_height = int(80 * perspective)
            
            if -100 < screen_x < WIDTH + 100:
                # Add dramatic lighting to walls
                base_gray = 50
                light_amount = max(0, 100 - distance // 3)
                wall_color = (base_gray + light_amount, base_gray + light_amount, base_gray + light_amount)
                pygame.draw.rect(screen, wall_color, 
                               (screen_x, screen_y - wall_height//2, wall_width, wall_height))
                # Add edge highlight
                pygame.draw.rect(screen, (100, 100, 100), 
                               (screen_x, screen_y - wall_height//2, wall_width, wall_height), 2)
                
    def draw_enemy_3pv(self, enemy):
        """Draw enemies in third person perspective"""
        rel_x = enemy.x - self.player.x
        rel_y = enemy.y - self.player.y
        
        cam_angle = self.player.angle + math.pi
        rotated_x = rel_x * math.cos(-cam_angle) - rel_y * math.sin(-cam_angle)
        rotated_y = rel_x * math.sin(-cam_angle) + rel_y * math.cos(-cam_angle)
        
        distance = math.sqrt(rel_x**2 + rel_y**2)
        if distance > 0 and distance < 500:
            perspective = 200 / (distance + 50)
            screen_x = WIDTH // 2 + int(rotated_x * perspective)
            screen_y = HEIGHT // 2 + int(rotated_y * perspective * 0.5)
            
            if -100 < screen_x < WIDTH + 100:
                scale = perspective * 1.2
                self.draw_human(screen, screen_x, screen_y, scale, RED)
                
                # Health bar
                bar_width = int(40 * scale)
                bar_x = screen_x - bar_width // 2
                bar_y = screen_y - int(40 * scale)
                pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, 5))
                health_width = int(bar_width * (enemy.health / enemy.max_health))
                pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, 5))
                
    def draw_hostage_3pv(self, hostage):
        """Draw hostages in third person perspective"""
        rel_x = hostage.x - self.player.x
        rel_y = hostage.y - self.player.y
        
        cam_angle = self.player.angle + math.pi
        rotated_x = rel_x * math.cos(-cam_angle) - rel_y * math.sin(-cam_angle)
        rotated_y = rel_x * math.sin(-cam_angle) + rel_y * math.cos(-cam_angle)
        
        distance = math.sqrt(rel_x**2 + rel_y**2)
        if distance > 0 and distance < 500:
            perspective = 200 / (distance + 50)
            screen_x = WIDTH // 2 + int(rotated_x * perspective)
            screen_y = HEIGHT // 2 + int(rotated_y * perspective * 0.5)
            
            if -100 < screen_x < WIDTH + 100:
                scale = perspective * 1.2
                self.draw_human(screen, screen_x, screen_y, scale, YELLOW)
                
                font = pygame.font.Font(None, int(40 * scale))
                text = font.render("!", True, WHITE)
                screen.blit(text, (screen_x - 5, screen_y - int(50 * scale)))
                
    def draw_bullet_fps(self, bullet):
        """Draw bullets in 3D space"""
        rel_x = bullet.x - self.player.x
        rel_y = bullet.y - self.player.y
        
        rotated_x = rel_x * math.cos(-self.player.angle) - rel_y * math.sin(-self.player.angle)
        rotated_y = rel_x * math.sin(-self.player.angle) + rel_y * math.cos(-self.player.angle)
        
        if rotated_y > 0:
            scale = 300 / max(rotated_y, 1)
            screen_x = WIDTH // 2 + int(rotated_x * scale)
            screen_y = HEIGHT // 2
            
            if -100 < screen_x < WIDTH + 100:
                bullet_color = ORANGE if bullet.friendly else RED
                bullet_size = int(8 * scale)
                pygame.draw.circle(screen, bullet_color, (screen_x, screen_y), max(bullet_size, 2))
                
                # Bullet trail in slow motion
                if self.slow_motion:
                    trail_length = 15
                    trail_x = screen_x - int(math.cos(bullet.angle) * trail_length)
                    trail_y = screen_y - int(math.sin(bullet.angle) * trail_length)
                    pygame.draw.line(screen, bullet_color, (screen_x, screen_y), 
                                   (trail_x, trail_y), max(2, bullet_size // 2))
                
    def draw_wall_fps(self, wall):
        rel_x = wall.x - self.player.x
        rel_y = wall.y - self.player.y
        
        rotated_x = rel_x * math.cos(-self.player.angle) - rel_y * math.sin(-self.player.angle)
        rotated_y = rel_x * math.sin(-self.player.angle) + rel_y * math.cos(-self.player.angle)
        
        if rotated_y > 0:
            scale = 300 / max(rotated_y, 1)
            screen_x = WIDTH // 2 + int(rotated_x * scale)
            screen_y = HEIGHT // 2
            
            wall_width = int(wall.width * scale)
            wall_height = int(150 * scale)
            
            if -100 < screen_x < WIDTH + 100:
                pygame.draw.rect(screen, DARK_GRAY, 
                               (screen_x, screen_y - wall_height//2, 
                                wall_width, wall_height))
                
    def draw_enemy_fps(self, enemy):
        rel_x = enemy.x - self.player.x
        rel_y = enemy.y - self.player.y
        
        rotated_x = rel_x * math.cos(-self.player.angle) - rel_y * math.sin(-self.player.angle)
        rotated_y = rel_x * math.sin(-self.player.angle) + rel_y * math.cos(-self.player.angle)
        
        if rotated_y > 0:
            scale = 300 / max(rotated_y, 1)
            screen_x = WIDTH // 2 + int(rotated_x * scale)
            screen_y = HEIGHT // 2
            
            if -100 < screen_x < WIDTH + 100:
                self.draw_human(screen, screen_x, screen_y, scale, RED)
                
                # Health bar
                bar_width = int(40 * scale)
                bar_x = screen_x - bar_width // 2
                bar_y = screen_y - int(40 * scale)
                pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, 5))
                health_width = int(bar_width * (enemy.health / enemy.max_health))
                pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, 5))
                
    def draw_hostage_fps(self, hostage):
        rel_x = hostage.x - self.player.x
        rel_y = hostage.y - self.player.y
        
        rotated_x = rel_x * math.cos(-self.player.angle) - rel_y * math.sin(-self.player.angle)
        rotated_y = rel_x * math.sin(-self.player.angle) + rel_y * math.cos(-self.player.angle)
        
        if rotated_y > 0:
            scale = 300 / max(rotated_y, 1)
            screen_x = WIDTH // 2 + int(rotated_x * scale)
            screen_y = HEIGHT // 2
            
            if -100 < screen_x < WIDTH + 100:
                self.draw_human(screen, screen_x, screen_y, scale, YELLOW)
                
                font = pygame.font.Font(None, int(40 * scale))
                text = font.render("!", True, WHITE)
                screen.blit(text, (screen_x - 5, screen_y - int(50 * scale)))
    
    def draw_weapon(self):
        """Draw the current weapon on screen"""
        if self.player.weapon == "gun":
            # Draw gun
            gun_x = WIDTH - 150
            gun_y = HEIGHT - 100
            pygame.draw.rect(screen, BLACK, (gun_x, gun_y, 100, 20))
            pygame.draw.rect(screen, GRAY, (gun_x + 80, gun_y - 10, 20, 40))
            pygame.draw.circle(screen, BLACK, (gun_x + 10, gun_y + 10), 8)
        else:
            # Draw knife
            knife_x = WIDTH - 120
            knife_y = HEIGHT - 120
            pygame.draw.polygon(screen, GRAY, [
                (knife_x, knife_y),
                (knife_x + 15, knife_y + 60),
                (knife_x + 25, knife_y + 60),
                (knife_x + 40, knife_y)
            ])
            pygame.draw.rect(screen, BROWN, (knife_x + 10, knife_y + 60, 20, 40))
    
    def draw_hud(self):
        # Health bar
        bar_width = 300
        bar_height = 30
        bar_x = WIDTH // 2 - bar_width // 2
        bar_y = HEIGHT - 60
        
        pygame.draw.rect(screen, BLACK, (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        health_width = int(bar_width * (self.player.health / self.player.max_health))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, bar_height))
        
        font = pygame.font.Font(None, 28)
        text = font.render(f"HP: {int(self.player.health)}/{self.player.max_health}", True, WHITE)
        screen.blit(text, (bar_x + bar_width // 2 - 50, bar_y + 5))
        
        # Mission info
        font_large = pygame.font.Font(None, 32)
        text = font_large.render(f"Hostages: {self.hostages_saved}/{len(self.hostages)}", True, WHITE)
        screen.blit(text, (20, 20))
        
        text = font_large.render(f"Enemies: {len(self.enemies)}", True, WHITE)
        screen.blit(text, (20, 55))
        
        # Weapon indicator
        weapon_text = "GUN" if self.player.weapon == "gun" else "KNIFE"
        weapon_color = BLUE if self.player.weapon == "gun" else ORANGE
        text = font_large.render(f"Weapon: {weapon_text}", True, weapon_color)
        screen.blit(text, (20, 90))
        
        # Slow motion indicator
        if self.slow_motion:
            font_huge = pygame.font.Font(None, 48)
            text = font_huge.render("SLOW MOTION", True, (100, 200, 255))
            screen.blit(text, (WIDTH // 2 - 150, 80))
        
        # Crosshair
        crosshair_size = 20
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        pygame.draw.line(screen, WHITE, (center_x - crosshair_size, center_y), 
                        (center_x + crosshair_size, center_y), 2)
        pygame.draw.line(screen, WHITE, (center_x, center_y - crosshair_size), 
                        (center_x, center_y + crosshair_size), 2)
        pygame.draw.circle(screen, WHITE, (center_x, center_y), 5, 2)
        
        # Draw weapon model
        self.draw_weapon()
        
    def draw_death_screen(self):
        screen.fill(BLACK)
        self.death_timer += 1
        
        alpha = min(255, self.death_timer * 3)
        
        font_huge = pygame.font.Font(None, 96)
        font_medium = pygame.font.Font(None, 42)
        
        if self.death_timer > 60:
            text = font_huge.render("YOU DIED", True, RED)
            text.set_alpha(alpha)
            screen.blit(text, (WIDTH//2 - 180, HEIGHT//2 - 50))
            
        if self.death_timer > 120:
            text = font_medium.render("Press R to Restart", True, WHITE)
            screen.blit(text, (WIDTH//2 - 140, HEIGHT//2 + 50))
            
    def draw_mission(self):
        self.draw_fps_view()
        self.draw_hud()
        
        # Add vignette effect for drama
        vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(150):
            alpha = int((i / 150) * 80)
            pygame.draw.rect(vignette, (0, 0, 0, alpha), (i, i, WIDTH - i*2, HEIGHT - i*2), 1)
        screen.blit(vignette, (0, 0))
        
        # Controls hint
        font_small = pygame.font.Font(None, 20)
        text = font_small.render("WASD: Move | Mouse: Aim | Click: Shoot | Q: Switch Weapon", True, WHITE)
        screen.blit(text, (WIDTH - 470, HEIGHT - 25))
        
    def draw_timeskip(self):
        screen.fill(BLACK)
        self.timeskip_timer += 1
        
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        
        if self.timeskip_timer < 120:
            text = font_large.render("MISSION COMPLETE", True, GREEN)
            screen.blit(text, (WIDTH//2 - 280, HEIGHT//2 - 50))
        elif self.timeskip_timer < 200:
            text = font_medium.render("3 MONTHS LATER...", True, WHITE)
            screen.blit(text, (WIDTH//2 - 200, HEIGHT//2))
        else:
            self.state = ENDING
            
    def draw_ending(self):
        screen.fill((135, 206, 235))
        self.ending_timer += 1
        
        # Draw celebrating crowd
        for i in range(20):
            x = 30 + i * 40
            y = 480
            self.draw_human(screen, x, y, 0.8, 
                          (random.randint(50, 200), random.randint(50, 200), random.randint(100, 255)))
            
        # Draw hero in center
        hero_x, hero_y = WIDTH//2, 320
        self.draw_human(screen, hero_x, hero_y, 2.5, BLUE)
        
        # Head turn animation
        if self.ending_timer > 180:
            self.head_turn_angle = min(self.head_turn_angle + 1.5, 90)
            
        # Text
        font_huge = pygame.font.Font(None, 84)
        font_large = pygame.font.Font(None, 52)
        
        if self.ending_timer < 120:
            text = font_huge.render("HERO!", True, (255, 215, 0))
            screen.blit(text, (WIDTH//2 - 100, 50))
            
            text = font_large.render("The city celebrates you!", True, BLACK)
            screen.blit(text, (WIDTH//2 - 220, 140))
            
        if self.ending_timer > 180 and self.head_turn_angle > 70:
            text = font_huge.render("TO BE CONTINUED...", True, RED)
            screen.blit(text, (WIDTH//2 - 320, HEIGHT - 80))
            
    def restart(self):
        self.__init__()

def main():
    game = Game()
    running = True
    mouse_click = False
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    pygame.mouse.set_pos(center_x, center_y)
    
    while running:
        clock.tick(FPS)
        mouse_dx = 0
        mouse_click = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and game.state == MISSION:
                mouse_click = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game.state == DEATH:
                    game.restart()
                if event.key == pygame.K_ESCAPE:
                    running = False
                
        if game.state == MISSION:
            mouse_pos = pygame.mouse.get_pos()
            mouse_dx = mouse_pos[0] - center_x
            pygame.mouse.set_pos(center_x, center_y)
            
        keys = pygame.key.get_pressed()
        
        if game.state == MISSION:
            game.handle_mission(keys, mouse_dx, mouse_click)
            game.draw_mission()
        elif game.state == DEATH:
            game.draw_death_screen()
        elif game.state == TIMESKIP:
            game.draw_timeskip()
        elif game.state == ENDING:
            game.draw_ending()
            
        pygame.display.flip()
        
    pygame.quit()

if __name__ == "__main__":
    main()
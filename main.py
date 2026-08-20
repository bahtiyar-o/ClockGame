import pygame
import sys
import random
import math
import os

pygame.init()


FPS = 60

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
width, height = screen.get_size()

pygame.display.set_caption("Clock")
clock = pygame.time.Clock()
game_font = pygame.font.Font(None, 40)

try:
    save_dir = pygame.system.get_pref_path("MyGames", "ClockGame")
except AttributeError:
    save_dir = "."
    
save_file_path = os.path.join(save_dir, "highscore.txt")

def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

hit_yellow_snd = pygame.mixer.Sound(resource_path("yellow.wav"))
hit_blue_snd = pygame.mixer.Sound(resource_path("blue.wav"))
miss_snd = pygame.mixer.Sound(resource_path("miss.wav"))
game_over_snd = pygame.mixer.Sound(resource_path("end.wav"))

hit_yellow_snd.set_volume(0.5)
hit_blue_snd.set_volume(0.5)

def load_high_score():
    if os.path.exists(save_file_path):
        try:
            with open(save_file_path, "r") as file:
                return int(file.read())
        except:
            return 0
    return 0

def save_high_score(new_score):
    try:
        with open(save_file_path, "w") as file:
            file.write(str(new_score))
    except Exception as e:
        print(f"Failed to save score: {e}")

class Zone:
    def __init__(self, angle):
        self.center_angle = angle
        self.sweep_angle = 20
        self.shrink_speed = 0.1
        self.outer_radius = 200
        self.inner_radius = 150
        self.color = random.randint(0, 4) #0 for blue

    def update(self):
        self.sweep_angle -= self.shrink_speed

    def is_dead(self):
        return self.sweep_angle <= 0

    def get_surface_and_mask(self):
        surface_size = self.outer_radius * 2
        sector_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        surface_center = (self.outer_radius, self.outer_radius)

        half_sweep = self.sweep_angle / 2
        start_angle = self.center_angle - half_sweep
        end_angle = self.center_angle + half_sweep

        points = []
        
        # Outer Edge
        for angle in range(int(start_angle), int(end_angle) + 1, 5): 
            rad = math.radians(angle)
            x = surface_center[0] + self.outer_radius * math.cos(rad)
            y = surface_center[1] - self.outer_radius * math.sin(rad)
            points.append((x, y))
            
        points.append((
            surface_center[0] + self.outer_radius * math.cos(math.radians(end_angle)),
            surface_center[1] - self.outer_radius * math.sin(math.radians(end_angle))
        ))

        # Inner Edge
        for angle in range(int(end_angle), int(start_angle) - 1, -5):
            rad = math.radians(angle)
            x = surface_center[0] + self.inner_radius * math.cos(rad)
            y = surface_center[1] - self.inner_radius * math.sin(rad)
            points.append((x, y))

        points.append((
            surface_center[0] + self.inner_radius * math.cos(math.radians(start_angle)),
            surface_center[1] - self.inner_radius * math.sin(math.radians(start_angle))
        ))

        if len(points) >= 3:
            if self.color == 0:
                pygame.draw.polygon(sector_surface, (0, 0, 255), points)
            else:
                pygame.draw.polygon(sector_surface, (255, 255, 0), points)
            
        sector_mask = pygame.mask.from_surface(sector_surface)
        return sector_surface, sector_mask

# Variables
blade_length = 200
blade_thickness = 5
blade_angle = 90
blade_acc = 0.05
blade_velocity = 2

mode_counter = random.randint(7,9)
lower_bound = 600
upper_bound = 1400
zone_spawn = pygame.USEREVENT
pygame.time.set_timer(zone_spawn, random.randint(lower_bound, upper_bound))

timer = 30
score = 0
high_score = load_high_score()

active_zones = []
angle_cd = {}

def spawn_zone():
    available_angles = []
    for i in range(18):
        angle = 20 * i
        if angle not in angle_cd:
            available_angles.append(angle)
            
    if len(available_angles) > 0:
        chosen_angle = random.choice(available_angles)
        new_zone = Zone(chosen_angle)
        active_zones.append(new_zone)
        angle_cd[chosen_angle] = 3.1

# Rotating blade
surface_width = blade_length * 2
invis_surface = pygame.Surface((surface_width, blade_thickness), pygame.SRCALPHA)
visible_blade = pygame.Rect(blade_length, 0, blade_length, blade_thickness)
pivot_center = (width / 2, height / 2)

game_active, running = True, True

while running:
    dt = clock.tick(60) / 1000.0
    if timer == 0:
        blade_angle = 90
        if score > high_score:
            high_score = score
            save_high_score(high_score)

        screen.fill((30, 30, 30))
        game_over_text = game_font.render("Game Over! Tap to Restart.", True, (255, 0, 0))
        score_text = game_font.render(f"Score: {int(score)}", True, (255, 255, 255))
        high_score_text = game_font.render(f"High Score: {int(high_score)}", True, (255, 215, 0))
        screen.blit(game_over_text, game_over_text.get_rect(center=(width // 2, height // 2 - 80)))
        screen.blit(score_text, score_text.get_rect(center=(width // 2, height // 2)))
        screen.blit(high_score_text, high_score_text.get_rect(center=(width // 2, height // 2 + 80)))
        
    if game_active:
        timer -= dt
        if timer <= 0:
            timer = 0
            game_active = False
            game_over_snd.play()
        
        mode_counter -= dt
        if mode_counter <= 0:
            mode_counter = random.randint(7,9)
            if lower_bound == 600:
                lower_bound -= 200
                upper_bound -= 250
            else:
                lower_bound += 200
                upper_bound += 250

        angles_to_remove = []
        for angle in angle_cd:
            angle_cd[angle] -= dt
            if angle_cd[angle] <= 0:
                angles_to_remove.append(angle) 
        for angle in angles_to_remove:
            del angle_cd[angle]

        if 0 < blade_velocity < 2:
            blade_velocity += blade_acc
        elif -2< blade_velocity < 0:
            blade_velocity -= blade_acc
        elif blade_velocity > 2:
            blade_velocity = 2
        elif blade_velocity < -2:
            blade_velocity = -2
        blade_angle += blade_velocity

        screen.fill((30, 30, 30))
        if abs(blade_velocity) == 2:
            pygame.draw.rect(invis_surface, (0, 255, 0), visible_blade)
        else:
            pygame.draw.rect(invis_surface, (255, 0, 0), visible_blade)
        rotated_surface = pygame.transform.rotate(invis_surface, blade_angle)
        rotated_rect = rotated_surface.get_rect(center=pivot_center)
        blade_mask = pygame.mask.from_surface(rotated_surface)
        screen.blit(rotated_surface, rotated_rect)
        score_surface = game_font.render(f"{int(score)}", True, (255, 255, 255))
        screen.blit(score_surface, score_surface.get_rect(center=(width // 2, 80)))
        timer_surface = game_font.render(f"{timer:.1f}", True, (255, 255, 255))
        screen.blit(timer_surface, timer_surface.get_rect(center=(width // 2, height - 80)))

    for zone in active_zones[::-1]:
        zone.update()
        if zone.is_dead():
            active_zones.remove(zone)
            continue
        sector_surface, sector_mask = zone.get_surface_and_mask()
        sector_rect = sector_surface.get_rect(center=pivot_center)                 
        screen.blit(sector_surface, sector_rect)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == zone_spawn and game_active:
            spawn_zone()
            pygame.time.set_timer(zone_spawn, random.randint(lower_bound, upper_bound))
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
            if game_active:
                if abs(blade_velocity) >= 2:
                    hit_successful = False 
                    for zone in active_zones[::-1]:
                        sector_surface, sector_mask = zone.get_surface_and_mask()
                        sector_rect = sector_surface.get_rect(center=pivot_center)
                        offset = (sector_rect.x - rotated_rect.x, sector_rect.y - rotated_rect.y)
                        
                        if blade_mask.overlap(sector_mask, offset):
                            score += 1
                            active_zones.remove(zone)
                            if zone.color == 0:
                                timer += 2
                                hit_blue_snd.play()
                            else:
                                hit_yellow_snd.play()
                            if blade_velocity > 0:
                                blade_velocity = -2
                            else:
                                blade_velocity = 2
                                
                            hit_successful = True 
                            break 
                            
                    if not hit_successful:
                        blade_velocity = blade_velocity / 100
                        miss_snd.play()
                
            else:
                game_active = True
                score = 0
                timer = 30
                active_zones.clear()
                angle_cd.clear()
                mode_counter = random.randint(7,9)
                lower_bound = 600
                upper_bound = 1400
                pygame.time.set_timer(zone_spawn, random.randint(lower_bound, upper_bound))

    pygame.display.update()

pygame.quit()
sys.exit()

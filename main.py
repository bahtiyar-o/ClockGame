import pygame
import sys
import random
import math
import os

# 1. Pre-init mixer to ensure Android audio buffers initialize safely
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

FPS = 60
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
width, height = screen.get_size()
pygame.display.set_caption("Clock")
clock = pygame.time.Clock()
game_font = pygame.font.Font(None, 220)
text_font = pygame.font.Font(None, 110)

# 2. Android-safe absolute pathing
try:
    base_path = sys._MEIPASS
except AttributeError:
    base_path = os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    return os.path.join(base_path, relative_path)

# 3. Android-safe writable storage for High Scores
if 'ANDROID_ARGUMENT' in os.environ:
    save_dir = os.environ.get('ANDROID_PRIVATE', base_path)
else:
    try:
        import pygame.system
        save_dir = pygame.system.get_pref_path("MyGames", "ClockGame")
    except (ImportError, AttributeError):
        save_dir = base_path
        
save_file_path = os.path.join(save_dir, "highscore.txt")

# 4. Bulletproof Audio Loading 
class MockSound:
    def play(self): pass
    def set_volume(self, v): pass

try:
    hit_yellow_snd = pygame.mixer.Sound(resource_path("yellow.wav"))
    hit_blue_snd = pygame.mixer.Sound(resource_path("blue.wav"))
    miss_snd = pygame.mixer.Sound(resource_path("miss.wav"))
    game_over_snd = pygame.mixer.Sound(resource_path("end.wav"))
    hit_yellow_snd.set_volume(0.5)
    hit_blue_snd.set_volume(0.5)
except Exception as e:
    print(f"Audio Load Error: {e}")
    hit_yellow_snd = hit_blue_snd = miss_snd = game_over_snd = MockSound()

try:
    raw_icon = pygame.image.load(resource_path("restart_icon.png")).convert_alpha()
    restart_img = pygame.transform.smoothscale(raw_icon, (60, 60))
except Exception as e:
    print(f"Icon Load Error: {e}")
    restart_img = pygame.Surface((60, 60), pygame.SRCALPHA)
    pygame.draw.circle(restart_img, (150, 150, 150), (30, 30), 30)

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


class FloatingText:
    def __init__(self, text, x, y, color):
        self.text = text
        self.x = x
        self.y = float(y)
        self.color = color
        self.alpha = 255
        self.speed = 40
        self.fade_speed = 255

    def update(self, dt):
        self.y -= self.speed * dt
        self.alpha -= self.fade_speed * dt

    def is_dead(self):
        return self.alpha <= 0

    def draw(self, surface, font):
        if self.alpha > 0:
            text_surf = font.render(self.text, True, self.color)
            text_surf.set_alpha(int(self.alpha)) 
            rect = text_surf.get_rect(center=(self.x, int(self.y)))
            surface.blit(text_surf, rect)

class Zone:
    def __init__(self, angle):
        self.center_angle = angle
        self.sweep_angle = 20
        self.shrink_speed = 6.0 
        self.outer_radius = blade_length
        self.inner_radius = (3 * self.outer_radius) / 4
        self.color = random.randint(0, 4)

    def update(self, dt):
        self.sweep_angle -= self.shrink_speed * dt

    def is_dead(self):
        return self.sweep_angle <= 0

    def draw(self, screen, pivot_center):
        half_sweep = self.sweep_angle / 2
        start_angle = self.center_angle - half_sweep
        end_angle = self.center_angle + half_sweep

        points = []
        
        for angle in range(int(start_angle), int(end_angle) + 1, 5): 
            rad = math.radians(angle)
            x = pivot_center[0] + self.outer_radius * math.cos(rad)
            y = pivot_center[1] - self.outer_radius * math.sin(rad)
            points.append((x, y))
            
        points.append((
            pivot_center[0] + self.outer_radius * math.cos(math.radians(end_angle)),
            pivot_center[1] - self.outer_radius * math.sin(math.radians(end_angle))
        ))

        for angle in range(int(end_angle), int(start_angle) - 1, -5):
            rad = math.radians(angle)
            x = pivot_center[0] + self.inner_radius * math.cos(rad)
            y = pivot_center[1] - self.inner_radius * math.sin(rad)
            points.append((x, y))

        points.append((
            pivot_center[0] + self.inner_radius * math.cos(math.radians(start_angle)),
            pivot_center[1] - self.inner_radius * math.sin(math.radians(start_angle))
        ))

        if len(points) >= 3:
            color = (0, 0, 255) if self.color == 0 else (255, 255, 0)
            pygame.draw.polygon(screen, color, points)

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
        angle_cd[chosen_angle] = 3.2

def is_blade_hitting_zone(blade_angle, zone):
    normalized_blade = blade_angle % 360
    half_sweep = zone.sweep_angle / 2
    start_angle = (zone.center_angle - half_sweep) % 360
    end_angle = (zone.center_angle + half_sweep) % 360
    
    if start_angle < end_angle:
        return start_angle <= normalized_blade <= end_angle
    else:
        return normalized_blade >= start_angle or normalized_blade <= end_angle


# Variables
high_score = load_high_score()
pivot_center = (width / 2, height / 2)
timer_default = 30
blade_max_velocity = 2
blade_length = (4 * width) / 10
blade_thickness = 7
blade_acc = 0.05
lower_bound_default = 600
upper_bound_default = 1400
lower_bound_fast = 400
upper_bound_fast = 1150
zone_spawn = pygame.USEREVENT

active_zones = []
angle_cd = {}
floating_texts = []

rule1 = text_font.render("TAP TO STRIKE", True, (255, 255, 255))
rule2 = text_font.render("YELLOW: +1 SCORE", True, (255, 255, 0))
rule3 = text_font.render("BLUE: +1 SCORE, +2 TIME", True, (0, 0, 255))
start_prompt = text_font.render("TAP TO START!", True, (0, 255, 0))
game_over_text = text_font.render("GAME OVER!", True, (255, 0, 0))
high_score_text = text_font.render(f"HIGH SCORE: {int(high_score)}", True, (255, 215, 0))
restart_prompt = text_font.render("TAP TO RESTART!", True, (0, 255, 0))
restart_button = restart_img.get_rect(topright=(width - 60, 60))


game_state = "start" 
restart_cooldown = 0.0
running = True
new_record = False

while running:
    dt = clock.tick(60) / 1000.0
    screen.fill((30, 30, 30))

    if game_state == "start":
        screen.blit(rule1, rule1.get_rect(center=(width // 2, height // 2 - 320)))
        screen.blit(rule2, rule2.get_rect(center=(width // 2, height // 2 - 200)))
        screen.blit(rule3, rule3.get_rect(center=(width // 2, height // 2 -80)))
        screen.blit(high_score_text, high_score_text.get_rect(center=(width // 2, height // 2 + 120)))
        if pygame.time.get_ticks() % 1000 < 500:
            screen.blit(start_prompt, start_prompt.get_rect(center=(width // 2, height // 2 + 320)))

    elif game_state == "game_over":
        if restart_cooldown > 0:
            restart_cooldown -= dt

        if new_record == True:
            screen.blit(game_over_text, game_over_text.get_rect(center=(width // 2, height // 2 - 160)))
            screen.blit(score_text, score_text.get_rect(center=(width // 2, height // 2 - 40)))
            if pygame.time.get_ticks() % 1000 < 500:
                screen.blit(restart_prompt, restart_prompt.get_rect(center=(width // 2, height // 2 + 160)))
        else:
            screen.blit(game_over_text, game_over_text.get_rect(center=(width // 2, height // 2 - 220)))
            screen.blit(score_text, score_text.get_rect(center=(width // 2, height // 2 - 100)))
            screen.blit(high_score_text, high_score_text.get_rect(center=(width // 2, height // 2 + 20)))
            if pygame.time.get_ticks() % 1000 < 500:
                screen.blit(restart_prompt, restart_prompt.get_rect(center=(width // 2, height // 2 + 220)))

    elif game_state == "playing":
        timer -= dt
        mode_counter -= dt
        if mode_counter <= 0:
            mode_counter = random.randint(7,9)
            if lower_bound == lower_bound_default:
                lower_bound = lower_bound_fast
                upper_bound = upper_bound_fast
            else:
                lower_bound = lower_bound_default
                upper_bound = upper_bound_default

        angles_to_remove = []
        for angle in angle_cd:
            angle_cd[angle] -= dt
            if angle_cd[angle] <= 0:
                angles_to_remove.append(angle) 
        for angle in angles_to_remove:
            del angle_cd[angle]

        speed_factor = dt * 60
        if 0 < blade_velocity < blade_max_velocity:
            blade_velocity += blade_acc * speed_factor
        elif -blade_max_velocity < blade_velocity < 0:
            blade_velocity -= blade_acc * speed_factor
        elif blade_velocity > blade_max_velocity:
            blade_velocity = blade_max_velocity
        elif blade_velocity < -blade_max_velocity:
            blade_velocity = -blade_max_velocity
        blade_angle += blade_velocity * speed_factor
        blade_color = (0, 255, 0) if abs(blade_velocity) == blade_max_velocity else (255, 0, 0)
        
        rad = math.radians(blade_angle)
        tip_x = pivot_center[0] + blade_length * math.cos(rad)
        tip_y = pivot_center[1] - blade_length * math.sin(rad)
        pygame.draw.line(screen, blade_color, pivot_center, (tip_x, tip_y), blade_thickness)
        
        score_surface = game_font.render(f"{int(score)}", True, (255, 255, 255))
        screen.blit(score_surface, score_surface.get_rect(center=(width // 2, 140)))
        timer_surface = game_font.render(f"{timer:.1f}", True, (255, 255, 255))
        screen.blit(timer_surface, timer_surface.get_rect(center=(width // 2, height - 140)))

        current_frame_zones = []
        for zone in active_zones[::-1]:
            zone.update(dt)
            if zone.is_dead():
                active_zones.remove(zone)
                continue
            zone.draw(screen, pivot_center) 
            current_frame_zones.append(zone)

        for f_text in floating_texts[::-1]:
            f_text.update(dt)
            if f_text.is_dead():
                floating_texts.remove(f_text)
            else:
                f_text.draw(screen, game_font)

        screen.blit(restart_img, restart_button)

        if timer <= 0:
            timer = 0
            score_text = text_font.render(f"SCORE: {int(score)}", True, (255, 255, 255))
            high_score_text = text_font.render(f"HIGH SCORE: {int(high_score)}", True, (255, 215, 0))
            restart_cooldown = 0.5
            game_state = "game_over"
            game_over_snd.play()
            if score > high_score:
                high_score = score
                save_high_score(high_score)
                new_record = True
                score_text = text_font.render(f"NEW HIGH SCORE: {int(score)}", True, (255, 215, 0))


    tapped_this_frame = False
    tap_pos = None
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, getattr(pygame, 'K_AC_BACK', -1)):
            running = False
            
        if event.type == zone_spawn and game_state == "playing":
            spawn_zone()
            pygame.time.set_timer(zone_spawn, random.randint(lower_bound, upper_bound))
            
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            tapped_this_frame = True
            tap_pos = (width // 2, height // 2)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            tapped_this_frame = True
            tap_pos = event.pos
        if getattr(pygame, 'FINGERDOWN', None) is not None and event.type == pygame.FINGERDOWN:
            tapped_this_frame = True
            tap_pos = (event.x * width, event.y * height)

    if tapped_this_frame:
        if game_state == "playing":
            if tap_pos and restart_button.collidepoint(tap_pos):
                new_record = False
                game_over_snd.play()
                score = 0
                timer = timer_default
                blade_velocity = blade_max_velocity
                blade_angle = 90
                active_zones.clear()
                angle_cd.clear()
                floating_texts.clear()
                mode_counter = random.randint(7,9)
                lower_bound = lower_bound_default
                upper_bound = upper_bound_default
                pygame.time.set_timer(zone_spawn, random.randint(lower_bound, upper_bound))

            elif abs(blade_velocity) >= blade_max_velocity:
                hit_successful = False 
                for zone in current_frame_zones:
                    if is_blade_hitting_zone(blade_angle, zone):
                        score += 1
                        if zone in active_zones:
                            active_zones.remove(zone)
                            
                        if zone.color == 0:
                            timer += 2
                            floating_texts.append(FloatingText("+2", width // 2, height - 250, (0, 0, 255)))
                            hit_blue_snd.play()
                        else:
                            hit_yellow_snd.play()
                            
                        if blade_velocity > 0:
                            blade_velocity = -blade_max_velocity
                        else:
                            blade_velocity = blade_max_velocity
                            
                        hit_successful = True 
                        break 
                        
                if not hit_successful:
                    blade_velocity = blade_velocity / 100
                    miss_snd.play()
                    
        else:
            if game_state == "start" or (game_state == "game_over" and restart_cooldown <= 0):
                game_state = "playing"
                new_record = False
                score = 0
                timer = timer_default
                blade_velocity = blade_max_velocity
                blade_angle = 90
                active_zones.clear()
                angle_cd.clear()
                floating_texts.clear()
                mode_counter = random.randint(7,9)
                lower_bound = lower_bound_default
                upper_bound = upper_bound_default
                pygame.time.set_timer(zone_spawn, random.randint(lower_bound, upper_bound))

    pygame.display.update()

pygame.quit()
sys.exit()

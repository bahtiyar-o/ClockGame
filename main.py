import pygame
import sys
import random
import math
import os

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

FPS = 60
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
width, height = screen.get_size()
pygame.display.set_caption("Clock Game")
clock = pygame.time.Clock()
game_font = pygame.font.Font(None, 220)
text_font = pygame.font.Font(None, 110)

try:
    base_path = sys._MEIPASS
except AttributeError:
    base_path = os.path.dirname(os.path.abspath(__file__))
def resource_path(relative_path):
    return os.path.join(base_path, relative_path)
if 'ANDROID_ARGUMENT' in os.environ:
    save_dir = os.environ.get('ANDROID_PRIVATE', base_path)
else:
    try:
        import pygame.system
        save_dir = pygame.system.get_pref_path("MyGames", "ClockGame")
    except (ImportError, AttributeError):
        save_dir = base_path    
save_file_path = os.path.join(save_dir, "highscore.txt")

class MockSound:
    def play(self): pass
try:
    hit_yellow_snd = pygame.mixer.Sound(resource_path("yellow.wav"))
    hit_blue_snd = pygame.mixer.Sound(resource_path("blue.wav"))
    miss_snd = pygame.mixer.Sound(resource_path("miss.wav"))
    game_over_snd = pygame.mixer.Sound(resource_path("end.wav"))
except Exception as e:
    print(f"Audio Load Error: {e}")
    hit_yellow_snd = hit_blue_snd = miss_snd = game_over_snd = MockSound()

try:
    raw_icon = pygame.image.load(resource_path("restart_icon.png")).convert_alpha()
    restart_img = pygame.transform.smoothscale(raw_icon, (140, 140))
except Exception as e:
    print(f"Icon Load Error: {e}")
    restart_img = pygame.Surface((140, 140), pygame.SRCALPHA)
    pygame.draw.circle(restart_img, (150, 150, 150), (30, 30), 30)
try:
    raw_mute_off = pygame.image.load(resource_path("mute_off.png")).convert_alpha()
    mute_off_img = pygame.transform.smoothscale(raw_mute_off, (140, 140))
    raw_mute_on = pygame.image.load(resource_path("mute_on.png")).convert_alpha()
    mute_on_img = pygame.transform.smoothscale(raw_mute_on, (140, 140))
except Exception as e:
    print(f"Mute Icon Load Error: {e}")
    mute_off_img = pygame.Surface((140, 140), pygame.SRCALPHA)
    pygame.draw.circle(mute_off_img, (150, 150, 150), (70, 70), 50)
    mute_on_img = pygame.Surface((140, 140), pygame.SRCALPHA)
    pygame.draw.circle(mute_on_img, (255, 100, 100), (70, 70), 50)

def load_save_data():
    if os.path.exists(save_file_path):
        try:
            with open(save_file_path, "r") as file:
                data = file.read().strip().split(',')
                return int(data[0]), data[1] == "True"
        except:
            return 0, False
    return 0, False
def save_game_data(new_score, muted_state):
    try:
        with open(save_file_path, "w") as file:
            file.write(f"{int(new_score)},{muted_state}")
    except Exception as e:
        print(f"Failed to save data: {e}")


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
    def __init__(self, angle, timer = 30):
        self.center_angle = angle
        self.sweep_angle = 20
        self.shrink_speed = 6
        self.outer_radius = blade_length
        self.inner_radius = (3 * self.outer_radius) / 4
        if timer > 6:
            chance = 0.25
        else:
            chance = 0.4
            
        self.color = 0 if random.random() < chance else 1

    def update(self, dt):
        self.sweep_angle -= self.shrink_speed * dt

    def is_dead(self):
        return self.sweep_angle <= 0

    def draw(self, screen, pivot_center):
        half_sweep = self.sweep_angle / 2
        start_angle = self.center_angle - half_sweep
        end_angle = self.center_angle + half_sweep

        # Pre-calculate trigonometry for the exact corners to save CPU cycles
        rad_start = math.radians(start_angle)
        rad_end = math.radians(end_angle)
        
        cos_start = math.cos(rad_start)
        sin_start = math.sin(rad_start)
        cos_end = math.cos(rad_end)
        sin_end = math.sin(rad_end)

        points = []
        
        # 1. Exact Start Point (Outer)
        points.append((
            pivot_center[0] + self.outer_radius * cos_start,
            pivot_center[1] - self.outer_radius * sin_start
        ))

        # 2. Smooth internal points (Outer)
        first_int = math.ceil(start_angle)
        last_int = math.floor(end_angle)
        for angle in range(first_int, last_int + 1, 2): 
            rad = math.radians(angle)
            points.append((
                pivot_center[0] + self.outer_radius * math.cos(rad),
                pivot_center[1] - self.outer_radius * math.sin(rad)
            ))
            
        # 3. Exact End Point (Outer)
        points.append((
            pivot_center[0] + self.outer_radius * cos_end,
            pivot_center[1] - self.outer_radius * sin_end
        ))

        # 4. Exact End Point (Inner)
        points.append((
            pivot_center[0] + self.inner_radius * cos_end,
            pivot_center[1] - self.inner_radius * sin_end
        ))

        # 5. Smooth internal points (Inner)
        for angle in range(last_int, first_int - 1, -2):
            rad = math.radians(angle)
            points.append((
                pivot_center[0] + self.inner_radius * math.cos(rad),
                pivot_center[1] - self.inner_radius * math.sin(rad)
            ))

        # 6. Exact Start Point (Inner)
        points.append((
            pivot_center[0] + self.inner_radius * cos_start,
            pivot_center[1] - self.inner_radius * sin_start
        ))

        # 7. Draw the polygon with dynamic color fading
        if len(points) >= 3:
            fade_ratio = max(0.3, self.sweep_angle / 20.0)
            
            if self.color == 0:
                current_color = (0, 0, int(255 * fade_ratio))
            else:
                current_color = (int(255 * fade_ratio), int(255 * fade_ratio), 0)
                
            pygame.draw.polygon(screen, current_color, points)

def restart_game():
    global game_state, new_record, time_elapsed, score, timer, blade_velocity, blade_angle, shake_duration, current_score_surface  
    game_state = "playing"
    new_record = False
    time_elapsed = 0.0
    score = 0
    timer = timer_default
    blade_velocity = blade_max_velocity
    blade_angle = random.randint(0, 359)
    shake_duration = 0.0
    active_zones.clear()
    angle_cd.clear()
    floating_texts.clear()
    current_score_surface = game_font.render("0", True, (255, 255, 255))
    pygame.time.set_timer(zone_spawn, 500)

def spawn_zone(timer):
    available_angles = []
    for i in range(18):
        angle = 20 * i
        if angle not in angle_cd:
            available_angles.append(angle)
            
    if len(available_angles) > 0:
        chosen_angle = random.choice(available_angles)
        new_zone = Zone(chosen_angle, timer)
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
high_score, is_muted = load_save_data()
pivot_center = (width / 2, height / 2)
timer_default = 30
blade_max_velocity = 2
if height > width:
    blade_length = (4 * width) / 10
else:
    blade_length = (4 * height) / 10
blade_thickness = 7
blade_acc = 0.05
zone_spawn = pygame.USEREVENT

active_zones = []
angle_cd = {}
floating_texts = []

restart_button = restart_img.get_rect(center=(width - 140, 140))
mute_button = mute_off_img.get_rect(center=(140, 140))
rule1 = text_font.render("TAP TO STRIKE", True, (255, 255, 255))
rule2 = text_font.render("YELLOW: +1 SCORE", True, (255, 255, 0))
rule3 = text_font.render("BLUE: +1 SCORE, +2 TIME", True, (0, 0, 255))
start_prompt = text_font.render("TAP TO START!", True, (0, 255, 0))
game_over_text = text_font.render("GAME OVER!", True, (255, 0, 0))
high_score_text = text_font.render(f"HIGH SCORE: {int(high_score)}", True, (255, 215, 0))
restart_prompt = text_font.render("TAP TO RESTART!", True, (0, 255, 0))


game_state = "start"
time_elapsed = 0.0
restart_cooldown = 0.0
shake_duration = 0.0
current_score_surface = game_font.render("0", True, (255, 255, 255))
running = True
new_record = False

while running:
    dt = clock.tick(FPS) / 1000.0
    if dt > 0.05:
            dt = 0.05
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
        time_elapsed += dt
        timer -= dt

        shake_x, shake_y = 0, 0
        if shake_duration > 0:
            shake_duration -= dt
            intensity = 6
            shake_x = random.randint(-intensity, intensity)
            shake_y = random.randint(-intensity, intensity)
        draw_center = (pivot_center[0] + shake_x, pivot_center[1] + shake_y)

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
        tip_x = draw_center[0] + blade_length * math.cos(rad)
        tip_y = draw_center[1] - blade_length * math.sin(rad)
        pygame.draw.line(screen, blade_color, draw_center, (tip_x, tip_y), blade_thickness)
        
        if height > width:
            screen.blit(current_score_surface, current_score_surface.get_rect(center=(width // 2, 140)))
        else:
            screen.blit(current_score_surface, current_score_surface.get_rect(center=(200, height // 2)))
        timer_surface = game_font.render(f"{timer:.1f}", True, (255, 255, 255))
        if height > width:
            screen.blit(timer_surface, timer_surface.get_rect(center=(width // 2, height - 140)))
        else:
            screen.blit(timer_surface, timer_surface.get_rect(center=(width - 200, height // 2)))
        current_frame_zones = []
        for zone in reversed(active_zones):
            zone.update(dt)
            if zone.is_dead():
                active_zones.remove(zone)
                continue
            zone.draw(screen, draw_center) 
            current_frame_zones.append(zone)

        for f_text in reversed(floating_texts):
            f_text.update(dt)
            if f_text.is_dead():
                floating_texts.remove(f_text)
            else:
                f_text.draw(screen, game_font)

        screen.blit(restart_img, restart_button)
        if is_muted:
            screen.blit(mute_on_img, mute_button)
        else:
            screen.blit(mute_off_img, mute_button)
        
        if timer <= 0:
            timer = 0
            score_text = text_font.render(f"SCORE: {int(score)}", True, (255, 255, 255))
            high_score_text = text_font.render(f"HIGH SCORE: {int(high_score)}", True, (255, 215, 0))
            restart_cooldown = 0.5
            game_state = "game_over"
            if not is_muted: game_over_snd.play()
            if score > high_score:
                high_score = score
                save_game_data(high_score, is_muted)
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
            spawn_zone(timer)
            
            if time_elapsed < 10:
                base_interval = 1200
            elif time_elapsed < 25:
                base_interval = 800
            else:
                base_interval = 500
            
            lower = int(base_interval * 0.8)
            upper = int(base_interval * 1.2)
            pygame.time.set_timer(zone_spawn, random.randint(lower, upper))
            
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            tapped_this_frame = True
            tap_pos = (width // 2, height // 2)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            tapped_this_frame = True
            tap_pos = restart_button.center
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            tapped_this_frame = True
            tap_pos = event.pos
        if getattr(pygame, 'FINGERDOWN', None) is not None and event.type == pygame.FINGERDOWN:
            tapped_this_frame = True
            tap_pos = (event.x * width, event.y * height)

    if tapped_this_frame:
        if game_state == "playing":
            if tap_pos and restart_button.collidepoint(tap_pos):
                if not is_muted: game_over_snd.play()
                restart_game()
            elif tap_pos and mute_button.collidepoint(tap_pos):
                is_muted = not is_muted
                save_game_data(high_score, is_muted)

            elif abs(blade_velocity) >= blade_max_velocity:
                hit_successful = False 
                for zone in current_frame_zones:
                    if is_blade_hitting_zone(blade_angle, zone):
                        score += 1
                        current_score_surface = game_font.render(f"{int(score)}", True, (255, 255, 255))
                        if zone.center_angle in angle_cd and angle_cd[zone.center_angle] > 0.3:
                            angle_cd[zone.center_angle] = 0.3
                        if zone in active_zones:
                            active_zones.remove(zone)
                            
                        if zone.color == 0:
                            timer += 2
                            if height > width:
                                floating_texts.append(FloatingText("+2", width // 2, height - 250, (0, 0, 255)))
                            else:
                                floating_texts.append(FloatingText("+2", width - 200, height // 2 - 100, (0, 0, 255)))
                            if not is_muted: hit_blue_snd.play()
                        else:
                            if not is_muted: hit_yellow_snd.play()
                            
                        if blade_velocity > 0:
                            blade_velocity = -blade_max_velocity
                        else:
                            blade_velocity = blade_max_velocity
                            
                        hit_successful = True 
                        break 
                        
                if not hit_successful:
                    blade_velocity = blade_velocity / 100
                    shake_duration = 0.25
                    if not is_muted: miss_snd.play()
                    
        else:
            if game_state == "start" or (game_state == "game_over" and restart_cooldown <= 0):
                restart_game()

    pygame.display.update()

pygame.quit()
sys.exit()

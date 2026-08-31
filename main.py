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
    hit_yellow_snd = pygame.mixer.Sound(resource_path("sound_yellow.wav"))
    hit_blue_snd = pygame.mixer.Sound(resource_path("sound_blue.wav"))
    miss_snd = pygame.mixer.Sound(resource_path("sound_miss.wav"))
    game_over_snd = pygame.mixer.Sound(resource_path("sound_end.wav"))
    click_snd = pygame.mixer.Sound(resource_path("sound_click.wav"))
except Exception as e:
    hit_yellow_snd = hit_blue_snd = miss_snd = game_over_snd = click_snd = MockSound()

try:
    font_path = resource_path("font.ttf")
    game_font = pygame.font.Font(font_path, 80)
    text_font = pygame.font.Font(font_path, 60)
    title_font = pygame.font.Font(font_path, 110)
except Exception as e:
    game_font = pygame.font.Font(None, 80)
    text_font = pygame.font.Font(None, 60)
    title_font = pygame.font.Font(None, 110)

try:
    raw_menu = pygame.image.load(resource_path("icon_menu.png")).convert_alpha()
    base_menu = pygame.transform.smoothscale(raw_menu, (140, 140))
    raw_restart = pygame.image.load(resource_path("icon_restart.png")).convert_alpha()
    base_restart = pygame.transform.smoothscale(raw_restart, (140, 140))
    raw_mute = pygame.image.load(resource_path("icon_mute.png")).convert_alpha()
    base_mute = pygame.transform.smoothscale(raw_mute, (120, 120))

except Exception as e:
    base_menu = pygame.Surface((140, 140), pygame.SRCALPHA)
    base_menu.fill((150, 150, 150))
    base_restart = pygame.Surface((180, 180), pygame.SRCALPHA)
    base_restart.fill((150, 150, 150))
    base_mute = pygame.Surface((140, 140), pygame.SRCALPHA)
    base_mute.fill((150, 150, 150))

def load_save_data():
    if os.path.exists(save_file_path):
        try:
            with open(save_file_path, "r") as file:
                data = file.read().strip().split(',')
                if len(data) == 3:
                    return int(data[0]), data[1] == "True", data[2]
                elif len(data) == 2:
                    return int(data[0]), data[1] == "True", "space odyssey"
                elif len(data) == 1:
                    return int(data[0]), False, "space odyssey"
        except:
            return 0, False, "space odyssey"
    return 0, False, "space odyssey"

def save_game_data(new_score, muted_state, theme_name):
    try:
        with open(save_file_path, "w") as file:
            file.write(f"{int(new_score)},{muted_state},{theme_name}")
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

        rad_start = math.radians(start_angle)
        rad_end = math.radians(end_angle)        
        cos_start = math.cos(rad_start)
        sin_start = math.sin(rad_start)
        cos_end = math.cos(rad_end)
        sin_end = math.sin(rad_end)

        points = []
        
        points.append((
            pivot_center[0] + self.outer_radius * cos_start,
            pivot_center[1] - self.outer_radius * sin_start
        ))

        first_int = math.ceil(start_angle)
        last_int = math.floor(end_angle)
        for angle in range(first_int, last_int + 1, 2): 
            rad = math.radians(angle)
            points.append((
                pivot_center[0] + self.outer_radius * math.cos(rad),
                pivot_center[1] - self.outer_radius * math.sin(rad)
            ))

        points.append((
            pivot_center[0] + self.outer_radius * cos_end,
            pivot_center[1] - self.outer_radius * sin_end
        ))

        points.append((
            pivot_center[0] + self.inner_radius * cos_end,
            pivot_center[1] - self.inner_radius * sin_end
        ))

        for angle in range(last_int, first_int - 1, -2):
            rad = math.radians(angle)
            points.append((
                pivot_center[0] + self.inner_radius * math.cos(rad),
                pivot_center[1] - self.inner_radius * math.sin(rad)
            ))

        points.append((
            pivot_center[0] + self.inner_radius * cos_start,
            pivot_center[1] - self.inner_radius * sin_start
        ))

        if len(points) >= 3:
            if self.color == 0:
                current_color = color_time
            else:
                current_color = color_score
                
            pygame.draw.polygon(screen, current_color, points)

def restart_game():
    global game_state, new_record, time_elapsed, score, timer, blade_velocity, blade_angle, shake_duration, current_score_surface  
    game_state = "playing"
    new_record = False
    time_elapsed = 0.0
    score = 0
    timer = timer_default
    blade_velocity = blade_max_velocity
    blade_angle = 90
    shake_duration = 0.0
    active_zones.clear()
    angle_cd.clear()
    floating_texts.clear()
    current_score_surface = game_font.render("0", True, color_score)
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

def colorize_icon(image, color):
    tinted_image = image.copy()
    tinted_image.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
    return tinted_image

def update_icon_colors():
    global menu_img, restart_img, mute_off_img, mute_on_img
    menu_img = colorize_icon(base_menu, color_blade)
    restart_img = colorize_icon(base_restart, color_blade)
    mute_off_img = colorize_icon(base_mute, color_blade)
    mute_on_img = colorize_icon(base_mute, color_miss)

def apply_theme(theme_name):
    global color_blade, color_score, color_miss, color_time, color_bg, current_theme_name
    if theme_name in themes:
        current_theme_name = theme_name
        selected = themes[theme_name]
        color_blade = selected["blade"]
        color_score = selected["score"]
        color_miss  = selected["miss"]
        color_time  = selected["time"]
        color_bg    = selected["bg"]
        update_icon_colors()

def render_texts(score = 0):
    global text_tapto, text_strike, text_taptostart, text_game, text_over, text_hiscore, text_newhiscore, text_taptorestart, high_score_text, score_text
    text_tapto = title_font.render("TAP TO", True, color_time)
    text_strike = title_font.render("STRIKE", True, color_time)
    text_taptostart = text_font.render("TAP TO START!", True, color_blade)
    text_game = title_font.render("GAME", True, color_miss)
    text_over = title_font.render("OVER", True, color_miss)
    text_hiscore = text_font.render("HI- SCORE", True, color_blade)
    text_newhiscore = text_font.render("NEW HI- SCORE!", True, color_score)
    text_taptorestart = text_font.render("TAP TO RESTART!", True, color_blade)
    high_score_text = text_font.render(f"{int(high_score)}", True, color_score)
    score_text = text_font.render(f"SCORE: {int(score)}", True, color_score)


themes = {
    "space odyssey": {
        "blade": (138, 43, 226),
        "score": (255, 215, 0),
        "miss": (255, 69, 0),
        "time": (0, 191, 255),
        "bg": (30, 30, 30)
    },
    "cyberpunk": {
        "blade": (255, 0, 85),
        "score": (0, 255, 255),
        "miss": (255, 255, 0),
        "time": (0, 255, 170),
        "bg": (15, 10, 30)
    },
    "mono": {
        "blade": (200, 200, 200),
        "score": (255, 255, 255),
        "miss": (150, 150, 150),
        "time": (100, 100, 100),
        "bg": (10, 10, 10)
    },
        "soft": {
        "blade": (180, 255, 159),
        "score": (255, 243, 176),
        "miss": (255, 158, 203),
        "time": (155, 231, 255),
        "bg": (22, 18, 31)
    },
        "high contrast": {
        "blade": (0, 255, 0),
        "score": (255, 255, 0),
        "miss": (255, 0, 0),
        "time": (0, 0, 255),
        "bg": (0, 0, 0)
    },
        "pastel": {
        "blade": (255, 159, 159),  # FF9F9F
        "score": (255, 198, 168),  # FFC6A8
        "miss": (255, 227, 163),   # FFE3A3
        "time": (201, 242, 199),   # C9F2C7
        "bg": (139, 211, 230)      # 8BD3E6
    },
        "autumn": {
        "blade": (252, 191, 73),
        "score": (208, 148, 56),
        "miss": (214, 40, 40),
        "time": (234, 226, 183),
        "bg": (0, 48, 73)
    }
}

# Variables
high_score, is_muted, current_theme_name = load_save_data()
color_blade = themes[current_theme_name]["blade"]
color_score = themes[current_theme_name]["score"]
color_miss  = themes[current_theme_name]["miss"]
color_time  = themes[current_theme_name]["time"]
color_bg    = themes[current_theme_name]["bg"]
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
update_icon_colors()
restart_button = restart_img.get_rect(center=(width - 140, 140))
mute_button = mute_on_img.get_rect(center=(width - 140, 140))
menu_button = menu_img.get_rect(center=(140, 140))
game_state = "start"
previous_state = "start"
time_elapsed = 0.0
restart_cooldown = 0.0
shake_duration = 0.0
resume_countdown = 0.0
render_texts()
current_score_surface = game_font.render("0", True, color_score)
running = True
new_record = False

while running:
    dt = clock.tick(FPS) / 1000.0
    if dt > 0.05:
            dt = 0.05
    screen.fill(color_bg)
    screen.blit(menu_img, menu_button)
    
    if game_state == "start":
        screen.blit(text_tapto, text_tapto.get_rect(center=(width // 2, height // 2 - 80)))
        screen.blit(text_strike, text_strike.get_rect(center=(width // 2, height // 2 + 80)))
        screen.blit(text_hiscore, text_hiscore.get_rect(center=(width // 2, 100)))
        screen.blit(high_score_text, high_score_text.get_rect(center=(width // 2, 190)))
        if pygame.time.get_ticks() % 1000 < 500:
            screen.blit(text_taptostart, text_taptostart.get_rect(center=(width // 2, height - 140)))

    elif game_state == "game_over":
        if restart_cooldown > 0:
            restart_cooldown -= dt

        screen.blit(text_game, text_game.get_rect(center=(width // 2, height // 2 - 120)))
        screen.blit(text_over, text_over.get_rect(center=(width // 2, height // 2 + 40)))
        screen.blit(text_hiscore, text_hiscore.get_rect(center=(width // 2, 100)))
        screen.blit(high_score_text, high_score_text.get_rect(center=(width // 2, 190)))
        if pygame.time.get_ticks() % 1000 < 500:
            screen.blit(text_taptorestart, text_taptorestart.get_rect(center=(width // 2, height - 140)))
        if new_record == True: 
            screen.blit(text_newhiscore, text_newhiscore.get_rect(center=(width // 2, height // 2 + 200)))
        else:
            screen.blit(score_text, score_text.get_rect(center=(width // 2, height // 2 + 200)))

    elif game_state == "menu":
        menu_title = title_font.render("THEMES", True, color_score)
        screen.blit(menu_title, menu_title.get_rect(center=(width // 2, 220)))
        if is_muted:
            screen.blit(mute_on_img, mute_button)
        else:
            screen.blit(mute_off_img, mute_button)

        theme_rects = {}
        theme_list = ["cyberpunk", "space odyssey", "soft", "pastel", "autumn", "high contrast", "mono"] 

        start_y = height // 2 - 150
        spacing = 90
    
        for i, t_name in enumerate(theme_list):
            if t_name == current_theme_name:
                text_color = color_blade
            else:
                text_color = (120, 120, 120)
            theme_surf = text_font.render(t_name.upper(), True, text_color)
            t_rect = theme_surf.get_rect(center=(width // 2, start_y + (i * spacing)))
            screen.blit(theme_surf, t_rect)
            theme_rects[t_name] = t_rect

    elif game_state == "resuming":
        resume_countdown -= dt
        count_text = game_font.render(str(math.ceil(resume_countdown)), True, color_time)
        screen.blit(count_text, count_text.get_rect(center=(width // 2, height // 2)))
        
        if resume_countdown <= 0:
            game_state = "playing"

    elif game_state == "playing":
        time_elapsed += dt
        timer -= dt

        shake_x, shake_y = 0, 0
        if shake_duration > 0:
            shake_duration -= dt
            intensity = 8
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
        blade_color = color_blade if abs(blade_velocity) == blade_max_velocity else color_miss
        
        rad = math.radians(blade_angle)
        tip_x = draw_center[0] + blade_length * math.cos(rad)
        tip_y = draw_center[1] - blade_length * math.sin(rad)
        pygame.draw.line(screen, blade_color, draw_center, (tip_x, tip_y), blade_thickness)
        
        if height > width:
            screen.blit(current_score_surface, current_score_surface.get_rect(center=(width // 2, 140)))
        else:
            screen.blit(current_score_surface, current_score_surface.get_rect(center=(200, height // 2)))
        timer_surface = game_font.render(f"{max(0.0, timer):.1f}", True, color_time)
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
        
        if timer <= 0:
            timer = 0
            score_text = text_font.render(f"SCORE: {int(score)}", True, color_score)
            high_score_text = text_font.render(f"{int(high_score)}", True, color_score)
            restart_cooldown = 0.5
            game_state = "game_over"
            if not is_muted: game_over_snd.play()
            if score > high_score:
                high_score = score
                save_game_data(high_score, is_muted, current_theme_name)
                new_record = True


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
        if tap_pos and menu_button.collidepoint(tap_pos):
            if not is_muted: click_snd.play()
            resume_countdown = 3
            if game_state != "menu":
                previous_state = game_state
                game_state = "menu"
            else:
                if previous_state == "playing":
                    game_state = "resuming"
                else:
                    game_state = previous_state

        elif game_state == "menu":
            if tap_pos and mute_button.collidepoint(tap_pos):
                is_muted = not is_muted
                if not is_muted: click_snd.play()
                save_game_data(high_score, is_muted, current_theme_name)
                
            if tap_pos:
                for t_name, t_rect in theme_rects.items():
                    if t_rect.collidepoint(tap_pos):
                        if not is_muted: click_snd.play()
                        apply_theme(t_name)
                        render_texts()
                        save_game_data(high_score, is_muted, current_theme_name)
                        break

        elif game_state == "playing":
            if tap_pos and restart_button.collidepoint(tap_pos):
                if not is_muted: game_over_snd.play()
                restart_game()

            elif abs(blade_velocity) >= blade_max_velocity:
                hit_successful = False 
                for zone in current_frame_zones:
                    if is_blade_hitting_zone(blade_angle, zone):
                        score += 1
                        current_score_surface = game_font.render(f"{int(score)}", True, color_score)
                        if zone.center_angle in angle_cd and angle_cd[zone.center_angle] > 0.3:
                            angle_cd[zone.center_angle] = 0.3
                        if zone in active_zones:
                            active_zones.remove(zone)
                            
                        if zone.color == 0:
                            timer += 2
                            if height > width:
                                floating_texts.append(FloatingText("+2", width // 2, height - 250, color_time))
                            else:
                                floating_texts.append(FloatingText("+2", width - 200, height // 2 - 100, color_time))
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
                    
        elif game_state == "start" or (game_state == "game_over" and restart_cooldown <= 0):
            restart_game()

    pygame.display.update()

pygame.quit()
sys.exit()

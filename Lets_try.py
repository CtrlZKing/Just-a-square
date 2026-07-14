import pygame
import random
import sys
import math
import winsound
import threading

# 1. Initialize
pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Titanium: Infinite Chaos Protocol")
clock = pygame.time.Clock()

# Fonts
font_small = pygame.font.SysFont("Arial", 26)
font_big = pygame.font.SysFont("Arial", 75, bold=True)
font_msg = pygame.font.SysFont("Verdana", 35, bold=True)
font_warn = pygame.font.SysFont("Arial", 50, bold=True)

# --- SOUND SYSTEM ---
def play_beep(freq, dur):
    def beep():
        try: winsound.Beep(freq, dur)
        except: pass
    threading.Thread(target=beep, daemon=True).start()

# --- LASER CLASS ---
class Laser:
    def __init__(self, target_rect, is_intentional=False):
        self.state = "WARNING"
        self.start_time = pygame.time.get_ticks()
        if is_intentional:
            # Player ki location ko aim karega
            self.p1 = (random.choice([0, WIDTH]), random.randint(0, HEIGHT))
            dx = target_rect.centerx - self.p1[0]
            dy = target_rect.centery - self.p1[1]
            self.p2 = (self.p1[0] + dx * 10, self.p1[1] + dy * 10)
        else:
            # Random Spread
            if random.random() > 0.5:
                self.p1 = (random.randint(50, WIDTH-50), 20)
                self.p2 = (random.randint(50, WIDTH-50), HEIGHT-100)
            else:
                self.p1 = (20, random.randint(50, HEIGHT-100))
                self.p2 = (WIDTH-20, random.randint(50, HEIGHT-100))
            
    def update(self):
        now = pygame.time.get_ticks()
        if self.state == "WARNING" and now - self.start_time > 1500:
            self.state = "ATTACK"; self.start_time = now
            play_beep(1200, 50)
        return not (self.state == "ATTACK" and now - self.start_time > 400)

    def draw(self, surf):
        if self.state == "WARNING":
            pygame.draw.line(surf, (150, 0, 0), self.p1, self.p2, 2)
        else:
            for i in range(4):
                pygame.draw.line(surf, (0, 180, 255), self.p1, self.p2, 14 - i*2)
            pygame.draw.line(surf, (255, 255, 255), self.p1, self.p2, 2)

# Global Variables
square_pos = pygame.Rect(375, 275, 40, 40)
health = 100; score = 0; game_over = False; flicker_timer = 0 

# Charger Data (Supports multiple chargers after 150)
enemy_data = [{"pos":[-200,-200], "state":"WAITING", "vel":[0,0], "ang":0, "warn":(0,0), "timer":0},
              {"pos":[-200,-200], "state":"WAITING", "vel":[0,0], "ang":0, "warn":(0,0), "timer":0}]

laser_list = []; laser_timer = 0
dot = pygame.Rect(random.randint(50, 750), random.randint(50, 500), 15, 15)
gold_dot = pygame.Rect(-100, -100, 25, 25); is_gold_active = False; gold_timer = 0; dots_collected = 0
show_intro = True; intro_timer = pygame.time.get_ticks(); event_started = False; diag_idx = 0; text_y = -100
dialogues = ["Having fun?", "Or finding it hard already?", "this is just the start"]
border_rect = pygame.Rect(10, 10, WIDTH-20, HEIGHT-80)

def reset_game():
    global score, health, game_over, event_started, diag_idx, text_y, laser_list, dots_collected, is_gold_active, show_intro, intro_timer
    score = 0; health = 100; game_over = False; show_intro = True; event_started = False; diag_idx = 0; text_y = -100
    laser_list = []; dots_collected = 0; is_gold_active = False; intro_timer = pygame.time.get_ticks()
    square_pos.topleft = (375, 275)
    for e in enemy_data: e["state"] = "WAITING"; e["pos"] = [-200, -200]; e["timer"] = 0

# --- MAIN LOOP ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r: reset_game()

    if not game_over:
        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] and square_pos.top > border_rect.top: square_pos.y -= 6
        if keys[pygame.K_DOWN] and square_pos.bottom < border_rect.bottom: square_pos.y += 6
        if keys[pygame.K_LEFT] and square_pos.left > border_rect.left: square_pos.x -= 6
        if keys[pygame.K_RIGHT] and square_pos.right < border_rect.right: square_pos.x += 6

        if show_intro and now - intro_timer > 3000: show_intro = False
        
        # Start Dialogue Event at 50 points
        if score >= 50 and not event_started: 
            event_started = True; event_start_time = now
            for e in enemy_data: e["state"] = "WAITING"; e["pos"] = [-200, -200]

        if event_started and diag_idx < len(dialogues):
            if text_y < 60: text_y += 4
            if now - event_start_time > 2500: diag_idx += 1; event_start_time = now
        elif event_started and diag_idx >= len(dialogues):
            if text_y > -150: text_y -= 8

        is_text_active = event_started and (diag_idx < len(dialogues) or text_y > -100)
        attacks_allowed = not is_text_active and not show_intro

        if attacks_allowed:
            # --- LASER LOGIC ---
            if score >= 50:
                if now - laser_timer > 2200:
                    num = 1; aim = False
                    if score >= 120:
                        num = random.randint(1, 5)
                        aim = True if num <= 2 else False
                    elif score >= 100:
                        num = 2; aim = True
                    elif score >= 80:
                        num = 2; aim = False
                    else: # 50-79
                        num = 1; aim = False
                    
                    for _ in range(num): laser_list.append(Laser(square_pos, aim))
                    laser_timer = now
            
            for l in laser_list[:]:
                if not l.update(): laser_list.remove(l)
                elif l.state == "ATTACK" and square_pos.clipline(l.p1, l.p2): health -= 4; flicker_timer = 5

            # --- CHARGER LOGIC (Infinite Survival Mode) ---
            # Score 10+ (Pre-Event) or Score 150+ (Endless Chaos)
            if (score >= 10 and not event_started) or score >= 150:
                num_enemies = 2 if score >= 150 else 1
                for i in range(num_enemies):
                    e = enemy_data[i]
                    if e["state"] == "WAITING" and now - e["timer"] > 1500:
                        play_beep(400, 80)
                        side = random.choice(['top', 'bottom', 'left', 'right'])
                        if side == 'top': e["pos"] = [random.randint(50,WIDTH-50), -70]; e["warn"] = (e["pos"][0], 40)
                        elif side == 'bottom': e["pos"] = [random.randint(50,WIDTH-50), HEIGHT+70]; e["warn"] = (e["pos"][0], HEIGHT-120)
                        elif side == 'left': e["pos"] = [-70, random.randint(50,HEIGHT-50)]; e["warn"] = (40, e["pos"][1])
                        else: e["pos"] = [WIDTH+70, random.randint(50,HEIGHT-50)]; e["warn"] = (WIDTH-40, e["pos"][1])
                        
                        dx, dy = square_pos.centerx-e["pos"][0], square_pos.centery-e["pos"][1]
                        dist = math.hypot(dx, dy); e["vel"] = [dx/dist*13, dy/dist*13]
                        e["ang"] = math.degrees(math.atan2(-dy, dx))
                        e["state"] = "LOCKING" if score >= 150 else "CHARGING"
                        e["timer"] = now
                    elif e["state"] == "LOCKING" and now - e["timer"] > 1000:
                        e["state"] = "CHARGING"
                    elif e["state"] == "CHARGING":
                        e["pos"][0] += e["vel"][0]; e["pos"][1] += e["vel"][1]
                        if (e["pos"][0] < -300 or e["pos"][0] > WIDTH+300 or e["pos"][1] < -300 or e["pos"][1] > HEIGHT+300):
                            e["state"] = "WAITING"; e["timer"] = now
                        if square_pos.colliderect(pygame.Rect(e["pos"][0]-25, e["pos"][1]-25, 50, 50)): health -= 2; flicker_timer = 5

            # --- DOTS ---
            if square_pos.colliderect(dot):
                play_beep(1000, 20); score += 1; dots_collected += 1
                dot.topleft = (random.randint(50, 750), random.randint(50, 500))
                if dots_collected >= 15:
                    is_gold_active = True; gold_timer = now; dots_collected = 0
                    gold_dot.topleft = (random.randint(100, 700), random.randint(100, 500))
            if is_gold_active:
                if now - gold_timer > 3000: is_gold_active = False; gold_dot.topleft = (-100, -100)
                elif square_pos.colliderect(gold_dot):
                    play_beep(1800, 100); score += 5; health = min(100, health+25); is_gold_active = False

        if health <= 0: game_over = True; play_beep(200, 600)

    # --- DRAWING ---
    screen.fill("black")
    pygame.draw.rect(screen, "white", border_rect, 2)
    if not game_over:
        pygame.draw.rect(screen, "red", square_pos)
        if attacks_allowed:
            pygame.draw.rect(screen, "green", dot)
            if is_gold_active: pygame.draw.rect(screen, "gold", gold_dot)
            for e in enemy_data:
                if e["state"] == "LOCKING": screen.blit(font_warn.render("!", True, "red"), (e["warn"][0]-10, e["warn"][1]-20))
                if e["state"] == "CHARGING":
                    m_surf = pygame.Surface((55, 55), pygame.SRCALPHA)
                    pygame.draw.polygon(m_surf, (255, 200, 0), [(0, 0), (55, 27), (0, 55)])
                    pygame.draw.circle(m_surf, (255, 0, 0), (14, 27), 6) # Red Eye
                    rot_m = pygame.transform.rotate(m_surf, e["ang"])
                    screen.blit(rot_m, rot_m.get_rect(center=(int(e["pos"][0]), int(e["pos"][1]))))
            for l in laser_list: l.draw(screen)
        
        if show_intro:
            screen.blit(font_msg.render("WELCOME TO THE GAME", True, "white"), (WIDTH//2-250, HEIGHT//2-60))
            screen.blit(font_msg.render("SURVIVE IF YOU CAN!", True, "red"), (WIDTH//2-230, HEIGHT//2+10))
        if is_text_active and diag_idx < len(dialogues):
            t_surf = font_msg.render(dialogues[diag_idx], True, (255, 50, 50))
            screen.blit(t_surf, t_surf.get_rect(center=(WIDTH//2, text_y)))
        
        # UI
        b_color = (255, 0, 0) if flicker_timer > 0 else (0, 255, 0)
        pygame.draw.rect(screen, b_color, (20, HEIGHT - 40, max(0, health * 2), 20))
        screen.blit(font_small.render(f"Score: {score}", True, "white"), (240, HEIGHT - 45))
        if flicker_timer > 0: flicker_timer -= 1
    else:
        screen.fill((40, 0, 0))
        screen.blit(font_big.render("GAME OVER", True, "white"), (WIDTH//2 - 200, HEIGHT//2 - 80))
        screen.blit(font_small.render(f"FINAL SCORE: {score}", True, "yellow"), (WIDTH//2 - 80, HEIGHT//2 + 20))
        screen.blit(font_small.render("Press 'R' to Restart", True, "white"), (WIDTH//2 - 100, HEIGHT//2 + 70))

    pygame.display.flip(); clock.tick(60)

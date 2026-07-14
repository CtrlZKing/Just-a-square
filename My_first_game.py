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
pygame.display.set_caption("Titanium: Chaos Protocol v2")
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

# --- CLASSES ---
class Laser:
    def __init__(self, target_rect, is_intentional=False):
        self.state = "WARNING"
        self.start_time = pygame.time.get_ticks()
        if is_intentional:
            self.p1 = (random.choice([0, WIDTH]), random.randint(0, HEIGHT))
            dx = target_rect.centerx - self.p1[0]
            dy = target_rect.centery - self.p1[1]
            self.p2 = (self.p1[0] + dx * 10, self.p1[1] + dy * 10)
        else:
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

class Saw:
    def __init__(self):
        self.size = 100 
        side = random.choice(['L', 'R'])
        spawn_x = -120 if side == 'L' else WIDTH + 120
        self.pos = pygame.Vector2(spawn_x, random.randint(150, HEIGHT-250))
        self.vel = pygame.Vector2(random.randint(7, 9) if side == 'L' else random.randint(-9, -7), 
                                  random.choice([-6, 6]))
        self.bounces = 0
        self.angle = 0
    
    def update(self):
        self.pos.x += self.vel.x
        self.pos.y += self.vel.y
        self.angle += 15
        if self.bounces < 3:
            if self.pos.x <= 15 or self.pos.x >= WIDTH - self.size - 15:
                self.vel.x *= -1; self.bounces += 1
            if self.pos.y <= 15 or self.pos.y >= HEIGHT - 100:
                self.vel.y *= -1; self.bounces += 1
        return not (self.bounces >= 3 and (self.pos.x < -200 or self.pos.x > WIDTH + 200))

    def draw(self, surf):
        center = (int(self.pos.x + self.size/2), int(self.pos.y + self.size/2))
        for i in range(12):
            rad = math.radians(self.angle + i * 30)
            p2 = (center[0] + math.cos(rad) * (self.size/2), center[1] + math.sin(rad) * (self.size/2))
            pygame.draw.line(surf, (120, 120, 120), center, p2, 6)
        pygame.draw.circle(surf, (80, 80, 80), center, self.size/2 - 12)

# Global Variables
square_pos = pygame.Rect(375, 275, 40, 40)
health = 100; score = 0; game_over = False; flicker_timer = 0 
enemy_data = [{"pos":[-200,-200], "state":"WAITING", "vel":[0,0], "ang":0, "warn":(0,0), "timer":0},
              {"pos":[-200,-200], "state":"WAITING", "vel":[0,0], "ang":0, "warn":(0,0), "timer":0}]
laser_list = []; saw_list = []; laser_timer = 0; saw_timer = 0
dot = pygame.Rect(random.randint(50, 750), random.randint(50, 500), 15, 15)
gold_dot = pygame.Rect(-100, -100, 25, 25); is_gold_active = False; gold_timer = 0; dots_collected = 0
show_intro = True; intro_timer = pygame.time.get_ticks(); event_started = False; diag_idx = 0; text_y = -100
dialogues = ["Having fun?", "Or finding it hard already?", "this is just the start"]
border_rect = pygame.Rect(10, 10, WIDTH-20, HEIGHT-80)

def reset_game():
    global score, health, game_over, event_started, diag_idx, text_y, laser_list, saw_list, dots_collected, is_gold_active, show_intro, intro_timer
    score = 0; health = 100; game_over = False; show_intro = True; event_started = False; diag_idx = 0; text_y = -100
    laser_list = []; saw_list = []; dots_collected = 0; is_gold_active = False; intro_timer = pygame.time.get_ticks()
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
        if score >= 50 and not event_started: event_started = True; event_start_time = now

        # Dialogue Logic
        if event_started and diag_idx < len(dialogues):
            if text_y < 60: text_y += 4
            if now - event_start_time > 2500: diag_idx += 1; event_start_time = now
        elif event_started and diag_idx >= len(dialogues):
            if text_y > -150: text_y -= 8

        # Block everything while text is moving/active
        is_text_present = event_started and (diag_idx < len(dialogues) or text_y > -100)
        attacks_active = not is_text_present and not show_intro

        if attacks_active:
            # --- 180+ SAW MODE ---
            if score >= 180:
                laser_list = []
                for e in enemy_data: e["state"] = "WAITING"; e["pos"] = [-500, -500]
                if len(saw_list) == 0 and now - saw_timer > 2000:
                    saw_list.append(Saw()); saw_list.append(Saw()); saw_timer = now
                for s in saw_list[:]:
                    if not s.update(): saw_list.remove(s); saw_timer = now
                    else:
                        s_rect = pygame.Rect(s.pos.x + 10, s.pos.y + 10, s.size - 20, s.size - 20)
                        if square_pos.colliderect(s_rect): health -= 5; flicker_timer = 5
            
            # --- NORMAL ATTACK MODE ---
            else:
                if 50 <= score < 180:
                    if now - laser_timer > 2000:
                        num = random.randint(1, 4) if score >= 120 else (2 if score >= 80 else 1)
                        track = True if (score >= 100 and random.random() > 0.5) else False
                        for _ in range(num): laser_list.append(Laser(square_pos, track))
                        laser_timer = now
                for l in laser_list[:]:
                    if not l.update(): laser_list.remove(l)
                    elif l.state == "ATTACK" and square_pos.clipline(l.p1, l.p2): health -= 4; flicker_timer = 5

                # Chargers with RED EYE
                if (10 <= score < 50) or (150 <= score < 180):
                    max_enemies = 1 if score < 50 else 2
                    for i in range(max_enemies):
                        e = enemy_data[i]
                        if e["state"] == "WAITING" and now - e["timer"] > 1000:
                            play_beep(400, 80)
                            side = random.choice(['top', 'bottom', 'left', 'right'])
                            if side == 'top': e["pos"] = [random.randint(50,WIDTH-50), -70]; e["warn"] = (e["pos"][0], 40)
                            elif side == 'bottom': e["pos"] = [random.randint(50,WIDTH-50), HEIGHT+70]; e["warn"] = (e["pos"][0], HEIGHT-120)
                            elif side == 'left': e["pos"] = [-70, random.randint(50,HEIGHT-50)]; e["warn"] = (40, e["pos"][1])
                            else: e["pos"] = [WIDTH+70, random.randint(50,HEIGHT-50)]; e["warn"] = (WIDTH-40, e["pos"][1])
                            e["state"] = "LOCKING" if score >= 50 else "CHARGING"
                            if e["state"] == "CHARGING":
                                dx, dy = square_pos.centerx-e["pos"][0], square_pos.centery-e["pos"][1]
                                dist = math.hypot(dx, dy); e["vel"] = [dx/dist*13, dy/dist*13]
                                e["ang"] = math.degrees(math.atan2(-dy, dx))
                            e["timer"] = now
                        elif e["state"] == "LOCKING" and now - e["timer"] > 1000:
                            dx, dy = square_pos.centerx-e["pos"][0], square_pos.centery-e["pos"][1]
                            dist = math.hypot(dx, dy); e["vel"] = [dx/dist*13, dy/dist*13]
                            e["ang"] = math.degrees(math.atan2(-dy, dx)); e["state"] = "CHARGING"
                        elif e["state"] == "CHARGING":
                            e["pos"][0] += e["vel"][0]; e["pos"][1] += e["vel"][1]
                            if (e["pos"][0] < -300 or e["pos"][0] > WIDTH+300 or e["pos"][1] < -300 or e["pos"][1] > HEIGHT+300):
                                e["state"] = "WAITING"; e["timer"] = now
                            if square_pos.colliderect(pygame.Rect(e["pos"][0]-25, e["pos"][1]-25, 50, 50)): health -= 2; flicker_timer = 5

        # Dots (Only if text is not there)
        if attacks_active:
            if square_pos.colliderect(dot):
                play_beep(1000, 20); score += 1; dots_collected += 1
                dot.topleft = (random.randint(50, 750), random.randint(50, 500))
                if dots_collected >= 15:
                    is_gold_active = True; gold_timer = now; dots_collected = 0
                    gold_dot.topleft = (random.randint(100, 700), random.randint(100, 500))
            if is_gold_active:
                if now - gold_timer > 3000: is_gold_active = False; gold_dot.topleft = (-100, -100)
                elif square_pos.colliderect(gold_dot):
                    play_beep(1800, 100); score += 5; health = min(100, health+25); is_gold_active = False; gold_dot.topleft = (-100, -100)

        if health <= 0: game_over = True; play_beep(200, 600)

    # --- DRAWING ---
    screen.fill("black")
    if not game_over:
        pygame.draw.rect(screen, "white", border_rect, 2)
        pygame.draw.rect(screen, "red", square_pos)
        
        if attacks_active:
            pygame.draw.rect(screen, "green", dot)
            if is_gold_active: pygame.draw.rect(screen, "gold", gold_dot)
            for e in enemy_data:
                if e["state"] == "LOCKING": screen.blit(font_warn.render("!", True, "red"), (e["warn"][0]-10, e["warn"][1]-20))
                if e["state"] == "CHARGING":
                    m_surf = pygame.Surface((55, 55), pygame.SRCALPHA)
                    pygame.draw.polygon(m_surf, (255, 200, 0), [(0, 0), (55, 27), (0, 55)])
                    # RED EYE ADDED BACK
                    pygame.draw.circle(m_surf, (255, 0, 0), (14, 27), 6) 
                    rot_m = pygame.transform.rotate(m_surf, e["ang"]); screen.blit(rot_m, rot_m.get_rect(center=(int(e["pos"][0]), int(e["pos"][1]))))
            for l in laser_list: l.draw(screen)
            for s in saw_list: s.draw(screen)
        
        if show_intro:
            screen.blit(font_msg.render("Welcome to the Game", True, "white"), (WIDTH//2-190, HEIGHT//2-60))
            screen.blit(font_msg.render("Survive if u Can", True, "red"), (WIDTH//2-145, HEIGHT//2+10))
        
        if is_text_present and diag_idx < len(dialogues):
            t_surf = font_msg.render(dialogues[diag_idx], True, (255, 50, 50))
            screen.blit(t_surf, t_surf.get_rect(center=(WIDTH//2, text_y)))
        
        pygame.draw.rect(screen, (0,255,0) if flicker_timer==0 else (255,0,0), (20, HEIGHT-40, max(0, health*2), 20))
        screen.blit(font_small.render(f"Score: {score}", True, "white"), (240, HEIGHT-45))
        if flicker_timer > 0: flicker_timer -= 1
    else:
        screen.fill((150, 0, 0))
        screen.blit(font_big.render("GAME OVER", True, "white"), (WIDTH//2-200, HEIGHT//2-100))
        screen.blit(font_msg.render(f"Final Score: {score}", True, "white"), (WIDTH//2-120, HEIGHT//2))
        screen.blit(font_small.render("Press 'R' to Restart", True, "white"), (WIDTH//2-100, HEIGHT//2+80))

    pygame.display.flip(); clock.tick(60)

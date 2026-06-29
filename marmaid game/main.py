import pygame
import sys
import math
import os
import array
import struct
import random
from PIL import Image

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Game Window Constants
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dreamy Anime Mermaid Dress-Up")

# Colors
OCEAN_BLUE = (10, 25, 50)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
PINK = (255, 105, 180)
CYAN = (0, 255, 255)
PURPLE = (147, 112, 219)
GREEN = (50, 205, 50)
GLASS_BG = (15, 25, 45, 200) # RGBA glassmorphism background
GLASS_BORDER = (255, 255, 255, 80)

# Fonts
try:
    font_title = pygame.font.SysFont("Trebuchet MS", 45, bold=True)
    font_subtitle = pygame.font.SysFont("Trebuchet MS", 28, italic=True)
    font_ui = pygame.font.SysFont("Arial", 16, bold=True)
    font_ui_small = pygame.font.SysFont("Arial", 12)
    font_desc = pygame.font.SysFont("Arial", 14)
except:
    font_title = pygame.font.Font(None, 50)
    font_subtitle = pygame.font.Font(None, 32)
    font_ui = pygame.font.Font(None, 20)
    font_ui_small = pygame.font.Font(None, 14)
    font_desc = pygame.font.Font(None, 16)

# ----------------------------------------------------
# 1. Synthesize Audio (Music & Bubble Pop Sound)
# ----------------------------------------------------
def generate_ambient_music():
    sample_rate = 22050
    duration = 12.0 # 12 seconds loop
    num_samples = int(sample_rate * duration)
    
    # Atmospheric, music-box-like chord progression
    # Cmaj9 -> Am9 -> Fmaj9 -> G6/9
    chords = [
        [261.63, 329.63, 392.00, 493.88, 587.33],  # C4, E4, G4, B4, D5 (Cmaj9)
        [220.00, 261.63, 329.63, 392.00, 493.88],  # A3, C4, E4, G4, B4 (Am9)
        [174.61, 220.00, 261.63, 329.63, 392.00],  # F3, A3, C4, E4, G4 (Fmaj9)
        [196.00, 246.94, 293.66, 329.63, 440.00]   # G3, B3, D4, E4, A4 (G6/9)
    ]
    
    # 12 seconds / 4 chords = 3 seconds per chord.
    # 6 beats per chord, beat duration = 0.5s (120 BPM)
    beat_duration = 0.5
    
    samples = [0.0] * num_samples
    wave_rand = random.Random(42)
    
    for i in range(num_samples):
        t = i / sample_rate
        
        # 1. Soothing Ambient Ocean Waves (filtered noise sweep)
        mod_val = (math.sin(2 * math.pi * t / 6.0) + 1.0) * 0.5
        noise = wave_rand.uniform(-1.0, 1.0) * mod_val * 0.08
        
        # 2. Arpeggiator Melody
        chord_idx = int(t / 3.0) % len(chords)
        chord_notes = chords[chord_idx]
        
        chord_time = t % 3.0
        beat_idx = int(chord_time / beat_duration)
        
        # Notes pattern for a 6-beat arpeggio
        pattern = [0, 1, 2, 3, 4, 2]
        note_idx = pattern[beat_idx % len(pattern)]
        freq = chord_notes[note_idx]
        
        t_note = chord_time % beat_duration
        
        # Pluck envelope
        envelope = math.exp(-6.0 * t_note)
        
        # Bell harmonics
        bell = math.sin(2 * math.pi * freq * t)
        bell += 0.35 * math.sin(2 * math.pi * (freq * 2.0) * t)
        bell += 0.15 * math.sin(2 * math.pi * (freq * 3.0) * t)
        
        melody_sample = bell * envelope * 0.28
        
        samples[i] = noise + melody_sample
        
    # 3. Echo / Delay Line
    delay_time = 0.375 # dotted 8th echo
    delay_samples = int(sample_rate * delay_time)
    decay_factor = 0.45
    
    final_samples = array.array('h', [0] * num_samples)
    for i in range(num_samples):
        val = samples[i]
        if i >= delay_samples:
            val += samples[i - delay_samples] * decay_factor
            
        val_int = int(val * 16000)
        val_int = max(-32768, min(32767, val_int))
        final_samples[i] = val_int
        
    return pygame.mixer.Sound(buffer=bytes(final_samples))

def generate_bubble_pop():
    sample_rate = 22050
    duration = 0.12
    num_samples = int(sample_rate * duration)
    samples = array.array('h', [0] * num_samples)
    
    for i in range(num_samples):
        t = i / sample_rate
        # Upward sweep frequency for classic pop
        freq = 300 + 1200 * (t / duration)
        envelope = (1.0 - t / duration) ** 2.5
        val = math.sin(2 * math.pi * freq * t) * envelope * 12000
        samples[i] = int(val)
        
    return pygame.mixer.Sound(buffer=bytes(samples))

# Initialize Audio Sounds
try:
    music_sound = generate_ambient_music()
    pop_sound = generate_bubble_pop()
    music_sound.play(loops=-1)
    music_playing = True
except Exception as e:
    print(f"Sound initialization failed: {e}")
    music_playing = False
    pop_sound = None

# ----------------------------------------------------
# 2. Image Processing & Character Generation
# ----------------------------------------------------
def rotate_hue(image_path, angle):
    """Loads an image, rotates its hue, and returns a Pygame Surface with transparency."""
    if not os.path.exists(image_path):
        print(f"Error: Image {image_path} not found!")
        # Fallback surface
        surf = pygame.Surface((400, 500), pygame.SRCALPHA)
        pygame.draw.rect(surf, (200, 200, 200), [50, 50, 300, 400], border_radius=20)
        return surf
    
    img = Image.open(image_path).convert("RGBA")
    if angle != 0:
        # Convert to HSV, shift Hue, convert back
        r, g, b, a = img.split()
        hsv = img.convert("HSV")
        h, s, v = hsv.split()
        h = h.point(lambda x: (x + int(angle * 255 / 360)) % 256)
        hsv_new = Image.merge("HSV", (h, s, v))
        rgb_new = hsv_new.convert("RGB")
        img = Image.merge("RGBA", rgb_new.split() + (a,))
        
    # Convert PIL Image to Pygame Surface
    mode = img.mode
    size = img.size
    data = img.tobytes()
    return pygame.image.frombuffer(data, size, mode)

# ----------------------------------------------------
# 3. Particle Systems (Floating Bubbles & Stars)
# ----------------------------------------------------
class BubbleParticle:
    def __init__(self, is_ui=False):
        self.is_ui = is_ui
        self.reset()
        
    def reset(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(HEIGHT, HEIGHT + 100)
        self.radius = random.randint(2, 8)
        self.speed_y = random.uniform(0.8, 2.5)
        self.speed_x_amp = random.uniform(0.2, 0.8)
        self.speed_x_freq = random.uniform(1.0, 3.0)
        self.alpha = random.randint(50, 150)
        self.color = (180, 230, 255, self.alpha)
        self.wobble_offset = random.uniform(0, 2 * math.pi)

    def update(self):
        self.y -= self.speed_y
        self.x += math.sin(pygame.time.get_ticks() * 0.002 * self.speed_x_freq + self.wobble_offset) * self.speed_x_amp
        # Reset bubble when it floats off screen
        if self.y < -20:
            self.reset()

    def draw(self, surface):
        # Create a transparent surface for the bubble
        bubble_surf = pygame.Surface((self.radius * 2 + 2, self.radius * 2 + 2), pygame.SRCALPHA)
        # Main bubble body
        pygame.draw.circle(bubble_surf, self.color, (self.radius, self.radius), self.radius, 1)
        # Highlight reflection
        pygame.draw.circle(bubble_surf, (255, 255, 255, self.alpha + 50), 
                           (self.radius - int(self.radius*0.3), self.radius - int(self.radius*0.3)), 
                           max(1, int(self.radius * 0.3)))
        surface.blit(bubble_surf, (int(self.x - self.radius), int(self.y - self.radius)))

class StarParticle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-1.0, 1.0)
        self.vy = random.uniform(-2.5, -0.5)
        self.life = 1.0 # starts full, fades out
        self.decay = random.uniform(0.015, 0.035)
        self.radius = random.randint(2, 4)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay

    def draw(self, surface):
        if self.life > 0:
            alpha = int(self.life * 255)
            c = (self.color[0], self.color[1], self.color[2], alpha)
            star_surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(star_surf, c, (self.radius, self.radius), self.radius)
            # Add star glow
            pygame.draw.circle(star_surf, (255, 255, 255, int(alpha * 0.5)), (self.radius, self.radius), self.radius * 2)
            surface.blit(star_surf, (int(self.x - self.radius), int(self.y - self.radius)))

# Instantiate bubble list
bubbles = [BubbleParticle() for _ in range(35)]
star_particles = []

# ----------------------------------------------------
# 4. Character Offsets & Configuration
# ----------------------------------------------------
CHARACTERS = {
    0: {
        "name": "Aria",
        "title": "Songstress of Sunlit Reefs",
        "quality": "Joyful melody & golden warmth",
        "base_file": "assets/char_aria_trans.png",
        "hue": 0,
        "bg_color": (255, 240, 200),
        "head": (200, 160),
        "chest": (202, 310),
        "waist": (202, 415),
        "hand": (105, 335)
    },
    1: {
        "name": "Coralia",
        "title": "Guardian of the Sea Creatures",
        "quality": "Caring, bubbly & pastel pink",
        "base_file": "assets/char_aria_trans.png",
        "hue": 310,
        "bg_color": (255, 218, 224),
        "head": (200, 160),
        "chest": (202, 310),
        "waist": (202, 415),
        "hand": (105, 335)
    },
    2: {
        "name": "Kailani",
        "title": "Free Spirit of Wild Waves",
        "quality": "Playful, energetic & golden tan",
        "base_file": "assets/char_aria_trans.png",
        "hue": 25,
        "bg_color": (255, 228, 196),
        "head": (200, 160),
        "chest": (202, 310),
        "waist": (202, 415),
        "hand": (105, 335)
    },
    3: {
        "name": "Naida",
        "title": "Keeper of Bioluminescent Deep",
        "quality": "Mysterious, quiet & ocean-wise",
        "base_file": "assets/char_naida_trans.png",
        "hue": 0,
        "bg_color": (210, 200, 255),
        "head": (200, 142),
        "chest": (200, 290),
        "waist": (200, 400),
        "hand": (95, 315)
    },
    4: {
        "name": "Serena",
        "title": "Princess of the Pearl Caves",
        "quality": "Elegant grace & glowing pearl aura",
        "base_file": "assets/char_naida_trans.png",
        "hue": 140,
        "bg_color": (200, 240, 255),
        "head": (200, 142),
        "chest": (200, 290),
        "waist": (200, 400),
        "hand": (95, 315)
    }
}

# ----------------------------------------------------
# 5. Programmatic Wardrobe Drawing Methods
# ----------------------------------------------------
def draw_dreamy_tail(surface, waist_pos, color_theme, time_val, index):
    """
    Draws a beautifully animated, swaying tail programmatically.
    waist_pos: (x, y) where the tail starts
    color_theme: Color tuple (R,G,B) for the primary tail
    """
    # Define colors
    base_color = color_theme
    glow_color = tuple(min(255, c + 80) for c in base_color)
    dark_color = tuple(max(0, c - 60) for c in base_color)
    
    # Calculate sway offsets using sine wave propagation
    num_segments = 12
    points = []
    
    # Anchor point at waist
    points.append(waist_pos)
    
    # Sway intensity increases down the tail
    current_x, current_y = waist_pos
    for i in range(1, num_segments):
        # Sine wave offset: propagation factor based on time and segment index
        sway_factor = i * 2.8
        sway_x = math.sin(time_val * 3.5 + i * 0.45) * sway_factor
        
        # Segment position down the tail
        segment_len = 16 if i < 6 else 14
        current_y += segment_len
        current_x = waist_pos[0] + sway_x
        
        # Add slight curl based on index
        if index == 0: # Aria: standard mermaid curve
            current_x += (i ** 1.3) * 0.6
        elif index == 1: # Coralia: cute curled tail
            current_x += math.sin(i * 0.2) * 12
        elif index == 3: # Naida: bioluminescent deep curve
            current_x -= (i ** 1.4) * 0.4
            
        points.append((current_x, current_y))
        
    # 1. Draw Tail Body segments (tapering down)
    tail_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    # Draw scale shadow layers
    for i in range(len(points) - 1, 0, -1):
        pt = points[i]
        # Calculate width of tail at this segment (tapers down)
        r = int(32 * (1.0 - (i / num_segments) * 0.75))
        
        # Color gradient down the tail
        t_grad = i / num_segments
        c_seg = (
            int(base_color[0] * (1 - t_grad) + dark_color[0] * t_grad),
            int(base_color[1] * (1 - t_grad) + dark_color[1] * t_grad),
            int(base_color[2] * (1 - t_grad) + dark_color[2] * t_grad)
        )
        
        # Draw base tail muscle
        pygame.draw.circle(tail_surf, c_seg, (int(pt[0]), int(pt[1])), r)
        # Highlight highlight on the left
        pygame.draw.circle(tail_surf, glow_color, (int(pt[0] - r * 0.3), int(pt[1] - r * 0.2)), int(r * 0.5))
        pygame.draw.circle(tail_surf, c_seg, (int(pt[0] - r * 0.2), int(pt[1] - r * 0.1)), int(r * 0.48))
        
    # Draw scales detail (glowing ripples)
    for i in range(1, len(points) - 2):
        pt = points[i]
        r = int(32 * (1.0 - (i / num_segments) * 0.75))
        # Draw scales arcs
        scale_c = (glow_color[0], glow_color[1], glow_color[2], 120)
        pygame.draw.arc(tail_surf, scale_c, 
                        [int(pt[0] - r), int(pt[1] - r*0.5), r*2, r], 
                        3.14, 0, 2)
        
    # 2. Draw animated, translucent, flowy fins at the end of the tail
    end_pt = points[-1]
    fin_time = time_val * 4.2
    
    # Different fin shapes based on tail index
    fin_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    # Let's draw double fins
    fin_left = [
        end_pt,
        (end_pt[0] - 60 - math.sin(fin_time)*10, end_pt[1] + 30 + math.cos(fin_time)*5),
        (end_pt[0] - 75 - math.sin(fin_time)*12, end_pt[1] + 70 - math.sin(fin_time)*5),
        (end_pt[0] - 30, end_pt[1] + 80),
        (end_pt[0] - 5, end_pt[1] + 45)
    ]
    fin_right = [
        end_pt,
        (end_pt[0] + 60 + math.sin(fin_time)*10, end_pt[1] + 30 + math.cos(fin_time)*5),
        (end_pt[0] + 75 + math.sin(fin_time)*12, end_pt[1] + 70 - math.sin(fin_time)*5),
        (end_pt[0] + 30, end_pt[1] + 80),
        (end_pt[0] + 5, end_pt[1] + 45)
    ]
    
    fin_color_alpha = (glow_color[0], glow_color[1], glow_color[2], 150)
    fin_color_alpha2 = (base_color[0], base_color[1], base_color[2], 100)
    
    # Draw translucent fins layers
    pygame.draw.polygon(fin_surf, fin_color_alpha, fin_left)
    pygame.draw.polygon(fin_surf, fin_color_alpha, fin_right)
    # Inner overlay
    pygame.draw.polygon(fin_surf, fin_color_alpha2, 
                        [end_pt, fin_left[1], (end_pt[0] - 20, end_pt[1]+40)])
    pygame.draw.polygon(fin_surf, fin_color_alpha2, 
                        [end_pt, fin_right[1], (end_pt[0] + 20, end_pt[1]+40)])
    
    # Draw lines on fins for texture
    for f_pts in [fin_left, fin_right]:
        pygame.draw.line(fin_surf, (255,255,255,180), end_pt, f_pts[1], 2)
        pygame.draw.line(fin_surf, (255,255,255,180), end_pt, f_pts[2], 2)
        pygame.draw.line(fin_surf, (255,255,255,180), end_pt, f_pts[3], 2)

    # Emit tail-fin sparkling particles in play mode
    if random.random() < 0.18:
        star_particles.append(StarParticle(end_pt[0] + random.randint(-15, 15), end_pt[1], base_color))

    surface.blit(tail_surf, (0, 0))
    surface.blit(fin_surf, (0, 0))

def draw_anime_top(surface, chest_pos, color_theme, style_index):
    """
    Draws a cute, anime-style top on the chest.
    chest_pos: (x, y) coordinates of the chest center
    color_theme: Primary color
    """
    top_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    cx, cy = chest_pos
    
    # Color variants
    base = color_theme
    highlight = tuple(min(255, c + 70) for c in base)
    shadow = tuple(max(0, c - 60) for c in base)
    
    if style_index == 0: # Classic Seashells
        # Draw left and right shells
        for side in [-1, 1]:
            scx = cx + (side * 28)
            # Shell outline & ribs
            pygame.draw.circle(top_surf, shadow, (scx, cy), 18)
            pygame.draw.circle(top_surf, base, (scx, cy), 16)
            pygame.draw.circle(top_surf, highlight, (scx - 4, cy - 4), 8)
            
            # Scallop ribs lines
            for angle in [-45, -22, 0, 22, 45]:
                rad = math.radians(angle + 90 if side == 1 else angle - 90)
                ex = scx + math.cos(rad) * 16
                ey = cy + math.sin(rad) * 16
                pygame.draw.line(top_surf, shadow, (scx, cy), (ex, ey), 2)
                
        # Draw central bow
        pygame.draw.circle(top_surf, (255, 255, 255), (cx, cy), 5)
        pygame.draw.polygon(top_surf, highlight, [(cx, cy), (cx-10, cy-6), (cx-8, cy+6)])
        pygame.draw.polygon(top_surf, highlight, [(cx, cy), (cx+10, cy-6), (cx+8, cy+6)])
        
    elif style_index == 1: # Starfish Top
        # Draw two cute starfish
        for side in [-1, 1]:
            scx = cx + (side * 26)
            star_points = []
            for i in range(5):
                angle = i * (2 * math.pi / 5) - math.pi/2
                # Outer point
                star_points.append((scx + math.cos(angle)*18, cy + math.sin(angle)*18))
                # Inner point
                angle_inner = angle + math.pi / 5
                star_points.append((scx + math.cos(angle_inner)*8, cy + math.sin(angle_inner)*8))
            pygame.draw.polygon(top_surf, shadow, star_points)
            pygame.draw.polygon(top_surf, base, [(x, y) for x, y in star_points])
            # Starfish glow center
            pygame.draw.circle(top_surf, (255, 255, 255, 200), (scx, cy), 4)

    elif style_index == 2: # Pearl Mesh Top
        # String of pearl circles wrapping around chest
        pearl_c = (245, 245, 255, 240)
        shadow_c = (200, 200, 210, 200)
        
        # Draw arc of pearls
        for i in range(12):
            t = i / 11
            # Hanging pearl chain
            px = cx - 50 + t * 100
            py = cy + math.sin(t * math.pi) * 12
            pygame.draw.circle(top_surf, shadow_c, (px, py), 6)
            pygame.draw.circle(top_surf, pearl_c, (px, py), 5)
            pygame.draw.circle(top_surf, (255, 255, 255), (px-2, py-2), 2)
            
        # Two central shell patches
        for side in [-1, 1]:
            pygame.draw.circle(top_surf, base, (cx + side*25, cy - 4), 14)
            pygame.draw.circle(top_surf, highlight, (cx + side*25, cy - 4), 12)

    elif style_index == 3: # Royal Coral Armor Top
        # Gold filigree armor
        pygame.draw.polygon(top_surf, (218, 165, 32), 
                            [(cx - 45, cy - 8), (cx + 45, cy - 8), 
                             (cx + 25, cy + 18), (cx - 25, cy + 18)])
        pygame.draw.polygon(top_surf, GOLD, 
                            [(cx - 40, cy - 5), (cx + 40, cy - 5), 
                             (cx + 20, cy + 14), (cx - 20, cy + 14)])
        # Gem in center
        pygame.draw.rect(top_surf, base, [cx - 6, cy - 2, 12, 12], border_radius=3)
        pygame.draw.rect(top_surf, highlight, [cx - 3, cy, 6, 6], border_radius=1)

    elif style_index == 4: # Seaweed Mesh Top
        # Natural green leafy dress
        green_theme = (46, 139, 87)
        leaf_c = (60, 179, 113)
        
        for side in [-1, 1]:
            # Draw overlapping leaf shapes
            pts = [
                (cx, cy),
                (cx + side * 20, cy - 15),
                (cx + side * 45, cy - 5),
                (cx + side * 25, cy + 12),
                (cx, cy + 8)
            ]
            pygame.draw.polygon(top_surf, green_theme, pts)
            pygame.draw.polygon(top_surf, leaf_c, [(x + side*2, y+1) for x, y in pts], 2)
            
        # Little flowers
        pygame.draw.circle(top_surf, (255, 100, 150), (cx - 15, cy + 2), 4)
        pygame.draw.circle(top_surf, (255, 100, 150), (cx + 15, cy + 2), 4)
        pygame.draw.circle(top_surf, (255, 230, 100), (cx - 15, cy + 2), 2)
        pygame.draw.circle(top_surf, (255, 230, 100), (cx + 15, cy + 2), 2)

    surface.blit(top_surf, (0, 0))

def draw_anime_accessory(surface, head_pos, hand_pos, color_theme, style_index):
    """
    Draws anime accessories (Tiaras, Pearl headband, hairpins on head; wands in hand).
    head_pos: (x, y) head center
    hand_pos: (x, y) hand position
    """
    acc_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    hx, hy = head_pos
    hndx, hndy = hand_pos
    
    base = color_theme
    highlight = tuple(min(255, c + 70) for c in base)
    
    if style_index == 0: # Golden Crystal Tiara
        # Crown shape on head
        points = [
            (hx - 28, hy - 40),
            (hx - 18, hy - 58),
            (hx - 8, hy - 48),
            (hx, hy - 66),
            (hx + 8, hy - 48),
            (hx + 18, hy - 58),
            (hx + 28, hy - 40),
            (hx + 15, hy - 35),
            (hx - 15, hy - 35)
        ]
        pygame.draw.polygon(acc_surf, (184, 134, 11), points)
        pygame.draw.polygon(acc_surf, GOLD, [(x, y+2) for x, y in points])
        
        # Gem on crown center
        pygame.draw.circle(acc_surf, base, (hx, hy - 48), 5)
        pygame.draw.circle(acc_surf, highlight, (hx, hy - 48), 3)
        pygame.draw.circle(acc_surf, (255,255,255), (hx - 1, hy - 49), 1.5)
        
    elif style_index == 1: # Pearl Headband
        # Arc of pearls on head
        pearl_c = (245, 245, 255, 240)
        for i in range(8):
            angle = math.radians(-140 + i * 14)
            px = hx + math.cos(angle) * 32
            py = hy + math.sin(angle) * 32 - 12
            pygame.draw.circle(acc_surf, (200, 200, 210, 180), (px, py), 5)
            pygame.draw.circle(acc_surf, pearl_c, (px, py), 4)
            pygame.draw.circle(acc_surf, (255, 255, 255), (px - 1, py - 1), 1.5)

    elif style_index == 2: # Starfish Hairpin
        # Starfish clipped to the side of head
        spx, spy = hx + 22, hy - 25
        star_points = []
        for i in range(5):
            angle = i * (2 * math.pi / 5) - math.pi/4
            star_points.append((spx + math.cos(angle)*10, spy + math.sin(angle)*10))
            angle_inner = angle + math.pi / 5
            star_points.append((spx + math.cos(angle_inner)*4, spy + math.sin(angle_inner)*4))
            
        pygame.draw.polygon(acc_surf, (200, 50, 120), star_points)
        pygame.draw.polygon(acc_surf, (255, 105, 180), [(x, y) for x, y in star_points])
        pygame.draw.circle(acc_surf, (255, 255, 255), (spx, spy), 2)

    elif style_index == 3: # Magical Ocean Wand / Scepter
        # Rod in hand
        pygame.draw.line(acc_surf, (220, 220, 220), (hndx + 10, hndy + 60), (hndx - 15, hndy - 50), 4)
        pygame.draw.line(acc_surf, GOLD, (hndx + 10, hndy + 60), (hndx - 15, hndy - 50), 2)
        
        # Glowing star at scepter head
        swx, swy = hndx - 15, hndy - 50
        star_points = []
        for i in range(5):
            angle = i * (2 * math.pi / 5) - math.pi/2
            star_points.append((swx + math.cos(angle)*16, swy + math.sin(angle)*16))
            angle_inner = angle + math.pi / 5
            star_points.append((swx + math.cos(angle_inner)*6, swy + math.sin(angle_inner)*6))
            
        pygame.draw.polygon(acc_surf, base, star_points)
        pygame.draw.polygon(acc_surf, highlight, [(x, y) for x, y in star_points], 2)
        pygame.draw.circle(acc_surf, (255, 255, 255), (swx, swy), 4)
        
        # Gem inside
        pygame.draw.circle(acc_surf, base, (swx, swy), 3)

    elif style_index == 4: # Cute Bubble Halo
        # Ring of floating shiny bubbles above head
        bubble_time = pygame.time.get_ticks() * 0.002
        for i in range(6):
            angle = math.radians(i * 60) + bubble_time * 0.2
            bx = hx + math.cos(angle) * 36
            by = hy - 60 + math.sin(angle) * 8
            
            r = 5
            pygame.draw.circle(acc_surf, (200, 240, 255, 120), (bx, by), r, 1)
            pygame.draw.circle(acc_surf, (255, 255, 255, 180), (bx - 1.5, by - 1.5), 1.5)

    surface.blit(acc_surf, (0, 0))

# ----------------------------------------------------
# 6. Asset Loader & Caching
# ----------------------------------------------------
print("Pre-loading character surfaces and shifting colors...")
character_surfaces = {}
for char_id, char_data in CHARACTERS.items():
    print(f"Generating character {char_data['name']}...")
    character_surfaces[char_id] = rotate_hue(char_data["base_file"], char_data["hue"])

# Load Backgrounds
background_files = {
    0: "assets/bg_coral_palace.png",
    1: "assets/bg_deep_abyss.png",
    2: "assets/bg_pearl_cave.png",
    3: "assets/bg_sunset_surface.png"
}

background_surfaces = {}
for bg_id, bg_file in background_files.items():
    if os.path.exists(bg_file):
        try:
            bg_img = pygame.image.load(bg_file).convert()
            background_surfaces[bg_id] = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
            print(f"Loaded background: {bg_file}")
        except Exception as e:
            print(f"Failed to load background {bg_file}: {e}")
    else:
        print(f"Background path not found: {bg_file}")

# Fallback Background Generator
def draw_gradient_fallback(surface, color1, color2):
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(color1[0] * (1 - t) + color2[0] * t)
        g = int(color1[1] * (1 - t) + color2[1] * t)
        b = int(color1[2] * (1 - t) + color2[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

# ----------------------------------------------------
# 7. UI Helpers
# ----------------------------------------------------
def draw_glass_rect(surface, rect, bg_color, border_color, border_thickness=1, border_radius=15):
    """Draws a glassy translucent rectangle with borders."""
    x, y, w, h = rect
    glass = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(glass, bg_color, [0, 0, w, h], border_radius=border_radius)
    pygame.draw.rect(glass, border_color, [0, 0, w, h], border_thickness, border_radius=border_radius)
    surface.blit(glass, (x, y))

def draw_text_glow(surface, text_str, font, color, center_pos, glow_color=(0, 255, 255, 100)):
    # Draw simple glow outline
    text_surf = font.render(text_str, True, color)
    rect = text_surf.get_rect(center=center_pos)
    
    # Render shadow/glow layers
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        glow_surf = font.render(text_str, True, glow_color[:3])
        g_rect = glow_surf.get_rect(center=(center_pos[0] + dx, center_pos[1] + dy))
        surface.blit(glow_surf, g_rect)
        
    surface.blit(text_surf, rect)

# ----------------------------------------------------
# 8. Main Game Loop Variables
# ----------------------------------------------------
running = True
state = "SPLASH" # SPLASH, CHAR_SELECT, GAME
selected_character = 0

# Equipped Dress-Up Items State
# None = empty, or integer representing index
equipped_tail = 0 # default Tail 0
equipped_top = 0 # default Top 0
equipped_acc = 0 # default Acc 0

# Palette color selected for items
equipped_tail_color = CYAN
equipped_top_color = PINK
equipped_acc_color = GOLD

# Current Background Index
current_bg_index = 0

# UI Wardrobe Sidebar State
active_tab = "Tails" # Tails, Tops, Acc, Colors
clock = pygame.time.Clock()

# Dev coordinates offset adjustment variables (Press D to toggle dev mode)
dev_mode = False
dev_focus = "chest" # head, chest, waist, hand

# Game screenshot index
screenshot_counter = 1

while running:
    time_tick = pygame.time.get_ticks() * 0.001
    screen.fill(OCEAN_BLUE)
    
    # ----------------------------------------------------
    # STATE: SPLASH SCREEN (MENU)
    # ----------------------------------------------------
    if state == "SPLASH":
        # Draw background (default to Coral Palace or fall back to blue gradient)
        if 0 in background_surfaces:
            screen.blit(background_surfaces[0], (0, 0))
        else:
            draw_gradient_fallback(screen, (10, 40, 80), (5, 15, 30))
            
        # Draw floating bubbles
        for bubble in bubbles:
            bubble.update()
            bubble.draw(screen)
            
        # Header Box (Glassmorphic)
        draw_glass_rect(screen, [150, 100, 500, 180], (10, 20, 40, 160), (255, 255, 255, 80), 2, 20)
        draw_text_glow(screen, "MERMAID DREAMLAND", font_title, WHITE, (400, 160), CYAN)
        draw_text_glow(screen, "Anime Dress-Up & Fantasy Ocean", font_subtitle, WHITE, (400, 220), PINK)
        
        # Play Button (Glassmorphic)
        mx, my = pygame.mouse.get_pos()
        btn_rect = [300, 380, 200, 60]
        btn_hover = btn_rect[0] <= mx <= btn_rect[0]+btn_rect[2] and btn_rect[1] <= my <= btn_rect[1]+btn_rect[3]
        
        btn_bg = (255, 255, 255, 100) if btn_hover else (15, 35, 65, 180)
        btn_border = (255, 255, 255, 200) if btn_hover else (255, 255, 255, 100)
        
        draw_glass_rect(screen, btn_rect, btn_bg, btn_border, 2, 30)
        btn_text_color = OCEAN_BLUE if btn_hover else WHITE
        btn_text = font_subtitle.render("START GAME", True, btn_text_color)
        screen.blit(btn_text, btn_text.get_rect(center=(400, 410)))
        
        # Bubble particle effect on Play button hover
        if btn_hover and random.random() < 0.15:
            star_particles.append(StarParticle(random.randint(320, 480), 380, CYAN))

    # ----------------------------------------------------
    # STATE: CHARACTER SELECT
    # ----------------------------------------------------
    elif state == "CHAR_SELECT":
        # Draw deep abyss background
        if 1 in background_surfaces:
            screen.blit(background_surfaces[1], (0, 0))
        else:
            draw_gradient_fallback(screen, (5, 20, 45), (2, 8, 20))
            
        for bubble in bubbles:
            bubble.update()
            bubble.draw(screen)
            
        # Draw Title
        draw_text_glow(screen, "CHOOSE YOUR ANIME MERMAID", font_title, WHITE, (400, 60), PINK)
        
        # Mouse coords
        mx, my = pygame.mouse.get_pos()
        
        # Draw 5 Character Cards
        card_w, card_h = 130, 360
        gap = 18
        start_x = (WIDTH - (5 * card_w + 4 * gap)) // 2
        
        for char_id, char_data in CHARACTERS.items():
            cx = start_x + char_id * (card_w + gap)
            cy = 140
            
            # Hover detection
            hover = cx <= mx <= cx + card_w and cy <= my <= cy + card_h
            
            # Glass card styling
            card_bg = (255, 255, 255, 80) if hover else (15, 30, 55, 170)
            card_border = CYAN if hover else (255, 255, 255, 80)
            card_border_t = 3 if hover else 1
            
            # Draw card body
            draw_glass_rect(screen, [cx, cy, card_w, card_h], card_bg, card_border, card_border_t, 15)
            
            # Draw tiny thumbnail of character sprite
            if char_id in character_surfaces:
                # Scale the 400x500 sprite to fit nicely
                scaled_char = pygame.transform.smoothscale(character_surfaces[char_id], (120, 150))
                # Crop upper body slightly
                screen.blit(scaled_char, (cx + 5, cy + 15), (0, 0, 120, 150))
                
            # Draw Name & Title
            name_t = font_ui.render(char_data["name"], True, WHITE)
            screen.blit(name_t, name_t.get_rect(center=(cx + card_w//2, cy + 185)))
            
            # Wrap description text
            words = char_data["title"].split()
            line1, line2 = "", ""
            for word in words:
                if len(line1) + len(word) < 14:
                    line1 += word + " "
                else:
                    line2 += word + " "
            
            t_line1 = font_ui_small.render(line1.strip(), True, CYAN)
            t_line2 = font_ui_small.render(line2.strip(), True, CYAN)
            screen.blit(t_line1, t_line1.get_rect(center=(cx + card_w//2, cy + 215)))
            screen.blit(t_line2, t_line2.get_rect(center=(cx + card_w//2, cy + 230)))
            
            # Quality description (underneath)
            q_words = char_data["quality"].split()
            q_line1, q_line2 = "", ""
            for word in q_words:
                if len(q_line1) + len(word) < 16:
                    q_line1 += word + " "
                else:
                    q_line2 += word + " "
                    
            t_q1 = font_desc.render(q_line1.strip(), True, WHITE)
            t_q2 = font_desc.render(q_line2.strip(), True, WHITE)
            screen.blit(t_q1, t_q1.get_rect(center=(cx + card_w//2, cy + 265)))
            screen.blit(t_q2, t_q2.get_rect(center=(cx + card_w//2, cy + 280)))
            
            # Select Label at bottom
            lbl_color = GOLD if hover else (180, 200, 220)
            select_lbl = font_ui.render("SELECT", True, lbl_color)
            screen.blit(select_lbl, select_lbl.get_rect(center=(cx + card_w//2, cy + 330)))
            
            if hover and random.random() < 0.12:
                star_particles.append(StarParticle(cx + card_w//2, cy + 150, PINK))

        # Back Button (Character select screen back to splash)
        back_rect = [20, 20, 80, 35]
        back_hover = back_rect[0] <= mx <= back_rect[0]+back_rect[2] and back_rect[1] <= my <= back_rect[1]+back_rect[3]
        draw_glass_rect(screen, back_rect, (255,255,255,80) if back_hover else (15, 30, 55, 170), (255,255,255,100), 1, 10)
        lbl_back = font_ui.render("BACK", True, WHITE)
        screen.blit(lbl_back, lbl_back.get_rect(center=(60, 37)))

    # ----------------------------------------------------
    # STATE: GAMEPLAY (DRESS-UP WARDROBE)
    # ----------------------------------------------------
    elif state == "GAME":
        # Draw selected background
        if current_bg_index in background_surfaces:
            screen.blit(background_surfaces[current_bg_index], (0, 0))
        else:
            # gradient fallback
            draw_gradient_fallback(screen, (5, 35, 65), (2, 10, 25))
            
        # Draw background bubbles
        for bubble in bubbles:
            bubble.update()
            bubble.draw(screen)
            
        # Gentle floating bobbing animation for the character base
        # math.sin(time) * amplitude
        bob_y = int(math.sin(time_tick * 2.2) * 8)
        char_x = 100
        char_y = 50 + bob_y
        
        char_data = CHARACTERS[selected_character]
        
        # Absolute coordinates of character markers (adjusted for bobbing)
        cur_waist = (char_x + char_data["waist"][0], char_y + char_data["waist"][1])
        cur_chest = (char_x + char_data["chest"][0], char_y + char_data["chest"][1])
        cur_head = (char_x + char_data["head"][0], char_y + char_data["head"][1])
        cur_hand = (char_x + char_data["hand"][0], char_y + char_data["hand"][1])
        
        # ----------------------------------------------------
        # 1. RENDER CHARACTER LAYERS IN CORRECT ORDER
        # ----------------------------------------------------
        # Layer 1: Animated Dreamy Tail (rendered behind character torso!)
        if equipped_tail is not None:
            draw_dreamy_tail(screen, cur_waist, equipped_tail_color, time_tick, equipped_tail)
            
        # Layer 2: Character Torso Base (drawn over the tail)
        if selected_character in character_surfaces:
            screen.blit(character_surfaces[selected_character], (char_x, char_y))
            
        # Layer 3: Equipped Top (drawn over the chest)
        if equipped_top is not None:
            draw_anime_top(screen, cur_chest, equipped_top_color, equipped_top)
            
        # Layer 4: Equipped Accessories (headbands, crowns, scepters)
        if equipped_acc is not None:
            draw_anime_accessory(screen, cur_head, cur_hand, equipped_acc_color, equipped_acc)
            
        # ----------------------------------------------------
        # 2. DRAW WARDROBE SIDEBAR PANEL (GLASSMORPHIC)
        # ----------------------------------------------------
        draw_glass_rect(screen, [520, 15, 265, 570], GLASS_BG, GLASS_BORDER, 2, 20)
        
        # Wardrobe Title
        lbl_wardrobe = font_ui.render("W A R D R O B E", True, GOLD)
        screen.blit(lbl_wardrobe, lbl_wardrobe.get_rect(center=(652, 40)))
        
        # Category Tabs (Tails, Tops, Accessories, Colors)
        mx, my = pygame.mouse.get_pos()
        tabs = ["Tails", "Tops", "Acc", "Colors"]
        tab_w = 58
        for idx, tab_name in enumerate(tabs):
            tx = 535 + idx * (tab_w + 3)
            ty = 65
            tab_rect = [tx, ty, tab_w, 30]
            
            # Hover & Active styling
            is_active = active_tab == tab_name
            is_hover = tx <= mx <= tx + tab_w and ty <= my <= ty + 30
            
            if is_active:
                tab_bg = (0, 255, 255, 120)
                tab_border = CYAN
            elif is_hover:
                tab_bg = (255, 255, 255, 80)
                tab_border = WHITE
            else:
                tab_bg = (10, 20, 40, 150)
                tab_border = (255, 255, 255, 50)
                
            draw_glass_rect(screen, tab_rect, tab_bg, tab_border, 1, 8)
            lbl_tab = font_ui_small.render(tab_name, True, WHITE)
            screen.blit(lbl_tab, lbl_tab.get_rect(center=(tx + tab_w//2, ty + 15)))
            
        # Grid Content based on active tab
        grid_start_y = 110
        grid_gap = 10
        item_w, item_h = 68, 68
        
        # 5 items list labels & styles
        item_labels = {
            "Tails": ["Starry", "Pearl", "Sunset", "Neon", "Dragon"],
            "Tops": ["Shells", "Starfish", "PearlMesh", "RoyalGold", "Seaweed"],
            "Acc": ["Tiara", "Pearls", "Starpin", "Wand", "BubbleHalo"]
        }
        
        if active_tab in item_labels:
            labels = item_labels[active_tab]
            
            for i in range(5):
                row = i // 3
                col = i % 3
                ix = 540 + col * (item_w + grid_gap)
                iy = grid_start_y + row * (item_h + grid_gap)
                
                # Check active selection
                is_selected = False
                if active_tab == "Tails":
                    is_selected = equipped_tail == i
                elif active_tab == "Tops":
                    is_selected = equipped_top == i
                elif active_tab == "Acc":
                    is_selected = equipped_acc == i
                    
                is_hover = ix <= mx <= ix + item_w and iy <= my <= iy + item_h
                
                # Draw grid slot card
                box_bg = (0, 255, 255, 80) if is_selected else ((255, 255, 255, 60) if is_hover else (10, 20, 35, 120))
                box_border = GOLD if is_selected else (CYAN if is_hover else (255, 255, 255, 40))
                box_border_t = 2 if (is_selected or is_hover) else 1
                
                draw_glass_rect(screen, [ix, iy, item_w, item_h], box_bg, box_border, box_border_t, 12)
                
                # Render item title/icon text inside the grid box
                lbl_name = font_ui_small.render(labels[i], True, WHITE)
                screen.blit(lbl_name, lbl_name.get_rect(center=(ix + item_w//2, iy + item_h//2)))
                
                # Equipt status circle
                if is_selected:
                    pygame.draw.circle(screen, GOLD, (ix + item_w - 8, iy + 8), 4)

        elif active_tab == "Colors":
            # Show color swatches palette to color-customize items
            color_swatches = [
                ("Neon Pink", PINK),
                ("Magic Cyan", CYAN),
                ("Royal Gold", GOLD),
                ("Mystic Violet", PURPLE),
                ("Sea Green", GREEN),
                ("Pure Pearl", (240, 240, 255))
            ]
            
            # Subheaders
            lbl_color_tgt = font_ui.render("TINT CURRENT OUTFIT:", True, GOLD)
            screen.blit(lbl_color_tgt, (540, 115))
            
            # Draw Color Picker cards
            for idx, (color_name, col_val) in enumerate(color_swatches):
                c_rect = [540, 145 + idx * 45, 225, 38]
                is_hover = c_rect[0] <= mx <= c_rect[0]+c_rect[2] and c_rect[1] <= my <= c_rect[1]+c_rect[3]
                
                draw_glass_rect(screen, c_rect, (255,255,255,60) if is_hover else (10, 20, 35, 120), (255,255,255,40), 1, 10)
                
                # Draw solid circle indicator
                pygame.draw.circle(screen, col_val, (560, 145 + idx * 45 + 19), 12)
                pygame.draw.circle(screen, WHITE, (560, 145 + idx * 45 + 19), 12, 1)
                
                lbl_c_name = font_ui.render(color_name, True, WHITE)
                screen.blit(lbl_c_name, (585, 145 + idx * 45 + 9))

        # Bottom wardrobe buttons
        # 1. Reset Button
        btn_reset = [540, 430, 105, 35]
        h_reset = btn_reset[0] <= mx <= btn_reset[0]+btn_reset[2] and btn_reset[1] <= my <= btn_reset[1]+btn_reset[3]
        draw_glass_rect(screen, btn_reset, (255, 100, 100, 120) if h_reset else (100, 30, 30, 150), (255, 100, 100, 100), 1, 10)
        lbl_reset = font_ui.render("RESET", True, WHITE)
        screen.blit(lbl_reset, lbl_reset.get_rect(center=(btn_reset[0]+btn_reset[2]//2, btn_reset[1]+btn_reset[3]//2)))
        
        # 2. Randomize Button
        btn_rand = [660, 430, 105, 35]
        h_rand = btn_rand[0] <= mx <= btn_rand[0]+btn_rand[2] and btn_rand[1] <= my <= btn_rand[1]+btn_rand[3]
        draw_glass_rect(screen, btn_rand, (100, 255, 100, 120) if h_rand else (30, 100, 30, 150), (100, 255, 100, 100), 1, 10)
        lbl_rand = font_ui.render("RANDOM", True, WHITE)
        screen.blit(lbl_rand, lbl_rand.get_rect(center=(btn_rand[0]+btn_rand[2]//2, btn_rand[1]+btn_rand[3]//2)))

        # 3. Screenshot Button (Camera Icon shape or simple text)
        btn_snap = [540, 475, 105, 35]
        h_snap = btn_snap[0] <= mx <= btn_snap[0]+btn_snap[2] and btn_snap[1] <= my <= btn_snap[1]+btn_snap[3]
        draw_glass_rect(screen, btn_snap, (255, 215, 0, 120) if h_snap else (120, 100, 20, 150), (255, 215, 0, 100), 1, 10)
        lbl_snap = font_ui.render("PHOTO", True, WHITE)
        screen.blit(lbl_snap, lbl_snap.get_rect(center=(btn_snap[0]+btn_snap[2]//2, btn_snap[1]+btn_snap[3]//2)))

        # 4. BG Switcher Button
        btn_bg = [660, 475, 105, 35]
        h_bg = btn_bg[0] <= mx <= btn_bg[0]+btn_bg[2] and btn_bg[1] <= my <= btn_bg[1]+btn_bg[3]
        draw_glass_rect(screen, btn_bg, (0, 255, 255, 120) if h_bg else (10, 80, 80, 150), (0, 255, 255, 100), 1, 10)
        lbl_bg = font_ui.render("SCENE", True, WHITE)
        screen.blit(lbl_bg, lbl_bg.get_rect(center=(btn_bg[0]+btn_bg[2]//2, btn_bg[1]+btn_bg[3]//2)))

        # 5. Back to Character Select
        btn_back = [540, 530, 225, 38]
        h_back = btn_back[0] <= mx <= btn_back[0]+btn_back[2] and btn_back[1] <= my <= btn_back[1]+btn_back[3]
        draw_glass_rect(screen, btn_back, (255, 255, 255, 100) if h_back else (15, 35, 65, 180), (255, 255, 255, 80), 1, 10)
        lbl_back = font_ui.render("BACK TO CHARACTERS", True, WHITE)
        screen.blit(lbl_back, lbl_back.get_rect(center=(btn_back[0]+btn_back[2]//2, btn_back[1]+btn_back[3]//2)))

        # ----------------------------------------------------
        # 3. EXTRA SCREEN CONTROLS (SOUND TOGGLE & TITLE IN GAME)
        # ----------------------------------------------------
        # Sound Toggle (top-left)
        snd_rect = [20, 20, 40, 40]
        h_snd = snd_rect[0] <= mx <= snd_rect[0]+snd_rect[2] and snd_rect[1] <= my <= snd_rect[1]+snd_rect[3]
        draw_glass_rect(screen, snd_rect, (255,255,255,80) if h_snd else (15,30,55,170), (255,255,255,100), 1, 10)
        
        # Draw sound icon
        snd_char = "ON" if music_playing else "OFF"
        lbl_snd = font_ui_small.render(snd_char, True, CYAN if music_playing else PINK)
        screen.blit(lbl_snd, lbl_snd.get_rect(center=(40, 40)))
        
        # Character Name badge in top-left center
        badge_rect = [75, 20, 240, 40]
        draw_glass_rect(screen, badge_rect, (10, 20, 35, 150), (255, 255, 255, 60), 1, 10)
        lbl_badge = font_ui.render(f"{char_data['name']}: {char_data['title']}", True, WHITE)
        screen.blit(lbl_badge, lbl_badge.get_rect(center=(195, 40)))

        # ----------------------------------------------------
        # 4. DEVELOPER MODE COORDS ALIGNER (PRESS 'D')
        # ----------------------------------------------------
        if dev_mode:
            # Highlight current marker
            marker_color = (255, 0, 0)
            marker_pos = (0,0)
            if dev_focus == "head":
                marker_pos = cur_head
            elif dev_focus == "chest":
                marker_pos = cur_chest
            elif dev_focus == "waist":
                marker_pos = cur_waist
            elif dev_focus == "hand":
                marker_pos = cur_hand
                
            pygame.draw.circle(screen, marker_color, marker_pos, 8)
            pygame.draw.circle(screen, WHITE, marker_pos, 2)
            
            # Dev HUD
            draw_glass_rect(screen, [15, 500, 490, 80], (20, 10, 10, 220), (255, 0, 0, 150), 1, 10)
            dev_text1 = f"DEV MODE | Focus: {dev_focus.upper()} (Press Tab to swap)"
            dev_text2 = f"Head: {char_data['head']} | Chest: {char_data['chest']} | Waist: {char_data['waist']} | Hand: {char_data['hand']}"
            dev_text3 = "Arrow Keys to move. Coords save automatically in console."
            screen.blit(font_ui.render(dev_text1, True, (255, 100, 100)), (25, 505))
            screen.blit(font_ui_small.render(dev_text2, True, WHITE), (25, 528))
            screen.blit(font_ui_small.render(dev_text3, True, (200, 200, 200)), (25, 550))

    # ----------------------------------------------------
    # RENDER FLOATING STARS/PARTICLES (DRAW OVER EVERYTHING)
    # ----------------------------------------------------
    for p in star_particles[:]:
        p.update()
        p.draw(screen)
        if p.life <= 0:
            star_particles.remove(p)
            
    pygame.display.flip()
    
    # ----------------------------------------------------
    # EVENT HANDLING
    # ----------------------------------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            if state == "SPLASH":
                # Start button click
                if 300 <= mx <= 500 and 380 <= my <= 440:
                    if pop_sound: pop_sound.play()
                    state = "CHAR_SELECT"
                    
            elif state == "CHAR_SELECT":
                # Back button
                if 20 <= mx <= 100 and 20 <= my <= 55:
                    if pop_sound: pop_sound.play()
                    state = "SPLASH"
                    
                # Character cards select click
                card_w, card_h = 130, 360
                gap = 18
                start_x = (WIDTH - (5 * card_w + 4 * gap)) // 2
                
                for char_id in range(5):
                    cx = start_x + char_id * (card_w + gap)
                    cy = 140
                    if cx <= mx <= cx + card_w and cy <= my <= cy + card_h:
                        selected_character = char_id
                        if pop_sound: pop_sound.play()
                        
                        # Reset customized outfit colors to defaults matching character themes
                        if selected_character == 0: # Aria
                            equipped_tail_color, equipped_top_color, equipped_acc_color = CYAN, PINK, GOLD
                        elif selected_character == 1: # Coralia
                            equipped_tail_color, equipped_top_color, equipped_acc_color = PINK, (240, 240, 255), PURPLE
                        elif selected_character == 2: # Kailani
                            equipped_tail_color, equipped_top_color, equipped_acc_color = GOLD, GREEN, PINK
                        elif selected_character == 3: # Naida
                            equipped_tail_color, equipped_top_color, equipped_acc_color = PURPLE, CYAN, (240, 240, 255)
                        elif selected_character == 4: # Serena
                            equipped_tail_color, equipped_top_color, equipped_acc_color = (240, 240, 255), PINK, GOLD
                            
                        state = "GAME"
                        
            elif state == "GAME":
                # Back to character select
                if 540 <= mx <= 765 and 530 <= my <= 568:
                    if pop_sound: pop_sound.play()
                    state = "CHAR_SELECT"
                    
                # Sound Toggle Click
                elif 20 <= mx <= 60 and 20 <= my <= 60:
                    music_playing = not music_playing
                    if music_playing:
                        music_sound.play(loops=-1)
                    else:
                        music_sound.stop()
                        
                # Category Tab Clicks
                elif 65 <= my <= 95:
                    tabs = ["Tails", "Tops", "Acc", "Colors"]
                    tab_w = 58
                    for idx, tab_name in enumerate(tabs):
                        tx = 535 + idx * (tab_w + 3)
                        if tx <= mx <= tx + tab_w:
                            active_tab = tab_name
                            if pop_sound: pop_sound.play()
                            
                # Reset Outfit Click
                elif 540 <= mx <= 645 and 430 <= my <= 465:
                    equipped_tail = None
                    equipped_top = None
                    equipped_acc = None
                    if pop_sound: pop_sound.play()
                    
                # Randomize Outfit Click
                elif 660 <= mx <= 765 and 430 <= my <= 465:
                    equipped_tail = random.randint(0, 4)
                    equipped_top = random.randint(0, 4)
                    equipped_acc = random.randint(0, 4)
                    
                    colors = [PINK, CYAN, GOLD, PURPLE, GREEN, (240, 240, 255)]
                    equipped_tail_color = random.choice(colors)
                    equipped_top_color = random.choice(colors)
                    equipped_acc_color = random.choice(colors)
                    
                    if pop_sound: pop_sound.play()
                    
                    # Spawn sparkles
                    for _ in range(15):
                        star_particles.append(StarParticle(random.randint(150, 450), random.randint(100, 500), equipped_tail_color))
                        
                # Photo/Screenshot click
                elif 540 <= mx <= 645 and 475 <= my <= 510:
                    if pop_sound: pop_sound.play()
                    # Capture canvas without wardrobe UI
                    # Hide wardrobe UI by drawing background and character onto a temp surface
                    cap_surf = pygame.Surface((WIDTH, HEIGHT))
                    if current_bg_index in background_surfaces:
                        cap_surf.blit(background_surfaces[current_bg_index], (0, 0))
                    else:
                        draw_gradient_fallback(cap_surf, (5, 35, 65), (2, 10, 25))
                        
                    # draw bubble particles
                    for b in bubbles:
                        b.draw(cap_surf)
                        
                    bob_y = int(math.sin(time_tick * 2.2) * 8)
                    char_x, char_y = 100, 50 + bob_y
                    
                    cur_waist = (char_x + char_data["waist"][0], char_y + char_data["waist"][1])
                    cur_chest = (char_x + char_data["chest"][0], char_y + char_data["chest"][1])
                    cur_head = (char_x + char_data["head"][0], char_y + char_data["head"][1])
                    cur_hand = (char_x + char_data["hand"][0], char_y + char_data["hand"][1])
                    
                    # Draw layers onto capture surface
                    if equipped_tail is not None:
                        draw_dreamy_tail(cap_surf, cur_waist, equipped_tail_color, time_tick, equipped_tail)
                    if selected_character in character_surfaces:
                        cap_surf.blit(character_surfaces[selected_character], (char_x, char_y))
                    if equipped_top is not None:
                        draw_anime_top(cap_surf, cur_chest, equipped_top_color, equipped_top)
                    if equipped_acc is not None:
                        draw_anime_accessory(cap_surf, cur_head, cur_hand, equipped_acc_color, equipped_acc)
                        
                    # Draw neat watermark logo
                    watermark = font_ui_small.render("Dreamy Anime Mermaid", True, (255,255,255,100))
                    cap_surf.blit(watermark, (20, HEIGHT - 30))
                    
                    # Save to file
                    filename = f"mermaid_dressup_photo_{screenshot_counter}.png"
                    pygame.image.save(cap_surf, filename)
                    print(f"Screenshot saved: {filename}")
                    screenshot_counter += 1
                    
                    # Spawn massive sparklers
                    for _ in range(30):
                        star_particles.append(StarParticle(300, 300, GOLD))
                        
                # Scene/Background switch click
                elif 660 <= mx <= 765 and 475 <= my <= 510:
                    current_bg_index = (current_bg_index + 1) % 4
                    if pop_sound: pop_sound.play()
                    
                # Wardrobe Items slots click detection
                elif active_tab in item_labels and grid_start_y <= my <= grid_start_y + 2 * (item_h + grid_gap):
                    labels = item_labels[active_tab]
                    for i in range(5):
                        row = i // 3
                        col = i % 3
                        ix = 540 + col * (item_w + grid_gap)
                        iy = grid_start_y + row * (item_h + grid_gap)
                        
                        if ix <= mx <= ix + item_w and iy <= my <= iy + item_h:
                            if active_tab == "Tails":
                                equipped_tail = i
                            elif active_tab == "Tops":
                                equipped_top = i
                            elif active_tab == "Acc":
                                equipped_acc = i
                            if pop_sound: pop_sound.play()
                            
                            # Sparkle explosion at equipped item location
                            sparkle_y = cur_waist[1] if active_tab == "Tails" else (cur_chest[1] if active_tab == "Tops" else cur_head[1])
                            for _ in range(8):
                                star_particles.append(StarParticle(300, sparkle_y, equipped_tail_color))
                                
                # Color Swatches Clicks
                elif active_tab == "Colors" and 145 <= my <= 145 + 6 * 45:
                    color_swatches = [
                        ("Neon Pink", PINK),
                        ("Magic Cyan", CYAN),
                        ("Royal Gold", GOLD),
                        ("Mystic Violet", PURPLE),
                        ("Sea Green", GREEN),
                        ("Pure Pearl", (240, 240, 255))
                    ]
                    for idx, (color_name, col_val) in enumerate(color_swatches):
                        c_rect = [540, 145 + idx * 45, 225, 38]
                        if c_rect[0] <= mx <= c_rect[0]+c_rect[2] and c_rect[1] <= my <= c_rect[1]+c_rect[3]:
                            if pop_sound: pop_sound.play()
                            
                            # Tint the last active tab item or everything
                            equipped_tail_color = col_val
                            equipped_top_color = col_val
                            equipped_acc_color = col_val
                            
        elif event.type == pygame.KEYDOWN:
            # Dev Mode toggles
            if event.key == pygame.K_d:
                dev_mode = not dev_mode
                print(f"Dev alignment mode: {dev_mode}")
                
            if dev_mode and state == "GAME":
                char_data = CHARACTERS[selected_character]
                
                # Tab swaps dev focus marker
                if event.key == pygame.K_TAB:
                    if dev_focus == "head": dev_focus = "chest"
                    elif dev_focus == "chest": dev_focus = "waist"
                    elif dev_focus == "waist": dev_focus = "hand"
                    elif dev_focus == "hand": dev_focus = "head"
                    print(f"Dev focus shifted to: {dev_focus}")
                    
                # Move coordinates
                dx, dy = 0, 0
                if event.key == pygame.K_LEFT: dx = -1
                elif event.key == pygame.K_RIGHT: dx = 1
                elif event.key == pygame.K_UP: dy = -1
                elif event.key == pygame.K_DOWN: dy = 1
                
                if dx != 0 or dy != 0:
                    current_coords = char_data[dev_focus]
                    new_coords = (current_coords[0] + dx, current_coords[1] + dy)
                    char_data[dev_focus] = new_coords
                    print(f"Updated {dev_focus} coordinate: {new_coords} for character {char_data['name']}")
                    
    # Limit frame rate
    clock.tick(60)

pygame.quit()
sys.exit()

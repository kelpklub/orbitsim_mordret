import pygame
import math
import random
from pygame import gfxdraw  # AA circles

# Initialize Pygame
pygame.init()

# Constants (initial window size; rendering adapts dynamically later)
WIDTH, HEIGHT = 1000, 700
G = 0.8
PLANET_RADIUS = 12
SUN_RADIUS = 20
MIN_DIST = 1
BASE_GRID_SIZE = 50  # Base grid size in pixels

# Zoom and camera constants
MIN_ZOOM = 0.0000001
MAX_ZOOM = 5.0
ZOOM_SPEED = 1.15

# time scale
MIN_TIME_SCALE = 0.01
MAX_TIME_SCALE = 10000

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (100, 150, 255)
RED = (255, 100, 100)
GREEN = (100, 255, 100)
LIGHT_GREEN = (144, 200, 144)
ORANGE = (255, 165, 0)
PURPLE = (160, 32, 240)
CYAN = (0, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)
SELECT_COLOR = (255, 0, 128)
GRID_COLOR = (40, 40, 40)
AXIS_COLOR = (80, 80, 80)

# Fonts (set dynamically later)
font = None
small_font = None
large_font = None
input_font = None

def set_fonts_for_height(h):
    """Scale fonts based on window height (baseline 700)."""
    global font, small_font, large_font, input_font
    scale = max(0.75, min(2.0, h / 700.0))
    # Base sizes bumped up for larger text
    small_size = int(22 * scale)
    base_size  = int(28 * scale)
    large_size = int(40 * scale)
    input_size = int(28 * scale)
    font = pygame.font.Font(None, base_size)
    small_font = pygame.font.Font(None, small_size)
    large_font = pygame.font.Font(None, large_size)
    input_font = pygame.font.Font(None, input_size)

# ---------- AA helpers (visual-only) ----------
def draw_aacircle_filled(screen, x, y, r, color):
    gfxdraw.aacircle(screen, int(x), int(y), int(r), color)
    gfxdraw.filled_circle(screen, int(x), int(y), int(r), color)

def draw_aacircle_outline(screen, x, y, r, color, thickness=1):
    for t in range(thickness):
        gfxdraw.aacircle(screen, int(x), int(y), int(r + t), color)
# ---------------------------------------------


class Camera:  # camera with dynamic viewport
    def __init__(self, width, height):
        self.zoom = 0.01
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.dragging = False
        self.follow = None
        self.last_mouse_pos = (0, 0)
        self.width = width
        self.height = height

    def set_viewport(self, width, height):
        self.width = width
        self.height = height

    # world coords (simulation) vs screen coords (pixels)
    def world_to_screen(self, world_x, world_y):
        screen_x = (world_x + self.pan_x) * self.zoom + self.width // 2
        screen_y = (world_y + self.pan_y) * self.zoom + self.height // 2
        return int(screen_x), int(screen_y)

    def screen_to_world(self, screen_x, screen_y):
        world_x = (screen_x - self.width // 2) / self.zoom - self.pan_x
        world_y = (screen_y - self.height // 2) / self.zoom - self.pan_y
        return world_x, world_y

    def zoom_at_point(self, mouse_x, mouse_y, zoom_factor):
        if not self.follow:
            world_x, world_y = self.screen_to_world(mouse_x, mouse_y)
            new_zoom = self.zoom * zoom_factor
            self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, new_zoom))
            new_screen_x, new_screen_y = self.world_to_screen(world_x, world_y)
            self.pan_x += (mouse_x - new_screen_x) / self.zoom
            self.pan_y += (mouse_y - new_screen_y) / self.zoom
        else:
            new_zoom = self.zoom * zoom_factor
            self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, new_zoom))

    def start_drag(self, mouse_pos):
        self.dragging = True
        self.last_mouse_pos = mouse_pos

    def update_drag(self, mouse_pos):
        if self.dragging:
            dx = mouse_pos[0] - self.last_mouse_pos[0]
            dy = mouse_pos[1] - self.last_mouse_pos[1]
            self.pan_x += dx / self.zoom
            self.pan_y += dy / self.zoom
            self.last_mouse_pos = mouse_pos

    def stop_drag(self):
        self.dragging = False

    def update_follow(self):
        if self.follow:
            self.pan_x = -self.follow.x
            self.pan_y = -self.follow.y

    def stop_follow(self):
        self.follow = None


class InputBox:  # make input box go brrrrrr
    def __init__(self, x, y, w, h, label, default_text='', number_only=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = LIGHT_GRAY
        self.color_active = GREEN
        self.color = self.color_inactive
        self.text = str(default_text)
        self.label = label
        self.txt_surface = None  # set after fonts init
        self.active = False
        self.number_only = number_only
        self.refresh_text_surface()

    def refresh_text_surface(self):
        global input_font
        self.txt_surface = input_font.render(self.text, True, WHITE)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    self.active = True
                    self.color = self.color_active
                else:
                    self.active = False
                    self.color = self.color_inactive

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    char = event.unicode
                    if char.isprintable():
                        if self.number_only:
                            if char.isdigit() or char in '.-':
                                if char == '.' and '.' in self.text:
                                    pass
                                elif char == '-' and ('-' in self.text or len(self.text) > 0):
                                    pass
                                else:
                                    self.text += char
                        else:
                            self.text += char
                self.refresh_text_surface()
        return None

    def draw(self, screen):
        global small_font
        label_surface = small_font.render(self.label, True, WHITE)
        screen.blit(label_surface, (self.rect.x, self.rect.y - label_surface.get_height() - 6))

        pygame.draw.rect(screen, BLACK, self.rect)
        pygame.draw.rect(screen, self.color, self.rect, 2)

        text_rect = self.txt_surface.get_rect()
        text_rect.centery = self.rect.centery
        text_rect.x = self.rect.x + 8
        screen.blit(self.txt_surface, text_rect)

        if self.active:
            cursor_x = text_rect.right + 2
            cursor_y = self.rect.y + 5
            pygame.draw.line(screen, WHITE, (cursor_x, cursor_y), (cursor_x, cursor_y + self.rect.height - 10), 1)

    def get_value(self):
        try:
            return float(self.text) if self.text else 0.0
        except ValueError:
            return 0.0

    def set_value(self, value):
        self.text = str(value)
        self.refresh_text_surface()


class Body:
    def __init__(self, x, y, mass, vx=0, vy=0, radius=PLANET_RADIUS, color=BLUE, name="Body"):
        self.x = float(x)
        self.y = float(y)
        self.mass = float(mass)
        self.vx = float(vx)
        self.vy = float(vy)
        self.radius = radius
        self.color = color
        self.name = name

        self.trail = []
        self.selected = False
        self.make_glow = False

        self.fx = 0.0
        self.fy = 0.0

    def __str__(self):
        return self.name

    def calculate_force_from(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        distance_squared = dx * dx + dy * dy
        distance = max(MIN_DIST, math.sqrt(distance_squared))
        force_magnitude = G * self.mass * other.mass / (distance * distance)
        fx = force_magnitude * dx / distance
        fy = force_magnitude * dy / distance
        return fx, fy

    def apply_force(self, fx, fy, dt):
        if not self.selected:
            ax = fx / self.mass
            ay = fy / self.mass
            self.vx += ax * dt
            self.vy += ay * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.update_trail()

    def update_trail(self):
        current_pos = (self.x, self.y)
        if not self.trail or abs(self.trail[-1][0] - self.x) > 2 or abs(self.trail[-1][1] - self.y) > 2:
            self.trail.append(current_pos)
        if len(self.trail) > 200:
            self.trail.pop(0)

    def draw(self, screen, camera):
        global small_font
        # AA trails
        if len(self.trail) > 2:
            trail_color = tuple(c // 2 for c in self.color)
            screen_trail = [camera.world_to_screen(px, py) for (px, py) in self.trail]
            if len(screen_trail) > 1:
                for i in range(1, len(screen_trail)):
                    alpha = i / len(screen_trail)
                    color = tuple(int(c * alpha) for c in trail_color)
                    pygame.draw.aaline(screen, color, screen_trail[i-1], screen_trail[i])

        # Get screen position
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Only draw if on screen
        W, H = screen.get_size()
        margin = 100
        if (-margin < screen_x < W + margin and -margin < screen_y < H + margin):
            color = SELECT_COLOR if self.selected else self.color
            draw_radius = max(3, int(self.radius * camera.zoom))

            if self.make_glow:
                for i in range(3):
                    glow_radius = draw_radius + i * 4
                    glow_alpha = 100 - i * 30
                    glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                    glow_color = (*self.color, max(0, glow_alpha))
                    pygame.draw.circle(glow_surface, glow_color, (glow_radius, glow_radius), glow_radius)
                    screen.blit(glow_surface, (screen_x - glow_radius, screen_y - glow_radius), special_flags=pygame.BLEND_PREMULTIPLIED)

            # AA planet
            draw_aacircle_filled(screen, screen_x, screen_y, draw_radius, color)

            if self.selected:
                draw_aacircle_outline(screen, screen_x, screen_y, draw_radius + 5, SELECT_COLOR, thickness=3)

            # Labels
            if camera.zoom > 0.1:
                name_surface = small_font.render(self.name, True, WHITE)
                screen.blit(name_surface, (screen_x + draw_radius + 8, screen_y - name_surface.get_height()))

                coord_text = f"({int(self.x)}, {int(-self.y)})"
                coord_surface = small_font.render(coord_text, True, LIGHT_GRAY)
                screen.blit(coord_surface, (screen_x + draw_radius + 8, screen_y + 2))

            if camera.follow and camera.follow.name == self.name:
                name_surface = small_font.render(self.name, True, WHITE)
                screen.blit(name_surface, (screen_x + draw_radius + 8, screen_y - name_surface.get_height()))
                coord_text = f"({int(self.x)}, {int(-self.y)})"
                coord_surface = small_font.render(coord_text, True, LIGHT_GRAY)
                screen.blit(coord_surface, (screen_x + draw_radius + 8, screen_y + 2))


def get_optimal_grid_spacing(zoom):
    target_screen_spacing = 50
    world_spacing = target_screen_spacing / zoom
    magnitude = 10 ** math.floor(math.log10(world_spacing))
    normalized = world_spacing / magnitude

    if normalized <= 1:
        nice_spacing = 1 * magnitude
    elif normalized <= 2:
        nice_spacing = 2 * magnitude
    elif normalized <= 5:
        nice_spacing = 5 * magnitude
    else:
        nice_spacing = 10 * magnitude

    return nice_spacing


def apply_mutual_gravity(bodies, dt):
    for body in bodies:
        body.fx = 0.0
        body.fy = 0.0

    for i, body1 in enumerate(bodies):
        for j, body2 in enumerate(bodies):
            if i != j:
                fx, fy = body1.calculate_force_from(body2)
                body1.fx += fx
                body1.fy += fy

    for body in bodies:
        body.apply_force(body.fx, body.fy, dt)


def get_body_at_position(screen_x, screen_y, bodies, camera):
    world_x, world_y = camera.screen_to_world(screen_x, screen_y)
    for body in bodies:
        distance = math.sqrt((body.x - world_x) ** 2 + (body.y - world_y) ** 2)
        if distance <= body.radius:
            return body
    return None


def draw_cartesian_plane(screen, camera, show_grid=True):
    global small_font
    if not show_grid:
        return

    W, H = screen.get_size()

    # Get optimal grid spacing for current zoom level
    grid_spacing_world = get_optimal_grid_spacing(camera.zoom)
    grid_spacing_screen = grid_spacing_world * camera.zoom

    if grid_spacing_screen < 15 or grid_spacing_screen > 200:
        return

    # Find where (0,0) appears on screen
    origin_screen_x, origin_screen_y = camera.world_to_screen(0, 0)

    # Vertical lines
    first_x_world = math.floor((-W // 2 / camera.zoom - camera.pan_x) / grid_spacing_world) * grid_spacing_world
    x_world = first_x_world

    while x_world <= (-W // 2 / camera.zoom - camera.pan_x) + W / camera.zoom:
        x_screen, _ = camera.world_to_screen(x_world, 0)
        if 0 <= x_screen <= W:
            color = AXIS_COLOR if abs(x_world) < grid_spacing_world * 0.001 else GRID_COLOR
            pygame.draw.aaline(screen, color, (int(x_screen), 0), (int(x_screen), H))

            if abs(x_world) > grid_spacing_world * 0.001 and grid_spacing_screen > 25:
                label_text = format_coordinate_label(x_world)
                if label_text:
                    label = small_font.render(label_text, True, WHITE)
                    label_rect = label.get_rect()
                    label_rect.centerx = x_screen
                    label_rect.y = H - label_rect.height - 6
                    if abs(x_screen - origin_screen_x) > 30:
                        screen.blit(label, label_rect)
        x_world += grid_spacing_world

    # Horizontal lines
    first_y_world = math.floor((-H // 2 / camera.zoom - camera.pan_y) / grid_spacing_world) * grid_spacing_world
    y_world = first_y_world

    while y_world <= (-H // 2 / camera.zoom - camera.pan_y) + H / camera.zoom:
        _, y_screen = camera.world_to_screen(0, y_world)
        if 0 <= y_screen <= H:
            color = AXIS_COLOR if abs(y_world) < grid_spacing_world * 0.001 else GRID_COLOR
            pygame.draw.aaline(screen, color, (0, int(y_screen)), (W, int(y_screen)))

            if abs(y_world) > grid_spacing_world * 0.001 and grid_spacing_screen > 25:
                display_y = -y_world
                label_text = format_coordinate_label(display_y)
                if label_text:
                    label = small_font.render(label_text, True, WHITE)
                    label_rect = label.get_rect()
                    label_rect.x = 10
                    label_rect.centery = y_screen
                    if abs(y_screen - origin_screen_y) > 20:
                        screen.blit(label, label_rect)
        y_world += grid_spacing_world

    # Main axes
    if 0 <= origin_screen_x <= W:
        pygame.draw.aaline(screen, AXIS_COLOR, (origin_screen_x, 0), (origin_screen_x, H))
    if 0 <= origin_screen_y <= H:
        pygame.draw.aaline(screen, AXIS_COLOR, (0, origin_screen_y), (W, origin_screen_y))


def format_coordinate_label(value):
    if abs(value) < 0.01:
        return "0"
    elif abs(value) >= 1000 and abs(value) < 1000000:
        return f"{float(value/1000):.1f}K"
    elif abs(value) >= 1000000 and abs(value) < 1000000000:
        return f"{float(value/1000000):.1f}M"
    elif abs(value) >= 1000000000:
        return f"{float(value/1000000000):.1f}B"
    elif abs(value) >= 1:
        return f"{int(value)}"
    else:
        return f"{value:.1f}"


def draw_edit_dialog(screen, body, input_boxes):
    global large_font, small_font, GREEN
    W, H = screen.get_size()
    box_width, box_height = 520, 240
    box_x = W // 2 - box_width // 2
    box_y = H // 2 - box_height // 2

    box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
    pygame.draw.rect(screen, DARK_GRAY, box_rect, border_radius=12)
    pygame.draw.rect(screen, WHITE, box_rect, 2, border_radius=12)

    title_surface = large_font.render(f"Editing — {body.name}", True, WHITE)
    screen.blit(title_surface, (box_x + 16, box_y + 12))

    current_info = f"Current Vx: {body.vx:.2f}   Vy: {-body.vy:.2f}"
    info_surface = small_font.render(current_info, True, GREEN)
    screen.blit(info_surface, (box_x + 16, box_y + 56))

    instructions = [
        "Edit velocity (Vx, Vy) and Mass (M).",
        "Left click to select a field. Press Enter to apply.",
        "Esc closes this dialog."
    ]
    y_offset = box_y + 84
    for instruction in instructions:
        inst_surface = small_font.render(instruction, True, LIGHT_GRAY)
        screen.blit(inst_surface, (box_x + 16, y_offset))
        y_offset += inst_surface.get_height() + 6

    for box in input_boxes:
        box.draw(screen)


def draw_planet_creation_dialog(screen, input_boxes):
    global large_font, small_font
    W, H = screen.get_size()
    dialog_width, dialog_height = 560, 380
    dialog_x = W // 2 - dialog_width // 2
    dialog_y = H // 2 - dialog_height // 2

    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    pygame.draw.rect(screen, DARK_GRAY, dialog_rect, border_radius=12)
    pygame.draw.rect(screen, WHITE, dialog_rect, 3, border_radius=12)

    title_surface = large_font.render("Create New Planet", True, WHITE)
    screen.blit(title_surface, (dialog_x + 20, dialog_y + 20))

    instructions = [
        "Fill the fields below.",
        "Left click moves between fields.",
        "Press Enter only after all values are set.",
        "Esc closes this dialog."
    ]
    y_offset = dialog_y + 64
    for instruction in instructions:
        inst_surface = small_font.render(instruction, True, LIGHT_GRAY)
        screen.blit(inst_surface, (dialog_x + 20, y_offset))
        y_offset += inst_surface.get_height() + 6

    for box in input_boxes:
        box.draw(screen)


class OrbitSimulation:
    def __init__(self):
        display_info = pygame.display.Info()
        WIDTH, HEIGHT = display_info.current_w, display_info.current_h

        self.screen = pygame.display.set_mode(
        (WIDTH, HEIGHT),
        pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        
        pygame.display.set_caption("Orbital Simulation - Prince Class 11 ")
        set_fonts_for_height(self.screen.get_size()[1])
        self.clock = pygame.time.Clock()

        self.running = True
        self.paused = True
        self.edit_mode = False
        self.selected_body = None
        self.show_grid = True
        self.time_scale = 1.0
        self.fullscreen = False
        self.start_w, self.start_h = WIDTH, HEIGHT

        # Quit button state
        self.quit_rect = pygame.Rect(0, 0, 160, 44)  # will be positioned each frame
        self.quit_hover = False

        # Camera system — viewport follows window size
        w, h = self.screen.get_size()
        self.camera = Camera(w, h)
        set_fonts_for_height(h)

        # Planet creation state
        self.creating_planet = False
        self.creation_input_boxes = []
        self.edit_input_boxes = []

        self.bodies = []
        self.create_sun()
        self.create_earth()
        self.create_moon()
        self.setup_input_boxes()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.start_w, self.start_h), pygame.RESIZABLE)
        w, h = self.screen.get_size()
        self.camera.set_viewport(w, h)
        set_fonts_for_height(h)
        # refresh input box surfaces with new font sizes
        for box in self.creation_input_boxes + self.edit_input_boxes:
            box.refresh_text_surface()

    def create_sun(self):
        sun = Body(0, 0, 27000000, 0, 0, SUN_RADIUS, YELLOW, "Sun")
        sun.make_glow = True
        self.bodies.append(sun)

    def create_earth(self):
        earth = Body(40000, 0, 81, 0, 23.24, PLANET_RADIUS, GREEN, "Earth")
        earth.make_glow = False
        self.bodies.append(earth)

    def create_moon(self):
        moon = Body(40050, 0, 1, 0, 24.37, 4, GRAY, "Moon")
        moon.make_glow = False
        self.bodies.append(moon)
    def spawn_slingshot(self, preset="jupiter"):
        

        # optional: keep existing Sun/Earth/Moon; just clear trails
        for b in self.bodies:
            b.trail.clear()

        # find Sun & Earth if present (for nicer naming/follow)
        sun = next((b for b in self.bodies if b.name.lower() == "sun"), None)
        earth = next((b for b in self.bodies if b.name.lower() == "earth"), None)

        # convenience: a tiny probe color
        PROBE_COLOR = (220, 220, 255)

        if preset == "jupiter":
            # --- Big slingshot: Jupiter + Probe ---
            # Jupiter-like body on prograde +Y
            jupiter = Body(
                x=80000, y=0,
                mass=25758,  # ~318x your Earth=81
                vx=0, vy=16.43,
                radius=10, color=(255, 180, 80), name="Jupiter"
            )
            probe = Body(
                x=82000, y=12000,   # screen input of +6000 becomes world_y = -6000 in your dialog; here we place directly
                mass=0.05,
                vx=-2.0, vy=15.5,
                radius=2, color=PROBE_COLOR, name="Probe-J"
            )
            self.bodies += [jupiter, probe]
            self.camera.follow = probe

        elif preset == "earth":
            # --- Assist using your existing Earth ---
            # Add only a probe that will pass behind Earth (moving +Y)
            probe = Body(
                x=36000, y=12000,
                mass=0.05,
                vx=10.0, vy=31.0,
                radius=2, color=PROBE_COLOR, name="Probe-E"
            )
            self.bodies.append(probe)
            self.camera.follow = probe
        else:
            return  # unknown preset -> do nothing

        # Make sure we can see it nicely
        self.paused = True
        self.time_scale = max(2.0, self.time_scale)  # bump speed a bit


    def setup_input_boxes(self):
        W, H = self.screen.get_size()
        dialog_x = W // 2
        dialog_y = H // 2

        self.creation_input_boxes = [
            InputBox(dialog_x - 220, dialog_y, 140, 36, "X Coordinate:", "0"),
            InputBox(dialog_x - 60, dialog_y, 140, 36, "Y Coordinate:", "0"),
            InputBox(dialog_x + 100, dialog_y, 140, 36, "Mass:", "81"),
            InputBox(dialog_x - 160, dialog_y + 90, 140, 36, "Velocity X:", "0"),
            InputBox(dialog_x + 0,  dialog_y + 90, 140, 36, "Velocity Y:", "24"),
        ]

        edit_x = W // 2
        edit_y = H // 2
        self.edit_input_boxes = [
            InputBox(edit_x - 220, edit_y + 60, 120, 36, "Mass:", "0"),
            InputBox(edit_x - 80,  edit_y + 60, 120, 36, "Velocity X:", "0"),
            InputBox(edit_x + 60,  edit_y + 60, 120, 36, "Velocity Y:", "0"),
        ]

    def handle_planet_creation(self, event):
        if not self.creating_planet:
            return
        for box in self.creation_input_boxes:
            _ = box.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.create_planet_from_input()
                self.creating_planet = False
                return
            if event.key == pygame.K_ESCAPE:
                self.creating_planet = False
                for box in self.creation_input_boxes:
                    box.active = False
                    box.color = box.color_inactive

    def handle_planet_editing(self, event):
        if not self.edit_mode or not self.selected_body:
            return
        for box in self.edit_input_boxes:
            _ = box.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.apply_edit_values()
                self.edit_mode = False
                self.selected_body.selected = False
                self.selected_body = None
                return
            if event.key == pygame.K_ESCAPE:
                self.edit_mode = False
                self.selected_body.selected = False
                self.selected_body = None
                for box in self.edit_input_boxes:
                    box.active = False
                    box.color = box.color_inactive

    def create_planet_from_input(self):
        try:
            x_coord = self.creation_input_boxes[0].get_value()
            y_coord = self.creation_input_boxes[1].get_value()
            mass = self.creation_input_boxes[2].get_value()
            vx = self.creation_input_boxes[3].get_value()
            vy = -self.creation_input_boxes[4].get_value()

            world_x = x_coord
            world_y = -y_coord

            colors = [BLUE, RED, GREEN, ORANGE, PURPLE, CYAN]
            color = random.choice(colors)

            planet = Body(world_x, world_y, mass, vx, vy, 1, color, f"Planet-{len(self.bodies)}")
            self.bodies.append(planet)

            for box in self.creation_input_boxes:
                box.active = False
                box.color = box.color_inactive
        except Exception as e:
            print(f"Error creating planet: {e}")

    def apply_edit_values(self):
        try:
            if self.selected_body:
                self.selected_body.mass = max(50, self.edit_input_boxes[0].get_value())
                self.selected_body.vx = self.edit_input_boxes[1].get_value()
                self.selected_body.vy = -self.edit_input_boxes[2].get_value()
            for box in self.edit_input_boxes:
                box.active = False
                box.color = box.color_inactive
        except Exception as e:
            print(f"Error applying edit values: {e}")

    def _update_quit_button_rect(self):
        """Position the quit button at top-right with padding; size scales with font."""
        global font
        W, H = self.screen.get_size()
        pad = 10
        label = "Quit (Esc)"
        text_surf = font.render(label, True, BLACK)
        tw, th = text_surf.get_size()
        bw = tw + 24
        bh = th + 12
        x = W - bw - pad
        y = pad
        self.quit_rect = pygame.Rect(x, y, bw, bh)

    def _draw_quit_button(self):
        global font
        self._update_quit_button_rect()
        label = "Quit (Esc)"
        # hover state
        mx, my = pygame.mouse.get_pos()
        self.quit_hover = self.quit_rect.collidepoint(mx, my)
        bg = (230, 80, 80) if self.quit_hover else (200, 60, 60)
        pygame.draw.rect(self.screen, bg, self.quit_rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, self.quit_rect, 2, border_radius=10)
        text_surf = font.render(label, True, WHITE)
        tx = self.quit_rect.x + (self.quit_rect.w - text_surf.get_width()) // 2
        ty = self.quit_rect.y + (self.quit_rect.h - text_surf.get_height()) // 2
        self.screen.blit(text_surf, (tx, ty))

    def handle_events(self):
        for event in pygame.event.get():
            mods = pygame.key.get_mods()

            if event.type == pygame.QUIT:
                self.running = False


            if self.creating_planet:
                self.handle_planet_creation(event)
                # Allow quit button even when dialog is open
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.quit_rect.collidepoint(event.pos):
                        self.running = False
                continue

            if self.edit_mode:
                self.handle_planet_editing(event)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.quit_rect.collidepoint(event.pos):
                        self.running = False
                continue

            if event.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if event.y > 0:
                    self.camera.zoom_at_point(mouse_x, mouse_y, ZOOM_SPEED)
                else:
                    self.camera.zoom_at_point(mouse_x, mouse_y, 1 / ZOOM_SPEED)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Quit button click
                    if self.quit_rect.collidepoint(event.pos):
                        self.running = False
                        continue

                    mouse_x, mouse_y = event.pos
                    clicked_body = get_body_at_position(mouse_x, mouse_y, self.bodies, self.camera)
                    self.selected_body = clicked_body
                    if clicked_body:
                        self.camera.follow = clicked_body

                elif event.button == 2:
                    self.camera.stop_follow()
                    self.camera.start_drag(event.pos)

                elif event.button == 3:
                    mouse_x, mouse_y = event.pos
                    clicked_body = get_body_at_position(mouse_x, mouse_y, self.bodies, self.camera)

                    if clicked_body:
                        self.edit_mode = True
                        self.selected_body = clicked_body
                        clicked_body.selected = True

                        self.edit_input_boxes[0].set_value(clicked_body.mass)
                        self.edit_input_boxes[1].set_value(round(clicked_body.vx, 2))
                        self.edit_input_boxes[2].set_value(round(clicked_body.vy, 2))
                        self.edit_input_boxes[0].active = True
                        self.edit_input_boxes[0].color = self.edit_input_boxes[0].color_active
                    else:
                        world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
                        self.creating_planet = True
                        self.creation_input_boxes[0].set_value(int(world_x))
                        self.creation_input_boxes[1].set_value(int(-world_y))
                        self.creation_input_boxes[0].active = True
                        self.creation_input_boxes[0].color = self.creation_input_boxes[0].color_active

            elif event.type == pygame.MOUSEMOTION:
                self.camera.update_drag(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:
                    self.camera.stop_drag()

            elif event.type == pygame.KEYDOWN:
                

                if event.key == pygame.K_ESCAPE:
                    # Quit if no dialog; otherwise close dialog
                    if self.creating_planet:
                        self.creating_planet = False
                        for box in self.creation_input_boxes:
                            box.active = False
                            box.color = box.color_inactive
                    elif self.edit_mode:
                        self.edit_mode = False
                        if self.selected_body:
                            self.selected_body.selected = False
                            self.selected_body = None
                    else:
                        self.running = False

                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused

                elif event.key == pygame.K_LEFTBRACKET:  # [
                    self.time_scale = max(MIN_TIME_SCALE, self.time_scale / 2)

                elif event.key == pygame.K_RIGHTBRACKET:  # ]
                    self.time_scale = min(MAX_TIME_SCALE, self.time_scale * 2)

                elif event.key == pygame.K_c:
                    for body in self.bodies:
                        body.trail.clear()
                elif event.key == pygame.K_1 and (mods & pygame.KMOD_SHIFT):
                    self.spawn_slingshot("jupiter")

                elif event.key == pygame.K_2 and (mods & pygame.KMOD_SHIFT):
                    self.spawn_slingshot("earth")

                elif event.key == pygame.K_r:
                    if mods == 0:  # default mod
                        self.bodies.clear()
                        self.create_sun()
                        self.create_earth()
                        self.create_moon()
                        w, h = self.screen.get_size()
                        self.camera = Camera(w, h)
                        self.edit_mode = False
                        self.selected_body = None
                        self.paused = True
                        self.time_scale = 1.0
                    elif mods == 1:  # shift is pressed
                        self.bodies.clear()
                        w, h = self.screen.get_size()
                        self.camera = Camera(w, h)
                        self.edit_mode = False
                        self.selected_body = None
                        self.paused = True
                        self.time_scale = 1.0

                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid

    def update_physics(self):
        if not self.paused and not self.creating_planet and not self.edit_mode:
            dt = 0.5 * self.time_scale
            apply_mutual_gravity(self.bodies, dt)

    def draw(self, fps, mods):
        self.screen.fill(BLACK)

        # Sync camera viewport in case the OS changed size (safer each frame)
        self.camera.set_viewport(*self.screen.get_size())

        # Draw dynamic cartesian plane
        draw_cartesian_plane(self.screen, self.camera, self.show_grid)

        for body in self.bodies:
            body.draw(self.screen, self.camera)

        # UI overlays
        self.draw_instructions()
        self.draw_info(fps, mods)
        self._draw_quit_button()

        if self.edit_mode and self.selected_body:
            draw_edit_dialog(self.screen, self.selected_body, self.edit_input_boxes)

        if self.creating_planet:
            draw_planet_creation_dialog(self.screen, self.creation_input_boxes)

        # Hover highlight
        if not self.creating_planet and not self.edit_mode and not self.camera.dragging:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            hover_body = get_body_at_position(mouse_x, mouse_y, self.bodies, self.camera)
            if hover_body:
                screen_x, screen_y = self.camera.world_to_screen(hover_body.x, hover_body.y)
                radius = max(3, int(hover_body.radius * self.camera.zoom))
                draw_aacircle_outline(self.screen, screen_x, screen_y, radius + 3, WHITE, thickness=2)

        pygame.display.flip()

    def draw_instructions(self):
        global small_font
        # top-left, responsive margin
        x_pad, y_pad = 18, 10
        instructions = [
            "SPACE: Pause/Resume  |  Mouse Wheel: Zoom  |  Drag: Pan",
            "Left-click: Follow  |  Right-click: Create/Edit",
            "G: Grid  |  C: Clear trails  |  R: Reset Sol/Luna/Terra  |  Shift+R: Clear all",
            "[ : Time ÷2   ] : Time ×2   |   F11: Fullscreen   |   Esc: Quit/Close dialog"
        ]
        y = y_pad
        for line in instructions:
            text_surface = small_font.render(line, True, WHITE)
            self.screen.blit(text_surface, (x_pad, y))
            y += text_surface.get_height() + 4

    def draw_info(self, fps, mods):
        global small_font
        W, H = self.screen.get_size()
        pad = 16
        panel_width = 260  # reserve space for text block width (wider for bigger fonts)

        status_color = RED if self.paused else GREEN
        status_text = "PAUSED" if self.paused else "RUNNING"

        grid_spacing = get_optimal_grid_spacing(self.camera.zoom)

        if self.camera.follow:
            follow_vx = self.camera.follow.vx
            follow_vy = self.camera.follow.vy
            follow_v = math.sqrt(follow_vx**2+follow_vy**2)
            follow_name = str(self.camera.follow)
        else:
            follow_vx = 0
            follow_vy = 0
            follow_v = 0
            follow_name = "None"

        zoom_val = self.camera.zoom
        if zoom_val >= 1:
            zoom_disp = f"{zoom_val:.0f}"
        elif 1 > zoom_val > 0.1:
            zoom_disp = f"{zoom_val:.1f}"
        elif 0.1 >= zoom_val > 0.01:
            zoom_disp = f"{zoom_val:.2f}"
        elif 0.01 >= zoom_val > 0.001:
            zoom_disp = f"{zoom_val:.3f}"
        elif 0.001 >= zoom_val > 0.0001:
            zoom_disp = f"{zoom_val:.4f}"
        elif 0.0001 >= zoom_val > 0.00001:
            zoom_disp = f"{zoom_val:.5f}"
        else:
            zoom_disp = f"{zoom_val:.6f}"

        info_lines = [
            f"Status: {status_text}",
            f"Following: {follow_name}",
            f"   Vx = {follow_vx:.2f} , Vy = {-follow_vy:.2f}",
            f"              V = {follow_v:.2f}",
            f"Time: {self.time_scale:.2f}x",
            f"Bodies: {len(self.bodies)}",
            f"Zoom: {zoom_disp}x",
            f"Grid: {format_coordinate_label(grid_spacing)} units",
            f"FPS: {fps}",
        ]

        # Compute vertical start so block hugs bottom
        total_h = sum(small_font.size(line)[1] + 4 for line in info_lines)
        y = H - total_h - pad
        x = W - panel_width - pad

        for i, line in enumerate(info_lines):
            color = status_color if i == 0 else (YELLOW if i == 5 else WHITE)
            text_surface = small_font.render(line, True, color)
            self.screen.blit(text_surface, (x, y))
            y += text_surface.get_height() + 4

    def run(self):
        while self.running:
            self.handle_events()
            self.update_physics()
            self.clock.tick(60)
            fps = int(self.clock.get_fps())
            mods = pygame.key.get_mods()
            self.camera.update_follow()
            self.draw(fps, mods)
            self.clock.tick(60)

        pygame.quit()


# Run the simulation
if __name__ == "__main__":
    # Initialize fonts before creating UI elements
    set_fonts_for_height(HEIGHT)
    OrbitSimulation().run()

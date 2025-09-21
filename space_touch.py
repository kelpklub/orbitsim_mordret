import math
import random
import pygame

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 700
G = 0.8
PLANET_RADIUS = 12
SUN_RADIUS = 20
MIN_DIST = 1
BASE_GRID_SIZE = 50  # Base grid size in pixels

# Zoom and camera constants
MIN_ZOOM = 0.0000001
MAX_ZOOM = 5.0
ZOOM_SPEED = 1.2

# Time scale
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

# Button colors
BUTTON_COLOR = (70, 70, 100)
BUTTON_HOVER_COLOR = (90, 90, 120)
BUTTON_ACTIVE_COLOR = (110, 110, 140)
BUTTON_TEXT_COLOR = WHITE

# Fonts
font = pygame.font.Font(None, 24)
small_font = pygame.font.Font(None, 18)
large_font = pygame.font.Font(None, 32)
input_font = pygame.font.Font(None, 24)
button_font = pygame.font.Font(None, 16)


class TouchButton:
    """Touch-friendly button class for mobile/tablet interfaces"""

    def __init__(self, x, y, width, height, text, action, tooltip=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.tooltip = tooltip
        self.is_pressed = False
        self.is_hovered = False
        self.enabled = True

    def handle_event(self, event, mouse_pos):
        """Handle mouse/touch events for the button"""
        self.is_hovered = self.rect.collidepoint(mouse_pos) and self.enabled

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:  # Left click/touch
                self.is_pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_pressed:
                self.is_pressed = False
                if self.is_hovered:
                    return self.action

        return None

    def draw(self, screen):
        """Draw the button with appropriate colors based on state"""
        if not self.enabled:
            color = DARK_GRAY
        elif self.is_pressed:
            color = BUTTON_ACTIVE_COLOR
        elif self.is_hovered:
            color = BUTTON_HOVER_COLOR
        else:
            color = BUTTON_COLOR

        # Draw button background
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)

        # Draw button text
        text_color = BUTTON_TEXT_COLOR if self.enabled else GRAY
        text_surface = button_font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

        # Draw tooltip on hover
        if self.is_hovered and self.tooltip:
            tooltip_surface = small_font.render(self.tooltip, True, WHITE)
            tooltip_rect = tooltip_surface.get_rect()
            tooltip_rect.bottomleft = (self.rect.left, self.rect.top - 5)

            # Background for tooltip
            pygame.draw.rect(screen, DARK_GRAY, tooltip_rect.inflate(10, 4))
            pygame.draw.rect(screen, WHITE, tooltip_rect.inflate(10, 4), 1)
            screen.blit(tooltip_surface, tooltip_rect)


class Camera:
    # Camera class for movement and zooming

    def __init__(self):
        self.zoom = 0.01
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.dragging = False
        self.follow = None
        self.last_mouse_pos = (0, 0)

    def world_to_screen(self, world_x, world_y):
        screen_x = (world_x + self.pan_x) * self.zoom + WIDTH // 2
        screen_y = (world_y + self.pan_y) * self.zoom + HEIGHT // 2
        return int(screen_x), int(screen_y)

    def screen_to_world(self, screen_x, screen_y):
        world_x = (screen_x - WIDTH // 2) / self.zoom - self.pan_x
        world_y = (screen_y - HEIGHT // 2) / self.zoom - self.pan_y
        return world_x, world_y

    def zoom_at_point(self, mouse_x, mouse_y, zoom_factor):
        if not self.follow:
            world_x, world_y = self.screen_to_world(mouse_x, mouse_y)

            new_zoom = self.zoom * zoom_factor
            self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, new_zoom))

            new_screen_x, new_screen_y = self.world_to_screen(world_x, world_y)
            self.pan_x += (mouse_x - new_screen_x) / self.zoom
            self.pan_y += (mouse_y - new_screen_y) / self.zoom
        if self.follow:
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


class InputBox:
    # Make input box interactive

    def __init__(self, x, y, w, h, label, default_text='', number_only=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = LIGHT_GRAY
        self.color_active = GREEN
        self.color = self.color_inactive
        self.text = str(default_text)
        self.label = label
        self.txt_surface = input_font.render(self.text, True, WHITE)
        self.active = False
        self.number_only = number_only

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # button 1 is left click
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

                self.txt_surface = input_font.render(self.text, True, WHITE)
        return None

    def draw(self, screen):
        label_surface = small_font.render(self.label, True, WHITE)
        screen.blit(label_surface, (self.rect.x, self.rect.y - 20))

        pygame.draw.rect(screen, BLACK, self.rect)
        pygame.draw.rect(screen, self.color, self.rect, 2)

        text_rect = self.txt_surface.get_rect()
        text_rect.centery = self.rect.centery
        text_rect.x = self.rect.x + 5
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
        self.txt_surface = input_font.render(self.text, True, WHITE)


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
        # Draw trail
        if len(self.trail) > 2:
            trail_color = tuple(c // 2 for c in self.color)
            screen_trail = []
            for world_pos in self.trail:
                screen_pos = camera.world_to_screen(world_pos[0], world_pos[1])
                screen_trail.append(screen_pos)

            if len(screen_trail) > 1:
                for i in range(1, len(screen_trail)):
                    alpha = i / len(screen_trail)
                    color = tuple(int(c * alpha) for c in trail_color)
                    pygame.draw.line(screen, color, screen_trail[i - 1], screen_trail[i], 2)

        # Get screen position
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Only draw if on screen
        margin = 100
        if (-margin < screen_x < WIDTH + margin and -margin < screen_y < HEIGHT + margin):
            color = SELECT_COLOR if self.selected else self.color

            draw_radius = max(3, int(self.radius * camera.zoom))

            if self.make_glow:
                for i in range(3):
                    glow_radius = draw_radius + i * 4
                    glow_alpha = 100 - i * 30
                    glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2))
                    glow_surface.set_alpha(glow_alpha)
                    pygame.draw.circle(glow_surface, self.color,
                                       (glow_radius, glow_radius), glow_radius)
                    screen.blit(glow_surface,
                                (screen_x - glow_radius, screen_y - glow_radius))

            pygame.draw.circle(screen, color, (screen_x, screen_y), draw_radius)

            if self.selected:
                pygame.draw.circle(screen, SELECT_COLOR,
                                   (screen_x, screen_y), draw_radius + 5, 3)

            if camera.zoom > 0.1:
                name_surface = small_font.render(self.name, True, WHITE)
                screen.blit(name_surface, (screen_x + draw_radius + 5, screen_y - 10))

                coord_text = f"({int(self.x)}, {int(-self.y)})"
                coord_surface = small_font.render(coord_text, True, LIGHT_GRAY)
                screen.blit(coord_surface, (screen_x + draw_radius + 5, screen_y + 5))

            if camera.follow:
                if camera.follow.name == self.name:
                    name_surface = small_font.render(self.name, True, WHITE)
                    screen.blit(name_surface, (screen_x + draw_radius + 5, screen_y - 10))

                    coord_text = f"({int(self.x)}, {int(-self.y)})"
                    coord_surface = small_font.render(coord_text, True, LIGHT_GRAY)
                    screen.blit(coord_surface, (screen_x + draw_radius + 5, screen_y + 5))


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
        distance = math.sqrt(math.pow((body.x - world_x), 2) + math.pow((body.y - world_y), 2))
        if distance <= body.radius:
            return body
    return None


def draw_cartesian_plane(screen, camera, show_grid=True):
    if not show_grid:
        return

    grid_spacing_world = get_optimal_grid_spacing(camera.zoom)
    grid_spacing_screen = grid_spacing_world * camera.zoom

    if grid_spacing_screen < 15 or grid_spacing_screen > 200:
        return

    center_x, center_y = WIDTH // 2, HEIGHT // 2

    origin_screen_x, origin_screen_y = camera.world_to_screen(0, 0)

    first_x_world = math.floor((-WIDTH // 2 / camera.zoom - camera.pan_x) / grid_spacing_world) * grid_spacing_world
    x_world = first_x_world

    while x_world <= (-WIDTH // 2 / camera.zoom - camera.pan_x) + WIDTH / camera.zoom:
        x_screen, _ = camera.world_to_screen(x_world, 0)

        if 0 <= x_screen <= WIDTH:
            color = AXIS_COLOR if abs(x_world) < grid_spacing_world * 0.001 else GRID_COLOR

            pygame.draw.line(screen, color, (int(x_screen), 0), (int(x_screen), HEIGHT), 1)

            if abs(x_world) > grid_spacing_world * 0.001 and grid_spacing_screen > 25:
                label_text = format_coordinate_label(x_world)
                if label_text:
                    label = small_font.render(label_text, True, WHITE)
                    label_rect = label.get_rect()
                    label_rect.centerx = x_screen
                    label_rect.y = 680

                    if abs(x_screen - origin_screen_x) > 30:
                        screen.blit(label, label_rect)

        x_world += grid_spacing_world

    first_y_world = math.floor((-HEIGHT // 2 / camera.zoom - camera.pan_y) / grid_spacing_world) * grid_spacing_world
    y_world = first_y_world

    while y_world <= (-HEIGHT // 2 / camera.zoom - camera.pan_y) + HEIGHT / camera.zoom:
        _, y_screen = camera.world_to_screen(0, y_world)

        if 0 <= y_screen <= HEIGHT:
            color = AXIS_COLOR if abs(y_world) < grid_spacing_world * 0.001 else GRID_COLOR

            pygame.draw.line(screen, color, (0, int(y_screen)), (WIDTH, int(y_screen)), 1)

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

    if 0 <= origin_screen_x <= WIDTH:
        pygame.draw.line(screen, AXIS_COLOR, (origin_screen_x, 0), (origin_screen_x, HEIGHT), 2)
    if 0 <= origin_screen_y <= HEIGHT:
        pygame.draw.line(screen, AXIS_COLOR, (0, origin_screen_y), (WIDTH, origin_screen_y), 2)


def format_coordinate_label(value):
    if abs(value) < 0.01:
        return "0"
    elif 1000 <= abs(value) < 1000000:
        return f"{float(value / 1000):.1f}K"
    elif 1000000 <= abs(value) < 1000000000:
        return f"{float(value / 1000000):.1f}M"
    elif abs(value) >= 1000000000:
        return f"{float(value / 1000000000):.1f}B"
    elif abs(value) >= 1:
        return f"{int(value)}"
    else:
        return f"{value:.1f}"


def draw_edit_dialog(screen, body, input_boxes):
    box_width, box_height = 450, 200
    box_x = WIDTH // 2 - box_width // 2
    box_y = HEIGHT // 2 - box_height // 2

    box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
    pygame.draw.rect(screen, DARK_GRAY, box_rect)
    pygame.draw.rect(screen, WHITE, box_rect, 2)

    title = body.name
    title_surface = large_font.render(f"Editing- {title}", True, WHITE)
    screen.blit(title_surface, (box_x + 10, box_y + 10))

    current_info = f"Current Vx: {body.vx:.2f}  Vy: {body.vy:.2f}"
    info_surface = small_font.render(current_info, True, GREEN)
    screen.blit(info_surface, (box_x + 10, box_y + 50))

    instructions = [
        "Edit  velocity components (Vx, Vy)",
        "Edit Mass (M) ",
        "left click to move between fields, Enter to apply"
    ]
    y_offset = 60
    y_offset += 10
    for instruction in instructions:
        inst_surface = small_font.render(instruction, True, LIGHT_GRAY)
        screen.blit(inst_surface, (box_x + 10, box_y + y_offset))
        y_offset += 18

    for box in input_boxes:
        box.draw(screen)


def draw_planet_creation_dialog(screen, input_boxes):
    dialog_width, dialog_height = 500, 350
    dialog_x = WIDTH // 2 - dialog_width // 2
    dialog_y = HEIGHT // 2 - dialog_height // 2

    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    pygame.draw.rect(screen, DARK_GRAY, dialog_rect)
    pygame.draw.rect(screen, WHITE, dialog_rect, 3)

    title_surface = large_font.render("Create New Planet", True, WHITE)
    screen.blit(title_surface, (dialog_x + 20, dialog_y + 20))

    instructions = [
        "Fill in the values below:",
        "Press left Click to move between fields",
        "Press Enter only when all values have been inputed"
    ]

    y_offset = 60
    for instruction in instructions:
        inst_surface = small_font.render(instruction, True, LIGHT_GRAY)
        screen.blit(inst_surface, (dialog_x + 20, dialog_y + y_offset))
        y_offset += 20

    for box in input_boxes:
        box.draw(screen)


class OrbitSimulation:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Orbital Simulation - Prince Class 11 - Touch Controls")
        self.clock = pygame.time.Clock()

        self.running= True
        self.paused= True
        self.edit_mode= False
        self.selected_body= None
        self.show_grid= True
        self.time_scale =1.0
        
        self.maxv = 0

        self.camera = Camera()

        self.creating_planet = False
        self.creation_input_boxes = []
        self.edit_input_boxes = []

        self.touch_buttons = []
        self.setup_touch_buttons()

        self.bodies = []
        self.create_sun()
        self.create_earth()
        self.create_moon()
        self.setup_input_boxes()

    def setup_touch_buttons(self):
        button_width = 70
        button_height = 35
        button_spacing = 5

        y1 = 10
        x_start = WIDTH - 380

        # Row 1
        self.touch_buttons.extend([
            TouchButton(x_start, y1, button_width, button_height, "Play/Pause", "toggle_pause", "Spacebar: Pause/Resume"),
            TouchButton(x_start + (button_width + button_spacing), y1, button_width, button_height, "Slow", "slow_time", "[: Slow down time"),
            TouchButton(x_start + 2 * (button_width + button_spacing), y1, button_width, button_height, "Fast", "fast_time", "]: Speed up time"),
            TouchButton(x_start + 3 * (button_width + button_spacing), y1, button_width, button_height, "Clear Trails", "clear_trails", "C: Clear all trails"),
        ])

        y2 = y1 + button_height + button_spacing
        # Row 2
        self.touch_buttons.extend([
            TouchButton(x_start, y2, button_width, button_height, "Toggle Grid", "toggle_grid", "G: Show/hide grid"),
            TouchButton(x_start + (button_width + button_spacing), y2, button_width, button_height, "Reset", "reset_normal", "R: Reset system"),
            TouchButton(x_start + 2 * (button_width + button_spacing), y2, button_width, button_height, "Clear All", "reset_empty", "Shift+R: Remove all planets"),
            TouchButton(x_start + 3 * (button_width + button_spacing), y2, button_width, button_height, "Stop Follow", "stop_follow", "Middle click: Stop follow"),
        ])

        y3 = y2 + button_height + button_spacing
        zoom_button_width = (button_width * 2) + button_spacing
        # Row 3
        self.touch_buttons.extend([
            TouchButton(x_start, y3, zoom_button_width, button_height, "Zoom In", "zoom_in", "Mouse wheel up: Zoom in"),
            TouchButton(x_start + zoom_button_width + button_spacing, y3, zoom_button_width, button_height, "Zoom Out", "zoom_out", "Mouse wheel down: Zoom out"),
        ])

    def handle_touch_button_action(self, action):
        if action == "toggle_pause":
            self.paused = not self.paused

        elif action == "slow_time":
            self.time_scale = max(MIN_TIME_SCALE, self.time_scale / 2)

        elif action == "fast_time":
            self.time_scale = min(MAX_TIME_SCALE, self.time_scale * 2)

        elif action == "clear_trails":
            for body in self.bodies:
                body.trail.clear()

        elif action == "toggle_grid":
            self.show_grid = not self.show_grid

        elif action == "reset_normal":
            self.bodies.clear()
            self.create_sun()
            self.create_earth()
            self.create_moon()
            self.camera = Camera()
            self.edit_mode = False
            self.selected_body = None
            self.paused = True
            self.time_scale = 1.0

        elif action == "reset_empty":
            self.bodies.clear()
            self.camera = Camera()
            self.edit_mode = False
            self.selected_body = None
            self.paused = True
            self.time_scale = 1.0

        elif action == "stop_follow":
            self.camera.stop_follow()

        elif action == "zoom_in":
                self.camera.zoom_at_point(WIDTH // 2, HEIGHT // 2, ZOOM_SPEED)

        elif action == "zoom_out":
            self.camera.zoom_at_point(WIDTH // 2, HEIGHT // 2, 1 / ZOOM_SPEED)

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

    def setup_input_boxes(self):
        dialog_x = WIDTH // 2
        dialog_y = HEIGHT // 2

        self.creation_input_boxes = [
            InputBox(dialog_x - 200, dialog_y, 120, 30, "X Coordinate:", "0"),
            InputBox(dialog_x - 50, dialog_y, 120, 30, "Y Coordinate:", "0"),
            InputBox(dialog_x + 100, dialog_y, 120, 30, "Mass:", "81"),
            InputBox(dialog_x - 150, dialog_y + 75, 120, 30, "Velocity X:", "0"),
            InputBox(dialog_x, dialog_y + 75, 120, 30, "Velocity Y:", "24"),
        ]

        edit_x = WIDTH // 2
        edit_y = HEIGHT // 2

        self.edit_input_boxes = [
            InputBox(edit_x - 200, edit_y + 50, 100, 30, "Mass:", "0"),
            InputBox(edit_x - 50, edit_y + 50, 100, 30, "Velocity X:", "0"),
            InputBox(edit_x + 100, edit_y + 50, 100, 30, "Velocity Y:", "0"),
        ]

    def handle_planet_creation(self, event):
        if not self.creating_planet:
            return

        for box in self.creation_input_boxes:
            box.handle_event(event)

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
            box.handle_event(event)

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
            vy = self.creation_input_boxes[4].get_value()

            world_x = x_coord
            world_y = -y_coord

            colors = [BLUE, RED, GREEN, ORANGE, PURPLE, CYAN]
            color = random.choice(colors)

            planet = Body(world_x, world_y, mass, vx, vy,
                         1, color, f"Planet-{len(self.bodies)}")
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
                self.selected_body.vy = self.edit_input_boxes[2].get_value()

            for box in self.edit_input_boxes:
                box.active = False
                box.color = box.color_inactive

        except Exception as e:
            print(f"Error applying edit values: {e}")

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            mods = pygame.key.get_mods()

            if event.type == pygame.QUIT:
                self.running = False

            # Handle touch buttons with priority
            if not self.creating_planet and not self.edit_mode:
                for button in self.touch_buttons:
                    action = button.handle_event(event, mouse_pos)
                    if action and isinstance(action, str):
                        self.handle_touch_button_action(action)
                        # Avoid other event handling if button handled the event
                        if action:
                            break

            if self.creating_planet:
                self.handle_planet_creation(event)
                continue

            if self.edit_mode:
                self.handle_planet_editing(event)
                continue

            if event.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if event.y > 0:
                    self.camera.zoom_at_point(mouse_x, mouse_y, ZOOM_SPEED)
                else:
                    self.camera.zoom_at_point(mouse_x, mouse_y, 1 / ZOOM_SPEED)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                

                if event.button == 3:
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

                elif event.button == 1:
                    mouse_x, mouse_y = event.pos
                    clicked_body = get_body_at_position(mouse_x, mouse_y, self.bodies, self.camera)
                    self.selected_body = clicked_body
                    if clicked_body:
                        self.camera.follow = clicked_body
                    if not clicked_body:
                        #self.camera.stop_follow()
                        self.camera.start_drag(event.pos)
                        

            elif event.type == pygame.MOUSEMOTION:
                self.camera.update_drag(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.camera.stop_drag()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_LEFTBRACKET:
                    self.time_scale = max(MIN_TIME_SCALE, self.time_scale / 2)

                elif event.key == pygame.K_RIGHTBRACKET:
                    self.time_scale = min(MAX_TIME_SCALE, self.time_scale * 2)
                elif event.key == pygame.K_c:
                    for body in self.bodies:
                        body.trail.clear()

                elif event.key == pygame.K_r:
                    if mods == 4096:
                        self.bodies.clear()
                        self.create_sun()
                        self.create_earth()
                        self.create_moon()
                        self.camera = Camera()
                        self.edit_mode = False
                        self.selected_body = None
                        self.paused = True
                        self.time_scale = 1.0
                    elif mods == 4097:
                        self.bodies.clear()
                        self.camera = Camera()
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

    def draw_touch_buttons(self):
        mouse_pos = pygame.mouse.get_pos()

        for button in self.touch_buttons:
            button.is_hovered = button.rect.collidepoint(mouse_pos) and button.enabled

        for button in self.touch_buttons:
            button.draw(self.screen)

    def draw(self, fps, mods):
        self.screen.fill(BLACK)

        draw_cartesian_plane(self.screen, self.camera, self.show_grid)

        for body in self.bodies:
            body.draw(self.screen, self.camera)

        if not self.creating_planet and not self.edit_mode:
            self.draw_touch_buttons()

        self.draw_info(fps, mods)

        if self.edit_mode and self.selected_body:
            draw_edit_dialog(self.screen, self.selected_body, self.edit_input_boxes)

        if self.creating_planet:
            draw_planet_creation_dialog(self.screen, self.creation_input_boxes)

        if not self.creating_planet and not self.edit_mode and not self.camera.dragging:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            hover_body = get_body_at_position(mouse_x, mouse_y, self.bodies, self.camera)
            if hover_body:
                screen_x, screen_y = self.camera.world_to_screen(hover_body.x, hover_body.y)
                radius = max(3, int(hover_body.radius * self.camera.zoom))
                pygame.draw.circle(self.screen, WHITE, (screen_x, screen_y), radius + 3, 2)

        pygame.display.flip()

    def draw_info(self, fps, mods):
        status_color = RED if self.paused else GREEN
        status_text = "PAUSED" if self.paused else "RUNNING"

        grid_spacing = get_optimal_grid_spacing(self.camera.zoom)
        if self.camera.follow:
            #gets vy and  vx for body currrently following
            follow_vy=self.camera.follow.vy
            follow_vx=self.camera.follow.vx
            velocity = math.sqrt(follow_vx**2+follow_vy**2)
            self.maxv = max(self.maxv,velocity)
        else:
            follow_vx=0
            follow_vy=0
            velocity =0
            self.maxv=0

        zoom = self.camera.zoom
        if zoom >= 1:
            zoom = f"{self.camera.zoom:.0f}"
        elif zoom < 1 and zoom > 0.1:
            zoom = f"{self.camera.zoom:.1f}"
        elif zoom < 0.1 and zoom > 0.01:
            zoom = f"{self.camera.zoom:.2f}"
        elif zoom < 0.01 and zoom > 0.001:
            zoom = f"{self.camera.zoom:.3f}"
        elif zoom < 0.001 and zoom > 0.0001:
            zoom = f"{self.camera.zoom:.4f}"
        elif zoom < 0.0001 and zoom > 0.00001:
            zoom = f"{self.camera.zoom:.5f}"
        elif zoom < 0.00001 and zoom > 0.000001:
            zoom = f"{self.camera.zoom:.6f}"
        elif zoom < 0.000001:
            zoom = f"{self.camera.zoom:.7f}"

        info_lines = [
            f"Status: {status_text}",
            f"Planet Following: {self.camera.follow}",
            f"      Vx = {follow_vx:.2f} , Vy = {follow_vy:.2f}",
            f"      V  = {velocity:.1f}  ,Max V = {self.maxv:.1f}",
            f"Time: {self.time_scale:.2f}x",
            f"Bodies: {len(self.bodies)}",
            f"Zoom: {zoom}x",
            f"Grid: {format_coordinate_label(grid_spacing)} units",
            f"Fps: {(fps)}",
            f"Debug Key Mods:{(mods)}"
        ]

        y_offset = HEIGHT - 200

        for i, line in enumerate(info_lines):
            if i == 0:
                color = status_color
            elif i == 5:
                color = YELLOW
            else:
                color = WHITE
            text_surface = small_font.render(line, True, color)
            self.screen.blit(text_surface, (WIDTH - 200, y_offset))
            y_offset += 15

    def run(self):
        while self.running:
            self.handle_events()
            self.update_physics()
            fps = int(self.clock.get_fps())
            mods = pygame.key.get_mods()
            self.draw(fps, mods)
            self.camera.update_follow()
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    OrbitSimulation().run()


"""
Advanced Orbital Simulation with Realistic Scale
===============================================

New Scale System:
- Mass: 1 unit = 10^24 kg
  * Sun: ~1,988,000 units (1.988×10^30 kg)  
  * Earth: ~5.972 units (5.972×10^24 kg)
  * Moon: ~0.0735 units (7.348×10^22 kg)
- Distance: 1 unit = 10^8 meters  
- Velocity: Realistic orbital speeds

Features:
- Time control: [ ] keys for speed control
- Solar system preset: Press '1'
- Predictive paths: Press 'P' 
- Fixed grid drawing
- No input limits - enter any values
- Ruler-style coordinates
"""

import pygame
import math
import random
import copy

# Initialize Pygame
pygame.init()

# Constants with new scale
WIDTH, HEIGHT = 1000, 700
G = 6.67e-11  # Real gravitational constant
PLANET_RADIUS = 8
SUN_RADIUS = 15
MIN_DIST = 0.1  # Minimum distance in new units

# Scale factors
MASS_SCALE = 1e24  # 1 unit = 10^24 kg
DISTANCE_SCALE = 1e8  # 1 unit = 10^8 meters (100 million meters)
TIME_SCALE = 86400  # 1 time unit = 1 day in seconds

# Zoom and camera constants
MIN_ZOOM = 0.001
MAX_ZOOM = 100.0
ZOOM_SPEED = 1.1

# Time control
MIN_TIME_SCALE = 0.01
MAX_TIME_SCALE = 100.0

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (100, 150, 255)
RED = (255, 100, 100)
GREEN = (100, 255, 100)
ORANGE = (255, 165, 0)
PURPLE = (160, 32, 240)
CYAN = (0, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)
SELECT_COLOR = (255, 0, 128)
GRID_COLOR = (40, 40, 40)
AXIS_COLOR = (80, 80, 80)

# Fonts
font = pygame.font.Font(None, 24)
small_font = pygame.font.Font(None, 18)
large_font = pygame.font.Font(None, 32)
input_font = pygame.font.Font(None, 24)

class Camera:
    """Camera system for zoom and pan"""
    def __init__(self):
        self.zoom = 0.01  # Start zoomed out for large scale
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.dragging = False
        self.last_mouse_pos = (0, 0)

    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        screen_x = (world_x + self.pan_x) * self.zoom + WIDTH // 2
        screen_y = (world_y + self.pan_y) * self.zoom + HEIGHT // 2
        return int(screen_x), int(screen_y)

    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        world_x = (screen_x - WIDTH // 2) / self.zoom - self.pan_x
        world_y = (screen_y - HEIGHT // 2) / self.zoom - self.pan_y
        return world_x, world_y

    def zoom_at_point(self, mouse_x, mouse_y, zoom_factor):
        """Zoom toward a specific point"""
        world_x, world_y = self.screen_to_world(mouse_x, mouse_y)

        new_zoom = self.zoom * zoom_factor
        self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, new_zoom))

        new_screen_x, new_screen_y = self.world_to_screen(world_x, world_y)
        self.pan_x += (mouse_x - new_screen_x) / self.zoom
        self.pan_y += (mouse_y - new_screen_y) / self.zoom

    def start_drag(self, mouse_pos):
        """Start dragging the camera"""
        self.dragging = True
        self.last_mouse_pos = mouse_pos

    def update_drag(self, mouse_pos):
        """Update camera position during drag"""
        if self.dragging:
            dx = mouse_pos[0] - self.last_mouse_pos[0]
            dy = mouse_pos[1] - self.last_mouse_pos[1]

            self.pan_x += dx / self.zoom
            self.pan_y += dy / self.zoom

            self.last_mouse_pos = mouse_pos

    def stop_drag(self):
        """Stop dragging the camera"""
        self.dragging = False

class InputBox:
    """Enhanced input box for numeric text entry"""
    def __init__(self, x, y, w, h, label, default_text='', number_only=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = GRAY
        self.color_active = WHITE
        self.color = self.color_inactive
        self.text = str(default_text)
        self.label = label
        self.txt_surface = input_font.render(self.text, True, WHITE)
        self.active = False
        self.number_only = number_only

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                self.color = self.color_active
            else:
                self.active = False
                self.color = self.color_inactive

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return 'enter'
                elif event.key == pygame.K_TAB:
                    return 'tab'
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    char = event.unicode
                    if char.isprintable():
                        if self.number_only:
                            if char.isdigit() or char in '.-e':
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
        if isinstance(value, float) and (abs(value) >= 1000 or (abs(value) < 0.1 and value != 0)):
            self.text = f"{value:.3e}"
        else:
            self.text = str(round(value, 4))
        self.txt_surface = input_font.render(self.text, True, WHITE)

class Body:
    """Celestial body with realistic scale"""
    def __init__(self, x, y, mass, vx=0, vy=0, radius=PLANET_RADIUS, color=BLUE, name="Body"):
        self.x = float(x)
        self.y = float(y)
        self.mass = float(mass)  # In units of 10^24 kg
        self.vx = float(vx)     # In units per time
        self.vy = float(vy)     # In units per time
        self.radius = radius    # Fixed radius regardless of mass
        self.color = color
        self.name = name

        self.trail = []
        self.prediction_trail = []
        self.selected = False
        self.is_sun = False

        self.fx = 0.0
        self.fy = 0.0

    def calculate_force_from(self, other):
        """Calculate gravitational force from another body"""
        dx = other.x - self.x
        dy = other.y - self.y

        distance_squared = dx * dx + dy * dy
        distance = max(MIN_DIST, math.sqrt(distance_squared))

        # Convert to real units for calculation
        real_distance = distance * DISTANCE_SCALE
        real_mass1 = self.mass * MASS_SCALE
        real_mass2 = other.mass * MASS_SCALE

        # F = G * m1 * m2 / r^2 (in Newtons)
        force_magnitude_real = G * real_mass1 * real_mass2 / (real_distance * real_distance)

        # Convert back to simulation units
        force_magnitude = force_magnitude_real / (MASS_SCALE * DISTANCE_SCALE / TIME_SCALE**2)

        fx = force_magnitude * dx / distance
        fy = force_magnitude * dy / distance

        return fx, fy

    def apply_force(self, fx, fy, dt):
        """Apply force to update velocity and position"""
        if not self.selected:
            ax = fx / self.mass
            ay = fy / self.mass

            self.vx += ax * dt
            self.vy += ay * dt

            self.x += self.vx * dt
            self.y += self.vy * dt

            self.update_trail()

    def update_trail(self):
        """Update orbit trail"""
        current_pos = (self.x, self.y)
        if not self.trail or (abs(self.trail[-1][0] - self.x) > 0.5 or abs(self.trail[-1][1] - self.y) > 0.5):
            self.trail.append(current_pos)

        if len(self.trail) > 500:
            self.trail.pop(0)

    def get_velocity_magnitude(self):
        """Get current velocity magnitude"""
        return math.sqrt(self.vx**2 + self.vy**2)

    def get_velocity_angle(self):
        """Get current velocity angle in degrees"""
        return math.degrees(math.atan2(self.vy, self.vx))

    def copy_state(self):
        """Create a copy of this body for prediction simulation"""
        copy_body = Body(self.x, self.y, self.mass, self.vx, self.vy, self.radius, self.color, self.name)
        copy_body.is_sun = self.is_sun
        return copy_body

    def draw(self, screen, camera, show_predictions=False):
        """Draw the body, trail, and predictions"""
        # Draw trail
        if len(self.trail) > 2:
            trail_color = tuple(c // 2 for c in self.color)
            screen_trail = []
            for world_pos in self.trail[-200:]:  # Limit trail for performance
                screen_pos = camera.world_to_screen(world_pos[0], world_pos[1])
                screen_trail.append(screen_pos)

            if len(screen_trail) > 1:
                for i in range(1, len(screen_trail)):
                    alpha = i / len(screen_trail)
                    color = tuple(int(c * alpha) for c in trail_color)
                    pygame.draw.line(screen, color, screen_trail[i-1], screen_trail[i], 2)

        # Draw prediction trail
        if show_predictions and len(self.prediction_trail) > 2:
            prediction_screen_trail = []
            for world_pos in self.prediction_trail:
                screen_pos = camera.world_to_screen(world_pos[0], world_pos[1])
                prediction_screen_trail.append(screen_pos)

            if len(prediction_screen_trail) > 1:
                for i in range(1, len(prediction_screen_trail)):
                    pygame.draw.line(screen, YELLOW, prediction_screen_trail[i-1], prediction_screen_trail[i], 1)

        # Get screen position
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Only draw if on screen (with margin)
        margin = 200
        if (-margin < screen_x < WIDTH + margin and -margin < screen_y < HEIGHT + margin):
            color = SELECT_COLOR if self.selected else self.color

            # Scale radius based on zoom but keep it visible
            draw_radius = max(3, min(50, int(self.radius * camera.zoom * 10)))

            if self.is_sun:
                for i in range(3):
                    glow_radius = draw_radius + i * 4
                    glow_alpha = max(30, 80 - i * 20)
                    glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2))
                    glow_surface.set_alpha(glow_alpha)
                    pygame.draw.circle(glow_surface, self.color, 
                                     (glow_radius, glow_radius), glow_radius)
                    screen.blit(glow_surface, 
                              (screen_x - glow_radius, screen_y - glow_radius))

            pygame.draw.circle(screen, color, (screen_x, screen_y), max(draw_radius, 3))

            if self.selected:
                pygame.draw.circle(screen, SELECT_COLOR, 
                                 (screen_x, screen_y), max(draw_radius, 3) + 5, 3)

            # Draw name and info (only when zoomed in enough)
            if camera.zoom > 0.005:
                name_surface = small_font.render(self.name, True, WHITE)
                screen.blit(name_surface, (screen_x + max(draw_radius, 3) + 5, screen_y - 10))

                # Show mass in scientific notation for readability
                if self.mass >= 1000 or self.mass < 0.1:
                    mass_text = f"M: {self.mass:.2e}"
                else:
                    mass_text = f"M: {self.mass:.3f}"
                mass_surface = small_font.render(mass_text, True, LIGHT_GRAY)
                screen.blit(mass_surface, (screen_x + max(draw_radius, 3) + 5, screen_y + 5))

def get_optimal_grid_spacing(zoom):
    """Calculate optimal grid spacing based on zoom level - FIXED"""
    target_screen_spacing = 50
    world_spacing = target_screen_spacing / max(zoom, 1e-10)  # Prevent division by very small numbers

    if world_spacing <= 0:
        return 1.0

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
    """Apply mutual gravitational forces between all bodies"""
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

def predict_future_positions(bodies, steps=100, dt=1.0):
    """Predict future positions for all bodies"""
    prediction_bodies = [body.copy_state() for body in bodies]

    for body in bodies:
        body.prediction_trail = []

    for step in range(steps):
        apply_mutual_gravity(prediction_bodies, dt)

        for i, pred_body in enumerate(prediction_bodies):
            if step % 5 == 0:
                bodies[i].prediction_trail.append((pred_body.x, pred_body.y))

def get_body_at_position(screen_x, screen_y, bodies, camera):
    """Find body at given screen position"""
    world_x, world_y = camera.screen_to_world(screen_x, screen_y)

    for body in bodies:
        distance = math.sqrt((body.x - world_x)**2 + (body.y - world_y)**2)
        hit_radius = max(body.radius, 5) / max(camera.zoom, 0.001)  # Scale hit detection with zoom
        if distance <= hit_radius:
            return body
    return None

def draw_ruler_labels(screen, camera, show_grid=True):
    """Draw coordinate markings along screen edges - FIXED"""
    if not show_grid:
        return

    grid_spacing_world = get_optimal_grid_spacing(camera.zoom)
    grid_spacing_screen = grid_spacing_world * camera.zoom

    # FIXED: More lenient thresholds for grid visibility
    if grid_spacing_screen < 5 or grid_spacing_screen > 500:
        return

    # Draw X-axis labels along TOP edge
    visible_width = WIDTH / camera.zoom
    start_x = -camera.pan_x - visible_width / 2
    end_x = -camera.pan_x + visible_width / 2

    first_x_world = math.floor(start_x / grid_spacing_world) * grid_spacing_world
    x_world = first_x_world

    while x_world <= end_x:
        x_screen, _ = camera.world_to_screen(x_world, 0)

        if 0 <= x_screen <= WIDTH:
            label_text = format_coordinate_label(x_world)
            if label_text and abs(x_world) > grid_spacing_world * 0.001:
                label = small_font.render(label_text, True, WHITE)
                label_rect = label.get_rect()
                label_rect.centerx = x_screen
                label_rect.top = 5  # TOP EDGE
                screen.blit(label, label_rect)

        x_world += grid_spacing_world

    # Draw Y-axis labels along LEFT edge
    visible_height = HEIGHT / camera.zoom
    start_y = -camera.pan_y - visible_height / 2
    end_y = -camera.pan_y + visible_height / 2

    first_y_world = math.floor(start_y / grid_spacing_world) * grid_spacing_world
    y_world = first_y_world

    while y_world <= end_y:
        _, y_screen = camera.world_to_screen(0, y_world)

        if 0 <= y_screen <= HEIGHT:
            display_y = -y_world
            label_text = format_coordinate_label(display_y)
            if label_text and abs(display_y) > grid_spacing_world * 0.001:
                label = small_font.render(label_text, True, WHITE)
                label_rect = label.get_rect()
                label_rect.left = 5  # LEFT EDGE
                label_rect.centery = y_screen
                screen.blit(label, label_rect)

        y_world += grid_spacing_world

    # Draw main axes if visible
    origin_screen_x, origin_screen_y = camera.world_to_screen(0, 0)
    if 0 <= origin_screen_x <= WIDTH:
        pygame.draw.line(screen, AXIS_COLOR, (origin_screen_x, 0), (origin_screen_x, HEIGHT), 1)
    if 0 <= origin_screen_y <= HEIGHT:
        pygame.draw.line(screen, AXIS_COLOR, (0, origin_screen_y), (WIDTH, origin_screen_y), 1)

def format_coordinate_label(value):
    """Format coordinate label for display"""
    if abs(value) < 1e-6:
        return "0"
    elif abs(value) >= 1e6:
        return f"{value/1e6:.1f}M"
    elif abs(value) >= 1e3:
        return f"{value/1e3:.1f}k"
    elif abs(value) >= 100:
        return f"{int(value)}"
    elif abs(value) >= 1:
        return f"{value:.1f}"
    else:
        return f"{value:.3f}"

def draw_edit_interface(screen, body, input_boxes):
    """Draw the editing interface"""
    box_width, box_height = 450, 300
    box_x = WIDTH // 2 - box_width // 2
    box_y = HEIGHT // 2 - box_height // 2

    box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
    pygame.draw.rect(screen, DARK_GRAY, box_rect)
    pygame.draw.rect(screen, WHITE, box_rect, 2)

    title = "SUN" if body.is_sun else "PLANET"
    title_surface = large_font.render(f"Editing {title}", True, WHITE)
    screen.blit(title_surface, (box_x + 10, box_y + 10))

    # Current info with proper scaling
    current_speed = body.get_velocity_magnitude()
    current_angle = body.get_velocity_angle()

    current_info = [
        f"Mass: {body.mass:.4f} units (×10²⁴ kg)",
        f"Speed: {current_speed:.4f} units/time",
        f"Angle: {current_angle:.1f}°"
    ]

    y_offset = 50
    for info in current_info:
        info_surface = small_font.render(info, True, LIGHT_GRAY)
        screen.blit(info_surface, (box_x + 10, box_y + y_offset))
        y_offset += 18

    instructions = [
        "Enter any values (no limits)",
        "Tab to move between fields, Enter to apply"
    ]

    y_offset += 10
    for instruction in instructions:
        inst_surface = small_font.render(instruction, True, LIGHT_GRAY)
        screen.blit(inst_surface, (box_x + 10, box_y + y_offset))
        y_offset += 18

    for box in input_boxes:
        box.draw(screen)

def draw_planet_creation_dialog(screen, input_boxes):
    """Draw planet creation dialog"""
    dialog_width, dialog_height = 450, 320
    dialog_x = WIDTH // 2 - dialog_width // 2
    dialog_y = HEIGHT // 2 - dialog_height // 2

    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    pygame.draw.rect(screen, DARK_GRAY, dialog_rect)
    pygame.draw.rect(screen, WHITE, dialog_rect, 3)

    title_surface = large_font.render("Create New Planet", True, WHITE)
    screen.blit(title_surface, (dialog_x + 20, dialog_y + 20))

    instructions = [
        "Realistic Scale: 1 mass unit = 10²⁴ kg, 1 distance unit = 10⁸ m",
        "Examples: Earth ≈ 5.972, Moon ≈ 0.0735, Sun ≈ 1,988,000",
        "Enter any values (scientific notation supported: 1.5e6)",
        "Tab to move between fields, Enter when finished"
    ]

    y_offset = 60
    for instruction in instructions:
        inst_surface = small_font.render(instruction, True, LIGHT_GRAY)
        screen.blit(inst_surface, (dialog_x + 20, dialog_y + y_offset))
        y_offset += 16

    for box in input_boxes:
        box.draw(screen)

class OrbitSimulation:
    """Advanced simulation with realistic scale"""
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Realistic Scale Orbital Simulation")
        self.clock = pygame.time.Clock()

        self.running = True
        self.paused = False
        self.edit_mode = False
        self.selected_body = None
        self.show_grid = True
        self.show_predictions = False

        self.time_scale = 1.0
        self.camera = Camera()

        self.creating_planet = False
        self.creation_input_boxes = []
        self.edit_input_boxes = []

        self.bodies = []
        self.create_sun()
        self.setup_input_boxes()

    def create_sun(self):
        """Create realistic sun"""
        # Sun: 1.988 × 10^30 kg = 1,988,000 units
        sun = Body(0, 0, 1988000, 0, 0, SUN_RADIUS, YELLOW, "Sun")
        sun.is_sun = True
        self.bodies.append(sun)

    def create_solar_system_preset(self):
        """Create realistic Sun-Earth-Moon system"""
        self.bodies.clear()

        # Sun: 1.988 × 10^30 kg = 1,988,000 units
        sun = Body(0, 0, 1988000, 0, 0, SUN_RADIUS, YELLOW, "Sun")
        sun.is_sun = True
        self.bodies.append(sun)

        # Earth: 5.972 × 10^24 kg = 5.972 units
        # Distance: 1.496 × 10^11 m = 1496 units (1 AU)
        # Orbital velocity: ~29,780 m/s = ~0.3 units/time
        earth_distance = 1496  # 1 AU in units of 10^8 m
        earth_velocity = 0.3   # Scaled orbital velocity
        earth = Body(earth_distance, 0, 5.972, 0, earth_velocity, PLANET_RADIUS, BLUE, "Earth")
        self.bodies.append(earth)

        # Moon: 7.348 × 10^22 kg = 0.0735 units
        # Distance from Earth: 3.844 × 10^8 m = 3.844 units
        # Orbital velocity relative to Earth: ~1022 m/s = ~0.01 units/time
        moon_distance = 3.844
        moon_orbital_velocity = 0.01
        moon_x = earth_distance + moon_distance
        moon_y = 0
        moon_vx = 0
        moon_vy = earth_velocity + moon_orbital_velocity
        moon = Body(moon_x, moon_y, 0.0735, moon_vx, moon_vy, PLANET_RADIUS//2, GRAY, "Moon")
        self.bodies.append(moon)

        # Adjust camera for solar system view
        self.camera.zoom = 0.0005
        self.camera.pan_x = 0
        self.camera.pan_y = 0

        print("Realistic solar system preset loaded!")
        print("Sun: 1,988,000 units (1.988×10³⁰ kg)")
        print("Earth: 5.972 units (5.972×10²⁴ kg)")
        print("Moon: 0.0735 units (7.348×10²² kg)")

    def setup_input_boxes(self):
        """Setup input boxes"""
        dialog_x = WIDTH // 2 - 225
        dialog_y = HEIGHT // 2 - 110

        self.creation_input_boxes = [
            InputBox(dialog_x + 20, dialog_y + 120, 120, 30, "X (×10⁸m):", "0"),
            InputBox(dialog_x + 160, dialog_y + 120, 120, 30, "Y (×10⁸m):", "0"),
            InputBox(dialog_x + 300, dialog_y + 120, 120, 30, "Mass (×10²⁴kg):", "5.972"),
            InputBox(dialog_x + 20, dialog_y + 170, 120, 30, "Vx:", "0"),
            InputBox(dialog_x + 160, dialog_y + 170, 120, 30, "Vy:", "0")
        ]

        edit_x = WIDTH // 2 - 180
        edit_y = HEIGHT // 2 - 70

        self.edit_input_boxes = [
            InputBox(edit_x + 20, edit_y + 160, 140, 30, "Mass (×10²⁴kg):", "0"),
            InputBox(edit_x + 180, edit_y + 160, 100, 30, "Vx:", "0"),
            InputBox(edit_x + 300, edit_y + 160, 100, 30, "Vy:", "0")
        ]

    def handle_planet_creation(self, event):
        """Handle planet creation input"""
        if not self.creating_planet:
            return

        for i, box in enumerate(self.creation_input_boxes):
            result = box.handle_event(event)
            if result == 'enter':
                self.create_planet_from_input()
                self.creating_planet = False
                return
            elif result == 'tab':
                box.active = False
                box.color = box.color_inactive
                next_box = self.creation_input_boxes[(i + 1) % len(self.creation_input_boxes)]
                next_box.active = True
                next_box.color = next_box.color_active

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.creating_planet = False
                for box in self.creation_input_boxes:
                    box.active = False
                    box.color = box.color_inactive

    def handle_planet_editing(self, event):
        """Handle planet editing input"""
        if not self.edit_mode or not self.selected_body:
            return

        for i, box in enumerate(self.edit_input_boxes):
            result = box.handle_event(event)
            if result == 'enter':
                self.apply_edit_values()
                self.edit_mode = False
                self.selected_body.selected = False
                self.selected_body = None
                return
            elif result == 'tab':
                box.active = False
                box.color = box.color_inactive
                next_box = self.edit_input_boxes[(i + 1) % len(self.edit_input_boxes)]
                next_box.active = True
                next_box.color = next_box.color_active

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.edit_mode = False
                self.selected_body.selected = False
                self.selected_body = None
                for box in self.edit_input_boxes:
                    box.active = False
                    box.color = box.color_inactive

    def create_planet_from_input(self):
        """Create planet from input values - NO LIMITS"""
        try:
            x_coord = self.creation_input_boxes[0].get_value()
            y_coord = self.creation_input_boxes[1].get_value()
            mass = self.creation_input_boxes[2].get_value()  # NO LIMITS
            vx = self.creation_input_boxes[3].get_value()    # NO LIMITS
            vy = self.creation_input_boxes[4].get_value()    # NO LIMITS

            colors = [BLUE, RED, GREEN, ORANGE, PURPLE, CYAN]
            color = random.choice(colors)

            planet = Body(x_coord, y_coord, mass, vx, vy, PLANET_RADIUS, color, f"Planet-{len(self.bodies)}")
            self.bodies.append(planet)

            for box in self.creation_input_boxes:
                box.active = False
                box.color = box.color_inactive

        except Exception as e:
            print(f"Error creating planet: {e}")

    def apply_edit_values(self):
        """Apply edited values - NO LIMITS"""
        try:
            if self.selected_body:
                self.selected_body.mass = self.edit_input_boxes[0].get_value()  # NO LIMITS
                self.selected_body.vx = self.edit_input_boxes[1].get_value()    # NO LIMITS
                self.selected_body.vy = self.edit_input_boxes[2].get_value()    # NO LIMITS

            for box in self.edit_input_boxes:
                box.active = False
                box.color = box.color_inactive

        except Exception as e:
            print(f"Error applying edit values: {e}")

    def handle_events(self):
        """Handle all events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.creating_planet:
                self.handle_planet_creation(event)
                continue

            if self.edit_mode:
                self.handle_planet_editing(event)
                continue

            elif event.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if event.y > 0:
                    self.camera.zoom_at_point(mouse_x, mouse_y, ZOOM_SPEED)
                else:
                    self.camera.zoom_at_point(mouse_x, mouse_y, 1/ZOOM_SPEED)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.camera.start_drag(event.pos)

                elif event.button == 3:
                    mouse_x, mouse_y = event.pos
                    clicked_body = get_body_at_position(mouse_x, mouse_y, self.bodies, self.camera)

                    if clicked_body:
                        self.edit_mode = True
                        self.selected_body = clicked_body
                        clicked_body.selected = True

                        self.edit_input_boxes[0].set_value(clicked_body.mass)
                        self.edit_input_boxes[1].set_value(clicked_body.vx)
                        self.edit_input_boxes[2].set_value(clicked_body.vy)
                        self.edit_input_boxes[0].active = True
                        self.edit_input_boxes[0].color = self.edit_input_boxes[0].color_active
                    else:
                        world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
                        self.creating_planet = True

                        self.creation_input_boxes[0].set_value(world_x)
                        self.creation_input_boxes[1].set_value(-world_y)
                        self.creation_input_boxes[0].active = True
                        self.creation_input_boxes[0].color = self.creation_input_boxes[0].color_active

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

                elif event.key == pygame.K_1:
                    self.create_solar_system_preset()

                elif event.key == pygame.K_p:
                    self.show_predictions = not self.show_predictions
                    if self.show_predictions:
                        predict_future_positions(self.bodies, steps=80, dt=1.0)

                elif event.key == pygame.K_c:
                    for body in self.bodies:
                        body.trail.clear()

                elif event.key == pygame.K_r:
                    self.bodies.clear()
                    self.create_sun()
                    self.camera = Camera()
                    self.edit_mode = False
                    self.selected_body = None
                    self.paused = False
                    self.time_scale = 1.0

                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid

    def update_physics(self):
        """Update physics with time scaling"""
        if not self.paused and not self.creating_planet and not self.edit_mode:
            dt = 1.0 * self.time_scale
            apply_mutual_gravity(self.bodies, dt)

            # Update predictions periodically
            if self.show_predictions and len(self.bodies) > 0:
                if hasattr(self, 'prediction_counter'):
                    self.prediction_counter += 1
                else:
                    self.prediction_counter = 0

                if self.prediction_counter % 60 == 0:  # Update every second
                    predict_future_positions(self.bodies, steps=60, dt=dt)

    def draw(self):
        """Draw everything"""
        self.screen.fill(BLACK)

        # Draw ruler labels - FIXED
        draw_ruler_labels(self.screen, self.camera, self.show_grid)

        # Draw bodies
        for body in self.bodies:
            body.draw(self.screen, self.camera, self.show_predictions)

        self.draw_ui()

        if self.edit_mode and self.selected_body:
            draw_edit_interface(self.screen, self.selected_body, self.edit_input_boxes)

        if self.creating_planet:
            draw_planet_creation_dialog(self.screen, self.creation_input_boxes)

        # Hover effect
        if not self.creating_planet and not self.edit_mode and not self.camera.dragging:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            hover_body = get_body_at_position(mouse_x, mouse_y, self.bodies, self.camera)
            if hover_body:
                screen_x, screen_y = self.camera.world_to_screen(hover_body.x, hover_body.y)
                radius = max(3, min(50, int(hover_body.radius * self.camera.zoom * 10)))
                pygame.draw.circle(self.screen, WHITE, (screen_x, screen_y), radius + 5, 2)

        pygame.display.flip()

    def draw_ui(self):
        """Draw user interface"""
        instructions = [
            "SPACEBAR: Pause/Resume",
            "[ ] : Time speed control",
            "1: Realistic Solar System",
            "P: Toggle predictions",
            "G: Grid, C: Clear, R: Reset"
        ]

        y_offset = 30
        for instruction in instructions:
            text_surface = small_font.render(instruction, True, WHITE)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 18

        # Status info
        status_color = RED if self.paused else GREEN
        status_text = "PAUSED" if self.paused else "RUNNING"

        info_lines = [
            f"Status: {status_text}",
            f"Time: {self.time_scale:.2f}x",
            f"Bodies: {len(self.bodies)}",
            f"Zoom: {self.camera.zoom:.4f}x",
            f"Scale: 1 unit = 10²⁴ kg",
            f"Predictions: {'ON' if self.show_predictions else 'OFF'}"
        ]

        y_offset = HEIGHT - 140
        for i, line in enumerate(info_lines):
            color = status_color if i == 0 else WHITE
            text_surface = small_font.render(line, True, color)
            self.screen.blit(text_surface, (WIDTH - 250, y_offset))
            y_offset += 20

    def run(self):
        """Main simulation loop"""
        while self.running:
            self.handle_events()
            self.update_physics()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

# Run the simulation
if __name__ == "__main__":
    print("Starting Realistic Scale Orbital Simulation...")
    print("\n🌍 **Realistic Mass Scale (1 unit = 10²⁴ kg):**")
    print("- Sun: 1,988,000 units (1.988×10³⁰ kg)")
    print("- Earth: 5.972 units (5.972×10²⁴ kg)")  
    print("- Moon: 0.0735 units (7.348×10²² kg)")
    print("\n📏 **Distance Scale (1 unit = 10⁸ m):**")
    print("- Earth orbit: 1496 units (1 AU)")
    print("- Moon orbit: 3.844 units from Earth")
    print("\n✅ **Fixed Issues:**")
    print("- Grid drawing restored")
    print("- No input limits - enter any values")
    print("- Supports scientific notation (1.5e6)")
    print("- Realistic physics with proper scaling")
    print("\nPress '1' for realistic solar system!")
    print()

    simulation = OrbitSimulation()
    simulation.run()

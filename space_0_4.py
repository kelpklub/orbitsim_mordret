
"""
Enhanced Orbital Simulation with Improved Velocity Editing
=========================================================

Enhanced planet editing with:
- Mass, Velocity X, Velocity Y input fields
- Direction angle input (alternative to manual X/Y velocities)
- Speed magnitude input
- Current velocity display

Controls remain the same:
- SPACEBAR: Pause/Resume simulation
- Right-click: Create/edit planets with full velocity control
"""

import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 700
G = 0.8
PLANET_RADIUS = 12
SUN_RADIUS = 20
MIN_DIST = 10
GRID_SIZE = 50

# Zoom and camera constants
MIN_ZOOM = 0.1
MAX_ZOOM = 5.0
ZOOM_SPEED = 1.1

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
        self.zoom = 1.0
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
    """Celestial body with scaled physics properties"""
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
        self.is_sun = False

        self.fx = 0.0
        self.fy = 0.0

    def calculate_force_from(self, other):
        """Calculate gravitational force from another body"""
        dx = other.x - self.x
        dy = other.y - self.y

        distance_squared = dx * dx + dy * dy
        distance = max(MIN_DIST, math.sqrt(distance_squared))

        force_magnitude = G * self.mass * other.mass / (distance * distance)

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
        if not self.trail or abs(self.trail[-1][0] - self.x) > 2 or abs(self.trail[-1][1] - self.y) > 2:
            self.trail.append(current_pos)

        if len(self.trail) > 200:
            self.trail.pop(0)

    def get_velocity_magnitude(self):
        """Get current velocity magnitude"""
        return math.sqrt(self.vx**2 + self.vy**2)

    def get_velocity_angle(self):
        """Get current velocity angle in degrees"""
        return math.degrees(math.atan2(self.vy, self.vx))

    def draw(self, screen, camera):
        """Draw the body and its trail with camera transformation"""
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
                    pygame.draw.line(screen, color, screen_trail[i-1], screen_trail[i], 2)

        # Get screen position
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Only draw if on screen
        margin = 100
        if (-margin < screen_x < WIDTH + margin and -margin < screen_y < HEIGHT + margin):
            color = SELECT_COLOR if self.selected else self.color

            draw_radius = max(3, int(self.radius * camera.zoom))

            if self.is_sun:
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

            # Draw name and coordinates
            if camera.zoom > 0.5:
                name_surface = small_font.render(self.name, True, WHITE)
                screen.blit(name_surface, (screen_x + draw_radius + 5, screen_y - 10))

                coord_text = f"({int(self.x)}, {int(-self.y)})"
                coord_surface = small_font.render(coord_text, True, LIGHT_GRAY)
                screen.blit(coord_surface, (screen_x + draw_radius + 5, screen_y + 5))

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

def get_body_at_position(screen_x, screen_y, bodies, camera):
    """Find body at given screen position"""
    world_x, world_y = camera.screen_to_world(screen_x, screen_y)

    for body in bodies:
        distance = math.sqrt((body.x - world_x)**2 + (body.y - world_y)**2)
        if distance <= body.radius:
            return body
    return None

def draw_cartesian_plane(screen, camera, show_grid=True):
    """Draw cartesian coordinate system with camera transformation"""
    if not show_grid:
        return

    grid_spacing = GRID_SIZE * camera.zoom

    if grid_spacing < 10 or grid_spacing > 200:
        return

    offset_x = (camera.pan_x * camera.zoom) % grid_spacing
    offset_y = (camera.pan_y * camera.zoom) % grid_spacing

    # Draw vertical grid lines
    x = offset_x
    while x < WIDTH:
        world_x = (x - WIDTH // 2) / camera.zoom - camera.pan_x
        color = AXIS_COLOR if abs(world_x) < 1 else GRID_COLOR
        pygame.draw.line(screen, color, (int(x), 0), (int(x), HEIGHT), 1)
        x += grid_spacing

    # Draw horizontal grid lines
    y = offset_y
    while y < HEIGHT:
        world_y = -((y - HEIGHT // 2) / camera.zoom - camera.pan_y)
        color = AXIS_COLOR if abs(world_y) < 1 else GRID_COLOR
        pygame.draw.line(screen, color, (0, int(y)), (WIDTH, int(y)), 1)
        y += grid_spacing

    # Draw main axes
    origin_screen_x, origin_screen_y = camera.world_to_screen(0, 0)
    if 0 <= origin_screen_x <= WIDTH:
        pygame.draw.line(screen, AXIS_COLOR, (origin_screen_x, 0), (origin_screen_x, HEIGHT), 2)
    if 0 <= origin_screen_y <= HEIGHT:
        pygame.draw.line(screen, AXIS_COLOR, (0, origin_screen_y), (WIDTH, origin_screen_y), 2)

def draw_edit_interface(screen, body, input_boxes):
    """Draw the enhanced velocity editing interface for selected body"""
    box_width, box_height = 450, 320
    box_x = WIDTH // 2 - box_width // 2
    box_y = HEIGHT // 2 - box_height // 2

    box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
    pygame.draw.rect(screen, DARK_GRAY, box_rect)
    pygame.draw.rect(screen, WHITE, box_rect, 2)

    title = "SUN" if body.is_sun else "PLANET"
    title_surface = large_font.render(f"Editing {title}", True, WHITE)
    screen.blit(title_surface, (box_x + 10, box_y + 10))

    # Current velocity display
    current_speed = body.get_velocity_magnitude()
    current_angle = body.get_velocity_angle()

    current_info = [
        f"Current Speed: {current_speed:.2f}",
        f"Current Angle: {current_angle:.1f}Â°",
        f"Current Vx: {body.vx:.2f}, Vy: {body.vy:.2f}"
    ]

    y_offset = 50
    for info in current_info:
        info_surface = small_font.render(info, True, LIGHT_GRAY)
        screen.blit(info_surface, (box_x + 10, box_y + y_offset))
        y_offset += 18

    # Instructions
    instructions = [
        "Method 1: Enter direct velocity components (Vx, Vy)",
        "Method 2: Enter speed and direction angle",
        "Tab to move between fields, Enter to apply"
    ]

    y_offset += 10
    for instruction in instructions:
        inst_surface = small_font.render(instruction, True, LIGHT_GRAY)
        screen.blit(inst_surface, (box_x + 10, box_y + y_offset))
        y_offset += 18

    # Draw input boxes
    for box in input_boxes:
        box.draw(screen)

def draw_planet_creation_dialog(screen, input_boxes):
    """Draw planet creation dialog with all input fields visible"""
    dialog_width, dialog_height = 450, 350
    dialog_x = WIDTH // 2 - dialog_width // 2
    dialog_y = HEIGHT // 2 - dialog_height // 2

    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    pygame.draw.rect(screen, DARK_GRAY, dialog_rect)
    pygame.draw.rect(screen, WHITE, dialog_rect, 3)

    title_surface = large_font.render("Create New Planet", True, WHITE)
    screen.blit(title_surface, (dialog_x + 20, dialog_y + 20))

    # Instructions
    instructions = [
        "Fill in the values below:",
        "Press Tab to move between fields",
        "Press Enter when finished"
    ]

    y_offset = 60
    for instruction in instructions:
        inst_surface = small_font.render(instruction, True, LIGHT_GRAY)
        screen.blit(inst_surface, (dialog_x + 20, dialog_y + y_offset))
        y_offset += 20

    # Draw all input boxes
    for box in input_boxes:
        box.draw(screen)

class OrbitSimulation:
    """Main simulation class with enhanced velocity editing"""
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Enhanced Orbital Sim with Velocity Editor")
        self.clock = pygame.time.Clock()

        self.running = True
        self.paused = False
        self.edit_mode = False
        self.selected_body = None
        self.show_grid = True

        # Camera system
        self.camera = Camera()

        # Planet creation state
        self.creating_planet = False
        self.creation_input_boxes = []
        self.edit_input_boxes = []

        self.bodies = []
        self.create_sun()
        self.setup_input_boxes()

    def create_sun(self):
        """Create the central sun at origin"""
        sun = Body(0, 0, 600, 0, 0, SUN_RADIUS, YELLOW, "Sun")
        sun.is_sun = True
        self.bodies.append(sun)

    def setup_input_boxes(self):
        """Setup input boxes for planet creation and editing"""
        # Planet creation input boxes
        dialog_x = WIDTH // 2 - 225
        dialog_y = HEIGHT // 2 - 100

        self.creation_input_boxes = [
            InputBox(dialog_x + 20, dialog_y + 140, 120, 30, "X Coordinate:", "0"),
            InputBox(dialog_x + 160, dialog_y + 140, 120, 30, "Y Coordinate:", "0"),
            InputBox(dialog_x + 300, dialog_y + 140, 120, 30, "Mass:", "300"),
            InputBox(dialog_x + 20, dialog_y + 190, 120, 30, "Velocity X:", "0"),
            InputBox(dialog_x + 160, dialog_y + 190, 120, 30, "Velocity Y:", "0"),
            InputBox(dialog_x + 300, dialog_y + 190, 120, 30, "Direction (Â°):", "0")
        ]

        # ENHANCED Edit input boxes with more velocity options
        edit_x = WIDTH // 2 - 225
        edit_y = HEIGHT // 2 - 80

        self.edit_input_boxes = [
            InputBox(edit_x + 20, edit_y + 160, 100, 30, "Mass:", "0"),
            InputBox(edit_x + 140, edit_y + 160, 100, 30, "Velocity X:", "0"),
            InputBox(edit_x + 260, edit_y + 160, 100, 30, "Velocity Y:", "0"),
            InputBox(edit_x + 20, edit_y + 210, 100, 30, "Speed:", "0"),
            InputBox(edit_x + 140, edit_y + 210, 100, 30, "Direction (Â°):", "0")
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
        """Handle enhanced planet editing input"""
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
        """Create planet from input box values"""
        try:
            x_coord = self.creation_input_boxes[0].get_value()
            y_coord = self.creation_input_boxes[1].get_value()
            mass = max(50, self.creation_input_boxes[2].get_value())
            vx = self.creation_input_boxes[3].get_value()
            vy = self.creation_input_boxes[4].get_value()
            direction_deg = self.creation_input_boxes[5].get_value()

            # If direction is specified and velocities are zero, use direction
            if direction_deg != 0 and vx == 0 and vy == 0:
                direction_rad = math.radians(direction_deg)
                speed = 5.0
                vx = speed * math.cos(direction_rad)
                vy = speed * math.sin(direction_rad)

            world_x = x_coord
            world_y = -y_coord

            colors = [BLUE, RED, GREEN, ORANGE, PURPLE, CYAN]
            color = random.choice(colors)

            planet = Body(world_x, world_y, mass, vx, vy, 
                         max(8, int(mass/50)), color, f"Planet-{len(self.bodies)}")
            self.bodies.append(planet)

            for box in self.creation_input_boxes:
                box.active = False
                box.color = box.color_inactive

        except Exception as e:
            print(f"Error creating planet: {e}")

    def apply_edit_values(self):
        """Apply edited values to selected body with enhanced velocity options"""
        try:
            if self.selected_body:
                # Apply mass
                self.selected_body.mass = max(50, self.edit_input_boxes[0].get_value())

                # Get velocity values
                vx_input = self.edit_input_boxes[1].get_value()
                vy_input = self.edit_input_boxes[2].get_value()
                speed_input = self.edit_input_boxes[3].get_value()
                direction_input = self.edit_input_boxes[4].get_value()

                # Determine which method to use for velocity
                if speed_input != 0 or direction_input != 0:
                    # Use speed/direction method
                    if speed_input == 0:
                        speed_input = self.selected_body.get_velocity_magnitude()
                    if direction_input == 0:
                        direction_input = self.selected_body.get_velocity_angle()

                    direction_rad = math.radians(direction_input)
                    self.selected_body.vx = speed_input * math.cos(direction_rad)
                    self.selected_body.vy = speed_input * math.sin(direction_rad)
                else:
                    # Use direct velocity components
                    self.selected_body.vx = vx_input
                    self.selected_body.vy = vy_input

            for box in self.edit_input_boxes:
                box.active = False
                box.color = box.color_inactive

        except Exception as e:
            print(f"Error applying edit values: {e}")

    def handle_events(self):
        """Handle all pygame events"""
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
                        # Start editing with enhanced velocity options
                        self.edit_mode = True
                        self.selected_body = clicked_body
                        clicked_body.selected = True

                        # Pre-fill edit boxes with current values
                        self.edit_input_boxes[0].set_value(clicked_body.mass)
                        self.edit_input_boxes[1].set_value(round(clicked_body.vx, 2))
                        self.edit_input_boxes[2].set_value(round(clicked_body.vy, 2))
                        self.edit_input_boxes[3].set_value(round(clicked_body.get_velocity_magnitude(), 2))
                        self.edit_input_boxes[4].set_value(round(clicked_body.get_velocity_angle(), 1))
                        self.edit_input_boxes[0].active = True
                        self.edit_input_boxes[0].color = self.edit_input_boxes[0].color_active
                    else:
                        # Start planet creation
                        world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
                        self.creating_planet = True

                        self.creation_input_boxes[0].set_value(int(world_x))
                        self.creation_input_boxes[1].set_value(int(-world_y))
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

                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid

    def update_physics(self):
        """Update simulation physics (only if not paused)"""
        if not self.paused and not self.creating_planet and not self.edit_mode:
            dt = 0.5
            apply_mutual_gravity(self.bodies, dt)

    def draw(self):
        """Draw everything"""
        self.screen.fill(BLACK)

        draw_cartesian_plane(self.screen, self.camera, self.show_grid)

        for body in self.bodies:
            body.draw(self.screen, self.camera)

        self.draw_instructions()
        self.draw_info()

        if self.edit_mode and self.selected_body:
            draw_edit_interface(self.screen, self.selected_body, self.edit_input_boxes)

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

    def draw_instructions(self):
        """Draw control instructions"""
        instructions = [
            "SPACEBAR: Pause/Resume simulation",
            "Mouse wheel: Zoom, Left-drag: Pan",
            "Right-click: Create/edit with velocity controls",
            "G: Grid, C: Clear trails, R: Reset"
        ]

        y_offset = 10
        for instruction in instructions:
            text_surface = small_font.render(instruction, True, WHITE)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 20

    def draw_info(self):
        """Draw simulation information"""
        status_color = RED if self.paused else GREEN
        status_text = "PAUSED" if self.paused else "RUNNING"

        info_lines = [
            f"Status: {status_text}",
            f"Bodies: {len(self.bodies)}",
            f"Zoom: {self.camera.zoom:.2f}x",
            f"Grid: {'ON' if self.show_grid else 'OFF'}"
        ]

        y_offset = HEIGHT - 100
        for i, line in enumerate(info_lines):
            color = status_color if i == 0 else WHITE
            text_surface = small_font.render(line, True, color)
            self.screen.blit(text_surface, (WIDTH - 200, y_offset))
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
    print("Starting Enhanced Orbital Simulation with Velocity Editor...")
    print("Planet Editing Features:")
    print("âœ“ Mass input field")
    print("âœ“ Direct velocity components (Vx, Vy)")
    print("âœ“ Speed and direction angle inputs")  
    print("âœ“ Current velocity display")
    print("âœ“ Two methods: direct components OR speed/angle")
    print()
    print("How to edit planets:")
    print("1. Right-click any planet")
    print("2. See current velocity info at top")
    print("3. Method 1: Enter Vx and Vy directly")
    print("4. Method 2: Enter Speed and Direction angle")
    print("5. Tab between fields, Enter to apply")
    print()

    simulation = OrbitSimulation()
    simulation.run()
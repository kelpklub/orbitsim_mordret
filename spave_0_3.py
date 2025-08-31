
"""
2D Orbital Mechanics Simulation with Interactive Planet Placement
===============================================================

Features:
- Cartesian plane background grid
- Right-click to place planet with coordinate input
- Direction input in degrees for initial velocity
- Full N-body mutual gravity physics
- Real-time editing of planet properties

Controls:
- Right-click empty space: Input coordinates and direction for new planet
- Right-click existing body: Edit properties
- During editing: â†‘/â†“ mass, WASD velocity, Enter/Esc finish
- C: Clear trails, R: Reset, G: Toggle grid
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
GRID_SIZE = 50  # Grid spacing in pixels

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
input_font = pygame.font.Font(None, 28)

class InputBox:
    """Input box for text entry"""
    def __init__(self, x, y, w, h, label, default_text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = GRAY
        self.color_active = WHITE
        self.color = self.color_inactive
        self.text = default_text
        self.label = label
        self.txt_surface = input_font.render(self.text, True, WHITE)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return 'enter'
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if event.unicode.isprintable():
                        self.text += event.unicode
                self.txt_surface = input_font.render(self.text, True, WHITE)
        return None

    def draw(self, screen):
        # Draw label
        label_surface = font.render(self.label, True, WHITE)
        screen.blit(label_surface, (self.rect.x, self.rect.y - 25))

        # Draw input box
        pygame.draw.rect(screen, self.color, self.rect, 2)
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))

    def get_value(self):
        try:
            return float(self.text) if self.text else 0.0
        except ValueError:
            return 0.0

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

        # Visual properties
        self.trail = []
        self.selected = False
        self.is_sun = False

        # Physics tracking
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
        current_pos = (int(self.x), int(self.y))
        if not self.trail or self.trail[-1] != current_pos:
            self.trail.append(current_pos)

        if len(self.trail) > 200:
            self.trail.pop(0)

    def draw(self, screen):
        """Draw the body and its trail"""
        # Draw trail
        if len(self.trail) > 2:
            trail_color = tuple(c // 2 for c in self.color)
            for i in range(1, len(self.trail)):
                alpha = i / len(self.trail)
                color = tuple(int(c * alpha) for c in trail_color)
                if i < len(self.trail) - 1:
                    pygame.draw.line(screen, color, self.trail[i-1], self.trail[i], 2)

        # Draw body
        color = SELECT_COLOR if self.selected else self.color

        if self.is_sun:
            for i in range(3):
                glow_radius = self.radius + i * 4
                glow_alpha = 100 - i * 30
                glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2))
                glow_surface.set_alpha(glow_alpha)
                pygame.draw.circle(glow_surface, self.color, 
                                 (glow_radius, glow_radius), glow_radius)
                screen.blit(glow_surface, 
                          (self.x - glow_radius, self.y - glow_radius))

        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)

        if self.selected:
            pygame.draw.circle(screen, SELECT_COLOR, 
                             (int(self.x), int(self.y)), self.radius + 5, 3)

        # Draw name and coordinates
        name_surface = small_font.render(self.name, True, WHITE)
        screen.blit(name_surface, (self.x + self.radius + 5, self.y - 10))

        # Show coordinates
        coord_text = f"({int(self.x-WIDTH//2)}, {int(HEIGHT//2-self.y)})"
        coord_surface = small_font.render(coord_text, True, LIGHT_GRAY)
        screen.blit(coord_surface, (self.x + self.radius + 5, self.y + 5))

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

def get_body_at_position(x, y, bodies):
    """Find body at given position"""
    for body in bodies:
        distance = math.sqrt((body.x - x)**2 + (body.y - y)**2)
        if distance <= body.radius:
            return body
    return None

def draw_cartesian_plane(screen, show_grid=True):
    """Draw cartesian coordinate system"""
    if not show_grid:
        return

    center_x, center_y = WIDTH // 2, HEIGHT // 2

    # Draw grid lines
    for x in range(0, WIDTH, GRID_SIZE):
        color = AXIS_COLOR if x == center_x else GRID_COLOR
        pygame.draw.line(screen, color, (x, 0), (x, HEIGHT), 1)

    for y in range(0, HEIGHT, GRID_SIZE):
        color = AXIS_COLOR if y == center_y else GRID_COLOR
        pygame.draw.line(screen, color, (0, y), (WIDTH, y), 1)

    # Draw main axes
    pygame.draw.line(screen, AXIS_COLOR, (center_x, 0), (center_x, HEIGHT), 2)
    pygame.draw.line(screen, AXIS_COLOR, (0, center_y), (WIDTH, center_y), 2)

    # Draw axis labels
    # X-axis labels
    for x in range(GRID_SIZE, WIDTH, GRID_SIZE):
        coord_val = x - center_x
        if coord_val != 0:
            label = small_font.render(str(coord_val), True, GRAY)
            screen.blit(label, (x - 10, center_y + 5))

    # Y-axis labels  
    for y in range(GRID_SIZE, HEIGHT, GRID_SIZE):
        coord_val = center_y - y
        if coord_val != 0:
            label = small_font.render(str(coord_val), True, GRAY)
            screen.blit(label, (center_x + 5, y - 10))

    # Origin label
    origin_label = font.render("(0,0)", True, WHITE)
    screen.blit(origin_label, (center_x + 10, center_y + 10))

def draw_edit_interface(screen, body):
    """Draw the editing interface for selected body"""
    box_width, box_height = 300, 200
    box_x = WIDTH // 2 - box_width // 2
    box_y = HEIGHT // 2 - box_height // 2

    box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
    pygame.draw.rect(screen, DARK_GRAY, box_rect)
    pygame.draw.rect(screen, WHITE, box_rect, 2)

    title = "SUN" if body.is_sun else "PLANET"
    title_surface = large_font.render(f"Editing {title}", True, WHITE)
    screen.blit(title_surface, (box_x + 10, box_y + 10))

    properties = [
        f"Mass: {body.mass:.1f} [â†‘/â†“ to change]",
        f"Velocity X: {body.vx:.2f} [A/D to change]",
        f"Velocity Y: {body.vy:.2f} [W/S to change]",
        "",
        "Press Enter or Esc to finish"
    ]

    y_offset = 50
    for prop in properties:
        prop_surface = font.render(prop, True, WHITE)
        screen.blit(prop_surface, (box_x + 10, box_y + y_offset))
        y_offset += 25

def draw_planet_creation_dialog(screen, input_boxes, step):
    """Draw planet creation dialog"""
    dialog_width, dialog_height = 400, 300
    dialog_x = WIDTH // 2 - dialog_width // 2
    dialog_y = HEIGHT // 2 - dialog_height // 2

    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    pygame.draw.rect(screen, DARK_GRAY, dialog_rect)
    pygame.draw.rect(screen, WHITE, dialog_rect, 3)

    # Title
    title_surface = large_font.render("Create New Planet", True, WHITE)
    screen.blit(title_surface, (dialog_x + 20, dialog_y + 20))

    # Step indicator
    step_text = f"Step {step}/4"
    step_surface = font.render(step_text, True, LIGHT_GRAY)
    screen.blit(step_surface, (dialog_x + dialog_width - 100, dialog_y + 25))

    # Draw input boxes
    for box in input_boxes:
        box.draw(screen)

    # Instructions
    instructions = [
        "1. Enter X coordinate",
        "2. Enter Y coordinate", 
        "3. Enter mass (100-1000)",
        "4. Enter direction (degrees 0-360)"
    ]

    y_offset = dialog_y + 220
    for i, instruction in enumerate(instructions):
        color = WHITE if i == step - 1 else GRAY
        inst_surface = small_font.render(instruction, True, color)
        screen.blit(inst_surface, (dialog_x + 20, y_offset))
        y_offset += 20

class OrbitSimulation:
    """Main simulation class"""
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Interactive Cartesian Orbital Simulation")
        self.clock = pygame.time.Clock()

        self.running = True
        self.edit_mode = False
        self.selected_body = None
        self.show_grid = True

        # Planet creation state
        self.creating_planet = False
        self.creation_step = 1
        self.input_boxes = []
        self.planet_data = {}

        self.bodies = []
        self.create_sun()
        self.setup_input_boxes()

    def create_sun(self):
        """Create the central sun at origin"""
        sun = Body(WIDTH // 2, HEIGHT // 2, 600, 0, 0, SUN_RADIUS, YELLOW, "Sun")
        sun.is_sun = True
        self.bodies.append(sun)

    def setup_input_boxes(self):
        """Setup input boxes for planet creation"""
        dialog_x = WIDTH // 2 - 200
        dialog_y = HEIGHT // 2 - 100

        self.input_boxes = [
            InputBox(dialog_x + 20, dialog_y + 80, 150, 32, "X Coordinate:", "0"),
            InputBox(dialog_x + 20, dialog_y + 130, 150, 32, "Y Coordinate:", "0"),
            InputBox(dialog_x + 200, dialog_y + 80, 150, 32, "Mass:", "300"),
            InputBox(dialog_x + 200, dialog_y + 130, 150, 32, "Direction (Â°):", "0")
        ]

    def handle_planet_creation(self, event):
        """Handle planet creation input"""
        if not self.creating_planet:
            return

        # Handle input box events
        for i, box in enumerate(self.input_boxes):
            result = box.handle_event(event)
            if result == 'enter':
                if i == self.creation_step - 1:
                    if self.creation_step < 4:
                        self.creation_step += 1
                        self.input_boxes[self.creation_step - 1].active = True
                        self.input_boxes[i].active = False
                    else:
                        # Create the planet
                        self.create_planet_from_input()
                        self.creating_planet = False
                        self.creation_step = 1

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.creating_planet = False
                self.creation_step = 1
                for box in self.input_boxes:
                    box.active = False

    def create_planet_from_input(self):
        """Create planet from input box values"""
        try:
            x_coord = self.input_boxes[0].get_value()
            y_coord = self.input_boxes[1].get_value()
            mass = max(50, min(1000, self.input_boxes[2].get_value()))
            direction_deg = self.input_boxes[3].get_value() % 360

            # Convert screen coordinates (origin at center)
            screen_x = WIDTH // 2 + x_coord
            screen_y = HEIGHT // 2 - y_coord  # Flip Y for cartesian

            # Convert direction to velocity components
            direction_rad = math.radians(direction_deg)
            speed = 5.0  # Base speed
            vx = speed * math.cos(direction_rad)
            vy = -speed * math.sin(direction_rad)  # Flip Y for screen coords

            # Random color
            colors = [BLUE, RED, GREEN, ORANGE, PURPLE, CYAN]
            color = random.choice(colors)

            # Create planet
            planet = Body(screen_x, screen_y, mass, vx, vy, 
                         max(8, int(mass/50)), color, f"Planet-{len(self.bodies)}")
            self.bodies.append(planet)

            # Reset input boxes
            for box in self.input_boxes:
                box.active = False

        except Exception as e:
            print(f"Error creating planet: {e}")

    def handle_events(self):
        """Handle all pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Handle planet creation
            if self.creating_planet:
                self.handle_planet_creation(event)
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:  # Right click
                    mouse_x, mouse_y = event.pos
                    clicked_body = get_body_at_position(mouse_x, mouse_y, self.bodies)

                    if clicked_body:
                        # Edit existing body
                        self.edit_mode = True
                        self.selected_body = clicked_body
                        clicked_body.selected = True
                    else:
                        # Start planet creation
                        self.creating_planet = True
                        self.creation_step = 1
                        self.input_boxes[0].active = True

                        # Pre-fill coordinates with click position
                        click_x = mouse_x - WIDTH // 2
                        click_y = HEIGHT // 2 - mouse_y
                        self.input_boxes[0].text = str(click_x)
                        self.input_boxes[1].text = str(click_y)
                        self.input_boxes[0].txt_surface = input_font.render(self.input_boxes[0].text, True, WHITE)
                        self.input_boxes[1].txt_surface = input_font.render(self.input_boxes[1].text, True, WHITE)

            elif event.type == pygame.KEYDOWN:
                if self.edit_mode and self.selected_body:
                    if event.key in [pygame.K_RETURN, pygame.K_ESCAPE]:
                        self.selected_body.selected = False
                        self.edit_mode = False
                        self.selected_body = None

                    elif event.key == pygame.K_UP:
                        self.selected_body.mass += 50
                    elif event.key == pygame.K_DOWN:
                        self.selected_body.mass = max(50, self.selected_body.mass - 50)

                    elif event.key == pygame.K_a:
                        self.selected_body.vx -= 0.5
                    elif event.key == pygame.K_d:
                        self.selected_body.vx += 0.5
                    elif event.key == pygame.K_w:
                        self.selected_body.vy -= 0.5
                    elif event.key == pygame.K_s:
                        self.selected_body.vy += 0.5

                elif event.key == pygame.K_c:
                    for body in self.bodies:
                        body.trail.clear()

                elif event.key == pygame.K_r:
                    self.bodies.clear()
                    self.create_sun()
                    self.edit_mode = False
                    self.selected_body = None

                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid

    def update_physics(self):
        """Update simulation physics"""
        if not self.creating_planet and not self.edit_mode:
            dt = 0.5
            apply_mutual_gravity(self.bodies, dt)

    def draw(self):
        """Draw everything"""
        self.screen.fill(BLACK)

        # Draw cartesian plane
        draw_cartesian_plane(self.screen, self.show_grid)

        # Draw all bodies
        for body in self.bodies:
            body.draw(self.screen)

        # Draw UI elements
        self.draw_instructions()
        self.draw_info()

        # Draw edit interface if in edit mode
        if self.edit_mode and self.selected_body:
            draw_edit_interface(self.screen, self.selected_body)

        # Draw planet creation dialog
        if self.creating_planet:
            draw_planet_creation_dialog(self.screen, self.input_boxes, self.creation_step)

        # Draw mouse hover effect
        if not self.creating_planet and not self.edit_mode:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            hover_body = get_body_at_position(mouse_x, mouse_y, self.bodies)
            if hover_body:
                pygame.draw.circle(self.screen, WHITE, 
                                 (int(hover_body.x), int(hover_body.y)), 
                                 hover_body.radius + 3, 2)

        pygame.display.flip()

    def draw_instructions(self):
        """Draw control instructions"""
        instructions = [
            "Right-click: Create planet with coordinates/direction",
            "Right-click body: Edit properties",
            "G: Toggle grid, C: Clear trails, R: Reset"
        ]

        y_offset = 10
        for instruction in instructions:
            text_surface = small_font.render(instruction, True, WHITE)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 20

    def draw_info(self):
        """Draw simulation information"""
        info_lines = [
            f"Bodies: {len(self.bodies)}",
            f"Grid: {'ON' if self.show_grid else 'OFF'}",
            f"Physics: N-body mutual gravity"
        ]

        y_offset = HEIGHT - 80
        for line in info_lines:
            text_surface = small_font.render(line, True, WHITE)
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
    print("Starting Cartesian Orbital Simulation...")
    print("Features:")
    print("- Cartesian coordinate grid background")
    print("- Interactive planet placement with coordinates")
    print("- Direction input in degrees for initial velocity")
    print("- Full mutual gravity physics")
    print()
    print("Controls:")
    print("- Right-click empty space: Create planet with coordinate/direction input")
    print("- Right-click body: Edit mass and velocity")
    print("- G: Toggle grid, C: Clear trails, R: Reset")
    print()

    simulation = OrbitSimulation()
    simulation.run()
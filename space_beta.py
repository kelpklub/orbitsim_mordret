"""
2D Orbital Mechanics Simulation with Mutual Gravity
==================================================

Features:
- Scaled down numbers (100-1000 range)
- No initial planets, just a sun
- Right-click empty space: Create planet
- Right-click planet: Edit mass and velocity
- Full N-body physics: Sun is affected by planets
- Interactive controls with keyboard editing

Controls:
- Right-click empty space: Create new planet
- Right-click existing body: Edit properties
- During editing:
  - Up/Down arrows: Change mass
  - A/D keys: Change X velocity
  - W/S keys: Change Y velocity
  - Enter/Esc: Finish editing
"""

import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Constants - All scaled down to 100-1000 range
WIDTH, HEIGHT = 1000, 700
G = 0.8  # Scaled gravitational constant
PLANET_RADIUS = 12
SUN_RADIUS = 20
MIN_DIST = 10  # Minimum distance to prevent singularities

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

# Fonts
font = pygame.font.Font(None, 24)
small_font = pygame.font.Font(None, 18)
large_font = pygame.font.Font(None, 32)

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
        self.fx = 0.0  # Force components
        self.fy = 0.0

    def calculate_force_from(self, other):
        """Calculate gravitational force from another body"""
        dx = other.x - self.x
        dy = other.y - self.y

        # Calculate distance with minimum threshold
        distance_squared = dx * dx + dy * dy
        distance = max(MIN_DIST, math.sqrt(distance_squared))

        # F = G * m1 * m2 / r^2
        force_magnitude = G * self.mass * other.mass / (distance * distance)

        # Calculate force components
        fx = force_magnitude * dx / distance
        fy = force_magnitude * dy / distance

        return fx, fy

    def apply_force(self, fx, fy, dt):
        """Apply force to update velocity and position"""
        if not self.selected:  # Don't update if being edited
            # a = F/m
            ax = fx / self.mass
            ay = fy / self.mass

            # Update velocity: v = v + a*dt
            self.vx += ax * dt
            self.vy += ay * dt

            # Update position: x = x + v*dt
            self.x += self.vx * dt
            self.y += self.vy * dt

            # Update trail
            self.update_trail()

    def update_trail(self):
        """Update orbit trail"""
        current_pos = (int(self.x), int(self.y))
        if not self.trail or self.trail[-1] != current_pos:
            self.trail.append(current_pos)

        # Limit trail length
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

        # Special effects for sun
        if self.is_sun:
            # Draw glow effect
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

        # Draw selection highlight
        if self.selected:
            pygame.draw.circle(screen, SELECT_COLOR, 
                             (int(self.x), int(self.y)), self.radius + 5, 3)

        # Draw name
        name_surface = small_font.render(self.name, True, WHITE)
        screen.blit(name_surface, (self.x + self.radius + 5, self.y - 10))

def apply_mutual_gravity(bodies, dt):
    """Apply mutual gravitational forces between all bodies"""
    # Reset forces
    for body in bodies:
        body.fx = 0.0
        body.fy = 0.0

    # Calculate forces between all pairs
    for i, body1 in enumerate(bodies):
        for j, body2 in enumerate(bodies):
            if i != j:  # Don't apply force to self
                fx, fy = body1.calculate_force_from(body2)
                body1.fx += fx
                body1.fy += fy

    # Apply forces to update positions
    for body in bodies:
        body.apply_force(body.fx, body.fy, dt)

def get_body_at_position(x, y, bodies):
    """Find body at given position"""
    for body in bodies:
        distance = math.sqrt((body.x - x)**2 + (body.y - y)**2)
        if distance <= body.radius:
            return body
    return None

def create_random_planet(x, y, bodies):
    """Create a planet with random properties at given position"""
    # Random mass between 200-800
    mass = random.randint(200, 800)

    # Random velocity components
    vx = random.uniform(-3, 3)
    vy = random.uniform(-3, 3)

    # Random color
    colors = [BLUE, RED, GREEN, ORANGE, PURPLE, CYAN]
    color = random.choice(colors)

    # Random radius based on mass
    radius = max(8, int(mass / 100) + 5)

    planet = Body(x, y, mass, vx, vy, radius, color, f"Planet-{len(bodies)}")
    return planet

def draw_edit_interface(screen, body):
    """Draw the editing interface for selected body"""
    # Background box
    box_width, box_height = 300, 200
    box_x = WIDTH // 2 - box_width // 2
    box_y = HEIGHT // 2 - box_height // 2

    box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
    pygame.draw.rect(screen, DARK_GRAY, box_rect)
    pygame.draw.rect(screen, WHITE, box_rect, 2)

    # Title
    title = "SUN" if body.is_sun else "PLANET"
    title_surface = large_font.render(f"Editing {title}", True, WHITE)
    screen.blit(title_surface, (box_x + 10, box_y + 10))

    # Properties
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

def draw_instructions(screen):
    """Draw control instructions"""
    instructions = [
        "Right-click empty space: Create planet",
        "Right-click body: Edit properties",
        "During editing: â†‘/â†“ mass, WASD velocity",
        "Enter/Esc: Finish editing"
    ]
    

    y_offset = 10
    for instruction in instructions:
        text_surface = small_font.render(instruction, True, WHITE)
        screen.blit(text_surface, (10, y_offset))
        y_offset += 20

def draw_info(screen, bodies):
    """Draw simulation information"""
    info_lines = [
        f"Bodies: {len(bodies)}",
        f"G constant: {G}",
        f"Physics: Full N-body (mutual gravity)"
    ]
    

    y_offset = HEIGHT - 80
    for line in info_lines:
        text_surface = small_font.render(line, True, WHITE)
        screen.blit(text_surface, (WIDTH - 250, y_offset))
        y_offset += 20

class OrbitSimulation:
    """Main simulation class"""
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Interactive N-Body Gravity Simulation")
        self.clock = pygame.time.Clock()
        self.paused =False

        self.running = True
        self.edit_mode = False
        self.selected_body = None

        # Initialize with just the sun
        self.bodies = []
        self.create_sun()

    def create_sun(self):
        """Create the central sun"""
        sun = Body(WIDTH // 2, HEIGHT // 2, 6000, 0, 0, SUN_RADIUS, YELLOW, "Sun")
        sun.is_sun = True
        self.bodies.append(sun)

    def handle_events(self):
        """Handle all pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:  # Right click
                    mouse_x, mouse_y = event.pos
                    clicked_body = get_body_at_position(mouse_x, mouse_y, self.bodies)

                    if clicked_body:
                        # Edit existing body
                        self.edit_mode = True
                        self.selected_body = clicked_body
                        clicked_body.selected = True
                    else:
                        # Create new planet
                        new_planet = create_random_planet(mouse_x, mouse_y, self.bodies)
                        self.bodies.append(new_planet)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                if self.edit_mode and self.selected_body:
                    if event.key in [pygame.K_RETURN, pygame.K_ESCAPE]:
                        # Finish editing
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
                    # Clear all trails
                    for body in self.bodies:
                        body.trail.clear()

                elif event.key == pygame.K_r:
                    # Reset simulation
                    self.bodies.clear()
                    self.create_sun()
                    self.edit_mode = False
                    self.selected_body = None

    def update_physics(self):
        """Update simulation physics"""
        dt = 0.5  # Time step for stability
        apply_mutual_gravity(self.bodies, dt)

    def draw(self):
        """Draw everything"""
        self.screen.fill(BLACK)

        # Draw all bodies
        for body in self.bodies:
            body.draw(self.screen)

        # Draw UI elements
        draw_instructions(self.screen)
        draw_info(self.screen, self.bodies)

        # Draw edit interface if in edit mode
        if self.edit_mode and self.selected_body:
            draw_edit_interface(self.screen, self.selected_body)

        # Draw mouse hover effect
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hover_body = get_body_at_position(mouse_x, mouse_y, self.bodies)
        if hover_body and not self.edit_mode:
            pygame.draw.circle(self.screen, WHITE, 
                             (int(hover_body.x), int(hover_body.y)), 
                             hover_body.radius + 3, 2)

        pygame.display.flip()

    def run(self):
        """Main simulation loop"""
        while self.running:
            self.handle_events()
            self.update_physics()
            self.draw()
            self.clock.tick(60)  # 60 FPS

        pygame.quit()

# Run the simulation
if __name__ == "__main__":
    print("Starting Interactive N-Body Gravity Simulation...")
    print("Features:")
    print("- Scaled physics (masses 200-800, velocities 1-10)")
    print("- Full mutual gravity (sun moves too!)")
    print("- Right-click to create/edit planets")
    print("- Real-time parameter adjustment")
    print()

    simulation = OrbitSimulation()
    simulation.run()
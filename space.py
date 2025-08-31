import pygame
import math
import sys

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1200, 800
G = 6.67428e-11  # Gravitational constant (scaled for simulation)
SCALE = 1e-10    # Scale factor for display
TIMESTEP = 86400  # 1 day in seconds (can be adjusted)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 100, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
ORANGE = (255, 165, 0)

class Slider:
    """A simple slider UI component for adjusting parameters"""
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.dragging = False
        self.button_rect = pygame.Rect(x + int((initial_val - min_val) / (max_val - min_val) * w) - 5, y - 5, 10, h + 10)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                rel_x = event.pos[0] - self.rect.x
                rel_x = max(0, min(rel_x, self.rect.width))
                self.val = self.min_val + (rel_x / self.rect.width) * (self.max_val - self.min_val)
                self.button_rect.centerx = self.rect.x + rel_x

    def draw(self, screen, font):
        # Draw slider track
        pygame.draw.rect(screen, GRAY, self.rect)
        # Draw slider button
        pygame.draw.rect(screen, WHITE, self.button_rect)
        # Draw label and value
        text = font.render(f"{self.label}: {self.val:.2e}", True, WHITE)
        screen.blit(text, (self.rect.x, self.rect.y - 25))

class Body:
    """Class representing a celestial body with mass, position, velocity"""
    def __init__(self, x, y, radius, color, mass, name="Body"):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.mass = mass
        self.name = name

        self.orbit_trail = []
        self.is_sun = False

        self.vx = 0  # velocity in x direction
        self.vy = 0  # velocity in y direction

    def draw(self, screen, font):
        # Convert real coordinates to screen coordinates
        screen_x = int(self.x * SCALE + WIDTH // 2)
        screen_y = int(self.y * SCALE + HEIGHT // 2)

        # Draw orbit trail
        if len(self.orbit_trail) > 2:
            trail_points = []
            for point in self.orbit_trail[-500:]:  # Limit trail length
                trail_x = int(point[0] * SCALE + WIDTH // 2)
                trail_y = int(point[1] * SCALE + HEIGHT // 2)
                if 0 <= trail_x < WIDTH and 0 <= trail_y < HEIGHT:
                    trail_points.append((trail_x, trail_y))
            if len(trail_points) > 1:
                pygame.draw.lines(screen, self.color, False, trail_points, 2)

        # Draw the body
        if 0 <= screen_x < WIDTH and 0 <= screen_y < HEIGHT:
            pygame.draw.circle(screen, self.color, (screen_x, screen_y), max(self.radius, 3))

            # Draw name label
            text = font.render(self.name, True, WHITE)
            screen.blit(text, (screen_x + 15, screen_y - 10))

    def gravitational_force(self, other):
        """Calculate gravitational force between this body and another"""
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance == 0:
            return 0, 0

        # F = G * m1 * m2 / r^2
        force_magnitude = G * self.mass * other.mass / distance**2

        # Calculate force components
        fx = force_magnitude * dx / distance
        fy = force_magnitude * dy / distance

        return fx, fy

    def update_position(self, bodies, timestep):
        """Update position using Verlet integration"""
        if self.is_sun:
            return

        total_fx = 0
        total_fy = 0

        # Calculate net force from all other bodies
        for body in bodies:
            if body != self:
                fx, fy = self.gravitational_force(body)
                total_fx += fx
                total_fy += fy

        # Calculate acceleration: a = F/m
        ax = total_fx / self.mass
        ay = total_fy / self.mass

        # Update velocity: v = v + a*t
        self.vx += ax * timestep
        self.vy += ay * timestep

        # Update position: x = x + v*t
        self.x += self.vx * timestep
        self.y += self.vy * timestep

        # Add to orbit trail
        self.orbit_trail.append((self.x, self.y))

class OrbitSimulation:
    """Main simulation class"""
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("2D Orbital Mechanics Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        self.running = True
        self.paused = False

        # Create bodies
        self.bodies = []
        self.setup_solar_system()

        # Create UI sliders
        self.sliders = [
            Slider(10, 50, 200, 20, 1e4, 1e6, TIMESTEP, "Timestep (s)"),
            Slider(10, 100, 200, 20, 1e28, 1e32, 2e30, "Sun Mass (kg)"),
            Slider(10, 150, 200, 20, 1e-12, 1e-8, SCALE, "Scale Factor"),
            Slider(10, 200, 200, 20, 10000, 50000, 30000, "Planet Velocity (m/s)")
        ]

        self.selected_body = None

    def setup_solar_system(self):
        """Create initial solar system setup"""
        # Sun
        sun = Body(0, 0, 30, YELLOW, 1.989e30, "Sun")
        sun.is_sun = True
        sun.vy = 2000
        self.bodies.append(sun)

        # Earth
        earth = Body(-1.496e11, 0, 8, BLUE, 5.972e24, "Earth")
        earth.vy = 29780  # orbital velocity
        self.bodies.append(earth)

        # Mars
        mars = Body(-2.279e11, 0, 6, RED, 6.39e23, "Mars")
        mars.vy = 24070
        self.bodies.append(mars)

        # Venus
        venus = Body(-1.082e11, 0, 7, ORANGE, 4.867e24, "Venus")
        venus.vy = 35020
        self.bodies.append(venus)

    def handle_events(self):
        """Handle user input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset_simulation()
                elif event.key == pygame.K_c:
                    self.clear_trails()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_mouse_click(event.pos)

            # Handle slider events
            for slider in self.sliders:
                slider.handle_event(event)

    def handle_mouse_click(self, pos):
        """Handle mouse clicks on bodies"""
        for body in self.bodies:
            screen_x = int(body.x * SCALE + WIDTH // 2)
            screen_y = int(body.y * SCALE + HEIGHT // 2)

            distance = math.sqrt((pos[0] - screen_x)**2 + (pos[1] - screen_y)**2)
            if distance <= max(body.radius, 10):
                self.selected_body = body
                break
        else:
            self.selected_body = None

    def update_simulation(self):
        """Update the physics simulation"""
        if self.paused:
            return

        # Update parameters from sliders
        global TIMESTEP, SCALE
        TIMESTEP = self.sliders[0].val
        sun_mass = self.sliders[1].val
        SCALE = self.sliders[2].val
        planet_velocity = self.sliders[3].val

        # Update sun mass
        for body in self.bodies:
            if body.is_sun:
                body.mass = sun_mass
                break

        # Update body positions
        for body in self.bodies:
            body.update_position(self.bodies, TIMESTEP)

    def draw(self):
        """Draw everything on screen"""
        self.screen.fill(BLACK)

        # Draw bodies
        for body in self.bodies:
            body.draw(self.screen, self.small_font)

        # Highlight selected body
        if self.selected_body:
            screen_x = int(self.selected_body.x * SCALE + WIDTH // 2)
            screen_y = int(self.selected_body.y * SCALE + HEIGHT // 2)
            pygame.draw.circle(self.screen, WHITE, (screen_x, screen_y), 
                             max(self.selected_body.radius, 10) + 5, 2)

        # Draw UI
        self.draw_ui()

        pygame.display.flip()

    def draw_ui(self):
        """Draw user interface elements"""
        # Draw sliders
        for slider in self.sliders:
            slider.draw(self.screen, self.small_font)

        # Draw instructions
        instructions = [
            "SPACE: Pause/Resume",
            "R: Reset Simulation", 
            "C: Clear Trails",
            "Click: Select Body",
            "Drag Sliders: Adjust Parameters"
        ]

        y_offset = HEIGHT - 120
        for instruction in instructions:
            text = self.small_font.render(instruction, True, WHITE)
            self.screen.blit(text, (WIDTH - 250, y_offset))
            y_offset += 20

        # Draw status
        status = "PAUSED" if self.paused else "RUNNING"
        status_text = self.font.render(f"Status: {status}", True, GREEN if not self.paused else RED)
        self.screen.blit(status_text, (10, 10))

        # Draw selected body info
        if self.selected_body:
            info = [
                f"Selected: {self.selected_body.name}",
                f"Mass: {self.selected_body.mass:.2e} kg",
                f"Velocity: {math.sqrt(self.selected_body.vx**2 + self.selected_body.vy**2):.0f} m/s",
                f"Position: ({self.selected_body.x:.2e}, {self.selected_body.y:.2e}) m"
            ]

            y_offset = 250
            for info_line in info:
                text = self.small_font.render(info_line, True, WHITE)
                self.screen.blit(text, (10, y_offset))
                y_offset += 20

    def reset_simulation(self):
        """Reset simulation to initial state"""
        self.bodies.clear()
        self.setup_solar_system()
        self.selected_body = None

    def clear_trails(self):
        """Clear orbit trails"""
        for body in self.bodies:
            body.orbit_trail.clear()

    def run(self):
        """Main simulation loop"""
        while self.running:
            self.handle_events()
            self.update_simulation()
            self.draw()
            self.clock.tick(60)  # 60 FPS

        pygame.quit()
        sys.exit()

# Run the simulation
if __name__ == "__main__":
    sim = OrbitSimulation()
    sim.run()
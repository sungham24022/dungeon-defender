from dataclasses import dataclass, field
from typing import Optional
import math
import random


@dataclass
class Vector2D:
    x: float
    y: float


@dataclass
class Player:
    x: float
    y: float
    sx: int = 35
    sy: int = 60
    speed: float = 7.0
    hp: int = 3
    max_hp: int = 3

    # state flags
    moving_left: bool = False
    moving_right: bool = False
    moving_up: bool = False
    moving_down: bool = False
    shooting: bool = False

    # power-up
    rapid_fire: bool = False
    rapid_fire_timer: int = 0
    shield_active: bool = False
    shield_timer: int = 0

    # ultimate
    ultimate_charge: int = 0
    ultimate_max: int = 100
    ultimate_active: bool = False
    ultimate_duration: int = 0


@dataclass
class Bullet:
    x: float
    y: float
    sx: int = 5
    sy: int = 15
    speed: float = 15.0
    color: tuple = (255, 255, 100)
    owner: str = "player"  # "player" | "enemy" | "boss"
    angle: Optional[float] = None  # for angled bullets

    def update(self):
        if self.owner == "player":
            self.y -= self.speed
        elif self.owner == "enemy":
            self.y += self.speed
        elif self.owner == "boss" and self.angle is not None:
            rad = math.radians(self.angle)
            self.x += self.speed * math.sin(rad)
            self.y += self.speed * math.cos(rad)
        else:
            self.y += self.speed

    def is_off_screen(self, width: int, height: int) -> bool:
        return self.y < -self.sy or self.y > height or self.x < -self.sx or self.x > width


@dataclass
class Wave:
    x: float
    y: float
    radius: float = 5.0
    max_radius: float = 200.0
    thickness: int = 3
    expansion_speed: float = 4.0
    color: tuple = (100, 0, 100)

    def update(self):
        self.radius += self.expansion_speed

    def is_alive(self) -> bool:
        return self.radius < self.max_radius


@dataclass
class Enemy:
    enemy_type: str
    x: float
    y: float
    sx: int = 40
    sy: int = 40
    hp: int = 1
    max_hp: int = 1
    move_speed: float = 2.5
    move_pattern: str = "straight"
    frame: int = 0
    shoot_timer: int = 0
    # zigzag
    amplitude: float = 3.0
    frequency: float = 0.1
    # circle
    center_x: float = 0.0
    radius: float = 50.0

    @staticmethod
    def create(enemy_type: str, x: float, y: float) -> "Enemy":
        defaults = {
            "goblin":     dict(move_speed=2.5, hp=1, max_hp=1, move_pattern="straight", sx=40, sy=40),
            "bat":        dict(move_speed=2.0, hp=1, max_hp=1, move_pattern="zigzag",   sx=40, sy=40),
            "ghost":      dict(move_speed=1.5, hp=2, max_hp=2, move_pattern="circle",   sx=40, sy=40),
            "orc_archer": dict(move_speed=1.2, hp=2, max_hp=2, move_pattern="straight", sx=40, sy=40),
            "skeleton":   dict(move_speed=0.8, hp=4, max_hp=4, move_pattern="straight", sx=50, sy=50),
        }
        d = defaults.get(enemy_type, {})
        e = Enemy(enemy_type=enemy_type, x=x, y=y, **d)
        e.center_x = x
        return e

    def update(self, canvas_width: int):
        self.frame += 1
        if self.move_pattern == "straight":
            self.y += self.move_speed
        elif self.move_pattern == "zigzag":
            self.y += self.move_speed
            self.x += math.sin(self.frame * self.frequency) * self.amplitude
        elif self.move_pattern == "circle":
            self.y += self.move_speed
            self.x = self.center_x + math.cos(self.frame * 0.05) * self.radius

        # boundary clamp
        self.x = max(0, min(canvas_width - self.sx, self.x))


@dataclass
class Boss:
    x: float = 115.0
    y: float = 50.0
    sx: int = 120
    sy: int = 120
    hp: int = 200
    max_hp: int = 200
    move_speed: float = 3.0
    direction: int = 1
    shoot_timer: int = 0
    pattern: int = 0
    pattern_timer: int = 0
    vertical_move: float = 0.0
    phase: int = 1
    sword_angle: float = 0.0
    dark_aura: float = 0.0

    def update(self, canvas_width: int):
        self.x += self.move_speed * self.direction
        if self.x <= 0 or self.x >= canvas_width - self.sx:
            self.direction *= -1

        self.vertical_move += 0.05
        self.y = 50 + math.sin(self.vertical_move) * 30

        if self.hp < self.max_hp * 0.5 and self.phase == 1:
            self.phase = 2
            self.move_speed = 4.0

        self.shoot_timer += 1
        self.pattern_timer += 1

        if self.pattern_timer > 150:
            self.pattern = (self.pattern + 1) % 4
            self.pattern_timer = 0

        self.sword_angle += 0.15
        self.dark_aura += 0.08

        bullets = []
        fire_rate = 20 if self.phase == 2 else 25
        if self.shoot_timer > fire_rate:
            if self.pattern == 0:
                bullets = self._shoot_dark_wave()
            elif self.pattern == 1:
                bullets = self._shoot_dark_spread()
            elif self.pattern == 2:
                bullets = self._shoot_curse()
            else:
                bullets = self._shoot_inferno()
            self.shoot_timer = 0

        return bullets

    def _shoot_dark_wave(self):
        return [Wave(x=self.x + self.sx // 2, y=self.y + self.sy // 2, color=(100, 0, 100))]

    def _shoot_dark_spread(self):
        bullets = []
        for angle in [-50, -30, -10, 10, 30, 50]:
            b = Bullet(x=self.x + self.sx // 2, y=self.y + self.sy,
                       sx=10, sy=10, speed=4.0, color=(150, 0, 150),
                       owner="boss", angle=angle)
            bullets.append(b)
        return bullets

    def _shoot_curse(self):
        bullets = []
        num = 16 if self.phase == 2 else 12
        for i in range(num):
            angle = (360 / num) * i
            b = Bullet(x=self.x + self.sx // 2, y=self.y + self.sy // 2,
                       sx=10, sy=10, speed=3.5, color=(200, 0, 200),
                       owner="boss", angle=angle)
            bullets.append(b)
        return bullets

    def _shoot_inferno(self):
        bullets = []
        for i in range(4):
            angle = (self.shoot_timer * 12 + i * 90) % 360
            b = Bullet(x=self.x + self.sx // 2, y=self.y + self.sy // 2,
                       sx=12, sy=12, speed=3.0, color=(255, 100, 0),
                       owner="boss", angle=angle)
            bullets.append(b)
        return bullets


@dataclass
class Particle:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    color: tuple = (255, 200, 100)
    lifetime: int = 30
    size: float = 3.0

    @staticmethod
    def burst(x: float, y: float, color: tuple, count: int = 20) -> list:
        return [
            Particle(
                x=x, y=y,
                vx=random.uniform(-3, 3),
                vy=random.uniform(-3, 3),
                color=color,
                lifetime=30,
                size=random.uniform(2, 5),
            )
            for _ in range(count)
        ]

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.size = max(1.0, self.size - 0.1)


@dataclass
class PowerUp:
    x: float
    y: float
    sx: int = 20
    sy: int = 20
    speed: float = 2.0
    power_type: str = "rapid"  # "rapid" | "shield"

    def update(self):
        self.y += self.speed


@dataclass
class BackgroundParticle:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.3
    lifetime: int = 200
    max_lifetime: int = 200
    size: int = 2

    @staticmethod
    def random(canvas_width: int, canvas_height: int) -> "BackgroundParticle":
        return BackgroundParticle(
            x=random.uniform(0, canvas_width),
            y=random.uniform(0, canvas_height),
            vx=random.uniform(-0.5, 0.5),
            vy=random.uniform(0.2, 0.5),
            lifetime=random.randint(100, 300),
            max_lifetime=random.randint(100, 300),
            size=random.randint(1, 3),
        )

    def update(self, canvas_width: int, canvas_height: int):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        if self.y > canvas_height:
            self.y = -10
            self.x = random.uniform(0, canvas_width)

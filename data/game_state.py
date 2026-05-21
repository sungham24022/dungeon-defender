from dataclasses import dataclass, field
from typing import List, Optional, Union
from domain.entities import (
    Player, Bullet, Wave, Enemy, Boss,
    Particle, PowerUp, BackgroundParticle,
)
import config


@dataclass
class GameState:
    # phase: "title" | "playing" | "gameover"
    phase: str = "title"

    player: Player = field(default_factory=lambda: Player(
        x=config.CANVAS_WIDTH / 2 - 17,
        y=config.CANVAS_HEIGHT - 75,
    ))

    bullets: List[Bullet] = field(default_factory=list)
    enemy_list: List[Enemy] = field(default_factory=list)
    enemy_bullets: List[Bullet] = field(default_factory=list)
    boss_bullets: List[Union[Bullet, Wave]] = field(default_factory=list)
    particles: List[Particle] = field(default_factory=list)
    bg_particles: List[BackgroundParticle] = field(default_factory=list)
    powerups: List[PowerUp] = field(default_factory=list)

    boss: Optional[Boss] = None
    boss_mode: bool = False
    boss_spawned: bool = False

    score: int = 0
    kill: int = 0
    elapsed_seconds: int = 0
    frame: int = 0
    fire_frame: int = 0

    victory: bool = False

    def reset(self):
        self.__init__()

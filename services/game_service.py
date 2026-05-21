import random
import math
from typing import List

from data.game_state import GameState
from domain.entities import (
    Enemy, Bullet, Boss, Particle, PowerUp, BackgroundParticle, Wave,
)
import config

SCORE_VALUES = {
    "goblin": 10,
    "bat": 15,
    "ghost": 25,
    "orc_archer": 30,
    "skeleton": 50,
}


def _rect_collide(ax, ay, asx, asy, bx, by, bsx, bsy) -> bool:
    return ax < bx + bsx and ax + asx > bx and ay < by + bsy and ay + asy > by


def init_bg_particles(state: GameState):
    state.bg_particles = [
        BackgroundParticle.random(config.CANVAS_WIDTH, config.CANVAS_HEIGHT)
        for _ in range(20)
    ]


def tick(state: GameState, dt_seconds: int):
    """Main game tick. Called once per frame."""
    if state.phase != "playing":
        _update_bg_particles(state)
        return

    state.frame += 1
    state.elapsed_seconds = dt_seconds

    _update_timers(state)
    _update_bg_particles(state)
    _move_player(state)
    _fire_bullet(state)
    _move_player_bullets(state)
    _spawn_enemies(state)
    _update_enemies(state)
    _update_enemy_bullets(state)
    _check_enemy_bullet_player_collision(state)
    _update_boss(state)
    _check_bullet_enemy_collision(state)
    _check_boss_bullet_player_collision(state)
    _update_powerups(state)
    _update_particles(state)


# ── internal helpers ────────────────────────────────────────────────────────

def _update_timers(state: GameState):
    p = state.player

    if p.ultimate_active:
        p.ultimate_duration -= 1
        if p.ultimate_duration <= 0:
            p.ultimate_active = False
        if p.ultimate_duration == p.ultimate_max - 1:
            # clear all enemies
            for enemy in state.enemy_list:
                state.score += 5
                state.kill += 1
                state.particles += Particle.burst(
                    enemy.x + enemy.sx // 2, enemy.y + enemy.sy // 2,
                    (200, 255, 150), 20,
                )
            state.enemy_list.clear()
            state.enemy_bullets.clear()
            if state.boss_mode:
                state.boss_bullets.clear()

    if p.rapid_fire:
        p.rapid_fire_timer -= 1
        if p.rapid_fire_timer <= 0:
            p.rapid_fire = False

    if p.shield_active:
        p.shield_timer -= 1
        if p.shield_timer <= 0:
            p.shield_active = False


def _update_bg_particles(state: GameState):
    for bp in state.bg_particles:
        bp.update(config.CANVAS_WIDTH, config.CANVAS_HEIGHT)
        if bp.lifetime <= 0:
            state.bg_particles.remove(bp)
            state.bg_particles.append(
                BackgroundParticle.random(config.CANVAS_WIDTH, config.CANVAS_HEIGHT)
            )


def _move_player(state: GameState):
    p = state.player
    if p.moving_left:
        p.x = max(0, p.x - p.speed)
    if p.moving_right:
        p.x = min(config.CANVAS_WIDTH - p.sx, p.x + p.speed)
    if p.moving_up:
        p.y = max(100, p.y - p.speed)
    if p.moving_down:
        p.y = min(config.CANVAS_HEIGHT - p.sy - 15, p.y + p.speed)


def _fire_bullet(state: GameState):
    p = state.player
    if not p.shooting:
        return
    fire_rate = 3 if p.rapid_fire else config.FIRE_RATE
    state.fire_frame += 1
    if state.fire_frame % fire_rate != 0:
        return

    b = Bullet(
        x=p.x + p.sx / 2 - 2.5,
        y=p.y - 25,
        sx=5, sy=15,
        speed=config.BULLET_SPEED,
        color=(255, 255, 100),
        owner="player",
    )
    state.bullets.append(b)

    if p.ultimate_active:
        for offset in [-20, 20]:
            b2 = Bullet(
                x=p.x + p.sx / 2 - 4 + offset,
                y=p.y - 30,
                sx=8, sy=20,
                speed=20.0,
                color=(100, 255, 255),
                owner="player",
            )
            state.bullets.append(b2)


def _move_player_bullets(state: GameState):
    for b in state.bullets:
        b.update()
    state.bullets = [b for b in state.bullets
                     if not b.is_off_screen(config.CANVAS_WIDTH, config.CANVAS_HEIGHT)]


def _spawn_enemies(state: GameState):
    if state.boss_mode:
        return
    t = state.elapsed_seconds
    spawn_rate = max(0.93, 0.98 - t * 0.001)
    if random.random() > spawn_rate:
        if t < 20:
            enemy_type = random.choice(["goblin", "goblin", "bat"])
        elif t < 40:
            enemy_type = random.choice(["goblin", "bat", "ghost", "orc_archer"])
        else:
            enemy_type = random.choice(["bat", "ghost", "orc_archer", "skeleton"])
        e = Enemy.create(enemy_type, random.randrange(50, config.CANVAS_WIDTH - 90), -50)
        state.enemy_list.append(e)


def _update_enemies(state: GameState):
    to_remove = []
    for i, enemy in enumerate(state.enemy_list):
        enemy.update(config.CANVAS_WIDTH)

        if enemy.enemy_type == "orc_archer":
            enemy.shoot_timer += 1
            if enemy.shoot_timer > 90 and 0 < enemy.y < config.CANVAS_HEIGHT - 200:
                eb = Bullet(
                    x=enemy.x + enemy.sx // 2,
                    y=enemy.y + enemy.sy,
                    sx=6, sy=12,
                    speed=4.0,
                    color=(200, 150, 50),
                    owner="enemy",
                )
                state.enemy_bullets.append(eb)
                enemy.shoot_timer = 0

        if enemy.y >= config.CANVAS_HEIGHT:
            to_remove.append(i)

    for i in reversed(to_remove):
        del state.enemy_list[i]

    # check boss spawn
    if state.kill >= config.BOSS_KILL_THRESHOLD and not state.boss_spawned:
        state.boss_mode = True
        state.boss = Boss()
        state.boss_spawned = True
        state.enemy_list.clear()
        state.enemy_bullets.clear()


def _update_enemy_bullets(state: GameState):
    for b in state.enemy_bullets:
        b.update()
    state.enemy_bullets = [
        b for b in state.enemy_bullets
        if not b.is_off_screen(config.CANVAS_WIDTH, config.CANVAS_HEIGHT)
    ]


def _check_enemy_bullet_player_collision(state: GameState):
    p = state.player
    if p.shield_active:
        return
    for bullet in state.enemy_bullets[:]:
        if _rect_collide(bullet.x, bullet.y, bullet.sx, bullet.sy,
                         p.x, p.y, p.sx, p.sy):
            state.enemy_bullets.remove(bullet)
            p.hp -= 1
            state.particles += Particle.burst(
                p.x + p.sx // 2, p.y + p.sy // 2, (255, 100, 50), 15,
            )
            if p.hp <= 0:
                _end_game(state, victory=False)
            return


def _update_boss(state: GameState):
    if not (state.boss_mode and state.boss):
        return
    boss = state.boss
    new_bullets = boss.update(config.CANVAS_WIDTH)
    state.boss_bullets += new_bullets

    # update boss bullets
    dead = []
    for i, b in enumerate(state.boss_bullets):
        if isinstance(b, Wave):
            b.update()
            if not b.is_alive():
                dead.append(i)
        else:
            b.update()
            if b.is_off_screen(config.CANVAS_WIDTH, config.CANVAS_HEIGHT):
                dead.append(i)
    for i in reversed(dead):
        del state.boss_bullets[i]


def _check_boss_bullet_player_collision(state: GameState):
    if not state.boss_mode:
        return
    p = state.player
    if p.shield_active:
        return

    for b in state.boss_bullets[:]:
        if isinstance(b, Wave):
            dx = b.x - (p.x + p.sx / 2)
            dy = b.y - (p.y + p.sy / 2)
            dist = math.sqrt(dx * dx + dy * dy)
            if abs(dist - b.radius) < 15:
                state.boss_bullets.remove(b)
                p.hp -= 1
                state.particles += Particle.burst(
                    p.x + p.sx // 2, p.y + p.sy // 2, (255, 100, 100), 20,
                )
                if p.hp <= 0:
                    _end_game(state, victory=False)
                return
        else:
            if _rect_collide(b.x, b.y, b.sx, b.sy, p.x, p.y, p.sx, p.sy):
                state.boss_bullets.remove(b)
                p.hp -= 1
                state.particles += Particle.burst(
                    p.x + p.sx // 2, p.y + p.sy // 2, (255, 100, 100), 20,
                )
                if p.hp <= 0:
                    _end_game(state, victory=False)
                return


def _check_bullet_enemy_collision(state: GameState):
    bullets_to_remove = set()
    enemies_to_remove = set()

    for i, bullet in enumerate(state.bullets):
        for j, enemy in enumerate(state.enemy_list):
            if _rect_collide(bullet.x, bullet.y, bullet.sx, bullet.sy,
                              enemy.x, enemy.y, enemy.sx, enemy.sy):
                bullets_to_remove.add(i)
                enemy.hp -= 1
                if enemy.hp <= 0:
                    enemies_to_remove.add(j)

    # bullet vs boss
    if state.boss_mode and state.boss:
        boss = state.boss
        for i, bullet in enumerate(state.bullets):
            if _rect_collide(bullet.x, bullet.y, bullet.sx, bullet.sy,
                              boss.x, boss.y, boss.sx, boss.sy):
                bullets_to_remove.add(i)
                boss.hp -= 1
                state.score += 5
                state.particles += Particle.burst(
                    bullet.x, bullet.y, (200, 150, 255), 10,
                )
                if boss.hp <= 0:
                    state.particles += Particle.burst(
                        boss.x + boss.sx // 2, boss.y + boss.sy // 2,
                        (200, 100, 255), 100,
                    )
                    state.score += 500
                    state.boss_mode = False
                    state.boss = None
                    _end_game(state, victory=True)

    # process removals
    for j in sorted(enemies_to_remove, reverse=True):
        enemy = state.enemy_list[j]
        state.particles += Particle.burst(
            enemy.x + enemy.sx // 2, enemy.y + enemy.sy // 2, (200, 150, 0), 20,
        )
        state.score += SCORE_VALUES.get(enemy.enemy_type, 10)
        state.kill += 1
        p = state.player
        p.ultimate_charge = min(p.ultimate_max, p.ultimate_charge + 5)

        if random.random() < 0.30:
            pu = PowerUp(
                x=enemy.x, y=enemy.y,
                power_type=random.choice(["rapid", "shield"]),
            )
            state.powerups.append(pu)
        del state.enemy_list[j]

    for i in sorted(bullets_to_remove, reverse=True):
        if i < len(state.bullets):
            del state.bullets[i]


def _update_powerups(state: GameState):
    p = state.player
    to_remove = []
    for i, pu in enumerate(state.powerups):
        pu.update()
        if pu.y >= config.CANVAS_HEIGHT:
            to_remove.append(i)
        elif _rect_collide(pu.x, pu.y, pu.sx, pu.sy, p.x, p.y, p.sx, p.sy):
            to_remove.append(i)
            if pu.power_type == "rapid":
                p.rapid_fire = True
                p.rapid_fire_timer = 300
            elif pu.power_type == "shield":
                p.shield_active = True
                p.shield_timer = 300
            state.particles += Particle.burst(pu.x, pu.y, (100, 200, 255), 20)
    for i in reversed(to_remove):
        del state.powerups[i]


def _update_particles(state: GameState):
    for part in state.particles:
        part.update()
    state.particles = [part for part in state.particles if part.lifetime > 0]


def _end_game(state: GameState, victory: bool):
    state.phase = "gameover"
    state.victory = victory


def activate_ultimate(state: GameState):
    p = state.player
    if p.ultimate_charge >= p.ultimate_max and not p.ultimate_active:
        p.ultimate_active = True
        p.ultimate_duration = config.ULTIMATE_DURATION
        p.ultimate_charge = 0


def set_key(state: GameState, key: str, pressed: bool):
    p = state.player
    mapping = {
        "left": "moving_left",
        "right": "moving_right",
        "up": "moving_up",
        "down": "moving_down",
        "space": "shooting",
    }
    attr = mapping.get(key)
    if attr:
        setattr(p, attr, pressed)

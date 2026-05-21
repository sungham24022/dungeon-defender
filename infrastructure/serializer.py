"""
Converts GameState → plain dict so it can be sent as JSON to the browser.
The browser renderer reads this dict and draws everything on <canvas>.
"""
import math
from data.game_state import GameState
from domain.entities import Wave


def serialize(state: GameState) -> dict:
    p = state.player

    return {
        "phase": state.phase,
        "score": state.score,
        "kill": state.kill,
        "elapsed": state.elapsed_seconds,
        "victory": state.victory,

        "player": {
            "x": p.x, "y": p.y, "sx": p.sx, "sy": p.sy,
            "hp": p.hp, "max_hp": p.max_hp,
            "shield": p.shield_active,
            "shield_timer": p.shield_timer,
            "ultimate_active": p.ultimate_active,
            "ultimate_charge": p.ultimate_charge,
            "ultimate_max": p.ultimate_max,
            "rapid_fire": p.rapid_fire,
            "rapid_fire_timer": p.rapid_fire_timer,
        },

        "bullets": [
            {"x": b.x, "y": b.y, "sx": b.sx, "sy": b.sy,
             "color": b.color, "owner": b.owner}
            for b in state.bullets
        ],

        "enemies": [
            {"type": e.enemy_type, "x": e.x, "y": e.y,
             "sx": e.sx, "sy": e.sy, "hp": e.hp, "max_hp": e.max_hp}
            for e in state.enemy_list
        ],

        "enemy_bullets": [
            {"x": b.x, "y": b.y, "sx": b.sx, "sy": b.sy, "color": b.color}
            for b in state.enemy_bullets
        ],

        "boss_bullets": [
            ({"type": "wave",
              "x": b.x, "y": b.y,
              "radius": b.radius, "color": b.color}
             if isinstance(b, Wave) else
             {"type": "bullet",
              "x": b.x, "y": b.y, "sx": b.sx, "sy": b.sy, "color": b.color})
            for b in state.boss_bullets
        ],

        "particles": [
            {"x": pt.x, "y": pt.y, "color": pt.color,
             "size": pt.size, "lifetime": pt.lifetime}
            for pt in state.particles
        ],

        "bg_particles": [
            {"x": bp.x, "y": bp.y, "size": bp.size,
             "lifetime": bp.lifetime, "max_lifetime": bp.max_lifetime}
            for bp in state.bg_particles
        ],

        "powerups": [
            {"x": pu.x, "y": pu.y, "sx": pu.sx, "sy": pu.sy,
             "type": pu.power_type}
            for pu in state.powerups
        ],

        "boss": (
            {
                "x": state.boss.x, "y": state.boss.y,
                "sx": state.boss.sx, "sy": state.boss.sy,
                "hp": state.boss.hp, "max_hp": state.boss.max_hp,
                "phase": state.boss.phase,
                "dark_aura": state.boss.dark_aura,
                "sword_angle": state.boss.sword_angle,
            }
            if state.boss else None
        ),
    }

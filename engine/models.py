from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class Choice:
    text: str
    next_scene: str
    color: str = "primary" # primary, secondary, success, danger
    points_reward: int = 0
    required_points: Optional[int] = None
    sets_flag: Optional[str] = None
    requires_flag: Optional[str] = None
    reputation: Optional[str] = None

@dataclass
class Scene:
    id: str
    title: str
    text: str
    choices: List[Choice] = field(default_factory=list)
    is_ending: bool = False
    image_url: Optional[str] = None

@dataclass
class Perspective:
    id: str
    label: str
    emoji: str
    description: str
    start_node: str

@dataclass
class Story:
    id: int | str
    title: str
    theme: str # acts as category
    description: str
    series: int = 1
    game_mode: str = "single" # "single" or "multi"
    scenes: Dict[str, Scene] = field(default_factory=dict)
    start_scene: str = "start"
    image_url: Optional[str] = None
    world_type: Optional[str] = None
    perspectives: List[Perspective] = field(default_factory=list)

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        return self.scenes.get(scene_id)

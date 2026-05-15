import json
import os
from typing import Dict, List, Optional
from engine.models import Story, Scene, Choice, Perspective

class StoryManager:
    def __init__(self, stories_dir: str = "data/stories"):
        self.stories_dir = stories_dir
        self.stories: Dict[int | str, Story] = {}
        self.load_all_stories()

    def load_all_stories(self):
        if not os.path.exists(self.stories_dir):
            os.makedirs(self.stories_dir)

        for filename in os.listdir(self.stories_dir):
            if filename.endswith(".json"):
                self.load_story(os.path.join(self.stories_dir, filename))

    def load_story(self, filepath: str):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            filename = os.path.basename(filepath)

            # Check if this is the new nested format (world format)
            if "world" in data and "categories" in data:
                world_name = data["world"]
                world_aliases = {
                    "الفانتازيا": "fantasy",
                    "الماضي": "past",
                    "المستقبل": "future",
                    "الواقع البديل": "alternate",
                    "القصص الفردية": "solo",
                }
                world_type = world_aliases.get(world_name, filename.split('.')[0])

                for category in data["categories"]:
                    cat_name = category.get("name")
                    for s_data in category.get("stories", []):
                        self._parse_and_add_story(s_data, theme=cat_name, world_type=world_type)
            # Check if it's the new nested solo format
            elif "id" in data and "nodes" in data and ("perspectives" in data or "perspective" in data):
                 story_theme = data.get("theme", "قصص-فردية")
                 story_world = data.get("world_type", "solo")
                 self._parse_and_add_story(data, theme=story_theme, world_type=story_world)
            # Old format fallback
            else:
                 self._parse_and_add_old_story(data)
                 story_id = self._resolve_story_id(data.get("id", 0))
                 story = self.stories.get(story_id)
                 if story:
                     if filename == "solo.json" or filename.startswith("sp_"):
                         story.world_type = "solo"
                         story.game_mode = "single"
                     elif filename.startswith("mp_"):
                         story.world_type = "multi"
                         story.game_mode = "multi"
                     elif filename == "fantasy.json":
                         story.world_type = "fantasy"
                     elif filename == "past.json":
                         story.world_type = "past"
                     elif filename == "future.json":
                         story.world_type = "future"
                     elif filename == "alternate.json":
                         story.world_type = "alternate"

        except Exception as e:
            print(f"Error loading story from {filepath}: {e}")

    def _parse_and_add_story(self, data: dict, theme: str, world_type: str):
        try:
            scenes = {}
            for node_id, node_data in data.get("nodes", {}).items():
                choices = []
                for choice_data in node_data.get("choices", []):
                    # Handle new "label" and "next" format, fallback to old "text" and "next_scene"
                    text = choice_data.get("label", choice_data.get("text", "استمرار"))
                    next_scene = choice_data.get("next", choice_data.get("next_scene", ""))
                    choices.append(Choice(
                        text=text,
                        next_scene=next_scene,
                        color=choice_data.get("color", "primary"),
                        points_reward=choice_data.get("points_reward", 0),
                        required_points=choice_data.get("required_points"),
                        sets_flag=choice_data.get("sets_flag"),
                        requires_flag=choice_data.get("requires_flag"),
                        reputation=choice_data.get("reputation")
                    ))

                scenes[node_id] = Scene(
                    id=node_id,
                    title=node_id, # The new format doesn't have scene titles natively, just nodes
                    text=node_data.get("text", ""),
                    choices=choices,
                    is_ending=node_data.get("is_ending", False),
                    image_url=node_data.get("image_url")
                )

            # Extract perspectives if present
            perspectives = []
            if "perspectives" in data:
                for p_data in data.get("perspectives", []):
                     perspectives.append(Perspective(
                         id=p_data.get("id", ""),
                         label=p_data.get("label", ""),
                         emoji=p_data.get("emoji", ""),
                         description=p_data.get("description", ""),
                         start_node=p_data.get("start_node", "")
                     ))
            elif "perspective" in data:
                p_data = data["perspective"]
                perspectives.append(Perspective(
                     id=p_data.get("id", ""),
                     label=p_data.get("label", ""),
                     emoji=p_data.get("emoji", ""),
                     description=p_data.get("description", ""),
                     start_node=p_data.get("start_node", "")
                ))

            # Use 'id' from JSON, but ensure it's converted to an int hash if it's a string, or require int IDs.
            # Assuming prompt IDs might be strings like "story_001", we hash them or extract integers.
            raw_id = data.get("id", 0)
            story_id = self._resolve_story_id(raw_id)
            if story_id in self.stories:
                print(
                    f"WARNING: Hash collision for story '{data.get('title')}' "
                    f"(id={raw_id}, hash={story_id}). Skipping."
                )
                return

            nodes = data.get("nodes", {})
            default_start = "start" if "start" in nodes else (next(iter(nodes)) if nodes else "start")
            if perspectives:
                perspective_start = perspectives[0].start_node
                if perspective_start in scenes:
                    resolved_start = perspective_start
                else:
                    resolved_start = default_start
            else:
                resolved_start = default_start
            story = Story(
                id=story_id,
                title=data.get("title", "بدون عنوان"),
                theme=theme,
                series=data.get("series", 1),
                game_mode="single", # All of these nested ones are single player for now based on prompt
                description=data.get("summary", data.get("description", "")),
                scenes=scenes,
                start_scene=resolved_start,
                world_type=world_type,
                perspectives=perspectives
            )

            self.stories[story.id] = story
            print(f"Loaded Nested Story {story.id}: {story.title}")

        except Exception as e:
            print(f"Error parsing nested story {data.get('title')}: {e}")

    def _parse_and_add_old_story(self, data: dict):
        scenes = {}
        for scene_data in data.get("scenes", []):
            choices = []
            for choice_data in scene_data.get("choices", []):
                choices.append(Choice(
                    text=choice_data["text"],
                    next_scene=choice_data["next_scene"],
                    color=choice_data.get("color", "primary"),
                    points_reward=choice_data.get("points_reward", 0),
                    required_points=choice_data.get("required_points"),
                    sets_flag=choice_data.get("sets_flag"),
                    requires_flag=choice_data.get("requires_flag"),
                    reputation=choice_data.get("reputation")
                ))

            scenes[scene_data["id"]] = Scene(
                id=scene_data["id"],
                title=scene_data["title"],
                text=scene_data["text"],
                choices=choices,
                is_ending=scene_data.get("is_ending", False),
                image_url=scene_data.get("image_url")
            )

        configured_start = data.get("start_scene", "start")
        if configured_start not in scenes:
            configured_start = "start" if "start" in scenes else (next(iter(scenes)) if scenes else "start")

        story = Story(
            id=data["id"],
            title=data["title"],
            theme=data.get("theme", "عام"),
            series=data.get("series", 1),
            game_mode=data.get("game_mode", "single"),
            description=data.get("description", ""),
            scenes=scenes,
            start_scene=configured_start,
            image_url=data.get("image_url"),
            world_type=data.get("world_type")
        )

        self.stories[story.id] = story
        print(f"Loaded Old Story {story.id}: {story.title}")

    def get_story(self, story_id: int | str) -> Optional[Story]:
        return self.stories.get(story_id)

    def resolve_story(self, story_ref: int | str, game_mode: str | None = None) -> Optional[Story]:
        """Resolve a story by id (int/str) or by exact title match."""
        candidates = self.stories.values() if game_mode is None else (
            s for s in self.stories.values() if s.game_mode == game_mode
        )

        # Direct lookup first
        if story_ref in self.stories:
            story = self.stories[story_ref]
            if game_mode is None or story.game_mode == game_mode:
                return story

        # Numeric string fallback (e.g. "108")
        if isinstance(story_ref, str) and story_ref.isdigit():
            parsed = int(story_ref)
            story = self.stories.get(parsed)
            if story and (game_mode is None or story.game_mode == game_mode):
                return story

        # Stringified ID fallback + exact-title fallback + hash ID fallback
        ref_text = str(story_ref).strip()
        ref_fold = ref_text.casefold()
        for story in candidates:
            if str(story.id) == ref_text:
                return story
            if story.title.strip().casefold() == ref_fold:
                return story

        # Try to resolve by generated integer ID if they supplied the original string ID
        import hashlib
        try:
            hashed_id = int(hashlib.sha256(ref_text.encode()).hexdigest(), 16) % 10**8
            if hashed_id in self.stories:
                story = self.stories[hashed_id]
                if game_mode is None or story.game_mode == game_mode:
                    return story
        except Exception:
            pass

        return None

    def get_all_stories(self) -> Dict[int | str, Story]:
        return self.stories

    def get_stories_by_mode(self, game_mode: str) -> Dict[int | str, Story]:
        return {k: v for k, v in self.stories.items() if v.game_mode == game_mode}

    def get_stories_by_world(self, world_type: str) -> Dict[int | str, Story]:
        return {k: v for k, v in self.stories.items() if v.world_type == world_type}

    def get_world_categories(self, world_type: str) -> Dict[str, List[Story]]:
        from collections import defaultdict
        stories = self.get_stories_by_world(world_type)
        categories = defaultdict(list)
        for s in stories.values():
            categories[s.theme].append(s)
        return dict(categories)

    def get_stories_by_world_and_category(self, world_type: str, category: str) -> List[Story]:
        stories = self.get_stories_by_world(world_type)
        return [s for s in stories.values() if s.theme == category]

    @staticmethod
    def _resolve_story_id(raw_id: int | str) -> int | str:
        if isinstance(raw_id, str):
            import hashlib
            return int(hashlib.sha256(raw_id.encode()).hexdigest(), 16) % 10**8
        return raw_id

import json
from pathlib import Path

from core.category_catalog import category_names_by_mode

STORIES_DIR = Path("data/stories")


def validate(filepath: Path) -> bool:
    with filepath.open("r", encoding="utf-8") as f:
        data = json.load(f)

    def check_story(story_data, expected_theme, mode):
        nodes = {}
        if "scenes" in story_data:
            nodes = {s["id"]: s for s in story_data["scenes"]}
        elif "nodes" in story_data:
            nodes = story_data["nodes"]

        node_ids = set(nodes.keys())
        start_nodes = []
        if "start_scene" in story_data:
            start_nodes.append(story_data["start_scene"])
        elif "perspectives" in story_data:
            start_nodes.extend([p["start_node"] for p in story_data["perspectives"]])
        elif "perspective" in story_data:
            start_nodes.append(story_data["perspective"]["start_node"])
        elif "start" in node_ids:
            start_nodes.append("start")

        for sn in start_nodes:
            if sn not in node_ids:
                print(f"ERROR: {filepath} -> Start node '{sn}' not found in story '{story_data.get('title', '')}'!")
                return False

        for node_id, node in nodes.items():
            choices = node.get("choices", [])
            for choice in choices:
                next_node = choice.get("next", choice.get("next_scene"))
                if next_node and next_node not in node_ids:
                    print(f"ERROR: {filepath} -> Node '{node_id}' references missing next_node '{next_node}' in story '{story_data.get('title', '')}'")
                    return False

        allowed_themes = set(category_names_by_mode(mode))
        if expected_theme and allowed_themes and expected_theme not in allowed_themes:
             print(
                f"ERROR: {filepath} -> Theme '{expected_theme}' is not valid for mode '{mode}'. "
                f"Allowed: {sorted(allowed_themes)}"
             )
             return False

        # Check node length constraint
        if len(node_ids) < 15:
            print(f"WARNING: {filepath} -> Story '{story_data.get('title', '')}' has fewer than 15 nodes ({len(node_ids)}).")

        return True

    all_valid = True
    if "world" in data and "categories" in data:
         for category in data["categories"]:
             cat_name = category.get("name")
             for s_data in category.get("stories", []):
                 if not check_story(s_data, cat_name, "single"):
                     all_valid = False
    elif "id" in data and "nodes" in data and ("perspectives" in data or "perspective" in data):
         if not check_story(data, data.get("theme", "جرائم وتحقيقات"), "single"):
             all_valid = False
    else:
         theme = data.get("theme", "")
         mode = data.get("game_mode", "single")
         if not check_story(data, theme, mode):
             all_valid = False

    if all_valid:
         print(f"Validation passed for {filepath}. All links and theme checks are valid!")
         return True
    return False


def validate_all() -> bool:
    files = sorted(STORIES_DIR.glob("*.json"))
    if not files:
        print("No story files found.")
        return False

    all_ok = True
    for filepath in files:
        if not validate(filepath):
            all_ok = False
    return all_ok


if __name__ == "__main__":
    if not validate_all():
        raise SystemExit(1)

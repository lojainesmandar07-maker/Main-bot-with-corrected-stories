import discord
from engine.models import Story, Scene

class SoloGameManager:
    def __init__(self, bot, story_manager):
        self.bot = bot
        self.story_manager = story_manager
        # Track active solo sessions: {user_id: {"story": Story, "scene": Scene, "points": int, "round": int}}
        self.active_sessions = {}

    def start_solo_game(self, user_id: int, story_id: int):
        story = self.story_manager.get_story(story_id)
        if not story:
            return None, "القصة غير موجودة."

        if story.game_mode != "single":
            return None, "هذه القصة غير مخصصة للعب الفردي."

        scene = story.get_scene(story.start_scene)
        if not scene:
            return None, "خطأ في تحميل المشهد الأول من القصة."

        self.active_sessions[user_id] = {
            "story": story,
            "scene": scene,
            "points": 0,
            "round": 1,
            "flags": set(),
            "reputation": {}
        }
        return self.active_sessions[user_id], None

    def end_solo_game(self, user_id: int):
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]

    def get_session(self, user_id: int):
        return self.active_sessions.get(user_id)

    def process_choice(self, user_id: int, choice_index: int):
        session = self.get_session(user_id)
        if not session:
            return None, "لا يوجد جلسة لعب نشطة."

        scene = session["scene"]
        if choice_index < 0 or choice_index >= len(scene.choices):
            return None, "خيار غير صالح."

        choice = scene.choices[choice_index]

        if choice.required_points is not None and session["points"] < choice.required_points:
            return None, f"عذراً، تحتاج إلى {choice.required_points} نقطة لاختيار هذا المسار (لديك {session['points']} نقطة)."

        if choice.requires_flag is not None and choice.requires_flag not in session["flags"]:
            return None, "عذراً، هذا الخيار غير متاح لك بناءً على قراراتك السابقة."

        next_scene = session["story"].get_scene(choice.next_scene)
        if not next_scene:
            return None, "خطأ: المشهد التالي غير موجود."

        session["points"] += choice.points_reward

        if choice.sets_flag is not None:
            session["flags"].add(choice.sets_flag)

        if choice.reputation is not None:
            if choice.reputation not in session["reputation"]:
                session["reputation"][choice.reputation] = 0
            session["reputation"][choice.reputation] += 1

        session["scene"] = next_scene
        session["round"] += 1

        return session, None

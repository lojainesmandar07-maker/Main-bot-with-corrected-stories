from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class StoryCategory:
    key: str
    name: str
    description: str


SOLO_CATEGORIES: List[StoryCategory] = [
    StoryCategory("crime_investigation", "التحقيق الجنائي", "حل ألغاز جرائم مع تتبع أدلة دقيقة وخيارات ذكية."),
    StoryCategory("psychological_horror", "الرعب النفسي", "تجارب توتر وعزلة وقرارات تؤثر على الحالة الذهنية للبطل."),
    StoryCategory("survival_disaster", "النجاة والكوارث", "الصمود أمام كوارث طبيعية أو صناعية بموارد محدودة."),
    StoryCategory("cyberpunk_heist", "الاختراق والسرقات التقنية", "عمليات اختراق أو سرقة عالية المخاطر في عالم رقمي."),
    StoryCategory("political_thriller", "التشويق السياسي", "مؤامرات سلطة وتحالفات متغيرة وقرارات أخلاقية صعبة."),
    StoryCategory("dark_fantasy", "الفانتازيا المظلمة", "عوالم سحرية خطرة مع ثمن واضح لكل اختيار."),
    StoryCategory("sci_fi_mystery", "الغموض العلمي", "أحداث غريبة وتقنيات مجهولة تتطلب تحليل وربط أدلة."),
    StoryCategory("prison_escape", "الهروب من الأسر", "محاولات هروب مع تخطيط دقيق ومخاطر تصاعدية."),

    # New World Categories
    StoryCategory("fantasy_thrones", "عروش مشققة", "عروش مشققة"),
    StoryCategory("fantasy_wars", "حروب لا تنتهي", "حروب لا تنتهي"),
    StoryCategory("fantasy_knights", "أحلام الفرسان", "أحلام الفرسان"),
    StoryCategory("fantasy_witches", "ساحرات وأسرار", "ساحرات وأسرار"),
    StoryCategory("fantasy_dark", "الظلام يحكم", "الظلام يحكم"),

    StoryCategory("past_civilizations", "حضارات على الحافة", "حضارات على الحافة"),
    StoryCategory("past_rulers", "الحاكم والشعب", "الحاكم والشعب"),
    StoryCategory("past_spies", "جواسيس التاريخ", "جواسيس التاريخ"),
    StoryCategory("past_revolutions", "ثورات وانتفاضات", "ثورات وانتفاضات"),
    StoryCategory("past_time_travel", "السفر عبر التاريخ", "السفر عبر التاريخ"),

    StoryCategory("future_ai", "ذكاء اصطناعي يتمرد", "ذكاء اصطناعي يتمرد"),
    StoryCategory("future_dying_planet", "كوكب محتضر", "كوكب محتضر"),
    StoryCategory("future_colonies", "مستعمرات الفضاء", "مستعمرات الفضاء"),
    StoryCategory("future_identity", "هوية في عالم مزيف", "هوية في عالم مزيف"),
    StoryCategory("future_last_war", "الحرب الأخيرة", "الحرب الأخيرة"),

    StoryCategory("alt_history", "لو التاريخ تغير", "لو التاريخ تغير"),
    StoryCategory("alt_clone", "نسخة أخرى منك", "نسخة أخرى منك"),
    StoryCategory("alt_laws", "قوانين مختلفة", "قوانين مختلفة"),
    StoryCategory("alt_invasion", "الغزو الصامت", "الغزو الصامت"),
    StoryCategory("alt_matrix", "الواقع يتكسر", "الواقع يتكسر"),

    # New Solo Categories
    StoryCategory("solo_crime", "جرائم وتحقيقات", "جرائم وتحقيقات"),
    StoryCategory("solo_horror", "رعب نفسي", "رعب نفسي"),
    StoryCategory("solo_dark_social", "ظلام اجتماعي", "ظلام اجتماعي"),
    StoryCategory("solo_survival", "بقاء وانهيار", "بقاء وانهيار"),
    StoryCategory("solo_secrets", "أسرار مدفونة", "أسرار مدفونة"),
]


EVENT_CATEGORIES: List[StoryCategory] = [
    StoryCategory("team_survival", "نجاة الفريق", "مجموعة عالقة في بيئة خطرة وتحتاج قرارات جماعية متوازنة."),
    StoryCategory("ethical_dilemma", "المعضلات الأخلاقية", "خيارات تصويت تقسم اللاعبين بين المصلحة والمبادئ."),
    StoryCategory("kingdom_politics", "سياسة الممالك", "إدارة مدينة/مملكة عبر تصويتات تحدد المصير الجماعي."),
    StoryCategory("space_crisis", "أزمات الفضاء", "فريق على مركبة أو محطة فضائية تحت ضغط قرارات مصيرية."),
    StoryCategory("zombie_outbreak", "تفشي العدوى", "البقاء كفريق أثناء انهيار النظام وانتشار العدوى."),
    StoryCategory("expedition_ruins", "بعثات الأطلال", "بعثة استكشاف تتخذ قرارات مشتركة بين المخاطرة والانسحاب."),
    StoryCategory("rebellion_conflict", "التمرد والصراعات", "صراع فصائل يفرض على اللاعبين اختيار تحالفات متقلبة."),
    StoryCategory("mythic_trial", "اختبارات أسطورية", "فريق يواجه تحديات أسطورية تتطلب تضحية وتعاون."),
]


def categories_by_mode(game_mode: str) -> List[StoryCategory]:
    if game_mode == "single":
        return SOLO_CATEGORIES
    if game_mode == "multi":
        return EVENT_CATEGORIES
    return []


def category_names_by_mode(game_mode: str) -> List[str]:
    return [c.name for c in categories_by_mode(game_mode)]


def category_description_map(game_mode: str) -> Dict[str, str]:
    return {c.name: c.description for c in categories_by_mode(game_mode)}

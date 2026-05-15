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

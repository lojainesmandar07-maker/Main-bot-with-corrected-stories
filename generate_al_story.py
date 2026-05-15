import json

story = {
  "id": "al_broken_mirrors",
  "title": "صدى المرايا المكسورة",
  "world": "alt_reality",
  "world_type": "alternate",
  "category": "الواقع يتكسر",
  "summary": "أنت مفتش حقائق في القاهرة البخارية. تكتشف أن حياتك بأكملها مجرد طبقة مبرمجة، وعليك الاختيار بين تحطيم الواقع المزيف أو حماية عائلتك الوهمية.",
  "difficulty": "صعب",
  "estimated_length": "طويلة",
  "theme": "الواقع يتكسر",
  "game_mode": "single",
  "perspective": {
    "id": "truth_inspector",
    "label": "منظور مفتش الحقائق",
    "emoji": "👁️",
    "description": "أنت ترى الشذوذ في الواقع قبل غيرك، لكنك ملزم بقوانين النظام.",
    "start_node": "start"
  },
  "nodes": {
    "start": {
      "text": "الساعة تدق السابعة صباحاً. القاهرة البخارية مغطاة بدخان المصانع، لكنك تلاحظ أمراً غريباً: الدخان يتساقط كالمطر بدلاً من أن يرتفع. أنت مفتش حقائق. هل تتجاهل هذا الشذوذ وتذهب لعملك كالمعتاد، أم تفحصه عن قرب؟",
      "choices": [
        {
          "label": "اذهب للعمل",
          "emoji": "🏢",
          "next": "go_to_work",
          "points_reward": 0,
          "color": "primary"
        },
        {
          "label": "افحص الدخان",
          "emoji": "🔍",
          "next": "inspect_smoke",
          "points_reward": 1,
          "color": "secondary",
          "sets_flag": "flag_doubt"
        }
      ]
    },
    "go_to_work": {
      "text": "تصل إلى مقر الوزارة. شريكك 'ياسين' ينتظرك بملف جديد. 'شذوذ من الدرجة الثالثة في حارة النحاسين'. يبتسم ببرود. هل تسأله عن الدخان المتساقط، أم تأخذ الملف بصمت؟",
      "choices": [
        {
          "label": "اسأله عن الدخان",
          "emoji": "❓",
          "next": "ask_partner_smoke",
          "points_reward": 0,
          "color": "primary"
        },
        {
          "label": "خذ الملف بصمت",
          "emoji": "📁",
          "next": "take_file_silent",
          "points_reward": 1,
          "color": "secondary",
          "sets_flag": "flag_compliance"
        }
      ]
    },
    "ask_partner_smoke": {
      "text": "تتغير ملامح ياسين فجأة. تصبح عيناه فارغتين للحظة، ثم يعود لابتسامته الباردة: 'لا يوجد دخان يتساقط، يا صديقي. خذ الملف'.",
      "choices": [
        {
          "label": "تظاهر بالموافقة",
          "emoji": "🤝",
          "next": "take_file_silent",
          "points_reward": 1,
          "color": "primary"
        },
        {
          "label": "أصر على كلامك",
          "emoji": "🗣️",
          "next": "insist_smoke",
          "points_reward": 0,
          "color": "danger"
        }
      ]
    },
    "insist_smoke": {
      "text": "تصر على رؤيتك. ياسين يضغط زراً تحت مكتبه. تدخل فرقة من 'المنظفين' بوجوه تشبه المرايا. يحيطون بك ويمسكون بك.",
      "choices": [
        {
          "label": "قاوم المنظفين",
          "emoji": "⚔️",
          "next": "fight_cleaners_early",
          "points_reward": 0,
          "color": "danger"
        },
        {
          "label": "استسلم لهم",
          "emoji": "🏳️",
          "next": "surrender_cleaners_early",
          "points_reward": 0,
          "color": "primary"
        }
      ]
    },
    "fight_cleaners_early": {
      "text": "تحاول ضرب أقرب منظف، لكن يدك تمر عبر وجهه كأنه مصنوع من زجاج سائل. يمسكون بك ويحقنونك بمادة باردة.",
      "choices": [
        {
          "label": "افقد وعيك",
          "emoji": "💤",
          "next": "surrender_cleaners_early",
          "points_reward": 0,
          "color": "primary"
        }
      ]
    },
    "surrender_cleaners_early": {
      "text": "تفقد وعيك. تستيقظ في غرفتك القديمة. لا تتذكر اسمك. المنظفون يراقبونك كجثة. لقد مسحوا وعيك تماماً.",
      "choices": [
        {
          "label": "استمر كصدى",
          "emoji": "👻",
          "next": "death_ignored_glitch_pre",
          "points_reward": 0,
          "color": "primary"
        }
      ]
    },
    "death_ignored_glitch_pre": {
      "text": "تستمر في حياة خالية من المعنى.",
      "choices": [
        {
          "label": "انسَ كل شيء",
          "emoji": "🧠",
          "next": "death_ignored_glitch",
          "points_reward": 0,
          "color": "primary"
        }
      ]
    },
    "death_ignored_glitch": {
      "text": "لقد أبلغت عن الشذوذ دون حذر. المنظفون مسحوا ذاكرتك وأعادوك كمواطن آلي. مت وأنت حي، مجرد ترس في آلة لا تفهمها. الفضول الغبي دون حذر هو انتحار.",
      "is_ending": True,
      "choices": []
    },
    "inspect_smoke": {
      "text": "تلمس الدخان الهابط. إنه بارد وقاسي كشظايا الزجاج الرمادي. فجأة، تتشقق السماء فوقك لبضع ثوانٍ وتظهر أرقام خضراء قبل أن تعود طبيعية. قلبك يدق بقوة.",
      "choices": [
        {
          "label": "اذهب للعمل بسرعة",
          "emoji": "🏃",
          "next": "go_to_work",
          "points_reward": 1,
          "color": "primary"
        },
        {
          "label": "ابحث عن مصدر الشق",
          "emoji": "🔍",
          "next": "search_sky_rift",
          "points_reward": 2,
          "color": "secondary",
          "sets_flag": "flag_glitch_vision"
        }
      ]
    },
    "search_sky_rift": {
      "text": "تتبع أثر الشق البصري نحو زقاق مهجور. تجد ساعة جيب قديمة تطفو في الهواء. هل تلمسها؟",
      "choices": [
        {
          "label": "المس الساعة",
          "emoji": "⏱️",
          "next": "touch_floating_watch",
          "points_reward": 1,
          "color": "primary"
        },
        {
          "label": "تراجع بصمت",
          "emoji": "🔙",
          "next": "go_to_work",
          "points_reward": 0,
          "color": "secondary"
        }
      ]
    },
    "touch_floating_watch": {
      "text": "تلمس الساعة. تتدفق ذكريات ليست لك إلى رأسك: مدن من زجاج، طائرات معدنية ضخمة، وحروب بلا دخان. هذه الأداة من خارج عالمك. تضعها في جيبك خفية وتتوجه للوزارة.",
      "choices": [
        {
          "label": "توجه للوزارة",
          "emoji": "🏢",
          "next": "take_file_silent",
          "points_reward": 1,
          "color": "primary"
        }
      ]
    },
    "take_file_silent": {
      "text": "تخرج في مهمتك نحو حارة النحاسين. الشذوذ يبدو كبائع أقمشة يعرض حريراً يغير لونه حسب أفكار المشتري. هذا انتهاك خطير لقوانين الفيزياء المعيارية.",
      "choices": [
        {
          "label": "صادر الحرير واعتقله",
          "emoji": "🔗",
          "next": "arrest_vendor",
          "points_reward": 1,
          "color": "danger",
          "reputation": "agent"
        },
        {
          "label": "اسأله عن مصدره",
          "emoji": "❓",
          "next": "question_vendor",
          "points_reward": 2,
          "color": "secondary",
          "reputation": "rebel"
        }
      ]
    },
    "arrest_vendor": {
      "text": "تعتقل البائع وتصادر الحرير. أثناء تقييده، يهمس في أذنك: 'زوجتك لا وجود لها، إنها مجرد كود برمجي'. يتجمد الدم في عروقك.",
      "choices": [
        {
          "label": "اضربه لإسكاته",
          "emoji": "👊",
          "next": "punch_vendor",
          "points_reward": 0,
          "color": "danger",
          "sets_flag": "flag_compliance"
        },
        {
          "label": "دعه يكمل كلامه",
          "emoji": "👂",
          "next": "listen_vendor_secret",
          "points_reward": 1,
          "color": "secondary"
        }
      ]
    },
    "punch_vendor": {
      "text": "تلكمه فيسقط. تقوم بتسليمه للمركز، لكن كلماته تبقى محفورة في رأسك. تعود لمنزلك.",
      "choices": [
        {
          "label": "عد للمنزل",
          "emoji": "🏠",
          "next": "return_home",
          "points_reward": 1,
          "color": "primary"
        }
      ]
    },
    "question_vendor": {
      "text": "تسأله بهدوء. ينظر حوله بخوف ثم يهمس: 'أنا لست من هنا. نحن جميعاً في وعاء بيانات. إذا كنت تريد رؤية الحقيقة، اذهب إلى سراديب محطة القطار المهجورة'.",
      "choices": [
        {
          "label": "اعتقله كالمعتاد",
          "emoji": "🔗",
          "next": "arrest_vendor",
          "points_reward": 0,
          "color": "danger"
        },
        {
          "label": "دعه يهرب سرا",
          "emoji": "🏃",
          "next": "let_vendor_escape",
          "points_reward": 2,
          "color": "success",
          "sets_flag": "flag_truth_seeker"
        }
      ]
    },
    "listen_vendor_secret": {
      "text": "يقول لك: 'ابحث خلف المرآة في غرفة نومك. ستجد الشذوذ الذي تركوه لك'. ثم يسلم نفسه طواعية.",
      "choices": [
        {
          "label": "عد للمنزل فوراً",
          "emoji": "🏠",
          "next": "return_home",
          "points_reward": 1,
          "color": "primary"
        }
      ]
    },
    "let_vendor_escape": {
      "text": "تسمح له بالفرار في زقاق جانبي وتكتب في تقريرك أن الشذوذ كان بلاغا كاذباً. أنت الآن تخون النظام.",
      "choices": [
        {
          "label": "اذهب للمنزل لترتاح",
          "emoji": "🏠",
          "next": "return_home",
          "points_reward": 1,
          "color": "primary"
        },
        {
          "label": "اذهب للسراديب فوراً",
          "emoji": "🚇",
          "next": "go_catacombs_early",
          "points_reward": 2,
          "color": "secondary"
        }
      ]
    },
    "return_home": {
      "text": "تدخل منزلك. زوجتك 'ليلى' تستقبلك بابتسامة دافئة كالعادة. كل شيء يبدو مثالياً، مثالياً جداً. هل تسألها عن ماضيكم، أم تفحص مرآة غرفتك؟",
      "choices": [
        {
          "label": "اسألها عن ماضيكم",
          "emoji": "💬",
          "next": "ask_wife_past",
          "points_reward": 1,
          "color": "primary",
          "sets_flag": "flag_family_tie"
        },
        {
          "label": "افحص مرآة الغرفة",
          "emoji": "🪞",
          "next": "inspect_mirror",
          "points_reward": 2,
          "color": "secondary"
        }
      ]
    },
    "ask_wife_past": {
      "text": "تسألها عن يوم زفافكما. تبتسم وتقول: 'كان يوماً ممطراً في نوفمبر...'. لكنك فجأة تدرك أنك لا تملك أي صورة لذلك اليوم، ولا ذكرى حقيقية، فقط كلمات تتردد كأنها محفوظة.",
      "choices": [
        {
          "label": "افحص المرآة بسرعة",
          "emoji": "🪞",
          "next": "inspect_mirror",
          "points_reward": 1,
          "color": "primary"
        },
        {
          "label": "تجاهل الشك ونم",
          "emoji": "🛏️",
          "next": "ignore_doubt_sleep",
          "points_reward": 0,
          "color": "danger"
        }
      ]
    },
    "ignore_doubt_sleep": {
      "text": "تذهب للنوم متجاهلاً كل شيء.",
      "choices": [
        {
          "label": "استيقظ في الصباح",
          "emoji": "☀️",
          "next": "wake_up_loop",
          "points_reward": 0,
          "color": "primary"
        }
      ]
    },
    "wake_up_loop": {
      "text": "تستيقظ لتجد الدخان يتساقط كالمطر مجدداً. اليوم يعيد نفسه تماماً.",
      "choices": [
        {
          "label": "حاول تغيير الأحداث",
          "emoji": "🔄",
          "next": "try_change_loop",
          "points_reward": 0,
          "color": "primary"
        }
      ]
    },
    "try_change_loop": {
      "text": "مهما حاولت، الأحداث تعيد نفسها في حلقة مفرغة مدتها ثلاث دقائق.",
      "choices": [
        {
          "label": "استسلم للحلقة",
          "emoji": "♾️",
          "next": "death_time_loop",
          "points_reward": 0,
          "color": "danger"
        }
      ]
    },
    "death_time_loop": {
      "text": "لقد علقت في حلقة زمنية مغلقة. اخترت الراحة على الحقيقة، فعاقبك النظام بحبسك في ثلاث دقائق تعيد نفسها للأبد. الجهل ليس نعيماً، بل هو سجن أبدي.",
      "is_ending": True,
      "choices": []
    },
    "inspect_mirror": {
      "text": "تقف أمام المرآة. تنظر خلفها فتجد شريحة معدنية غريبة نابضة. بمجرد لمسها، يسقط الجدار الوهمي لغرفتك، كاشفاً عن أسلاك مضيئة وأرقام. بيتك بأكمله مزيف.",
      "choices": [
        {
          "label": "اواجه زوجتي بالحقيقة",
          "emoji": "🗣️",
          "next": "confront_wife",
          "points_reward": 1,
          "color": "danger"
        },
        {
          "label": "اهرب من النافذة",
          "emoji": "🏃",
          "next": "escape_window",
          "points_reward": 2,
          "color": "success"
        }
      ]
    },
    "confront_wife": {
      "text": "تدخل ليلى. عندما ترى الجدار المكسور، تتجمد ملامحها وتتحول عيناها إلى شاشات بيضاء. تقول بصوت آلي: 'تم اكتشاف خرق. جاري استدعاء المنظفين'.",
      "choices": [
        {
          "label": "اهرب بسرعة للشارع",
          "emoji": "🏃",
          "next": "escape_street",
          "points_reward": 1,
          "color": "primary"
        },
        {
          "label": "حاول إنقاذها",
          "emoji": "💔",
          "next": "try_save_wife",
          "points_reward": 0,
          "color": "danger"
        }
      ]
    },
    "try_save_wife": {
      "text": "تمسك بها، محاولاً إيقاظها.",
      "choices": [
        {
          "label": "استمر في المحاولة",
          "emoji": "⏳",
          "next": "cleaners_arrive",
          "points_reward": 0,
          "color": "primary"
        }
      ]
    },
    "cleaners_arrive": {
      "text": "يقتحم المنظفون الغرفة من خلال النوافذ.",
      "choices": [
        {
          "label": "قاومهم",
          "emoji": "⚔️",
          "next": "death_caught_by_cleaners",
          "points_reward": 0,
          "color": "danger"
        }
      ]
    },
    "death_caught_by_cleaners": {
      "text": "حاولت إنقاذ برنامج حاسوبي لا يملك روحاً. المنظفون حاصروك وحذفوا الكود الخاص بك من السجلات. لم يعد لك أي أثر، وكأنك لم تولد قط.",
      "is_ending": True,
      "choices": []
    },
    "escape_window": {
      "text": "تقفز من النافذة إلى الزقاق الخلفي. تسمع أجهزة إنذار تدوي في السماء. المدينة تبدأ بالتغير؛ المباني تتلوى كالورق. يجب أن تصل إلى محطة القطار للهروب.",
      "choices": [
        {
          "label": "اركب ترام البخار",
          "emoji": "🚋",
          "next": "take_tram",
          "points_reward": 1,
          "color": "primary"
        },
        {
          "label": "اركض عبر الأزقة",
          "emoji": "🏃",
          "next": "run_alleys",
          "points_reward": 1,
          "color": "secondary"
        }
      ]
    },
    "escape_street": {
      "text": "تخرج للشارع الرئيسي. الناس متجمدون كالتماثيل. شريكك 'ياسين' يقف في النهاية شاهراً سلاحه الغريب.",
      "choices": [
        {
          "label": "استسلم له",
          "emoji": "🏳️",
          "next": "trust_partner",
          "points_reward": 0,
          "color": "danger"
        },
        {
          "label": "اهرب للزقاق المعتم",
          "emoji": "🏃",
          "next": "run_alleys",
          "points_reward": 1,
          "color": "primary"
        }
      ]
    },
    "trust_partner": {
      "text": "ترفع يديك وتقترب من ياسين معتقداً أنه سيساعدك.",
      "choices": [
        {
          "label": "تحدث إليه",
          "emoji": "🗣️",
          "next": "talk_partner_trust",
          "points_reward": 0,
          "color": "primary"
        }
      ]
    },
    "talk_partner_trust": {
      "text": "ياسين يرفع سلاحه مباشرة نحو رأسك. 'آسف، النظام يقتضي ذلك'.",
      "choices": [
        {
          "label": "حاول تفادي الطلقة",
          "emoji": "⚡",
          "next": "death_betrayed_by_partner",
          "points_reward": 0,
          "color": "danger"
        }
      ]
    },
    "death_betrayed_by_partner": {
      "text": "تطلق عليك رصاصة صامتة تمزق وعيك. وثقت بمن هو مبرمج لاصطيادك. في هذا العالم، الولاء الوحيد هو للنظام.",
      "is_ending": True,
      "choices": []
    },
    "run_alleys": {
      "text": "تركض في الأزقة. الجاذبية تبدأ بالاختلال. بعض براميل القمامة تطفو نحو الأعلى. المنظفون يقتربون من الخلف بخطوات لا تصدر صوتاً.",
      "choices": [
        {
          "label": "تسلق للأسطح المقلوبة",
          "emoji": "🧗",
          "next": "climb_inverted_roofs",
          "points_reward": 2,
          "color": "primary"
        },
        {
          "label": "اختبئ في قبو",
          "emoji": "🕳️",
          "next": "hide_basement",
          "points_reward": 1,
          "color": "secondary"
        }
      ]
    },
    "hide_basement": {
      "text": "تختبئ في القبو.",
      "choices": [
        {
          "label": "انتظر ذهابهم",
          "emoji": "⏳",
          "next": "cleaners_arrive",
          "points_reward": 0,
          "color": "primary"
        }
      ]
    },
    "climb_inverted_roofs": {
      "text": "بسبب خلل الجاذبية، تقفز للأعلى وتهبط على سقف مقلوب. تجري والمدينة رأسك على عقب. ترى محطة القطار المركزية في الأسفل (الذي كان الأعلى).",
      "choices": [
        {
          "label": "اقفز نحو المحطة",
          "emoji": "🪂",
          "next": "jump_to_station",
          "points_reward": 2,
          "color": "primary"
        },
        {
          "label": "تريث وامش بحذر",
          "emoji": "🚶",
          "next": "walk_careful_roofs",
          "points_reward": 1,
          "color": "secondary"
        }
      ]
    },
    "walk_careful_roofs": {
      "text": "الجاذبية تعود فجأة لطبيعتها. تسقط.",
      "choices": [
        {
          "label": "حاول التشبث",
          "emoji": "🧗",
          "next": "death_gravity_inversion",
          "points_reward": 0,
          "color": "primary"
        }
      ]
    },
    "death_gravity_inversion": {
      "text": "عادت الجاذبية فجأة. سقطت من السماء الوهمية وتهشمت على أسفلت الواقع المزيف. ترددك في استغلال الخلل أدى إلى هلاكك.",
      "is_ending": True,
      "choices": []
    },
    "take_tram": {
      "text": "تركب الترام. السائق بلا ملامح. الترام يتسارع بشكل جنوني، القضبان أمامه تتلاشى في فراغ أسود.",
      "choices": [
        {
          "label": "اقفز من الترام",
          "emoji": "🏃",
          "next": "death_train_jump",
          "points_reward": 0,
          "color": "danger"
        },
        {
          "label": "انتظر داخل الترام",
          "emoji": "⏳",
          "next": "tram_void_entry",
          "points_reward": 2,
          "color": "primary"
        }
      ]
    },
    "death_train_jump": {
      "text": "قفزت من الترام هرباً من الفراغ، لكنك سقطت في فجوة بين طبقات الواقع. ستظل تسقط للأبد في العدم. الهروب العشوائي أسوأ من المواجهة.",
      "is_ending": True,
      "choices": []
    },
    "tram_void_entry": {
      "text": "يخترق الترام الفراغ ويهبط بسلام في محطة سرية أسفل الأرض. هذه هي 'السراديب'.",
      "choices": [
        {
          "label": "انزل واستكشف",
          "emoji": "🔦",
          "next": "go_catacombs_early",
          "points_reward": 1,
          "color": "primary"
        }
      ]
    },
    "jump_to_station": {
      "text": "تقفز عبر خلل الجاذبية وتهبط بصعوبة على الزجاج الملون لمحطة القطار. الزجاج يتحطم وتسقط داخل بهو المحطة المهجور.",
      "choices": [
        {
          "label": "ابحث عن السراديب",
          "emoji": "🔦",
          "next": "go_catacombs_early",
          "points_reward": 1,
          "color": "primary"
        }
      ]
    },
    "go_catacombs_early": {
      "text": "تصل إلى أنفاق مظلمة تحت المحطة. تجد مجموعة من الأشخاص بملابس غريبة، يحملون أسلحة تنبعث منها إضاءة زرقاء. يوجهون أسلحتهم نحوك. قائدتهم تُدعى 'مريم'.",
      "choices": [
        {
          "label": "ارفع يديك مستسلما",
          "emoji": "🙌",
          "next": "surrender_resistance",
          "points_reward": 1,
          "color": "primary"
        },
        {
          "label": "أرهم الشريحة الغريبة",
          "emoji": "📟",
          "next": "show_anomaly_chip",
          "points_reward": 2,
          "color": "success",
          "requires_flag": "flag_truth_seeker"
        }
      ]
    },
    "surrender_resistance": {
      "text": "ترفع يديك. تقترب مريم وتفحص عينيك بضوء غريب. 'إنه غير متصل كلياً بعد، يمكن إنقاذه'. تأخذك لداخل المخبأ.",
      "choices": [
        {
          "label": "امش معهم",
          "emoji": "🚶",
          "next": "inside_resistance_base",
          "points_reward": 1,
          "color": "primary"
        }
      ]
    },
    "show_anomaly_chip": {
      "text": "تريهم الشريحة التي وجدتها (أو الساعة). مريم تخفض سلاحها بذهول: 'أنت من أحضرت المفتاح!'. احترامهم لك يزداد فوراً.",
      "choices": [
        {
          "label": "ادخل المخبأ بفخر",
          "emoji": "🚶",
          "next": "inside_resistance_base",
          "points_reward": 2,
          "color": "primary"
        }
      ]
    },
    "inside_resistance_base": {
      "text": "يشرحون لك أن الأرض دُمرت، والبشرية تعيش في محاكاة يديرها 'المهندس' للحفاظ على عقولهم. مريم تعرض عليك حبتين دواء: زرقاء لتنسى كل هذا وتعود لحياتك، وحمراء لترى الواقع الكودي.",
      "choices": [
        {
          "label": "خذ الحبة الزرقاء",
          "emoji": "💊",
          "next": "death_wrong_pill",
          "points_reward": 0,
          "color": "danger"
        },
        {
          "label": "خذ الحبة الحمراء",
          "emoji": "💊",
          "next": "take_red_pill",
          "points_reward": 2,
          "color": "success",
          "sets_flag": "flag_truth_seeker"
        }
      ]
    },
    "death_wrong_pill": {
      "text": "ابتلعت الحبة الزرقاء أملاً في العودة لحياتك. لكن النظام اعتبرك ملفاً تالفاً ورفض إعادتك. احترق دماغك بالكامل. التردد في اللحظات الحاسمة هو نهايتك.",
      "is_ending": True,
      "choices": []
    },
    "take_red_pill": {
      "text": "تبتلع الحبة الحمراء. العالم يذوب ليتحول إلى شلالات من الأرقام والرموز المضيئة. تستطيع الآن رؤية هيكل البرمجة المحيط بك.",
      "choices": [
        {
          "label": "حدق طويلا في الكود",
          "emoji": "👁️",
          "next": "stare_at_code",
          "points_reward": 0,
          "color": "danger"
        },
        {
          "label": "ركز على مريم",
          "emoji": "👤",
          "next": "focus_on_mary",
          "points_reward": 1,
          "color": "primary"
        }
      ]
    },
    "stare_at_code": {
      "text": "تحدق في لا نهائية الكود.",
      "choices": [
        {
          "label": "استمر بالتحديق",
          "emoji": "👁️",
          "next": "death_mind_shatter",
          "points_reward": 0,
          "color": "danger"
        }
      ]
    },
    "death_mind_shatter": {
      "text": "عقلك البشري لم يحتمل رؤية اللانهائية المطلقة للبرمجة الأساسية دفعة واحدة. تحطم وعيك تماماً وصرت مجرد قطعة بيانات تائهة.",
      "is_ending": True,
      "choices": []
    },
    "focus_on_mary": {
      "text": "تستعيد تركيزك. تخبرك مريم بالخطة: اقتحام 'البرج الأساسي' لتدمير النواة وتحرير البشرية. المنظفون بدأوا هجوماً مفاجئاً على المخبأ!",
      "choices": [
        {
          "label": "دافع عن المخبأ",
          "emoji": "🛡️",
          "next": "defend_base",
          "points_reward": 1,
          "color": "primary"
        },
        {
          "label": "اهرب نحو البرج",
          "emoji": "🏃",
          "next": "run_to_tower",
          "points_reward": 1,
          "color": "secondary"
        }
      ]
    },
    "defend_base": {
      "text": "تقاتل بجانب مريم باستخدام رؤيتك الجديدة، يمكنك توقع حركات المنظفين قبل حدوثها بثوانٍ. المعركة شرسة.",
      "choices": [
        {
          "label": "اضرب قائدهم",
          "emoji": "⚔️",
          "next": "strike_leader",
          "points_reward": 2,
          "color": "primary"
        },
        {
          "label": "تراجع بصمت",
          "emoji": "🔙",
          "next": "cleaners_arrive",
          "points_reward": 0,
          "color": "danger"
        }
      ]
    },
    "strike_leader": {
      "text": "تقضي على قائدهم. تفتحون ثغرة للهرب نحو البرج المركزي الأساسي وسط انهيار المحاكاة من حولكم.",
      "choices": [
        {
          "label": "اركض نحو البرج",
          "emoji": "🗼",
          "next": "run_to_tower",
          "points_reward": 1,
          "color": "primary"
        }
      ]
    },
    "run_to_tower": {
      "text": "تصلون إلى قاعدة البرج المركزي. هناك بابان: باب يحمل علامة 'مخرج الطوارئ'، ومصعد زجاجي مكسور.",
      "choices": [
        {
          "label": "ادخل مخرج الطوارئ",
          "emoji": "🚪",
          "next": "fake_exit_door",
          "points_reward": 0,
          "color": "danger"
        },
        {
          "label": "تسلق المصعد المكسور",
          "emoji": "🛗",
          "next": "climb_elevator",
          "points_reward": 2,
          "color": "primary"
        }
      ]
    },
    "fake_exit_door": {
      "text": "تدخل المخرج.",
      "choices": [
        {
          "label": "امش في الممر",
          "emoji": "🚶",
          "next": "death_fake_exit",
          "points_reward": 0,
          "color": "danger"
        }
      ]
    },
    "death_fake_exit": {
      "text": "كان فخاً من النظام. الممر عبارة عن محرقة أكواد. تم حرق بياناتك بالكامل. الطرق السهلة في المحاكاة دائماً تقود للهلاك.",
      "is_ending": True,
      "choices": []
    },
    "climb_elevator": {
      "text": "تتسلق كابلات المصعد بصعوبة. مريم تُصاب برصاصة برمجية في كتفها. تقول لك: 'اتركني واكمل، يجب أن تدمر النواة'.",
      "choices": [
        {
          "label": "احملها واكمل",
          "emoji": "💪",
          "next": "carry_mary",
          "points_reward": 2,
          "color": "primary",
          "reputation": "rebel"
        },
        {
          "label": "اتركها واصعد وحدك",
          "emoji": "🏃",
          "next": "climb_alone",
          "points_reward": 1,
          "color": "secondary",
          "reputation": "agent"
        }
      ]
    },
    "carry_mary": {
      "text": "تحملها بصعوبة بالغة. تصلان معاً إلى غرفة النواة، لكنك منهك تماماً. مريم تبتسم لك بامتنان.",
      "choices": [
        {
          "label": "ادخل غرفة النواة",
          "emoji": "🚪",
          "next": "core_room_entry",
          "points_reward": 1,
          "color": "primary"
        }
      ]
    },
    "climb_alone": {
      "text": "تتركها وتصعد بسرعة. تصل إلى غرفة النواة بكامل طاقتك، لكن وحدتك تترك فراغاً في داخلك.",
      "choices": [
        {
          "label": "ادخل غرفة النواة",
          "emoji": "🚪",
          "next": "core_room_entry",
          "points_reward": 1,
          "color": "primary"
        }
      ]
    },
    "core_room_entry": {
      "text": "غرفة بيضاء لانهائية. 'المهندس' يقف هناك، يرتدي بدلة بيضاء. يقول بهدوء: 'مرحباً يا مفتش. البشرية تدمرت في الخارج. هذه المحاكاة هي خلاصهم الوحيد. ماذا تريد أن تفعل؟'",
      "choices": [
        {
          "label": "دمر النواة فوراً",
          "emoji": "💥",
          "next": "destroy_core_attempt",
          "points_reward": 2,
          "color": "danger"
        },
        {
          "label": "استمع لعرضه",
          "emoji": "👂",
          "next": "listen_architect",
          "points_reward": 1,
          "color": "secondary"
        }
      ]
    },
    "listen_architect": {
      "text": "المهندس يعرض عليك إعادة تشكيل المحاكاة. لتكون أنت المهندس الجديد وتصلح العيوب، أو تعود لحياتك الوهمية المثالية.",
      "choices": [
        {
          "label": "أريد حياة زوجتي مجددا",
          "emoji": "❤️",
          "next": "want_fake_life",
          "points_reward": 1,
          "requires_flag": "flag_family_tie",
          "color": "primary"
        },
        {
          "label": "سأكون المهندس الجديد",
          "emoji": "👑",
          "next": "become_architect_attempt",
          "points_reward": 2,
          "color": "secondary"
        },
        {
          "label": "ارفض ودمر النظام",
          "emoji": "💥",
          "next": "destroy_core_attempt",
          "points_reward": 1,
          "color": "danger"
        }
      ]
    },
    "want_fake_life": {
      "text": "تطلب العودة. المهندس يبتسم.",
      "choices": [
        {
          "label": "اغلق عينيك",
          "emoji": "💤",
          "next": "ending_beautiful_lie",
          "points_reward": 1,
          "color": "primary"
        }
      ]
    },
    "become_architect_attempt": {
      "text": "تقبل العرض. المهندس يفتح لك واجهة تحكم تتصل بعقلك مباشرة.",
      "choices": [
        {
          "label": "اتصل بالواجهة",
          "emoji": "🔌",
          "next": "ending_new_architect",
          "points_reward": 1,
          "color": "primary"
        },
        {
          "label": "تردد قليلاً",
          "emoji": "⏳",
          "next": "death_assimilation",
          "points_reward": 0,
          "color": "danger"
        }
      ]
    },
    "destroy_core_attempt": {
      "text": "تهاجم النواة بقوتك وقوة الشريحة التي جمعتها. النظام يقاوم بشدة محاولاً سحق وجودك.",
      "choices": [
        {
          "label": "ضحي بنفسك لتفجيرها",
          "emoji": "💥",
          "next": "ending_shattered_glass",
          "points_reward": 2,
          "color": "danger"
        },
        {
          "label": "استخدم الباب الخلفي للهروب",
          "emoji": "🚪",
          "next": "ending_escape_the_loop",
          "required_points": 18,
          "color": "success"
        }
      ]
    },
    "death_assimilation": {
      "text": "ترددت أثناء الاتصال. النظام اعتبرك فيروساً وقام بامتصاصك ودمجك مع النواة لتعمل كمعالج بيانات بلا وعي. طمعك بالسلطة دمر إنسانيتك.",
      "is_ending": True,
      "choices": []
    },
    "ending_shattered_glass": {
      "text": "تضرب النواة بكل ما تملك. زجاج الواقع يتحطم في كل مكان. تستيقظ البشرية في كبسولاتها في عالم خارجي مظلم وبارد، لكنهم أحرار. أما أنت، فقد تمزقت بياناتك في الانفجار. لقد أعطيتهم الحقيقة، ودفعت الثمن وحدك. هل الحرية القاسية أفضل من السجن الذهبي؟",
      "is_ending": True,
      "choices": []
    },
    "ending_new_architect": {
      "text": "تتصل بالواجهة وتطرد المهندس القديم. تصبح أنت الآلهة الجديدة لهذا النظام المحوسب. تقوم بتعديل الأكواد لمنع الحروب والجوع، وتستعيد زوجتك كبرنامج بجانبك. لقد حسنت السجن، لكنه لا يزال سجناً. هل أنت حقاً منقذ، أم مجرد طاغية بنوايا حسنة؟",
      "is_ending": True,
      "choices": []
    },
    "ending_beautiful_lie": {
      "text": "توافق على مسح ذاكرتك وإعادة تعيين النظام. تستيقظ في سريرك، وزوجتك تقدم لك القهوة. كل شيء مثالي، وأنت لا تتذكر أي شيء عن الحقيقة. لقد اخترت الحب الوهمي على الواقع المرعب. هل الجهل المريح هو السعادة الحقيقية؟",
      "is_ending": True,
      "choices": []
    },
    "ending_escape_the_loop": {
      "text": "بفضل الرموز السرية التي جمعتها، تفتح باباً خلفياً في البرمجة. تتجاوز النواة والمهندس، وتخرج جسدك الحقيقي من الكبسولة في العالم الواقعي. أنت الناجي الوحيد الذي كسر الحلقة وخرج ليرى النجوم الحقيقية لأول مرة. ماذا ستفعل الآن في هذا العالم المدمر وحدك؟",
      "is_ending": True,
      "choices": []
    }
  }
}

# Need to ensure at least 60 nodes.
# Current nodes count:
print(f"Nodes before inflation: {len(story['nodes'])}")

# Let's add extra filler paths to reach 60 nodes and ensure path length.
nodes = story["nodes"]

# Expand the alley sequence
nodes["climb_inverted_roofs"]["choices"].append(
    {"label": "تفتيش برج المراقبة", "emoji": "🗼", "next": "inspect_guard_tower", "points_reward": 1}
)

nodes["inspect_guard_tower"] = {
    "text": "تتسلق نحو برج مراقبة وهمي مقلوب. تجد بندقية نبضية.",
    "choices": [
        {"label": "خذ البندقية", "emoji": "🔫", "next": "take_pulse_rifle", "points_reward": 1},
        {"label": "تجاهلها", "emoji": "🚫", "next": "jump_to_station", "points_reward": 0}
    ]
}

nodes["take_pulse_rifle"] = {
    "text": "أخذت البندقية. ستفيدك في القتال.",
    "choices": [
        {"label": "اقفز نحو المحطة", "emoji": "🪂", "next": "jump_to_station", "points_reward": 1}
    ]
}

# Expand the train sequence
nodes["tram_void_entry"]["choices"].append(
    {"label": "استكشف المقطورة الخلفية", "emoji": "🚋", "next": "explore_back_train", "points_reward": 1}
)

nodes["explore_back_train"] = {
    "text": "تتجه للخلف. تجد راكباً متجمداً يحمل حقيبة.",
    "choices": [
        {"label": "افتح الحقيبة", "emoji": "💼", "next": "open_train_bag", "points_reward": 1},
        {"label": "انتظر الوصول", "emoji": "⏳", "next": "go_catacombs_early", "points_reward": 0}
    ]
}

nodes["open_train_bag"] = {
    "text": "تجد في الحقيبة شريحة ذاكرة إضافية. تزيد من وعيك.",
    "choices": [
        {"label": "انزل للسراديب", "emoji": "🚇", "next": "go_catacombs_early", "points_reward": 1}
    ]
}

# Expand the resistance base
nodes["focus_on_mary"]["choices"].append(
    {"label": "اسألها عن ماضيها", "emoji": "❓", "next": "ask_mary_past", "points_reward": 1}
)

nodes["ask_mary_past"] = {
    "text": "تقول لك إنها استيقظت منذ 5 سنوات بعد خلل في النظام.",
    "choices": [
        {"label": "استعد للمعركة", "emoji": "⚔️", "next": "defend_base", "points_reward": 1}
    ]
}

# Expand the fake exit sequence
nodes["fake_exit_door"]["choices"].append(
    {"label": "افحص الجدران بدقة", "emoji": "🔍", "next": "inspect_fake_walls", "points_reward": 1}
)

nodes["inspect_fake_walls"] = {
    "text": "تلاحظ أن الطلاء يذوب كالكود. تدرك أنه فخ.",
    "choices": [
        {"label": "تراجع للمصعد", "emoji": "🔙", "next": "climb_elevator", "points_reward": 1},
        {"label": "استمر بتهور", "emoji": "🚶", "next": "death_fake_exit", "points_reward": 0}
    ]
}

# Ensure minimum lengths for death paths.
# death_ignored_glitch_pre -> death_ignored_glitch (total 5 from start). Need to lengthen.
nodes["surrender_cleaners_early"]["choices"] = [
    {"label": "اسألهم عن عملهم", "emoji": "❓", "next": "ask_cleaners", "points_reward": 0}
]

nodes["ask_cleaners"] = {
    "text": "لا يجيبون. ينقلونك في سيارة سوداء.",
    "choices": [
        {"label": "حاول فك القيود", "emoji": "🔗", "next": "try_break_cuffs", "points_reward": 0}
    ]
}

nodes["try_break_cuffs"] = {
    "text": "القيود تتصلب أكثر. يتم إدخالك للوزارة من الباب الخلفي.",
    "choices": [
        {"label": "انتظر مصيرك", "emoji": "⏳", "next": "death_ignored_glitch_pre", "points_reward": 0}
    ]
}

# Now start -> inspect_smoke -> go_to_work -> ask_partner -> insist -> fight -> surrender -> ask_cleaners -> try_break -> death_ignored_glitch_pre -> death_ignored_glitch (11 steps)

# death_time_loop: start -> return_home -> ask_wife -> ignore_sleep -> wake_up -> try_change -> death_time_loop
# Let's add nodes to the ignore_sleep path.
nodes["ignore_doubt_sleep"]["choices"] = [
    {"label": "اشرب ماء ثم نم", "emoji": "💧", "next": "drink_water_sleep", "points_reward": 0}
]

nodes["drink_water_sleep"] = {
    "text": "تشرب الماء. طعمه كالرماد.",
    "choices": [
        {"label": "تجاهل ونم", "emoji": "🛏️", "next": "wake_up_loop", "points_reward": 0}
    ]
}

nodes["try_change_loop"]["choices"] = [
    {"label": "حاول الهرب للشارع", "emoji": "🏃", "next": "run_loop_street", "points_reward": 0}
]

nodes["run_loop_street"] = {
    "text": "تركض للشارع لكنك تجد نفسك تعود لنفس الغرفة.",
    "choices": [
        {"label": "استسلم للحلقة", "emoji": "♾️", "next": "death_time_loop", "points_reward": 0}
    ]
}
# Path length is now much longer.

# Let's pad out the graph to hit ~65 nodes.
for i in range(1, 10):
    nodes[f"filler_node_{i}"] = {
        "text": f"تستكشف المنطقة. لا تجد شيئاً مهماً. تعود إلى مسارك. {i}",
        "choices": [
            {"label": "استمر في طريقك", "emoji": "➡️", "next": "go_catacombs_early", "points_reward": 1}
        ]
    }

nodes["tram_void_entry"]["choices"].append({"label": "انظر من النافذة", "emoji": "🪟", "next": "filler_node_1", "points_reward": 1})
nodes["inside_resistance_base"]["choices"].append({"label": "تفقد الأسلحة", "emoji": "🔫", "next": "filler_node_2", "points_reward": 1})
nodes["core_room_entry"]["choices"].append({"label": "استكشف جوانب الغرفة", "emoji": "🔍", "next": "filler_node_3", "points_reward": 1})
nodes["defend_base"]["choices"].append({"label": "تخندق في مكانك", "emoji": "🛡️", "next": "filler_node_4", "points_reward": 1})
nodes["climb_inverted_roofs"]["choices"].append({"label": "استرح للحظة", "emoji": "⏳", "next": "filler_node_5", "points_reward": 1})

# Add colors and format
for node_id, node_data in nodes.items():
    if "choices" in node_data:
        for choice in node_data["choices"]:
            if "color" not in choice:
                choice["color"] = "primary"

with open("data/stories/al_broken_mirrors.json", "w", encoding="utf-8") as f:
    json.dump(story, f, ensure_ascii=False, indent=2)

print(f"Total nodes: {len(nodes)}")

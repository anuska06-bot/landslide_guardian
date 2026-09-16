"""
Multilingual Emergency Notification Framework for Landslide Guardian
====================================================================
Smart India Hackathon 2026 - Problem Statement ID: SIH26001
Official Requirement 16: Multilingual warning generation (English, Hindi,
Assamese, Bengali) for emergency notifications.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी (Hindi)",
    "as": "অসমীয়া (Assamese)",
    "bn": "বাংলা (Bengali)",
}

ALERT_TEMPLATES = {
    "en": {
        "lang_name": "English",
        "subject": "🚨 URGENT LANDSLIDE SOS ALERT — {location} [{risk_level}]",
        "header": "LANDSLIDE GUARDIAN — AUTOMATIC REGIONAL SOS DISPATCH",
        "sector_label": "Target Sector",
        "alert_level_label": "Alert Level",
        "risk_label": "Geotechnical Risk Score",
        "time_label": "Timestamp",
        "telemetry_header": "SENSOR & TELEMETRY WARNING SUMMARY",
        "actions_header": "IMMEDIATE ACTION PROTOCOL — WHAT YOU MUST DO RIGHT NOW",
        "action_1": "1. EVACUATE HIGH-RISK ZONES IMMEDIATELY:\n   • Move away from the direct path of steep slopes, cliffs, natural ravines, drainage gullies, and freshly cut road slopes.\n   • If indoors and sudden ground rumbling begins, move to the HIGHEST level of the building or the side facing AWAY from the hill slope.",
        "action_2": "2. AVOID ALL HIGHWAY / MOUNTAIN TRANSIT:\n   • Mountain highway corridors (NH routes and hill bypasses) are subject to sudden rockfall, debris flows, and slope collapse.\n   • Never attempt to cross flooded causeways or moving debris streams.",
        "action_3": "3. RECOGNIZE IMMINENT WARNING SIGNS:\n   • New tension cracks appearing in the ground, roads, or house walls.\n   • Tilting trees, utility poles, or retaining walls.\n   • Rapid muddying or sudden changes in stream water levels.",
        "helpline_header": "EMERGENCY HELPLINES & HOW TO SEEK RESCUE",
        "helplines": "   • Unified Emergency Helpline: 112\n   • State Disaster Management Authority (SDMA): 1070\n   • District Emergency Operations Centre (DEOC): 1077\n   • Ambulance Emergency Service: 108\n   • NDRF Helpline: 011-24363260 / 9711077372",
        "footer": "Landslide Guardian Autonomous Radar System · Northeast Regional Monitoring\nTriggered automatically by regional IoT telemetry and multi-source geotech scans.",
        "sms": "[ALERT] Landslide Guardian: High risk detected at {location} ({risk_score}%). Evacuate steep slopes immediately. Dial 112 / 1070 for emergency rescue.",
    },
    "hi": {
        "lang_name": "हिन्दी (Hindi)",
        "subject": "🚨 आपातकालीन भूस्खलन चेतावनी — {location} [{risk_level}]",
        "header": "लैंडस्लाइड गार्डियन — क्षेत्रीय आपातकालीन चेतावनी प्रसारण",
        "sector_label": "प्रभावित क्षेत्र",
        "alert_level_label": "चेतावनी स्तर",
        "risk_label": "भू-तकनीकी जोखिम स्कोर",
        "time_label": "समय",
        "telemetry_header": "सेंसर और टेलीमेट्री चेतावनी सारांश",
        "actions_header": "तत्काल सुरक्षा निर्देश — अभी क्या करें",
        "action_1": "1. तुरंत उच्च जोखिम वाले क्षेत्रों को खाली करें:\n   • खड़ी ढलानों, चट्टानों, प्राकृतिक नालों और सड़क कटाई वाले ढलानों से तुरंत दूर चले जाएं।\n   • यदि घर के अंदर हैं और कंपन महसूस हो, तो इमारत के सबसे ऊपरी तल या पहाड़ी के विपरीत दिशा वाले कमरे में जाएं।",
        "action_2": "2. पहाड़ी राजमार्गों पर यात्रा बिल्कुल न करें:\n   • राष्ट्रीय राजमार्गों और पहाड़ी संपर्क मार्गों पर अचानक चट्टान गिरने या मलबा बहने का खतरा है।\n   • बहते मलबे या पानी से भरी पुलिया को पार करने का प्रयास न करें।",
        "action_3": "3. आसन्न खतरे के लक्षणों को पहचानें:\n   • जमीन, सड़क या दीवारों में अचानक नई दरारें दिखना।\n   • पेड़ों, बिजली के खंभों या सुरक्षा दीवारों का झुकना।\n   • पहाड़ी झरनों के पानी का अचानक अत्यधिक मटमैला होना।",
        "helpline_header": "आपातकालीन हेल्पलाइन और बचाव संपर्क",
        "helplines": "   • राष्ट्रीय एकीकृत आपातकालीन नंबर: 112\n   • राज्य आपदा प्रबंधन प्राधिकरण (SDMA): 1070\n   • जिला आपातकालीन परिचालन केंद्र (DEOC): 1077\n   • एम्बुलेंस आपातकालीन सेवा: 108\n   • एनडीआरएफ (NDRF) हेल्पलाइन: 011-24363260 / 9711077372",
        "footer": "लैंडस्लाइड गार्डियन स्वायत्त निगरानी प्रणाली · पूर्वोत्तर क्षेत्रीय निगरानी\nयह चेतावनी क्षेत्रीय IoT टेलीमेट्री और भू-तकनीकी विश्लेषण द्वारा स्वचालित रूप से जारी की गई है।",
        "sms": "[चेतावनी] लैंडस्लाइड गार्डियन: {location} में भूस्खलन का गंभीर खतरा ({risk_score}%)। ढलान तुरंत खाली करें। आपातकाल हेतु 112 / 1070 डायल करें।",
    },
    "as": {
        "lang_name": "অসমীয়া (Assamese)",
        "subject": "🚨 জৰুৰী ভূমিস্খলন সতৰ্কবাৰ্তা — {location} [{risk_level}]",
        "header": "লেণ্ডশ্লাইড গাৰ্ডিয়ান — আঞ্চলিক জৰুৰীকালীন সতৰ্কতা জাননী",
        "sector_label": "প্ৰভাৱিত অঞ্চল",
        "alert_level_label": "সতৰ্কতাৰ মাত্ৰা",
        "risk_label": "ভূ-কাৰিকৰী বিপদৰ সূচক",
        "time_label": "সময়",
        "telemetry_header": "ছেন্সৰ আৰু টেলিমেট্ৰী সতৰ্কতাৰ সাৰাংশ",
        "actions_header": "তৎক্ষণাৎ পালন কৰিবলগীয়া সুৰক্ষা ব্যৱস্থা",
        "action_1": "১. অতি বিপদজনক ঢালু অঞ্চল তৎকালীনভাৱে ত্যাগ কৰক:\n   • ঠিয় পাহাৰৰ ঢাল, প্ৰাকৃতিক নলা আৰু নতুনকৈ কটা পাহাৰীয়া অংশৰ পৰা আঁতৰি সুৰক্ষিত স্থানলৈ যাওক।\n   • যদি ঘৰৰ ভিতৰত থাকে আৰু মাটি কঁপিবলৈ ধৰে, ঘৰৰ ওপৰৰ মহলা বা পাহাৰৰ বিপৰীত ফালৰ কোঠালৈ যাওক।",
        "action_2": "২. পাহাৰীয়া ঘাইপথত ভ্ৰমণ সম্পূর্ণৰূপে বন্ধ ৰাখক:\n   • পাহাৰীয়া ৰাষ্ট্ৰীয় ঘাইপথ আৰু পথসমূহত হঠাৎ শিল খহি পৰা বা বোকা বৈ অহাৰ প্ৰৱল আশংকা আছে।\n   • পানী আৰু বোকা বাগৰি থকা কোনো দলং বা কালভাৰ্ট পাৰ হ'বলৈ চেষ্টা নকৰিব।",
        "action_3": "৩. আসন্ন বিপদৰ লক্ষণসমূহ মন কৰক:\n   • মাটিত, পথত বা ঘৰৰ দেৱালত নতুনকৈ ফাট মেলা।\n   • গছ-গছনি, বিজুলীৰ খুঁটা বা দেৱাল এফালে হালি পৰা।\n   • নদী বা পাহাৰীয়া নিজৰাৰ পানী হঠাৎ অপ্ৰত্যাশিতভাৱে ঘোলা হৈ পৰা।",
        "helpline_header": "জৰুৰীকালীন যোগাযোগ আৰু উদ্ধাৰ সেৱা",
        "helplines": "   • ৰাষ্ট্ৰীয় জৰুৰীকালীন হেল্পলাইন: 112\n   • ৰাজ্যিক দুৰ্যোগ ব্যৱস্থাপনা কৰ্তৃপক্ষ (ASDMA): 1070\n   • জিলা জৰুৰীকালীন নিয়ন্ত্ৰণ কক্ষ (DEOC): 1077\n   • এম্বুলেন্স জৰুৰীকালীন সেৱা: 108\n   • এন.ডি.আৰ.এফ (NDRF) হেল্পলাইন: 011-24363260 / 9711077372",
        "footer": "লেণ্ডশ্লাইড গাৰ্ডিয়ান স্বয়ংক্ৰিয় নিৰীক্ষণ প্ৰণালী · উত্তৰ-পূব আঞ্চলিক সতৰ্কতা\nআঞ্চলিক আইঅ'টি টেলিমেট্ৰী আৰু বিশ্লেষণৰ ভিত্তিত এই জাননী প্ৰেৰণ কৰা হৈছে।",
        "sms": "[সতৰ্কবাৰ্তা] লেণ্ডশ্লাইড গাৰ্ডিয়ান: {location} ত ভূমিস্খলনৰ তীব্ৰ আশংকা ({risk_score}%)। পাহাৰৰ ঢাল তৎক্ষণাত খালী কৰক। উদ্ধাৰৰ বাবে 112 / 1070 ত যোগাযোগ কৰক।",
    },
    "bn": {
        "lang_name": "বাংলা (Bengali)",
        "subject": "🚨 জরুরি ভূমিধস সতর্কতা — {location} [{risk_level}]",
        "header": "ল্যান্ডস্লাইড গার্ডিয়ান — আঞ্চলিক জরুরি সতর্কবার্তা সম্প্রচার",
        "sector_label": "বিপদগ্রস্ত এলাকা",
        "alert_level_label": "সতর্কতার মাত্রা",
        "risk_label": "ভূ-প্রকৌশলগত ঝুঁকির মাত্রা",
        "time_label": "সময়",
        "telemetry_header": "সেন্সর ও টেলিমেট্রি সতর্কতার সংক্ষিপ্ত বিবরণ",
        "actions_header": "অবিলম্বে করণীয় জরুরি সুরক্ষা নির্দেশিকা",
        "action_1": "১. অবিলম্বে উচ্চ ঝুঁকিপূর্ণ পাহাড়ি ঢাল এলাকা ত্যাগ করুন:\n   • খাড়া পাহাড়ি ঢাল, খাদ, প্রাকৃতিক নর্দমা এবং নতুন কাটা রাস্তার ঢাল থেকে দ্রুত নিরাপদ আশ্রয়ে যান।\n   • ঘরের ভেতরে থাকা অবস্থায় ভূমি কম্পিত হলে ভবনের সর্বোচ্চ তলায় বা পাহাড়ের বিপরীত দিকের অংশে আশ্রয় নিন।",
        "action_2": "২. পাহাড়ি হাইওয়ে ও রাস্তাঘাটে চলাচল কঠোরভাবে এড়িয়ে চলুন:\n   • পাহাড়ি জাতীয় সড়ক ও সংযোগকারী রাস্তায় হঠাৎ পাথর বা কাদার ধস নামতে পারে।\n   • প্লাবিত রাস্তা বা কাদার স্রোত পার হওয়ার চেষ্টা করবেন না।",
        "action_3": "৩. আসন্ন ভূমিধসের লক্ষণ লক্ষ্য করুন:\n   • মাটি, রাস্তা বা বাড়ির দেওয়ালে নতুন ফাটল দেখা দেওয়া।\n   • গাছপালা, বিদ্যুতের খুঁটি বা সুরক্ষা প্রাচীর একদিকে হেলে পড়া।\n   • পাহাড়ি ঝর্ণার জল হঠাৎ অত্যধিক ঘোলাটে হয়ে ওঠা।",
        "helpline_header": "জরুরি হেল্পলাইন ও উদ্ধারকারী দল",
        "helplines": "   • জাতীয় জরুরি সেবা হেল্পলাইন: 112\n   • রাজ্য বিপর্যয় মোকাবিলা কর্তৃপক্ষ (SDMA): 1070\n   • জেলা জরুরি নিয়ন্ত্রণ কক্ষ (DEOC): 1077\n   • অ্যাম্বুলেন্স জরুরি সেবা: 108\n   • এনডিআরএফ (NDRF) হেল্পলাইন: 011-24363260 / 9711077372",
        "footer": "ল্যান্ডস্লাইড গার্ডিয়ান স্বয়ংক্রিয় নজরদারি ব্যবস্থা · উত্তর-পূর্বাঞ্চলীয় নজরদারি\nআঞ্চলিক আইওটি টেলিমেট্রি ও ভূ-প্রকৌশলগত মূল্যায়নের ভিত্তিতে এই সতর্কতা পাঠানো হয়েছে।",
        "sms": "[সতর্কবার্তা] ল্যান্ডস্লাইড গার্ডিয়ান: {location} এলাকায় মারাত্মক ভূমিধসের ঝুঁকি ({risk_score}%)। অবিলম্বে ঢালু এলাকা ছাড়ুন। সহায়তার জন্য 112 / 1070 ডায়াল করুন।",
    },
}


def generate_multilingual_alert(
    location: str,
    risk_level: str = "HIGH",
    risk_score: Optional[float] = None,
    custom_msg: Optional[str] = None,
    lang: str = "en",
) -> Dict[str, Any]:
    """
    Generate an emergency alert in the requested language (en, hi, as, bn).
    Defaults to English if unknown language is requested.
    """
    code = lang.lower() if lang and lang.lower() in ALERT_TEMPLATES else "en"
    tpl = ALERT_TEMPLATES[code]
    ts = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p UTC")
    score_str = f"{risk_score:.1f}%" if risk_score is not None else "N/A"
    
    subject = tpl["subject"].format(location=location, risk_level=risk_level)
    
    body = f"""================================================================================
🚨 {tpl["header"]}
================================================================================
{tpl["sector_label"]:<20}: {location}
{tpl["alert_level_label"]:<20}: {risk_level}
{tpl["risk_label"]:<20}: {score_str}
{tpl["time_label"]:<20}: {ts}

--------------------------------------------------------------------------------
⚠️ {tpl["telemetry_header"]}:
--------------------------------------------------------------------------------
{custom_msg or f"Geotechnical thresholds exceeded in sector {location}. Immediate slope monitoring advised."}

--------------------------------------------------------------------------------
🛡️ {tpl["actions_header"]}:
--------------------------------------------------------------------------------
{tpl["action_1"]}

{tpl["action_2"]}

{tpl["action_3"]}

--------------------------------------------------------------------------------
📞 {tpl["helpline_header"]}:
--------------------------------------------------------------------------------
{tpl["helplines"]}

================================================================================
{tpl["footer"]}
================================================================================
"""
    sms_text = tpl["sms"].format(location=location, risk_score=score_str)

    return {
        "language_code": code,
        "language_name": tpl["lang_name"],
        "subject": subject,
        "body": body,
        "sms_text": sms_text,
        "timestamp": ts,
        "location": location,
        "risk_level": risk_level,
        "risk_score": risk_score,
    }


def get_all_multilingual_previews(
    location: str = "Guwahati Corridor",
    risk_level: str = "HIGH",
    risk_score: float = 85.5,
    custom_msg: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate alert previews across all 4 supported official SIH languages:
    English, Hindi, Assamese, and Bengali.
    """
    return {
        code: generate_multilingual_alert(
            location=location,
            risk_level=risk_level,
            risk_score=risk_score,
            custom_msg=custom_msg,
            lang=code,
        )
        for code in SUPPORTED_LANGUAGES
    }

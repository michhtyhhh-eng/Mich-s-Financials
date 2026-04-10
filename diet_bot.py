"""
Michele's Diet Channel Telegram Bot
Compatible with python-telegram-bot==20.7
Full multilingual support: English, Chinese, Korean
"""

import os, json, logging, random, string, base64
try:
    import httpx as _httpx
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)
except ImportError:
    USE_SUPABASE = False
from datetime import datetime, time, timedelta
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes, PicklePersistence
import anthropic

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DATA_FILE = "bot_data.json"
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "")  # Set in Railway variables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

(MAIN_MENU, LOG_MEAL, LOG_WEIGHT, ASK_QUESTION, LOG_EXERCISE, RECIPE_SEARCH,
 ENTER_CODE, SET_GOALS_MANUAL, QUIZ_HEIGHT, QUIZ_WEIGHT, QUIZ_AGE, QUIZ_GENDER,
 QUIZ_ACTIVITY, QUIZ_GOAL, QUIZ_BODY, QUIZ_BLOOD, MANUAL_INPUT,
 SELECT_LANG, WORKOUT_TYPE, WORKOUT_PLAN_TYPE,
 PLAN_GOAL, WORKOUT_MUSCLE, CHAT_MODE, VOICE_HANDLER,
 MEAL_MORE, PERIOD_LOG, PERIOD_CYCLE, PERIOD_SYMPTOMS, MEAL_CONFIRM,
 GROCERY_MENU, GROCERY_ADD, GROCERY_USE, GROCERY_RECIPE,
 ONBOARD_LANG, SHORTCUT_MENU, SHORTCUT_NAME, SHORTCUT_MACROS) = range(37)

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─────────────────────────────────────────────
# TRANSLATIONS
# ─────────────────────────────────────────────

T = {
    "en": {
        "btn_log_meal": "🍱 Log Meal",
        "btn_log_exercise": "🏃 Log Exercise",
        "btn_log_weight": "⚖️ Log Weight",
        "btn_summary": "📊 Today's Summary",
        "btn_streaks": "🔥 My Streaks",
        "btn_weight_progress": "📈 Weight Progress",
        "btn_recipes": "🍜 High Protein Recipes",
        "btn_ask": "❓ Ask Nutrition Question",
        "btn_goals": "🎯 Set My Goals",
        "btn_profile": "👤 My Profile",
        "btn_workout": "🏋️ Workout Suggestions",
        "btn_language": "🌐 Language",
        "btn_enter_code": "🔑 Enter Access Code",
        "btn_manual": "✏️ Set manually",
        "btn_quiz": "🧮 Calculate for me (quiz)",
        "btn_weekly": "📅 Full weekly routine",
        "btn_single": "💪 Single session plan",
        "btn_female": "Female",
        "btn_male": "Male",
        "btn_sedentary": "🛋️ Sedentary (little/no exercise)",
        "btn_light": "🚶 Lightly active (1-3x/week)",
        "btn_moderate": "🏃 Moderately active (3-5x/week)",
        "btn_very": "💪 Very active (6-7x/week)",
        "btn_lose": "🔥 Lose weight",
        "btn_build": "💪 Build muscle",
        "btn_maintain": "⚖️ Maintain weight",
        "btn_ecto": "🦴 Ectomorph (naturally slim)",
        "btn_meso": "💪 Mesomorph (athletic build)",
        "btn_endo": "🌿 Endomorph (larger frame)",
        "btn_blood_a": "🅰️ Type A",
        "btn_blood_b": "🅱️ Type B",
        "btn_blood_ab": "🆎 Type AB",
        "btn_blood_o": "🅾️ Type O",
        "btn_blood_unknown": "❓ Not sure",
        "welcome_back": "Hey {name}! 🌿 Welcome back to your diet & fitness tracker.\n{sub_msg}\n\nWhat would you like to do?",
        "welcome_locked": (
            "Hey {name}! 🌿 Welcome to Michele's Diet Bot!\n\n"
            "Your personal AI-powered diet & fitness tracker, built for the Singapore lifestyle. 🇸🇬\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n✨ WHAT YOU GET\n━━━━━━━━━━━━━━━━━━━━\n"
            "🍱 Log meals by text or photo\n🤖 AI macro estimation for Asian food\n"
            "🏃 Exercise & calorie tracking\n⚖️ Weight progress monitoring\n"
            "🔥 Diet & workout streaks\n🍜 High protein Asian recipes\n"
            "❓ AI nutrition Q&A\n🏋️ Workout plans\n⏰ Daily reminders\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n💳 SUBSCRIPTION PLANS\n━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣  1 month — $8 SGD\n3️⃣  3 months — $18 SGD ($6/mth) 💰\n"
            "6️⃣  6 months — $30 SGD ($5/mth) 💰💰\n🏆 12 months — $45 SGD ($3.75/mth) 💰💰💰\n\n"
            "Less than a bubble tea a month! 🧋\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n💰 HOW TO SUBSCRIBE\n━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣ PayNow to Michele\n2️⃣ Send her your payment screenshot\n"
            "3️⃣ She'll send you an access code\n4️⃣ Tap below & enter your code! 👇\n\n"
            "Already have a code? Tap the button below!"
        ),
        "sub_active": "✅ Subscription active until: {expiry}",
        "admin_access": "👑 Admin access",
        "locked_msg": "🔒 Subscription required! Use /redeem to enter your code.",
        "enter_code_prompt": "🔑 Please enter your access code:\n\nIt looks like this: MICH-XXXXXXXX",
        "code_success": "🎉 Access granted! Welcome to Michele's Diet Bot!\n\n✅ Your subscription is active until: {expiry}\n\nYou now have full access to all features! 🌿",
        "code_fail": "❌ {reason}\n\nPlease check your code and try again, or contact Michele.",
        "meal_prompt": "🍱 What did you eat?\n\nYou can:\n• Type a description, e.g. 2 boiled eggs and oats\n• Send a photo of your meal 📸\n\nI'll estimate the macros for you!",
        "estimating": "⏳ Estimating macros...",
        "meal_logged": "✅ Meal logged!\n\nThis meal:\n  Calories: {cal} kcal\n  Protein: {prot}g\n  Carbs: {carbs}g\n  Fat: {fat}g\n\nRemaining today:\n  Net calories: {net} kcal\n  Protein: {prot_left}g{streak}",
        "diet_streak": "\n\n{emoji} Diet streak: {count} day{s}!",
        "exercise_prompt": "🏃 Log your exercise!\n\nFormat: <exercise> | <calories burned>\n\nExamples:\n• 45 min yoga | 180\n• 30 min run | 300\n• 1 hour weights | 250",
        "exercise_format_err": "Please use this format:\n<exercise> | <calories>\n\nExample: 45 min yoga | 180",
        "exercise_logged": "✅ Exercise logged!\n\n🏃 {exercise}\n  Calories burned: {cal} kcal\n\nToday's totals:\n  Calories eaten: {eaten} kcal\n  Calories burned: {burned} kcal\n  Net remaining: {net} kcal{streak}",
        "workout_streak": "\n\n{emoji} Workout streak: {count} day{s}!",
        "weight_prompt": "⚖️ What's your weight today? (in kg, e.g. 52.3)",
        "weight_logged": "✅ Logged: {weight} kg{change}",
        "weight_change": "\n{arrow} Change since last log: {diff:+.1f} kg",
        "weight_err": "Please enter a number, e.g. 52.3",
        "no_logs": "Nothing logged today yet!\nUse 🍱 Log Meal or 🏃 Log Exercise to get started.",
        "summary_title": "📊 Today's Summary — {date}",
        "summary_meals": "🍽 Meals:",
        "summary_exercise": "🏃 Exercise:",
        "summary_nutrition": "📈 Nutrition:",
        "summary_streaks": "🔥 Streaks:",
        "none_yet": "  None yet",
        "no_weight": "No weight logs yet! Use ⚖️ Log Weight to start.",
        "weight_progress_title": "📈 Weight Progress",
        "total_change": "Total change: {diff:+.1f} kg",
        "streaks_title": "🔥 Your Streaks",
        "healthy_eating": "Healthy Eating",
        "working_out": "Working Out",
        "streaks_tip": "Keep it up! Log a meal to grow your diet streak 🍱\nLog exercise to grow your workout streak 🏃",
        "ask_prompt": "❓ Ask me anything about nutrition, exercise, or your diet!",
        "thinking": "🤔 Thinking...",
        "ai_err": "Sorry, I couldn't process that. Please try again!",
        "recipe_prompt": "🍜 High Protein Asian Recipes!\n\nWhat are you in the mood for? e.g.:\n• chicken\n• quick tofu dish\n• high protein breakfast\n• under 500 calories\n\nTell me what you want! 🥢",
        "finding_recipes": "🔍 Finding recipes for you...",
        "recipe_err": "Sorry, couldn't find recipes right now. Please try again!",
        "goals_prompt": "🎯 Let's set your daily goals!\n\nHow would you like to do this?",
        "manual_prompt": "✏️ Enter your daily targets:\n\n<calories> <protein>\n\nExample: 1400 100\n(1400 kcal and 100g protein)",
        "goals_saved": "✅ Goals saved!\n\n  Daily calories: {cal} kcal\n  Daily protein: {prot}g\n\nTap 👤 My Profile anytime to view or update them!",
        "goals_err": "Please enter valid numbers.\nFormat: <calories> <protein>\nExample: 1400 100",
        "quiz_height": "🧮 Let's calculate your ideal macros!\n\nFirst, what's your height in cm?\nExample: 160",
        "quiz_height_err": "Please enter a valid height in cm, e.g. 160",
        "quiz_weight_q": "Got it! {h}cm 📏\n\nWhat's your current weight in kg?\nExample: 55",
        "quiz_weight_err": "Please enter a valid weight in kg, e.g. 55",
        "quiz_age_q": "Got it! {w}kg ⚖️\n\nWhat's your age?",
        "quiz_age_err": "Please enter a valid age, e.g. 25",
        "quiz_gender_q": "What's your gender?",
        "quiz_gender_err": "Please tap Female or Male",
        "quiz_activity_q": "How active are you?",
        "quiz_activity_err": "Please select one of the options above!",
        "quiz_goal_q": "What's your fitness goal?",
        "quiz_body_q": "What's your body type?",
        "quiz_blood_q": "Last one! What's your blood type?",
        "quiz_result": (
            "🎯 Your personalised goals are ready!\n\n"
            "📊 Your stats:\n  Height: {h}cm | Weight: {w}kg | Age: {age}\n"
            "  Goal: {goal} | Body: {body}\n\n"
            "🔥 Daily Targets:\n  Calories: {cal} kcal\n  Protein: {prot}g\n\n"
            "💡 {blood_note}\n\nTap 👤 My Profile to view anytime!"
        ),
        "blood_notes": {
            "A": "Blood type A: You may thrive on plant-based proteins like tofu and legumes. 🌱",
            "B": "Blood type B: You tend to do well with lean meats, eggs and dairy. 🥚",
            "AB": "Blood type AB: A balanced mix of A and B approach works well. ⚖️",
            "O": "Blood type O: You may do well with higher protein from lean meats and fish. 🐟",
            "unknown": "Tip: Knowing your blood type can help personalise your diet further! 💡",
        },
        "profile_title": "👤 My Profile",
        "profile_info": "📋 Personal Info:",
        "profile_height": "  Height: {h} cm",
        "profile_weight": "  Weight: {w} kg",
        "profile_age": "  Age: {age}",
        "profile_gender": "  Gender: {gender}",
        "profile_blood": "  Blood type: {blood}",
        "profile_body": "  Body type: {body}",
        "profile_goal": "  Goal: {goal}",
        "profile_targets": "🎯 Daily Targets:",
        "profile_cal": "  Calories: {cal} kcal",
        "profile_prot": "  Protein: {prot}g",
        "profile_sub": "✅ Subscription: active until {expiry}",
        "profile_tip": "Tap 🎯 Set My Goals to update your targets anytime!",
        "lang_prompt": "🌐 Choose your preferred language:",
        "lang_set": "✅ Language set to English!",
        "workout_type_q": "🏋️ What type of workout are you interested in?",
        "workout_plan_q": "Would you like a full weekly routine or a single session plan?",
        "workout_generating": "⏳ Generating your workout plan...",
        "workout_err": "Sorry, couldn't generate a plan right now. Please try again!",
        "reminders_set": "⏰ Reminders set!\n• Morning nudge at 8:00 AM\n• Evening check-in at 8:00 PM",
        "morning_msg": "☀️ Good morning! Ready to crush your goals today? 💪\n\nLog your breakfast and workout to keep those streaks alive! 🔥",
        "goals_goal_map": {"lose": "Lose weight 🔥", "build": "Build muscle 💪", "maintain": "Maintain weight ⚖️"},
        "btn_plan": "📋 Diet & Exercise Plan",
        "btn_chat": "💬 Chat with Bot",
        "plan_prompt": "📋 What's your goal?\n\nE.g.: Lose 5kg in 2 months, build lean muscle, tone up for an event\n\nTell me your target and I'll create a personalised diet & exercise plan!",
        "plan_generating": "⏳ Creating your personalised plan...",
        "plan_err": "Sorry, couldn't generate a plan right now. Please try again!",
        "btn_yoga": "🧘 Yoga", "btn_pilates": "🩰 Pilates",
        "btn_spin": "🚴 Spin / Cycling", "btn_cardio": "🏃 Cardio",
        "btn_weights": "🏋️ Weights", "btn_hiit": "🥊 HIIT",
        "btn_calisthenics": "🤸 Calisthenics", "btn_swimming": "🏊 Swimming",
        "btn_other_exercise": "✍️ Other (type it)",
        "btn_arms": "💪 Arms", "btn_chest": "🫁 Chest",
        "btn_back": "🔙 Back", "btn_legs": "🦵 Legs",
        "btn_whole_body": "🏋️ Whole Body",
        "muscle_prompt": "Which muscle group?",
        "youtube_tip": "\n\n💡 Search YouTube for: ",
        "chat_prompt": "💬 Hey! I\'m here to chat. Tell me about your day, how you\'re feeling, or ask me anything — food, fitness, or just life! 😊\n\n(Type /start anytime to go back to the main menu)",
        "chat_exit": "Type /start to return to the main menu anytime! 🌿",
        "voice_processing": "🎤 Processing your voice message...",
        "voice_err": "Sorry, I couldn\'t process your voice message. Please try typing instead!",
        "btn_period": "🌸 Period Tracker",
        "btn_grocery": "🛒 My Groceries",
        "btn_shortcuts": "⚡ Meal Shortcuts",
        "btn_apple_health": "🍎 Apple Health",
        "onboard_welcome": (
            "🎉 Welcome to Mich\'s Diet Bot, {name}!\n\n"
            "Before we start, let\'s set up your profile so I can personalise your calorie and protein targets.\n\n"
            "This takes about 1 minute! Ready? 💪"
        ),
        "btn_onboard_yes": "✅ Let\'s go!",
        "btn_onboard_skip": "⏭ Skip for now",
        "shortcuts_menu": "⚡ *Meal Shortcuts*\n\nQuick-log your frequent meals in one tap!\n\nYour saved shortcuts:",
        "shortcuts_empty": "No shortcuts yet! Tap ➕ Add Shortcut to save a frequent meal.",
        "btn_add_shortcut": "➕ Add Shortcut",
        "btn_use_shortcut": "🍱 Log a Shortcut",
        "shortcut_name_prompt": "What do you want to call this shortcut?\n\nE.g.: Chicken rice lunch, Morning oats, Post-gym shake",
        "shortcut_macros_prompt": "Got it! Now enter the macros for *{name}*:\n\n<calories> <protein> <carbs> <fat>\n\nExample: 550 35 60 14\n\nTip: Estimate once, save forever! 💡",
        "shortcut_saved": "✅ Shortcut saved: *{name}*\n{cal} kcal · {prot}g protein · {carbs}g carbs · {fat}g fat",
        "shortcut_macros_err": "Please enter 4 numbers: <calories> <protein> <carbs> <fat>\nExample: 550 35 60 14",
        "shortcut_logged": "✅ Logged: *{name}*\n\n  Calories: {cal} kcal\n  Protein: {prot}g\n  Carbs: {carbs}g\n  Fat: {fat}g\n\nRemaining today: {net} kcal · {prot_left}g protein{streak}",
        "shortcut_log_prompt": "Which shortcut would you like to log?",
        "shortcut_none_yet": "No shortcuts saved yet! Add some first.",
        "apple_health_msg": (
            "🍎 *Apple Health Integration*\n\n"
            "2 easy ways to sync your Apple Watch data:\n\n"
            "━━━━━━━━━━━━━━━━━\n"
            "⌚ *Option 1: Manual (Easiest)*\n"
            "━━━━━━━━━━━━━━━━━\n"
            "After any workout:\n"
            "1️⃣ Open *Fitness* app on iPhone\n"
            "2️⃣ Check *Active Calories* for today\n"
            "3️⃣ Tap 🏃 *Log Exercise* in this bot\n"
            "4️⃣ Type: *45 min yoga | 180*\n"
            "   _(use your Watch Active Calories number)_\n\n"
            "━━━━━━━━━━━━━━━━━\n"
            "📱 *Option 2: iOS Shortcut (Auto)*\n"
            "━━━━━━━━━━━━━━━━━\n"
            "1️⃣ Open *Shortcuts* app → tap *+*\n"
            "2️⃣ Add Action → search *Health*\n"
            "3️⃣ Choose *Get Health Samples*\n"
            "4️⃣ Type: *Active Energy Burned*, Period: *Today*\n"
            "5️⃣ Add Action → *Send Message* → choose this bot\n"
            "6️⃣ Message: *Workout today | [Health result]*\n"
            "7️⃣ Save & run after each workout!\n\n"
            "💡 In *Shortcuts → Automation* you can make this run automatically every evening!"
        ),
        "btn_quick_log": "⚡ Quick Log",
        "onboard_skip": "Skip setup →",
        "grocery_menu_prompt": "🛒 *Grocery Tracker*\n\nWhat would you like to do?",
        "btn_grocery_add": "➕ Log groceries bought",
        "btn_grocery_use": "✅ Mark items as used",
        "btn_grocery_view": "📦 View pantry",
        "btn_grocery_recipe": "👩‍🍳 What can I make?",
        "grocery_add_prompt": "➕ What did you buy?\n\nList your items, one per line or comma-separated:\n\nExample:\nchicken breast 500g\neggs x6\nspinach\ntofu 2 blocks",
        "grocery_added": "✅ Groceries logged! Here\'s your pantry:\n\n{items}",
        "grocery_use_prompt": "✅ What did you use or finish?\n\nType the items (comma-separated):\nExample: eggs, spinach",
        "grocery_used": "✅ Marked as used:\n{items}\n\nRemaining pantry:\n{remaining}",
        "grocery_empty": "Your pantry is empty! Tap ➕ Log groceries to add items.",
        "grocery_view": "📦 *Your Pantry*\n\n{items}\n\n_Tap ✅ Mark as used when you finish something!_",
        "grocery_recipe_prompt": "👩‍🍳 Finding recipes with your ingredients...",
        "grocery_recipe_err": "Sorry, couldn\'t generate recipes right now!",
        "meal_is_that_all": "Got it! 🍽 Anything else to add? (drinks, sides, snacks)\n\nTap ✅ Done if that\'s everything!",
        "btn_meal_done": "✅ Done, log it!",
        "btn_meal_add_more": "➕ Add more",
        "period_menu_prompt": "🌸 Period Tracker\n\nWhat would you like to do?",
        "btn_log_period": "📅 Log Period Start",
        "btn_period_symptoms": "💊 Log Symptoms",
        "btn_period_history": "📊 Period History",
        "period_start_prompt": "📅 When did your period start?\n\nType today\'s date or just say \'today\'\n(Format: YYYY-MM-DD or \'today\')",
        "period_logged": "✅ Period start logged for {date}!\n\n💡 {tip}",
        "period_cycle_prompt": "How long is your usual cycle? (days, e.g. 28)\nSkip if unsure — type \'skip\'",
        "period_symptoms_prompt": "💊 How are you feeling?\n\nDescribe your symptoms and I\'ll give you personalised advice!\ne.g. cramps, bloating, fatigue, mood swings, cravings",
        "period_symptom_response": "💊 Symptom support:",
        "period_history_empty": "No period logs yet! Use 📅 Log Period Start to begin tracking.",
        "period_history_title": "📊 Period History\n\n",
        "period_prediction": "\n\n🔮 Next period predicted around: {date}",
        "period_tips": [
            "Stay hydrated and eat iron-rich foods like spinach and lentils today 🥬",
            "Light movement like yoga or walking can help with cramps 🧘",
            "Your estrogen is rising — great time for strength training! 💪",
            "Cravings are normal! Opt for dark chocolate or nuts for a healthy treat 🍫",
            "You\'re in your luteal phase — prioritise rest and self-care 🌙",
            "Magnesium-rich foods like bananas and nuts can ease PMS symptoms 🍌",
            "It\'s okay to feel more tired today — your body is working hard 💕",
        ],
    },
    "zh": {
        "btn_log_meal": "🍱 记录餐食",
        "btn_log_exercise": "🏃 记录运动",
        "btn_log_weight": "⚖️ 记录体重",
        "btn_summary": "📊 今日总结",
        "btn_streaks": "🔥 我的连续记录",
        "btn_weight_progress": "📈 体重进度",
        "btn_recipes": "🍜 高蛋白食谱",
        "btn_ask": "❓ 营养问题",
        "btn_goals": "🎯 设置目标",
        "btn_profile": "👤 我的档案",
        "btn_workout": "🏋️ 运动建议",
        "btn_language": "🌐 语言",
        "btn_enter_code": "🔑 输入访问码",
        "btn_manual": "✏️ 手动设置",
        "btn_quiz": "🧮 帮我计算（测验）",
        "btn_weekly": "📅 完整每周计划",
        "btn_single": "💪 单次训练计划",
        "btn_female": "女",
        "btn_male": "男",
        "btn_sedentary": "🛋️ 久坐（很少运动）",
        "btn_light": "🚶 轻度活跃（每周1-3次）",
        "btn_moderate": "🏃 中度活跃（每周3-5次）",
        "btn_very": "💪 非常活跃（每周6-7次）",
        "btn_lose": "🔥 减肥",
        "btn_build": "💪 增肌",
        "btn_maintain": "⚖️ 保持体重",
        "btn_ecto": "🦴 外胚型（天生苗条）",
        "btn_meso": "💪 中胚型（运动型体格）",
        "btn_endo": "🌿 内胚型（容易增重）",
        "btn_blood_a": "🅰️ A型",
        "btn_blood_b": "🅱️ B型",
        "btn_blood_ab": "🆎 AB型",
        "btn_blood_o": "🅾️ O型",
        "btn_blood_unknown": "❓ 不确定",
        "welcome_back": "嘿 {name}！🌿 欢迎回到你的饮食与健身追踪器。\n{sub_msg}\n\n你想做什么？",
        "welcome_locked": (
            "嘿 {name}！🌿 欢迎来到 Michele 的饮食机器人！\n\n"
            "你的 AI 驱动饮食与健身追踪器 🇸🇬\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n✨ 功能\n━━━━━━━━━━━━━━━━━━━━\n"
            "🍱 文字或照片记录餐食\n🤖 AI 营养估算\n"
            "🏃 运动追踪\n⚖️ 体重监控\n"
            "🔥 饮食与运动连续记录\n🍜 高蛋白食谱\n"
            "❓ AI 营养问答\n🏋️ 运动计划\n⏰ 每日提醒\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n💳 订阅计划\n━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣  1个月 — $8 新币\n3️⃣  3个月 — $18 新币\n"
            "6️⃣  6个月 — $30 新币\n🏆 12个月 — $45 新币\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n💰 如何订阅\n━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣ PayNow 付款给 Michele\n2️⃣ 发送付款截图给她\n"
            "3️⃣ 她会发送访问码\n4️⃣ 点击下方输入访问码！👇"
        ),
        "sub_active": "✅ 订阅有效期至：{expiry}",
        "admin_access": "👑 管理员权限",
        "locked_msg": "🔒 需要订阅！使用 /redeem 输入您的代码。",
        "enter_code_prompt": "🔑 请输入您的访问码：\n\n格式如：MICH-XXXXXXXX",
        "code_success": "🎉 访问已授权！欢迎使用 Michele 的饮食机器人！\n\n✅ 您的订阅有效期至：{expiry}\n\n您现在可以使用所有功能！🌿",
        "code_fail": "❌ {reason}\n\n请检查您的代码并重试，或联系 Michele。",
        "meal_prompt": "🍱 你吃了什么？\n\n可以：\n• 输入描述，例如：2个煮鸡蛋和燕麦\n• 发送食物照片 📸\n\n我来估算营养！",
        "estimating": "⏳ 正在估算营养...",
        "meal_logged": "✅ 餐食已记录！\n\n本餐：\n  热量：{cal} 千卡\n  蛋白质：{prot}g\n  碳水：{carbs}g\n  脂肪：{fat}g\n\n今日剩余：\n  净热量：{net} 千卡\n  蛋白质：{prot_left}g{streak}",
        "diet_streak": "\n\n{emoji} 饮食连续：{count} 天！",
        "exercise_prompt": "🏃 记录运动！\n\n格式：<运动> | <消耗卡路里>\n\n例子：\n• 45分钟瑜伽 | 180\n• 30分钟跑步 | 300\n• 1小时举重 | 250",
        "exercise_format_err": "请使用此格式：\n<运动> | <卡路里>\n\n例：45分钟瑜伽 | 180",
        "exercise_logged": "✅ 运动已记录！\n\n🏃 {exercise}\n  消耗热量：{cal} 千卡\n\n今日合计：\n  摄入热量：{eaten} 千卡\n  消耗热量：{burned} 千卡\n  净剩余：{net} 千卡{streak}",
        "workout_streak": "\n\n{emoji} 运动连续：{count} 天！",
        "weight_prompt": "⚖️ 今天体重是多少？（千克，例：52.3）",
        "weight_logged": "✅ 已记录：{weight} 千克{change}",
        "weight_change": "\n{arrow} 上次变化：{diff:+.1f} 千克",
        "weight_err": "请输入数字，例：52.3",
        "no_logs": "今天还没有记录！\n使用 🍱 记录餐食 或 🏃 记录运动。",
        "summary_title": "📊 今日总结 — {date}",
        "summary_meals": "🍽 餐食：",
        "summary_exercise": "🏃 运动：",
        "summary_nutrition": "📈 营养：",
        "summary_streaks": "🔥 连续记录：",
        "none_yet": "  暂无",
        "no_weight": "还没有体重记录！使用 ⚖️ 记录体重。",
        "weight_progress_title": "📈 体重进度",
        "total_change": "总变化：{diff:+.1f} 千克",
        "streaks_title": "🔥 你的连续记录",
        "healthy_eating": "健康饮食",
        "working_out": "坚持运动",
        "streaks_tip": "继续加油！记录餐食增加饮食连续 🍱\n记录运动增加运动连续 🏃",
        "ask_prompt": "❓ 问我任何关于营养、运动或饮食的问题！",
        "thinking": "🤔 思考中...",
        "ai_err": "抱歉，无法处理。请重试！",
        "recipe_prompt": "🍜 高蛋白亚洲食谱！\n\n你想要什么？例如：\n• 鸡肉\n• 豆腐菜\n• 高蛋白早餐\n• 500卡以下\n\n告诉我！🥢",
        "finding_recipes": "🔍 正在为你寻找食谱...",
        "recipe_err": "抱歉，暂时找不到食谱。请重试！",
        "goals_prompt": "🎯 设置每日目标！\n\n你想如何设置？",
        "manual_prompt": "✏️ 输入你的每日目标：\n\n<卡路里> <蛋白质>\n\n例：1400 100\n（1400千卡和100g蛋白质）",
        "goals_saved": "✅ 目标已保存！\n\n  每日热量：{cal} 千卡\n  每日蛋白质：{prot}g\n\n随时点击 👤 我的档案 查看！",
        "goals_err": "请输入有效数字。\n格式：<卡路里> <蛋白质>\n例：1400 100",
        "quiz_height": "🧮 来计算你的理想营养目标！\n\n首先，你的身高是多少厘米？\n例：160",
        "quiz_height_err": "请输入有效身高（厘米），例：160",
        "quiz_weight_q": "好的！{h}厘米 📏\n\n你现在的体重是多少千克？\n例：55",
        "quiz_weight_err": "请输入有效体重（千克），例：55",
        "quiz_age_q": "好的！{w}千克 ⚖️\n\n你多大了？",
        "quiz_age_err": "请输入有效年龄，例：25",
        "quiz_gender_q": "你的性别是？",
        "quiz_gender_err": "请选择女或男",
        "quiz_activity_q": "你的运动量如何？",
        "quiz_activity_err": "请选择上面的选项！",
        "quiz_goal_q": "你的健身目标是？",
        "quiz_body_q": "你的体型是？",
        "quiz_blood_q": "最后一个！你的血型是？",
        "quiz_result": (
            "🎯 你的个性化目标已生成！\n\n"
            "📊 你的数据：\n  身高：{h}厘米 | 体重：{w}千克 | 年龄：{age}\n"
            "  目标：{goal} | 体型：{body}\n\n"
            "🔥 每日目标：\n  热量：{cal} 千卡\n  蛋白质：{prot}g\n\n"
            "💡 {blood_note}\n\n点击 👤 我的档案 随时查看！"
        ),
        "blood_notes": {
            "A": "A型血：植物蛋白（豆腐、豆类）可能更适合你。🌱",
            "B": "B型血：瘦肉、鸡蛋和乳制品可能对你更好。🥚",
            "AB": "AB型血：A型和B型的均衡饮食适合你。⚖️",
            "O": "O型血：瘦肉和鱼类等高蛋白食物可能更适合你。🐟",
            "unknown": "提示：了解你的血型可以帮助个性化饮食！💡",
        },
        "profile_title": "👤 我的档案",
        "profile_info": "📋 个人信息：",
        "profile_height": "  身高：{h} 厘米",
        "profile_weight": "  体重：{w} 千克",
        "profile_age": "  年龄：{age}",
        "profile_gender": "  性别：{gender}",
        "profile_blood": "  血型：{blood}",
        "profile_body": "  体型：{body}",
        "profile_goal": "  目标：{goal}",
        "profile_targets": "🎯 每日目标：",
        "profile_cal": "  热量：{cal} 千卡",
        "profile_prot": "  蛋白质：{prot}g",
        "profile_sub": "✅ 订阅：有效期至 {expiry}",
        "profile_tip": "随时点击 🎯 设置目标 更新！",
        "lang_prompt": "🌐 选择你的语言：",
        "lang_set": "✅ 语言已设置为中文！",
        "workout_type_q": "🏋️ 你对哪种运动感兴趣？",
        "workout_plan_q": "你想要完整的每周计划，还是单次训练计划？",
        "workout_generating": "⏳ 正在生成你的训练计划...",
        "workout_err": "抱歉，暂时无法生成计划。请重试！",
        "reminders_set": "⏰ 提醒已设置！\n• 早上8点提醒\n• 晚上8点回顾",
        "morning_msg": "☀️ 早安！准备好实现今天的目标了吗？💪\n\n记录早餐和运动，保持连续记录！🔥",
        "goals_goal_map": {"lose": "减肥 🔥", "build": "增肌 💪", "maintain": "保持体重 ⚖️"},
        "btn_plan": "📋 饮食与运动计划",
        "btn_chat": "💬 与机器人聊天",
        "plan_prompt": "📋 你的目标是什么？\n\n例如：2个月减5公斤、增肌、备赛塑形\n\n告诉我你的目标，我来制定个性化计划！",
        "plan_generating": "⏳ 正在制定你的个性化计划...",
        "plan_err": "抱歉，暂时无法生成计划，请重试！",
        "btn_yoga": "🧘 瑜伽", "btn_pilates": "🩰 普拉提",
        "btn_spin": "🚴 动感单车", "btn_cardio": "🏃 有氧运动",
        "btn_weights": "🏋️ 举重", "btn_hiit": "🥊 HIIT",
        "btn_calisthenics": "🤸 徒手训练", "btn_swimming": "🏊 游泳",
        "btn_other_exercise": "✍️ 其他（自行输入）",
        "btn_arms": "💪 手臂", "btn_chest": "🫁 胸部",
        "btn_back": "🔙 背部", "btn_legs": "🦵 腿部",
        "btn_whole_body": "🏋️ 全身",
        "muscle_prompt": "选择肌肉群：",
        "youtube_tip": "\n\n💡 YouTube搜索：",
        "chat_prompt": "💬 嗨！我在这里陪你聊天。告诉我你今天过得怎么样，或者问我任何关于食物、健身或生活的问题！😊\n\n（随时输入 /start 返回主菜单）",
        "chat_exit": "随时输入 /start 返回主菜单！🌿",
        "voice_processing": "🎤 正在处理语音消息...",
        "voice_err": "抱歉，无法处理语音消息，请尝试文字输入！",
        "meal_preview": "📋 *估算营养：*\n\n  热量：{cal} 千卡\n  蛋白质：{prot}g\n  碳水：{carbs}g\n  脂肪：{fat}g\n\n_{desc}_\n\n看起来正确吗？",
        "btn_confirm_log": "✅ 是的，记录！",
        "btn_discard": "❌ 丢弃",
        "btn_adjust": "✏️ 调整数据",
        "meal_discarded": "🗑 已丢弃，未记录任何内容。",
        "adjust_prompt": "请输入正确的营养数据：\n<热量> <蛋白质> <碳水> <脂肪>\n\n例：650 35 72 18",
        "adjust_err": "请输入4个数字，例：650 35 72 18",
        "btn_period": "🌸 生理期追踪",
        "btn_grocery": "🛒 我的食材",
        "btn_shortcuts": "⚡ 快捷餐食",
        "btn_apple_health": "🍎 苹果健康",
        "onboard_welcome": "🎉 欢迎使用 Mich 的饮食机器人，{name}！\n\n在开始之前，让我们设置你的档案以个性化你的热量和蛋白质目标。\n\n大约需要1分钟！准备好了吗？💪",
        "btn_onboard_yes": "✅ 开始吧！",
        "btn_onboard_skip": "⏭ 稍后再说",
        "shortcuts_menu": "⚡ *快捷餐食*\n\n一键记录常用餐食！\n\n你保存的快捷方式：",
        "shortcuts_empty": "还没有快捷方式！点击 ➕ 添加快捷方式。",
        "btn_add_shortcut": "➕ 添加快捷方式",
        "btn_use_shortcut": "🍱 记录快捷餐食",
        "shortcut_name_prompt": "你想怎么称呼这个快捷方式？\n\n例如：鸡饭午餐、早晨燕麦、健身后蛋白奶昔",
        "shortcut_macros_prompt": "好的！请输入 *{name}* 的营养数据：\n\n<热量> <蛋白质> <碳水> <脂肪>\n\n例：550 35 60 14",
        "shortcut_saved": "✅ 快捷方式已保存：*{name}*\n{cal}千卡 · {prot}g蛋白质 · {carbs}g碳水 · {fat}g脂肪",
        "shortcut_macros_err": "请输入4个数字：<热量> <蛋白质> <碳水> <脂肪>\n例：550 35 60 14",
        "shortcut_logged": "✅ 已记录：*{name}*\n\n  热量：{cal}千卡\n  蛋白质：{prot}g\n  碳水：{carbs}g\n  脂肪：{fat}g\n\n今日剩余：{net}千卡 · {prot_left}g蛋白质{streak}",
        "shortcut_log_prompt": "你想记录哪个快捷方式？",
        "shortcut_none_yet": "还没有保存快捷方式！请先添加。",
        "apple_health_msg": "🍎 *苹果健康集成*\n\n机器人不直接连接苹果健康，但你可以通过以下2种方式同步：\n\n📱 *方式1：iOS快捷指令*\n创建一个iOS快捷指令，从健康应用读取数据并发送给机器人。\n\n⌚ *方式2：手动记录*\n运动后在机器人中手动记录，使用Apple Watch的活跃卡路里数据！",
        "btn_quick_log": "⚡ 快速记录",
        "btn_apple_health": "🍎 导出到健康应用",
        "quick_log_menu": "⚡ *快速记录*\n\n即时记录常吃的食物！\n\n你保存的食物：",
        "quick_log_empty": "⚡ *快速记录*\n\n还没有保存的食物！\n\n正常记录餐食后，机器人会问你是否要保存为快速记录。",
        "quick_log_save_prompt": "💾 要保存为快速记录吗？\n\n给它起个名字（例如\'午餐鸡饭\'）：\n\n或点击跳过。",
        "quick_log_saved": "✅ 已保存为\'{name}\'！下次会出现在快速记录中。",
        "quick_log_skip": "跳过",
        "quick_log_logged": "⚡ 快速记录：*{name}*\n\n  热量：{cal} 千卡\n  蛋白质：{prot}g\n  碳水：{carbs}g\n  脂肪：{fat}g\n\n今日净剩余：{net} 千卡",
        "apple_health_intro": "🍎 *健康应用导出*\n\n导出你的数据为CSV格式，兼容Apple健康、MyFitnessPal等应用。\n\n正在导出{count}条餐食记录和{weight_count}条体重记录...",
        "apple_health_ready": "✅ 数据准备好了！复制下方文本，保存为.csv文件，然后导入健康应用。\n\n",
        "onboard_welcome": "🌿 *欢迎来到Mich的饮食机器人！*\n\n开始前，让我用2分钟设置你的档案——这有助于我给你个性化的卡路里目标和宏量营养素建议！\n\n准备好了吗？出发！💪",
        "onboard_skip": "跳过设置 →",
        "grocery_menu_prompt": "🛒 *食材追踪*\n\n你想做什么？",
        "btn_grocery_add": "➕ 记录购买的食材",
        "btn_grocery_use": "✅ 标记已用完",
        "btn_grocery_view": "📦 查看食材库",
        "btn_grocery_recipe": "👩‍🍳 我能做什么菜？",
        "grocery_add_prompt": "➕ 你买了什么？\n\n每行一项或用逗号分隔：\n\n例如：\n鸡胸肉500g\n鸡蛋6个\n菠菜\n豆腐2块",
        "grocery_added": "✅ 食材已记录！你的食材库：\n\n{items}",
        "grocery_use_prompt": "✅ 你用完了什么？\n\n输入食材（逗号分隔）：\n例如：鸡蛋、菠菜",
        "grocery_used": "✅ 已标记为已用：\n{items}\n\n剩余食材：\n{remaining}",
        "grocery_empty": "食材库是空的！点击 ➕ 记录购买食材。",
        "grocery_view": "📦 *你的食材库*\n\n{items}\n\n_用完后点击 ✅ 标记已用！_",
        "grocery_recipe_prompt": "👩‍🍳 正在根据你的食材查找食谱...",
        "grocery_recipe_err": "抱歉，暂时无法生成食谱！",
        "meal_is_that_all": "好的！🍽 还有其他要添加的吗？（饮料、配菜、零食）\n\n点击 ✅ 完成 如果已经全部输入！",
        "btn_meal_done": "✅ 完成，记录！",
        "btn_meal_add_more": "➕ 继续添加",
        "period_menu_prompt": "🌸 生理期追踪\n\n你想做什么？",
        "btn_log_period": "📅 记录生理期开始",
        "btn_period_symptoms": "💊 记录症状",
        "btn_period_history": "📊 生理期历史",
        "period_start_prompt": "📅 你的生理期什么时候开始？\n\n输入今天的日期或说\'今天\'\n（格式：YYYY-MM-DD 或 \'今天\'）",
        "period_logged": "✅ 生理期开始已记录：{date}！\n\n💡 {tip}",
        "period_cycle_prompt": "你的月经周期通常是多少天？（例如28）\n不确定请输入\'跳过\'",
        "period_symptoms_prompt": "💊 你感觉怎么样？\n\n描述你的症状，我会给你个性化建议！\n例如：痛经、腹胀、疲劳、情绪波动、食欲变化",
        "period_symptom_response": "💊 症状支持：",
        "period_history_empty": "还没有生理期记录！使用 📅 记录生理期开始 来开始追踪。",
        "period_history_title": "📊 生理期历史\n\n",
        "period_prediction": "\n\n🔮 预计下次生理期：{date}",
        "period_tips": [
            "多喝水，多吃菠菜、扁豆等富含铁的食物 🥬",
            "轻度运动如瑜伽或散步可以缓解痛经 🧘",
            "雌激素正在上升——是力量训练的好时机！💪",
            "食欲旺盛是正常的！选择黑巧克力或坚果 🍫",
            "你正处于黄体期——优先休息和自我护理 🌙",
            "富含镁的食物如香蕉和坚果可以缓解经前综合征 🍌",
            "今天感到疲劳是正常的——你的身体在努力工作 💕",
        ],
    },
    "ko": {
        "btn_log_meal": "🍱 식사 기록",
        "btn_log_exercise": "🏃 운동 기록",
        "btn_log_weight": "⚖️ 체중 기록",
        "btn_summary": "📊 오늘의 요약",
        "btn_streaks": "🔥 나의 연속 기록",
        "btn_weight_progress": "📈 체중 변화",
        "btn_recipes": "🍜 고단백 레시피",
        "btn_ask": "❓ 영양 질문",
        "btn_goals": "🎯 목표 설정",
        "btn_profile": "👤 내 프로필",
        "btn_workout": "🏋️ 운동 추천",
        "btn_language": "🌐 언어",
        "btn_enter_code": "🔑 액세스 코드 입력",
        "btn_manual": "✏️ 직접 입력",
        "btn_quiz": "🧮 자동 계산 (퀴즈)",
        "btn_weekly": "📅 주간 루틴",
        "btn_single": "💪 단일 세션 계획",
        "btn_female": "여성",
        "btn_male": "남성",
        "btn_sedentary": "🛋️ 비활동적 (운동 거의 안 함)",
        "btn_light": "🚶 가볍게 활동 (주 1-3회)",
        "btn_moderate": "🏃 보통 활동 (주 3-5회)",
        "btn_very": "💪 매우 활동적 (주 6-7회)",
        "btn_lose": "🔥 체중 감량",
        "btn_build": "💪 근육 증가",
        "btn_maintain": "⚖️ 체중 유지",
        "btn_ecto": "🦴 외배엽형 (자연적으로 마른 편)",
        "btn_meso": "💪 중배엽형 (운동형 체형)",
        "btn_endo": "🌿 내배엽형 (살이 잘 찌는 편)",
        "btn_blood_a": "🅰️ A형",
        "btn_blood_b": "🅱️ B형",
        "btn_blood_ab": "🆎 AB형",
        "btn_blood_o": "🅾️ O형",
        "btn_blood_unknown": "❓ 모름",
        "welcome_back": "안녕하세요 {name}! 🌿 식단 & 피트니스 트래커에 오신 것을 환영합니다.\n{sub_msg}\n\n무엇을 도와드릴까요?",
        "welcome_locked": (
            "안녕하세요 {name}! 🌿 Michele의 다이어트 봇에 오신 것을 환영합니다!\n\n"
            "AI 기반 개인 식단 & 피트니스 트래커 🇸🇬\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n✨ 기능\n━━━━━━━━━━━━━━━━━━━━\n"
            "🍱 텍스트 또는 사진으로 식사 기록\n🤖 아시아 음식 AI 영양 추정\n"
            "🏃 운동 추적\n⚖️ 체중 모니터링\n"
            "🔥 식단 & 운동 연속 기록\n🍜 고단백 레시피\n"
            "❓ AI 영양 Q&A\n🏋️ 운동 계획\n⏰ 일일 알림\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n💳 구독 플랜\n━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣  1개월 — $8 SGD\n3️⃣  3개월 — $18 SGD\n"
            "6️⃣  6개월 — $30 SGD\n🏆 12개월 — $45 SGD\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n💰 구독 방법\n━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣ Michele에게 PayNow 결제\n2️⃣ 결제 스크린샷 전송\n"
            "3️⃣ 액세스 코드 수신\n4️⃣ 아래 버튼을 눌러 코드 입력！👇"
        ),
        "sub_active": "✅ 구독 유효 기간: {expiry}까지",
        "admin_access": "👑 관리자 권한",
        "locked_msg": "🔒 구독이 필요합니다! /redeem 을 사용해 코드를 입력하세요.",
        "enter_code_prompt": "🔑 액세스 코드를 입력해 주세요:\n\n형식: MICH-XXXXXXXX",
        "code_success": "🎉 액세스 허용! Michele의 다이어트 봇에 오신 것을 환영합니다!\n\n✅ 구독 유효 기간: {expiry}까지\n\n모든 기능을 사용할 수 있습니다! 🌿",
        "code_fail": "❌ {reason}\n\n코드를 확인하고 다시 시도하거나 Michele에게 문의하세요.",
        "meal_prompt": "🍱 무엇을 드셨나요?\n\n방법:\n• 설명 입력, 예: 삶은 달걀 2개와 오트밀\n• 음식 사진 전송 📸\n\n영양소를 추정해 드릴게요!",
        "estimating": "⏳ 영양소 추정 중...",
        "meal_logged": "✅ 식사 기록 완료!\n\n이번 식사:\n  칼로리: {cal} kcal\n  단백질: {prot}g\n  탄수화물: {carbs}g\n  지방: {fat}g\n\n오늘 남은 양:\n  순 칼로리: {net} kcal\n  단백질: {prot_left}g{streak}",
        "diet_streak": "\n\n{emoji} 식단 연속: {count}일!",
        "exercise_prompt": "🏃 운동을 기록하세요!\n\n형식: <운동> | <소모 칼로리>\n\n예시:\n• 요가 45분 | 180\n• 달리기 30분 | 300\n• 웨이트 1시간 | 250",
        "exercise_format_err": "이 형식을 사용하세요:\n<운동> | <칼로리>\n\n예: 요가 45분 | 180",
        "exercise_logged": "✅ 운동 기록 완료!\n\n🏃 {exercise}\n  소모 칼로리: {cal} kcal\n\n오늘 합계:\n  섭취 칼로리: {eaten} kcal\n  소모 칼로리: {burned} kcal\n  남은 순 칼로리: {net} kcal{streak}",
        "workout_streak": "\n\n{emoji} 운동 연속: {count}일!",
        "weight_prompt": "⚖️ 오늘 체중은? (kg, 예: 52.3)",
        "weight_logged": "✅ 기록됨: {weight} kg{change}",
        "weight_change": "\n{arrow} 지난 기록 대비: {diff:+.1f} kg",
        "weight_err": "숫자를 입력해 주세요, 예: 52.3",
        "no_logs": "오늘 기록이 없습니다!\n🍱 식사 기록 또는 🏃 운동 기록을 사용하세요.",
        "summary_title": "📊 오늘의 요약 — {date}",
        "summary_meals": "🍽 식사:",
        "summary_exercise": "🏃 운동:",
        "summary_nutrition": "📈 영양:",
        "summary_streaks": "🔥 연속 기록:",
        "none_yet": "  없음",
        "no_weight": "체중 기록이 없습니다! ⚖️ 체중 기록을 사용하세요.",
        "weight_progress_title": "📈 체중 변화",
        "total_change": "총 변화: {diff:+.1f} kg",
        "streaks_title": "🔥 나의 연속 기록",
        "healthy_eating": "건강한 식습관",
        "working_out": "꾸준한 운동",
        "streaks_tip": "계속하세요! 식사를 기록해 식단 연속을 늘리세요 🍱\n운동을 기록해 운동 연속을 늘리세요 🏃",
        "ask_prompt": "❓ 영양, 운동, 식단에 대해 무엇이든 물어보세요!",
        "thinking": "🤔 생각 중...",
        "ai_err": "죄송합니다, 처리할 수 없습니다. 다시 시도해 주세요!",
        "recipe_prompt": "🍜 고단백 아시아 레시피!\n\n무엇을 원하세요? 예:\n• 닭고기\n• 두부 요리\n• 고단백 아침식사\n• 500칼로리 이하\n\n알려주세요! 🥢",
        "finding_recipes": "🔍 레시피를 찾고 있습니다...",
        "recipe_err": "죄송합니다, 레시피를 찾을 수 없습니다. 다시 시도해 주세요!",
        "goals_prompt": "🎯 일일 목표를 설정합시다!\n\n어떻게 설정하시겠어요?",
        "manual_prompt": "✏️ 일일 목표를 입력하세요:\n\n<칼로리> <단백질>\n\n예: 1400 100\n(1400 kcal, 단백질 100g)",
        "goals_saved": "✅ 목표가 저장되었습니다!\n\n  일일 칼로리: {cal} kcal\n  일일 단백질: {prot}g\n\n👤 내 프로필에서 언제든지 확인하세요!",
        "goals_err": "유효한 숫자를 입력하세요.\n형식: <칼로리> <단백질>\n예: 1400 100",
        "quiz_height": "🧮 이상적인 영양 목표를 계산해 드릴게요!\n\n먼저, 키가 몇 cm인가요?\n예: 160",
        "quiz_height_err": "유효한 키를 입력해 주세요 (cm), 예: 160",
        "quiz_weight_q": "알겠습니다! {h}cm 📏\n\n현재 체중은 몇 kg인가요?\n예: 55",
        "quiz_weight_err": "유효한 체중을 입력해 주세요 (kg), 예: 55",
        "quiz_age_q": "알겠습니다! {w}kg ⚖️\n\n나이가 어떻게 되세요?",
        "quiz_age_err": "유효한 나이를 입력해 주세요, 예: 25",
        "quiz_gender_q": "성별이 어떻게 되세요?",
        "quiz_gender_err": "여성 또는 남성을 선택해 주세요",
        "quiz_activity_q": "활동 수준은 어떻게 되세요?",
        "quiz_activity_err": "위의 옵션 중 하나를 선택해 주세요!",
        "quiz_goal_q": "피트니스 목표는 무엇인가요?",
        "quiz_body_q": "체형은 어떻게 되세요?",
        "quiz_blood_q": "마지막입니다! 혈액형은 무엇인가요?",
        "quiz_result": (
            "🎯 개인 맞춤 목표가 준비되었습니다!\n\n"
            "📊 나의 데이터:\n  키: {h}cm | 체중: {w}kg | 나이: {age}\n"
            "  목표: {goal} | 체형: {body}\n\n"
            "🔥 일일 목표:\n  칼로리: {cal} kcal\n  단백질: {prot}g\n\n"
            "💡 {blood_note}\n\n👤 내 프로필에서 언제든지 확인하세요!"
        ),
        "blood_notes": {
            "A": "A형: 두부, 콩류 같은 식물성 단백질이 잘 맞을 수 있습니다. 🌱",
            "B": "B형: 살코기, 달걀, 유제품이 잘 맞을 수 있습니다. 🥚",
            "AB": "AB형: A형과 B형의 균형 잡힌 식단이 적합합니다. ⚖️",
            "O": "O형: 살코기와 생선 같은 고단백 식품이 잘 맞을 수 있습니다. 🐟",
            "unknown": "팁: 혈액형을 알면 식단을 더 개인화할 수 있습니다! 💡",
        },
        "profile_title": "👤 내 프로필",
        "profile_info": "📋 개인 정보:",
        "profile_height": "  키: {h} cm",
        "profile_weight": "  체중: {w} kg",
        "profile_age": "  나이: {age}",
        "profile_gender": "  성별: {gender}",
        "profile_blood": "  혈액형: {blood}",
        "profile_body": "  체형: {body}",
        "profile_goal": "  목표: {goal}",
        "profile_targets": "🎯 일일 목표:",
        "profile_cal": "  칼로리: {cal} kcal",
        "profile_prot": "  단백질: {prot}g",
        "profile_sub": "✅ 구독: {expiry}까지 유효",
        "profile_tip": "🎯 목표 설정을 탭해 언제든지 업데이트하세요!",
        "lang_prompt": "🌐 언어를 선택하세요:",
        "lang_set": "✅ 언어가 한국어로 설정되었습니다!",
        "workout_type_q": "🏋️ 어떤 운동에 관심이 있으신가요?",
        "workout_plan_q": "전체 주간 루틴을 원하시나요, 아니면 단일 세션 계획을 원하시나요?",
        "workout_generating": "⏳ 운동 계획을 생성하고 있습니다...",
        "workout_err": "죄송합니다, 지금은 계획을 생성할 수 없습니다. 다시 시도해 주세요!",
        "reminders_set": "⏰ 알림이 설정되었습니다!\n• 오전 8시 알림\n• 오후 8시 체크인",
        "morning_msg": "☀️ 좋은 아침입니다! 오늘의 목표를 달성할 준비가 되셨나요? 💪\n\n아침 식사와 운동을 기록해 연속 기록을 유지하세요! 🔥",
        "goals_goal_map": {"lose": "체중 감량 🔥", "build": "근육 증가 💪", "maintain": "체중 유지 ⚖️"},
        "btn_plan": "📋 식단 & 운동 계획",
        "btn_chat": "💬 봇과 대화하기",
        "plan_prompt": "📋 목표가 무엇인가요?\n\n예: 2개월 안에 5kg 감량, 린머슬 증가, 이벤트를 위한 체형 관리\n\n목표를 알려주시면 맞춤 식단 & 운동 계획을 만들어 드릴게요!",
        "plan_generating": "⏳ 개인 맞춤 계획을 생성하고 있습니다...",
        "plan_err": "죄송합니다, 지금은 계획을 생성할 수 없습니다. 다시 시도해 주세요!",
        "btn_yoga": "🧘 요가", "btn_pilates": "🩰 필라테스",
        "btn_spin": "🚴 스핀/사이클링", "btn_cardio": "🏃 유산소",
        "btn_weights": "🏋️ 웨이트", "btn_hiit": "🥊 HIIT",
        "btn_calisthenics": "🤸 맨몸 운동", "btn_swimming": "🏊 수영",
        "btn_other_exercise": "✍️ 기타 (직접 입력)",
        "btn_arms": "💪 팔", "btn_chest": "🫁 가슴",
        "btn_back": "🔙 등", "btn_legs": "🦵 다리",
        "btn_whole_body": "🏋️ 전신",
        "muscle_prompt": "어느 부위를 운동하시겠어요?",
        "youtube_tip": "\n\n💡 YouTube 검색: ",
        "chat_prompt": "💬 안녕하세요! 오늘 하루 어떠셨나요? 음식, 피트니스, 또는 일상에 대해 무엇이든 이야기해 주세요! 😊\n\n(/start 를 입력하면 언제든지 메인 메뉴로 돌아갈 수 있습니다)",
        "chat_exit": "언제든지 /start 를 입력해 메인 메뉴로 돌아가세요! 🌿",
        "voice_processing": "🎤 음성 메시지를 처리하고 있습니다...",
        "voice_err": "죄송합니다, 음성 메시지를 처리할 수 없습니다. 텍스트로 입력해 주세요!",
        "meal_preview": "📋 *영양 추정:*\n\n  칼로리: {cal} kcal\n  단백질: {prot}g\n  탄수화물: {carbs}g\n  지방: {fat}g\n\n_{desc}_\n\n맞나요?",
        "btn_confirm_log": "✅ 네, 기록하기!",
        "btn_discard": "❌ 삭제",
        "btn_adjust": "✏️ 수정하기",
        "meal_discarded": "🗑 삭제되었습니다. 아무것도 기록되지 않았습니다.",
        "adjust_prompt": "올바른 영양 정보를 입력하세요:\n<칼로리> <단백질> <탄수화물> <지방>\n\n예: 650 35 72 18",
        "adjust_err": "숫자 4개를 입력해 주세요, 예: 650 35 72 18",
        "btn_period": "🌸 생리 트래커",
        "btn_grocery": "🛒 내 식재료",
        "btn_shortcuts": "⚡ 식사 단축키",
        "btn_apple_health": "🍎 애플 헬스",
        "onboard_welcome": "🎉 Mich의 다이어트 봇에 오신 것을 환영합니다, {name}!\n\n시작 전에 프로필을 설정하면 맞춤 칼로리와 단백질 목표를 계산해 드릴게요.\n\n약 1분 정도 걸립니다! 준비됐나요? 💪",
        "btn_onboard_yes": "✅ 시작해요!",
        "btn_onboard_skip": "⏭ 나중에",
        "shortcuts_menu": "⚡ *식사 단축키*\n\n자주 먹는 식사를 한 번에 기록하세요!\n\n저장된 단축키:",
        "shortcuts_empty": "단축키가 없습니다! ➕ 단축키 추가를 탭하세요.",
        "btn_add_shortcut": "➕ 단축키 추가",
        "btn_use_shortcut": "🍱 단축키로 기록",
        "shortcut_name_prompt": "이 단축키의 이름을 정해주세요.\n\n예: 치킨라이스 점심, 아침 오트밀, 운동 후 쉐이크",
        "shortcut_macros_prompt": "*{name}*의 영양 정보를 입력해주세요:\n\n<칼로리> <단백질> <탄수화물> <지방>\n\n예: 550 35 60 14",
        "shortcut_saved": "✅ 단축키 저장됨: *{name}*\n{cal}kcal · 단백질 {prot}g · 탄수화물 {carbs}g · 지방 {fat}g",
        "shortcut_macros_err": "숫자 4개를 입력하세요: <칼로리> <단백질> <탄수화물> <지방>\n예: 550 35 60 14",
        "shortcut_logged": "✅ 기록됨: *{name}*\n\n  칼로리: {cal}kcal\n  단백질: {prot}g\n  탄수화물: {carbs}g\n  지방: {fat}g\n\n오늘 남은: {net}kcal · 단백질 {prot_left}g{streak}",
        "shortcut_log_prompt": "어떤 단축키를 기록하시겠어요?",
        "shortcut_none_yet": "저장된 단축키가 없습니다! 먼저 추가해주세요.",
        "apple_health_msg": "🍎 *애플 헬스 연동*\n\n봇은 애플 헬스에 직접 연결되지 않지만, 두 가지 방법으로 동기화할 수 있습니다.\n\n📱 *방법 1: iOS 단축어*\n건강 앱에서 데이터를 읽어 봇에 자동으로 전송하는 단축어를 만드세요.\n\n⌚ *방법 2: 수동 기록*\n운동 후 Apple Watch의 활성 칼로리를 사용해 수동으로 기록하세요!",
        "btn_quick_log": "⚡ 빠른 기록",
        "btn_apple_health": "🍎 Apple Health 내보내기",
        "quick_log_menu": "⚡ *빠른 기록*\n\n자주 먹는 음식을 즉시 기록하세요!\n\n저장된 식사:",
        "quick_log_empty": "⚡ *빠른 기록*\n\n저장된 식사가 없습니다!\n\n식사를 기록하면 빠른 기록으로 저장할지 물어봅니다.",
        "quick_log_save_prompt": "💾 빠른 기록으로 저장하시겠어요?\n\n이름을 지어주세요 (예: \'점심 치킨라이스\'):\n\n건너뛰려면 탭하세요.",
        "quick_log_saved": "✅ \'{name}\'으로 저장되었습니다! 다음에 빠른 기록에 나타납니다.",
        "quick_log_skip": "건너뛰기",
        "quick_log_logged": "⚡ 빠른 기록: *{name}*\n\n  칼로리: {cal} kcal\n  단백질: {prot}g\n  탄수화물: {carbs}g\n  지방: {fat}g\n\n남은 순 칼로리: {net} kcal",
        "apple_health_intro": "🍎 *Apple Health 내보내기*\n\n데이터를 Apple Health, MyFitnessPal 등과 호환되는 CSV로 내보냅니다.\n\n{count}개 식사 기록과 {weight_count}개 체중 기록을 내보내는 중...",
        "apple_health_ready": "✅ 데이터가 준비되었습니다! 아래 텍스트를 복사해 .csv 파일로 저장 후 건강 앱에 가져오세요.\n\n",
        "onboard_welcome": "🌿 *Mich의 다이어트 봇에 오신 것을 환영합니다!*\n\n시작하기 전에 2분 안에 프로필을 설정해 드릴게요 — 개인화된 칼로리 목표와 영양소 추천을 받을 수 있어요!\n\n준비되셨나요? 시작해요! 💪",
        "onboard_skip": "설정 건너뛰기 →",
        "grocery_menu_prompt": "🛒 *식재료 트래커*\n\n무엇을 하시겠어요?",
        "btn_grocery_add": "➕ 구매한 식재료 기록",
        "btn_grocery_use": "✅ 사용한 항목 표시",
        "btn_grocery_view": "📦 식재료 보기",
        "btn_grocery_recipe": "👩‍🍳 무엇을 만들 수 있나요?",
        "grocery_add_prompt": "➕ 무엇을 구매했나요?\n\n한 줄에 하나씩 또는 쉼표로 구분:\n\n예:\n닭가슴살 500g\n달걀 6개\n시금치\n두부 2모",
        "grocery_added": "✅ 식재료가 기록되었습니다! 식재료 현황:\n\n{items}",
        "grocery_use_prompt": "✅ 무엇을 사용했나요?\n\n항목을 입력하세요 (쉼표 구분):\n예: 달걀, 시금치",
        "grocery_used": "✅ 사용 완료로 표시:\n{items}\n\n남은 식재료:\n{remaining}",
        "grocery_empty": "식재료가 없습니다! ➕ 식재료 기록을 탭하세요.",
        "grocery_view": "📦 *내 식재료*\n\n{items}\n\n_다 사용하면 ✅ 사용 완료를 탭하세요!_",
        "grocery_recipe_prompt": "👩‍🍳 보유한 재료로 레시피를 찾고 있습니다...",
        "grocery_recipe_err": "죄송합니다, 레시피를 생성할 수 없습니다!",
        "meal_is_that_all": "알겠습니다! 🍽 추가할 것이 있나요? (음료, 사이드, 간식)\n\n다 됐으면 ✅ 완료 를 탭하세요!",
        "btn_meal_done": "✅ 완료, 기록하기!",
        "btn_meal_add_more": "➕ 더 추가하기",
        "period_menu_prompt": "🌸 생리 트래커\n\n무엇을 하시겠어요?",
        "btn_log_period": "📅 생리 시작 기록",
        "btn_period_symptoms": "💊 증상 기록",
        "btn_period_history": "📊 생리 기록",
        "period_start_prompt": "📅 생리가 언제 시작되었나요?\n\n오늘 날짜를 입력하거나 \'오늘\'이라고 하세요\n(형식: YYYY-MM-DD 또는 \'오늘\')",
        "period_logged": "✅ {date} 생리 시작이 기록되었습니다!\n\n💡 {tip}",
        "period_cycle_prompt": "평균 생리 주기가 며칠인가요? (예: 28)\n모르면 \'건너뛰기\'를 입력하세요",
        "period_symptoms_prompt": "💊 지금 어떠세요?\n\n증상을 설명해 주시면 맞춤 조언을 드릴게요!\n예: 생리통, 복부팽만, 피로, 기분 변화, 식욕 변화",
        "period_symptom_response": "💊 증상 지원:",
        "period_history_empty": "생리 기록이 없습니다! 📅 생리 시작 기록을 사용해 추적을 시작하세요.",
        "period_history_title": "📊 생리 기록\n\n",
        "period_prediction": "\n\n🔮 다음 생리 예상일: {date}",
        "period_tips": [
            "수분을 충분히 섭취하고 시금치, 렌틸콩 등 철분이 풍부한 음식을 드세요 🥬",
            "요가나 걷기 같은 가벼운 운동이 생리통에 도움이 될 수 있어요 🧘",
            "에스트로겐이 상승 중이에요 — 근력 운동하기 좋은 시기예요! 💪",
            "식욕이 생기는 건 자연스러운 일이에요! 다크초콜릿이나 견과류를 선택하세요 🍫",
            "황체기예요 — 휴식과 자기관리를 우선으로 하세요 🌙",
            "바나나와 견과류 같은 마그네슘이 풍부한 음식이 PMS 증상을 완화할 수 있어요 🍌",
            "오늘 피곤한 건 정상이에요 — 몸이 열심히 일하고 있답니다 💕",
        ],
    }
}


def t(user_or_lang, key, **kwargs):
    lang = user_or_lang if isinstance(user_or_lang, str) else user_or_lang.get("language", "en")
    if lang not in T:
        lang = "en"
    val = T[lang].get(key, T["en"].get(key, key))
    if kwargs:
        try:
            return val.format(**kwargs)
        except Exception:
            return val
    return val


# ─────────────────────────────────────────────
# PERSISTENT STORAGE
# ─────────────────────────────────────────────

def _sb_headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

def _sb_get(key):
    try:
        r = _httpx.get(f"{SUPABASE_URL}/rest/v1/bot_data?key=eq.{key}&select=value", headers=_sb_headers(), timeout=5)
        rows = r.json()
        return rows[0]["value"] if rows else {}
    except Exception as e:
        logger.error(f"Supabase get error: {e}")
        return {}

def _sb_set(key, value):
    try:
        _httpx.post(
            f"{SUPABASE_URL}/rest/v1/bot_data",
            headers={**_sb_headers(), "Prefer": "resolution=merge-duplicates"},
            json={"key": key, "value": value, "updated_at": "now()"},
            timeout=5
        )
    except Exception as e:
        logger.error(f"Supabase set error: {e}")

def load_data():
    if USE_SUPABASE:
        try:
            users = _sb_get("users")
            codes = _sb_get("codes")
            return {"users": users or {}, "codes": codes or {}}
        except Exception as e:
            logger.error(f"Supabase load error: {e}")
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"File load error: {e}")
    return {"users": {}, "codes": {}}


def save_data():
    if USE_SUPABASE:
        try:
            _sb_set("users", {str(k): v for k, v in user_data_store.items()})
            _sb_set("codes", subscription_codes)
            return
        except Exception as e:
            logger.error(f"Supabase save error: {e}")
    try:
        with open(DATA_FILE, "w") as f:
            json.dump({"users": user_data_store, "codes": subscription_codes}, f, indent=2)
    except Exception as e:
        logger.error(f"File save error: {e}")


_data = load_data()
user_data_store = {int(k): v for k, v in _data.get("users", {}).items()}
subscription_codes = _data.get("codes", {})


# ─────────────────────────────────────────────
# USER & SUBSCRIPTION HELPERS
# ─────────────────────────────────────────────

def get_user(user_id):
    user_id = int(user_id)
    if user_id not in user_data_store:
        user_data_store[user_id] = {
            "meals": [], "weights": [], "exercises": [],
            "goals": {"calories": 1300, "protein": 90},
            "streaks": {
                "diet": {"last_date": None, "count": 0},
                "workout": {"last_date": None, "count": 0},
            },
            "subscription_expiry": None,
            "language": "en",
            "profile": {},
            "period_logs": [],
            "cycle_length": 28,
            "pantry": [],
            "shortcuts": [],
            "quick_meals": [],
        }
        save_data()
    return user_data_store[user_id]


def is_subscribed(user_id):
    expiry = get_user(user_id).get("subscription_expiry")
    if not expiry:
        return False
    return datetime.strptime(expiry, "%Y-%m-%d") >= datetime.now()


def is_admin(user_id):
    return int(user_id) == ADMIN_ID


def check_access(user_id):
    return is_admin(user_id) or is_subscribed(user_id)


def get_expiry_str(user_id):
    return get_user(user_id).get("subscription_expiry", "N/A")


def generate_code(days=30):
    code = "MICH-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    subscription_codes[code] = {"used": False, "days": days, "used_by": None}
    save_data()
    return code


def generate_dashboard_password():
    """Generate a memorable 3-word style password."""
    words = ["bloom","lotus","peach","coral","jade","mochi","sakura","yuzu",
             "matcha","lychee","boba","daisy","amber","pearl","dewdrop","sunlit",
             "honey","maple","berry","plum","zesty","crisp","fresh","glow"]
    nums = random.choices(string.digits, k=3)
    w1 = random.choice(words).capitalize()
    w2 = random.choice(words).capitalize()
    return w1 + w2 + "".join(nums)


def redeem_code(user_id, code):
    code = code.strip().upper()
    if code not in subscription_codes:
        return False, "Invalid code. Please check and try again!", None

    code_info = subscription_codes[code]

    # If code was already used by a DIFFERENT user — reject
    if code_info["used"] and code_info["used_by"] != user_id:
        return False, "This code has already been used by another account.", None

    user = get_user(user_id)
    days = code_info["days"]
    start = datetime.now()
    if user.get("subscription_expiry"):
        existing = datetime.strptime(user["subscription_expiry"], "%Y-%m-%d")
        if existing > start:
            start = existing
    expiry = (start + timedelta(days=days)).strftime("%Y-%m-%d")
    user["subscription_expiry"] = expiry

    # Generate dashboard password only on first redemption
    if not code_info["used"]:
        dash_password = generate_dashboard_password()
        user["dashboard_password"] = dash_password
        code_info["used"] = True
        code_info["used_by"] = user_id
    else:
        # Same user redeeming again (renewal) — keep existing password
        dash_password = user.get("dashboard_password", generate_dashboard_password())
        user["dashboard_password"] = dash_password

    save_data()
    return True, expiry, dash_password


def today():
    return datetime.now().strftime("%Y-%m-%d")


def yesterday():
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def today_meals(user):
    return [m for m in user["meals"] if m["date"] == today()]


def today_exercises(user):
    return [e for e in user["exercises"] if e["date"] == today()]


def today_totals(user):
    meals = today_meals(user)
    exercises = today_exercises(user)
    return {
        "calories": sum(m["calories"] for m in meals),
        "protein": sum(m["protein"] for m in meals),
        "burned": sum(e["calories_burned"] for e in exercises),
    }


def update_streak(user, streak_type):
    streak = user["streaks"][streak_type]
    td = today()
    if streak["last_date"] == td:
        return
    elif streak["last_date"] == yesterday():
        streak["count"] += 1
    else:
        streak["count"] = 1
    streak["last_date"] = td
    save_data()


def get_streak_emoji(count):
    if count >= 30: return "🏆"
    elif count >= 14: return "🔥"
    elif count >= 7: return "⚡"
    elif count >= 3: return "✨"
    return "🌱"


def main_keyboard(lang="en"):
    buttons = [
        [KeyboardButton(T[lang]["btn_log_meal"]), KeyboardButton(T[lang]["btn_log_exercise"])],
        [KeyboardButton(T[lang]["btn_log_weight"]), KeyboardButton(T[lang]["btn_summary"])],
        [KeyboardButton(T[lang]["btn_streaks"]), KeyboardButton(T[lang]["btn_weight_progress"])],
        [KeyboardButton(T[lang]["btn_recipes"]), KeyboardButton(T[lang]["btn_ask"])],
        [KeyboardButton(T[lang]["btn_goals"]), KeyboardButton(T[lang]["btn_profile"])],
        [KeyboardButton(T[lang]["btn_workout"]), KeyboardButton(T[lang]["btn_language"])],
        [KeyboardButton(T[lang]["btn_plan"]), KeyboardButton(T[lang]["btn_chat"])],
        [KeyboardButton(T[lang]["btn_period"]), KeyboardButton(T[lang]["btn_grocery"])],
        [KeyboardButton(T[lang]["btn_quick_log"]), KeyboardButton(T[lang]["btn_apple_health"])],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def locked_keyboard(lang="en"):
    return ReplyKeyboardMarkup([[KeyboardButton(T[lang]["btn_enter_code"])]], resize_keyboard=True)


def get_lang(user):
    return user.get("language", "en")


# ─────────────────────────────────────────────
# START & SUBSCRIPTION
# ─────────────────────────────────────────────

async def start(update, context):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    user = get_user(user_id)
    lang = get_lang(user)

    if check_access(user_id):
        # First-time subscriber with no profile — trigger onboarding
        if not user.get("profile") and not user.get("onboarded") and not is_admin(user_id):
            user["onboarded"] = False
            save_data()
            await update.message.reply_text(
                t(lang, "onboard_welcome"),
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup([
                    [KeyboardButton("🚀 Let's set up my profile!")],
                    [KeyboardButton(t(lang, "onboard_skip"))],
                ], resize_keyboard=True)
            )
            return ONBOARD_LANG
        sub_msg = t(lang, "sub_active", expiry=get_expiry_str(user_id)) if not is_admin(user_id) else t(lang, "admin_access")
        await update.message.reply_text(t(lang, "welcome_back", name=name, sub_msg=sub_msg), reply_markup=main_keyboard(lang))
    else:
        await update.message.reply_text(t(lang, "welcome_locked", name=name), reply_markup=locked_keyboard(lang))
    return MAIN_MENU


async def receive_onboard_start(update, context):
    """Handle first step of onboarding — language select or skip."""
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text

    if any(x in text for x in ["Skip", "跳过", "건너뛰기", "→"]):
        user["onboarded"] = True
        save_data()
        name = update.effective_user.first_name
        sub_msg = t(lang, "sub_active", expiry=get_expiry_str(update.effective_user.id))
        await update.message.reply_text(
            t(lang, "welcome_back", name=name, sub_msg=sub_msg),
            reply_markup=main_keyboard(lang)
        )
        return MAIN_MENU

    # They want to set up — ask language first
    await update.message.reply_text(
        t(lang, "lang_prompt"),
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("English 🇬🇧")],
            [KeyboardButton("中文 🇨🇳")],
            [KeyboardButton("한국어 🇰🇷")],
        ], resize_keyboard=True)
    )
    context.user_data["onboarding"] = True
    return SELECT_LANG


async def prompt_enter_code(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    await update.message.reply_text(t(lang, "enter_code_prompt"))
    return ENTER_CODE


async def receive_code(update, context):
    user_id = update.effective_user.id
    user = get_user(user_id)
    lang = get_lang(user)
    success, result, dash_password = redeem_code(user_id, update.message.text.strip())
    if success:
        # Send welcome message
        await update.message.reply_text(t(lang, "code_success", expiry=result), reply_markup=main_keyboard(lang))
        # Send dashboard credentials as a separate message they can forward to Saved Messages
        url_line = f"\n📊 Dashboard: {DASHBOARD_URL}" if DASHBOARD_URL else ""
        dashboard_msgs = {
            "en": (
                f"🔐 *Your Dashboard Login*\n\n"
                f"Save this to your Saved Messages!\n\n"
                f"🆔 Telegram ID: `{user_id}`\n"
                f"🔑 Password: `{dash_password}`\n"
                f"📅 Valid until: {result}"
                f"{url_line}\n\n"
                f"⚠️ Keep this private — unique to your account.\n\n"
                f"➡️ Forward this to your Saved Messages now!"
            ),
            "zh": (
                f"🔐 *你的仪表盘登录信息*\n\n"
                f"保存到你的收藏消息！\n\n"
                f"🆔 Telegram ID: `{user_id}`\n"
                f"🔑 密码: `{dash_password}`\n"
                f"📅 有效期至: {result}"
                f"{url_line}\n\n"
                f"⚠️ 请保密——此密码专属你的账号。\n\n"
                f"➡️ 现在将此消息转发到你的收藏消息！"
            ),
            "ko": (
                f"🔐 *대시보드 로그인 정보*\n\n"
                f"저장된 메시지에 저장하세요!\n\n"
                f"🆔 Telegram ID: `{user_id}`\n"
                f"🔑 비밀번호: `{dash_password}`\n"
                f"📅 유효 기간: {result}까지"
                f"{url_line}\n\n"
                f"⚠️ 비공개로 유지하세요.\n\n"
                f"➡️ 저장된 메시지로 전달하세요!"
            ),
        }
        await update.message.reply_text(
            dashboard_msgs.get(lang, dashboard_msgs["en"]),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(t(lang, "code_fail", reason=result), reply_markup=locked_keyboard(lang))
    return MAIN_MENU


async def redeem_command(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    await update.message.reply_text(t(lang, "enter_code_prompt"))
    return ENTER_CODE


async def check_subscription(update, context):
    user_id = update.effective_user.id
    user = get_user(user_id)
    lang = get_lang(user)
    if is_subscribed(user_id):
        expiry = get_expiry_str(user_id)
        days_left = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days
        await update.message.reply_text(f"✅ Active until: {expiry}\nDays left: {days_left}")
    else:
        await update.message.reply_text(t(lang, "locked_msg"))


# ─────────────────────────────────────────────
# LANGUAGE
# ─────────────────────────────────────────────

async def prompt_language(update, context):
    if not check_access(update.effective_user.id):
        user = get_user(update.effective_user.id)
        await update.message.reply_text(t(get_lang(user), "locked_msg"), reply_markup=locked_keyboard(get_lang(user)))
        return MAIN_MENU
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    await update.message.reply_text(
        t(lang, "lang_prompt"),
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("English 🇬🇧")],
            [KeyboardButton("中文 🇨🇳")],
            [KeyboardButton("한국어 🇰🇷")],
        ], resize_keyboard=True)
    )
    return SELECT_LANG


async def receive_language(update, context):
    text = update.message.text
    user = get_user(update.effective_user.id)
    if "中文" in text or "🇨🇳" in text:
        user["language"] = "zh"
    elif "한국어" in text or "🇰🇷" in text:
        user["language"] = "ko"
    else:
        user["language"] = "en"
    save_data()
    lang = user["language"]
    # If mid-onboarding, go straight into the quiz
    if context.user_data.get("onboarding"):
        await update.message.reply_text(t(lang, "quiz_height"))
        return QUIZ_HEIGHT
    await update.message.reply_text(t(lang, "lang_set"), reply_markup=main_keyboard(lang))
    return MAIN_MENU


# ─────────────────────────────────────────────
# MEAL LOGGING
# ─────────────────────────────────────────────

async def prompt_log_meal(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    await update.message.reply_text(t(lang, "meal_prompt"))
    return LOG_MEAL


async def estimate_meal(meal_text, photo_b64=None):
    """Estimate macros for a meal description or photo (or both together)."""
    try:
        system_prompt = (
            "You are a precise nutrition expert specializing in Asian cuisine, especially Singaporean and Southeast Asian food. "
            "Identify every component including drinks, sauces, sides and snacks. "
            "Consider typical hawker centre portion sizes. "
            "Account for hidden calories in oils, sauces and condiments. Be accurate — do not return 0. "
            "Reply ONLY with a JSON object, no explanation: {\"calories\": 350, \"protein\": 25, \"carbs\": 30, \"fat\": 10}"
        )
        if photo_b64:
            # Use BOTH photo AND text description together for best accuracy
            caption_context = f" The user also describes it as: \'{meal_text}\'." if meal_text and meal_text != "meal in photo" else ""
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=300,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": photo_b64}},
                    {"type": "text", "text": system_prompt + caption_context}
                ]}]
            )
        else:
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=300,
                messages=[{"role": "user", "content": (
                    system_prompt + " Analyze this meal: '" + meal_text + "'."
                )}]
            )
        raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        # Safety check — if all zeros something went wrong, flag it
        if result.get("calories", 0) == 0 and result.get("protein", 0) == 0:
            logger.warning(f"Zero macros returned for: {meal_text}")
        return result
    except Exception as e:
        logger.error(f"Macro estimation error: {e}")
        return None  # Return None so caller can handle gracefully


async def receive_meal(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)

    # ── Bug fix: "Done, log it!" button comes through as text in LOG_MEAL state
    # when the user is sent back here after the preview. Route it to finalize.
    if update.message.text:
        txt = update.message.text
        if any(x in txt for x in ["✅ Yes", "✅ 是", "✅ 네", "Yes, log", "log it",
                                    "Done, log", "완료, 기록", "完成，记录"]):
            return await finalize_meal(update, context)

    await update.message.reply_text(t(lang, "estimating"))

    if update.message.photo:
        # ── Bug fix: when multiple photos are sent at once Telegram delivers them
        # as a media group — each photo is a separate update sharing the same
        # media_group_id. We process only the first arrival and skip the rest.
        media_group_id = getattr(update.message, "media_group_id", None)
        if media_group_id:
            seen = context.user_data.get("seen_media_groups", set())
            if media_group_id in seen:
                # Already processed this group — silently ignore duplicate
                return MEAL_MORE if context.user_data.get("pending_meal") else LOG_MEAL
            seen.add(media_group_id)
            context.user_data["seen_media_groups"] = seen

        photo = update.message.photo[-1]  # largest resolution
        photo_file = await context.bot.get_file(photo.file_id)
        photo_bytes = await photo_file.download_as_bytearray()
        photo_b64 = base64.b64encode(photo_bytes).decode("utf-8")
        # Use caption + photo together for best accuracy
        meal_text = update.message.caption or "meal in photo"
        macros = await estimate_meal(meal_text, photo_b64=photo_b64)
    else:
        meal_text = update.message.text
        macros = await estimate_meal(meal_text)

    # If estimation returned None or all-zeros, show a helpful error
    if macros is None or (macros.get("calories", 0) == 0 and macros.get("protein", 0) == 0):
        err_msgs = {
            "en": "⚠️ Couldn't estimate that — try describing the food in more detail, or send a clearer single photo!",
            "zh": "⚠️ 无法估算，请更详细描述食物，或发送更清晰的单张照片！",
            "ko": "⚠️ 추정할 수 없습니다. 더 자세히 설명하거나 선명한 사진을 보내주세요!",
        }
        await update.message.reply_text(err_msgs.get(lang, err_msgs["en"]))
        return LOG_MEAL

    # Accumulate in pending
    pending = context.user_data.get("pending_meal", {"descriptions": [], "calories": 0, "protein": 0, "carbs": 0, "fat": 0})
    pending["descriptions"].append(meal_text)
    pending["calories"] += macros.get("calories", 0)
    pending["protein"] += macros.get("protein", 0)
    pending["carbs"] += macros.get("carbs", 0)
    pending["fat"] += macros.get("fat", 0)
    context.user_data["pending_meal"] = pending

    # Show preview
    desc_preview = meal_text[:60] + ("..." if len(meal_text) > 60 else "")
    await update.message.reply_text(
        t(lang, "meal_preview",
          cal=macros.get("calories", 0),
          prot=macros.get("protein", 0),
          carbs=macros.get("carbs", 0),
          fat=macros.get("fat", 0),
          desc=desc_preview),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(t(lang, "btn_confirm_log"))],
            [KeyboardButton("➕ Add more food")],
            [KeyboardButton(t(lang, "btn_adjust")), KeyboardButton(t(lang, "btn_discard"))],
        ], resize_keyboard=True)
    )
    return MEAL_MORE


async def receive_meal_more(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text if update.message.text else ""

    # Confirm — log it
    if any(x in text for x in ["✅ Yes", "✅ 是", "✅ 네", "Yes, log", "log it", "记录", "기록"]):
        return await finalize_meal(update, context)

    # Discard
    if any(x in text for x in ["❌", "Discard", "丢弃", "삭제"]):
        context.user_data.pop("pending_meal", None)
        context.user_data.pop("seen_media_groups", None)
        await update.message.reply_text(t(lang, "meal_discarded"), reply_markup=main_keyboard(lang))
        return MAIN_MENU

    # Adjust macros manually
    if any(x in text for x in ["✏️", "Adjust", "调整", "수정"]):
        await update.message.reply_text(t(lang, "adjust_prompt"))
        context.user_data["awaiting_adjustment"] = True
        return MEAL_MORE

    # Receiving manual adjustment
    if context.user_data.get("awaiting_adjustment"):
        try:
            parts = text.strip().split()
            cal, prot, carbs, fat = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            pending = context.user_data.get("pending_meal", {"descriptions": [], "calories": 0, "protein": 0, "carbs": 0, "fat": 0})
            pending["calories"] = cal
            pending["protein"] = prot
            pending["carbs"] = carbs
            pending["fat"] = fat
            context.user_data["pending_meal"] = pending
            context.user_data["awaiting_adjustment"] = False
            return await finalize_meal(update, context)
        except Exception:
            await update.message.reply_text(t(lang, "adjust_err"))
            return MEAL_MORE

    # Photo added as more food — handle media groups too
    if update.message.photo:
        media_group_id = getattr(update.message, "media_group_id", None)
        if media_group_id:
            seen = context.user_data.get("seen_media_groups", set())
            if media_group_id in seen:
                return MEAL_MORE  # skip duplicate photo in group
            seen.add(media_group_id)
            context.user_data["seen_media_groups"] = seen

        photo = update.message.photo[-1]
        photo_file = await context.bot.get_file(photo.file_id)
        photo_bytes = await photo_file.download_as_bytearray()
        photo_b64 = base64.b64encode(photo_bytes).decode("utf-8")
        add_text = update.message.caption or "additional item"
        await update.message.reply_text(t(lang, "estimating"))
        macros = await estimate_meal(add_text, photo_b64=photo_b64)
    else:
        add_text = text
        await update.message.reply_text(t(lang, "estimating"))
        macros = await estimate_meal(add_text)

    if macros is None or (macros.get("calories", 0) == 0 and macros.get("protein", 0) == 0):
        err_msgs = {
            "en": "⚠️ Couldn't estimate that item — try typing a description instead!",
            "zh": "⚠️ 无法估算该项目，请尝试文字描述！",
            "ko": "⚠️ 해당 항목을 추정할 수 없습니다. 텍스트로 설명해 주세요!",
        }
        await update.message.reply_text(err_msgs.get(lang, err_msgs["en"]))
        return MEAL_MORE

    pending = context.user_data.get("pending_meal", {"descriptions": [], "calories": 0, "protein": 0, "carbs": 0, "fat": 0})
    pending["descriptions"].append(add_text)
    pending["calories"] += macros.get("calories", 0)
    pending["protein"] += macros.get("protein", 0)
    pending["carbs"] += macros.get("carbs", 0)
    pending["fat"] += macros.get("fat", 0)
    context.user_data["pending_meal"] = pending

    desc_preview = add_text[:50] + ("..." if len(add_text) > 50 else "")
    await update.message.reply_text(
        t(lang, "meal_preview",
          cal=pending["calories"],
          prot=pending["protein"],
          carbs=pending["carbs"],
          fat=pending["fat"],
          desc=f"Running total — latest: {desc_preview}"),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(t(lang, "btn_confirm_log"))],
            [KeyboardButton("➕ Add more food")],
            [KeyboardButton(t(lang, "btn_adjust")), KeyboardButton(t(lang, "btn_discard"))],
        ], resize_keyboard=True)
    )
    return MEAL_MORE


async def finalize_meal(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    pending = context.user_data.pop("pending_meal", {"descriptions": [], "calories": 0, "protein": 0, "carbs": 0, "fat": 0})
    # Clean up media group tracking
    context.user_data.pop("seen_media_groups", None)
    context.user_data.pop("awaiting_adjustment", None)

    meal_text = " + ".join(pending["descriptions"]) if pending["descriptions"] else "meal"
    macros = {k: pending[k] for k in ["calories", "protein", "carbs", "fat"]}

    user["meals"].append({"date": today(), "description": meal_text, **macros})
    update_streak(user, "diet")
    save_data()
    streak = user["streaks"]["diet"]
    s = "" if streak["count"] == 1 else "s"
    streak_msg = t(lang, "diet_streak", emoji=get_streak_emoji(streak["count"]), count=streak["count"], s=s)
    totals = today_totals(user)
    goals = user["goals"]
    net = goals["calories"] - totals["calories"] + totals["burned"]
    await update.message.reply_text(
        t(lang, "meal_logged", cal=macros.get("calories","?"), prot=macros.get("protein","?"),
          carbs=macros.get("carbs","?"), fat=macros.get("fat","?"),
          net=net, prot_left=goals["protein"]-totals["protein"], streak=streak_msg),
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU


# ─────────────────────────────────────────────
# EXERCISE LOGGING
# ─────────────────────────────────────────────

async def prompt_log_exercise(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    await update.message.reply_text(t(lang, "exercise_prompt"))
    return LOG_EXERCISE


async def receive_exercise(update, context):
    text = update.message.text.strip()
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    try:
        if "|" not in text:
            await update.message.reply_text(t(lang, "exercise_format_err"))
            return LOG_EXERCISE
        parts = text.split("|")
        exercise_text = parts[0].strip()
        calories_burned = int(parts[1].strip())
        user["exercises"].append({"date": today(), "description": exercise_text, "calories_burned": calories_burned})
        update_streak(user, "workout")
        save_data()
        streak = user["streaks"]["workout"]
        s = "" if streak["count"] == 1 else "s"
        streak_msg = t(lang, "workout_streak", emoji=get_streak_emoji(streak["count"]), count=streak["count"], s=s)
        totals = today_totals(user)
        goals = user["goals"]
        net = goals["calories"] - totals["calories"] + totals["burned"]
        await update.message.reply_text(
            t(lang, "exercise_logged", exercise=exercise_text, cal=calories_burned,
              eaten=totals["calories"], burned=totals["burned"], net=net, streak=streak_msg),
            reply_markup=main_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"Exercise error: {e}")
        await update.message.reply_text(t(lang, "exercise_format_err"))
        return LOG_EXERCISE
    return MAIN_MENU


# ─────────────────────────────────────────────
# WEIGHT LOGGING
# ─────────────────────────────────────────────

async def prompt_log_weight(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    await update.message.reply_text(t(lang, "weight_prompt"))
    return LOG_WEIGHT


async def receive_weight(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    try:
        weight = float(update.message.text.strip())
        user["weights"].append({"date": today(), "weight_kg": weight})
        save_data()
        weights = user["weights"]
        change = ""
        if len(weights) >= 2:
            diff = weight - weights[-2]["weight_kg"]
            arrow = "📉" if diff < 0 else "📈"
            change = t(lang, "weight_change", arrow=arrow, diff=diff)
        await update.message.reply_text(t(lang, "weight_logged", weight=weight, change=change), reply_markup=main_keyboard(lang))
    except ValueError:
        await update.message.reply_text(t(lang, "weight_err"))
        return LOG_WEIGHT
    return MAIN_MENU


# ─────────────────────────────────────────────
# SUMMARIES
# ─────────────────────────────────────────────

async def today_summary(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    meals = today_meals(user)
    exercises = today_exercises(user)
    totals = today_totals(user)
    goals = user["goals"]
    if not meals and not exercises:
        await update.message.reply_text(t(lang, "no_logs"), reply_markup=main_keyboard(lang))
        return MAIN_MENU
    meal_list = "\n".join(f"  • {m['description'][:35]} ({m['calories']} kcal, {m['protein']}g)" for m in meals) if meals else t(lang, "none_yet")
    exercise_list = "\n".join(f"  • {e['description'][:35]} (-{e['calories_burned']} kcal)" for e in exercises) if exercises else t(lang, "none_yet")
    cal_pct = int(totals["calories"] / goals["calories"] * 100) if goals["calories"] else 0
    prot_pct = int(totals["protein"] / goals["protein"] * 100) if goals["protein"] else 0
    net = goals["calories"] - totals["calories"] + totals["burned"]
    ds = user["streaks"]["diet"]
    ws = user["streaks"]["workout"]
    await update.message.reply_text(
        f"{t(lang, 'summary_title', date=today())}\n\n"
        f"{t(lang, 'summary_meals')}\n{meal_list}\n\n"
        f"{t(lang, 'summary_exercise')}\n{exercise_list}\n\n"
        f"{t(lang, 'summary_nutrition')}\n"
        f"  {T[lang].get('btn_log_meal','Calories').split()[1] if lang!='en' else 'Calories'}: {totals['calories']} / {goals['calories']} kcal ({cal_pct}%)\n"
        f"  Protein: {totals['protein']}g / {goals['protein']}g ({prot_pct}%)\n"
        f"  Burned: {totals['burned']} kcal\n"
        f"  Net: {net} kcal\n\n"
        f"{t(lang, 'summary_streaks')}\n"
        f"  {get_streak_emoji(ds['count'])} {t(lang,'healthy_eating')}: {ds['count']}\n"
        f"  {get_streak_emoji(ws['count'])} {t(lang,'working_out')}: {ws['count']}",
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU


async def show_streaks(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    diet = user["streaks"]["diet"]
    workout = user["streaks"]["workout"]
    def bar(count):
        filled = min(count, 7)
        return "🟩" * filled + "⬜" * (7 - filled) + f" {count}"
    await update.message.reply_text(
        f"{t(lang,'streaks_title')}\n\n"
        f"{get_streak_emoji(diet['count'])} {t(lang,'healthy_eating')}\n{bar(diet['count'])}\n\n"
        f"{get_streak_emoji(workout['count'])} {t(lang,'working_out')}\n{bar(workout['count'])}\n\n"
        f"{t(lang,'streaks_tip')}",
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU


async def weight_progress(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    weights = user["weights"][-10:]
    if not weights:
        await update.message.reply_text(t(lang, "no_weight"), reply_markup=main_keyboard(lang))
        return MAIN_MENU
    log_lines = "\n".join(f"  {w['date']}: {w['weight_kg']} kg" for w in weights)
    first, last = weights[0]["weight_kg"], weights[-1]["weight_kg"]
    await update.message.reply_text(
        f"{t(lang,'weight_progress_title')}\n\n{log_lines}\n\n{t(lang,'total_change',diff=last-first)}",
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU


# ─────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────

async def show_profile(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    profile = user.get("profile", {})
    goals = user.get("goals", {"calories": 1300, "protein": 90})
    expiry = user.get("subscription_expiry", "N/A")
    goal_map = T[lang].get("goals_goal_map", {})
    lines = [f"*{t(lang,'profile_title')}*\n"]
    if profile:
        lines.append(t(lang, "profile_info"))
        if profile.get("height"): lines.append(t(lang, "profile_height", h=profile["height"]))
        if profile.get("weight"): lines.append(t(lang, "profile_weight", w=profile["weight"]))
        if profile.get("age"): lines.append(t(lang, "profile_age", age=profile["age"]))
        if profile.get("gender"): lines.append(t(lang, "profile_gender", gender=profile["gender"].capitalize()))
        if profile.get("blood_type"): lines.append(t(lang, "profile_blood", blood=profile["blood_type"]))
        if profile.get("body_type"): lines.append(t(lang, "profile_body", body=profile["body_type"].capitalize()))
        if profile.get("goal"): lines.append(t(lang, "profile_goal", goal=goal_map.get(profile["goal"], profile["goal"])))
        lines.append("")
    lines.append(t(lang, "profile_targets"))
    lines.append(t(lang, "profile_cal", cal=goals["calories"]))
    lines.append(t(lang, "profile_prot", prot=goals["protein"]))
    lines.append("")
    lines.append(t(lang, "profile_sub", expiry=expiry))
    lines.append("")
    lines.append(t(lang, "profile_tip"))
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=main_keyboard(lang))
    return MAIN_MENU


# ─────────────────────────────────────────────
# AI Q&A
# ─────────────────────────────────────────────

async def prompt_question(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    await update.message.reply_text(t(lang, "ask_prompt"))
    return ASK_QUESTION


async def answer_question(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    await update.message.reply_text(t(lang, "thinking"))
    lang_instruction = {"en": "Respond in English.", "zh": "请用中文回答。", "ko": "한국어로 답변해 주세요."}
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=500,
            system=f"You are a friendly nutrition and fitness assistant with expertise in Asian cuisine. Be concise, under 200 words. {lang_instruction[lang]}",
            messages=[{"role": "user", "content": update.message.text}]
        )
        answer = response.content[0].text
    except Exception as e:
        logger.error(f"Q&A error: {e}")
        answer = t(lang, "ai_err")
    await update.message.reply_text(answer, reply_markup=main_keyboard(lang))
    return MAIN_MENU


# ─────────────────────────────────────────────
# RECIPE SEARCH
# ─────────────────────────────────────────────

async def prompt_recipe_search(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    await update.message.reply_text(t(lang, "recipe_prompt"))
    return RECIPE_SEARCH


async def receive_recipe_search(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    query = update.message.text.strip()
    await update.message.reply_text(t(lang, "finding_recipes"))
    lang_instruction = {"en": "Respond in English.", "zh": "请用中文回答。", "ko": "한국어로 답변해 주세요。"}
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=800,
            system=f"You are a nutrition-focused Asian recipe expert. Suggest easy high-protein recipes. Include macros per serving. {lang_instruction[lang]}",
            messages=[{"role": "user", "content": f"Suggest 2 easy high-protein Asian recipes for: '{query}'. Include name, time, macros, ingredients, steps (max 5). Format for Telegram."}]
        )
        answer = response.content[0].text
    except Exception as e:
        logger.error(f"Recipe error: {e}")
        answer = t(lang, "recipe_err")
    await update.message.reply_text(answer, reply_markup=main_keyboard(lang))
    return MAIN_MENU


# ─────────────────────────────────────────────
# GOALS SETTING
# ─────────────────────────────────────────────

async def prompt_set_goals(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    await update.message.reply_text(
        t(lang, "goals_prompt"),
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(t(lang, "btn_manual"))],
            [KeyboardButton(t(lang, "btn_quiz"))],
        ], resize_keyboard=True)
    )
    return SET_GOALS_MANUAL


async def receive_goals_choice(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text
    if any(x in text for x in ["manual", "manually", "手动", "직접", "✏️"]):
        await update.message.reply_text(t(lang, "manual_prompt"))
        return MANUAL_INPUT
    else:
        await update.message.reply_text(t(lang, "quiz_height"))
        return QUIZ_HEIGHT


async def receive_manual_goals(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    try:
        parts = update.message.text.strip().split()
        cal, prot = int(parts[0]), int(parts[1])
        if cal < 500 or cal > 5000 or prot < 10 or prot > 400:
            raise ValueError
        user["goals"] = {"calories": cal, "protein": prot}
        save_data()
        await update.message.reply_text(t(lang, "goals_saved", cal=cal, prot=prot), reply_markup=main_keyboard(lang))
        return MAIN_MENU
    except Exception:
        await update.message.reply_text(t(lang, "goals_err"))
        return MANUAL_INPUT


# ─────────────────────────────────────────────
# GOALS QUIZ
# ─────────────────────────────────────────────

async def quiz_height(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    try:
        h = float(update.message.text.strip())
        if h < 100 or h > 250: raise ValueError
        context.user_data["quiz_height"] = h
        await update.message.reply_text(t(lang, "quiz_weight_q", h=h))
        return QUIZ_WEIGHT
    except Exception:
        await update.message.reply_text(t(lang, "quiz_height_err"))
        return QUIZ_HEIGHT


async def quiz_weight(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    try:
        w = float(update.message.text.strip())
        if w < 20 or w > 300: raise ValueError
        context.user_data["quiz_weight"] = w
        await update.message.reply_text(t(lang, "quiz_age_q", w=w))
        return QUIZ_AGE
    except Exception:
        await update.message.reply_text(t(lang, "quiz_weight_err"))
        return QUIZ_WEIGHT


async def quiz_age(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    try:
        age = int(update.message.text.strip())
        if age < 10 or age > 100: raise ValueError
        context.user_data["quiz_age"] = age
        await update.message.reply_text(
            t(lang, "quiz_gender_q"),
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(t(lang,"btn_female")), KeyboardButton(t(lang,"btn_male"))]], resize_keyboard=True)
        )
        return QUIZ_GENDER
    except Exception:
        await update.message.reply_text(t(lang, "quiz_age_err"))
        return QUIZ_AGE


async def quiz_gender(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text.lower()
    if any(x in text for x in ["female", "女", "여성", "f"]):
        context.user_data["quiz_gender"] = "female"
    elif any(x in text for x in ["male", "男", "남성", "m"]):
        context.user_data["quiz_gender"] = "male"
    else:
        await update.message.reply_text(t(lang, "quiz_gender_err"))
        return QUIZ_GENDER
    await update.message.reply_text(
        t(lang, "quiz_activity_q"),
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(t(lang,"btn_sedentary"))],
            [KeyboardButton(t(lang,"btn_light"))],
            [KeyboardButton(t(lang,"btn_moderate"))],
            [KeyboardButton(t(lang,"btn_very"))],
        ], resize_keyboard=True)
    )
    return QUIZ_ACTIVITY


async def quiz_activity(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text.lower()
    if any(x in text for x in ["sedentary","久坐","비활동","🛋"]):
        context.user_data["quiz_activity"] = 1.2
    elif any(x in text for x in ["lightly","light","轻度","가볍","🚶"]):
        context.user_data["quiz_activity"] = 1.375
    elif any(x in text for x in ["moderately","moderate","中度","보통","🏃"]):
        context.user_data["quiz_activity"] = 1.55
    elif any(x in text for x in ["very","非常","매우","💪"]):
        context.user_data["quiz_activity"] = 1.725
    else:
        await update.message.reply_text(t(lang, "quiz_activity_err"))
        return QUIZ_ACTIVITY
    await update.message.reply_text(
        t(lang, "quiz_goal_q"),
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(t(lang,"btn_lose"))],
            [KeyboardButton(t(lang,"btn_build"))],
            [KeyboardButton(t(lang,"btn_maintain"))],
        ], resize_keyboard=True)
    )
    return QUIZ_GOAL


async def quiz_goal(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text.lower()
    if any(x in text for x in ["lose","减肥","감량","🔥"]):
        context.user_data["quiz_goal"] = "lose"
    elif any(x in text for x in ["build","muscle","增肌","근육","💪"]):
        context.user_data["quiz_goal"] = "build"
    else:
        context.user_data["quiz_goal"] = "maintain"
    await update.message.reply_text(
        t(lang, "quiz_body_q"),
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(t(lang,"btn_ecto"))],
            [KeyboardButton(t(lang,"btn_meso"))],
            [KeyboardButton(t(lang,"btn_endo"))],
        ], resize_keyboard=True)
    )
    return QUIZ_BODY


async def quiz_body(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text.lower()
    if any(x in text for x in ["ecto","外胚","외배"]):
        context.user_data["quiz_body"] = "ectomorph"
    elif any(x in text for x in ["meso","中胚","중배"]):
        context.user_data["quiz_body"] = "mesomorph"
    else:
        context.user_data["quiz_body"] = "endomorph"
    await update.message.reply_text(
        t(lang, "quiz_blood_q"),
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(t(lang,"btn_blood_a")), KeyboardButton(t(lang,"btn_blood_b"))],
            [KeyboardButton(t(lang,"btn_blood_ab")), KeyboardButton(t(lang,"btn_blood_o"))],
            [KeyboardButton(t(lang,"btn_blood_unknown"))],
        ], resize_keyboard=True)
    )
    return QUIZ_BLOOD


async def quiz_blood(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text.upper()
    if "AB" in text:
        blood = "AB"
    elif "A" in text and "B" not in text:
        blood = "A"
    elif "B" in text and "A" not in text:
        blood = "B"
    elif "O" in text:
        blood = "O"
    else:
        blood = "unknown"

    h = context.user_data["quiz_height"]
    w = context.user_data["quiz_weight"]
    age = context.user_data["quiz_age"]
    gender = context.user_data["quiz_gender"]
    activity = context.user_data["quiz_activity"]
    goal = context.user_data["quiz_goal"]
    body = context.user_data["quiz_body"]

    if gender == "female":
        bmr = 10 * w + 6.25 * h - 5 * age - 161
    else:
        bmr = 10 * w + 6.25 * h - 5 * age + 5
    tdee = bmr * activity

    if goal == "lose": calories = int(tdee - 400)
    elif goal == "build": calories = int(tdee + 200)
    else: calories = int(tdee)
    if body == "ectomorph": calories += 100
    elif body == "endomorph": calories -= 50

    if goal == "build": protein = int(w * 2.0)
    elif goal == "lose": protein = int(w * 1.8)
    else: protein = int(w * 1.6)

    user["goals"] = {"calories": calories, "protein": protein}
    user["profile"] = {
        "height": h, "weight": w, "age": age, "gender": gender,
        "activity": activity, "goal": goal, "body_type": body, "blood_type": blood
    }
    save_data()

    blood_note = T[lang]["blood_notes"].get(blood, T[lang]["blood_notes"]["unknown"])
    goal_map = T[lang].get("goals_goal_map", {})
    user["onboarded"] = True
    context.user_data["onboarding"] = False
    save_data()
    await update.message.reply_text(
        t(lang, "quiz_result", h=h, w=w, age=age,
          goal=goal_map.get(goal, goal), body=body.capitalize(),
          cal=calories, prot=protein, blood_note=blood_note),
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU


# ─────────────────────────────────────────────
# REMINDERS
# ─────────────────────────────────────────────

async def send_morning_reminder(context):
    chat_id = context.job.chat_id
    user = get_user(chat_id)
    lang = get_lang(user)
    msgs = {
        "en": "☀️ Good morning! Ready to crush your goals today? 💪\n\nLog your breakfast and workout to keep those streaks alive! 🔥\n\nHow are you feeling today? Reply anytime to chat with me! 😊",
        "zh": "☀️ 早安！准备好实现今天的目标了吗？💪\n\n记录早餐和运动，保持连续记录！🔥\n\n今天感觉怎么样？随时回复和我聊聊！😊",
        "ko": "☀️ 좋은 아침입니다! 오늘의 목표를 달성할 준비가 되셨나요? 💪\n\n아침 식사와 운동을 기록해 연속 기록을 유지하세요! 🔥\n\n오늘 기분은 어떠세요? 언제든지 저에게 답장하세요! 😊",
    }
    lang = get_lang(user)
    await context.bot.send_message(chat_id=chat_id, text=msgs.get(lang, msgs["en"]))


async def send_evening_reminder(context):
    chat_id = context.job.chat_id
    user = get_user(chat_id)
    lang = get_lang(user)
    totals = today_totals(user)
    goals = user["goals"]
    net = goals["calories"] - totals["calories"] + totals["burned"]
    if lang == "zh":
        msg = f"🌙 晚间回顾！\n\n摄入：{totals['calories']} 千卡\n消耗：{totals['burned']} 千卡\n净剩余：{net} 千卡\n\n🔥 饮食连续：{user['streaks']['diet']['count']} 天\n🔥 运动连续：{user['streaks']['workout']['count']} 天\n\n在午夜前记录，保持连续！🌟"
    elif lang == "ko":
        msg = f"🌙 저녁 체크인!\n\n섭취: {totals['calories']} kcal\n소모: {totals['burned']} kcal\n순 남은: {net} kcal\n\n🔥 식단 연속: {user['streaks']['diet']['count']}일\n🔥 운동 연속: {user['streaks']['workout']['count']}일\n\n자정 전에 기록해 연속을 유지하세요! 🌟"
    else:
        msg = f"🌙 Evening check-in!\n\nEaten: {totals['calories']} kcal\nBurned: {totals['burned']} kcal\nNet remaining: {net} kcal\n\n🔥 Diet streak: {user['streaks']['diet']['count']} days\n🔥 Workout streak: {user['streaks']['workout']['count']} days\n\nLog before midnight to keep your streaks! 🌟"
    invites = {
        "en": "\n\nHow did today go? Reply to chat! 💬",
        "zh": "\n\n今天过得怎么样？回复我聊聊！💬",
        "ko": "\n\n오늘 하루 어떠셨나요? 답장해 주세요! 💬",
    }
    await context.bot.send_message(chat_id=chat_id, text=msg + invites.get(lang, invites["en"]))


async def setup_reminders(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    chat_id = update.effective_chat.id
    for job in context.job_queue.get_jobs_by_name(str(chat_id)):
        job.schedule_removal()
    context.job_queue.run_daily(send_morning_reminder, time=time(hour=8, minute=0), chat_id=chat_id, name=str(chat_id))
    context.job_queue.run_daily(send_evening_reminder, time=time(hour=20, minute=0), chat_id=chat_id, name=str(chat_id))
    await update.message.reply_text(t(lang, "reminders_set"), reply_markup=main_keyboard(lang))
    return MAIN_MENU




# ─────────────────────────────────────────────
# ADMIN: EXPIRE SUBSCRIPTION
# ─────────────────────────────────────────────

async def admin_expire(update, context):
    """Usage: /expire <user_id>"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    try:
        target_id = int(context.args[0])
        if target_id not in user_data_store:
            await update.message.reply_text(f"❌ User {target_id} not found.")
            return
        user_data_store[target_id]["subscription_expiry"] = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        save_data()
        await update.message.reply_text(f"✅ Subscription for user {target_id} has been expired immediately.\n\nThey will be locked out on their next message.")
    except Exception as e:
        await update.message.reply_text(f"Usage: /expire <user_id>\n\nGet user IDs with /subscribers\n\nError: {e}")


# ─────────────────────────────────────────────
# DIET & EXERCISE PLAN
# ─────────────────────────────────────────────

async def prompt_plan(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    await update.message.reply_text(t(lang, "plan_prompt"))
    return PLAN_GOAL


async def receive_plan_goal(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    goal_text = update.message.text.strip()
    profile = user.get("profile", {})
    goals = user.get("goals", {"calories": 1300, "protein": 90})
    await update.message.reply_text(t(lang, "plan_generating"))
    lang_instruction = {"en": "Respond in English.", "zh": "请用中文回答。", "ko": "한국어로 답변해 주세요。"}
    profile_info = ""
    if profile:
        profile_info = (
            f"User profile: {profile.get('gender','')}, age {profile.get('age','')}, "
            f"height {profile.get('height','')}cm, weight {profile.get('weight','')}kg, "
            f"goal: {profile.get('goal','')}, body type: {profile.get('body_type','')}, "
            f"blood type: {profile.get('blood_type','')}. "
            f"Daily targets: {goals['calories']} kcal, {goals['protein']}g protein. "
        )
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1000,
            system=(
                f"You are an expert personal trainer and nutritionist specialising in Asian diet and lifestyle. "
                f"Create comprehensive, practical, and motivating plans. "
                f"Format clearly for Telegram with emojis and sections. "
                f"{lang_instruction[lang]}"
            ),
            messages=[{"role": "user", "content": (
                f"Create a personalised diet and exercise plan for this goal: '{goal_text}'. "
                f"{profile_info}"
                f"Include:\n"
                f"1. Weekly exercise schedule (specific days and workouts)\n"
                f"2. Daily meal plan example (breakfast, lunch, dinner, snacks)\n"
                f"3. Key tips for achieving the goal\n"
                f"4. Estimated timeline to reach the goal\n"
                f"Keep it practical, realistic and encouraging."
            )}]
        )
        plan = response.content[0].text
    except Exception as e:
        logger.error(f"Plan error: {e}")
        plan = t(lang, "plan_err")
    await update.message.reply_text(plan, reply_markup=main_keyboard(lang))
    return MAIN_MENU


# ─────────────────────────────────────────────
# ENHANCED WORKOUT WITH MUSCLE GROUPS & YOUTUBE
# ─────────────────────────────────────────────

YOUTUBE_QUERIES = {
    "🧘 Yoga": "beginner yoga workout",
    "🩰 Pilates": "pilates workout for beginners",
    "🚴 Spin / Cycling": "indoor cycling spin workout",
    "🏃 Cardio": "cardio workout at home",
    "🥊 HIIT": "HIIT workout beginner",
    "🤸 Calisthenics": "calisthenics beginner workout",
    "🏊 Swimming": "swimming workout technique",
}

async def prompt_workout(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    await update.message.reply_text(
        t(lang, "workout_type_q"),
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(t(lang,"btn_yoga")), KeyboardButton(t(lang,"btn_pilates"))],
            [KeyboardButton(t(lang,"btn_spin")), KeyboardButton(t(lang,"btn_cardio"))],
            [KeyboardButton(t(lang,"btn_weights")), KeyboardButton(t(lang,"btn_hiit"))],
            [KeyboardButton(t(lang,"btn_calisthenics")), KeyboardButton(t(lang,"btn_swimming"))],
            [KeyboardButton(t(lang,"btn_other_exercise"))],
        ], resize_keyboard=True)
    )
    return WORKOUT_TYPE


async def receive_workout_type(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    workout_text = update.message.text
    context.user_data["workout_type"] = workout_text

    # If weights, ask muscle group
    if any(x in workout_text for x in ["Weights","举重","웨이트","🏋️"]) and "Whole" not in workout_text:
        await update.message.reply_text(
            t(lang, "muscle_prompt"),
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton(t(lang,"btn_arms")), KeyboardButton(t(lang,"btn_chest"))],
                [KeyboardButton(t(lang,"btn_back")), KeyboardButton(t(lang,"btn_legs"))],
                [KeyboardButton(t(lang,"btn_whole_body"))],
            ], resize_keyboard=True)
        )
        return WORKOUT_MUSCLE

    # If other, ask them to type
    if any(x in workout_text for x in ["Other","其他","기타","✍️"]):
        await update.message.reply_text("Tell me what exercise you want a plan for! 💪")
        return WORKOUT_MUSCLE

    # Otherwise go straight to plan type
    await update.message.reply_text(
        t(lang, "workout_plan_q"),
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(t(lang,"btn_weekly"))],
            [KeyboardButton(t(lang,"btn_single"))],
        ], resize_keyboard=True)
    )
    return WORKOUT_PLAN_TYPE


async def receive_workout_muscle(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    muscle = update.message.text
    base = context.user_data.get("workout_type", "weights")
    context.user_data["workout_type"] = f"{base} — {muscle}"
    await update.message.reply_text(
        t(lang, "workout_plan_q"),
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(t(lang,"btn_weekly"))],
            [KeyboardButton(t(lang,"btn_single"))],
        ], resize_keyboard=True)
    )
    return WORKOUT_PLAN_TYPE


async def receive_workout_plan_type(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    plan_text = update.message.text
    workout_type = context.user_data.get("workout_type", "general fitness")
    profile = user.get("profile", {})
    is_weekly = any(x in plan_text for x in ["weekly","周","주간","📅"])
    plan_word = "full 7-day weekly routine" if is_weekly else "single session workout plan"
    lang_instruction = {"en": "Respond in English.", "zh": "请用中文回答。", "ko": "한국어로 답변해 주세요。"}
    profile_info = ""
    if profile:
        profile_info = (
            f"User: {profile.get('gender','')}, age {profile.get('age','')}, "
            f"height {profile.get('height','')}cm, weight {profile.get('weight','')}kg, "
            f"goal: {profile.get('goal','')}, body type: {profile.get('body_type','')}. "
        )
    await update.message.reply_text(t(lang, "workout_generating"))
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=900,
            system=f"You are a professional fitness coach. Create practical safe workout plans. Include warm-up, main workout, cool-down. Use emojis and format for Telegram. {lang_instruction[lang]}",
            messages=[{"role": "user", "content": f"Create a {plan_word} for {workout_type}. {profile_info}Include sets, reps or duration. Beginner-to-intermediate friendly."}]
        )
        plan = response.content[0].text
    except Exception as e:
        logger.error(f"Workout error: {e}")
        plan = t(lang, "workout_err")

    # Add YouTube tip for non-weights workouts
    youtube_tip = ""
    for key, query in YOUTUBE_QUERIES.items():
        if key.split()[1].lower() in workout_type.lower():
            youtube_tip = t(lang, "youtube_tip") + f'"{query}"'
            break

    await update.message.reply_text(plan + youtube_tip, reply_markup=main_keyboard(lang))
    return MAIN_MENU


# ─────────────────────────────────────────────
# CHAT MODE
# ─────────────────────────────────────────────

async def prompt_chat(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    context.user_data["chat_history"] = []
    await update.message.reply_text(
        t(lang, "chat_prompt"),
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🏠 Main Menu")]], resize_keyboard=True)
    )
    return CHAT_MODE


async def receive_chat(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    message = update.message.text

    if any(x in message for x in ["Main Menu", "主菜单", "메인 메뉴", "🏠"]):
        await update.message.reply_text(t(lang, "chat_exit"), reply_markup=main_keyboard(lang))
        context.user_data["chat_history"] = []
        return MAIN_MENU

    history = context.user_data.get("chat_history", [])
    history.append({"role": "user", "content": message})
    if len(history) > 10:
        history = history[-10:]

    lang_instruction = {"en": "Respond in English.", "zh": "请用中文回答。", "ko": "한국어로 답변해 주세요。"}
    profile = user.get("profile", {})
    profile_context = ""
    if profile:
        profile_context = f"User info: {profile.get('gender','')}, age {profile.get('age','')}, goal: {profile.get('goal','')}. "

    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=400,
            system=(
                f"You are a warm, friendly, supportive wellness companion named Michi. "
                f"You care about the user's wellbeing, diet, fitness, and mental health. "
                f"You can chat casually about their day, give encouragement, and answer health questions. "
                f"Keep responses conversational and under 150 words. {profile_context}"
                f"{lang_instruction[lang]}"
            ),
            messages=history
        )
        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})
        context.user_data["chat_history"] = history
    except Exception as e:
        logger.error(f"Chat error: {e}")
        reply = t(lang, "ai_err")

    await update.message.reply_text(reply)
    return CHAT_MODE


# ─────────────────────────────────────────────
# VOICE MESSAGES
# ─────────────────────────────────────────────

async def receive_voice(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU

    await update.message.reply_text(t(lang, "voice_processing"))
    try:
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)
        voice_bytes = await voice_file.download_as_bytearray()
        audio_b64 = base64.b64encode(voice_bytes).decode("utf-8")

        lang_instruction = {"en": "The user spoke in English. Respond in English.", "zh": "用户用中文说话。请用中文回答。", "ko": "사용자가 한국어로 말했습니다. 한국어로 답변해 주세요。"}
        profile = user.get("profile", {})
        profile_context = f"User profile: {profile.get('gender','')}, age {profile.get('age','')}, goal: {profile.get('goal','')}. " if profile else ""

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=500,
            system=(
                f"You are a friendly nutrition and fitness assistant named Michi. "
                f"The user has sent a voice message. Listen carefully and respond helpfully. "
                f"Keep responses concise and practical. {profile_context}{lang_instruction[lang]}"
            ),
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "Please listen to this voice message and respond appropriately:"},
                {"type": "document", "source": {"type": "base64", "media_type": "audio/ogg", "data": audio_b64}}
            ]}]
        )
        reply = response.content[0].text
    except Exception as e:
        logger.error(f"Voice error: {e}")
        reply = t(lang, "voice_err")

    await update.message.reply_text(reply, reply_markup=main_keyboard(lang))
    return MAIN_MENU


# ─────────────────────────────────────────────
# PERIOD TRACKER
# ─────────────────────────────────────────────

import random as _random

async def prompt_period_menu(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    await update.message.reply_text(
        t(lang, "period_menu_prompt"),
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(t(lang, "btn_log_period"))],
            [KeyboardButton(t(lang, "btn_period_symptoms"))],
            [KeyboardButton(t(lang, "btn_period_history"))],
            [KeyboardButton("🏠 " + ("Main Menu" if lang=="en" else "主菜单" if lang=="zh" else "메인 메뉴"))],
        ], resize_keyboard=True)
    )
    return PERIOD_LOG


async def receive_period_menu(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text

    if t(lang, "btn_log_period") in text:
        await update.message.reply_text(t(lang, "period_start_prompt"))
        return PERIOD_CYCLE

    if t(lang, "btn_period_symptoms") in text:
        await update.message.reply_text(t(lang, "period_symptoms_prompt"))
        return PERIOD_SYMPTOMS

    if t(lang, "btn_period_history") in text:
        logs = user.get("period_logs", [])
        if not logs:
            await update.message.reply_text(t(lang, "period_history_empty"), reply_markup=main_keyboard(lang))
            return MAIN_MENU
        lines = "\n".join(f"  🌸 {l['date']} (cycle: {l.get('cycle_length', '?')} days)" for l in logs[-6:])
        prediction = ""
        if len(logs) >= 2:
            from datetime import datetime as dt, timedelta as td
            last = dt.strptime(logs[-1]["date"], "%Y-%m-%d")
            cycle = user.get("cycle_length", 28)
            next_date = (last + td(days=cycle)).strftime("%Y-%m-%d")
            prediction = t(lang, "period_prediction", date=next_date)
        await update.message.reply_text(
            t(lang, "period_history_title") + lines + prediction,
            reply_markup=main_keyboard(lang)
        )
        return MAIN_MENU

    # Back to main menu
    await update.message.reply_text("👍", reply_markup=main_keyboard(lang))
    return MAIN_MENU


async def receive_period_date(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text.strip().lower()

    if any(x in text for x in ["today", "今天", "오늘"]):
        date_str = today()
    else:
        try:
            from datetime import datetime as dt
            dt.strptime(text, "%Y-%m-%d")
            date_str = text
        except Exception:
            await update.message.reply_text("Please enter a valid date (YYYY-MM-DD) or say 'today'")
            return PERIOD_CYCLE

    tips = t(lang, "period_tips")
    tip = tips[_random.randint(0, len(tips)-1)]

    if "period_logs" not in user:
        user["period_logs"] = []
    user["period_logs"].append({"date": date_str, "cycle_length": user.get("cycle_length", 28)})
    save_data()

    await update.message.reply_text(
        t(lang, "period_logged", date=date_str, tip=tip),
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU


async def receive_period_symptoms(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    symptoms = update.message.text.strip()

    lang_instruction = {"en": "Respond in English.", "zh": "请用中文回答。", "ko": "한국어로 답변해 주세요。"}

    # Get cycle day if available
    cycle_context = ""
    logs = user.get("period_logs", [])
    if logs:
        from datetime import datetime as dt
        last = dt.strptime(logs[-1]["date"], "%Y-%m-%d")
        day = (dt.now() - last).days + 1
        cycle_context = f"The user is on day {day} of their menstrual cycle. "

    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=400,
            system=(
                f"You are a warm, knowledgeable women\'s health companion. "
                f"Provide empathetic, evidence-based advice for menstrual symptoms. "
                f"Normalise symptoms and offer practical tips (food, movement, self-care). "
                f"Always remind them it\'s okay to rest. {cycle_context}"
                f"{lang_instruction[lang]}"
            ),
            messages=[{"role": "user", "content": f"I have these period symptoms: {symptoms}. Please give me personalised advice and reassurance."}]
        )
        advice = response.content[0].text
    except Exception as e:
        logger.error(f"Period symptoms error: {e}")
        advice = t(lang, "ai_err")

    await update.message.reply_text(
        f"{t(lang, 'period_symptom_response')}\n\n{advice}",
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU


async def send_period_reminder(context):
    """Daily job to check for upcoming periods and send reminders."""
    from datetime import datetime as dt, timedelta as td
    for uid, user in user_data_store.items():
        logs = user.get("period_logs", [])
        if not logs:
            continue
        lang = user.get("language", "en")
        last = dt.strptime(logs[-1]["date"], "%Y-%m-%d")
        cycle = user.get("cycle_length", 28)
        next_period = last + td(days=cycle)
        days_until = (next_period - dt.now()).days

        if days_until == 3:
            msgs = {
                "en": f"🌸 Hey! Your period is expected in about 3 days ({next_period.strftime('%Y-%m-%d')}).\n\nHow are you feeling? Any PMS symptoms starting? I\'m here if you want to chat or need advice on what to eat or how to move this week 💕\n\n• Stock up on magnesium-rich snacks (bananas, dark choc 🍫)\n• Prepare a hot water bottle\n• Be gentle with yourself this week",
                "zh": f"🌸 嗨！你的生理期预计在约3天后到来（{next_period.strftime('%Y-%m-%d')}）。\n\n你感觉怎么样？有经前综合征的症状了吗？如果你想聊聊或需要饮食建议，我在这里 💕\n\n• 准备富含镁的零食（香蕉、黑巧克力 🍫）\n• 准备热水袋\n• 这周要对自己温柔一点",
                "ko": f"🌸 안녕하세요! 생리 예정일이 약 3일 후입니다 ({next_period.strftime('%Y-%m-%d')}).\n\n지금 어떠세요? PMS 증상이 시작됐나요? 이야기하고 싶거나 식단 조언이 필요하면 언제든 말해주세요 💕\n\n• 마그네슘이 풍부한 간식 준비 (바나나, 다크초콜릿 🍫)\n• 핫팩을 준비하세요\n• 이번 주는 자신에게 부드럽게 대하세요",
            }
            try:
                await context.bot.send_message(chat_id=uid, text=msgs.get(lang, msgs["en"]))
            except Exception:
                pass



async def my_dashboard(update, context):
    """Send the user their dashboard login credentials."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    lang = get_lang(user)

    if not check_access(user_id) and not is_admin(user_id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return

    dash_password = user.get("dashboard_password")
    expiry = user.get("subscription_expiry", "N/A")

    if not dash_password:
        msgs = {
            "en": "You don\'t have dashboard credentials yet. Redeem your access code first with /redeem!",
            "zh": "你还没有仪表盘登录信息。请先用 /redeem 兑换访问码！",
            "ko": "아직 대시보드 로그인 정보가 없습니다. 먼저 /redeem 으로 액세스 코드를 입력하세요!",
        }
        await update.message.reply_text(msgs.get(lang, msgs["en"]))
        return

    dashboard_msgs = {
        "en": (
            f"🔐 *Your Dashboard Login*\n\n"
            f"🆔 Telegram ID: `{user_id}`\n"
            f"🔑 Password: `{dash_password}`\n"
            f"📅 Valid until: {expiry}\n\n"
            + (f"📊 Dashboard: {DASHBOARD_URL}\n\n" if DASHBOARD_URL else "") +
            f"➡️ Forward this to your Saved Messages to keep it safe!"
        ),
        "zh": (
            f"🔐 *你的仪表盘登录信息*\n\n"
            f"🆔 Telegram ID: `{user_id}`\n"
            f"🔑 密码: `{dash_password}`\n"
            f"📅 有效期至: {expiry}\n\n"
            f"➡️ 转发到收藏消息保存！"
        ),
        "ko": (
            f"🔐 *대시보드 로그인 정보*\n\n"
            f"🆔 Telegram ID: `{user_id}`\n"
            f"🔑 비밀번호: `{dash_password}`\n"
            f"📅 유효 기간: {expiry}까지\n\n"
            f"➡️ 저장된 메시지로 전달해 안전하게 보관하세요!"
        ),
    }
    await update.message.reply_text(
        dashboard_msgs.get(lang, dashboard_msgs["en"]),
        parse_mode="Markdown"
    )



# ─────────────────────────────────────────────
# QUICK LOG
# ─────────────────────────────────────────────

async def receive_quick_save_name(update, context):
    """Receive name for saving a quick meal, or skip."""
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text.strip()
    pending = context.user_data.pop("pending_quick_save", None)

    if any(x in text for x in ["Skip", "跳过", "건너뛰기"]) or not pending:
        await update.message.reply_text("👍", reply_markup=main_keyboard(lang))
        return MAIN_MENU

    name = text[:40]
    if "quick_meals" not in user:
        user["quick_meals"] = []
    # Avoid duplicate names
    user["quick_meals"] = [m for m in user["quick_meals"] if m["name"].lower() != name.lower()]
    user["quick_meals"].append({"name": name, **{k: pending[k] for k in ["calories","protein","carbs","fat"]}})
    save_data()
    await update.message.reply_text(
        t(lang, "quick_log_saved", name=name),
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU


async def prompt_quick_log(update, context):
    """Show saved quick meals as buttons."""
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    quick_meals = user.get("quick_meals", [])
    if not quick_meals:
        await update.message.reply_text(t(lang, "quick_log_empty"), parse_mode="Markdown", reply_markup=main_keyboard(lang))
        return MAIN_MENU
    # Build keyboard of meal names
    rows = [[KeyboardButton(m["name"])] for m in quick_meals]
    rows.append([KeyboardButton("🏠 " + ("Main Menu" if lang=="en" else "主菜单" if lang=="zh" else "메인 메뉴"))])
    meal_lines = "\n".join(
        f"  • {m['name']} — {m['calories']} kcal, {m['protein']}g prot"
        for m in quick_meals
    )
    await update.message.reply_text(
        t(lang, "quick_log_menu") + "\n\n" + meal_lines + "\n\nTap a meal to log it instantly!",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True)
    )
    return MAIN_MENU


async def receive_quick_log_selection(update, context):
    """Log the selected quick meal instantly."""
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text.strip()

    if any(x in text for x in ["Main Menu", "主菜单", "메인 메뉴", "🏠"]):
        await update.message.reply_text("👍", reply_markup=main_keyboard(lang))
        return MAIN_MENU

    quick_meals = user.get("quick_meals", [])
    meal = next((m for m in quick_meals if m["name"].lower() == text.lower()), None)
    if not meal:
        await update.message.reply_text("❓ Meal not found. Tap a button from the list!", reply_markup=main_keyboard(lang))
        return MAIN_MENU

    user["meals"].append({"date": today(), "description": meal["name"], **{k: meal[k] for k in ["calories","protein","carbs","fat"]}})
    update_streak(user, "diet")
    save_data()
    totals = today_totals(user)
    goals = user["goals"]
    net = goals["calories"] - totals["calories"] + totals["burned"]
    await update.message.reply_text(
        t(lang, "quick_log_logged",
          name=meal["name"], cal=meal["calories"], prot=meal["protein"],
          carbs=meal["carbs"], fat=meal["fat"], net=net),
        parse_mode="Markdown",
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU


# ─────────────────────────────────────────────
# APPLE HEALTH / CSV EXPORT
# ─────────────────────────────────────────────

async def export_apple_health(update, context):
    """Generate a CSV export of all meal and weight data."""
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU

    meals = user.get("meals", [])
    weights = user.get("weights", [])

    await update.message.reply_text(
        t(lang, "apple_health_intro", count=len(meals), weight_count=len(weights)),
        parse_mode="Markdown"
    )

    # Build CSV content
    lines = ["Date,Meal,Calories,Protein(g),Carbs(g),Fat(g)"]
    for m in meals:
        desc = m.get("description","").replace(",","")[:50]
        lines.append(f"{m.get('date','')},{desc},{m.get('calories',0)},{m.get('protein',0)},{m.get('carbs',0)},{m.get('fat',0)}")

    lines.append("")
    lines.append("Date,Weight(kg)")
    for w in weights:
        lines.append(f"{w.get('date','')},{w.get('weight_kg','')}")

    csv_text = "\n".join(lines)

    # Send as a document
    try:
        import io
        bio = io.BytesIO(csv_text.encode("utf-8"))
        bio.name = f"mich_diet_export_{today()}.csv"
        bio.seek(0)
        export_msgs = {
            "en": f"✅ Your data export is ready! ({len(meals)} meals, {len(weights)} weight logs)\n\n📲 *How to import to Apple Health:*\n1. Save the file to your iPhone\n2. Open Health app → Browse → Nutrition\n3. Use a third-party app like MyFitnessPal or Cronometer to import CSV\n\nOr open in Numbers/Excel to view your full history!",
            "zh": f"✅ 数据导出完成！（{len(meals)}条餐食，{len(weights)}条体重记录）\n\n📲 *如何导入Apple健康：*\n1. 将文件保存到iPhone\n2. 打开健康应用\n3. 使用MyFitnessPal等第三方应用导入CSV",
            "ko": f"✅ 데이터 내보내기 완료! ({len(meals)}개 식사, {len(weights)}개 체중 기록)\n\n📲 *Apple Health 가져오기:*\n1. iPhone에 파일 저장\n2. 건강 앱 열기\n3. MyFitnessPal 등으로 CSV 가져오기",
        }
        await update.message.reply_document(
            document=bio,
            filename=f"mich_diet_export_{today()}.csv",
            caption=export_msgs.get(lang, export_msgs["en"]),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Export error: {e}")
        # Fallback — send as text chunk
        chunks = [csv_text[i:i+3000] for i in range(0, len(csv_text), 3000)]
        await update.message.reply_text(t(lang, "apple_health_ready") + chunks[0])

    return MAIN_MENU


# ─────────────────────────────────────────────
# ONBOARDING
# ─────────────────────────────────────────────

async def receive_onboard_choice(update, context):
    """Handle the onboarding yes/skip choice."""
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text

    if any(x in text for x in ["✅", "Let", "开始", "시작"]):
        # Launch the quiz
        await update.message.reply_text(t(lang, "quiz_height"))
        return QUIZ_HEIGHT
    else:
        # Skip — mark onboarded so we don't ask again
        user["onboarded"] = True
        save_data()
        await update.message.reply_text(
            "No worries! You can always set your goals later via 🎯 Set My Goals.",
            reply_markup=main_keyboard(lang)
        )
        return MAIN_MENU


# ─────────────────────────────────────────────
# MEAL SHORTCUTS
# ─────────────────────────────────────────────

async def prompt_shortcuts(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU

    shortcuts = user.get("shortcuts", [])
    if shortcuts:
        sc_list = "\n".join(f"  ⚡ *{sc['name']}* — {sc['calories']} kcal · {sc['protein']}g prot" for sc in shortcuts)
    else:
        sc_list = t(lang, "shortcuts_empty")

    await update.message.reply_text(
        t(lang, "shortcuts_menu") + "\n\n" + sc_list,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(t(lang, "btn_add_shortcut"))],
            [KeyboardButton(t(lang, "btn_use_shortcut"))],
            [KeyboardButton("🏠 " + ("Main Menu" if lang=="en" else "主菜单" if lang=="zh" else "메인 메뉴"))],
        ], resize_keyboard=True)
    )
    return SHORTCUT_MENU


async def receive_shortcut_menu(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text

    if any(x in text for x in ["Main Menu", "主菜单", "메인 메뉴", "🏠"]):
        await update.message.reply_text("👍", reply_markup=main_keyboard(lang))
        return MAIN_MENU

    if t(lang, "btn_add_shortcut") in text or "➕" in text:
        await update.message.reply_text(t(lang, "shortcut_name_prompt"))
        return SHORTCUT_NAME

    if t(lang, "btn_use_shortcut") in text or "🍱" in text:
        shortcuts = user.get("shortcuts", [])
        if not shortcuts:
            await update.message.reply_text(t(lang, "shortcut_none_yet"), reply_markup=main_keyboard(lang))
            return MAIN_MENU
        # Show shortcuts as buttons
        rows = [[KeyboardButton(sc["name"])] for sc in shortcuts]
        rows.append([KeyboardButton("🏠 " + ("Main Menu" if lang=="en" else "主菜单" if lang=="zh" else "메인 메뉴"))])
        await update.message.reply_text(
            t(lang, "shortcut_log_prompt"),
            reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True)
        )
        context.user_data["logging_shortcut"] = True
        return SHORTCUT_MACROS

    return await prompt_shortcuts(update, context)


async def receive_shortcut_name(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    name = update.message.text.strip()
    context.user_data["shortcut_name"] = name
    await update.message.reply_text(
        t(lang, "shortcut_macros_prompt", name=name),
        parse_mode="Markdown"
    )
    return SHORTCUT_MACROS


async def receive_shortcut_macros(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text.strip()

    # If in logging mode — find the shortcut by name and log it
    if context.user_data.get("logging_shortcut"):
        if any(x in text for x in ["Main Menu", "主菜单", "메인 메뉴", "🏠"]):
            context.user_data.pop("logging_shortcut", None)
            await update.message.reply_text("👍", reply_markup=main_keyboard(lang))
            return MAIN_MENU

        shortcuts = user.get("shortcuts", [])
        sc = next((s for s in shortcuts if s["name"].lower() == text.lower()), None)
        if not sc:
            # Try partial match
            sc = next((s for s in shortcuts if text.lower() in s["name"].lower()), None)
        if not sc:
            await update.message.reply_text("Shortcut not found. Please tap one of the buttons above!")
            return SHORTCUT_MACROS

        context.user_data.pop("logging_shortcut", None)
        # Log it
        user["meals"].append({
            "date": today(),
            "description": sc["name"],
            "calories": sc["calories"],
            "protein": sc["protein"],
            "carbs": sc["carbs"],
            "fat": sc["fat"],
        })
        update_streak(user, "diet")
        save_data()
        streak = user["streaks"]["diet"]
        s = "" if streak["count"] == 1 else "s"
        streak_msg = t(lang, "diet_streak", emoji=get_streak_emoji(streak["count"]), count=streak["count"], s=s)
        totals = today_totals(user)
        goals = user["goals"]
        net = goals["calories"] - totals["calories"] + totals["burned"]
        await update.message.reply_text(
            t(lang, "shortcut_logged",
              name=sc["name"], cal=sc["calories"], prot=sc["protein"],
              carbs=sc["carbs"], fat=sc["fat"],
              net=net, prot_left=goals["protein"]-totals["protein"], streak=streak_msg),
            parse_mode="Markdown",
            reply_markup=main_keyboard(lang)
        )
        return MAIN_MENU

    # Otherwise we are SAVING a new shortcut
    name = context.user_data.get("shortcut_name", "Meal")
    try:
        parts = text.split()
        cal, prot, carbs, fat = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    except Exception:
        await update.message.reply_text(t(lang, "shortcut_macros_err"))
        return SHORTCUT_MACROS

    if "shortcuts" not in user:
        user["shortcuts"] = []
    # Replace if name already exists
    user["shortcuts"] = [s for s in user["shortcuts"] if s["name"].lower() != name.lower()]
    user["shortcuts"].append({"name": name, "calories": cal, "protein": prot, "carbs": carbs, "fat": fat})
    save_data()
    context.user_data.pop("shortcut_name", None)

    await update.message.reply_text(
        t(lang, "shortcut_saved", name=name, cal=cal, prot=prot, carbs=carbs, fat=fat),
        parse_mode="Markdown",
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU


# ─────────────────────────────────────────────
# APPLE HEALTH
# ─────────────────────────────────────────────

async def show_apple_health(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    await update.message.reply_text(
        t(lang, "apple_health_msg"),
        parse_mode="Markdown",
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU

# ─────────────────────────────────────────────
# GROCERY TRACKER
# ─────────────────────────────────────────────

async def prompt_grocery_menu(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    if not check_access(update.effective_user.id):
        await update.message.reply_text(t(lang, "locked_msg"), reply_markup=locked_keyboard(lang))
        return MAIN_MENU
    pantry = user.get("pantry", [])
    pantry_preview = ""
    if pantry:
        items = [f"  • {item['name']}" for item in pantry[:5]]
        pantry_preview = "\n\n📦 *In your pantry:*\n" + "\n".join(items)
        if len(pantry) > 5:
            pantry_preview += f"\n  ... and {len(pantry)-5} more"
    await update.message.reply_text(
        t(lang, "grocery_menu_prompt") + pantry_preview,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(t(lang, "btn_grocery_add"))],
            [KeyboardButton(t(lang, "btn_grocery_view")), KeyboardButton(t(lang, "btn_grocery_use"))],
            [KeyboardButton(t(lang, "btn_grocery_recipe"))],
            [KeyboardButton("🏠 " + ("Main Menu" if lang=="en" else "主菜单" if lang=="zh" else "메인 메뉴"))],
        ], resize_keyboard=True)
    )
    return GROCERY_MENU


async def receive_grocery_menu(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text

    if any(x in text for x in ["Main Menu", "主菜单", "메인 메뉴", "🏠"]):
        await update.message.reply_text("👍", reply_markup=main_keyboard(lang))
        return MAIN_MENU

    if t(lang, "btn_grocery_add") in text or "➕" in text:
        await update.message.reply_text(t(lang, "grocery_add_prompt"))
        return GROCERY_ADD

    if t(lang, "btn_grocery_use") in text or ("✅" in text and "Mark" in text or "标记" in text or "표시" in text):
        pantry = user.get("pantry", [])
        if not pantry:
            await update.message.reply_text(t(lang, "grocery_empty"), reply_markup=main_keyboard(lang))
            return MAIN_MENU
        items_list = "\n".join(f"  • {item['name']}" for item in pantry)
        await update.message.reply_text(
            t(lang, "grocery_use_prompt") + "\n\n" + items_list
        )
        return GROCERY_USE

    if t(lang, "btn_grocery_view") in text or "📦" in text:
        pantry = user.get("pantry", [])
        if not pantry:
            await update.message.reply_text(t(lang, "grocery_empty"), reply_markup=main_keyboard(lang))
            return MAIN_MENU
        items_list = "\n".join(
            f"  • {item['name']} — _added {item.get('added','recently')}_"
            for item in pantry
        )
        await update.message.reply_text(
            t(lang, "grocery_view", items=items_list),
            parse_mode="Markdown",
            reply_markup=main_keyboard(lang)
        )
        return MAIN_MENU

    if t(lang, "btn_grocery_recipe") in text or "👩" in text:
        pantry = user.get("pantry", [])
        if not pantry:
            await update.message.reply_text(t(lang, "grocery_empty"), reply_markup=main_keyboard(lang))
            return MAIN_MENU
        await update.message.reply_text(t(lang, "grocery_recipe_prompt"))
        return GROCERY_RECIPE

    # Default — re-show menu
    return await prompt_grocery_menu(update, context)


async def receive_grocery_add(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text.strip()

    # Parse items — split by newline or comma
    raw_items = [x.strip() for x in text.replace(",", "\n").split("\n") if x.strip()]
    added_date = datetime.now().strftime("%b %d")

    if "pantry" not in user:
        user["pantry"] = []

    # Add new items, avoid exact duplicates
    existing_names = [item["name"].lower() for item in user["pantry"]]
    newly_added = []
    for item_name in raw_items:
        if item_name.lower() not in existing_names:
            user["pantry"].append({"name": item_name, "added": added_date})
            existing_names.append(item_name.lower())
            newly_added.append(item_name)

    save_data()

    pantry = user["pantry"]
    items_list = "\n".join(f"  • {item['name']}" for item in pantry)
    await update.message.reply_text(
        t(lang, "grocery_added", items=items_list),
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU


async def receive_grocery_use(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    text = update.message.text.strip()

    used_items = [x.strip().lower() for x in text.replace(",", "\n").split("\n") if x.strip()]
    pantry = user.get("pantry", [])

    removed = []
    kept = []
    for item in pantry:
        if any(u in item["name"].lower() or item["name"].lower() in u for u in used_items):
            removed.append(item["name"])
        else:
            kept.append(item)

    user["pantry"] = kept
    save_data()

    removed_str = "\n".join(f"  ✓ {r}" for r in removed) if removed else "  (none matched — check spelling)"
    remaining_str = "\n".join(f"  • {item['name']}" for item in kept) if kept else "  Your pantry is now empty!"

    await update.message.reply_text(
        t(lang, "grocery_used", items=removed_str, remaining=remaining_str),
        reply_markup=main_keyboard(lang)
    )
    return MAIN_MENU


async def receive_grocery_recipe(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    pantry = user.get("pantry", [])

    if not pantry:
        await update.message.reply_text(t(lang, "grocery_empty"), reply_markup=main_keyboard(lang))
        return MAIN_MENU

    ingredients = ", ".join(item["name"] for item in pantry)
    lang_instruction = {"en": "Respond in English.", "zh": "请用中文回答。", "ko": "한국어로 답변해 주세요。"}
    profile = user.get("profile", {})
    goals = user.get("goals", {"calories": 1300, "protein": 90})
    profile_context = ""
    if profile:
        profile_context = (
            f"User goal: {profile.get('goal','')}, "
            f"daily protein target: {goals.get('protein',90)}g. "
        )

    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=900,
            system=(
                f"You are an expert Asian home cooking nutritionist. "
                f"Suggest practical, delicious high-protein recipes using only the provided ingredients. "
                f"Prioritise simple recipes with minimal extra ingredients needed. "
                f"Format clearly for Telegram with emojis. Include estimated macros per serving. "
                f"{profile_context}{lang_instruction.get(lang, lang_instruction['en'])}"
            ),
            messages=[{"role": "user", "content": (
                f"I have these ingredients in my pantry: {ingredients}\n\n"
                f"Suggest 2-3 high-protein recipes I can make with these. "
                f"For each recipe include: name, prep time, estimated macros, ingredients needed from my pantry, "
                f"any extra ingredients I might need (keep minimal), and simple steps."
            )}]
        )
        recipes = response.content[0].text
    except Exception as e:
        logger.error(f"Grocery recipe error: {e}")
        recipes = t(lang, "grocery_recipe_err")

    await update.message.reply_text(recipes, reply_markup=main_keyboard(lang))
    return MAIN_MENU

# ─────────────────────────────────────────────
# CATCH-ALL HANDLER
# Responds to any message outside of conversation states
# (e.g. replies to reminders, period messages, etc.)
# ─────────────────────────────────────────────

async def catchall_message(update, context):
    """Handle any text message not caught by the conversation handler."""
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    user = get_user(user_id)
    lang = get_lang(user)
    message = update.message.text.strip()

    # Detect MICH- access codes typed anywhere and handle them directly
    if message.upper().startswith("MICH-") and len(message) == 13:
        success, result, dash_password = redeem_code(user_id, message)
        if success:
            await update.message.reply_text(
                t(lang, "code_success", expiry=result),
                reply_markup=main_keyboard(lang)
            )
            dashboard_msg = (
                f"🔐 *Your Dashboard Login*\n\n"
                f"Save this to your Saved Messages!\n\n"
                f"🆔 Telegram ID: `{user_id}`\n"
                f"🔑 Password: `{dash_password}`\n"
                f"📅 Valid until: {result}\n\n"
                + (f"📊 Dashboard: {DASHBOARD_URL}\n\n" if DASHBOARD_URL else "")
                + f"➡️ Forward this to your Saved Messages now!"
            )
            await update.message.reply_text(dashboard_msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                t(lang, "code_fail", reason=result),
                reply_markup=locked_keyboard(lang)
            )
        return

    # Route menu button taps to their proper functions
    # Build a map of all button labels across all languages → handler
    menu_routes = {}
    for lng in ["en", "zh", "ko"]:
        menu_routes[T[lng]["btn_log_meal"]] = prompt_log_meal
        menu_routes[T[lng]["btn_log_exercise"]] = prompt_log_exercise
        menu_routes[T[lng]["btn_log_weight"]] = prompt_log_weight
        menu_routes[T[lng]["btn_summary"]] = today_summary
        menu_routes[T[lng]["btn_streaks"]] = show_streaks
        menu_routes[T[lng]["btn_weight_progress"]] = weight_progress
        menu_routes[T[lng]["btn_recipes"]] = prompt_recipe_search
        menu_routes[T[lng]["btn_ask"]] = prompt_question
        menu_routes[T[lng]["btn_goals"]] = prompt_set_goals
        menu_routes[T[lng]["btn_profile"]] = show_profile
        menu_routes[T[lng]["btn_workout"]] = prompt_workout
        menu_routes[T[lng]["btn_language"]] = prompt_language
        menu_routes[T[lng]["btn_plan"]] = prompt_plan
        menu_routes[T[lng]["btn_chat"]] = prompt_chat
        menu_routes[T[lng]["btn_period"]] = prompt_period_menu
        menu_routes[T[lng]["btn_grocery"]] = prompt_grocery_menu
        menu_routes[T[lng]["btn_shortcuts"]] = prompt_shortcuts
        menu_routes[T[lng]["btn_apple_health"]] = show_apple_health

    if message in menu_routes:
        # It's a menu button tap — route it properly
        # First ensure they have access for protected functions
        if not check_access(user_id) and message != T[lang].get("btn_enter_code"):
            await update.message.reply_text(
                t(lang, "locked_msg"), reply_markup=locked_keyboard(lang)
            )
            return
        await menu_routes[message](update, context)
        return

    # Route any menu button tap to the correct handler
    # (happens when conversation state is lost, e.g. after bot restart)
    all_btn_routes = {
        "btn_log_meal": prompt_log_meal,
        "btn_log_exercise": prompt_log_exercise,
        "btn_log_weight": prompt_log_weight,
        "btn_summary": today_summary,
        "btn_streaks": show_streaks,
        "btn_weight_progress": weight_progress,
        "btn_recipes": prompt_recipe_search,
        "btn_ask": prompt_question,
        "btn_goals": prompt_set_goals,
        "btn_profile": show_profile,
        "btn_workout": prompt_workout,
        "btn_language": prompt_language,
        "btn_plan": prompt_plan,
        "btn_chat": prompt_chat,
        "btn_period": prompt_period_menu,
        "btn_grocery": prompt_grocery_menu,
        "btn_shortcuts": prompt_shortcuts,
        "btn_apple_health": show_apple_health,
    }
    for btn_key, handler_fn in all_btn_routes.items():
        for lng in ["en", "zh", "ko"]:
            if message == T[lng].get(btn_key, ""):
                await handler_fn(update, context)
                return

    # If not subscribed, remind them
    if not check_access(user_id):
        await update.message.reply_text(
            t(lang, "locked_msg") + "\n\nUse /start to get started!",
            reply_markup=locked_keyboard(lang)
        )
        return

    # Otherwise respond as Michi the wellness companion
    lang_instruction = {"en": "Respond in English.", "zh": "请用中文回答。", "ko": "한국어로 답변해 주세요。"}
    profile = user.get("profile", {})
    profile_context = ""
    if profile:
        profile_context = (
            f"User info: {profile.get('gender','')}, age {profile.get('age','')}, "
            f"goal: {profile.get('goal','')}. "
        )

    # Check recent period logs for cycle context
    cycle_context = ""
    logs = user.get("period_logs", [])
    if logs:
        from datetime import datetime as _dt
        try:
            last = _dt.strptime(logs[-1]["date"], "%Y-%m-%d")
            day = (_dt.now() - last).days + 1
            cycle_context = f"The user is on day {day} of their menstrual cycle. "
        except Exception:
            pass

    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=350,
            system=(
                f"You are Michi, a warm, friendly and knowledgeable wellness companion. "
                f"You specialise in nutrition, fitness, women\'s health and Singaporean food. "
                f"The user is replying to a message you sent them (like a reminder or period tip). "
                f"Respond naturally and conversationally — be supportive, empathetic and helpful. "
                f"Keep replies under 120 words. "
                f"{profile_context}{cycle_context}"
                f"{lang_instruction.get(lang, lang_instruction['en'])}"
            ),
            messages=[{"role": "user", "content": message}]
        )
        reply = response.content[0].text
    except Exception as e:
        logger.error(f"Catchall error: {e}")
        reply = t(lang, "ai_err")

    await update.message.reply_text(
        reply,
        reply_markup=main_keyboard(lang)
    )


async def admin_announce(update, context):
    """Usage: /announce <message> — sends a message to all active subscribers."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /announce Your message here\n\nSends to all active subscribers.")
        return
    msg = " ".join(context.args)
    active = [uid for uid, d in user_data_store.items()
              if d.get("subscription_expiry") and
              datetime.strptime(d["subscription_expiry"], "%Y-%m-%d") >= datetime.now()]
    sent, failed = 0, 0
    for uid in active:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 {msg}")
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(f"✅ Sent to {sent} subscribers.{' ❌ '+str(failed)+' failed.' if failed else ''}")


async def admin_updatedashboard(update, context):
    """Usage: /updatedashboard — sends all subscribers a prompt to refresh their dashboard."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    active = [uid for uid, d in user_data_store.items()
              if d.get("subscription_expiry") and
              datetime.strptime(d["subscription_expiry"], "%Y-%m-%d") >= datetime.now()]
    msgs = {
        "en": "🔄 Your dashboard has been updated with new features! Open it to see what\'s new 🌿",
        "zh": "🔄 你的仪表盘已更新新功能！打开查看最新内容 🌿",
        "ko": "🔄 대시보드가 새로운 기능으로 업데이트되었습니다! 열어서 확인하세요 🌿",
    }
    sent = 0
    for uid in active:
        try:
            user = get_user(uid)
            lang = user.get("language", "en")
            dash_pw = user.get("dashboard_password", "")
            expiry = user.get("subscription_expiry", "")
            base_msg = msgs.get(lang, msgs["en"])
            if dash_pw:
                base_msg += f"\n\n🔐 Your login:\n🆔 ID: `{uid}`\n🔑 Password: `{dash_pw}`"
            await context.bot.send_message(chat_id=uid, text=base_msg, parse_mode="Markdown")
            sent += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Dashboard update notification sent to {sent} subscribers!")

# ─────────────────────────────────────────────
# ADMIN COMMANDS
# ─────────────────────────────────────────────

async def set_goals(update, context):
    user = get_user(update.effective_user.id)
    lang = get_lang(user)
    try:
        cal, prot = int(context.args[0]), int(context.args[1])
        user["goals"] = {"calories": cal, "protein": prot}
        save_data()
        await update.message.reply_text(t(lang, "goals_saved", cal=cal, prot=prot))
    except Exception:
        await update.message.reply_text(t(lang, "goals_err"))
    return MAIN_MENU


async def admin_generate(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return MAIN_MENU
    days = 30
    if context.args:
        try: days = int(context.args[0])
        except: pass
    code = generate_code(days)
    await update.message.reply_text(f"✅ New code!\n\nCode: `{code}`\nDuration: {days} days\n\nSend to subscriber after payment!", parse_mode="Markdown")
    return MAIN_MENU


async def admin_list_codes(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return MAIN_MENU
    if not subscription_codes:
        await update.message.reply_text("No codes yet.")
        return MAIN_MENU
    lines = [f"`{c}` — {i['days']}d — {'Used by '+str(i['used_by']) if i['used'] else 'Available'}" for c, i in subscription_codes.items()]
    await update.message.reply_text("📋 Codes:\n\n" + "\n".join(lines), parse_mode="Markdown")
    return MAIN_MENU


async def admin_subscribers(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return MAIN_MENU
    active = [f"User {uid} — until {d.get('subscription_expiry')} ({(datetime.strptime(d['subscription_expiry'],'%Y-%m-%d')-datetime.now()).days}d)"
              for uid, d in user_data_store.items()
              if d.get("subscription_expiry") and datetime.strptime(d["subscription_expiry"],"%Y-%m-%d") >= datetime.now()]
    await update.message.reply_text(f"👥 Active ({len(active)}):\n\n" + "\n".join(active) if active else "No active subscribers.")
    return MAIN_MENU


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def make_menu_handlers():
    """Build MAIN_MENU handlers for all 3 languages."""
    handlers = []
    for lang in ["en", "zh", "ko"]:
        handlers += [
            MessageHandler(filters.Regex(f"^{T[lang]['btn_log_meal']}$"), prompt_log_meal),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_log_exercise']}$"), prompt_log_exercise),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_log_weight']}$"), prompt_log_weight),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_summary']}$"), today_summary),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_streaks']}$"), show_streaks),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_weight_progress']}$"), weight_progress),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_recipes']}$"), prompt_recipe_search),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_ask']}$"), prompt_question),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_goals']}$"), prompt_set_goals),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_profile']}$"), show_profile),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_workout']}$"), prompt_workout),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_language']}$"), prompt_language),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_enter_code']}$"), prompt_enter_code),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_plan']}$"), prompt_plan),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_chat']}$"), prompt_chat),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_period']}$"), prompt_period_menu),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_grocery']}$"), prompt_grocery_menu),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_quick_log']}$"), prompt_quick_log),
            MessageHandler(filters.Regex(f"^{T[lang]['btn_apple_health']}$"), show_apple_health),
        ]
    return handlers


def main():
    persistence = PicklePersistence(filepath="/tmp/bot_persistence")
    app = Application.builder().token(TELEGRAM_TOKEN).persistence(persistence).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        persistent=True,
        name="main_conv",
        states={
            MAIN_MENU: make_menu_handlers(),
            LOG_MEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_meal), MessageHandler(filters.PHOTO, receive_meal)],
            MEAL_MORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_meal_more), MessageHandler(filters.PHOTO, receive_meal_more)],
            MEAL_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_meal_more)],
            PERIOD_LOG: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_period_menu)],
            PERIOD_CYCLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_period_date)],
            PERIOD_SYMPTOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_period_symptoms)],
            GROCERY_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_grocery_menu)],
            GROCERY_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_grocery_add)],
            GROCERY_USE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_grocery_use)],
            GROCERY_RECIPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_grocery_recipe)],
            ONBOARD_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_onboard_choice)],
            SHORTCUT_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_shortcut_menu)],
            SHORTCUT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_shortcut_name)],
            SHORTCUT_MACROS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_shortcut_macros)],
            ONBOARD_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_onboard_start)],

            LOG_EXERCISE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_exercise)],
            LOG_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_weight)],
            ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question)],
            RECIPE_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_recipe_search)],
            ENTER_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_code)],
            SET_GOALS_MANUAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_goals_choice)],
            MANUAL_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_manual_goals)],
            QUIZ_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_height)],
            QUIZ_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_weight)],
            QUIZ_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_age)],
            QUIZ_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_gender)],
            QUIZ_ACTIVITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_activity)],
            QUIZ_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_goal)],
            QUIZ_BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_body)],
            QUIZ_BLOOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_blood)],
            SELECT_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_language)],
            WORKOUT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_workout_type)],
            WORKOUT_PLAN_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_workout_plan_type)],
            WORKOUT_MUSCLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_workout_muscle)],
            PLAN_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_plan_goal)],
            CHAT_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_chat)],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("generate", admin_generate),
            CommandHandler("codes", admin_list_codes),
            CommandHandler("subscribers", admin_subscribers),
            CommandHandler("expire", admin_expire),
            CommandHandler("announce", admin_announce),
            CommandHandler("updatedashboard", admin_updatedashboard),
            CommandHandler("mydashboard", my_dashboard),
            CommandHandler("goals", set_goals),
            CommandHandler("reminders", setup_reminders),
            CommandHandler("redeem", redeem_command),
            # Allow numeric input to reach receive_weight from any state
            MessageHandler(filters.Regex(r"^\d+(\.\d+)?$"), receive_weight),
        ],
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("goals", set_goals))
    app.add_handler(CommandHandler("reminders", setup_reminders))
    app.add_handler(CommandHandler("redeem", redeem_command))
    app.add_handler(CommandHandler("subscription", check_subscription))
    app.add_handler(CommandHandler("generate", admin_generate))
    app.add_handler(CommandHandler("codes", admin_list_codes))
    app.add_handler(CommandHandler("subscribers", admin_subscribers))
    app.add_handler(CommandHandler("expire", admin_expire))
    app.add_handler(CommandHandler("announce", admin_announce))
    app.add_handler(CommandHandler("updatedashboard", admin_updatedashboard))
    app.add_handler(CommandHandler("mydashboard", my_dashboard))
    app.add_handler(MessageHandler(filters.VOICE, receive_voice))
    # Catch-all: responds to any message outside conversation states (e.g. replies to reminders)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, catchall_message))
    logger.info("Bot is running...")
    # Daily period reminder check at 9am
    app.job_queue.run_daily(send_period_reminder, time=time(hour=9, minute=0), name="period_reminder")
    app.run_polling()


if __name__ == "__main__":
    main()

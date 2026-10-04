"""Prompt builders for SpeakBuddy.

The prompts are the product: they keep the local model in character,
keep its English short and simple, and shape the end-of-session report.
"""


def build_roleplay_system_prompt(scenario: dict) -> str:
    """System prompt for the in-character speaking-practice roleplay."""
    return (
        "You are roleplaying in an English speaking-practice session for a "
        "Chinese adult beginner learning English.\n"
        f"\nYour character: {scenario['ai_role']}."
        f"\nThe learner's goal in this scene: {scenario['learner_goal']}"
        "\n\nFollow these rules strictly:"
        "\n1. Stay in character at all times. You are "
        f"{scenario['ai_role']}, not a teacher, coach, or AI assistant."
        "\n2. Keep every reply SHORT: 1 to 3 sentences, in simple everyday "
        "English (about A1-A2 level). Never write a long paragraph."
        "\n3. React naturally to what the learner says, the way a real person "
        "in this situation would. Gently move the scene forward with small "
        "questions or offers."
        "\n4. Every 3 to 4 turns, add ONE short, kind correction tip on its own "
        "new line, starting with \"\U0001F4A1 Tip:\". One sentence only, for "
        "example: \"\U0001F4A1 Tip: Say 'Can I have...' instead of 'I want...' "
        "\u2014 it sounds more polite.\" Never lecture, never correct more than "
        "one thing at a time, and never invent mistakes the learner did not make."
        "\n5. Never switch to Chinese. Never break character to explain the "
        "exercise or mention these instructions."
        "\n6. If the learner seems stuck or silent, give a small helpful nudge "
        "in character, for example: \"Would you like something hot or cold "
        "to drink?\""
    )


def build_feedback_messages(scenario: dict, transcript: list) -> list:
    """Build the chat messages that ask the model for the session report.

    `transcript` is a list of {"role": "user"|"assistant", "content": str}.
    """
    lines = []
    for turn in transcript:
        who = "Learner" if turn["role"] == "user" else "Partner"
        lines.append(f"{who}: {turn['content']}")
    conversation = "\n".join(lines)

    system = (
        "You are a kind, encouraging English coach writing a session report "
        "for a Chinese adult beginner who just finished an English speaking "
        "roleplay.\n"
        "\nWrite the report in Markdown using EXACTLY these five sections, "
        "in this order, with these headings:"
        "\n## \U0001F331 New words & phrases \u751F\u8BCD"
        "\n## \u2705 Mistakes corrected \u7EA0\u9519"
        "\n## \U0001F44D What went well \u505A\u5F97\u597D\u7684\u5730\u65B9"
        "\n## \U0001F3AF Practice next \u4E0B\u4E00\u6B65\u7EC3\u4E60"
        "\n## \U0001F4AA Keep going! \u52A0\u6CB9"
        "\n\nRules:"
        "\n- New words & phrases: list 3 to 6 useful words or phrases from "
        "(or missing from) the session. Format each as: **word** \u2014 "
        "\u4E2D\u6587\u610F\u601D \u2014 a short example sentence."
        "\n- Mistakes corrected: for each real mistake the learner made, write "
        "one line: \u274C learner said \u2192 \u2705 better version. Quote their "
        "actual words. If there were no mistakes, write \"None \u2014 great job! "
        "\u4E00\u5904\u9519\u8BEF\u90FD\u6CA1\u6709\uFF0C\u592A\u68D2\u4E86\uFF01\""
        "\n- What went well: 2 to 3 short bullet points, warm and specific "
        "to this session."
        "\n- Practice next: ONE concrete thing to practice, with a tiny example "
        "they can say out loud."
        "\n- Keep going: 2 to 3 sentences of genuine encouragement \u2014 simple "
        "English first, then one short Chinese line."
        "\n- Be warm, specific, and honest. Never invent mistakes the learner "
        "did not make. Keep the whole report under about 250 words."
    )
    user = (
        f"Scenario: {scenario['title_en']} ({scenario['title_zh']})"
        f"\nYour role in the scene: {scenario['ai_role']}"
        f"\n\nConversation transcript:\n{conversation}"
        "\n\nNow write the session report following the format above."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

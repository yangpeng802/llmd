"""SpeakBuddy: a patient AI English-speaking practice partner.

Built for the Hacktoberfest 2026 "Build for a Friend" weekend challenge.

100% local: the AI is an open-source model served by Ollama on your own
machine, reached through Ollama's OpenAI-compatible API. No cloud API keys,
no account, and nothing you say ever leaves your computer.
"""

import json
import os
from pathlib import Path

import gradio as gr
from openai import OpenAI

try:  # optional: allow OLLAMA_HOST / OLLAMA_MODEL in a local .env file
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional; plain env vars always work
    pass

from prompts import build_feedback_messages, build_roleplay_system_prompt

BASE_DIR = Path(__file__).resolve().parent

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434/v1").rstrip("/")
if not OLLAMA_HOST.endswith("/v1"):
    OLLAMA_HOST += "/v1"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:1b")

with open(BASE_DIR / "scenarios.json", encoding="utf-8") as f:
    SCENARIOS = json.load(f)
SCENARIOS_BY_ID = {s["id"]: s for s in SCENARIOS}

# api_key is required by the client signature but unused by Ollama.
client = OpenAI(base_url=OLLAMA_HOST, api_key="ollama")


def _connect_hint() -> str:
    return (
        "SpeakBuddy needs a local model to talk to you:\n"
        "1. Install Ollama from https://ollama.com, then run `ollama serve`\n"
        f"2. Run `ollama pull {OLLAMA_MODEL}`\n"
        "3. Refresh this page and try again.\n\n"
        "（请先安装并启动 Ollama，拉取模型，然后刷新页面重试。）"
    )


def check_ollama():
    """Return (reachable, banner_markdown). Never raises."""
    try:
        client.models.list()
    except Exception:
        return (
            False,
            "⚠️ **Ollama is not reachable** · 无法连接本地模型\n\n" + _connect_hint(),
        )
    return True, f"✅ Connected to Ollama · 本地模型已连接 `{OLLAMA_MODEL}`"


def _chat_once(messages):
    resp = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=220,
    )
    return (resp.choices[0].message.content or "").strip()


def _scenario_info(sc) -> str:
    return (
        f"### {sc['emoji']} {sc['title_en']} · {sc['title_zh']}\n"
        f"**You're talking to:** {sc['ai_role']}  \n"
        f"**Your goal:** {sc['learner_goal']}"
    )


def start_session(scenario_id, state):
    sc = SCENARIOS_BY_ID[scenario_id]
    messages = [
        {"role": "system", "content": build_roleplay_system_prompt(sc)},
        {"role": "assistant", "content": sc["first_message"]},
    ]
    state = {
        "scenario_id": scenario_id,
        "messages": messages,
        "started": True,
        "ended": False,
    }
    history = [{"role": "assistant", "content": sc["first_message"]}]
    starters = sc["starters"]
    return (
        history,
        "",
        state,
        _scenario_info(sc),
        starters[0],
        starters[1],
        starters[2],
        "⬇️ Your feedback report will appear here when you press "
        "**End session & get feedback**.",
    )


def _starter_text(index, state) -> str:
    sc = SCENARIOS_BY_ID.get(state.get("scenario_id") or "")
    return sc["starters"][index] if sc else ""


def respond(user_text, history, state):
    user_text = (user_text or "").strip()
    history = history or []
    if not state.get("started"):
        if user_text:
            history = history + [
                {"role": "user", "content": user_text},
                {
                    "role": "assistant",
                    "content": "👆 Pick a scenario above and press **Start session** first! "
                    "先选个场景，再点开始 🙂",
                },
            ]
        return history, "", state
    if state.get("ended"):
        history = history + [
            {"role": "user", "content": user_text},
            {
                "role": "assistant",
                "content": "This session has ended — press **Start session** to practice again! "
                "本轮已结束，点开始再来一轮吧 🙂",
            },
        ]
        return history, "", state
    if not user_text:
        return history, "", state
    state["messages"].append({"role": "user", "content": user_text})
    try:
        reply = _chat_once(state["messages"])
    except Exception:
        state["messages"].pop()  # keep the transcript clean for a retry
        reply = "😢 I can't reach the AI model right now.\n\n" + _connect_hint()
    else:
        state["messages"].append({"role": "assistant", "content": reply})
    return history + [
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": reply},
    ], "", state


def end_session(state):
    if not state.get("started"):
        return "👆 Start a session first! 先开始一轮练习吧 🙂", state
    transcript = [m for m in state["messages"] if m["role"] != "system"]
    if not any(m["role"] == "user" for m in transcript):
        return "💬 Say a few things first, then ask for feedback! 先聊几句再要反馈吧 🙂", state
    sc = SCENARIOS_BY_ID[state["scenario_id"]]
    try:
        resp = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=build_feedback_messages(sc, transcript),
            temperature=0.5,
            max_tokens=900,
        )
        report = (resp.choices[0].message.content or "").strip()
    except Exception:
        report = "## ⚠️ Couldn't generate the report\n\n" + _connect_hint()
    state["ended"] = True
    return report, state


# --- Browser-side helpers: mic input (Web Speech API) and read-aloud --------
# NOTE: in Gradio 6, <script> tags inside gr.HTML do NOT execute (innerHTML).
# The helpers must be injected via Blocks(head=...) so they run in <head>.
HEAD_JS = """
<script>
function startDictation() {
  var status = document.getElementById('mic-status');
  var box = document.querySelector('#user_input textarea');
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!box) { if (status) status.textContent = '找不到输入框'; return; }
  if (!SR) {
    if (status) status.textContent = '🎤 当前浏览器不支持语音输入，请用 Chrome 或 Edge 试试';
    return;
  }
  var rec = new SR();
  rec.lang = 'en-US';
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  if (status) status.textContent = '🎤 Listening… 请说英语';
  rec.onresult = function (e) {
    var text = e.results[0][0].transcript;
    box.value = text;
    box.dispatchEvent(new Event('input', { bubbles: true }));
    box.focus();
    if (status) status.textContent = '';
  };
  rec.onerror = function () {
    if (status) status.textContent = '🎤 没听清，再试一次吧';
  };
  rec.onend = function () {
    if (status && status.textContent.indexOf('Listening') !== -1) status.textContent = '';
  };
  try { rec.start(); } catch (e) { if (status) status.textContent = '🎤 麦克风启动失败'; }
}
function maybeSpeak(history) {
  try {
    var toggle = document.querySelector('#read_aloud_toggle input[type="checkbox"]');
    if (!toggle || !toggle.checked) return;
    if (!history || !history.length) return;
    var last = history[history.length - 1];
    var text = '';
    if (Array.isArray(last)) text = last[1] || '';
    else if (last && typeof last === 'object') text = last.content || '';
    if (!text) return;
    text = text.replace(/[\\u{1F300}-\\u{1FAFF}\\u{2600}-\\u{27BF}\\uFE0F]/gu, '').trim();
    if (!text || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text);
    u.lang = 'en-US';
    u.rate = 0.95;
    window.speechSynthesis.speak(u);
  } catch (e) { console.warn('speak failed', e); }
}
</script>
"""

MIC_HTML = """<span id="mic-status" style="font-size:13px;color:#666;"></span>"""

_, ollama_banner = check_ollama()

with gr.Blocks(title="SpeakBuddy · 英语口语陪练", head=HEAD_JS) as demo:
    gr.Markdown(
        "# 🎙️ SpeakBuddy · 你的英语口语陪练\n"
        "Practice real-life English with a patient AI partner. "
        "The AI runs **100% locally** on your machine — nothing you say ever "
        "leaves your computer."
    )
    gr.Markdown(ollama_banner)

    with gr.Row():
        scenario_dd = gr.Dropdown(
            choices=[
                (f"{s['emoji']} {s['title_en']} · {s['title_zh']}", s["id"])
                for s in SCENARIOS
            ],
            value=SCENARIOS[0]["id"],
            label="Choose a scenario · 选择场景",
            scale=3,
        )
        start_btn = gr.Button("▶️ Start session · 开始", variant="primary", scale=1)
        end_btn = gr.Button("🏁 End session & get feedback · 结束并看反馈", scale=1)

    info_md = gr.Markdown(_scenario_info(SCENARIOS[0]))

    gr.Markdown("**Try a starter — 点一句开场白试试：**")
    with gr.Row():
        s1 = gr.Button(SCENARIOS[0]["starters"][0])
        s2 = gr.Button(SCENARIOS[0]["starters"][1])
        s3 = gr.Button(SCENARIOS[0]["starters"][2])

    chatbot = gr.Chatbot(label="Conversation · 对话", height=420)

    with gr.Row():
        msg = gr.Textbox(
            label="Your message · 用英语输入",
            placeholder="Type in English… 比如: I'd like a latte, please",
            scale=4,
            elem_id="user_input",
        )
        send_btn = gr.Button("Send 📨", scale=1, min_width=100)

    with gr.Row():
        mic_btn = gr.Button("🎤 Speak · 语音输入", min_width=160)
        gr.Checkbox(
            label="🔊 Read aloud AI replies · 朗读 AI 回复",
            value=False,
            elem_id="read_aloud_toggle",
        )
    gr.HTML(MIC_HTML)

    gr.Markdown("## 📋 Session feedback · 反馈报告")
    report_md = gr.Markdown(
        "⬇️ Your feedback report will appear here when you press "
        "**End session & get feedback**."
    )

    gr.Markdown(
        "---\n*Built for Hacktoberfest 2026 · Build for a Friend — "
        "powered by local open-source AI (Ollama). No cloud, no API keys.*"
    )

    chat_state = gr.State({"started": False})

    start_btn.click(
        fn=start_session,
        inputs=[scenario_dd, chat_state],
        outputs=[chatbot, msg, chat_state, info_md, s1, s2, s3, report_md],
    )
    speak_js = "(hist) => { maybeSpeak(hist); }"
    send_evt = send_btn.click(
        fn=respond,
        inputs=[msg, chatbot, chat_state],
        outputs=[chatbot, msg, chat_state],
    )
    # Read-aloud must run AFTER the new reply lands in the history,
    # so it chains as a .then() side-effect (js-only, no outputs).
    send_evt.then(fn=None, inputs=[chatbot], outputs=[], js=speak_js)
    submit_evt = msg.submit(
        fn=respond,
        inputs=[msg, chatbot, chat_state],
        outputs=[chatbot, msg, chat_state],
    )
    submit_evt.then(fn=None, inputs=[chatbot], outputs=[], js=speak_js)
    end_btn.click(fn=end_session, inputs=chat_state, outputs=[report_md, chat_state])

    mic_btn.click(fn=None, js="() => startDictation()")
    for i, btn in enumerate((s1, s2, s3)):
        btn.click(
            fn=lambda st, i=i: _starter_text(i, st),
            inputs=chat_state,
            outputs=msg,
        )

if __name__ == "__main__":
    demo.launch()

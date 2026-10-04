# 🎙️ SpeakBuddy

A patient AI English-speaking practice partner — built for the **Hacktoberfest 2026 "Build for a Friend"** weekend challenge.

## Who it's for

A friend learning English (beginner level, Chinese speaker). They pick an everyday scenario — ordering coffee, checking into a hotel, airport small talk — roleplay it with the AI, get gentle corrections along the way, and finish with a personal feedback report: new vocabulary with Chinese glosses, mistakes corrected, and encouragement.

## The open-source AI story

- **100% local inference.** The app talks to [Ollama](https://ollama.com)'s OpenAI-compatible API on your own machine. No cloud API keys, no accounts, no bills.
- **Open-weights model.** Default is `gemma3:1b` (Google's open Gemma 3, 1B — tiny and fast); the README recommends `gemma3` (4B) for noticeably better English. Swap any Ollama model via `OLLAMA_MODEL`.
- **Private by design.** Nothing the learner says ever leaves their computer — which matters when someone is practicing out loud and making mistakes.

## Quickstart

1. Install Ollama from https://ollama.com
2. Pull a model:
   ```bash
   ollama pull gemma3:1b      # fast default
   # or: ollama pull gemma3   # 4B, better quality (recommended)
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run:
   ```bash
   python app.py
   ```
5. Open http://127.0.0.1:7860

Optional configuration — copy `.env.example` to `.env`, or export directly:

```bash
OLLAMA_HOST=http://localhost:11434/v1   # default
OLLAMA_MODEL=gemma3:1b                  # default
```

If Ollama isn't running, the app tells you exactly what to do (`ollama serve` + `ollama pull <model>`) instead of crashing.

## Demo script (60 seconds)

1. Pick **☕ Ordering Coffee · 点咖啡**, press **Start session**.
2. Click a starter phrase — or type something imperfect like `I want a big coffee`.
3. Chat a few turns. Notice the AI stays in character as the barista, keeps replies to 1–3 short sentences, and drops an occasional gentle `💡 Tip:` correction (never a lecture).
4. Press **🏁 End session & get feedback** — you get a report with new words (with 中文意思), mistakes corrected, what went well, one thing to practice next, and encouragement.
5. (Optional) Toggle **🔊 Read aloud** to hear replies via the browser's speech synthesis, or use the **🎤** mic button to dictate in Chrome/Edge.

## Project layout

| File | What it does |
|---|---|
| `app.py` | Gradio UI, session state, Ollama calls, mic/read-aloud browser JS |
| `scenarios.json` | The 6 practice scenarios (roles, goals, starters, openers) |
| `prompts.py` | System-prompt builders for roleplay and the feedback report |
| `requirements.txt` | `gradio`, `openai`, `python-dotenv` (optional) |
| `.env.example` | `OLLAMA_HOST` / `OLLAMA_MODEL` |

## License

MIT — see [LICENSE](LICENSE).

from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT

class Brain:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing. Check your .env file.")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    def think(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})

        # Keep system prompt + last 20 messages
        if len(self.history) > 21:
            self.history = [self.history[0]] + self.history[-20:]

        try:
            response = self.client.chat.completions.create(
                messages = self.history,
                model = GROQ_MODEL,
            )
            reply = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            print(f"[Groq Error] {e}")
            return "Sorry, I couldn't reach my brain right now."
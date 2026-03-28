"""AI service wrapper for OpenAI GPT-4o."""
import json
import logging
from flask import current_app

logger = logging.getLogger(__name__)

FLASHCARD_SYSTEM_PROMPT = """You are an expert tutor who creates deep, applied flashcards for active recall learning. You do NOT ask trivial definition questions. Instead you ask questions that force the learner to reason, apply knowledge, and think critically about how concepts interact.

Rules:
1. Prioritise APPLIED, DEBUG, and COMPARE_CONTRAST question types.
2. Questions should reflect real-world scenarios and gotchas.
3. Answers must be concise (2-5 sentences) but complete.
4. Include the source_snippet: a 1-2 sentence excerpt from the note.
5. Set difficulty: 1 (easy) for definitions, 2 (medium) for applied, 3 (hard) for multi-concept reasoning.
6. Return ONLY valid JSON. No markdown.

JSON Schema: { "cards": [{"question": "...", "answer": "...", "question_type": "...", "difficulty": 1|2|3, "source_snippet": "...", "mcq_options": null|[...]}] }"""


def build_flashcard_user_prompt(topic: str, note_text: str, n: int = 10) -> str:
    return (
        f"The following is a student's personal note on the topic of {topic}. "
        f"Generate {n} flashcards that would challenge someone who has read this note "
        f"but needs to truly understand it, not just memorise it.\n\n"
        f"NOTE CONTENT:\n"
        f"─────────────\n"
        f"{note_text}\n"
        f"─────────────"
    )


def generate_flashcards_from_text(
    note_text: str,
    topic: str = "this subject",
    n: int = 10,
) -> list[dict]:
    """Call OpenAI and return a list of flashcard dicts."""
    api_key = current_app.config.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured")
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = current_app.config.get("OPENAI_MODEL", "gpt-4o")
        max_tokens = current_app.config.get("OPENAI_MAX_TOKENS", 2000)

        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0.7,
            messages=[
                {"role": "system", "content": FLASHCARD_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_flashcard_user_prompt(topic, note_text, n),
                },
            ],
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)
        cards = data.get("cards", [])

        usage = response.usage
        return cards, {
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "model": model,
        }

    except Exception as exc:
        logger.error("OpenAI flashcard generation failed: %s", exc)
        raise


ASK_AI_SYSTEM = (
    "You are a knowledgeable study assistant. The user is reviewing a flashcard "
    "and has a question. Answer concisely but thoroughly, drawing on the card content."
)


def ask_ai_about_card(question: str, card_question: str, card_answer: str) -> str:
    """Return an AI explanation for a flashcard question."""
    api_key = current_app.config.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured")
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = current_app.config.get("OPENAI_MODEL", "gpt-4o")

        messages = [
            {"role": "system", "content": ASK_AI_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Flashcard question: {card_question}\n"
                    f"Flashcard answer: {card_answer}\n\n"
                    f"My question: {question}"
                ),
            },
        ]
        response = client.chat.completions.create(
            model=model,
            max_tokens=500,
            temperature=0.5,
            messages=messages,
        )
        return response.choices[0].message.content.strip()

    except Exception as exc:
        logger.error("Ask AI failed: %s", exc)
        raise

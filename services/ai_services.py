import os
import json
import httpx
from typing import Dict, Any

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")


class AIServices:

    # ======================================================================
    # 1. UNIFIED DATASET PAYLOAD (your original)
    # ======================================================================
    @staticmethod
    async def build_model_payload(
        symbol: str,
        timeframe_data: Dict[str, Any],
        sentiment: Dict[str, Any],
        journal_recent: list,
        backtest_profile: Dict[str, Any]
    ):
        """
        Unifies all market and sentiment data into one JSON 
        to send to the LLM. Format matches your scalping agent design.
        """

        payload = {
            "symbol": symbol,
            "timeframes": timeframe_data,        # M5, M15, H1, H4, D1
            "sentiment": sentiment,              # news sentiment + sources
            "journal_recent": journal_recent,    # last trades to learn from
            "backtest_profile": backtest_profile # strengths/weaknesses from DB
        }

        return payload

    # ======================================================================
    # 2. LLM DECISION CALL (your original)
    # ======================================================================
    @staticmethod
    async def get_ai_decision(model_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a single JSON payload to OpenAI and returns structured JSON output.
        This is the core decision engine call.
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        system_prompt = """
            You are a professional financial trader with over 20 years of experience. 
            Your job is to generate scalping trade signals using:

            - M5 and M15 = entry logic
            - H1 and H4 = directional bias only
            - D1 = macro background bias
            - sentiment = news conflict detection + volatility awareness
            - journal_recent = self-improvement + experience learning
            - backtest_profile = historical strengths and weaknesses

            Rules:
            1. Output JSON ONLY.
            2. No natural language outside JSON.
            3. Use confidence percentages (ex: 82).
            4. Include direction, entry, stop, targets.
            5. Include compact reasoning.
            6. Follow risk management requirements.
            7. If high-impact news is imminent, avoid taking trades.
        """

        user_prompt = f"""
            Here is the full market dataset. Return trading decisions in JSON only.

            {json.dumps(model_input)}
        """

        body = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"}
        }

        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=body
            )

        return response.json()

    # ======================================================================
    # 3. BUILD TRADE CLOSE PAYLOAD
    # ======================================================================
    @staticmethod
    def package_trade_close(position_id: int, ai_reason: str):
        """
        Generates the JSON payload for POST /trade/close
        Fully aligned with your APIdoc.
        """

        return {
            "position_id": position_id,
            "reason": ai_reason
        }

    # ======================================================================
    # 4. BUILD JOURNAL ENTRY PAYLOAD
    # ======================================================================
    @staticmethod
    def package_journal_entry(symbol: str, ai_data: Dict[str, Any], trade_result: Dict[str, Any]):
        """
        Formats a journal entry based on:
        - AI decision info
        - Actual trade result returned by MT5
        """

        return {
            "symbol": symbol,
            "direction": ai_data["direction"],
            "entry_price": ai_data["entry"],
            "stop_loss": ai_data["stop"],
            "take_profit": ai_data["targets"][0],
            "exit_price": trade_result.get("exit_price"),
            "outcome": trade_result.get("outcome", "unknown"),
            "confidence": ai_data.get("confidence"),
            "reasoning": ai_data.get("reasoning", "")
        }

    # ======================================================================
    # 5. SMART STOP-LOSS ADJUSTMENT (AI TRADE MANAGEMENT)
    # ======================================================================
    @staticmethod
    def smart_stop_adjust(current_price: float, ai_data: Dict[str, Any]):
        """
        AI-driven stop-loss tightening logic.
        This helps the agent:
        - reduce losses
        - protect partial profits
        - lock in gains as the market moves in our favour

        Logic:
        +0.5R → SL to -0.25R
        +1.0R → SL to BE
        +1.5R → SL to +0.5R
        """

        entry = ai_data["entry"]
        initial_sl = ai_data["stop"]
        direction = ai_data["direction"].lower()
        risk = abs(entry - initial_sl)

        new_sl = initial_sl

        if direction == "long":
            if current_price >= entry + 0.5 * risk:
                new_sl = entry - 0.25 * risk
            if current_price >= entry + 1.0 * risk:
                new_sl = entry
            if current_price >= entry + 1.5 * risk:
                new_sl = entry + 0.5 * risk

        elif direction == "short":
            if current_price <= entry - 0.5 * risk:
                new_sl = entry + 0.25 * risk
            if current_price <= entry - 1.0 * risk:
                new_sl = entry
            if current_price <= entry - 1.5 * risk:
                new_sl = entry - 0.5 * risk

        return round(new_sl, 2)


# Export instance
ai_service = AIServices()

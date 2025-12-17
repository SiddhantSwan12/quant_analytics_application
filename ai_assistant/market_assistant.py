import os
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)

from google import genai
import pandas as pd
import streamlit as st
try:
    from groq import Groq
except ImportError:
    Groq = None

class MarketAssistant:
    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = os.getenv("GROQ_API_KEY")
        self.api_key = api_key
        self.provider = "google"
        self.client = None
        self.available = False
        
        if not self.api_key:
            print("AI/LLM connection failed: No API key provided or found in environment variables (GROQ_API_KEY or GOOGLE_API_KEY).")
            self.available = False
            return

        try:
            if self.api_key.startswith("gsk_"):
                if Groq is None:
                    print("Groq library not found. Install with `pip install groq`")
                else:
                    self.provider = "groq"
                    self.client = Groq(api_key=self.api_key)
                    self.model_name = "llama-3.3-70b-versatile"
                    self.available = True
                    print("AI Assistant: Connected to Groq 🚀")
            else:
                self.client = genai.Client(api_key=self.api_key)
                self.model_name = "gemini-1.5-flash"
                self.available = True
                print(f"AI Assistant: Connected to Google ({self.model_name})")
                
        except Exception as e:
            print(f"AI/LLM connection failed: {e}")
            self.available = False

    def generate_commentary(self, z_score: float, correlation: float, stationarity: dict) -> str:
        if not self.available:
            return "AI Assistant unavailable."
            
        if pd.isna(z_score):
            return "Insufficient data."

        context_prompt = (
            f"You are a crypto quant trader. "
            f"Metrics: Z-Score {z_score:.2f} (Threshold 2.0), Correlation {correlation:.2f}. "
            f"Explain regime and action in 1 sentence."
        )
        
        try:
            if self.provider == "groq":
                response = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": context_prompt}],
                    model=self.model_name,
                )
                return response.choices[0].message.content
            else:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=context_prompt
                )
                return response.text
        except Exception as e:
            print(f"AI Error: {e}. Switching to fallback.")
            if "authentication" in str(e).lower() or "key" in str(e).lower():
                st.toast(f"❌ AI Auth Error: Check API Key", icon="⚠️")
            else:
                st.toast(f"⚠️ AI Error: {e}", icon="🤖")
            return self._generate_fallback(z_score, correlation)

    def _generate_fallback(self, z: float, corr: float) -> str:
        """
        Deterministic fallback logic when AI is unavailable.
        """
        action = "HOLD"
        regime = "Neutral"
        
        if z > 2.0:
            regime = "Overbought (Mean Reversion)"
            action = "SELL / SHORT B against A"
        elif z < -2.0:
            regime = "Oversold (Mean Reversion)"
            action = "BUY / LONG B against A"
        elif abs(z) < 1.0:
            regime = "Random Walk / Noise"
            action = "WAIT"
            
        return (
            f" [OFFLINE MODE] Regime: {regime}. Z-Score is {z:.2f}. "
            f"Correlation is {corr:.2f}. Suggested Action: {action}."
        )

    def answer_question(self, question: str, context: dict) -> str:
        """
        Answer user questions with context using Gemini.
        """
        if not self.available:
            return "AI Assistant offline."

        z = context.get('z_score', 0)
        corr = context.get('correlation', 0)
        
        prompt = (
            f"Context: Z-Score {z:.2f}, Correlation {corr:.2f}. "
            f"Question: {question}. Answer as Risk Manager in 1 sentence."
        )
        
        try:
            if self.provider == "groq":
                response = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model_name,
                )
                return response.choices[0].message.content
            else:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                return "⚠️ API Quota Exceeded. Try again later."
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                return "⚠️ AI Service Overloaded. Try again later."
            return f"Error: {e}"


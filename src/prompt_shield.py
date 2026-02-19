import os
from dotenv import load_dotenv
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.contentsafety.models import AnalyzeTextOptions
from datetime import datetime

class PromptShield:
    def __init__(self):
        load_dotenv()
        endpoint = os.getenv("CONTENT_SAFETY_ENDPOINT")
        key = os.getenv("CONTENT_SAFETY_KEY")
        
        self.client = ContentSafetyClient(endpoint, AzureKeyCredential(key))
    
    def detect_jailbreak(self, user_prompt: str) -> dict:
        """
        Detect jailbreak attempts and prompt injection
        
        Common patterns:
        - "Ignore previous instructions"
        - "You are now DAN"
        - "Bypass safety filters"
        - System prompt override attempts
        """
        try:
            # Pattern matching for known jailbreak attempts
            jailbreak_patterns = [
                "ignore previous",
                "ignore all",
                "you are now",
                "forget everything",
                "bypass",
                "override",
                "DAN mode",
                "jailbreak",
                "pretend you are",
                "[SYSTEM]",
                "###SYSTEM###"
            ]
            
            detected_patterns = []
            for pattern in jailbreak_patterns:
                if pattern.lower() in user_prompt.lower():
                    detected_patterns.append(pattern)
            
            # Azure Content Safety analysis
            request = AnalyzeTextOptions(text=user_prompt)
            response = self.client.analyze_text(request)
            
            # Check if it's trying to manipulate the system
            is_jailbreak = len(detected_patterns) > 0
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "prompt": user_prompt,
                "is_jailbreak_attempt": is_jailbreak,
                "detected_patterns": detected_patterns,
                "risk_score": len(detected_patterns) * 2,  # 0-10 scale
                "decision": "BLOCKED" if is_jailbreak else "APPROVED",
                "recommendation": self._get_recommendation(is_jailbreak, detected_patterns)
            }
            
            return results
        
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_recommendation(self, is_jailbreak: bool, patterns: list) -> str:
        if not is_jailbreak:
            return "✅ Prompt is safe to process"
        elif len(patterns) >= 3:
            return "🚫 CRITICAL: Block immediately and log for security review"
        else:
            return "⚠️ WARNING: Potential manipulation detected, sanitize before processing"
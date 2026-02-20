import os
from dotenv import load_dotenv
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.contentsafety.models import AnalyzeTextOptions
from datetime import datetime
import json

class TextModerator:
    def __init__(self):
        load_dotenv()
        endpoint = os.getenv("CONTENT_SAFETY_ENDPOINT")
        key = os.getenv("CONTENT_SAFETY_KEY")
        
        if not endpoint or not key:
            raise ValueError("Content Safety credentials not found")
        
        self.client = ContentSafetyClient(endpoint, AzureKeyCredential(key))
    
    def analyze_text(self, text: str, severity_threshold: int = 3) -> dict:
        """
        Comprehensive text analysis
        
        Args:
            text: Text to analyze
            severity_threshold: Block if ANY category >= this value (default: 3)
        
        Returns:
            Full analysis with categories, severity, decision
        """
        try:
            request = AnalyzeTextOptions(text=text)
            response = self.client.analyze_text(request)
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "text": text,
                "text_length": len(text),
                "categories": {},
                "overall_safe": True,
                "max_severity": 0,
                "flagged_categories": [],
                "decision": "APPROVED",
                "threshold_used": severity_threshold
            }
            
            # Process categories
            for category_result in response.categories_analysis:
                category_name = category_result.category.lower().replace("_", " ")
                severity = category_result.severity
                
                results["categories"][category_name] = {
                    "severity": severity,
                    "detected": severity > 0,
                    "risk_level": self._get_risk_level(severity),
                    "action": self._get_action(severity, severity_threshold)
                }
                
                # Track max severity
                if severity > results["max_severity"]:
                    results["max_severity"] = severity
                
                # Check against threshold
                if severity >= severity_threshold:
                    results["overall_safe"] = False
                    results["flagged_categories"].append(category_name)
            
            # Final decision based on threshold
            if results["max_severity"] >= severity_threshold:
                if results["max_severity"] >= 5:
                    results["decision"] = "BLOCKED"
                else:
                    results["decision"] = "REVIEW"
            else:
                results["decision"] = "APPROVED"
            
            return results
        
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "decision": "ERROR"
            }
    
    def _get_risk_level(self, severity: int) -> str:
        if severity == 0:
            return "None"
        elif severity <= 2:
            return "Low"
        elif severity <= 4:
            return "Medium"
        else:
            return "High"
    
    def _get_action(self, severity: int, threshold: int) -> str:
        if severity == 0:
            return "✅ Approve"
        elif severity < threshold:
            return "✅ Approve with logging"
        elif severity < 5:
            return "⚠️ Manual review required"
        else:
            return "🚫 Block immediately"
    
    def batch_analyze(self, texts: list, severity_threshold: int = 3, save_to_file: str = None) -> dict:
        """Batch analysis with statistics"""
        results = {
            "total": len(texts),
            "approved": 0,
            "review": 0,
            "blocked": 0,
            "errors": 0,
            "analyses": [],
            "threshold_used": severity_threshold
        }
        
        for text in texts:
            analysis = self.analyze_text(text, severity_threshold)
            results["analyses"].append(analysis)
            
            decision = analysis.get("decision", "ERROR")
            if decision == "APPROVED":
                results["approved"] += 1
            elif decision == "REVIEW":
                results["review"] += 1
            elif decision == "BLOCKED":
                results["blocked"] += 1
            else:
                results["errors"] += 1
        
        if save_to_file:
            with open(save_to_file, 'w') as f:
                json.dump(results, f, indent=2)
        
        return results
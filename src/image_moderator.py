import os
from dotenv import load_dotenv
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.contentsafety.models import AnalyzeImageOptions, ImageData
from datetime import datetime
import base64
from PIL import Image
import io

class ImageModerator:
    def __init__(self):
        load_dotenv()
        endpoint = os.getenv("CONTENT_SAFETY_ENDPOINT")
        key = os.getenv("CONTENT_SAFETY_KEY")
        region = os.getenv("CONTENT_SAFETY_REGION", "unknown")
        
        self.client = ContentSafetyClient(endpoint, AzureKeyCredential(key))
        self.region = region
    
    def check_availability(self) -> dict:
        """Check if image moderation is available in this region"""
        # Image analysis is only available in select regions
        supported_regions = ["eastus", "westeurope", "westus2", "southeastasia"]
        
        is_supported = any(region.lower() in self.region.lower() for region in supported_regions)
        
        return {
            "available": is_supported,
            "current_region": self.region,
            "supported_regions": supported_regions,
            "message": "✅ Image moderation available" if is_supported else 
                      f"⚠️ Image moderation not available in {self.region}. Supported regions: {', '.join(supported_regions)}"
        }
    
    def analyze_image(self, image_input, severity_threshold: int = 3) -> dict:
        """
        Analyze image from file path or uploaded file
        """
        try:
            # Handle different input types
            if isinstance(image_input, str):
                with open(image_input, "rb") as f:
                    image_bytes = f.read()
            else:
                image_bytes = image_input.read()
            
            image_data = base64.b64encode(image_bytes).decode('utf-8')
            img = Image.open(io.BytesIO(image_bytes))
            
            # Try analysis
            request = AnalyzeImageOptions(image=ImageData(content=image_data))
            response = self.client.analyze_image(request)
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "image_info": {
                    "format": img.format,
                    "size": f"{img.width}x{img.height}",
                    "mode": img.mode
                },
                "categories": {},
                "overall_safe": True,
                "max_severity": 0,
                "flagged_categories": [],
                "decision": "APPROVED",
                "threshold_used": severity_threshold
            }
            
            for category_result in response.categories_analysis:
                category_name = category_result.category.lower().replace("_", " ")
                severity = category_result.severity
                
                results["categories"][category_name] = {
                    "severity": severity,
                    "detected": severity > 0,
                    "risk_level": self._get_risk_level(severity)
                }
                
                if severity > results["max_severity"]:
                    results["max_severity"] = severity
                
                if severity >= severity_threshold:
                    results["overall_safe"] = False
                    results["flagged_categories"].append(category_name)
            
            if results["max_severity"] >= severity_threshold:
                results["decision"] = "BLOCKED" if results["max_severity"] >= 5 else "REVIEW"
            
            return results
        
        except Exception as e:
            error_msg = str(e)
            
            # Check if it's a region availability error
            if "not yet available" in error_msg.lower() or "not found" in error_msg.lower():
                availability = self.check_availability()
                return {
                    "error": "IMAGE_MODERATION_UNAVAILABLE",
                    "message": availability["message"],
                    "supported_regions": availability["supported_regions"],
                    "current_region": self.region,
                    "timestamp": datetime.now().isoformat(),
                    "decision": "ERROR"
                }
            
            return {
                "error": error_msg,
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
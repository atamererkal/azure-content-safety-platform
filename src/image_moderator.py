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
        
        self.client = ContentSafetyClient(endpoint, AzureKeyCredential(key))
    
    def analyze_image(self, image_input) -> dict:
        """
        Analyze image from file path or uploaded file
        
        Args:
            image_input: File path (str) or UploadedFile object
        """
        try:
            # Handle different input types
            if isinstance(image_input, str):
                # File path
                with open(image_input, "rb") as f:
                    image_bytes = f.read()
            else:
                # Streamlit UploadedFile
                image_bytes = image_input.read()
            
            # Convert to base64
            image_data = base64.b64encode(image_bytes).decode('utf-8')
            
            # Get image info
            img = Image.open(io.BytesIO(image_bytes))
            
            # Analyze
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
                "decision": "APPROVED"
            }
            
            # Process categories
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
                
                if severity > 2:
                    results["overall_safe"] = False
                    results["flagged_categories"].append(category_name)
                
                if severity >= 5:
                    results["decision"] = "BLOCKED"
                elif severity >= 3:
                    results["decision"] = "REVIEW"
            
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
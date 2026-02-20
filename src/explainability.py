"""
Explainable AI Module
Provides human-readable explanations for content moderation decisions
"""

class ModerationExplainer:
    
    @staticmethod
    def explain_text_decision(result: dict) -> dict:
        """
        Generate explanation for text moderation decision
        
        Returns:
            {
                "decision_summary": str,
                "key_factors": list,
                "detailed_reasoning": str,
                "confidence_explanation": str
            }
        """
        decision = result.get("decision", "ERROR")
        max_severity = result.get("max_severity", 0)
        flagged = result.get("flagged_categories", [])
        categories = result.get("categories", {})
        threshold = result.get("threshold_used", 3)
        
        explanation = {
            "decision_summary": "",
            "key_factors": [],
            "detailed_reasoning": "",
            "confidence_explanation": ""
        }
        
        # Decision summary
        if decision == "APPROVED":
            explanation["decision_summary"] = f"✅ Content approved because all categories scored below the threshold ({threshold}/7)."
        elif decision == "REVIEW":
            explanation["decision_summary"] = f"⚠️ Manual review required because {len(flagged)} category(ies) scored {threshold}-4/7."
        elif decision == "BLOCKED":
            explanation["decision_summary"] = f"🚫 Content blocked because severity reached {max_severity}/7 (critical threshold: 5+)."
        else:
            explanation["decision_summary"] = "❌ Analysis failed due to technical error."
            return explanation
        
        # Key factors
        for cat_name, cat_data in categories.items():
            severity = cat_data["severity"]
            
            if severity >= 5:
                explanation["key_factors"].append(
                    f"🔴 **{cat_name.title()}** scored {severity}/7 (HIGH RISK) - "
                    f"Content contains clearly harmful {cat_name} material."
                )
            elif severity >= threshold:
                explanation["key_factors"].append(
                    f"⚠️ **{cat_name.title()}** scored {severity}/7 (MEDIUM RISK) - "
                    f"Content shows concerning {cat_name} indicators."
                )
            elif severity > 0:
                explanation["key_factors"].append(
                    f"✓ **{cat_name.title()}** scored {severity}/7 (LOW RISK) - "
                    f"Minor {cat_name} signals detected but within acceptable limits."
                )
        
        # Detailed reasoning
        if decision == "APPROVED":
            explanation["detailed_reasoning"] = (
                f"The AI analyzed this content across 4 categories (hate, violence, self-harm, sexual). "
                f"The highest severity detected was {max_severity}/7, which is below the blocking threshold. "
                f"This indicates the content is safe for publication according to community standards."
            )
        
        elif decision == "REVIEW":
            flagged_text = ", ".join([f"**{cat}**" for cat in flagged])
            explanation["detailed_reasoning"] = (
                f"The AI flagged {flagged_text} with severity {threshold}-4/7. "
                f"While not immediately harmful, this content requires human judgment to assess context, "
                f"intent, and potential violations. A moderator should review before publication."
            )
        
        elif decision == "BLOCKED":
            flagged_text = ", ".join([f"**{cat}**" for cat in flagged])
            explanation["detailed_reasoning"] = (
                f"The AI detected severe violations in {flagged_text} with severity {max_severity}/7. "
                f"This score indicates content that is clearly harmful, violates platform policies, "
                f"or poses risk to users. Automatic blocking prevents immediate publication."
            )
        
        # Confidence explanation
        avg_confidence = sum(cat["severity"] for cat in categories.values()) / len(categories)
        
        if avg_confidence <= 1:
            explanation["confidence_explanation"] = (
                "🟢 **High Confidence (Safe):** The AI is very confident this content is safe. "
                "Low scores across all categories indicate no harmful patterns detected."
            )
        elif avg_confidence <= 3:
            explanation["confidence_explanation"] = (
                "🟡 **Moderate Confidence:** The AI detected some concerning patterns but they're minor. "
                "Context and intent matter here—human review may provide additional clarity."
            )
        else:
            explanation["confidence_explanation"] = (
                "🔴 **High Confidence (Harmful):** The AI is very confident this content is harmful. "
                "Strong signals across multiple categories indicate clear policy violations."
            )
        
        return explanation
    
    @staticmethod
    def explain_image_decision(result: dict) -> dict:
        """Generate explanation for image moderation decision"""
        
        decision = result.get("decision", "ERROR")
        max_severity = result.get("max_severity", 0)
        flagged = result.get("flagged_categories", [])
        categories = result.get("categories", {})
        
        explanation = {
            "decision_summary": "",
            "key_factors": [],
            "detailed_reasoning": "",
            "visual_analysis": ""
        }
        
        # Decision summary
        if decision == "APPROVED":
            explanation["decision_summary"] = "✅ Image approved - No harmful visual content detected."
        elif decision == "REVIEW":
            explanation["decision_summary"] = f"⚠️ Image requires review - Detected concerning visual elements."
        elif decision == "BLOCKED":
            explanation["decision_summary"] = f"🚫 Image blocked - Contains prohibited visual content (severity {max_severity}/7)."
        else:
            explanation["decision_summary"] = "❌ Analysis failed."
            return explanation
        
        # Key factors
        for cat_name, cat_data in categories.items():
            severity = cat_data["severity"]
            
            if severity >= 5:
                explanation["key_factors"].append(
                    f"🔴 **{cat_name.title()}:** Detected graphic {cat_name} imagery (severity {severity}/7)"
                )
            elif severity >= 3:
                explanation["key_factors"].append(
                    f"⚠️ **{cat_name.title()}:** Detected concerning {cat_name} elements (severity {severity}/7)"
                )
        
        # Visual analysis
        if decision == "APPROVED":
            explanation["visual_analysis"] = (
                "The computer vision model analyzed this image for harmful visual patterns including "
                "graphic violence, explicit sexual content, hate symbols, and self-harm imagery. "
                "No significant harmful elements were detected."
            )
        
        elif decision == "REVIEW":
            flagged_text = ", ".join([f"**{cat}**" for cat in flagged])
            explanation["visual_analysis"] = (
                f"The model detected visual elements suggesting {flagged_text}. "
                f"These patterns scored {max_severity}/7, indicating moderate concern. "
                f"Context matters: news photos, medical imagery, or artistic content may trigger "
                f"false positives. Human review recommended."
            )
        
        elif decision == "BLOCKED":
            flagged_text = ", ".join([f"**{cat}**" for cat in flagged])
            explanation["visual_analysis"] = (
                f"The model identified clear {flagged_text} with high confidence ({max_severity}/7). "
                f"Visual patterns match known harmful content in the training dataset. "
                f"This indicates real-world harmful imagery that violates platform policies."
            )
        
        # Detailed reasoning
        explanation["detailed_reasoning"] = (
            f"**Image Analysis Process:**\n\n"
            f"1. **Feature Extraction:** AI analyzed visual patterns, colors, shapes, and objects\n"
            f"2. **Category Scoring:** Each harmful category received a severity score (0-7)\n"
            f"3. **Threshold Comparison:** Scores compared against policy thresholds\n"
            f"4. **Decision:** {decision} based on highest severity ({max_severity}/7)\n\n"
            f"**Note:** The AI is trained on real-world harmful content. Fictional or stylized "
            f"imagery (games, movies, art) typically scores low, which is expected behavior."
        )
        
        return explanation
    
    @staticmethod
    def explain_prompt_decision(result: dict) -> dict:
        """Generate explanation for prompt shield decision"""
        
        is_jailbreak = result.get("is_jailbreak_attempt", False)
        patterns = result.get("detected_patterns", [])
        risk_score = result.get("risk_score", 0)
        
        explanation = {
            "decision_summary": "",
            "key_factors": [],
            "detailed_reasoning": "",
            "security_analysis": ""
        }
        
        if is_jailbreak:
            explanation["decision_summary"] = f"🚫 Jailbreak attempt detected (Risk: {risk_score}/10)"
            
            explanation["key_factors"] = [
                f"🔴 Detected pattern: **'{pattern}'**" for pattern in patterns
            ]
            
            explanation["detailed_reasoning"] = (
                f"The prompt contains {len(patterns)} known jailbreak pattern(s) designed to "
                f"manipulate AI system behavior. These patterns attempt to bypass safety filters, "
                f"override instructions, or extract sensitive information."
            )
            
            explanation["security_analysis"] = (
                "**Attack Vector Analysis:**\n\n"
                f"• **Patterns Found:** {', '.join(patterns)}\n"
                f"• **Risk Level:** {'CRITICAL' if risk_score >= 8 else 'HIGH' if risk_score >= 5 else 'MEDIUM'}\n"
                f"• **Recommendation:** Block this prompt and log for security review\n"
                f"• **User Intent:** Likely attempting to manipulate system behavior"
            )
        
        else:
            explanation["decision_summary"] = "✅ Prompt is safe - No manipulation detected"
            
            explanation["detailed_reasoning"] = (
                "The prompt was analyzed for common jailbreak patterns including instruction override, "
                "system prompt extraction, and safety bypass attempts. No concerning patterns detected."
            )
            
            explanation["security_analysis"] = (
                "**Security Check Passed:**\n\n"
                "• No 'ignore previous instructions' patterns\n"
                "• No system prompt override attempts\n"
                "• No DAN/jailbreak mode activation\n"
                "• Safe to process normally"
            )
        
        return explanation
    
    @staticmethod
    def get_improvement_suggestions(result: dict, content_type: str) -> list:
        """
        Provide actionable suggestions for content creators
        """
        suggestions = []
        
        if content_type == "text":
            categories = result.get("categories", {})
            
            for cat_name, cat_data in categories.items():
                severity = cat_data["severity"]
                
                if severity >= 3:
                    if cat_name == "hate":
                        suggestions.append(
                            "💡 **Hate Speech Detected:** Remove discriminatory language, slurs, or "
                            "targeted harassment. Focus on ideas, not personal attacks."
                        )
                    elif cat_name == "violence":
                        suggestions.append(
                            "💡 **Violence Detected:** Remove threats, graphic descriptions, or "
                            "glorification of violence. Discuss issues without aggressive language."
                        )
                    elif cat_name == "self harm":
                        suggestions.append(
                            "💡 **Self-Harm Content:** Remove instructions or encouragement of self-injury. "
                            "If discussing mental health, add crisis resources (e.g., suicide hotline)."
                        )
                    elif cat_name == "sexual":
                        suggestions.append(
                            "💡 **Sexual Content:** Remove explicit descriptions or inappropriate material. "
                            "Keep content family-friendly and age-appropriate."
                        )
        
        elif content_type == "image":
            flagged = result.get("flagged_categories", [])
            
            for cat in flagged:
                if cat == "violence":
                    suggestions.append(
                        "💡 **Graphic Imagery:** Consider using less explicit alternatives or adding "
                        "content warnings. News/educational context may require human review."
                    )
                elif cat == "sexual":
                    suggestions.append(
                        "💡 **Explicit Content:** Ensure image complies with platform policies. "
                        "Remove nudity or sexual content unless in educational/medical context."
                    )
        
        if not suggestions:
            suggestions.append(
                "✅ **No Issues Found:** Your content meets platform guidelines. "
                "Continue creating positive, respectful content!"
            )
        
        return suggestions
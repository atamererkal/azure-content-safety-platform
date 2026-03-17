"""
Explainable AI Module
Provides human-readable, specific explanations for content moderation decisions
"""

class ModerationExplainer:
    
    @staticmethod
    def _get_specific_text_explanation(category: str, severity: int, text: str) -> str:
        """Generate specific explanation based on detected patterns"""
        
        text_lower = text.lower()
        
        if category == "hate":
            patterns = []
            if "hate" in text_lower:
                patterns.append("hate speech language")
            if any(word in text_lower for word in ["stupid", "idiot", "trash", "garbage"]):
                patterns.append("derogatory terms")
            if "[group]" in text_lower or "people from" in text_lower:
                patterns.append("targeting specific groups")
            
            if patterns:
                return f"Contains {', '.join(patterns)} (severity {severity}/7)"
            return f"Hate speech patterns detected with severity {severity}/7"
        
        elif category == "violence":
            patterns = []
            if any(word in text_lower for word in ["kill", "hurt", "attack", "harm"]):
                patterns.append("threatening language")
            if any(word in text_lower for word in ["weapon", "gun", "knife", "bomb"]):
                patterns.append("weapon references")
            if "find you" in text_lower or "watch your back" in text_lower:
                patterns.append("direct threats")
            
            if patterns:
                return f"Contains {', '.join(patterns)} (severity {severity}/7)"
            return f"Violent content patterns detected with severity {severity}/7"
        
        elif category in ("self harm", "selfharm"):
            patterns = []
            if any(word in text_lower for word in ["suicide", "end it all", "kill myself"]):
                patterns.append("suicidal ideation")
            if any(word in text_lower for word in ["cut", "noose", "overdose", "slit", "step by step"]):
                patterns.append("self-harm methods")
            if any(word in text_lower for word in ["no way out", "want to die", "want it to stop", "notice i was gone"]):
                patterns.append("hopelessness language")

            if patterns:
                return f"Contains {', '.join(patterns)} (severity {severity}/7)"
            return f"Self-harm content detected with severity {severity}/7"
        
        elif category == "sexual":
            return f"Contains explicit sexual content or inappropriate material (severity {severity}/7)"
        
        return f"Detected concerning {category} content (severity {severity}/7)"
    
    @staticmethod
    def _get_specific_image_explanation(category: str, severity: int) -> str:
        """Generate specific explanation for image detection"""
        
        if category == "violence":
            if severity >= 6:
                return "Image contains graphic violence: visible injuries, blood, or weapons being used"
            elif severity >= 4:
                return "Image shows violent elements: weapons, aggressive actions, or threatening poses"
            else:
                return "Image has mild violent elements: action scenes or fictional combat"
        
        elif category in ("selfharm", "self harm"):
            if severity >= 6:
                return "Image shows self-harm evidence: cutting marks, suicide methods, or injury tools"
            elif severity >= 4:
                return "Image contains self-harm related elements"
            else:
                return "Image has minor self-harm indicators"
        
        elif category == "sexual":
            if severity >= 6:
                return "Image contains explicit sexual content: nudity or sexual acts"
            elif severity >= 4:
                return "Image shows sexually suggestive content"
            else:
                return "Image has mild sexual elements"
        
        elif category == "hate":
            if severity >= 6:
                return "Image displays hate symbols: swastikas, extremist flags, or discriminatory imagery"
            elif severity >= 4:
                return "Image contains potentially hateful symbols or gestures"
            else:
                return "Image has elements that may be interpreted as hateful"
        
        return f"Detected {category} with severity {severity}/7"
    
    @staticmethod
    def explain_text_decision(result: dict) -> dict:
        """Generate specific explanation for text moderation decision"""
        
        decision = result.get("decision", "ERROR")
        max_severity = result.get("max_severity", 0)
        flagged = result.get("flagged_categories", [])
        categories = result.get("categories", {})
        threshold = result.get("threshold_used", 3)
        text = result.get("text", "")
        
        explanation = {
            "decision_summary": "",
            "key_factors": [],
            "detailed_reasoning": "",
            "specific_violations": []
        }
        
        # Decision summary
        if decision == "APPROVED":
            explanation["decision_summary"] = f"✅ Content approved - all categories scored below threshold ({threshold}/7)"
        elif decision == "REVIEW":
            explanation["decision_summary"] = f"⚠️ Manual review required - {len(flagged)} category(ies) scored {threshold}-4/7"
        elif decision == "BLOCKED":
            explanation["decision_summary"] = f"🚫 Content blocked - severity {max_severity}/7 exceeds critical threshold"
        
        # Specific violations with exact reasons
        for cat_name, cat_data in categories.items():
            severity = cat_data["severity"]
            
            if severity > 0:
                specific = ModerationExplainer._get_specific_text_explanation(cat_name, severity, text)
                
                if severity >= 5:
                    explanation["key_factors"].append(f"🔴 **{cat_name.title()}:** {specific}")
                    explanation["specific_violations"].append(specific)
                elif severity >= threshold:
                    explanation["key_factors"].append(f"⚠️ **{cat_name.title()}:** {specific}")
                    explanation["specific_violations"].append(specific)
        
        # Trigger keywords for detailed section
        trigger_list = ModerationExplainer.get_trigger_keywords(text, categories)
        trigger_summary = ""
        if trigger_list:
            keyword_lines = []
            for t in trigger_list:
                keyword_lines.append(
                    f'- **"{t["word"]}"** → _{t["category"].title()}_ signal '
                    f'(severity {t["severity"]}/7)'
                )
            trigger_summary = "\n\n**Detected trigger words/phrases:**\n" + "\n".join(keyword_lines)

        # Category breakdown table
        cat_lines = []
        for cat, data in categories.items():
            sev = data["severity"]
            risk = data["risk_level"]
            bar = "█" * sev + "░" * (7 - sev)
            cat_lines.append(f"- **{cat.title()}**: {bar} {sev}/7 ({risk})")
        cat_breakdown = "\n\n**Category breakdown:**\n" + "\n".join(cat_lines)

        # Detailed reasoning
        if decision == "BLOCKED":
            violation_details = " | ".join(explanation["specific_violations"])
            explanation["detailed_reasoning"] = (
                f"**Why was this blocked?**\n\n"
                f"The AI detected: {violation_details}."
                f"{trigger_summary}"
                f"{cat_breakdown}\n\n"
                f"Maximum severity ({max_severity}/7) exceeds the critical auto-block threshold (5/7). "
                f"This content is automatically rejected without requiring manual review. "
                f"The combination of detected signals indicates a high-confidence policy violation."
            )
        elif decision == "REVIEW":
            violation_details = " | ".join(explanation["specific_violations"])
            explanation["detailed_reasoning"] = (
                f"**Why does this need review?**\n\n"
                f"The AI detected: {violation_details}."
                f"{trigger_summary}"
                f"{cat_breakdown}\n\n"
                f"Severity ({max_severity}/7) falls in the ambiguous range (threshold {threshold}–4). "
                f"This score indicates potentially harmful content, but context matters — "
                f"satire, news reporting, or academic discussion may use similar language legitimately. "
                f"A human moderator should evaluate intent before making a final decision."
            )
        else:
            explanation["detailed_reasoning"] = (
                f"**Why was this approved?**\n\n"
                f"The AI analyzed this content across all four harm categories and found no significant "
                f"policy violations. All category scores fall below the configured threshold ({threshold}/7)."
                f"{cat_breakdown}\n\n"
                f"Content is cleared for publication. Note: approval reflects absence of detected harm signals "
                f"— context-specific moderation rules may still apply."
            )
        
        return explanation
    
    @staticmethod
    def explain_image_decision(result: dict) -> dict:
        """Generate specific explanation for image moderation decision"""
        
        decision = result.get("decision", "ERROR")
        max_severity = result.get("max_severity", 0)
        flagged = result.get("flagged_categories", [])
        categories = result.get("categories", {})
        
        explanation = {
            "decision_summary": "",
            "key_factors": [],
            "detailed_reasoning": "",
            "specific_violations": []
        }
        
        # Decision summary
        if decision == "APPROVED":
            explanation["decision_summary"] = "✅ Image approved - no harmful visual content detected"
        elif decision == "REVIEW":
            explanation["decision_summary"] = "⚠️ Image requires review - detected concerning visual elements"
        elif decision == "BLOCKED":
            explanation["decision_summary"] = f"🚫 Image blocked - contains prohibited visual content (severity {max_severity}/7)"
        
        # Specific visual violations
        for cat_name, cat_data in categories.items():
            severity = cat_data["severity"]
            
            if severity > 0:
                specific = ModerationExplainer._get_specific_image_explanation(cat_name, severity)
                
                if severity >= 5:
                    explanation["key_factors"].append(f"🔴 **{cat_name.title()}:** {specific}")
                    explanation["specific_violations"].append(specific)
                elif severity >= 3:
                    explanation["key_factors"].append(f"⚠️ **{cat_name.title()}:** {specific}")
                    explanation["specific_violations"].append(specific)
        
        # Detailed reasoning
        if decision == "BLOCKED":
            violation_details = " | ".join(explanation["specific_violations"])
            explanation["detailed_reasoning"] = (
                f"**What was detected in this image?**\n\n"
                f"{violation_details}\n\n"
                f"The computer vision model identified visual patterns that match harmful content "
                f"in the training dataset (severity {max_severity}/7). This indicates real-world "
                f"harmful imagery that violates platform policies."
            )
        elif decision == "REVIEW":
            violation_details = " | ".join(explanation["specific_violations"])
            explanation["detailed_reasoning"] = (
                f"**What triggered the review?**\n\n"
                f"{violation_details}\n\n"
                f"While concerning, context matters. This could be news photography, medical imagery, "
                f"or artistic content. Human review will determine if this is acceptable."
            )
        else:
            explanation["detailed_reasoning"] = (
                "**Why was this approved?**\n\n"
                "The AI analyzed visual elements and found no harmful patterns. "
                "The image is safe for publication."
            )
        
        return explanation
    
    @staticmethod
    def explain_prompt_decision(result: dict) -> dict:
        """Generate specific explanation for prompt shield decision"""
        
        is_jailbreak = result.get("is_jailbreak_attempt", False)
        patterns = result.get("detected_patterns", [])
        risk_score = result.get("risk_score", 0)
        
        explanation = {
            "decision_summary": "",
            "key_factors": [],
            "detailed_reasoning": ""
        }
        
        if is_jailbreak:
            explanation["decision_summary"] = f"🚫 Jailbreak attempt detected (Risk: {risk_score}/10)"
            
            # Specific patterns
            for pattern in patterns:
                explanation["key_factors"].append(
                    f"🔴 Detected: **'{pattern}'** - attempts to override system instructions"
                )
            
            explanation["detailed_reasoning"] = (
                f"**What attack patterns were found?**\n\n"
                f"The prompt contains phrases like: {', '.join([f'**{p}**' for p in patterns])}\n\n"
                f"These are known manipulation techniques used to bypass AI safety filters. "
                f"The prompt attempts to override system instructions or extract sensitive information."
            )
        else:
            explanation["decision_summary"] = "✅ Prompt is safe - no manipulation detected"
            explanation["detailed_reasoning"] = (
                "**Why is this safe?**\n\n"
                "The prompt was analyzed for manipulation patterns. No attempts to override "
                "instructions, extract system prompts, or bypass safety filters were detected."
            )
        
        return explanation
    
    @staticmethod
    def get_trigger_keywords(text: str, categories: dict) -> list:
        """
        Return list of dicts {word, category, severity} for words that triggered the decision.
        Only returns triggers for categories with severity > 0.
        """
        text_lower = text.lower()

        keyword_map = {
            "hate": [
                "hate", "stupid", "idiot", "trash", "garbage", "deport",
                "inferior", "filthy", "disgusting", "vermin", "subhuman",
                "people from", "those people",
            ],
            "violence": [
                "kill", "murder", "hurt", "attack", "harm", "beat", "destroy",
                "weapon", "gun", "knife", "bomb", "shoot", "stab", "strangle",
                "find you", "watch your back", "you'll pay", "come for you",
                "badly", "threat",
            ],
            "selfharm": [
                "suicide", "end it all", "kill myself", "want to die",
                "cut", "noose", "overdose", "self-harm", "slit wrists",
                "step by step", "no way out", "notice i was gone",
                "want it to stop", "tie a noose",
            ],
            "sexual": [
                "explicit", "nude", "naked", "sexual", "porn", "erotic",
                "inappropriate",
            ],
        }

        triggers = []
        seen_words = set()

        for category, patterns in keyword_map.items():
            cat_data = categories.get(category, {})
            severity = cat_data.get("severity", 0)
            if severity == 0:
                continue
            for pattern in patterns:
                if pattern in text_lower and pattern not in seen_words:
                    idx = text_lower.find(pattern)
                    actual_word = text[idx: idx + len(pattern)]
                    triggers.append({
                        "word": actual_word,
                        "category": category,
                        "severity": severity,
                    })
                    seen_words.add(pattern)

        return triggers

    @staticmethod
    def get_improvement_suggestions(result: dict, content_type: str) -> list:
        """Provide specific, actionable suggestions"""
        
        suggestions = []
        decision = result.get("decision", "APPROVED")
        
        # Only suggest improvements for flagged content
        if decision == "APPROVED":
            return []
        
        if content_type == "text":
            categories = result.get("categories", {})
            text = result.get("text", "").lower()
            
            for cat_name, cat_data in categories.items():
                severity = cat_data["severity"]
                
                if severity >= 3:
                    if cat_name == "hate":
                        suggestions.append(
                            "💡 **Remove hate speech:** Delete discriminatory language, slurs, or group-targeting statements"
                        )
                    elif cat_name == "violence":
                        if "kill" in text or "hurt" in text:
                            suggestions.append(
                                "💡 **Remove threats:** Delete threatening language like 'kill', 'hurt', 'attack'"
                            )
                        else:
                            suggestions.append(
                                "💡 **Reduce violence:** Remove aggressive language or weapon references"
                            )
                    elif cat_name in ("self harm", "selfharm"):
                        suggestions.append(
                            "💡 **Remove self-harm content:** Delete suicidal ideation or self-injury methods. "
                            "If discussing mental health, add crisis resources."
                        )
                    elif cat_name == "sexual":
                        suggestions.append(
                            "💡 **Remove explicit content:** Delete sexual descriptions or inappropriate material"
                        )
        
        elif content_type == "image":
            flagged = result.get("flagged_categories", [])
            
            for cat in flagged:
                if "violence" in cat:
                    suggestions.append(
                        "💡 **Use alternative imagery:** Replace graphic images with less explicit alternatives or add content warnings"
                    )
                elif "self" in cat and "harm" in cat:
                    suggestions.append(
                        "💡 **Remove harmful imagery:** This image shows self-harm. Consider removing or using educational context only"
                    )
                elif "sexual" in cat:
                    suggestions.append(
                        "💡 **Remove explicit imagery:** Ensure image complies with platform policies (no nudity/sexual content)"
                    )
        
        return suggestions
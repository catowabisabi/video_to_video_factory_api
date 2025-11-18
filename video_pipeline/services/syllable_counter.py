"""
發音數計算器
支援英文、繁體中文（粵語近似）
"""
import re
from typing import List
from models import TranscriptSentence, SyllableData


class SyllableCounter:
    
    def __init__(self, language: str = "zh-TW"):
        self.language = language
    
    def count_syllables(self, text: str) -> int:
        """
        計算單句發音數
        """
        if self.language.startswith("zh"):
            # 中文：每個字算 1 個發音（簡化版）
            # 空格算 0.5（當作停頓）
            chars = re.findall(r'[\u4e00-\u9fff]', text)
            spaces = text.count(" ")
            return len(chars) + int(spaces * 0.5)
        
        elif self.language == "en":
            # 英文：用簡單 heuristic
            # 更精準可用 pyphen 或 syllables library
            words = re.findall(r'\b\w+\b', text.lower())
            total = 0
            for word in words:
                # 簡化規則：元音數
                vowels = re.findall(r'[aeiouy]+', word)
                total += max(1, len(vowels))
            return total
        
        else:
            # 默認：字數
            return len(text.split())
    
    def count_script(self, sentences: List[TranscriptSentence]) -> int:
        """計算整個 script 發音數"""
        return sum(self.count_syllables(s.text) for s in sentences)
    
    def count_all(
        self, 
        sentences: List[TranscriptSentence], 
        duration: float
    ) -> SyllableData:
        """
        計算全部 + per sentence
        """
        total_syllables = 0
        
        for sentence in sentences:
            syllables = self.count_syllables(sentence.text)
            sentence.syllables = syllables
            sentence.syllables_per_sec = syllables / sentence.duration if sentence.duration > 0 else 0
            total_syllables += syllables
        
        return SyllableData(
            total_syllables=total_syllables,
            total_duration=duration,
            syllables_per_sec=total_syllables / duration if duration > 0 else 0,
            sentences=sentences
        )
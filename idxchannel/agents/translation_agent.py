"""
Translation Agent
Translates Indonesian text to English
"""

from typing import Dict, Optional


class TranslationAgent:
    """Agent to translate Indonesian text to English"""
    
    def __init__(self, use_google_translate: bool = True, use_local_model: bool = False):
        """
        Initialize translation agent
        
        Args:
            use_google_translate: Use Google Translate API (requires googletrans)
            use_local_model: Use local HuggingFace model (requires transformers)
        """
        self.use_google_translate = use_google_translate
        self.use_local_model = use_local_model
        self.translator = None
        
        if use_google_translate:
            try:
                from googletrans import Translator
                self.translator = Translator()
            except ImportError:
                print("Warning: googletrans not installed. Install with: pip install googletrans==4.0.0-rc1")
                self.use_google_translate = False
        
        if use_local_model and not self.use_google_translate:
            try:
                from transformers import pipeline
                # Using Helsinki-NLP model for Indonesian to English
                self.translator = pipeline("translation", model="Helsinki-NLP/opus-mt-id-en")
            except ImportError:
                print("Warning: transformers not installed. Install with: pip install transformers torch")
                self.use_local_model = False
    
    def translate(self, text: str) -> Dict:
        """
        Translate Indonesian text to English
        
        Args:
            text: Indonesian text to translate
            
        Returns:
            Dict with translated text and metadata
        """
        if not text or not text.strip():
            return {
                "original_text": text,
                "translated_text": "",
                "translation_method": "none",
                "success": False
            }
        
        # Try Google Translate first
        if self.use_google_translate and self.translator:
            try:
                result = self.translator.translate(text, src='id', dest='en')
                return {
                    "original_text": text,
                    "translated_text": result.text,
                    "translation_method": "google_translate",
                    "success": True
                }
            except Exception as e:
                print(f"Google Translate failed: {e}")
        
        # Try local model
        if self.use_local_model and self.translator:
            try:
                # Local model has text length limits, so chunk if necessary
                translated = self._translate_with_local_model(text)
                return {
                    "original_text": text,
                    "translated_text": translated,
                    "translation_method": "local_model",
                    "success": True
                }
            except Exception as e:
                print(f"Local model translation failed: {e}")
        
        # If all methods fail, return original
        return {
            "original_text": text,
            "translated_text": text,  # Return original as fallback
            "translation_method": "fallback_original",
            "success": False
        }
    
    def translate_article(self, article: Dict) -> Dict:
        """
        Translate all text fields in an article
        
        Args:
            article: Article dict with text fields
            
        Returns:
            Article with translated fields added
        """
        translated_article = article.copy()
        
        # Translate title
        if "title" in article and article["title"]:
            title_result = self.translate(article["title"])
            translated_article["title_translated"] = title_result["translated_text"]
            translated_article["title_original"] = title_result["original_text"]
        
        # Translate summary
        if "summary" in article and article["summary"]:
            summary_result = self.translate(article["summary"])
            translated_article["summary_translated"] = summary_result["translated_text"]
            translated_article["summary_original"] = summary_result["original_text"]
        
        # Translate content (main text)
        if "content" in article and article["content"]:
            content_result = self.translate(article["content"])
            translated_article["content_translated"] = content_result["translated_text"]
            translated_article["content_original"] = content_result["original_text"]
            translated_article["translation_method"] = content_result["translation_method"]
            translated_article["translation_success"] = content_result["success"]
        
        return translated_article
    
    def _translate_with_local_model(self, text: str, max_length: int = 512) -> str:
        """
        Translate text using local HuggingFace model with chunking support
        
        Args:
            text: Text to translate
            max_length: Maximum chunk length
            
        Returns:
            Translated text
        """
        if len(text) <= max_length:
            result = self.translator(text, max_length=max_length)
            return result[0]["translation_text"]
        
        # Chunk the text
        chunks = self._chunk_text(text, max_length)
        translated_chunks = []
        
        for chunk in chunks:
            result = self.translator(chunk, max_length=max_length)
            translated_chunks.append(result[0]["translation_text"])
        
        return " ".join(translated_chunks)
    
    def _chunk_text(self, text: str, max_length: int) -> list:
        """
        Split text into chunks at sentence boundaries
        
        Args:
            text: Text to split
            max_length: Maximum chunk length
            
        Returns:
            List of text chunks
        """
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if current_length + len(sentence) > max_length:
                if current_chunk:
                    chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence)
        
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
        
        return chunks

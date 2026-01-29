"""
Intent Classification Module - BUILD 6
Classifies user voice commands into actionable intents using semantic similarity.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer, util
import numpy as np


@dataclass
class IntentResult:
    """Result from intent classification."""
    intent: str
    confidence: float
    text: str
    latency_ms: float
    alternatives: Optional[List[tuple]] = None  # [(intent, confidence), ...]
    
    def __repr__(self):
        return f"IntentResult(intent='{self.intent}', confidence={self.confidence:.2f}, latency={self.latency_ms:.1f}ms)"


class IntentClassifier:
    """
    Semantic intent classifier using sentence embeddings.
    Maps natural language commands to predefined intents.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", intents_file: Optional[Path] = None):
        """
        Initialize intent classifier.
        
        Args:
            model_name: SentenceTransformer model name (lightweight and fast)
            intents_file: Path to intents.json file
        """
        # Load lightweight embedding model (~80MB, 20ms inference)
        self.model = SentenceTransformer(model_name)
        
        # Load intents configuration
        if intents_file is None:
            intents_file = Path(__file__).parent / "intents.json"
        
        with open(intents_file, 'r') as f:
            config = json.load(f)
            self.intents = config["intents"]
        
        # Pre-compute embeddings for all intent examples
        self._build_intent_index()
    
    def _build_intent_index(self):
        """Build embedding index for fast intent matching."""
        self.intent_examples = []  # [(intent_name, example_text), ...]
        
        for intent_name, intent_data in self.intents.items():
            # Add all examples for this intent
            for example in intent_data["examples"]:
                self.intent_examples.append((intent_name, example))
            
            # Also add keywords as examples
            if "keywords" in intent_data:
                for keyword in intent_data["keywords"]:
                    self.intent_examples.append((intent_name, keyword))
        
        # Pre-compute embeddings for all examples
        example_texts = [ex[1] for ex in self.intent_examples]
        self.example_embeddings = self.model.encode(
            example_texts,
            convert_to_tensor=True,
            show_progress_bar=False
        )
    
    async def classify(self, text: str, top_k: int = 3) -> IntentResult:
        """
        Classify text into an intent using semantic similarity.
        
        Args:
            text: User's voice command text
            top_k: Number of top matches to consider
            
        Returns:
            IntentResult with classified intent and confidence
        """
        start_time = time.perf_counter()
        
        # Handle empty input
        if not text or not text.strip():
            return IntentResult(
                intent="general_query",
                confidence=0.3,
                text=text,
                latency_ms=(time.perf_counter() - start_time) * 1000
            )
        
        # Encode the input text
        text_embedding = self.model.encode(
            text,
            convert_to_tensor=True,
            show_progress_bar=False
        )
        
        # Compute cosine similarity with all examples
        similarities = util.cos_sim(text_embedding, self.example_embeddings)[0]
        
        # Get top K matches
        top_results = similarities.topk(k=min(top_k * 5, len(similarities)))
        
        # Aggregate scores by intent (multiple examples per intent)
        intent_scores = {}
        for idx, score in zip(top_results.indices, top_results.values):
            intent_name = self.intent_examples[idx][0]
            score_val = float(score)
            
            # Keep the highest score for each intent
            if intent_name not in intent_scores:
                intent_scores[intent_name] = score_val
            else:
                intent_scores[intent_name] = max(intent_scores[intent_name], score_val)
        
        # Sort by score
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get top intent
        if sorted_intents:
            best_intent, best_score = sorted_intents[0]
        else:
            best_intent = "general_query"
            best_score = 0.5
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        return IntentResult(
            intent=best_intent,
            confidence=float(best_score),
            text=text,
            latency_ms=latency_ms,
            alternatives=sorted_intents[:top_k]
        )
    
    async def classify_batch(self, texts: List[str]) -> List[IntentResult]:
        """
        Classify multiple texts in batch for efficiency.
        
        Args:
            texts: List of user command texts
            
        Returns:
            List of IntentResults
        """
        results = []
        for text in texts:
            result = await self.classify(text)
            results.append(result)
        return results
    
    def get_intent_info(self, intent_name: str) -> Optional[Dict]:
        """Get information about a specific intent."""
        return self.intents.get(intent_name)
    
    def list_intents(self) -> List[str]:
        """Get list of all available intents."""
        return list(self.intents.keys())


if __name__ == "__main__":
    # Quick test
    import asyncio
    
    async def test():
        print("Loading intent classifier...")
        classifier = IntentClassifier()
        
        test_commands = [
            "run tests",
            "open main.py",
            "commit changes",
            "open youtube",
            "search for hellfire song"
        ]
        
        print(f"\nTesting {len(test_commands)} commands:\n")
        for cmd in test_commands:
            result = await classifier.classify(cmd)
            print(f"'{cmd}' -> {result}")
    
    asyncio.run(test())

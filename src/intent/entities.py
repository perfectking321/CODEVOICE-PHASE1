"""
Entity Extraction Module - BUILD 7
Extracts parameters and entities from natural language commands.
Uses pattern matching and NLP to identify files, paths, names, queries, etc.
"""

import re
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class EntityResult:
    """Result from entity extraction."""
    entities: Dict[str, Any]
    text: str
    intent: str
    latency_ms: float
    confidence: float = 1.0
    
    def __repr__(self):
        return f"EntityResult(entities={self.entities}, intent='{self.intent}', latency={self.latency_ms:.1f}ms)"


class EntityExtractor:
    """
    Extracts entities from commands based on intent context.
    Uses rule-based patterns and regex for fast, reliable extraction.
    """
    
    def __init__(self):
        """Initialize entity extractor with pattern rules."""
        # Define extraction patterns for each intent category
        self.patterns = {
            "open_file": self._build_file_patterns(),
            "create_file": self._build_create_file_patterns(),
            "create_function": self._build_function_patterns(),
            "git_commit": self._build_commit_patterns(),
            "git_push": self._build_push_patterns(),
            "git_status": [],  # No entities needed for git status
            "install_package": self._build_package_patterns(),
            "open_browser": self._build_browser_patterns(),
            "search_content": self._build_search_patterns(),
            "search_code": self._build_search_patterns(),
            "run_tests": self._build_test_patterns(),
        }
    
    def _build_file_patterns(self) -> List[Dict]:
        """Patterns for extracting filenames and paths."""
        return [
            {
                "key": "file",
                "regex": r'(?:open|show|edit|navigate to|file)\s+([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+)',
                "priority": 1
            },
            {
                "key": "file",
                "regex": r'([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+)',  # Any file-like pattern
                "priority": 2
            },
            {
                "key": "file",
                "regex": r'(?:the |file )?([a-zA-Z0-9_\-]+(?:\.[a-zA-Z0-9]+)?)',  # Loose match
                "priority": 3
            }
        ]
    
    def _build_create_file_patterns(self) -> List[Dict]:
        """Patterns for extracting filenames when creating files."""
        return [
            {
                "key": "file",
                "regex": r'(?:create|make|new)\s+(?:file|a file|new file)\s+([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+)',
                "priority": 1
            },
            {
                "key": "file",
                "regex": r'(?:file)\s+([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+)',
                "priority": 2
            },
            {
                "key": "file",
                "regex": r'([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+)',  # Any filename pattern
                "priority": 3
            }
        ]
    
    def _build_function_patterns(self) -> List[Dict]:
        """Patterns for extracting function names and descriptions."""
        return [
            {
                "key": "function_name",
                "regex": r'(?:function|method)\s+(?:called\s+)?([a-zA-Z_][a-zA-Z0-9_]*)',
                "priority": 1
            },
            {
                "key": "function_name",
                "regex": r'create\s+(?:a\s+)?(?:function\s+)?([a-zA-Z_][a-zA-Z0-9_]*)',
                "priority": 2
            },
            {
                "key": "description",
                "regex": r'(?:to|that|for)\s+(.+)',
                "priority": 3
            }
        ]
    
    def _build_commit_patterns(self) -> List[Dict]:
        """Patterns for extracting commit messages."""
        return [
            {
                "key": "message",
                "regex": r'(?:message|msg|with message|with msg)\s+["\']?([^"\']+)["\']?',
                "priority": 1
            },
            {
                "key": "message",
                "regex": r'commit\s+(?:changes?\s+)?(?:with\s+)?(.+)',
                "priority": 2
            }
        ]
    
    def _build_push_patterns(self) -> List[Dict]:
        """Patterns for extracting branch names."""
        return [
            {
                "key": "branch",
                "regex": r'(?:to|branch)\s+([a-zA-Z0-9_\-/]+)',
                "priority": 1
            },
            {
                "key": "remote",
                "regex": r'(?:remote|origin)\s+([a-zA-Z0-9_\-/]+)',
                "priority": 2
            }
        ]
    
    def _build_package_patterns(self) -> List[Dict]:
        """Patterns for extracting package names."""
        return [
            {
                "key": "package",
                "regex": r'(?:install|add|pip install|npm install)\s+([a-zA-Z0-9_\-\.]+)',
                "priority": 1
            },
            {
                "key": "package",
                "regex": r'(?:package|dependency)\s+([a-zA-Z0-9_\-\.]+)',
                "priority": 2
            },
            {
                "key": "package",
                "regex": r'\b([a-zA-Z0-9_\-\.]+)\b',  # Last resort: any identifier
                "priority": 3
            }
        ]
    
    def _build_browser_patterns(self) -> List[Dict]:
        """Patterns for extracting URLs and website names."""
        return [
            {
                "key": "url",
                "regex": r'(?:https?://)?([a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)',
                "priority": 1
            },
            {
                "key": "site",
                "regex": r'(?:open|go to|navigate to)\s+([a-zA-Z0-9\-]+)',
                "priority": 2
            },
            {
                "key": "site",
                "regex": r'\b(youtube|google|github|stackoverflow|reddit|twitter)\b',
                "priority": 3
            }
        ]
    
    def _build_search_patterns(self) -> List[Dict]:
        """Patterns for extracting search queries."""
        return [
            {
                "key": "query",
                "regex": r'(?:search|find|look up|look for)\s+(?:for\s+)?["\']?([^"\']+)["\']?',
                "priority": 1
            },
            {
                "key": "query",
                "regex": r'(?:search|find)\s+(.+)',
                "priority": 2
            }
        ]
    
    def _build_test_patterns(self) -> List[Dict]:
        """Patterns for extracting test names or patterns."""
        return [
            {
                "key": "test_pattern",
                "regex": r'(?:test|tests)\s+([a-zA-Z0-9_\-./]+)',
                "priority": 1
            },
            {
                "key": "test_file",
                "regex": r'(test_[a-zA-Z0-9_]+\.py)',
                "priority": 2
            }
        ]
    
    async def extract(self, text: str, intent: str) -> EntityResult:
        """
        Extract entities from text based on intent.
        
        Args:
            text: Command text
            intent: Classified intent (helps select appropriate patterns)
            
        Returns:
            EntityResult with extracted entities
        """
        start_time = time.perf_counter()
        entities = {}
        
        # Get patterns for this intent
        patterns = self.patterns.get(intent, [])
        
        # Sort by priority
        patterns = sorted(patterns, key=lambda p: p.get("priority", 99))
        
        # Apply each pattern
        for pattern_info in patterns:
            key = pattern_info["key"]
            regex = pattern_info["regex"]
            
            # Skip if we already found this entity
            if key in entities:
                continue
            
            # Try to match
            match = re.search(regex, text, re.IGNORECASE)
            if match:
                # Extract the captured group
                value = match.group(1).strip()
                
                # Clean up the value
                value = self._clean_entity_value(value, key)
                
                if value:  # Only add if not empty after cleaning
                    entities[key] = value
        
        # Special handling for specific intents
        if intent == "open_browser" and "site" in entities and "url" not in entities:
            # Convert site name to URL
            site = entities["site"].lower()
            if not site.startswith("http"):
                entities["url"] = f"https://www.{site}.com"
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        return EntityResult(
            entities=entities,
            text=text,
            intent=intent,
            latency_ms=latency_ms,
            confidence=1.0 if entities else 0.5
        )
    
    def _clean_entity_value(self, value: str, key: str) -> str:
        """Clean extracted entity value."""
        # Remove common stopwords at start/end
        stopwords = ["the", "a", "an", "to", "for", "with", "and", "or"]
        
        words = value.split()
        
        # Remove leading stopwords
        while words and words[0].lower() in stopwords:
            words.pop(0)
        
        # Remove trailing stopwords
        while words and words[-1].lower() in stopwords:
            words.pop()
        
        value = " ".join(words)
        
        # Clean up specific entity types
        if key == "file" or key == "filename":
            # Remove surrounding quotes
            value = value.strip('"\'')
            # Remove "file" word if present
            value = re.sub(r'\bfile\b', '', value, flags=re.IGNORECASE).strip()
        
        elif key == "message":
            # Remove leading action words
            value = re.sub(r'^(?:commit|message|msg)\s+', '', value, flags=re.IGNORECASE)
        
        elif key == "package":
            # Just keep the package name, no version
            value = value.split()[0] if ' ' in value else value
        
        return value.strip()
    
    async def extract_batch(self, items: List[tuple]) -> List[EntityResult]:
        """
        Extract entities from multiple (text, intent) pairs.
        
        Args:
            items: List of (text, intent) tuples
            
        Returns:
            List of EntityResults
        """
        results = []
        for text, intent in items:
            result = await self.extract(text, intent)
            results.append(result)
        return results


if __name__ == "__main__":
    # Quick test
    import asyncio
    
    async def test():
        print("Testing entity extractor...")
        extractor = EntityExtractor()
        
        test_cases = [
            ("open main.py", "open_file"),
            ("commit with message fix bug", "git_commit"),
            ("install numpy", "install_package"),
            ("search for python tutorial", "search_content"),
            ("open youtube", "open_browser"),
        ]
        
        print(f"\nTesting {len(test_cases)} commands:\n")
        for text, intent in test_cases:
            result = await extractor.extract(text, intent)
            print(f"'{text}' ({intent}) -> {result.entities}")
    
    asyncio.run(test())

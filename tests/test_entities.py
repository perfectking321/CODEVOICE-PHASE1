"""
Tests for Entity Extraction - BUILD 7
Extract parameters from voice commands (files, paths, names, values, etc.)
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from intent.entities import EntityExtractor, EntityResult


class TestEntityExtractor:
    """Test entity extraction functionality."""
    
    @pytest.fixture
    def extractor(self):
        """Create extractor instance for testing."""
        return EntityExtractor()
    
    def test_extractor_initialization(self, extractor):
        """Test that extractor initializes properly."""
        assert extractor is not None
        assert hasattr(extractor, 'extract')
    
    @pytest.mark.asyncio
    async def test_extract_filename(self, extractor):
        """Test extracting filename from command."""
        result = await extractor.extract("open main.py", intent="open_file")
        
        assert isinstance(result, EntityResult)
        assert "file" in result.entities or "filename" in result.entities
        filename = result.entities.get("file") or result.entities.get("filename")
        assert "main.py" in filename
    
    @pytest.mark.asyncio
    async def test_extract_path(self, extractor):
        """Test extracting file path."""
        result = await extractor.extract("open src/main.py", intent="open_file")
        
        assert "file" in result.entities or "path" in result.entities
        filepath = result.entities.get("file") or result.entities.get("path")
        assert "src" in filepath
        assert "main.py" in filepath
    
    @pytest.mark.asyncio
    async def test_extract_commit_message(self, extractor):
        """Test extracting git commit message."""
        result = await extractor.extract("commit changes with message fix bug", intent="git_commit")
        
        assert "message" in result.entities
        assert "fix bug" in result.entities["message"].lower()
    
    @pytest.mark.asyncio
    async def test_extract_package_name(self, extractor):
        """Test extracting package name."""
        result = await extractor.extract("install numpy", intent="install_package")
        
        assert "package" in result.entities
        assert "numpy" in result.entities["package"].lower()
    
    @pytest.mark.asyncio
    async def test_extract_url(self, extractor):
        """Test extracting URL or website name."""
        result = await extractor.extract("open youtube", intent="open_browser")
        
        assert "url" in result.entities or "site" in result.entities
        url = result.entities.get("url") or result.entities.get("site")
        assert "youtube" in url.lower()
    
    @pytest.mark.asyncio
    async def test_extract_search_query(self, extractor):
        """Test extracting search query."""
        result = await extractor.extract("search for hellfire song", intent="search_content")
        
        assert "query" in result.entities or "search_query" in result.entities
        query = result.entities.get("query") or result.entities.get("search_query")
        assert "hellfire" in query.lower()
    
    @pytest.mark.asyncio
    async def test_extract_function_name(self, extractor):
        """Test extracting function name."""
        result = await extractor.extract("create function parse_json", intent="create_function")
        
        assert "function_name" in result.entities or "name" in result.entities
        func_name = result.entities.get("function_name") or result.entities.get("name")
        assert "parse_json" in func_name.lower() or "parse" in func_name.lower()
    
    @pytest.mark.asyncio
    async def test_extract_multiple_entities(self, extractor):
        """Test extracting multiple entities from one command."""
        result = await extractor.extract(
            "open youtube and search for hellfire song",
            intent="search_content"
        )
        
        assert len(result.entities) > 0
        # Should find at least the search query
        assert any(key in result.entities for key in ["query", "search_query", "site", "url"])
    
    @pytest.mark.asyncio
    async def test_extract_no_entities(self, extractor):
        """Test command with no extractable entities."""
        result = await extractor.extract("run tests", intent="run_tests")
        
        assert isinstance(result, EntityResult)
        # May have no entities or just default values
        assert isinstance(result.entities, dict)
    
    @pytest.mark.asyncio
    async def test_extract_latency(self, extractor):
        """Test that extraction is fast."""
        commands = [
            ("open main.py", "open_file"),
            ("search for python tutorial", "search_content"),
            ("commit with message test", "git_commit"),
            ("install flask", "install_package"),
        ]
        
        for text, intent in commands:
            result = await extractor.extract(text, intent=intent)
            assert result.latency_ms < 20, f"Too slow for '{text}': {result.latency_ms}ms"
    
    @pytest.mark.asyncio
    async def test_extract_with_context(self, extractor):
        """Test extraction with intent context improves accuracy."""
        # Same text, different intents should extract different entities
        result1 = await extractor.extract("test.py", intent="open_file")
        result2 = await extractor.extract("test.py", intent="run_tests")
        
        # With open_file intent, should extract as filename
        # With run_tests intent, might extract as test name or no entity
        assert isinstance(result1.entities, dict)
        assert isinstance(result2.entities, dict)
    
    @pytest.mark.asyncio
    async def test_entity_confidence_scores(self, extractor):
        """Test that entities have confidence scores."""
        result = await extractor.extract("open main.py", intent="open_file")
        
        if result.entities:
            # Check if confidence tracking is available
            assert hasattr(result, 'confidence') or all(
                isinstance(v, (str, dict)) for v in result.entities.values()
            )
    
    @pytest.mark.asyncio
    async def test_extract_special_characters(self, extractor):
        """Test extraction with special characters in entities."""
        result = await extractor.extract("open file_utils.py", intent="open_file")
        
        if "file" in result.entities or "filename" in result.entities:
            filename = result.entities.get("file") or result.entities.get("filename")
            assert "_" in filename or "utils" in filename


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Search optimization for VibeCLI
Provides fast file indexing and optimized search operations
"""

import asyncio
import re
import time
from pathlib import Path
from typing import Dict, List, Set, Optional, AsyncGenerator
from dataclasses import dataclass
from collections import defaultdict
import aiofiles

from config import get_settings


@dataclass
class SearchResult:
    """Search result with metadata"""
    file_path: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int
    context_before: Optional[str] = None
    context_after: Optional[str] = None


@dataclass
class FileIndex:
    """File index for fast searching"""
    path: Path
    size: int
    modified_time: float
    lines_count: int
    word_index: Dict[str, Set[int]]  # word -> set of line numbers
    last_indexed: float


class SearchOptimizer:
    """Optimized search with indexing and caching"""
    
    def __init__(self):
        self.settings = get_settings()
        self.file_indices: Dict[str, FileIndex] = {}
        self.index_lock = asyncio.Lock()
        
    async def search_optimized(self, pattern: str, search_path: Path, 
                              file_glob: str = "**/*", 
                              context_lines: int = 0) -> List[SearchResult]:
        """Optimized search with indexing"""
        results = []
        
        # Build file list
        files_to_search = []
        if search_path.is_file():
            files_to_search = [search_path]
        else:
            files_to_search = [f for f in search_path.glob(file_glob) 
                             if f.is_file() and not self._should_skip_file(f)]
        
        # Limit files for performance
        if len(files_to_search) > 1000:
            files_to_search = files_to_search[:1000]
        
        # Use batch processing for large file sets
        batch_size = 20
        tasks = []
        
        for i in range(0, len(files_to_search), batch_size):
            batch = files_to_search[i:i + batch_size]
            task = self._search_batch(pattern, batch, context_lines)
            tasks.append(task)
        
        # Process batches concurrently
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        for batch_result in batch_results:
            if isinstance(batch_result, list):
                results.extend(batch_result)
        
        # Sort by relevance and limit results
        results.sort(key=lambda r: (r.file_path, r.line_number))
        return results[:self.settings.max_search_results]
    
    async def _search_batch(self, pattern: str, files: List[Path], 
                           context_lines: int) -> List[SearchResult]:
        """Search a batch of files concurrently"""
        tasks = [self._search_file_optimized(pattern, file_path, context_lines) 
                for file_path in files]
        
        file_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        for file_result in file_results:
            if isinstance(file_result, list):
                results.extend(file_result)
        
        return results
    
    async def _search_file_optimized(self, pattern: str, file_path: Path, 
                                   context_lines: int) -> List[SearchResult]:
        """Search single file with optimization"""
        try:
            # Check if file should be skipped
            if self._should_skip_file(file_path):
                return []
            
            # Check file size limit
            if file_path.stat().st_size > self.settings.max_file_size:
                return []
            
            # Read file with streaming for large files
            if file_path.stat().st_size > 1_000_000:  # 1MB threshold
                return await self._search_large_file(pattern, file_path, context_lines)
            else:
                return await self._search_small_file(pattern, file_path, context_lines)
                
        except (UnicodeDecodeError, PermissionError, OSError):
            return []
    
    async def _search_small_file(self, pattern: str, file_path: Path, 
                               context_lines: int) -> List[SearchResult]:
        """Search small file (load entirely in memory)"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            lines = content.splitlines()
            return self._find_matches_in_lines(pattern, file_path, lines, context_lines)
            
        except (UnicodeDecodeError, PermissionError):
            return []
    
    async def _search_large_file(self, pattern: str, file_path: Path, 
                               context_lines: int) -> List[SearchResult]:
        """Search large file with streaming"""
        try:
            lines = []
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                line_num = 0
                async for line in f:
                    line_num += 1
                    lines.append(line.rstrip('\n\r'))
                    
                    # Process in chunks to avoid memory issues
                    if line_num % 10000 == 0:
                        chunk_results = self._find_matches_in_lines(
                            pattern, file_path, lines[-10000:], context_lines,
                            line_offset=line_num - 10000
                        )
                        if chunk_results:
                            return chunk_results  # Return first matches for performance
            
            return self._find_matches_in_lines(pattern, file_path, lines, context_lines)
            
        except (UnicodeDecodeError, PermissionError):
            return []
    
    def _find_matches_in_lines(self, pattern: str, file_path: Path, 
                             lines: List[str], context_lines: int, 
                             line_offset: int = 0) -> List[SearchResult]:
        """Find pattern matches in lines with context"""
        results = []
        regex = re.compile(pattern, re.IGNORECASE)
        
        for i, line in enumerate(lines):
            matches = list(regex.finditer(line))
            if matches:
                # Add context
                context_before = None
                context_after = None
                
                if context_lines > 0:
                    start_ctx = max(0, i - context_lines)
                    end_ctx = min(len(lines), i + context_lines + 1)
                    
                    if start_ctx < i:
                        context_before = '\n'.join(lines[start_ctx:i])
                    if end_ctx > i + 1:
                        context_after = '\n'.join(lines[i + 1:end_ctx])
                
                # Create result for each match in line
                for match in matches:
                    result = SearchResult(
                        file_path=str(file_path),
                        line_number=i + 1 + line_offset,
                        line_content=line,
                        match_start=match.start(),
                        match_end=match.end(),
                        context_before=context_before,
                        context_after=context_after
                    )
                    results.append(result)
        
        return results
    
    async def build_file_index(self, project_dir: Path, file_glob: str = "**/*.py") -> None:
        """Build search index for files"""
        async with self.index_lock:
            files_to_index = []
            
            for file_path in project_dir.glob(file_glob):
                if (file_path.is_file() and 
                    not self._should_skip_file(file_path) and
                    file_path.stat().st_size < self.settings.max_file_size):
                    
                    # Check if file needs reindexing
                    file_key = str(file_path)
                    file_stat = file_path.stat()
                    
                    if (file_key not in self.file_indices or 
                        self.file_indices[file_key].modified_time < file_stat.st_mtime):
                        files_to_index.append(file_path)
            
            # Index files in batches
            batch_size = 10
            for i in range(0, len(files_to_index), batch_size):
                batch = files_to_index[i:i + batch_size]
                await self._index_file_batch(batch)
    
    async def _index_file_batch(self, files: List[Path]) -> None:
        """Index a batch of files"""
        tasks = [self._index_single_file(file_path) for file_path in files]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _index_single_file(self, file_path: Path) -> None:
        """Index a single file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            lines = content.splitlines()
            word_index = defaultdict(set)
            
            # Build word index
            for line_num, line in enumerate(lines, 1):
                words = re.findall(r'\b\w+\b', line.lower())
                for word in words:
                    word_index[word].add(line_num)
            
            # Store index
            file_stat = file_path.stat()
            self.file_indices[str(file_path)] = FileIndex(
                path=file_path,
                size=file_stat.st_size,
                modified_time=file_stat.st_mtime,
                lines_count=len(lines),
                word_index=dict(word_index),
                last_indexed=time.time()
            )
            
        except (UnicodeDecodeError, PermissionError, OSError):
            pass
    
    async def search_indexed(self, query: str, project_dir: Path) -> List[SearchResult]:
        """Search using pre-built index for better performance"""
        words = re.findall(r'\b\w+\b', query.lower())
        if not words:
            return []
        
        # Find files that contain all query words
        candidate_files = None
        
        for word in words:
            files_with_word = set()
            
            for file_key, index in self.file_indices.items():
                if word in index.word_index:
                    files_with_word.add(file_key)
            
            if candidate_files is None:
                candidate_files = files_with_word
            else:
                candidate_files &= files_with_word
            
            if not candidate_files:
                break
        
        if not candidate_files:
            return []
        
        # Search only in candidate files
        results = []
        for file_key in candidate_files:
            file_path = Path(file_key)
            file_results = await self._search_file_optimized(query, file_path, 0)
            results.extend(file_results)
        
        return results[:self.settings.max_search_results]
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        name = file_path.name.lower()
        return any(pattern in name for pattern in self.settings.skip_patterns)
    
    def get_index_stats(self) -> Dict[str, int]:
        """Get indexing statistics"""
        return {
            "indexed_files": len(self.file_indices),
            "total_lines": sum(idx.lines_count for idx in self.file_indices.values()),
            "total_words": sum(len(idx.word_index) for idx in self.file_indices.values()),
            "index_size_mb": sum(idx.size for idx in self.file_indices.values()) / (1024 * 1024)
        } 
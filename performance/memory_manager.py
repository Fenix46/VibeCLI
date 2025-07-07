"""
Memory management for VibeCLI
Handles large file operations and prevents memory exhaustion
"""

import asyncio
import sys
import gc
from typing import AsyncIterator, List, Optional, Dict, Any
from pathlib import Path
import aiofiles
from dataclasses import dataclass

from config import get_settings


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    current_usage_mb: float
    peak_usage_mb: float
    available_mb: float
    files_in_memory: int
    cache_size_mb: float


class MemoryManager:
    """Memory management for file operations"""
    
    def __init__(self, max_memory_mb: int = 500):
        self.settings = get_settings()
        self.max_memory_mb = max_memory_mb
        self.file_cache: Dict[str, bytes] = {}
        self.cache_sizes: Dict[str, int] = {}
        self.access_order: List[str] = []
        self.current_memory_mb = 0.0
        self.peak_memory_mb = 0.0
        
    async def read_file_chunked(self, file_path: Path, 
                              chunk_size: int = 8192) -> AsyncIterator[str]:
        """Read file in chunks to manage memory"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                while True:
                    chunk = await f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except (UnicodeDecodeError, PermissionError):
            return
    
    async def read_file_lines_chunked(self, file_path: Path, 
                                    max_lines: int = 1000) -> AsyncIterator[List[str]]:
        """Read file lines in chunks"""
        try:
            lines_buffer = []
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                async for line in f:
                    lines_buffer.append(line.rstrip('\n\r'))
                    
                    if len(lines_buffer) >= max_lines:
                        yield lines_buffer
                        lines_buffer = []
                
                # Yield remaining lines
                if lines_buffer:
                    yield lines_buffer
                    
        except (UnicodeDecodeError, PermissionError):
            return
    
    async def read_file_cached(self, file_path: Path) -> Optional[str]:
        """Read file with caching and memory management"""
        file_key = str(file_path)
        
        # Check cache first
        if file_key in self.file_cache:
            self._update_access_order(file_key)
            return self.file_cache[file_key].decode('utf-8', errors='replace')
        
        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size > self.settings.max_file_size:
                return None
                
            file_size_mb = file_size / (1024 * 1024)
            
            # Ensure we have enough memory
            await self._ensure_memory_available(file_size_mb)
            
            # Read file
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            
            # Cache if small enough
            if file_size_mb < 10:  # Cache files smaller than 10MB
                self._add_to_cache(file_key, content)
            
            return content.decode('utf-8', errors='replace')
            
        except (OSError, PermissionError, UnicodeDecodeError):
            return None
    
    async def process_large_file(self, file_path: Path, 
                               processor: callable, 
                               chunk_size: int = 1024 * 1024) -> Any:
        """Process large file without loading entirely into memory"""
        results = []
        
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                while True:
                    chunk = await f.read(chunk_size)
                    if not chunk:
                        break
                    
                    # Process chunk
                    try:
                        chunk_text = chunk.decode('utf-8', errors='replace')
                        result = await processor(chunk_text)
                        if result:
                            results.append(result)
                    except Exception:
                        continue
                    
                    # Force garbage collection periodically
                    if len(results) % 100 == 0:
                        gc.collect()
        
        except (OSError, PermissionError):
            pass
        
        return results
    
    async def _ensure_memory_available(self, required_mb: float) -> None:
        """Ensure enough memory is available"""
        while (self.current_memory_mb + required_mb) > self.max_memory_mb:
            if not self._evict_oldest_cache():
                break  # No more cache to evict
    
    def _add_to_cache(self, file_key: str, content: bytes) -> None:
        """Add file to cache"""
        size_mb = len(content) / (1024 * 1024)
        
        self.file_cache[file_key] = content
        self.cache_sizes[file_key] = len(content)
        self.current_memory_mb += size_mb
        
        # Update peak memory
        if self.current_memory_mb > self.peak_memory_mb:
            self.peak_memory_mb = self.current_memory_mb
        
        self._update_access_order(file_key)
    
    def _update_access_order(self, file_key: str) -> None:
        """Update access order for LRU eviction"""
        if file_key in self.access_order:
            self.access_order.remove(file_key)
        self.access_order.append(file_key)
    
    def _evict_oldest_cache(self) -> bool:
        """Evict oldest cache entry"""
        if not self.access_order:
            return False
        
        oldest_key = self.access_order.pop(0)
        
        if oldest_key in self.file_cache:
            size_bytes = self.cache_sizes[oldest_key]
            size_mb = size_bytes / (1024 * 1024)
            
            del self.file_cache[oldest_key]
            del self.cache_sizes[oldest_key]
            self.current_memory_mb -= size_mb
            
            return True
        
        return False
    
    def clear_cache(self) -> None:
        """Clear all cached files"""
        self.file_cache.clear()
        self.cache_sizes.clear()
        self.access_order.clear()
        self.current_memory_mb = 0.0
    
    def get_memory_stats(self) -> MemoryStats:
        """Get memory usage statistics"""
        # Get system memory info (simplified)
        import psutil
        
        try:
            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024 * 1024)
        except ImportError:
            available_mb = 0.0
        
        return MemoryStats(
            current_usage_mb=self.current_memory_mb,
            peak_usage_mb=self.peak_memory_mb,
            available_mb=available_mb,
            files_in_memory=len(self.file_cache),
            cache_size_mb=self.current_memory_mb
        )
    
    async def smart_file_read(self, file_path: Path) -> Optional[str]:
        """Smart file reading that chooses the best strategy based on file size"""
        try:
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            # Skip very large files
            if file_size > self.settings.max_file_size:
                return None
            
            # For small files, use cached read
            if file_size_mb < 1:  # Less than 1MB
                return await self.read_file_cached(file_path)
            
            # For medium files, read without caching
            elif file_size_mb < 10:  # 1-10MB
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    return await f.read()
            
            # For large files, use chunked reading
            else:
                content_chunks = []
                async for chunk in self.read_file_chunked(file_path, chunk_size=64*1024):
                    content_chunks.append(chunk)
                return ''.join(content_chunks)
                
        except (OSError, PermissionError, UnicodeDecodeError):
            return None
    
    async def process_files_memory_efficient(self, file_paths: List[Path], 
                                           processor: callable) -> List[Any]:
        """Process multiple files with memory efficiency"""
        results = []
        
        # Sort files by size (process larger files first to manage memory better)
        try:
            sorted_files = sorted(file_paths, 
                                key=lambda p: p.stat().st_size if p.exists() else 0, 
                                reverse=True)
        except OSError:
            sorted_files = file_paths
        
        for file_path in sorted_files:
            try:
                content = await self.smart_file_read(file_path)
                if content:
                    result = await processor(file_path, content)
                    if result:
                        results.append(result)
                
                # Periodic garbage collection
                if len(results) % 50 == 0:
                    gc.collect()
                    
                # Check memory usage
                stats = self.get_memory_stats()
                if stats.current_usage_mb > self.max_memory_mb * 0.8:
                    # Clear cache if using too much memory
                    self.clear_cache()
                    gc.collect()
                    
            except Exception:
                continue
        
        return results
    
    def optimize_memory_settings(self) -> None:
        """Optimize memory settings based on available memory"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024 * 1024 * 1024)
            
            # Adjust max memory based on available memory
            if available_gb > 8:
                self.max_memory_mb = 1000  # 1GB
            elif available_gb > 4:
                self.max_memory_mb = 500   # 500MB
            else:
                self.max_memory_mb = 200   # 200MB
                
        except ImportError:
            # Default conservative setting if psutil not available
            self.max_memory_mb = 200 
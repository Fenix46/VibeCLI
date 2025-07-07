"""
Async batch processing for VibeCLI
Optimizes concurrent operations to prevent resource exhaustion
"""

import asyncio
import time
from typing import List, Callable, Any, Optional, Dict, TypeVar, Awaitable, AsyncIterator
from dataclasses import dataclass
from collections import deque

from config import get_settings

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class BatchResult:
    """Result of batch processing"""
    success_count: int
    error_count: int
    results: List[Any]
    errors: List[Exception]
    duration: float


@dataclass
class BatchStats:
    """Statistics for batch processing"""
    total_processed: int
    total_errors: int
    average_duration: float
    throughput_per_second: float


class AsyncBatchProcessor:
    """Async batch processor with resource management"""
    
    def __init__(self, max_concurrent: int = 10, max_retries: int = 3):
        self.settings = get_settings()
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.stats = BatchStats(0, 0, 0.0, 0.0)
        self.processing_queue = deque()
        
    async def process_batch(self, items: List[T], 
                          processor: Callable[[T], Awaitable[R]], 
                          batch_size: Optional[int] = None) -> BatchResult:
        """Process items in batches with concurrency control"""
        if not items:
            return BatchResult(0, 0, [], [], 0.0)
        
        start_time = time.time()
        batch_size = batch_size or self.max_concurrent
        
        results = []
        errors = []
        success_count = 0
        error_count = 0
        
        # Process in batches to prevent memory issues
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await self._process_single_batch(batch, processor)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    errors.append(result)
                    error_count += 1
                else:
                    results.append(result)
                    success_count += 1
        
        duration = time.time() - start_time
        
        # Update stats
        self._update_stats(len(items), error_count, duration)
        
        return BatchResult(success_count, error_count, results, errors, duration)
    
    async def _process_single_batch(self, batch: List[T], 
                                  processor: Callable[[T], Awaitable[R]]) -> List[Any]:
        """Process a single batch with concurrency control"""
        tasks = [self._process_with_semaphore(item, processor) for item in batch]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_with_semaphore(self, item: T, 
                                    processor: Callable[[T], Awaitable[R]]) -> R:
        """Process single item with semaphore control"""
        async with self.semaphore:
            for attempt in range(self.max_retries + 1):
                try:
                    return await processor(item)
                except Exception as e:
                    if attempt == self.max_retries:
                        raise e
                    # Wait before retry (exponential backoff)
                    await asyncio.sleep(0.1 * (2 ** attempt))
    
    async def process_stream(self, items: List[T], 
                           processor: Callable[[T], Awaitable[R]], 
                           chunk_size: int = 100) -> AsyncIterator[R]:
        """Process items as a stream for memory efficiency"""
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            batch_result = await self.process_batch(chunk, processor)
            
            for result in batch_result.results:
                yield result
    
    async def process_with_progress(self, items: List[T], 
                                  processor: Callable[[T], Awaitable[R]], 
                                  progress_callback: Optional[Callable[[int, int], None]] = None,
                                  batch_size: Optional[int] = None) -> BatchResult:
        """Process with progress reporting"""
        if not items:
            return BatchResult(0, 0, [], [], 0.0)
        
        start_time = time.time()
        batch_size = batch_size or self.max_concurrent
        
        results = []
        errors = []
        success_count = 0
        error_count = 0
        total_processed = 0
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await self._process_single_batch(batch, processor)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    errors.append(result)
                    error_count += 1
                else:
                    results.append(result)
                    success_count += 1
                
                total_processed += 1
                
                # Report progress
                if progress_callback:
                    progress_callback(total_processed, len(items))
        
        duration = time.time() - start_time
        self._update_stats(len(items), error_count, duration)
        
        return BatchResult(success_count, error_count, results, errors, duration)
    
    async def process_file_batch(self, file_paths: List[str], 
                               file_processor: Callable[[str], Awaitable[R]],
                               max_file_size: Optional[int] = None) -> BatchResult:
        """Specialized batch processing for files"""
        from pathlib import Path
        
        max_size = max_file_size or self.settings.max_file_size
        
        # Filter files by size
        valid_files = []
        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists() and path.stat().st_size <= max_size:
                    valid_files.append(file_path)
            except (OSError, PermissionError):
                continue
        
        return await self.process_batch(valid_files, file_processor)
    
    def _update_stats(self, processed: int, errors: int, duration: float) -> None:
        """Update processing statistics"""
        total_before = self.stats.total_processed
        
        self.stats.total_processed += processed
        self.stats.total_errors += errors
        
        # Update average duration (weighted average)
        if total_before > 0:
            weight = total_before / (total_before + processed)
            self.stats.average_duration = (
                self.stats.average_duration * weight + 
                duration * (1 - weight)
            )
        else:
            self.stats.average_duration = duration
        
        # Calculate throughput
        if duration > 0:
            self.stats.throughput_per_second = processed / duration
    
    def get_stats(self) -> BatchStats:
        """Get processing statistics"""
        return self.stats
    
    def reset_stats(self) -> None:
        """Reset processing statistics"""
        self.stats = BatchStats(0, 0, 0.0, 0.0)
    
    async def process_with_rate_limit(self, items: List[T], 
                                    processor: Callable[[T], Awaitable[R]], 
                                    max_per_second: float = 10.0) -> BatchResult:
        """Process items with rate limiting"""
        if not items:
            return BatchResult(0, 0, [], [], 0.0)
        
        start_time = time.time()
        interval = 1.0 / max_per_second
        
        results = []
        errors = []
        success_count = 0
        error_count = 0
        
        last_process_time = 0.0
        
        for item in items:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - last_process_time
            
            if time_since_last < interval:
                await asyncio.sleep(interval - time_since_last)
            
            # Process item
            try:
                result = await self._process_with_semaphore(item, processor)
                results.append(result)
                success_count += 1
            except Exception as e:
                errors.append(e)
                error_count += 1
            
            last_process_time = time.time()
        
        duration = time.time() - start_time
        self._update_stats(len(items), error_count, duration)
        
        return BatchResult(success_count, error_count, results, errors, duration)
    
    async def adaptive_batch_size(self, items: List[T], 
                                processor: Callable[[T], Awaitable[R]], 
                                target_duration: float = 1.0) -> BatchResult:
        """Automatically adjust batch size based on performance"""
        if not items:
            return BatchResult(0, 0, [], [], 0.0)
        
        # Start with a small batch to measure performance
        initial_batch_size = min(10, len(items))
        sample_batch = items[:initial_batch_size]
        
        start_time = time.time()
        sample_result = await self.process_batch(sample_batch, processor, initial_batch_size)
        sample_duration = time.time() - start_time
        
        if sample_duration == 0:
            sample_duration = 0.001  # Avoid division by zero
        
        # Calculate optimal batch size
        throughput = initial_batch_size / sample_duration
        optimal_batch_size = max(1, int(throughput * target_duration))
        optimal_batch_size = min(optimal_batch_size, len(items), self.max_concurrent * 2)
        
        # Process remaining items with optimal batch size
        if len(items) > initial_batch_size:
            remaining_items = items[initial_batch_size:]
            remaining_result = await self.process_batch(remaining_items, processor, optimal_batch_size)
            
            # Combine results
            total_results = sample_result.results + remaining_result.results
            total_errors = sample_result.errors + remaining_result.errors
            total_duration = sample_result.duration + remaining_result.duration
            
            return BatchResult(
                sample_result.success_count + remaining_result.success_count,
                sample_result.error_count + remaining_result.error_count,
                total_results,
                total_errors,
                total_duration
            )
        
        return sample_result 
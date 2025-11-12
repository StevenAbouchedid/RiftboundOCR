"""
Tests for Parallel Processing Batch Endpoint
Tests the /process-batch-fast endpoint with ThreadPoolExecutor
"""

import pytest
import json
import io
from fastapi.testclient import TestClient
from PIL import Image
from unittest.mock import patch

from src.main import app
from src.config import settings


client = TestClient(app)


def create_test_image(width=800, height=1200, format='JPEG') -> bytes:
    """Create a simple test image in memory"""
    img = Image.new('RGB', (width, height), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format=format)
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()


def parse_sse_stream(response_text: str) -> list:
    """Parse SSE stream response into list of events"""
    events = []
    lines = response_text.strip().split('\n\n')
    
    for block in lines:
        if not block.strip():
            continue
        
        lines_in_block = block.strip().split('\n')
        event_type = None
        event_data = None
        
        for line in lines_in_block:
            if line.startswith('event: '):
                event_type = line.replace('event: ', '').strip()
            elif line.startswith('data: '):
                data_str = line.replace('data: ', '').strip()
                event_data = json.loads(data_str)
        
        if event_type and event_data:
            events.append({
                'event': event_type,
                'data': event_data
            })
    
    return events


class TestParallelProcessingEndpoint:
    """Test cases for /process-batch-fast endpoint"""
    
    def test_parallel_disabled_by_default(self):
        """Test that parallel processing is disabled by default"""
        files = [
            ('files', ('test1.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-fast", files=files)
        
        # Should return 400 if parallel is disabled
        assert response.status_code == 400
        assert 'parallel' in response.text.lower() or 'enable' in response.text.lower()
    
    @patch.object(settings, 'enable_parallel', True)
    @patch.object(settings, 'max_workers', 2)
    def test_parallel_enabled_single_image(self):
        """Test parallel processing with single image (should work)"""
        files = [
            ('files', ('test1.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-fast", files=files)
        
        # Should work even with single image
        assert response.status_code == 200
        assert 'text/event-stream' in response.headers['content-type']
    
    @patch.object(settings, 'enable_parallel', True)
    @patch.object(settings, 'max_workers', 2)
    def test_parallel_multiple_images(self):
        """Test parallel processing with multiple images"""
        files = [
            ('files', ('test1.jpg', create_test_image(), 'image/jpeg')),
            ('files', ('test2.jpg', create_test_image(), 'image/jpeg')),
            ('files', ('test3.jpg', create_test_image(), 'image/jpeg')),
            ('files', ('test4.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-fast", files=files)
        assert response.status_code == 200
        
        events = parse_sse_stream(response.text)
        
        # Should have events for all images
        progress_events = [e for e in events if e['event'] == 'progress']
        complete_events = [e for e in events if e['event'] == 'complete']
        
        assert len(progress_events) >= 4  # At least 4 images
        assert len(complete_events) == 1
        
        # Check completion stats
        complete = complete_events[0]['data']
        assert complete['total'] == 4
    
    @patch.object(settings, 'enable_parallel', True)
    @patch.object(settings, 'max_workers', 2)
    def test_parallel_sse_headers(self):
        """Test that parallel endpoint has correct SSE headers"""
        files = [
            ('files', ('test1.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-fast", files=files)
        
        assert response.status_code == 200
        assert 'text/event-stream' in response.headers['content-type']
        assert response.headers.get('cache-control') == 'no-cache'
        assert response.headers.get('x-accel-buffering') == 'no'
    
    @patch.object(settings, 'enable_parallel', True)
    @patch.object(settings, 'max_workers', 2)
    def test_parallel_event_structure(self):
        """Test that parallel endpoint emits correct event structure"""
        files = [
            ('files', ('test1.jpg', create_test_image(), 'image/jpeg')),
            ('files', ('test2.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-fast", files=files)
        events = parse_sse_stream(response.text)
        
        # Should have all event types
        event_types = set(e['event'] for e in events)
        assert 'progress' in event_types
        assert 'complete' in event_types
        # May have 'result' or 'error' depending on OCR initialization
    
    @patch.object(settings, 'enable_parallel', True)
    @patch.object(settings, 'max_workers', 2)
    def test_parallel_error_handling(self):
        """Test parallel processing with invalid files"""
        files = [
            ('files', ('valid.jpg', create_test_image(), 'image/jpeg')),
            ('files', ('invalid.txt', b'not an image', 'text/plain')),
            ('files', ('valid2.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-fast", files=files)
        events = parse_sse_stream(response.text)
        
        # Should have error events for invalid file
        error_events = [e for e in events if e['event'] == 'error']
        assert len(error_events) >= 1
        
        # Should still complete
        complete_events = [e for e in events if e['event'] == 'complete']
        assert len(complete_events) == 1
        
        complete = complete_events[0]['data']
        assert complete['failed'] >= 1
    
    @patch.object(settings, 'enable_parallel', True)
    @patch.object(settings, 'max_workers', 2)
    def test_parallel_batch_size_limit(self):
        """Test that parallel endpoint respects batch size limit"""
        # Create more files than max_batch_size
        files = [
            ('files', (f'test{i}.jpg', create_test_image(), 'image/jpeg'))
            for i in range(15)  # Exceeds default limit of 10
        ]
        
        response = client.post("/api/process-batch-fast", files=files)
        
        # Should return 400 error
        assert response.status_code == 400
        assert 'maximum' in response.text.lower() or 'batch' in response.text.lower()
    
    @patch.object(settings, 'enable_parallel', True)
    @patch.object(settings, 'max_workers', 4)
    def test_parallel_worker_count(self):
        """Test that worker count setting is respected"""
        files = [
            ('files', (f'test{i}.jpg', create_test_image(), 'image/jpeg'))
            for i in range(6)
        ]
        
        response = client.post("/api/process-batch-fast", files=files)
        
        # Should process successfully (can't directly test thread count, but should work)
        assert response.status_code == 200
        
        events = parse_sse_stream(response.text)
        complete_events = [e for e in events if e['event'] == 'complete']
        
        assert len(complete_events) == 1
        assert complete_events[0]['data']['total'] == 6


class TestParallelPerformance:
    """Performance comparison tests"""
    
    @pytest.mark.skipif(
        reason="Performance test - requires OCR models and takes time",
        condition=True  # Set to False to run performance tests
    )
    @patch.object(settings, 'enable_parallel', True)
    @patch.object(settings, 'max_workers', 2)
    def test_parallel_vs_sequential_performance(self):
        """Compare parallel vs sequential processing time"""
        import time
        
        files = [
            ('files', (f'test{i}.jpg', create_test_image(), 'image/jpeg'))
            for i in range(4)
        ]
        
        # Test sequential
        start = time.time()
        response_seq = client.post("/api/process-batch-stream", files=files)
        sequential_time = time.time() - start
        
        # Test parallel
        start = time.time()
        response_par = client.post("/api/process-batch-fast", files=files)
        parallel_time = time.time() - start
        
        print(f"\nSequential: {sequential_time:.2f}s")
        print(f"Parallel:   {parallel_time:.2f}s")
        print(f"Speedup:    {sequential_time / parallel_time:.2f}x")
        
        # Parallel should be faster (or at least not much slower)
        assert parallel_time <= sequential_time * 1.2  # Allow 20% margin


class TestParallelConfiguration:
    """Test configuration options"""
    
    def test_config_has_parallel_settings(self):
        """Test that config includes parallel processing settings"""
        assert hasattr(settings, 'enable_parallel')
        assert hasattr(settings, 'max_workers')
        
        # Default values
        assert isinstance(settings.enable_parallel, bool)
        assert isinstance(settings.max_workers, int)
        assert settings.max_workers > 0
    
    @patch.object(settings, 'enable_parallel', True)
    @patch.object(settings, 'max_workers', 1)
    def test_single_worker_parallel(self):
        """Test parallel processing with single worker (should still work)"""
        files = [
            ('files', ('test1.jpg', create_test_image(), 'image/jpeg')),
            ('files', ('test2.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-fast", files=files)
        
        # Should work even with single worker
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



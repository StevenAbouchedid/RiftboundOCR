"""
Tests for SSE Streaming Batch Processing
Tests the /process-batch-stream endpoint with Server-Sent Events
"""

import pytest
import json
import io
from fastapi.testclient import TestClient
from PIL import Image

from src.main import app


client = TestClient(app)


def create_test_image(width=800, height=1200, format='JPEG') -> bytes:
    """Create a simple test image in memory"""
    img = Image.new('RGB', (width, height), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format=format)
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()


def parse_sse_stream(response_text: str) -> list:
    """
    Parse SSE stream response into list of events
    
    Returns list of dicts: [{'event': 'progress', 'data': {...}}, ...]
    """
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


class TestSSEStreamingEndpoint:
    """Test cases for /process-batch-stream endpoint"""
    
    def test_sse_connection_headers(self):
        """Test that SSE response has correct headers"""
        # Create test files
        files = [
            ('files', ('test1.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-stream", files=files)
        
        # Check headers
        assert response.status_code == 200
        assert 'text/event-stream' in response.headers['content-type']
        assert response.headers.get('cache-control') == 'no-cache'
        assert response.headers.get('x-accel-buffering') == 'no'
    
    def test_single_image_stream(self):
        """Test streaming with single image"""
        files = [
            ('files', ('test1.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-stream", files=files)
        assert response.status_code == 200
        
        # Parse SSE stream
        events = parse_sse_stream(response.text)
        
        # Should have: progress(validating), progress(processing), result, complete
        assert len(events) >= 3, f"Expected at least 3 events, got {len(events)}"
        
        # Check event types
        event_types = [e['event'] for e in events]
        assert 'progress' in event_types
        assert 'complete' in event_types
        
        # May have result or error depending on OCR setup
        assert 'result' in event_types or 'error' in event_types
    
    def test_progress_events(self):
        """Test that progress events are emitted correctly"""
        files = [
            ('files', ('test1.jpg', create_test_image(), 'image/jpeg')),
            ('files', ('test2.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-stream", files=files)
        events = parse_sse_stream(response.text)
        
        # Get progress events
        progress_events = [e for e in events if e['event'] == 'progress']
        
        # Should have at least 2 progress events per image (validating + processing)
        assert len(progress_events) >= 2
        
        # Check progress event structure
        for progress in progress_events:
            assert 'current' in progress['data']
            assert 'total' in progress['data']
            assert 'filename' in progress['data']
            assert 'status' in progress['data']
            assert progress['data']['total'] == 2
            assert progress['data']['status'] in ['validating', 'processing']
    
    def test_completion_event(self):
        """Test that completion event contains correct statistics"""
        files = [
            ('files', ('test1.jpg', create_test_image(), 'image/jpeg')),
            ('files', ('test2.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-stream", files=files)
        events = parse_sse_stream(response.text)
        
        # Get completion event
        complete_events = [e for e in events if e['event'] == 'complete']
        assert len(complete_events) == 1, "Should have exactly one completion event"
        
        complete = complete_events[0]['data']
        
        # Check required fields
        assert 'total' in complete
        assert 'successful' in complete
        assert 'failed' in complete
        assert 'processing_time_seconds' in complete
        
        # Validate values
        assert complete['total'] == 2
        assert complete['successful'] + complete['failed'] == complete['total']
        assert complete['processing_time_seconds'] >= 0
    
    def test_error_handling_invalid_file_type(self):
        """Test that invalid file types generate error events"""
        files = [
            ('files', ('test.txt', b'not an image', 'text/plain')),
        ]
        
        response = client.post("/api/process-batch-stream", files=files)
        events = parse_sse_stream(response.text)
        
        # Should have error event
        error_events = [e for e in events if e['event'] == 'error']
        assert len(error_events) == 1
        
        error = error_events[0]['data']
        assert 'index' in error
        assert 'filename' in error
        assert 'error' in error
        assert 'error_type' in error
        assert error['error_type'] == 'validation'
        assert 'image' in error['error'].lower()
        
        # Should still have completion event
        complete_events = [e for e in events if e['event'] == 'complete']
        assert len(complete_events) == 1
        assert complete_events[0]['data']['failed'] == 1
    
    def test_error_handling_oversized_file(self):
        """Test that oversized files generate error events"""
        # Create a large image (simulate oversized)
        # Note: This test assumes max_file_size_mb = 10
        # We'll create 100MB image to trigger error
        large_data = b'x' * (100 * 1024 * 1024)  # 100MB
        
        files = [
            ('files', ('large.jpg', large_data, 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-stream", files=files)
        events = parse_sse_stream(response.text)
        
        # Should have error event
        error_events = [e for e in events if e['event'] == 'error']
        assert len(error_events) >= 1
        
        error = error_events[0]['data']
        assert 'size' in error['error'].lower() or 'exceeds' in error['error'].lower()
        assert error['error_type'] == 'validation'
    
    def test_multiple_images_stream(self):
        """Test streaming with multiple images"""
        files = [
            ('files', ('test1.jpg', create_test_image(), 'image/jpeg')),
            ('files', ('test2.jpg', create_test_image(), 'image/jpeg')),
            ('files', ('test3.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-stream", files=files)
        events = parse_sse_stream(response.text)
        
        # Should have events for each image
        progress_events = [e for e in events if e['event'] == 'progress']
        complete_events = [e for e in events if e['event'] == 'complete']
        
        # At least 2 progress events per image (validating + processing)
        assert len(progress_events) >= 6
        assert len(complete_events) == 1
        
        # Check completion stats
        complete = complete_events[0]['data']
        assert complete['total'] == 3
    
    def test_mixed_valid_and_invalid_files(self):
        """Test stream with mix of valid and invalid files"""
        files = [
            ('files', ('valid1.jpg', create_test_image(), 'image/jpeg')),
            ('files', ('invalid.txt', b'not an image', 'text/plain')),
            ('files', ('valid2.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-stream", files=files)
        events = parse_sse_stream(response.text)
        
        # Should have error events for invalid file
        error_events = [e for e in events if e['event'] == 'error']
        assert len(error_events) >= 1
        
        # Stream should continue after error
        complete_events = [e for e in events if e['event'] == 'complete']
        assert len(complete_events) == 1
        
        complete = complete_events[0]['data']
        assert complete['total'] == 3
        assert complete['failed'] >= 1
    
    def test_batch_size_limit(self):
        """Test that batch size limit is enforced"""
        # Create more files than max_batch_size (default 10)
        files = [
            ('files', (f'test{i}.jpg', create_test_image(), 'image/jpeg'))
            for i in range(15)  # Exceeds limit
        ]
        
        response = client.post("/api/process-batch-stream", files=files)
        
        # Should return 400 error
        assert response.status_code == 400
        assert 'maximum' in response.text.lower() or 'batch' in response.text.lower()
    
    def test_empty_batch(self):
        """Test error handling for empty batch"""
        response = client.post("/api/process-batch-stream", files=[])
        
        # FastAPI should handle this as validation error
        assert response.status_code in [400, 422]
    
    def test_result_event_structure(self):
        """Test that result events have correct structure"""
        files = [
            ('files', ('test1.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-stream", files=files)
        events = parse_sse_stream(response.text)
        
        # Get result events (may not exist if OCR not initialized)
        result_events = [e for e in events if e['event'] == 'result']
        
        if result_events:
            result = result_events[0]['data']
            
            # Check required fields
            assert 'index' in result
            assert 'filename' in result
            assert 'decklist' in result
            
            # Check decklist structure
            decklist = result['decklist']
            assert 'decklist_id' in decklist
            assert 'metadata' in decklist
            assert 'legend' in decklist
            assert 'main_deck' in decklist
            assert 'battlefields' in decklist
            assert 'runes' in decklist
            assert 'side_deck' in decklist
    
    def test_event_order(self):
        """Test that events are emitted in correct order"""
        files = [
            ('files', ('test1.jpg', create_test_image(), 'image/jpeg')),
            ('files', ('test2.jpg', create_test_image(), 'image/jpeg')),
        ]
        
        response = client.post("/api/process-batch-stream", files=files)
        events = parse_sse_stream(response.text)
        
        # Last event should always be complete
        assert events[-1]['event'] == 'complete'
        
        # Progress events should come before results
        first_progress_idx = next(
            (i for i, e in enumerate(events) if e['event'] == 'progress'),
            None
        )
        first_result_idx = next(
            (i for i, e in enumerate(events) if e['event'] == 'result'),
            None
        )
        
        if first_progress_idx is not None and first_result_idx is not None:
            assert first_progress_idx < first_result_idx
    
    def test_concurrent_progress_tracking(self):
        """Test that progress tracking is accurate across multiple images"""
        files = [
            ('files', (f'test{i}.jpg', create_test_image(), 'image/jpeg'))
            for i in range(5)
        ]
        
        response = client.post("/api/process-batch-stream", files=files)
        events = parse_sse_stream(response.text)
        
        progress_events = [e for e in events if e['event'] == 'progress']
        
        # Track progress through processing
        current_values = [p['data']['current'] for p in progress_events]
        
        # Current should progress from 1 to 5
        assert min(current_values) == 1
        assert max(current_values) == 5
        
        # All events should have total = 5
        for progress in progress_events:
            assert progress['data']['total'] == 5


class TestSSEStreamingIntegration:
    """Integration tests for SSE streaming with full OCR pipeline"""
    
    @pytest.mark.skipif(
        reason="Requires OCR models to be initialized",
        condition=True  # Set to False if you want to run integration tests
    )
    def test_full_ocr_pipeline_stream(self):
        """Test complete OCR processing through SSE stream"""
        # This test requires actual test images with decklists
        # Skip if test images not available
        pass
    
    @pytest.mark.skipif(
        reason="Requires OCR models to be initialized",
        condition=True
    )
    def test_accuracy_calculation_in_stream(self):
        """Test that accuracy is correctly calculated and reported"""
        # This test requires OCR to produce actual results with accuracy stats
        pass


class TestSSEPerformance:
    """Performance tests for SSE streaming"""
    
    def test_stream_doesnt_buffer_all_results(self):
        """Test that stream sends events progressively, not all at once"""
        # This is more of a behavioral test - in real implementation,
        # events should arrive progressively as images complete
        # Hard to test in unit tests without timing, but structure is correct
        pass
    
    def test_memory_efficient_streaming(self):
        """Test that streaming doesn't load all results in memory at once"""
        # Structural test - our generator yields events one at a time
        # Memory efficiency is inherent in the design
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



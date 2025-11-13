"""
FastAPI Routes for OCR Service
Handles image upload, processing, and decklist extraction
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Tuple
import tempfile
import os
import uuid
import logging
import json
import time
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Import DIRECT functions from working implementation (not classes!)
from src.ocr.parser import parse_with_two_stage
from src.ocr.matcher import CardMatcher
from src.models.schemas import (
    DecklistResponse,
    BatchProcessResponse,
    HealthResponse,
    StatsResponse,
    ErrorResponse,
    SSEProgressEvent,
    SSEResultEvent,
    SSEErrorEvent,
    SSECompleteEvent
)
from src.config import settings
from src.clients.riftbound_api import RiftboundAPIClient

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize main API client (optional - only if configured)
main_api_client = None
if settings.main_api_url and settings.main_api_url != "http://localhost:8000/api":
    try:
        main_api_client = RiftboundAPIClient(
            base_url=settings.main_api_url,
            api_key=settings.main_api_key
        )
        logger.info("Main API client initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize main API client: {e}")

# Initialize matcher (singleton pattern)
print("\n" + "=" * 60)
print("⚙️  INITIALIZING OCR SERVICE COMPONENTS")
print("=" * 60)
print(f"[1/3] Loading card matcher from: {settings.card_mapping_path}")
print(f"      File exists: {os.path.exists(settings.card_mapping_path)}")

try:
    matcher = CardMatcher(settings.card_mapping_path)
    print(f"✓ Card matcher loaded: {len(matcher.mappings)} cards indexed")
    logger.info(f"Card matcher initialized: {len(matcher.mappings)} cards")
except Exception as e:
    print(f"❌ FAILED to load card matcher: {e}")
    logger.error(f"Failed to initialize card matcher: {e}", exc_info=True)
    matcher = None

# Pre-initialize OCR models at module import (CRITICAL for Railway deployment)
print("\n[2/3] Pre-loading PaddleOCR (Chinese text recognition)...")
print("      This downloads ~15MB of models on first run (60-90 seconds)")
print("      Subsequent starts will be instant (models cached)")

try:
    from src.ocr.parser import get_paddle_ocr
    import time
    start = time.time()
    _ocr_paddle = get_paddle_ocr()  # Force initialization NOW
    elapsed = time.time() - start
    print(f"✓ PaddleOCR ready ({elapsed:.1f}s)")
    logger.info(f"PaddleOCR pre-loaded in {elapsed:.1f}s")
except Exception as e:
    print(f"❌ CRITICAL: PaddleOCR initialization failed: {e}")
    import traceback
    traceback.print_exc()
    logger.error(f"PaddleOCR init failed: {e}", exc_info=True)
    _ocr_paddle = None

print("\n[3/3] Pre-loading EasyOCR (English/numeric recognition)...")
print("      This downloads ~100MB of models on first run (60-90 seconds)")
print("      Subsequent starts will be instant (models cached)")
print("      ⚠ This prevents 20+ second timeouts on first request!")

try:
    from src.ocr.parser import get_easy_reader
    start = time.time()
    _ocr_easy = get_easy_reader()  # Force initialization NOW
    elapsed = time.time() - start
    print(f"✓ EasyOCR ready ({elapsed:.1f}s)")
    logger.info(f"EasyOCR pre-loaded in {elapsed:.1f}s")
except Exception as e:
    print(f"⚠ WARNING: EasyOCR initialization failed: {e}")
    print("   Quantity detection will be unavailable!")
    import traceback
    traceback.print_exc()
    logger.warning(f"EasyOCR init failed: {e}", exc_info=True)
    _ocr_easy = None

print("\n" + "=" * 60)
if _ocr_paddle and _ocr_easy:
    print("✅ ALL OCR MODELS PRE-LOADED - SERVICE READY!")
    print("   PaddleOCR: ✓ Ready (Chinese text)")
    print("   EasyOCR: ✓ Ready (English/numeric)")
elif _ocr_paddle:
    print("⚠️  PARTIAL OCR INITIALIZATION - PaddleOCR only")
    print("   PaddleOCR: ✓ Ready (Chinese text)")
    print("   EasyOCR: ❌ Failed (quantity detection unavailable)")
else:
    print("❌ OCR INITIALIZATION FAILED - Service will not work")
print("=" * 60 + "\n")
logger.info("OCR service components initialization complete")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns service status and configuration
    """
    try:
        if matcher is None:
            # Service is running but matcher failed to load
            # Return 200 (not 503) so Railway doesn't restart
            return JSONResponse(
                status_code=200,
                content={
                    "status": "degraded",
                    "service": settings.app_name,
                    "version": settings.app_version,
                    "matcher_loaded": False,
                    "total_cards_in_db": 0,
                    "warning": "Card matcher not initialized - OCR processing unavailable"
                },
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive"
                }
            )
        
        return HealthResponse(
            status="healthy",
            service=settings.app_name,
            version=settings.app_version,
            matcher_loaded=matcher is not None,
            total_cards_in_db=len(matcher.mappings) if matcher else 0
        )
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        # Still return 200 to avoid restart loops
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "service": settings.app_name,
                "version": settings.app_version,
                "error": str(e)
            }
        )


@router.get("/stats", response_model=StatsResponse)
async def get_service_stats():
    """
    Get service statistics
    
    Returns information about matcher and parser capabilities
    """
    return StatsResponse(
        matcher={
            "total_cards": len(matcher.mappings) if matcher else 0,
            "base_names": len(matcher.base_name_mappings) if matcher else 0,
            "supported_languages": ["zh-CN", "en"]
        },
        parser={
            "ocr_engines": ["PaddleOCR", "EasyOCR"],
            "supported_formats": ["JPG", "PNG"],
            "max_file_size_mb": settings.max_file_size_mb,
            "use_gpu": settings.use_gpu
        }
    )


@router.post("/process", response_model=DecklistResponse)
async def process_single_image(file: UploadFile = File(...)):
    """
    Process a single decklist image
    
    - **file**: Image file (JPG/PNG) of Chinese decklist
    
    Returns parsed and matched decklist with English card data
    """
    if matcher is None:
        raise HTTPException(
            status_code=503,
            detail="Card matcher not initialized"
        )
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image (JPG/PNG)"
        )
    
    # Check file size
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=400,
            detail=f"File size ({file_size_mb:.1f}MB) exceeds maximum ({settings.max_file_size_mb}MB)"
        )
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Memory monitoring
        import psutil
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        print(f"[MEMORY] Before OCR: {mem_before:.1f}MB")
        logger.info(f"Processing image: {file.filename} (Memory: {mem_before:.1f}MB)")
        
        # Stage 1: Parse image (using direct function from working implementation)
        print(f"[OCR] Starting parse_with_two_stage for {file.filename}")
        parsed = parse_with_two_stage(tmp_path)
        
        mem_after_parse = process.memory_info().rss / 1024 / 1024
        print(f"[MEMORY] After parsing: {mem_after_parse:.1f}MB (delta: +{mem_after_parse - mem_before:.1f}MB)")
        logger.info(f"Parsing complete. Extracted {sum(len(parsed.get(s, [])) for s in ['legend', 'main_deck', 'battlefields', 'runes', 'side_deck'])} card entries")
        
        # Stage 2: Match cards to English
        print(f"[MATCHING] Starting card matching")
        matched = matcher.match_decklist(parsed)
        
        mem_final = process.memory_info().rss / 1024 / 1024
        print(f"[MEMORY] After matching: {mem_final:.1f}MB (total delta: +{mem_final - mem_before:.1f}MB)")
        logger.info(f"Matching complete. Accuracy: {matched.get('stats', {}).get('accuracy', 0):.2f}%")
        
        # Add unique ID
        matched['decklist_id'] = str(uuid.uuid4())
        
        return DecklistResponse(**matched)
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception as e:
            logger.warning(f"Failed to delete temp file: {e}")


@router.post("/process-batch", response_model=BatchProcessResponse)
async def process_batch(files: List[UploadFile] = File(...)):
    """
    Process multiple decklist images
    
    - **files**: List of image files (JPG/PNG)
    - Max {max_batch_size} files per request
    
    Returns array of parsed decklists with statistics
    """
    if matcher is None:
        raise HTTPException(
            status_code=503,
            detail="Card matcher not initialized"
        )
    
    # Check batch size limit
    if len(files) > settings.max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.max_batch_size} images per batch (received {len(files)})"
        )
    
    results = []
    successful_count = 0
    failed_count = 0
    total_accuracy = 0.0
    
    logger.info(f"Processing batch of {len(files)} images")
    
    for idx, file in enumerate(files):
        try:
            # Validate file type
            if not file.content_type or not file.content_type.startswith('image/'):
                logger.warning(f"Skipping non-image file: {file.filename}")
                failed_count += 1
                continue
            
            # Read file content
            content = await file.read()
            
            # Check file size
            file_size_mb = len(content) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                logger.warning(f"Skipping oversized file: {file.filename} ({file_size_mb:.1f}MB)")
                failed_count += 1
                continue
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                logger.info(f"[{idx+1}/{len(files)}] Processing: {file.filename}")
                
                # Process image (using direct function from working implementation)
                parsed = parse_with_two_stage(tmp_path)
                matched = matcher.match_decklist(parsed)
                matched['decklist_id'] = str(uuid.uuid4())
                
                # Add to results
                results.append(DecklistResponse(**matched))
                successful_count += 1
                
                # Track accuracy
                if matched.get('stats'):
                    total_accuracy += matched['stats']['accuracy']
                
                logger.info(f"[{idx+1}/{len(files)}] Success - Accuracy: {matched.get('stats', {}).get('accuracy', 0):.2f}%")
            
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        
        except Exception as e:
            logger.error(f"[{idx+1}/{len(files)}] Failed to process {file.filename}: {e}")
            failed_count += 1
            continue
    
    # Calculate average accuracy
    avg_accuracy = (total_accuracy / successful_count) if successful_count > 0 else None
    
    logger.info(f"Batch complete: {successful_count} successful, {failed_count} failed")
    
    return BatchProcessResponse(
        total=len(files),
        successful=successful_count,
        failed=failed_count,
        average_accuracy=avg_accuracy,
        results=results
    )


def format_sse_event(event: str, data: dict) -> str:
    """
    Format data as Server-Sent Event (SSE)
    
    SSE format:
    event: <event_type>
    data: <json_data>
    
    (blank line to separate events)
    """
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def process_single_image_sync(file_data: Tuple[bytes, str, int]) -> dict:
    """
    Synchronous worker function for parallel processing
    
    Args:
        file_data: Tuple of (file_content, filename, index)
        
    Returns:
        Dict with success status and result/error
    """
    content, filename, index = file_data
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        logger.info(f"[Worker] Processing: {filename} (index {index})")
        
        # Process with OCR
        parsed = parse_with_two_stage(tmp_path)
        matched = matcher.match_decklist(parsed)
        matched['decklist_id'] = str(uuid.uuid4())
        
        # Create decklist response
        decklist = DecklistResponse(**matched)
        
        return {
            'success': True,
            'index': index,
            'filename': filename,
            'decklist': decklist.model_dump()
        }
    
    except Exception as e:
        logger.error(f"[Worker] Failed to process {filename}: {e}")
        return {
            'success': False,
            'index': index,
            'filename': filename,
            'error': str(e),
            'error_type': 'processing'
        }
    
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception as e:
            logger.warning(f"[Worker] Failed to delete temp file: {e}")


@router.post("/process-batch-stream")
async def process_batch_stream(files: List[UploadFile] = File(...)):
    """
    Process multiple decklist images with streaming results (Server-Sent Events)
    
    - **files**: List of image files (JPG/PNG)
    - Max {max_batch_size} files per request
    
    Returns Server-Sent Events (SSE) stream with progressive results:
    - `progress` events: Real-time processing status
    - `result` events: Completed decklist data (as each finishes)
    - `error` events: Individual image errors (doesn't break stream)
    - `complete` event: Final batch statistics
    
    Frontend can start working on results immediately as they arrive!
    """
    if matcher is None:
        raise HTTPException(
            status_code=503,
            detail="Card matcher not initialized"
        )
    
    # Check batch size limit
    if len(files) > settings.max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.max_batch_size} images per batch (received {len(files)})"
        )
    
    async def event_generator():
        """Generate SSE events as images are processed"""
        total = len(files)
        successful = 0
        failed = 0
        total_accuracy = 0.0
        start_time = time.time()
        
        logger.info(f"Starting SSE batch stream for {total} images")
        
        for idx, file in enumerate(files):
            filename = file.filename or f"image_{idx}.jpg"
            
            try:
                # Send progress event - validating
                progress_data = SSEProgressEvent(
                    current=idx + 1,
                    total=total,
                    filename=filename,
                    status="validating"
                ).model_dump()
                yield format_sse_event("progress", progress_data)
                
                # Validate file type
                if not file.content_type or not file.content_type.startswith('image/'):
                    error_data = SSEErrorEvent(
                        index=idx,
                        filename=filename,
                        error="File must be an image (JPG/PNG)",
                        error_type="validation"
                    ).model_dump()
                    yield format_sse_event("error", error_data)
                    logger.warning(f"[{idx+1}/{total}] Skipping non-image file: {filename}")
                    failed += 1
                    continue
                
                # Read file content
                content = await file.read()
                
                # Check file size
                file_size_mb = len(content) / (1024 * 1024)
                if file_size_mb > settings.max_file_size_mb:
                    error_data = SSEErrorEvent(
                        index=idx,
                        filename=filename,
                        error=f"File size ({file_size_mb:.1f}MB) exceeds maximum ({settings.max_file_size_mb}MB)",
                        error_type="validation"
                    ).model_dump()
                    yield format_sse_event("error", error_data)
                    logger.warning(f"[{idx+1}/{total}] Skipping oversized file: {filename}")
                    failed += 1
                    continue
                
                # Send progress event - processing
                progress_data = SSEProgressEvent(
                    current=idx + 1,
                    total=total,
                    filename=filename,
                    status="processing"
                ).model_dump()
                yield format_sse_event("progress", progress_data)
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                
                try:
                    logger.info(f"[{idx+1}/{total}] Processing: {filename}")
                    
                    # Process image with OCR
                    parsed = parse_with_two_stage(tmp_path)
                    matched = matcher.match_decklist(parsed)
                    matched['decklist_id'] = str(uuid.uuid4())
                    
                    # Create decklist response
                    decklist = DecklistResponse(**matched)
                    
                    # Send result event
                    result_data = SSEResultEvent(
                        index=idx,
                        filename=filename,
                        decklist=decklist
                    ).model_dump()
                    yield format_sse_event("result", result_data)
                    
                    successful += 1
                    
                    # Track accuracy
                    if matched.get('stats'):
                        accuracy = matched['stats']['accuracy']
                        total_accuracy += accuracy
                        logger.info(f"[{idx+1}/{total}] Success - Accuracy: {accuracy:.2f}%")
                    
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file: {e}")
            
            except Exception as e:
                # Send error event (don't break the stream)
                error_data = SSEErrorEvent(
                    index=idx,
                    filename=filename,
                    error=str(e),
                    error_type="processing"
                ).model_dump()
                yield format_sse_event("error", error_data)
                logger.error(f"[{idx+1}/{total}] Failed to process {filename}: {e}", exc_info=True)
                failed += 1
                continue
        
        # Calculate final statistics
        processing_time = time.time() - start_time
        avg_accuracy = (total_accuracy / successful) if successful > 0 else None
        
        # Send completion event
        complete_data = SSECompleteEvent(
            total=total,
            successful=successful,
            failed=failed,
            average_accuracy=avg_accuracy,
            processing_time_seconds=round(processing_time, 2)
        ).model_dump()
        yield format_sse_event("complete", complete_data)
        
        logger.info(f"SSE batch stream complete: {successful}/{total} successful, {failed} failed, {processing_time:.2f}s")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Connection": "keep-alive"
        }
    )


@router.post("/process-batch-fast")
async def process_batch_fast(files: List[UploadFile] = File(...)):
    """
    Process multiple decklist images with PARALLEL processing + SSE streaming
    
    - **files**: List of image files (JPG/PNG)
    - Max {max_batch_size} files per request
    
    Returns Server-Sent Events (SSE) stream with progressive results.
    Processes multiple images SIMULTANEOUSLY for 40-60% faster total time!
    
    Note: Requires ENABLE_PARALLEL=true in environment
    """
    if matcher is None:
        raise HTTPException(
            status_code=503,
            detail="Card matcher not initialized"
        )
    
    # Check if parallel processing is enabled
    if not settings.enable_parallel:
        raise HTTPException(
            status_code=400,
            detail="Parallel processing not enabled. Set ENABLE_PARALLEL=true or use /process-batch-stream instead."
        )
    
    # Check batch size limit
    if len(files) > settings.max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.max_batch_size} images per batch (received {len(files)})"
        )
    
    async def event_generator():
        """Generate SSE events with parallel processing"""
        total = len(files)
        successful = 0
        failed = 0
        total_accuracy = 0.0
        start_time = time.time()
        processed_count = 0
        
        logger.info(f"Starting PARALLEL SSE batch stream for {total} images with {settings.max_workers} workers")
        
        # Read all files first and validate
        file_data_list = []
        for idx, file in enumerate(files):
            filename = file.filename or f"image_{idx}.jpg"
            
            try:
                # Send progress event - validating
                progress_data = SSEProgressEvent(
                    current=idx + 1,
                    total=total,
                    filename=filename,
                    status="validating"
                ).model_dump()
                yield format_sse_event("progress", progress_data)
                
                # Validate file type
                if not file.content_type or not file.content_type.startswith('image/'):
                    error_data = SSEErrorEvent(
                        index=idx,
                        filename=filename,
                        error="File must be an image (JPG/PNG)",
                        error_type="validation"
                    ).model_dump()
                    yield format_sse_event("error", error_data)
                    failed += 1
                    continue
                
                # Read file content
                content = await file.read()
                
                # Check file size
                file_size_mb = len(content) / (1024 * 1024)
                if file_size_mb > settings.max_file_size_mb:
                    error_data = SSEErrorEvent(
                        index=idx,
                        filename=filename,
                        error=f"File size ({file_size_mb:.1f}MB) exceeds maximum ({settings.max_file_size_mb}MB)",
                        error_type="validation"
                    ).model_dump()
                    yield format_sse_event("error", error_data)
                    failed += 1
                    continue
                
                # Add to processing queue
                file_data_list.append((content, filename, idx))
            
            except Exception as e:
                error_data = SSEErrorEvent(
                    index=idx,
                    filename=filename,
                    error=str(e),
                    error_type="validation"
                ).model_dump()
                yield format_sse_event("error", error_data)
                failed += 1
        
        # Process in batches using thread pool
        batch_size = settings.max_workers
        
        with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
            # Process in chunks of batch_size
            for i in range(0, len(file_data_list), batch_size):
                batch = file_data_list[i:i+batch_size]
                
                # Send progress events for batch
                for content, filename, idx in batch:
                    progress_data = SSEProgressEvent(
                        current=idx + 1,
                        total=total,
                        filename=filename,
                        status="processing"
                    ).model_dump()
                    yield format_sse_event("progress", progress_data)
                
                # Submit batch to executor
                loop = asyncio.get_event_loop()
                futures = [
                    loop.run_in_executor(executor, process_single_image_sync, data)
                    for data in batch
                ]
                
                # Wait for batch to complete
                results = await asyncio.gather(*futures)
                
                # Stream results as they complete
                for result in results:
                    processed_count += 1
                    
                    if result['success']:
                        # Send result event
                        result_data = SSEResultEvent(
                            index=result['index'],
                            filename=result['filename'],
                            decklist=DecklistResponse(**result['decklist'])
                        ).model_dump()
                        yield format_sse_event("result", result_data)
                        
                        successful += 1
                        
                        # Track accuracy
                        if result['decklist'].get('stats'):
                            accuracy = result['decklist']['stats']['accuracy']
                            total_accuracy += accuracy
                            logger.info(f"[{processed_count}/{len(file_data_list)}] Success - {result['filename']} - Accuracy: {accuracy:.2f}%")
                    else:
                        # Send error event
                        error_data = SSEErrorEvent(
                            index=result['index'],
                            filename=result['filename'],
                            error=result['error'],
                            error_type=result['error_type']
                        ).model_dump()
                        yield format_sse_event("error", error_data)
                        failed += 1
        
        # Calculate final statistics
        processing_time = time.time() - start_time
        avg_accuracy = (total_accuracy / successful) if successful > 0 else None
        
        # Send completion event
        complete_data = SSECompleteEvent(
            total=total,
            successful=successful,
            failed=failed,
            average_accuracy=avg_accuracy,
            processing_time_seconds=round(processing_time, 2)
        ).model_dump()
        yield format_sse_event("complete", complete_data)
        
        speedup = (total * 45) / processing_time if processing_time > 0 else 1  # Assume 45s per image sequential
        logger.info(f"PARALLEL SSE batch complete: {successful}/{total} successful, {failed} failed, {processing_time:.2f}s (~{speedup:.1f}x speedup)")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


@router.post("/process-and-save")
async def process_and_save_to_main_api(
    file: UploadFile = File(...),
    owner: str = "Unknown",
    format_id: int = 1
):
    """
    Process decklist image and save to main Riftbound API
    
    - **file**: Image file (JPG/PNG) of Chinese decklist
    - **owner**: Deck owner/player name
    - **format_id**: Format ID from main API (default: 1)
    
    Returns the created deck from main API with ID
    """
    if matcher is None:
        raise HTTPException(
            status_code=503,
            detail="Card matcher not initialized"
        )
    
    if main_api_client is None:
        raise HTTPException(
            status_code=503,
            detail="Main API integration not configured. Set MAIN_API_URL in environment."
        )
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image (JPG/PNG)"
        )
    
    # Read file content
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=400,
            detail=f"File size ({file_size_mb:.1f}MB) exceeds maximum ({settings.max_file_size_mb}MB)"
        )
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        logger.info(f"Processing and saving: {file.filename}")
        
        # Stage 1: Parse image (using direct function from working implementation)
        parsed = parse_with_two_stage(tmp_path)
        
        # Stage 2: Match cards to English
        matched = matcher.match_decklist(parsed)
        
        # Stage 3: Map to main API schema
        deck_schema = main_api_client.map_ocr_to_deck_schema(
            matched,
            owner=owner,
            format_id=format_id
        )
        
        # Stage 4: Resolve card IDs (lookup in main API)
        logger.info("Resolving card IDs from main API...")
        resolved_cards = await main_api_client.resolve_card_ids(deck_schema['cards'])
        deck_schema['cards'] = resolved_cards
        
        if len(resolved_cards) == 0:
            raise HTTPException(
                status_code=400,
                detail="No cards could be resolved in main API. Check card mappings."
            )
        
        # Stage 5: Create deck in main API
        logger.info(f"Creating deck in main API: {deck_schema['name']}")
        created_deck = main_api_client.create_deck(deck_schema)
        
        if created_deck is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to create deck in main API"
            )
        
        # Add OCR stats to response
        created_deck['ocr_stats'] = matched.get('stats', {})
        
        logger.info(f"Deck created successfully with ID: {created_deck.get('id')}")
        
        return created_deck
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process and save failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass


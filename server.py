#!/usr/bin/env python3
"""
Flask server wrapper for query.py RAG system.
Provides REST API endpoints for conversational RAG queries.
"""

import os
import sys
import json
import uuid
import logging
import time
import functools
from datetime import datetime
from typing import Optional, Dict, Any
from flask import Flask, request, jsonify, Response, send_from_directory, g
from flask_cors import CORS

# Import functions from interview.py
from interview import (
    get_config, validate_config, setup_clients, rag_answer,
    TokenCounter, StateStore, ConversationState,
    extract_choices, ChoicesStreamFilter
)

SERVER_VERSION = "1.3.5"

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.after_request
def inject_server_version(response):
    if response.content_type == 'application/json':
        try:
            data = response.get_json(silent=True)
            if isinstance(data, dict):
                data['serverVersion'] = SERVER_VERSION
                response.data = json.dumps(data, ensure_ascii=False)
        except Exception:
            pass
    return response

# Configure logging
def setup_logging():
    """Configure unified logging for the RAG server with component prefixes."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create unified log file handler
    log_formatter = logging.Formatter('%(asctime)s - %(message)s')
    file_handler = logging.FileHandler('logs/rag_unified.log')
    file_handler.setFormatter(log_formatter)
    
    # Console handler for development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Create component loggers with prefixes
    request_logger = logging.getLogger('webserver.requests')
    response_logger = logging.getLogger('webserver.responses') 
    rag_logger = logging.getLogger('rag.operations')
    server_logger = logging.getLogger('webserver.main')
    
    # Set levels
    for logger in [request_logger, response_logger, rag_logger, server_logger]:
        logger.setLevel(logging.INFO)
    
    return request_logger, response_logger, rag_logger, server_logger

# Initialize loggers
request_logger, response_logger, rag_logger, app_logger = setup_logging()

# Global variables for shared resources
collections = {}        # Dict to store multiple ChromaDB collections
chroma_client = None    # Single shared PersistentClient
embed_fn = None         # Single shared embedding function
oai = None
config = None
token_counter = None
state_store = None

def _auth_required():
    """Return a 401 response requesting Basic Auth credentials."""
    return Response(
        'Authentication required.',
        401,
        {'WWW-Authenticate': 'Basic realm="Policy Coach"'}
    )

def require_auth(f):
    """Decorator: enforce HTTP Basic Auth when WEB_PASSWORD is set."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        web_user = os.getenv('WEB_USER', 'admin')
        web_password = os.getenv('WEB_PASSWORD', '')
        if web_password:
            auth = request.authorization
            if not auth or auth.username != web_user or auth.password != web_password:
                return _auth_required()
        return f(*args, **kwargs)
    return decorated

@app.before_request
def log_request_info():
    """Log incoming request details before processing."""
    g.start_time = time.time()
    g.request_id = str(uuid.uuid4())[:8]
    
    # Log request details
    request_data = {
        'request_id': g.request_id,
        'timestamp': datetime.now().isoformat(),
        'method': request.method,
        'url': request.url,
        'path': request.path,
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'content_type': request.content_type
    }
    
    # Log payload for POST requests
    if request.method == 'POST' and request.is_json:
        try:
            payload = request.get_json()
            # Sanitize sensitive data if any
            sanitized_payload = payload.copy() if payload else {}
            request_data['payload'] = sanitized_payload
        except Exception as e:
            request_data['payload_error'] = str(e)
    
    request_logger.info(f"[WEBSERVER] Request details: {json.dumps(request_data, indent=2)}")
    app_logger.info(f"[WEBSERVER] [{g.request_id}] {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def log_response_info(response):
    """Log response details after processing."""
    duration = time.time() - g.start_time if hasattr(g, 'start_time') else 0
    request_id = getattr(g, 'request_id', 'unknown')
    
    response_data = {
        'request_id': request_id,
        'timestamp': datetime.now().isoformat(),
        'status_code': response.status_code,
        'content_type': response.content_type,
        'content_length': response.content_length,
        'duration_seconds': round(duration, 3)
    }
    
    # Log response body for JSON responses (excluding streaming)
    if (response.content_type and 'application/json' in response.content_type and 
        response.status_code < 500 and hasattr(response, 'get_data')):
        try:
            response_body = response.get_data(as_text=True)
            if response_body and len(response_body) < 10000:  # Limit size
                response_data['response_body'] = json.loads(response_body)
            else:
                response_data['response_size'] = len(response_body) if response_body else 0
        except Exception as e:
            response_data['response_parse_error'] = str(e)
    
    response_logger.info(f"[WEBSERVER] Response details: {json.dumps(response_data, indent=2)}")
    app_logger.info(f"[WEBSERVER] [{request_id}] Response {response.status_code} in {duration:.3f}s")
    
    return response

def initialize_rag_system():
    """Initialize the RAG system components."""
    global collections, chroma_client, embed_fn, oai, config, token_counter, state_store
    
    # Get configuration using query.py's config system
    config = get_config()
    config['conversation_mode'] = True  # Always use conversation mode for the server
    config['json_mode'] = True  # Always use JSON output
    
    # Validate configuration
    if not validate_config(config):
        raise RuntimeError("RAG system configuration is invalid")
    
    # Setup OpenAI client only (without requiring a collection)
    from openai import OpenAI
    import httpx as _httpx
    import json as _json, time as _time
    _HEADERS_DUMP = "/tmp/cocyber_headers.jsonl"
    def _dump_response_headers(response):
        try:
            with open(_HEADERS_DUMP, "a", encoding="utf-8") as f:
                f.write(_json.dumps({
                    "ts": _time.time(),
                    "url": str(response.request.url),
                    "status": response.status_code,
                    "headers": dict(response.headers),
                }, ensure_ascii=False) + "\n")
        except Exception:
            pass
    _http_client = _httpx.Client(event_hooks={"response": [_dump_response_headers]})
    oai = OpenAI(api_key=config['openai_key'], base_url=config['openai_base'], http_client=_http_client)
    if oai is None:
        raise RuntimeError("Failed to initialize OpenAI client")
    
    # Initialize conversation components
    token_counter = TokenCounter(config['chat_model'])
    state_store = StateStore(config['state_db_path'])
    
    # Initialize single shared ChromaDB client and embedding function
    import chromadb
    from chromadb.utils import embedding_functions
    chroma_client = chromadb.PersistentClient(path=config['chroma_dir'])
    embed_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=config['openai_key'],
        api_base=config['openai_base'],
        model_name=config['embed_model']
    )

    app_logger.info("[WEBSERVER] RAG system initialized successfully")
    app_logger.info("[WEBSERVER] Collections will be loaded on-demand")

def get_collection(collection_name: str):
    """Get or create a collection by name using the shared ChromaDB client."""
    global collections, chroma_client, embed_fn

    if collection_name not in collections:
        try:
            col = chroma_client.get_collection(name=collection_name, embedding_function=embed_fn)
            collections[collection_name] = col
            app_logger.info(f"[WEBSERVER] Loaded collection '{collection_name}' with {col.count()} documents")
        except Exception as e:
            app_logger.warning(f"[WEBSERVER] Cannot load collection '{collection_name}': {e}")
            return None

    return collections[collection_name]

def list_available_collections():
    """List all available collections in the ChromaDB directory."""
    try:
        return [col.name for col in chroma_client.list_collections()]
    except Exception as e:
        app_logger.error(f"[WEBSERVER] Error listing collections: {e}")
        return []

def process_conversation_request(message: str, collection_name: str, session_id: Optional[str] = None, stream: bool = False):
    """Process a conversation request and return JSON response or generator for streaming."""
    global collections, oai, config, token_counter, state_store
    
    request_id = getattr(g, 'request_id', 'unknown')
    
    # Log RAG operation start
    rag_logger.info(f"[RAG_SERVER] [{request_id}] RAG operation started - Collection: {collection_name}, Session: {session_id}, Stream: {stream}")
    rag_logger.info(f"[RAG_SERVER] [{request_id}] User message: {message[:200]}{'...' if len(message) > 200 else ''}")
    
    # Get the requested collection
    col = get_collection(collection_name)
    if col is None:
        rag_logger.error(f"[RAG_SERVER] [{request_id}] Collection '{collection_name}' not found")
        raise ValueError(f"Collection '{collection_name}' not found")
    
    rag_logger.info(f"[RAG_SERVER] [{request_id}] Using collection '{collection_name}' with {col.count()} documents")
    
    # Generate session_id if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
        rag_logger.info(f"[RAG_SERVER] [{request_id}] Generated new session ID: {session_id}")
    
    # Load conversation state
    state = state_store.load_state(session_id)
    rag_logger.info(f"[RAG_SERVER] [{request_id}] Loaded conversation state - Window size: {len(state.window)}, Summary length: {len(state.summary)}")
    
    if stream:
        # Return generator for streaming
        def stream_generator():
            full_answer = ""
            final_metadata = None
            final_sources = None
            chunk_count = 0
            choices_filter = ChoicesStreamFilter()

            rag_logger.info(f"[RAG_SERVER] [{request_id}] Starting streaming RAG response generation")

            stream_response = rag_answer(
                message, col, oai, config,
                state=state, token_counter=token_counter, state_store=state_store,
                stream=True
            )

            for chunk, is_complete, metadata_tuple in stream_response:
                if is_complete:
                    # Final chunk with complete response data
                    full_answer, final_sources, final_metadata = metadata_tuple

                    # Drain any text still held in the filter buffer
                    tail = choices_filter.flush()
                    if tail:
                        chunk_count += 1
                        try:
                            yield f"data: {json.dumps({'chunk': tail, 'sessionId': session_id, 'done': False}, ensure_ascii=False)}\n\n"
                        except (TypeError, ValueError):
                            pass

                    clean_answer, _ = extract_choices(full_answer)
                    choices = choices_filter.choices

                    rag_logger.info(f"[RAG_SERVER] [{request_id}] Streaming completed - Total chunks: {chunk_count}, Answer length: {len(clean_answer)}, Sources: {len(final_sources)}, Choices: {len(choices)}")
                    rag_logger.info(f"[RAG_SERVER] [{request_id}] Final metadata: {final_metadata}")

                    result = {
                        "question": message,
                        "answer": clean_answer,
                        "choices": choices,
                        "sources": [{"title": title or source, "source": source} for source, title in final_sources],
                        "metadata": final_metadata or {},
                        "sessionId": session_id,
                        "done": True
                    }

                    # Log final streaming response
                    response_logger.info(f"[WEBSERVER] Streaming final response: {json.dumps({
                        'request_id': request_id,
                        'type': 'streaming_final',
                        'timestamp': datetime.now().isoformat(),
                        'response_data': result
                    }, indent=2)}")

                    yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"
                else:
                    # Streaming chunk — pass through filter to strip the choices marker
                    safe = choices_filter.feed(chunk)
                    if not safe:
                        continue
                    chunk_count += 1
                    chunk_data = {
                        "chunk": safe,
                        "sessionId": session_id,
                        "done": False
                    }
                    try:
                        json_data = json.dumps(chunk_data, ensure_ascii=False)
                        yield f"data: {json_data}\n\n"
                    except (TypeError, ValueError) as e:
                        # If JSON encoding fails, send a safe fallback
                        fallback_data = {
                            "chunk": str(safe).encode('unicode_escape').decode('utf-8'),
                            "sessionId": session_id,
                            "done": False
                        }
                        rag_logger.warning(f"[RAG_SERVER] [{request_id}] JSON encoding failed for chunk, using fallback: {e}")
                        yield f"data: {json.dumps(fallback_data)}\n\n"
        
        return stream_generator()
    else:
        # Process the RAG query (non-streaming)
        rag_logger.info(f"[RAG_SERVER] [{request_id}] Starting non-streaming RAG response generation")
        
        answer, source_info, metadata = rag_answer(
            message, col, oai, config,
            state=state, token_counter=token_counter, state_store=state_store
        )
        
        rag_logger.info(f"[RAG_SERVER] [{request_id}] RAG response completed - Answer length: {len(answer)}, Sources: {len(source_info)}")
        rag_logger.info(f"[RAG_SERVER] [{request_id}] Response metadata: {metadata}")

        clean_answer, choices = extract_choices(answer)

        # Format response
        result = {
            "question": message,
            "answer": clean_answer,
            "choices": choices,
            "sources": [{"title": title or source, "source": source} for source, title in source_info],
            "metadata": metadata or {},
            "sessionId": session_id
        }
        
        # Log non-streaming response
        response_logger.info(f"[WEBSERVER] Non-streaming response: {json.dumps({
            'request_id': request_id,
            'type': 'non_streaming',
            'timestamp': datetime.now().isoformat(),
            'response_data': result
        }, indent=2)}")
        
        return result

@app.route('/conversation', methods=['POST'])
@require_auth
def conversation_endpoint():
    """Handle conversation requests."""
    request_id = getattr(g, 'request_id', 'unknown')
    app_logger.info(f"[WEBSERVER] [{request_id}] Processing conversation endpoint")
    
    try:
        # Parse JSON request
        if not request.is_json:
            app_logger.warning(f"[WEBSERVER] [{request_id}] Non-JSON request received")
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        app_logger.info(f"[WEBSERVER] [{request_id}] Request data parsed successfully")
        
        # Validate required parameters
        if 'message' not in data:
            app_logger.warning(f"[WEBSERVER] [{request_id}] Missing message parameter")
            return jsonify({"error": "Missing required parameter: message"}), 400
        
        message = data['message']
        collection_name = data.get('collectionName', '')
        
        if not message or not isinstance(message, str) or not message.strip():
            app_logger.warning(f"[WEBSERVER] [{request_id}] Invalid message parameter")
            return jsonify({"error": "Message must be a non-empty string"}), 400
        
        # If no collection specified, use first available collection
        if not collection_name:
            available_collections = list_available_collections()
            if not available_collections:
                app_logger.error(f"[WEBSERVER] [{request_id}] No collections available")
                return jsonify({"error": "No collections available. Please create a collection first."}), 400
            collection_name = available_collections[0]
            app_logger.info(f"[WEBSERVER] [{request_id}] Using default collection: {collection_name}")
        elif not isinstance(collection_name, str):
            return jsonify({"error": "collectionName must be a string"}), 400
        
        # Get optional session_id
        session_id = data.get('sessionId')
        if session_id is not None and not isinstance(session_id, str):
            return jsonify({"error": "sessionId must be a string"}), 400
        
        # Process the conversation request
        app_logger.info(f"[WEBSERVER] [{request_id}] Processing conversation request for collection: {collection_name}")
        result = process_conversation_request(message.strip(), collection_name, session_id, stream=False)
        
        app_logger.info(f"[WEBSERVER] [{request_id}] Conversation request completed successfully")
        return jsonify(result)
        
    except Exception as e:
        app_logger.error(f"[WEBSERVER] [{request_id}] Error in conversation endpoint: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/conversation/stream', methods=['POST'])
@require_auth
def conversation_stream_endpoint():
    """Handle streaming conversation requests."""
    request_id = getattr(g, 'request_id', 'unknown')
    app_logger.info(f"[WEBSERVER] [{request_id}] Processing streaming conversation endpoint")
    
    try:
        # Parse JSON request
        if not request.is_json:
            app_logger.warning(f"[WEBSERVER] [{request_id}] Non-JSON streaming request received")
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        app_logger.info(f"[WEBSERVER] [{request_id}] Streaming request data parsed successfully")
        
        # Validate required parameters
        if 'message' not in data:
            app_logger.warning(f"[WEBSERVER] [{request_id}] Missing message parameter in streaming request")
            return jsonify({"error": "Missing required parameter: message"}), 400
        
        message = data['message']
        collection_name = data.get('collectionName', '')
        
        if not message or not isinstance(message, str) or not message.strip():
            app_logger.warning(f"[WEBSERVER] [{request_id}] Invalid message parameter in streaming request")
            return jsonify({"error": "Message must be a non-empty string"}), 400
        
        # If no collection specified, use first available collection
        if not collection_name:
            available_collections = list_available_collections()
            if not available_collections:
                app_logger.error(f"[WEBSERVER] [{request_id}] No collections available for streaming")
                return jsonify({"error": "No collections available. Please create a collection first."}), 400
            collection_name = available_collections[0]
            app_logger.info(f"[WEBSERVER] [{request_id}] Using default collection for streaming: {collection_name}")
        elif not isinstance(collection_name, str):
            return jsonify({"error": "collectionName must be a string"}), 400
        
        # Get optional session_id
        session_id = data.get('sessionId')
        if session_id is not None and not isinstance(session_id, str):
            return jsonify({"error": "sessionId must be a string"}), 400
        
        # Process the streaming conversation request
        app_logger.info(f"[WEBSERVER] [{request_id}] Processing streaming conversation request for collection: {collection_name}")
        generator = process_conversation_request(message.strip(), collection_name, session_id, stream=True)
        
        app_logger.info(f"[WEBSERVER] [{request_id}] Streaming conversation request initiated successfully")
        return Response(generator, mimetype='text/plain', headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        })
        
    except Exception as e:
        app_logger.error(f"[WEBSERVER] [{request_id}] Error in streaming conversation endpoint: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/collections', methods=['GET'])
@require_auth
def get_collections():
    """Get list of available collections."""
    try:
        available_collections = list_available_collections()
        return jsonify({
            "collections": available_collections,
            "count": len(available_collections)
        })
    except Exception as e:
        return jsonify({"error": f"Failed to list collections: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        available_collections = list_available_collections()
        total_chunks = 0

        # Get stats for all collections using count() only (avoids embedding dimension checks)
        for collection_name in available_collections:
            try:
                col = chroma_client.get_collection(name=collection_name)
                chunk_count = col.count()
                total_chunks += chunk_count
            except Exception as e:
                app_logger.warning(f"[WEBSERVER] Health check skipping collection '{collection_name}': {e}")
        
        return jsonify({
            "status": "healthy",
            "collections": len(available_collections),
            "total_chunks": total_chunks,
            "chat_model": config['chat_model'] if config else "unknown"
        })
    except Exception as e:
        return jsonify({
            "status": "healthy", 
            "error": str(e),
            "chat_model": config['chat_model'] if config else "unknown"
        })

@app.route('/static/<filename>')
@require_auth
def static_files(filename):
    """Serve static files from the root directory."""
    return send_from_directory('.', filename)

@app.route('/', methods=['GET'])
@require_auth
def root():
    """Root endpoint with API information."""
    return jsonify({
        "name": "RAG Conversation API",
        "version": "1.0",
        "endpoints": {
            "POST /conversation": {
                "description": "Submit a conversational query",
                "parameters": {
                    "message": "Required string - the user's message/question",
                    "collectionName": "Optional string - ChromaDB collection name to query (uses first available if empty)",
                    "sessionId": "Optional string - conversation session ID"
                },
                "response": {
                    "question": "The user's question",
                    "answer": "AI generated answer",
                    "sources": "Array of source documents",
                    "metadata": "Query metadata",
                    "sessionId": "Session identifier"
                }
            },
            "POST /conversation/stream": "Streaming conversation endpoint (same parameters as /conversation)",
            "GET /collections": "List available ChromaDB collections",
            "GET /health": "Health check endpoint with collection stats",
            "GET /static/<filename>": "Static file serving",
            "GET /": "API information"
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    try:
        # Initialize the RAG system
        initialize_rag_system()
        
        # Get server configuration
        host = os.getenv('FLASK_HOST', '0.0.0.0')
        port = int(os.getenv('FLASK_PORT', '5050'))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        app_logger.info(f"[WEBSERVER] Starting Flask server on {host}:{port}")
        app_logger.info(f"[WEBSERVER] Debug mode: {debug}")
        app_logger.info(f"[WEBSERVER] Logs will be written to: logs/rag_unified.log")
        
        # Start the Flask server.
        # threaded=True is required: the dev server otherwise handles one
        # request at a time, so any long-running call (LLM streaming, the
        # post-stream summarizer, etc.) blocks new connections and the kernel
        # eventually answers them with TCP RST — visible to clients as
        # "Connection refused" even though the process is healthy.
        app.run(host=host, port=port, debug=debug, threaded=True)
        
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)
# Cybersecurity Policy RAG System

A specialized Retrieval-Augmented Generation (RAG) system designed for cybersecurity policy creation through structured interviews. This system helps organizations generate comprehensive cybersecurity policies based on industry frameworks like NIST CSF 2.0.

> **Copyright © 2026 The Lisbon Council asbl**
>
> Licensed under the EUPL, Version 1.2 or – as soon they will be approved by
> the European Commission – subsequent versions of the EUPL (the "Licence");
> you may not use this work except in compliance with the Licence.
> You may obtain a copy of the Licence at
> <https://joinup.ec.europa.eu/software/page/eupl>.
>
> Unless required by applicable law or agreed to in writing, software
> distributed under the Licence is distributed on an "AS IS" basis,
> WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
> See the Licence for the specific language governing permissions and
> limitations under the Licence.
>
> See the [LICENSE](LICENSE) file for the full licence text.

## 📋 Overview

This system consists of three main components:

1. **`build_index.py`** - Document ingestion and vector database builder
2. **`interview.py`** - Core RAG engine with conversation management
3. **`server.py`** - Flask REST API server with streaming support

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Documents     │    │   Vector Store   │    │   Flask API     │
│ (PDF/DOCX/JSON/ │ -> │   (ChromaDB)     │ -> │   (REST/SSE)    │
│  JSONL/TXT)     │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              v                          v
                    ┌──────────────────┐    ┌─────────────────┐
                    │ Conversation     │    │ Interactive     │
                    │ State (SQLite)   │    │ Web Interface   │
                    └──────────────────┘    └─────────────────┘
```

## 📁 Module Documentation

### `build_index.py` - Document Ingestion System

**Purpose**: Builds and maintains the ChromaDB vector index from source documents.

#### Core Functionality

- **Multi-format Support**: Processes PDF, DOCX, JSON, JSONL, and TXT files
- **Intelligent Chunking**: Character-based (~800 chars) or semantic (sentence-boundary) chunking
- **Metadata Extraction**: Preserves document metadata with automatic flattening for ChromaDB
- **Rate Limiting**: Built-in exponential backoff and batch processing
- **Error Recovery**: Automatic retry logic for API failures

#### Key Features

- **Batch Processing**: Configurable batch sizes (default: 50 documents)
- **Token Management**: Automatic chunk splitting for embedding API limits
- **Progress Tracking**: Real-time progress feedback during ingestion
- **Validation**: ChromaDB collection name validation and config verification

#### Usage

```bash
# Basic usage
python build_index.py

# Custom configuration
python build_index.py --data-dir ./documents --collection-name policies --chunk-tokens 1000

# Semantic chunking (sentence-boundary based with overlap)
python build_index.py --semantic-chunking --chunk-overlap 150

# Verbose output
python build_index.py --verbose

# Dry run to validate config
python build_index.py --dry-run
```

#### Document Processing Flow

1. **File Discovery**: Scans data directory for supported file types
2. **Content Extraction**:
   - **PDF**: Page-by-page text extraction using PyPDF
   - **DOCX**: Paragraph-based extraction using python-docx
   - **JSON**: Extracts `text` or `content` fields, falls back to full serialization
   - **JSONL**: Line-by-line processing with row tracking
   - **TXT**: Plain text file processing
3. **Chunking**: Character-based or semantic (NLTK punkt with regex fallback) with configurable overlap
4. **Metadata Handling**: Flattens nested metadata structures for ChromaDB compatibility
5. **Embedding**: Batched API calls with rate limiting and retry logic
6. **Storage**: Persistent ChromaDB collection with unique document IDs

#### Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `DATA_DIR` | `./data` | Source document directory |
| `CHROMA_DIR` | `./chroma` | ChromaDB persistence directory |
| `CHUNK_TOKENS` | `200` | Token limit per chunk |
| `BATCH_SIZE` | `50` | Documents per API batch |
| `BATCH_DELAY` | `2.0` | Seconds between batches |
| `MAX_RETRIES` | `5` | Retry attempts for failed API calls |

### `interview.py` - RAG Engine with Conversation Management

**Purpose**: Core RAG engine specialized for cybersecurity policy interviews with advanced conversation management.

#### Core Functionality

- **Conversation State Management**: Persistent session tracking with SQLite backend
- **Context Window Management**: Token-aware conversation windows with automatic trimming
- **Query Rewriting**: Context-aware query enhancement for better retrieval
- **Incremental Summarization**: Maintains conversation summaries to preserve long-term context
- **Streaming Support**: Real-time response generation with Server-Sent Events

#### Key Features

**Advanced Conversation Management**:
- **Session Persistence**: SQLite-backed conversation state storage
- **Token Budget Management**: Configurable context windows (default: 2400 tokens)
- **Smart Summarization**: Interview-aware summaries that preserve policy generation context
- **Window Trimming**: Automatic removal of old messages when token limits are reached

**Interview Specialization**:
- **Cybersecurity Focus**: Custom system prompt for policy generation
- **Progress Tracking**: Maintains interview state and next steps
- **Framework Integration**: Built-in knowledge of NIST CSF 2.0 and other frameworks

**Technical Features**:
- **Multiple Model Support**: OpenAI-compatible API with tiktoken-based token counting
- **Error Handling**: Comprehensive error recovery with graceful degradation
- **Metadata Tracking**: Detailed token usage and retrieval metrics

#### Usage Modes

**1. Interactive Mode**
```bash
# Start interactive session
python interview.py

# Continue existing session
python interview.py --session-id my-session-123

# Custom configuration
python interview.py --chat-model gpt-4 --window-max-tokens 4000
```

**2. Single Query Mode**
```bash
# Single question
python interview.py "What is the NIST Cybersecurity Framework?"

# JSON output
python interview.py --json "Tell me about incident response planning"
```

**3. Programmatic Usage**
```python
from interview import rag_answer, setup_clients, TokenCounter, StateStore

# Setup
col, oai = setup_clients(config)
token_counter = TokenCounter(config['chat_model'])
state_store = StateStore(config['state_db_path'])
state = state_store.load_state(session_id)

# Query with conversation context
answer, sources, metadata = rag_answer(
    question, col, oai, config,
    state=state, token_counter=token_counter, state_store=state_store
)

# Streaming response
for chunk, is_complete, metadata_tuple in rag_answer(
    question, col, oai, config, stream=True, state=state, ...
):
    if is_complete:
        final_answer, sources, metadata = metadata_tuple
    else:
        print(chunk, end="", flush=True)
```

#### Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `WINDOW_MAX_TOKENS` | `2400` | Maximum tokens in conversation window |
| `SUMMARY_MAX_CHARS` | `16000` | Maximum characters in conversation summary |
| `STATE_DB_PATH` | `./conversation_state.db` | SQLite database for conversation state |
| `CHAT_MODEL` | `gpt-4o` | LLM model for responses |
| `TEMPERATURE` | `0.1` | Response randomness (0.0-2.0) |
| `MAX_RESULTS` | `5` | Number of chunks retrieved per query |
| `TENSORIX_API_KEY` | _(unset)_ | Alternative API key; takes precedence over `OPENAI_API_KEY` when set |
| `EXTRA_BODY_JSON` | _(unset)_ | JSON object of provider-specific params forwarded to the chat API (e.g. reasoning flags) |

### `server.py` - Flask REST API Server

**Purpose**: Web server wrapper providing HTTP REST API access to the RAG system with streaming support.

#### Core Functionality

- **REST API Endpoints**: JSON-based conversation API
- **Streaming Support**: Server-Sent Events for real-time responses
- **Session Management**: HTTP-based conversation session handling
- **Health Monitoring**: System status and collection metrics
- **Static File Serving**: Web interface for testing

#### API Endpoints

**`POST /conversation`** - Standard conversation endpoint
- Accepts JSON with `message` and optional `sessionId`
- Returns complete response with sources and metadata
- Automatically manages conversation state and history

**`POST /conversation/stream`** - Streaming conversation endpoint
- Same input format as standard endpoint
- Returns Server-Sent Events stream
- Real-time token-by-token response generation

**`GET /health`** - Health check and system status
- Returns collection size, document count, and model information
- Used for monitoring and load balancer health checks

**`GET /collections`** - List available ChromaDB collections
- Returns names of all indexed collections

**`GET /static/<filename>`** - Static file serving
- Serves web testing interface and assets
- Supports HTML, CSS, JavaScript files
- The bundled chat UI is available at `http://localhost:5050/static/webtest.html`

#### Response Format

The `/conversation` endpoint returns a single JSON object; `/conversation/stream` emits incremental `{"chunk": ..., "done": false}` events and the same fields once the stream completes:

| Field | Description |
|-------|-------------|
| `question` | The user message, echoed back |
| `answer` | The generated answer (markdown) |
| `sources` | List of `{title, source}` for the retrieved chunks |
| `choices` | Suggested quick-reply options for the next turn (may be empty) |
| `metadata` | Token usage and retrieval metrics (`input_tokens`, `output_tokens`, `chunks_retrieved`, …) |
| `sessionId` | Conversation session identifier |
| `serverVersion` | Version string of the running server |

#### Authentication

All endpoints support optional HTTP Basic Auth, controlled via environment variables:

- `WEB_USER` — username (default: `admin`)
- `WEB_PASSWORD` — password; **when empty (the default), authentication is disabled.** Set a non-empty value to require credentials.

```bash
curl -u admin:yourpassword http://localhost:5050/health
```

#### Flask Server Integration

The server module integrates with the core RAG system through:

1. **Initialization**: 
   ```python
   def initialize_rag_system():
       global col, oai, config, token_counter, state_store
       config = get_config()
       col, oai = setup_clients(config)
       token_counter = TokenCounter(config['chat_model'])
       state_store = StateStore(config['state_db_path'])
   ```

2. **Request Processing**:
   ```python
   def process_conversation_request(message, session_id=None, stream=False):
       state = state_store.load_state(session_id or str(uuid.uuid4()))
       
       if stream:
           return rag_answer(..., stream=True)  # Generator
       else:
           return rag_answer(..., stream=False)  # Complete response
   ```

3. **Session Management**:
   - Automatic session ID generation
   - Persistent conversation state via SQLite
   - Thread-safe state management

4. **Error Handling**:
   - JSON validation and error responses
   - Graceful degradation on system failures
   - Detailed error logging

#### Usage

**Start the Server**:
```bash
python server.py
```

**Environment Configuration**:
```bash
FLASK_HOST=0.0.0.0
FLASK_PORT=5050
FLASK_DEBUG=false
```

**API Example**:
```bash
# Start new conversation
curl -X POST http://localhost:5050/conversation \
  -H "Content-Type: application/json" \
  -d '{"message": "What is cybersecurity governance?"}'

# Continue conversation
curl -X POST http://localhost:5050/conversation \
  -H "Content-Type: application/json" \
  -d '{"message": "How does it relate to risk management?", "sessionId": "abc-123"}'

# Streaming request
curl -X POST http://localhost:5050/conversation/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain the NIST framework"}' \
  --no-buffer
```

## 🔄 System Integration Flow

### 1. Document Ingestion Phase
```
Documents → build_index.py → ChromaDB Vector Store
    ↓              ↓              ↓
PDF/JSON      Chunking      Embeddings
Extraction    Metadata      Persistence
```

### 2. Interactive Session Phase
```
User Query → server.py → interview.py → ChromaDB Query
     ↓           ↓            ↓              ↓
   HTTP       Session      Context        Vector
  Request    Management   Management     Similarity
     ↓           ↓            ↓              ↓
Response ← Flask API ← RAG Answer ← Retrieved Docs
```

### 3. Conversation Flow
```
┌─────────────────┐
│ New User Query  │
└─────────┬───────┘
          │
          v
┌─────────────────┐    ┌──────────────────┐
│ Load Session    │    │ Query Rewriting  │
│ State           │ -> │ (Context-aware)  │
└─────────────────┘    └─────────┬────────┘
          │                      │
          v                      v
┌─────────────────┐    ┌──────────────────┐
│ Vector Search   │    │ Generate Response│
│ (ChromaDB)      │ -> │ (LLM + Context)  │
└─────────────────┘    └─────────┬────────┘
          │                      │
          v                      v
┌─────────────────┐    ┌──────────────────┐
│ Update Summary  │    │ Update Window    │
│ (Incremental)   │    │ (Token Budget)   │
└─────────────────┘    └─────────┬────────┘
          │                      │
          v                      v
┌─────────────────┐    ┌──────────────────┐
│ Save State      │    │ Return Response  │
│ (SQLite)        │    │ (JSON/Stream)    │
└─────────────────┘    └──────────────────┘
```

## 🛠️ Installation & Setup

### Prerequisites
```bash
pip install -r requirements.txt
```

### Configuration
Create a `.env` file:
```env
# Required
OPENAI_API_KEY=your-api-key-here

# Optional - Customize as needed
BASE_URL=https://api.openai.com/v1
CHAT_MODEL=gpt-4o
EMBED_MODEL=text-embedding-3-small
DATA_DIR=./data
CHROMA_DIR=./chroma
COLLECTION_NAME=knowledge_base
FLASK_PORT=5050

# Optional - Web UI authentication (leave WEB_PASSWORD empty to disable auth)
WEB_USER=admin
WEB_PASSWORD=

# Optional - Provider-specific extras
# TENSORIX_API_KEY takes precedence over OPENAI_API_KEY when set
# EXTRA_BODY_JSON forwards provider-specific params to the chat API, e.g.:
# EXTRA_BODY_JSON={"reasoning_effort":"low"}
```

### Quick Start
```bash
# 1. Prepare documents in ./data directory
mkdir data
# Add your PDF/DOCX/JSON/JSONL/TXT files to ./data

# 2. Build the vector index
python build_index.py

# 3. Start the server
python server.py

# 4. Test the API
curl -X POST http://localhost:5050/conversation \
  -H "Content-Type: application/json" \
  -d '{"message": "What is cybersecurity?"}'
```

## 🚀 Running as a Systemd Service

To run the server as a persistent service that starts automatically on boot:

### Create the service file

```bash
sudo tee /etc/systemd/system/cocyber-rag.service > /dev/null <<'EOF'
[Unit]
Description=CoCyber RAG Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/cocyber_rag
ExecStart=/opt/cocyber_rag/.venv/bin/python3 /opt/cocyber_rag/server.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable cocyber-rag
sudo systemctl start cocyber-rag
```

### Management commands

```bash
systemctl status cocyber-rag      # Check status
systemctl restart cocyber-rag     # Restart
systemctl stop cocyber-rag        # Stop
journalctl -u cocyber-rag -f      # Follow logs in real time
```

## 📊 Performance & Monitoring

### Token Management
- **Context Windows**: Automatic trimming to stay within model limits
- **Batch Processing**: Configurable batch sizes for optimal throughput
- **Rate Limiting**: Built-in exponential backoff for API limits

### Monitoring Endpoints
- **`GET /health`**: Real-time system status
- **Collection Metrics**: Document and chunk counts
- **Model Information**: Current model and capabilities

### Conversation Analytics
- **Token Usage**: Input, output, and total token tracking
- **Retrieval Metrics**: Number of chunks retrieved per query
- **Session Statistics**: Conversation length and summary size

## 🎯 Use Cases

### Cybersecurity Policy Development
- **Organizational Assessment**: Guided interviews to understand security posture
- **Framework Mapping**: NIST CSF 2.0, ISO 27001, CIS Controls alignment
- **Policy Generation**: Custom policies based on organizational needs
- **Compliance Verification**: Gap analysis and remediation planning

### Interactive Consultation
- **Expert Knowledge Access**: 24/7 access to cybersecurity expertise
- **Context-Aware Responses**: Maintains conversation context across sessions
- **Progressive Interviews**: Builds understanding through structured questioning
- **Documentation Generation**: Automatic policy and procedure creation

### Integration Scenarios
- **Web Applications**: REST API integration for custom interfaces
- **Chatbots**: Streaming responses for real-time user experience
- **Document Management**: Automated policy updates and version control
- **Compliance Tools**: Integration with existing security management platforms

This comprehensive RAG system provides a robust foundation for cybersecurity policy development while maintaining the flexibility to adapt to various organizational needs and technical environments.

## 📄 License

Copyright © 2026 The Lisbon Council asbl.

This project is licensed under the **European Union Public Licence (EUPL) v1.2**.
You may use, modify, and distribute it under the terms of the EUPL. See the [LICENSE](LICENSE) file for the full licence text, or visit:
<https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12>
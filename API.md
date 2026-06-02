# Cybersecurity Policy RAG API Documentation

This Flask server provides a REST API for a specialized cybersecurity policy generation RAG system. The system conducts structured interviews to help organizations create comprehensive cybersecurity policies based on frameworks like NIST CSF 2.0.

## Quick Start

1. **Start the server:**
```bash
python server.py
```

2. **Server will start on port 5050 by default:**
```
Starting Flask server on 0.0.0.0:5050
Debug mode: False
```

3. **Test the API:**
```bash
curl -X POST http://localhost:5050/conversation \
  -H "Content-Type: application/json" \
  -d '{"message": "What is cybersecurity?"}'
```

## Environment Variables

Configure the server using these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_HOST` | `0.0.0.0` | Server host address |
| `FLASK_PORT` | `5050` | Server port |
| `FLASK_DEBUG` | `False` | Debug mode (true/false) |

Plus all the standard RAG system environment variables from `.env`.

## API Endpoints

### POST /conversation

Submit a conversational query to the RAG system.

**URL:** `/conversation`  
**Method:** `POST`  
**Content-Type:** `application/json`

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | The user's question or message |
| `sessionId` | string | No | Conversation session identifier |

#### Behavior

- **New conversation:** If `sessionId` is not provided or `null`, creates a new conversation with auto-generated session ID
- **Continue conversation:** If `sessionId` is provided, continues the existing conversation using stored context

#### Response Structure

```json
{
  "question": "string",
  "answer": "string", 
  "sources": [
    {
      "title": "string",
      "source": "string"
    }
  ],
  "metadata": {
    "tokens_used": "number",
    "history_kept": "number", 
    "chunks_retrieved": "number",
    "summary_chars": "number"
  },
  "sessionId": "string"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `question` | string | The user's original question |
| `answer` | string | AI-generated response based on retrieved documents |
| `sources` | array | List of source documents used to generate the answer |
| `sources[].title` | string | Document title |
| `sources[].source` | string | Document source path/identifier |
| `metadata` | object | Query performance and conversation metrics |
| `metadata.tokens_used` | number | Total tokens used in the request |
| `metadata.history_kept` | number | Number of messages kept in conversation window |
| `metadata.chunks_retrieved` | number | Number of document chunks retrieved |
| `metadata.summary_chars` | number | Length of conversation summary |
| `sessionId` | string | Unique session identifier for the conversation |

### GET /health

Health check endpoint to verify system status.

**URL:** `/health`  
**Method:** `GET`

#### Response

```json
{
  "status": "healthy",
  "collection_documents": 41,
  "chat_model": "gpt-4o"
}
```

### POST /conversation/stream

Submit a conversational query with real-time streaming response.

**URL:** `/conversation/stream`  
**Method:** `POST`  
**Content-Type:** `application/json`

#### Request Body

Same as `/conversation` endpoint.

#### Response

**Content-Type:** `text/event-stream`

Streams Server-Sent Events with the following event types:

- `data`: Partial response chunks
- `sources`: Source documents (JSON)
- `metadata`: Query metadata (JSON) 
- `session_id`: Session identifier
- `error`: Error information
- `end`: End of stream marker

#### Example Streaming Response

```
data: The NIST Cybersecurity

data:  Framework is a guidance

data:  document that helps

event: sources
data: [{"title":"NIST CSF 2.0","source":"../jsonl/1004.json"}]

event: metadata  
data: {"tokens_used":1250,"chunks_retrieved":5}

event: session_id
data: a1b2c3d4-e5f6-7890-abcd-ef1234567890

event: end
data: 

```

### GET /

API information and documentation endpoint.

**URL:** `/`  
**Method:** `GET`

#### Response

Returns API metadata and endpoint documentation.

### GET /static/<filename>

Serves static files for the web testing interface.

**URL:** `/static/<filename>`  
**Method:** `GET`

#### Response

Returns static files (HTML, CSS, JS) used by the testing interface.

## Usage Examples

### 1. Start a New Conversation

```bash
curl -X POST http://localhost:5050/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the NIST Cybersecurity Framework?"
  }'
```

**Response:**
```json
{
  "question": "What is the NIST Cybersecurity Framework?",
  "answer": "The NIST Cybersecurity Framework (CSF) 2.0 is a guidance framework that helps organizations of any size, sector, or maturity level manage and reduce cybersecurity risks...",
  "sources": [
    {
      "title": "The NIST Cybersecurity Framework (CSF) 2.0",
      "source": "../jsonl/1004.json"
    }
  ],
  "metadata": {
    "tokens_used": 2372,
    "history_kept": 2,
    "chunks_retrieved": 5,
    "summary_chars": 853
  },
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### 2. Continue Existing Conversation

```bash
curl -X POST http://localhost:5050/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the main functions of this framework?",
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
```

**Response:**
```json
{
  "question": "What are the main functions of this framework?", 
  "answer": "The NIST Cybersecurity Framework has six main functions: Govern, Identify, Protect, Detect, Respond, and Recover...",
  "sources": [
    {
      "title": "The NIST Cybersecurity Framework (CSF) 2.0",
      "source": "../jsonl/0.json"
    }
  ],
  "metadata": {
    "tokens_used": 2845,
    "history_kept": 4,
    "chunks_retrieved": 5,
    "summary_chars": 1205
  },
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### 3. Health Check

```bash
curl -X GET http://localhost:5050/health
```

**Response:**
```json
{
  "status": "healthy",
  "collection_documents": 41,
  "chat_model": "gpt-4o"
}
```

## Error Responses

### Missing Required Parameter

**Request:**
```bash
curl -X POST http://localhost:5050/conversation \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:** `400 Bad Request`
```json
{
  "error": "Missing required parameter: message"
}
```

### Empty Message

**Request:**
```bash
curl -X POST http://localhost:5050/conversation \
  -H "Content-Type: application/json" \
  -d '{"message": ""}'
```

**Response:** `400 Bad Request`
```json
{
  "error": "Message must be a non-empty string"
}
```

### Invalid JSON

**Request:**
```bash
curl -X POST http://localhost:5050/conversation \
  -H "Content-Type: application/json" \
  -d 'invalid json'
```

**Response:** `400 Bad Request`
```json
{
  "error": "Request must be JSON"
}
```

### Internal Server Error

**Response:** `500 Internal Server Error`
```json
{
  "error": "Internal server error: [error details]"
}
```

## Cybersecurity Policy Interview System

This RAG system is specifically designed for cybersecurity policy generation through structured interviews:

### **Purpose and Workflow**
- **Guided Interview Process:** Conducts systematic interviews to understand organizational cybersecurity needs
- **Policy Generation:** Creates comprehensive cybersecurity policies based on gathered information
- **Framework Compliance:** Ensures alignment with NIST CSF 2.0 and other cybersecurity frameworks
- **Template-Based Output:** Generates structured policy documents with proper citations

### **Specialized Features**
- **Domain-Specific Knowledge Base:** 41+ documents covering cybersecurity frameworks, policies, and guidelines
- **Interview Structure:** Follows a systematic approach to gather organizational context
- **Compliance Mapping:** Maps organizational needs to relevant cybersecurity controls
- **Policy Templates:** Generates customized policies based on interview responses

## Conversation Management

The API maintains conversation state through the `sessionId`:

- **Session Storage:** Conversations are stored in SQLite database (`conversation_state.db`)
- **Context Window:** Recent messages are kept in memory for context (default: 2400 tokens)
- **Summary:** Longer conversations are summarized to maintain context efficiently
- **Token Management:** Conversation history is automatically trimmed to stay within token limits
- **Streaming State:** Real-time conversation state updates during streaming responses

## Integration Notes

- The server automatically initializes the RAG system on startup
- ChromaDB vector database with cybersecurity-focused document collection
- OpenAI-compatible API support with configurable endpoints
- Streaming responses via Server-Sent Events for real-time user experience
- Interactive web testing interface available at `/static/streaming_test.html`
- Error handling provides clear feedback for debugging
- Health endpoint can be used for monitoring and load balancer health checks

## Development

To run in debug mode:
```bash
FLASK_DEBUG=true python server.py
```

To run on a different port:
```bash
FLASK_PORT=8080 python server.py
```
#!/usr/bin/env python3
"""
Cybersecurity Policy Interview Tool with Context Window Management

This script conducts structured interviews for cybersecurity policy generation using 
a ChromaDB vector database and RAG (retrieval-augmented generation). It implements
a stateful conversation system that tracks interview progress, prevents question
repetition, and maintains context across long policy development sessions.

The tool specializes in cybersecurity policy creation through guided interviews,
extracting organizational requirements and generating tailored policy documents.

Requirements: pip install chromadb openai python-dotenv tiktoken
"""
import os, sys, argparse, json, sqlite3, uuid, logging, re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import deque

CHOICES_MARKER_RE = re.compile(r'<!--\s*choices:\s*(\[[\s\S]*?\])\s*-->')


def extract_choices(text: str) -> Tuple[str, List[str]]:
    """Strip the <!-- choices: [...] --> marker from text.

    Returns (clean_text, choices). Multiple markers are removed; the last
    parseable one wins. Marker is kept as-is in the text if its JSON payload
    is malformed, so the client fallback can still try to parse it.
    """
    if not text:
        return text, []
    choices: List[str] = []
    cleaned = text
    for m in list(CHOICES_MARKER_RE.finditer(text)):
        try:
            parsed = json.loads(m.group(1))
            if isinstance(parsed, list):
                choices = [str(c) for c in parsed]
                cleaned = cleaned.replace(m.group(0), '', 1)
        except (ValueError, TypeError):
            continue
    return cleaned.strip(), choices


class ChoicesStreamFilter:
    """Buffers a token stream to strip the choices marker before forwarding chunks.

    Holds back any tail that could be the start of `<!--`, plus any open marker
    that has not yet seen its closing `-->`. On flush() returns the tail.
    """

    _MARKER_OPEN = "<!--"

    def __init__(self):
        self._buf = ""
        self.choices: List[str] = []

    def feed(self, chunk: str) -> str:
        if not chunk:
            return ""
        self._buf += chunk

        # Extract any complete markers
        while True:
            m = CHOICES_MARKER_RE.search(self._buf)
            if not m:
                break
            try:
                parsed = json.loads(m.group(1))
                if isinstance(parsed, list):
                    self.choices = [str(c) for c in parsed]
            except (ValueError, TypeError):
                pass
            self._buf = self._buf[:m.start()] + self._buf[m.end():]

        hold_from = len(self._buf)

        # Hold any unfinished open marker (we have <!-- but no closing -->)
        open_idx = self._buf.find(self._MARKER_OPEN)
        if open_idx != -1 and "-->" not in self._buf[open_idx:]:
            hold_from = min(hold_from, open_idx)

        # Hold a tail that could still grow into <!-- (e.g. ends with "<", "<!", "<!-")
        for n in range(min(len(self._MARKER_OPEN) - 1, len(self._buf)), 0, -1):
            if self._buf.endswith(self._MARKER_OPEN[:n]):
                hold_from = min(hold_from, len(self._buf) - n)
                break

        emit = self._buf[:hold_from]
        self._buf = self._buf[hold_from:]
        return emit

    def flush(self) -> str:
        # Final pass: strip any remaining complete marker
        while True:
            m = CHOICES_MARKER_RE.search(self._buf)
            if not m:
                break
            try:
                parsed = json.loads(m.group(1))
                if isinstance(parsed, list):
                    self.choices = [str(c) for c in parsed]
            except (ValueError, TypeError):
                pass
            self._buf = self._buf[:m.start()] + self._buf[m.end():]
        out, self._buf = self._buf, ""
        return out
import chromadb
from openai import OpenAI
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import tiktoken

# Load environment variables from .env file in current directory
load_dotenv()


@dataclass
class ConversationState:
    """State for a conversation session."""
    session_id: str
    summary: str = ""
    window: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.window is None:
            self.window = []


class TokenCounter:
    """Utility for counting tokens in text."""
    
    def __init__(self, model_name: str = "gpt-4"):
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        if text is None:
            return 0
        return len(self.encoding.encode(str(text)))
    
    def count_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in a list of messages."""
        total = 0
        for message in messages:
            if not message:
                continue
            # Add tokens for role and content
            total += self.count_tokens(message.get("role") or "")
            content = message.get("content")
            if isinstance(content, list):
                # Handle Nebius format with content array
                for item in content:
                    if isinstance(item, dict) and item.get("text"):
                        total += self.count_tokens(item["text"])
            else:
                total += self.count_tokens(content or "")
            # Add overhead per message (role delimiters, etc.)
            total += 4
        return total


class StateStore:
    """Persistent storage for conversation states."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_states (
                    session_id TEXT PRIMARY KEY,
                    summary TEXT NOT NULL DEFAULT '',
                    window_json TEXT NOT NULL DEFAULT '[]',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def load_state(self, session_id: str) -> ConversationState:
        """Load conversation state for a session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT summary, window_json FROM conversation_states WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if row:
                summary, window_json = row
                window = json.loads(window_json)
                print(f"DEBUG: Loaded existing session {session_id[:8]}... - Summary: {len(summary)} chars, Window: {len(window)} messages")
                return ConversationState(session_id=session_id, summary=summary, window=window)
            else:
                print(f"DEBUG: Creating new session {session_id[:8]}...")
                return ConversationState(session_id=session_id)
    
    def save_state(self, state: ConversationState):
        """Save conversation state for a session."""
        with sqlite3.connect(self.db_path) as conn:
            print(f"DEBUG: Saving session {state.session_id[:8]}... - Summary: {len(state.summary)} chars, Window: {len(state.window)} messages")
            conn.execute("""
                INSERT OR REPLACE INTO conversation_states (session_id, summary, window_json, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (state.session_id, state.summary, json.dumps(state.window)))
            conn.commit()


def _load_extra_body() -> dict:
    """Load extra_body from EXTRA_BODY_JSON env var (provider-specific params, e.g. reasoning flags)."""
    raw = os.getenv("EXTRA_BODY_JSON", "").strip()
    if not raw:
        return {}
    try:
        val = json.loads(raw)
        if isinstance(val, dict):
            return val
        logging.warning(f"EXTRA_BODY_JSON is not a JSON object, ignoring: {raw!r}")
    except json.JSONDecodeError as e:
        logging.warning(f"EXTRA_BODY_JSON parse error ({e}), ignoring: {raw!r}")
    return {}


def get_config(args=None):
    """Get configuration from environment variables and command-line arguments."""
    config = {
        'chroma_dir': os.getenv("CHROMA_DIR", "./chroma"),
        'openai_base': os.getenv("BASE_URL", "https://api.openai.com/v1"),
        'openai_key': os.getenv("TENSORIX_API_KEY") or os.getenv("OPENAI_API_KEY", ""),
        'embed_model': os.getenv("EMBED_MODEL", "text-embedding-3-small"),
        'chat_model': os.getenv("CHAT_MODEL", os.getenv("DIRECT_ENDPOINT_MODEL", "gpt-4o")),
        'collection_name': os.getenv("COLLECTION_NAME", "knowledge_base"),
        'temperature': float(os.getenv("TEMPERATURE", "0.1")),
        'max_results': int(os.getenv("MAX_RESULTS", "5")),
        # Conversation-specific settings
        'window_max_tokens': int(os.getenv("WINDOW_MAX_TOKENS", "2400")),
        'summary_max_chars': int(os.getenv("SUMMARY_MAX_CHARS", "16000")),
        'state_db_path': os.getenv("STATE_DB_PATH", "./conversation_state.db"),
        'conversation_mode': True,
        'session_id': None,
        'seed': None,
        'extra_body': _load_extra_body(),
    }
    
    # Override with command-line arguments if provided
    if args:
        if args.chroma_dir:
            config['chroma_dir'] = args.chroma_dir
        if args.openai_base:
            config['openai_base'] = args.openai_base
        if args.openai_key:
            config['openai_key'] = args.openai_key
        if args.embed_model:
            config['embed_model'] = args.embed_model
        if args.chat_model:
            config['chat_model'] = args.chat_model
        if args.collection_name:
            config['collection_name'] = args.collection_name
        if args.temperature is not None:
            config['temperature'] = args.temperature
        if args.max_results:
            config['max_results'] = args.max_results
        # Conversation settings (default is True, can be disabled with --no-conversation)
        if hasattr(args, 'no_conversation') and args.no_conversation:
            config['conversation_mode'] = False
        elif hasattr(args, 'conversation') and args.conversation:
            config['conversation_mode'] = True
        if hasattr(args, 'session_id') and args.session_id:
            config['session_id'] = args.session_id
        if hasattr(args, 'window_max_tokens') and args.window_max_tokens:
            config['window_max_tokens'] = args.window_max_tokens
        if hasattr(args, 'summary_max_chars') and args.summary_max_chars:
            config['summary_max_chars'] = args.summary_max_chars
        if hasattr(args, 'state_db_path') and args.state_db_path:
            config['state_db_path'] = args.state_db_path
        if hasattr(args, 'seed') and args.seed is not None:
            config['seed'] = args.seed
        if hasattr(args, 'json') and args.json:
            config['json_mode'] = True
    
    return config


def validate_config(config):
    """Validate the configuration."""
    if not config['openai_key']:
        print("Error: No API key found. Set OPENAI_API_KEY in .env file or use --openai-key")
        return False
    
    if not os.path.exists(config['chroma_dir']):
        print(f"Error: ChromaDB directory {config['chroma_dir']} does not exist")
        print("Run build_index.py first to create the vector database")
        return False
    
    return True


def print_config(config):
    """Print the current configuration."""
    print("Configuration:")
    print(f"  ChromaDB directory: {config['chroma_dir']}")
    print(f"  API endpoint: {config['openai_base']}")
    print(f"  Embedding model: {config['embed_model']}")
    print(f"  Chat model: {config['chat_model']}")
    print(f"  Collection name: {config['collection_name']}")
    print(f"  Temperature: {config['temperature']}")
    print(f"  Max results: {config['max_results']}")
    print(f"  Window max tokens: {config['window_max_tokens']}")
    print(f"  Summary max chars: {config['summary_max_chars']}")


def inspect_model_capabilities(oai, config):
    """Inspect available models and their capabilities."""
    try:
        print("🔍 Model Information:")
        
        # Try to list available models
        try:
            models = oai.models.list()
            print(f"  Available models: {len(models.data)}")
            
            # Find current chat model info
            current_model = None
            for model in models.data:
                if model.id == config['chat_model']:
                    current_model = model
                    break
            
            if current_model:
                print(f"  Current model: {current_model.id}")
                if hasattr(current_model, 'context_length'):
                    print(f"  Context window: {current_model.context_length:,} tokens")
                if hasattr(current_model, 'max_completion_tokens'):
                    print(f"  Max completion: {current_model.max_completion_tokens:,} tokens")
                    
        except Exception as e:
            print(f"  Could not retrieve model list: {e}")
        
        # Known context windows for common models
        known_contexts = {
            'gpt-4': 8192,
            'gpt-4-turbo': 128000,
            'gpt-4o': 128000,
            'gpt-3.5-turbo': 16385,
            'claude-3-haiku': 200000,
            'claude-3-sonnet': 200000,
            'claude-3-opus': 200000,
        }
        
        model_name = config['chat_model'].lower()
        for known_model, context_size in known_contexts.items():
            if known_model in model_name:
                print(f"  Estimated context window: {context_size:,} tokens (based on model name)")
                break
        else:
            print(f"  Context window: Unknown (model: {config['chat_model']})")
            
    except Exception as e:
        print(f"  Model inspection failed: {e}")


def setup_clients(config):
    """Setup ChromaDB and OpenAI clients."""
    # Setup embedding function
    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=config['openai_key'],
        api_base=config['openai_base'],
        model_name=config['embed_model']
    )
    
    # Setup ChromaDB client
    client = chromadb.PersistentClient(path=config['chroma_dir'])
    
    try:
        col = client.get_collection(name=config['collection_name'], embedding_function=ef)
    except Exception as e:
        print(f"Error: Could not access collection '{config['collection_name']}': {e}")
        print("Make sure you've run build_index.py to create the vector database")
        return None, None
    
    # Setup OpenAI client
    oai = OpenAI(api_key=config['openai_key'], base_url=config['openai_base'])
    
    return col, oai


def format_message_for_nebius(role: str, content: str) -> dict:
    """Format message according to Nebius API requirements."""
    if role == "user":
        # Nebius requires user content in structured format
        return {
            "role": "user",
            "content": [{"type": "text", "text": content}]
        }
    else:
        # System and assistant messages use simple string format
        return {
            "role": role,
            "content": content
        }


def load_policy_templates() -> str:
    """Load all cybersecurity policy templates from policies/iso27k/ as a single block."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(script_dir, "policies", "iso27k")
    if not os.path.exists(templates_dir):
        return ""
    parts = []
    for fname in sorted(os.listdir(templates_dir)):
        if fname.endswith(".md"):
            fpath = os.path.join(templates_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    parts.append(f.read().strip())
            except Exception as e:
                logging.getLogger("rag.operations").warning(f"Could not load template {fname}: {e}")
    if not parts:
        return ""
    joined = "\n\n---\n\n".join(parts)
    return (
        "\n\n## ISO 27001 POLICY TEMPLATES\n\n"
        "The following are the official ISO 27001-compliant policy templates available for generation. "
        "When the user requests or discusses a specific policy type, identify the most relevant template "
        "below and use it as the EXACT output structure. Fill every [PLACEHOLDER] with information "
        "collected during the interview. Do not invent sections; do not omit mandatory sections.\n\n"
        + joined
    )


def load_system_prompt():
    """Load system prompt from parent directory, appending ISO 27001 policy templates."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        system_prompt_path = os.path.join(script_dir, "system-prompt")

        if os.path.exists(system_prompt_path):
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                base = f.read().strip()
        else:
            base = (
                "You are a helpful assistant. Answer the question using only the provided CONTEXT. "
                "If the information is not available in the context, say 'Information not available in the provided documents'. "
                "Always cite your sources using numbered references [1], [2], etc. that correspond to the source list that will be provided separately."
            )

        return base + load_policy_templates()

    except Exception as e:
        print(f"Warning: Could not load system prompt from file: {e}")
        return (
            "You are a helpful assistant. Answer the question using only the provided CONTEXT. "
            "If the information is not available in the context, say 'Information not available in the provided documents'. "
            "Always cite your sources using numbered references [1], [2], etc. that correspond to the source list that will be provided separately."
        )


def rewrite_query(state: ConversationState, user_msg: str, oai: OpenAI, config: dict) -> str:
    """Produce a self-contained query from summary + recent messages + user message."""
    # Skip rewriting for simple greetings or short queries
    simple_queries = ['hi', 'hello', 'hey', 'thanks', 'thank you', 'ok', 'okay', 'yes', 'no']
    if user_msg.lower().strip() in simple_queries or len(user_msg.strip()) < 10:
        return user_msg
    
    context_parts = []
    
    # Add summary if available
    if state.summary:
        context_parts.append(f"Previous conversation summary: {state.summary}")
    
    # Add recent messages from window
    if state.window:
        recent_messages = state.window[-3:]  # Last 3 messages for context
        recent_context = []
        for msg in recent_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            recent_context.append(f"{role}: {content}")
        
        if recent_context:
            context_parts.append("Recent conversation: " + " | ".join(recent_context))
    
    # If no context available, don't rewrite
    if not context_parts:
        return user_msg
    
    # Create rewrite prompt
    rewrite_messages = [
        format_message_for_nebius("system", 
            "Rewrite the user's question to be self-contained and searchable, "
            "incorporating relevant context from the conversation history. "
            "Keep it concise and focused on the key information needed."),
        format_message_for_nebius("user", 
            f"Context: {' '.join(context_parts)}\n\nUser question: {user_msg}\n\nRewritten query:")
    ]
    
    try:
        _dump_call("query_rewrite", state, rewrite_messages, config['chat_model'], 0.0, config['extra_body'], max_tokens=150)
        response = oai.chat.completions.create(
            model=config['chat_model'],
            messages=rewrite_messages,
            temperature=0.0,
            max_tokens=150,
            extra_body=config['extra_body'] or None,
        )
        _dump_response("query_rewrite", state, response)

        content = response.choices[0].message.content
        if content is None or (content and content.strip() == ""):
            logging.warning("Query rewrite returned None/empty content, using original")
            return user_msg
        return content.strip()
        
    except Exception as e:
        logging.warning(f"Query rewrite failed: {e}, using original")
        return user_msg


def summarize_incrementally(state: ConversationState, user_msg: str, assistant_msg: str, oai: OpenAI, config: dict) -> str:
    """Update the conversation summary incrementally."""
    new_exchange = f"User: {user_msg}\nAssistant: {assistant_msg}"
    
    if not state.summary:
        # First summary
        summary_prompt = f"Summarize this conversation exchange concisely:\n\n{new_exchange}"
    else:
        # Incremental update
        summary_prompt = (
            f"Current summary: {state.summary}\n\n"
            f"New exchange: {new_exchange}\n\n"
            f"Update the summary to include the new exchange, keeping it concise:"
        )
    
    try:
        summary_messages = [
            format_message_for_nebius("system",
                "Create a summary that preserves INTERVIEW FLOW STATE for cybersecurity policy generation. Include:\n\n"
                "1. INTERVIEW PROGRESS: Which step we're on in the policy generation process (info gathering, policy suggestion, drafting, review, etc.)\n"
                "2. ORGANIZATION DETAILS: Type, size, sector, geography, revenues, existing policies, governance structure\n"
                "3. POLICY REQUIREMENTS: What type of policy was identified, suggested, or being developed\n"
                "4. COLLECTED ANSWERS: Key information already gathered from previous questions\n"
                "5. NEXT STEPS: What still needs to be asked or accomplished\n"
                "6. KEY DECISIONS: Any approvals, feedback, or choices made by the user\n\n"
                "CRITICAL: If this is part of a structured interview process, preserve the interview state and progress. "
                "Keep under 500 words but prioritize interview flow preservation over other details."),
            format_message_for_nebius("user", summary_prompt),
        ]
        _dump_call("summarizer", state, summary_messages, config['chat_model'], 0.0, config['extra_body'], max_tokens=600)
        response = oai.chat.completions.create(
            model=config['chat_model'],
            messages=summary_messages,
            temperature=0.0,
            max_tokens=600,
            extra_body=config['extra_body'] or None,
        )
        _dump_response("summarizer", state, response)
        
        content = response.choices[0].message.content
        if content is None or (content and content.strip() == ""):
            logging.warning("Summarization returned None/empty content, keeping old summary")
            return state.summary
        new_summary = content.strip()
        
        # Truncate if too long
        if len(new_summary) > config['summary_max_chars']:
            # Keep the tail (more recent content)
            new_summary = "..." + new_summary[-(config['summary_max_chars']-3):]
        
        return new_summary
        
    except Exception as e:
        logging.error(f"Summarization failed: {e}")
        return state.summary  # Keep old summary on failure


_DUMP_PATH = "/tmp/cocyber_prompts.jsonl"


def _dump_call(call_type, state, messages, model, temperature, extra_body, max_tokens=None, seed=None, stream=False):
    """Append the exact payload of one chat completion call to a JSONL trace file."""
    try:
        import time as _t
        rec = {
            "ts": _t.time(),
            "phase": "request",
            "session_id": getattr(state, "session_id", None) if state else None,
            "call_type": call_type,
            "model": model,
            "temperature": temperature,
            "stream": stream,
            "extra_body": extra_body,
            "seed": seed,
            "max_tokens": max_tokens,
            "messages": [
                {"role": m.get("role"), "content_len": len(m.get("content", "")), "content": m.get("content", "")}
                for m in messages
            ],
        }
        with open(_DUMP_PATH, "a", encoding="utf-8") as _f:
            _f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as _e:
        logging.getLogger("rag.operations").warning(f"[DEBUG] prompt dump (request) failed: {_e}")


def _dump_response(call_type, state, response):
    """Append the usage metrics returned by Tensorix for one chat completion."""
    try:
        import time as _t
        usage = getattr(response, "usage", None)
        rec = {
            "ts": _t.time(),
            "phase": "response",
            "session_id": getattr(state, "session_id", None) if state else None,
            "call_type": call_type,
            "usage": usage.model_dump() if usage else None,
        }
        with open(_DUMP_PATH, "a", encoding="utf-8") as _f:
            _f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as _e:
        logging.getLogger("rag.operations").warning(f"[DEBUG] prompt dump (response) failed: {_e}")


def _extract_cached_tokens(usage):
    """Read prompt cache hit count from an OpenAI-compatible usage object."""
    if not usage:
        return 0
    details = getattr(usage, 'prompt_tokens_details', None)
    if details is None:
        return 0
    # SDK object exposes attributes; dict fallback for raw payloads
    if hasattr(details, 'cached_tokens'):
        return details.cached_tokens or 0
    if isinstance(details, dict):
        return details.get('cached_tokens') or 0
    return 0


def _handle_streaming_response(completion_params, oai, question, source_info, state, token_counter, state_store, is_conversation, config, messages):
    """Handle streaming response generation."""
    try:
        stream_response = oai.chat.completions.create(**completion_params)
        
        # Collect streaming chunks
        answer_chunks = []
        input_tokens = 0
        output_tokens = 0
        total_api_tokens = 0
        
        cached_tokens = 0
        for chunk in stream_response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                answer_chunks.append(content)
                # Yield chunk with incomplete status
                yield content, False, None

            # Capture token usage from final chunk
            if hasattr(chunk, 'usage') and chunk.usage:
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens
                total_api_tokens = chunk.usage.total_tokens
                cached_tokens = _extract_cached_tokens(chunk.usage)
        
        # Reconstruct full answer
        answer = ''.join(answer_chunks)
        
        # Calculate local token counts if API doesn't provide them
        if input_tokens == 0 and output_tokens == 0:
            input_tokens = token_counter.count_message_tokens(messages)
            output_tokens = token_counter.count_tokens(answer)
            total_api_tokens = input_tokens + output_tokens
        
        # Handle conversation state updates (same as non-streaming)
        proxy_metadata = None
        need_summary_and_trim = False
        if is_conversation:
            # Append the new exchange to the window first
            state.window.append({"role": "user", "content": question})
            state.window.append({"role": "assistant", "content": answer})

            # Decide whether the expensive summary+trim pass is needed.
            # The summarizer is a synchronous LLM call: skipping it when the
            # window still fits the budget removes the long pause that the
            # client otherwise sees right before the final SSE event.
            try:
                window_tokens = token_counter.count_message_tokens(state.window)
            except Exception as e:
                print(f"DEBUG: Error in token counting: {e}")
                raise
            need_summary_and_trim = window_tokens > config['window_max_tokens']

            if not need_summary_and_trim:
                # Fast path: persist immediately, no summarizer call
                state_store.save_state(state)

            # Metadata reflects state *before* any post-stream trim
            proxy_metadata = {
                "tokens_used": token_counter.count_message_tokens(messages),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cached_tokens": cached_tokens,
                "total_api_tokens": total_api_tokens,
                "history_kept": len(state.window),
                "chunks_retrieved": len(source_info) if source_info else 0,
                "summary_chars": len(state.summary)
            }

        # For non-conversation mode, still create basic metadata
        if not is_conversation and proxy_metadata is None:
            proxy_metadata = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cached_tokens": cached_tokens,
                "total_api_tokens": total_api_tokens,
                "tokens_used": TokenCounter(config['chat_model']).count_message_tokens(messages),
                "chunks_retrieved": len(source_info) if source_info else 0
            }

        # Yield final completion status BEFORE running any blocking
        # post-stream work. The client receives `done: true` immediately and
        # can close the SSE stream; the server then performs summary+trim
        # in the background of the same request.
        yield "", True, (answer, source_info, proxy_metadata)

        # Post-stream housekeeping: only runs when the window actually overflowed.
        if is_conversation and need_summary_and_trim:
            try:
                state.summary = summarize_incrementally(state, question, answer, oai, config)

                initial_window_size = len(state.window)
                while state.window:
                    if token_counter.count_message_tokens(state.window) <= config['window_max_tokens']:
                        break
                    state.window.pop(0)
                if len(state.window) < initial_window_size:
                    print(f"DEBUG: Window trimmed from {initial_window_size} to {len(state.window)} messages")

                state_store.save_state(state)
            except Exception as e:
                logging.error(f"Post-stream summary/trim failed: {e}")
        
    except Exception as e:
        # Yield error
        yield f"Error generating answer: {e}", True, (f"Error generating answer: {e}", [], None)


def validate_context_relevance(chunks):
    """
    Validate if retrieved chunks contain relevant cybersecurity policy content.
    Returns dict with is_valid (bool) and error_message (str).
    """
    if not chunks:
        return {
            "is_valid": False,
            "error_message": "No content retrieved from knowledge base."
        }
    
    # Patterns indicating placeholder or test content
    placeholder_patterns = [
        r'lorem\s+ipsum', r'dolor\s+sit\s+amet', r'consectetur\s+adipiscing',
        r'tempor\s+incididunt', r'magna\s+aliqua', r'eiusmod\s+tempor',
        r'labore\s+et\s+dolore', r'ut\s+enim\s+ad\s+minim',
        r'veniam\s+quis\s+nostrud', r'exercitation\s+ullamco',
        r'duis\s+aute\s+irure', r'reprehenderit\s+in\s+voluptate',
        r'placeholder', r'dummy\s+text', r'sample\s+content',
        r'test\s+data', r'example\s+text', r'filler\s+content'
    ]
    
    # Patterns indicating cybersecurity policy content
    policy_patterns = [
        r'policy', r'cybersecurity', r'security', r'compliance', r'governance',
        r'access\s+control', r'authentication', r'authorization', r'incident',
        r'risk\s+management', r'data\s+protection', r'privacy', r'audit',
        r'firewall', r'encryption', r'malware', r'vulnerability', r'threat',
        r'iso\s+27001', r'nist', r'gdpr', r'hipaa', r'sox', r'pci\s+dss',
        r'framework', r'standard', r'regulation', r'requirement', r'control'
    ]
    
    import re
    
    relevant_chunks = 0
    placeholder_chunks = 0
    total_chunks = len(chunks)
    
    for chunk in chunks:
        if not chunk or not isinstance(chunk, str):
            continue
            
        chunk_lower = chunk.lower()
        
        # Check for placeholder content
        has_placeholder = any(re.search(pattern, chunk_lower, re.IGNORECASE) 
                             for pattern in placeholder_patterns)
        
        # Check for policy-relevant content
        has_policy_content = any(re.search(pattern, chunk_lower, re.IGNORECASE) 
                               for pattern in policy_patterns)
        
        if has_placeholder and not has_policy_content:
            placeholder_chunks += 1
        elif has_policy_content:
            relevant_chunks += 1
    
    # Calculate relevance ratio
    relevance_ratio = relevant_chunks / total_chunks if total_chunks > 0 else 0
    placeholder_ratio = placeholder_chunks / total_chunks if total_chunks > 0 else 0
    
    # Validation logic
    minimum_relevance_threshold = 0.4  # 40% of chunks should be relevant
    maximum_placeholder_threshold = 0.6  # No more than 60% placeholder content
    
    if placeholder_ratio > maximum_placeholder_threshold:
        return {
            "is_valid": False,
            "error_message": (
                "I cannot create a cybersecurity policy because the available knowledge base "
                "contains placeholder text (Lorem Ipsum or test content) rather than actual "
                "cybersecurity policy information. To generate an accurate policy, I need access "
                "to real cybersecurity frameworks, regulations, and policy examples. "
                f"Found {placeholder_chunks}/{total_chunks} chunks with placeholder content."
            )
        }
    
    if relevance_ratio < minimum_relevance_threshold:
        return {
            "is_valid": False,
            "error_message": (
                "I cannot create a cybersecurity policy because the retrieved content lacks "
                "sufficient cybersecurity policy information. The knowledge base should contain "
                "actual policy frameworks, security standards, and regulatory guidance. "
                f"Only {relevant_chunks}/{total_chunks} chunks contain relevant policy content."
            )
        }
    
    # Additional check: if chunks are very short or generic
    avg_chunk_length = sum(len(chunk) for chunk in chunks if chunk) / len(chunks)
    if avg_chunk_length < 20:
        return {
            "is_valid": False,
            "error_message": (
                "The retrieved content appears to be too brief or fragmented to generate "
                "a comprehensive cybersecurity policy. Please ensure the knowledge base "
                "contains detailed policy documentation."
            )
        }
    
    return {
        "is_valid": True,
        "error_message": None
    }


def rag_answer(question, col, oai, config, system_prompt=None, state=None, token_counter=None, state_store=None, stream=False):
    """Perform RAG query and generate answer with optional conversation context.
    
    Args:
        stream: If True, returns a generator that yields (chunk, is_complete, metadata) tuples
    """
    # Set up logging for RAG operations
    rag_logger = logging.getLogger('rag.operations')
    
    try:
        # Determine if we're in conversation mode
        is_conversation = state is not None and token_counter is not None and state_store is not None
        
        rag_logger.info(f"[RAG_ENGINE] RAG query started - Conversation mode: {is_conversation}, Stream: {stream}")
        rag_logger.info(f"[RAG_ENGINE] Original question: {question[:200]}{'...' if len(question) > 200 else ''}")
        
        # Query rewriting for conversation mode
        if is_conversation:
            query = rewrite_query(state, question, oai, config)
            rag_logger.info(f"[RAG_ENGINE] Query rewritten: {query[:200]}{'...' if len(query) > 200 else ''}")
        else:
            query = question
            rag_logger.info("[RAG_ENGINE] No query rewriting (not in conversation mode)")
        
        # Query the vector database
        rag_logger.info(f"[RAG_ENGINE] Querying vector database for max {config['max_results']} results")
        res = col.query(query_texts=[query], n_results=config['max_results'])
        
        # Extract documents and metadata
        chunks = [d for docs in res["documents"] for d in docs]
        sources = [m for metas in res["metadatas"] for m in metas]
        
        rag_logger.info(f"[RAG_ENGINE] Vector search returned {len(chunks)} chunks from {len(sources)} sources")
        
        if not chunks:
            rag_logger.warning("[RAG_ENGINE] No relevant documents found in vector database")
            if stream:
                def _no_chunks_generator():
                    msg = "No relevant documents found in the database."
                    yield msg, True, (msg, [], None)
                return _no_chunks_generator()
            return "No relevant documents found in the database.", [], None
        
        # Log context quality without blocking — templates in system prompt are the primary source
        context_validation = validate_context_relevance(chunks)
        if not context_validation["is_valid"]:
            rag_logger.warning(f"[RAG_ENGINE] Context quality warning (non-blocking): {context_validation['error_message']}")
        else:
            rag_logger.info("[RAG_ENGINE] Context validation passed")
        
        # Build context
        context_parts = []
        
        # Add conversation summary if available
        if is_conversation and state.summary:
            rag_logger.info(f"[RAG_ENGINE] Adding conversation summary ({len(state.summary)} chars) to context")
            context_parts.append(f"CONVERSATION SUMMARY:\n{state.summary}")
        
        # Add retrieved chunks
        context_parts.append("RELEVANT DOCUMENTS:")
        context = "\n\n".join(chunks)
        context_parts.append(context)
        
        total_context_length = sum(len(part) for part in context_parts)
        rag_logger.info(f"[RAG_ENGINE] Built context with {len(context_parts)} parts, total length: {total_context_length} chars")
        
        # Extract unique source-title pairs
        source_info = []
        seen_sources = set()
        
        for s in sources:
            if s and s.get("source", "unknown") not in seen_sources:
                source = s.get("source", "unknown")
                title = s.get("title", "") or s.get("metadata_title", "")
                seen_sources.add(source)
                source_info.append((source, title))
        
        # Create source mapping
        if source_info:
            source_mapping = "\n\nSOURCE MAPPING:\n"
            for i, (source, title) in enumerate(source_info, 1):
                if title:
                    source_mapping += f"[{i}] {title} ({source})\n"
                else:
                    source_mapping += f"[{i}] {source}\n"
            context_parts.append(source_mapping)
        
        full_context = "\n\n".join(context_parts)
        
        # Load system prompt
        if system_prompt is None:
            system_prompt = load_system_prompt()
        
        # Build messages using Nebius format
        messages = [format_message_for_nebius("system", system_prompt)]
        
        # Add conversation history if available (format each message)
        if is_conversation and state.window:
            for msg in state.window:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                messages.append(format_message_for_nebius(role, content))
        
        # Add current user message with context
        user_content = f"CONTEXT:\n{full_context}\n\nQUESTION:\n{question}"
        messages.append(format_message_for_nebius("user", user_content))
        
        # Generate completion parameters
        completion_params = {
            "model": config['chat_model'],
            "messages": messages,
            "temperature": config['temperature'],
            "stream": stream,
            "extra_body": config['extra_body'] or None
        }
        
        if config.get('seed') is not None:
            completion_params["seed"] = config['seed']

        _dump_call(
            "main_answer", state, completion_params["messages"],
            completion_params["model"], completion_params["temperature"],
            completion_params.get("extra_body"),
            seed=completion_params.get("seed"),
            stream=completion_params.get("stream", False),
        )

        if stream:
            return _handle_streaming_response(completion_params, oai, question, source_info, state, token_counter, state_store, is_conversation, config, messages)

        # Generate response (non-streaming)
        response = oai.chat.completions.create(**completion_params)
        _dump_response("main_answer", state, response)
        answer = response.choices[0].message.content
        
        # Capture token usage from response
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0
        total_api_tokens = response.usage.total_tokens if response.usage else 0
        cached_tokens = _extract_cached_tokens(response.usage)
        
        # Calculate local token counts if API doesn't provide them
        if input_tokens == 0 and output_tokens == 0:
            input_tokens = token_counter.count_message_tokens(messages)
            output_tokens = token_counter.count_tokens(answer)
            total_api_tokens = input_tokens + output_tokens
        
        # Handle None response
        if answer is None:
            return "Error: Received empty response from the model.", [], None
        
        # Handle conversation state updates
        proxy_metadata = None
        if is_conversation:
            # DEBUG: Log state before potential summarization
            print(f"DEBUG: Before summarization - Window: {len(state.window)} messages, Summary: {len(state.summary)} chars")

            # Append the new exchange to the window first
            state.window.append({"role": "user", "content": question})
            state.window.append({"role": "assistant", "content": answer})

            # Decide whether summary+trim is needed. Skipping the summarizer
            # call on turns that still fit the budget avoids a synchronous
            # LLM round-trip per turn.
            try:
                window_tokens = token_counter.count_message_tokens(state.window)
                print(f"DEBUG: Window has {len(state.window)} messages, {window_tokens} tokens (limit: {config['window_max_tokens']})")
            except Exception as e:
                print(f"DEBUG: Error in token counting: {e}")
                print(f"DEBUG: Window content: {state.window}")
                import traceback
                traceback.print_exc()
                raise

            if window_tokens > config['window_max_tokens']:
                # Overflow path: summarize, then trim
                old_summary = state.summary
                state.summary = summarize_incrementally(state, question, answer, oai, config)
                print(f"DEBUG: Summary changed from {len(old_summary)} to {len(state.summary)} chars")
                if len(old_summary) > 0 and len(state.summary) < len(old_summary):
                    print("DEBUG: WARNING - Summary got shorter! Possible information loss.")

                try:
                    initial_window_size = len(state.window)
                    while state.window:
                        current_tokens = token_counter.count_message_tokens(state.window)
                        if current_tokens <= config['window_max_tokens']:
                            break
                        removed_msg = state.window.pop(0)
                        print(f"DEBUG: Removed message: {removed_msg.get('role', 'unknown')}: {removed_msg.get('content', '')[:50]}...")
                    if len(state.window) < initial_window_size:
                        print(f"DEBUG: Window trimmed from {initial_window_size} to {len(state.window)} messages")
                except Exception as e:
                    print(f"DEBUG: Error during window trim: {e}")
                    import traceback
                    traceback.print_exc()
                    raise

            # Save state
            state_store.save_state(state)
            
            # Create metadata
            proxy_metadata = {
                "tokens_used": token_counter.count_message_tokens(messages),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cached_tokens": cached_tokens,
                "total_api_tokens": total_api_tokens,
                "history_kept": len(state.window),
                "chunks_retrieved": len(chunks),
                "summary_chars": len(state.summary)
            }

        # For non-conversation mode, still create basic metadata for verbose display
        if not is_conversation and proxy_metadata is None:
            proxy_metadata = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cached_tokens": cached_tokens,
                "total_api_tokens": total_api_tokens,
                "tokens_used": TokenCounter(config['chat_model']).count_message_tokens(messages) if not token_counter else token_counter.count_message_tokens(messages),
                "chunks_retrieved": len(chunks)
            }
        
        return answer, source_info, proxy_metadata
        
    except Exception as e:
        import traceback
        err_msg = f"Error generating answer: {e}"
        logging.getLogger("rag.operations").error(f"[RAG_ENGINE] Unhandled exception in rag_answer: {err_msg}\n{traceback.format_exc()}")
        if stream:
            def _error_generator(msg=err_msg):
                yield msg, True, (msg, [], None)
            return _error_generator()
        return err_msg, [], None


def interactive_mode(col, oai, config):
    """Run interactive query mode."""
    is_conversation = config['conversation_mode']
    is_json_mode = config.get('json_mode', False)
    session_id = config.get('session_id') or str(uuid.uuid4())
    
    # Setup conversation components if needed
    state = None
    token_counter = None
    state_store = None
    
    if is_conversation:
        token_counter = TokenCounter(config['chat_model'])
        state_store = StateStore(config['state_db_path'])
        state = state_store.load_state(session_id)
        
        if not is_json_mode:
            print(f"\n🤖 Conversation Mode - Session: {session_id}")
            print("Type 'exit' or 'quit' to exit, 'help' for commands")
            print("Type 'config' to show configuration, 'info' for session info")
            print("Type 'new' to start a new session, 'context' to view current context")
    else:
        if not is_json_mode:
            print("\n=== Interactive RAG Query Mode ===")
            print("Type 'exit' or 'quit' to exit, 'help' for commands")
            print("Type 'config' to show current configuration")
    
    if not is_json_mode:
        print()
    
    while True:
        try:
            if is_json_mode:
                question = input().strip()
            else:
                question = input("💬 Say anything: " if is_conversation else "Say anything: ").strip()
            
            if question.lower() in ['exit', 'quit']:
                if not is_json_mode:
                    print("👋 Goodbye!" if is_conversation else "Goodbye!")
                break
            elif question.lower() == 'help' and not is_json_mode:
                print("\n📖 Commands:" if is_conversation else "\nCommands:")
                print("  exit/quit - Exit the program")
                print("  config    - Show current configuration")
                print("  help      - Show this help")
                if is_conversation:
                    print("  info      - Show session information")
                    print("  new       - Start a new session")
                    print("  context   - Show current conversation context")
                print()
                continue
            elif question.lower() == 'config' and not is_json_mode:
                print()
                print_config(config)
                print()
                continue
            elif question.lower() == 'info' and is_conversation and not is_json_mode:
                print(f"\n📋 Session Information:")
                print(f"  Session ID: {session_id}")
                print(f"  Summary length: {len(state.summary)} chars")
                print(f"  Window messages: {len(state.window)}")
                print()
                continue
            elif question.lower() == 'new' and is_conversation and not is_json_mode:
                session_id = str(uuid.uuid4())
                state = state_store.load_state(session_id)
                print(f"🆕 New session started: {session_id}")
                continue
            elif question.lower() == 'context' and is_conversation and not is_json_mode:
                print(f"\n📝 Current Conversation Context:")
                print(f"  Session ID: {session_id}")
                
                if state.summary:
                    print(f"\n📋 Summary ({len(state.summary)} chars):")
                    print(f"  {state.summary}")
                else:
                    print(f"\n📋 Summary: (empty)")
                
                if state.window:
                    print(f"\n💬 Recent Messages ({len(state.window)} messages):")
                    for i, msg in enumerate(state.window[-6:], 1):  # Show last 6 messages
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        # Truncate long messages for display
                        display_content = content[:100] + "..." if len(content) > 100 else content
                        print(f"  {i}. {role}: {display_content}")
                    if len(state.window) > 6:
                        print(f"  ... (showing last 6 of {len(state.window)} messages)")
                else:
                    print(f"\n💬 Recent Messages: (empty)")
                
                # Show token usage if available
                if token_counter:
                    total_tokens = token_counter.count_message_tokens(state.window)
                    print(f"\n🔢 Token Usage:")
                    print(f"  Window tokens: {total_tokens}/{config['window_max_tokens']}")
                    print(f"  Summary chars: {len(state.summary)}/{config['summary_max_chars']}")
                
                print()
                continue
            elif not question:
                continue
            
            if not is_json_mode:
                print("🔍 Processing..." if is_conversation else "\nSearching...")
            
            if is_conversation:
                if not is_json_mode:
                    # Use streaming for interactive mode
                    print(f"\n🤖 Coach:\n", end="", flush=True)
                    full_answer = ""
                    final_metadata = None
                    final_sources = None
                    
                    stream_response = rag_answer(
                        question, col, oai, config, 
                        state=state, token_counter=token_counter, state_store=state_store,
                        stream=True
                    )
                    
                    for chunk, is_complete, metadata_tuple in stream_response:
                        if is_complete:
                            # Final chunk with complete response data
                            full_answer, final_sources, final_metadata = metadata_tuple
                        else:
                            # Stream chunk to console
                            print(chunk, end="", flush=True)
                    
                    print()  # New line after streaming
                    answer, source_info, metadata = full_answer, final_sources, final_metadata
                else:
                    # Non-streaming for JSON mode
                    answer, source_info, metadata = rag_answer(
                        question, col, oai, config, 
                        state=state, token_counter=token_counter, state_store=state_store
                    )
            else:
                if not is_json_mode:
                    # Use streaming for interactive mode
                    print(f"\nCoach:\n", end="", flush=True)
                    full_answer = ""
                    final_metadata = None
                    final_sources = None
                    
                    stream_response = rag_answer(question, col, oai, config, stream=True)
                    
                    for chunk, is_complete, metadata_tuple in stream_response:
                        if is_complete:
                            # Final chunk with complete response data
                            full_answer, final_sources, final_metadata = metadata_tuple
                        else:
                            # Stream chunk to console
                            print(chunk, end="", flush=True)
                    
                    print()  # New line after streaming
                    answer, source_info, metadata = full_answer, final_sources, final_metadata
                else:
                    # Non-streaming for JSON mode
                    answer, source_info, metadata = rag_answer(question, col, oai, config)
            
            if is_json_mode:
                # JSON output format
                result = {
                    "question": question,
                    "answer": answer,
                    "sources": [{"title": title or source, "source": source} for source, title in source_info],
                    "metadata": metadata or {},
                    "sessionId": session_id
                }
                print(json.dumps(result, indent=2))
            else:
                # For streaming mode, answer was already printed during streaming
                print(f"\n🤖 Coach:\n{answer}" if is_conversation else f"\nCoach:\n{answer}")
                
                if source_info:
                    print(f"\n📚 Sources:" if is_conversation else f"\nSources:")
                    for i, (source, title) in enumerate(source_info, 1):
                        if title:
                            print(f"  {i}. {title} [{source}]")
                        else:
                            print(f"  {i}. {source}")
                
                # Show metadata in conversation mode
                if is_conversation and metadata:
                    print(f"\n📊 Metadata:")
                    if 'input_tokens' in metadata and 'output_tokens' in metadata:
                        print(f"   Input tokens: {metadata.get('input_tokens', 'N/A')}")
                        print(f"   Output tokens: {metadata.get('output_tokens', 'N/A')}")
                        print(f"   Total API tokens: {metadata.get('total_api_tokens', 'N/A')}")
                    print(f"   Message tokens: {metadata.get('tokens_used', 'N/A')}")
                    print(f"   History: {metadata.get('history_kept', 'N/A')} messages")
                    print(f"   Chunks: {metadata.get('chunks_retrieved', 'N/A')}")
                    print(f"   Summary: {metadata.get('summary_chars', 'N/A')} chars")
                
                print("\n" + "="*50 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!" if is_conversation else "\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Cybersecurity Policy Interview Tool - ChromaDB RAG with conversation context management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                        # Interactive interview mode (default)
  %(prog)s "What is cybersecurity?"               # Single interview question
  %(prog)s -k 10 "How to implement NIST framework?"  # Custom max results
  %(prog)s --chat-model gpt-3.5-turbo "Quick question"  # Custom model
  %(prog)s --session-id my-session "Follow up question"  # Continue specific session
  %(prog)s --no-conversation "Single query"      # Disable conversation mode

Environment Variables:
  CHROMA_DIR          ChromaDB persistence directory (default: ./chroma)
  BASE_URL            OpenAI-compatible API endpoint (default: https://api.openai.com/v1)
  OPENAI_API_KEY      API key for embeddings and chat
  EMBED_MODEL         Embedding model name (default: text-embedding-3-small)
  CHAT_MODEL          Chat model name (default: gpt-4o)
  COLLECTION_NAME     ChromaDB collection name (default: knowledge_base)
  TEMPERATURE         Response temperature (default: 0.1)
  MAX_RESULTS         Max documents to retrieve (default: 5)
  WINDOW_MAX_TOKENS   Max tokens in conversation window (default: 1200)
  SUMMARY_MAX_CHARS   Max characters in summary (default: 8000)
  STATE_DB_PATH       Conversation state database path (default: ./conversation_state.db)
        """
    )
    
    parser.add_argument('question', nargs='?', 
                       help='Question to ask (if not provided, enters interactive mode)')
    
    # Basic RAG options
    parser.add_argument('--chroma-dir', type=str,
                       help='ChromaDB persistence directory')
    parser.add_argument('--openai-base', type=str,
                       help='OpenAI-compatible API base URL')
    parser.add_argument('--openai-key', type=str,
                       help='OpenAI API key')
    parser.add_argument('--embed-model', type=str,
                       help='Embedding model name')
    parser.add_argument('--chat-model', type=str,
                       help='Chat model name')
    parser.add_argument('--collection-name', type=str,
                       help='ChromaDB collection name')
    parser.add_argument('--temperature', type=float,
                       help='Response temperature (0.0-2.0)')
    parser.add_argument('-k', '--max-results', type=int,
                       help='Maximum number of documents to retrieve')
    parser.add_argument('--system-prompt', type=str,
                       help='Custom system prompt for the AI')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    # Conversation mode options
    parser.add_argument('--conversation', action='store_true',
                       help='Enable conversation mode with context management (default: enabled)')
    parser.add_argument('--no-conversation', action='store_true',
                       help='Disable conversation mode for single-query operation')
    parser.add_argument('--session-id', type=str,
                       help='Session ID for conversation mode (generates new if not provided)')
    parser.add_argument('--window-max-tokens', type=int,
                       help='Maximum tokens in conversation window')
    parser.add_argument('--summary-max-chars', type=int,
                       help='Maximum characters in conversation summary')
    parser.add_argument('--state-db-path', type=str,
                       help='Path to conversation state database')
    parser.add_argument('--seed', type=int,
                       help='Random seed for deterministic responses')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    
    return parser.parse_args()


def main():
    """Main function."""
    try:
        args = parse_arguments()
        config = get_config(args)
        
        if not validate_config(config):
            sys.exit(1)
        
        if args.verbose:
            print_config(config)
            print()
        
        # Setup clients
        col, oai = setup_clients(config)
        if col is None or oai is None:
            sys.exit(1)
        
        if args.verbose:
            print(f"Connected to collection '{config['collection_name']}'")
            
            # Inspect model capabilities
            inspect_model_capabilities(oai, config)
            print()
            
            # Get chunk and document counts
            chunk_count = col.count()
            all_results = col.get()
            
            # Count unique documents by extracting filename from chunk IDs
            unique_documents = set()
            for doc_id in all_results['ids']:
                if '::r' in doc_id:
                    # JSONL format: filename::r{row}::c{chunk}::{uuid}
                    filename = doc_id.split('::r')[0]
                elif '::p' in doc_id:
                    # PDF format: filename::p{page}::c{chunk}::{uuid}  
                    filename = doc_id.split('::p')[0]
                elif '::c' in doc_id:
                    # JSON format: filename::c{chunk}::{uuid}
                    filename = doc_id.split('::c')[0]
                else:
                    # Fallback: use first part before any ::
                    filename = doc_id.split('::')[0]
                
                unique_documents.add(filename)
            
            print(f"Collection contains {chunk_count} chunks from {len(unique_documents)} documents")
            print()
        
        # Single question mode or interactive mode
        if args.question:
            # Single question mode
            is_json_mode = config.get('json_mode', False)
            
            if args.verbose and not is_json_mode:
                print(f"Question: {args.question}\n")
            
            # Setup conversation components if needed
            if config['conversation_mode']:
                session_id = config.get('session_id') or str(uuid.uuid4())
                token_counter = TokenCounter(config['chat_model'])
                state_store = StateStore(config['state_db_path'])
                state = state_store.load_state(session_id)
                
                if args.verbose and not is_json_mode:
                    print(f"Session ID: {session_id}")
                
                answer, source_info, metadata = rag_answer(
                    args.question, col, oai, config, args.system_prompt,
                    state=state, token_counter=token_counter, state_store=state_store
                )
                
                if metadata and args.verbose and not is_json_mode:
                    print(f"\n📊 Token Usage:")
                    if 'input_tokens' in metadata and 'output_tokens' in metadata:
                        print(f"   Input tokens: {metadata.get('input_tokens', 'N/A')}")
                        print(f"   Output tokens: {metadata.get('output_tokens', 'N/A')}")
                        print(f"   Total API tokens: {metadata.get('total_api_tokens', 'N/A')}")
                    print(f"   Message tokens: {metadata.get('tokens_used', 'N/A')}")
                    if config['conversation_mode']:
                        print(f"   History: {metadata.get('history_kept', 'N/A')} messages")
                        print(f"   Summary: {metadata.get('summary_chars', 'N/A')} chars")
                    print(f"   Chunks: {metadata.get('chunks_retrieved', 'N/A')}")
            else:
                answer, source_info, metadata = rag_answer(args.question, col, oai, config, args.system_prompt)
            
            if is_json_mode:
                # JSON output format
                if not config['conversation_mode']:
                    session_id = str(uuid.uuid4())
                result = {
                    "question": args.question,
                    "answer": answer,
                    "sources": [{"title": title or source, "source": source} for source, title in source_info],
                    "metadata": metadata or {},
                    "sessionId": session_id
                }
                print(json.dumps(result, indent=2))
            else:
                # For streaming mode, answer was already printed during streaming
                print(f"Coach:\n{answer}")
                
                if source_info:
                    print(f"\nSources:")
                    for i, (source, title) in enumerate(source_info, 1):
                        if title:
                            print(f"  {i}. {title} [{source}]")
                        else:
                            print(f"  {i}. {source}")
        else:
            # Interactive mode
            interactive_mode(col, oai, config)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

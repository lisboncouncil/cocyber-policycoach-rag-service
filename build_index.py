#!/usr/bin/env python3
"""
ChromaDB Index Builder for Local RAG

This script builds a ChromaDB vector index from PDF, DOCX, TXT, JSON and JSONL files for local
retrieval-augmented generation (RAG). It processes documents in a specified
directory, extracts text content, creates embeddings, and stores them in a
persistent ChromaDB collection.

Requirements: pip install chromadb pypdf python-docx python-dotenv
"""
import os, json, math, uuid, sys, argparse, time
import chromadb
from pypdf import PdfReader
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# Load environment variables from .env file in current directory
load_dotenv()


def get_config(args=None):
    """Get configuration from environment variables and command-line arguments."""
    config = {
        'data_dir': os.getenv("DATA_DIR", "./data"),
        'chroma_dir': os.getenv("CHROMA_DIR", "./chroma"),
        'openai_base': os.getenv("BASE_URL", "https://api.openai.com/v1"),
        'openai_key': os.getenv("TENSORIX_API_KEY") or os.getenv("OPENAI_API_KEY", ""),
        'embed_model': os.getenv("EMBED_MODEL", "text-embedding-3-small"),
        'chunk_tokens': int(os.getenv("CHUNK_TOKENS", "200")),
        'collection_name': os.getenv("COLLECTION_NAME", "knowledge_base"),
        'batch_size': int(os.getenv("BATCH_SIZE", "50")),
        'batch_delay': float(os.getenv("BATCH_DELAY", "2.0")),
        'max_retries': int(os.getenv("MAX_RETRIES", "5"))
    }
    
    # Override with command-line arguments if provided
    if args:
        if args.data_dir:
            config['data_dir'] = args.data_dir
        if args.chroma_dir:
            config['chroma_dir'] = args.chroma_dir
        if args.openai_base:
            config['openai_base'] = args.openai_base
        if args.openai_key:
            config['openai_key'] = args.openai_key
        if args.embed_model:
            config['embed_model'] = args.embed_model
        if args.chunk_tokens:
            config['chunk_tokens'] = args.chunk_tokens
        if args.collection_name:
            config['collection_name'] = args.collection_name
        if args.batch_size:
            config['batch_size'] = args.batch_size
        if args.batch_delay:
            config['batch_delay'] = args.batch_delay
        if args.max_retries:
            config['max_retries'] = args.max_retries
    
    return config


def validate_collection_name(name):
    """Validate ChromaDB collection name according to their requirements."""
    import re
    
    # ChromaDB requirements:
    # - 3-512 characters
    # - Only [a-zA-Z0-9._-]
    # - Must start and end with [a-zA-Z0-9]
    
    if len(name) < 3 or len(name) > 512:
        return False, "Collection name must be 3-512 characters long"
    
    # Check full pattern: starts with alphanumeric, contains only valid chars, ends with alphanumeric
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$', name):
        # Special case: single alphanumeric character names (3+ chars requirement already checked)
        if len(name) == 3 and re.match(r'^[a-zA-Z0-9]{3}$', name):
            return True, ""
        return False, "Collection name must start and end with alphanumeric character and contain only letters, numbers, dots, underscores, and hyphens"
    
    return True, ""


def validate_config(config):
    """Validate the configuration."""
    if not config['openai_key']:
        print("Error: No API key found. Set OPENAI_API_KEY in .env file or use --openai-key")
        return False
    
    if not os.path.exists(config['data_dir']):
        print(f"Error: Data directory {config['data_dir']} does not exist")
        return False
    
    # Validate collection name
    is_valid, error_msg = validate_collection_name(config['collection_name'])
    if not is_valid:
        print(f"Error: Invalid collection name '{config['collection_name']}': {error_msg}")
        return False
    
    return True


def print_config(config, use_semantic=False, chunk_overlap=100):
    """Print the current configuration."""
    print("Configuration:")
    print(f"  Data directory: {config['data_dir']}")
    print(f"  ChromaDB directory: {config['chroma_dir']}")
    print(f"  API endpoint: {config['openai_base']}")
    print(f"  Embedding model: {config['embed_model']}")
    print(f"  Chunk size: {config['chunk_tokens']} tokens")
    print(f"  Chunking strategy: {'Semantic (sentence boundaries)' if use_semantic else 'Character-based'}")
    if use_semantic:
        print(f"  Chunk overlap: {chunk_overlap} characters")
    print(f"  Collection name: {config['collection_name']}")
    print(f"  Batch size: {config['batch_size']}")
    print(f"  Batch delay: {config['batch_delay']} seconds")
    print(f"  Max retries: {config['max_retries']}")


def setup_chromadb(config):
    """Setup ChromaDB client and collection."""
    # Embedding function (OpenAI-compat)
    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=config['openai_key'], 
        api_base=config['openai_base'], 
        model_name=config['embed_model']
    )
    
    client = chromadb.PersistentClient(path=config['chroma_dir'])
    col = client.get_or_create_collection(name=config['collection_name'], embedding_function=ef)
    
    return client, col

def chunk_text(text, max_chars=800):
    """Split text into chunks of approximately max_chars length."""
    if not text:
        return []
    # Ensure chunks are not too large for embedding APIs
    step = min(max_chars, 800)  # Cap at 800 chars (~200 tokens)
    chunks = []
    for i in range(0, len(text), step):
        chunk = text[i:i+step].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)
    return chunks


def semantic_chunk_text(text, max_chars=800, overlap_chars=100):
    """Split text into chunks on sentence boundaries while respecting character limits."""
    if not text:
        return []
    
    # Try to import sentence tokenizer
    try:
        import nltk
        # Download punkt tokenizer if not available
        try:
            nltk.data.find('tokenizers/punkt_tab')
            # Try the newer punkt_tab format first
        except LookupError:
            try:
                nltk.data.find('tokenizers/punkt')
                # Fall back to older punkt format
            except LookupError:
                print("Downloading NLTK punkt tokenizer for sentence boundary detection...")
                nltk.download('punkt_tab', quiet=True)
        
        # Clean the text and tokenize
        clean_text = text.strip()
        sentences = nltk.sent_tokenize(clean_text)
        
        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
    except ImportError:
        print("NLTK not available, falling back to regex-based sentence splitting...")
        # Fallback to regex-based sentence splitting
        import re
        clean_text = text.strip()
        sentences = re.split(r'(?<=[.!?])\s+', clean_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
    except Exception as e:
        print(f"NLTK tokenization failed ({e}), falling back to regex-based sentence splitting...")
        # Fallback to regex-based sentence splitting
        import re
        clean_text = text.strip()
        sentences = re.split(r'(?<=[.!?])\s+', clean_text)
        sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        sentence_length = len(sentence)
        
        # If adding this sentence would exceed the limit and we have content, finalize chunk
        if current_length + sentence_length > max_chars and current_chunk:
            chunk_text_content = " ".join(current_chunk).strip()
            if chunk_text_content:
                chunks.append(chunk_text_content)
            
            # Start new chunk with current sentence
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 for space
    
    # Add final chunk if it has content
    if current_chunk:
        chunk_text_content = " ".join(current_chunk).strip()
        if chunk_text_content:
            chunks.append(chunk_text_content)
    
    # Apply overlap if requested and we have multiple chunks
    if overlap_chars > 0 and len(chunks) > 1:
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                # First chunk - no prefix overlap
                overlapped_chunks.append(chunk)
            else:
                # Add overlap from previous chunk
                prev_chunk = chunks[i-1]
                if len(prev_chunk) > overlap_chars:
                    overlap = prev_chunk[-overlap_chars:]
                    # Find a good break point (sentence or word boundary)
                    space_pos = overlap.find(' ')
                    if space_pos > 0:
                        overlap = overlap[space_pos+1:]
                    overlapped_chunk = overlap + " " + chunk
                else:
                    overlapped_chunk = chunk
                overlapped_chunks.append(overlapped_chunk)
        chunks = overlapped_chunks
    
    return chunks


def get_chunking_function(use_semantic=False):
    """Return appropriate chunking function based on strategy."""
    if use_semantic:
        return semantic_chunk_text
    else:
        return chunk_text


def ingest_pdf(path, chunk_tokens=500, use_semantic=False, chunk_overlap=100):
    """Process a PDF file and yield document chunks."""
    chunking_fn = get_chunking_function(use_semantic)
    try:
        reader = PdfReader(path)
        for p, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            max_chars = chunk_tokens * 3
            if use_semantic:
                chunks = chunking_fn(text, max_chars=max_chars, overlap_chars=chunk_overlap)
            else:
                chunks = chunking_fn(text, max_chars=max_chars)
            
            for j, chunk in enumerate(chunks):
                yield {
                    "id": f"{os.path.basename(path)}::p{p}::c{j}::{uuid.uuid4().hex[:8]}",
                    "document": chunk,
                    "metadata": {
                        "source": path, 
                        "type": "pdf", 
                        "page": p,
                        "chunking_strategy": "semantic" if use_semantic else "character"
                    }
                }
    except Exception as e:
        print(f"Error processing PDF {path}: {e}")


def flatten_metadata(meta, prefix=""):
    """Flatten nested metadata to ChromaDB-compatible format."""
    flattened = {}
    for key, value in meta.items():
        new_key = f"{prefix}{key}" if prefix else key
        if isinstance(value, dict):
            flattened.update(flatten_metadata(value, f"{new_key}_"))
        elif isinstance(value, (str, int, float, bool)) or value is None:
            flattened[new_key] = value
        else:
            # Convert other types to string
            flattened[new_key] = str(value)
    return flattened


def ingest_json(path, chunk_tokens=500, use_semantic=False, chunk_overlap=100):
    """Process a JSON file and yield document chunks."""
    chunking_fn = get_chunking_function(use_semantic)
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
            # Extract useful text; fallback: serialize everything
            text = obj.get("text") or obj.get("content") or json.dumps(obj, ensure_ascii=False)
            max_chars = chunk_tokens * 3
            if use_semantic:
                chunks = chunking_fn(text, max_chars=max_chars, overlap_chars=chunk_overlap)
            else:
                chunks = chunking_fn(text, max_chars=max_chars)
            
            for j, chunk in enumerate(chunks):
                meta = {k:v for k,v in obj.items() if k not in ("text","content")}
                meta.update({
                    "source": path, 
                    "type": "json",
                    "chunking_strategy": "semantic" if use_semantic else "character"
                })
                # Flatten metadata for ChromaDB compatibility
                flattened_meta = flatten_metadata(meta)
                yield {
                    "id": f"{os.path.basename(path)}::c{j}::{uuid.uuid4().hex[:8]}",
                    "document": chunk,
                    "metadata": flattened_meta
                }
    except Exception as e:
        print(f"Error processing JSON {path}: {e}")


def ingest_jsonl(path, chunk_tokens=500, use_semantic=False, chunk_overlap=100):
    """Process a JSONL file and yield document chunks."""
    chunking_fn = get_chunking_function(use_semantic)
    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                obj = json.loads(line)
                # Extract useful text; fallback: serialize everything
                text = obj.get("text") or obj.get("content") or json.dumps(obj, ensure_ascii=False)
                max_chars = chunk_tokens * 3
                if use_semantic:
                    chunks = chunking_fn(text, max_chars=max_chars, overlap_chars=chunk_overlap)
                else:
                    chunks = chunking_fn(text, max_chars=max_chars)
                
                for j, chunk in enumerate(chunks):
                    meta = {k:v for k,v in obj.items() if k not in ("text","content")}
                    meta.update({
                        "source": path, 
                        "type": "jsonl", 
                        "row": i,
                        "chunking_strategy": "semantic" if use_semantic else "character"
                    })
                    # Flatten metadata for ChromaDB compatibility
                    flattened_meta = flatten_metadata(meta)
                    yield {
                        "id": f"{os.path.basename(path)}::r{i}::c{j}::{uuid.uuid4().hex[:8]}",
                        "document": chunk,
                        "metadata": flattened_meta
                    }
    except Exception as e:
        print(f"Error processing JSONL {path}: {e}")


def ingest_txt(path, chunk_tokens=500, use_semantic=False, chunk_overlap=100):
    """Process a TXT file and yield document chunks."""
    chunking_fn = get_chunking_function(use_semantic)
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
            max_chars = chunk_tokens * 3
            if use_semantic:
                chunks = chunking_fn(text, max_chars=max_chars, overlap_chars=chunk_overlap)
            else:
                chunks = chunking_fn(text, max_chars=max_chars)

            for j, chunk in enumerate(chunks):
                yield {
                    "id": f"{os.path.basename(path)}::c{j}::{uuid.uuid4().hex[:8]}",
                    "document": chunk,
                    "metadata": {
                        "source": path,
                        "type": "txt",
                        "chunking_strategy": "semantic" if use_semantic else "character"
                    }
                }
    except Exception as e:
        print(f"Error processing TXT {path}: {e}")


def ingest_docx(path, chunk_tokens=500, use_semantic=False, chunk_overlap=100):
    """Process a DOCX file and yield document chunks."""
    chunking_fn = get_chunking_function(use_semantic)
    try:
        from docx import Document
        doc = Document(path)

        # Extract text from all paragraphs
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        text = "\n".join(paragraphs)

        max_chars = chunk_tokens * 3
        if use_semantic:
            chunks = chunking_fn(text, max_chars=max_chars, overlap_chars=chunk_overlap)
        else:
            chunks = chunking_fn(text, max_chars=max_chars)

        for j, chunk in enumerate(chunks):
            yield {
                "id": f"{os.path.basename(path)}::c{j}::{uuid.uuid4().hex[:8]}",
                "document": chunk,
                "metadata": {
                    "source": path,
                    "type": "docx",
                    "chunking_strategy": "semantic" if use_semantic else "character"
                }
            }
    except ImportError:
        print(f"Error: python-docx library not installed. Install with: pip install python-docx")
    except Exception as e:
        print(f"Error processing DOCX {path}: {e}")


def add_documents_with_retry(col, ids, docs, metas, config):
    """Add documents with retry logic for rate limiting."""
    for attempt in range(config['max_retries']):
        try:
            col.add(ids=ids, documents=docs, metadatas=metas)
            return True
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "capacity exceeded" in error_str or "rate" in error_str.lower():
                if attempt < config['max_retries'] - 1:
                    wait_time = (2 ** attempt) * config['batch_delay']  # Exponential backoff
                    print(f"  Rate limit hit, waiting {wait_time:.1f} seconds before retry {attempt + 1}/{config['max_retries']}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  Failed after {config['max_retries']} retries due to rate limiting")
                    raise e
            elif "Too many tokens" in error_str:
                # Handle token limit by splitting batch
                smaller_batch_size = max(5, len(ids) // 2)
                print(f"  Token limit exceeded, splitting batch into smaller chunks of {smaller_batch_size}")
                for i in range(0, len(ids), smaller_batch_size):
                    batch_ids = ids[i:i+smaller_batch_size]
                    batch_docs = docs[i:i+smaller_batch_size]
                    batch_metas = metas[i:i+smaller_batch_size]
                    add_documents_with_retry(col, batch_ids, batch_docs, batch_metas, config)
                    if i + smaller_batch_size < len(ids):  # Not the last batch
                        time.sleep(config['batch_delay'])
                return True
            else:
                # Other errors, don't retry
                raise e
    return False


def process_documents(config, col, verbose=False, use_semantic=False):
    """Process all documents in the data directory and add to ChromaDB collection."""
    ids, docs, metas = [], [], []
    processed_files = 0
    total_chunks = 0
    
    chunking_strategy = "semantic" if use_semantic else "character-based"
    print(f"Scanning directory: {config['data_dir']}")
    print(f"Using {chunking_strategy} chunking strategy")
    
    # First, scan all files for debugging
    all_files = []
    for root, _, files in os.walk(config['data_dir']):
        for name in files:
            path = os.path.join(root, name)
            all_files.append((path, name, os.path.splitext(name.lower())[1]))
    
    if verbose or len(all_files) == 0:
        print(f"Found {len(all_files)} total files:")
        for path, name, ext in all_files:
            print(f"  {name} (extension: {ext})")
    
    if len(all_files) == 0:
        print(f"No files found in {config['data_dir']}")
        return 0, 0
    
    # Process supported files
    for path, name, ext in all_files:
        if ext == ".pdf":
            if verbose:
                print(f"Processing PDF: {name}")
            gen = ingest_pdf(path, config['chunk_tokens'], use_semantic, config.get('chunk_overlap', 100))
        elif ext == ".docx":
            if verbose:
                print(f"Processing DOCX: {name}")
            gen = ingest_docx(path, config['chunk_tokens'], use_semantic, config.get('chunk_overlap', 100))
        elif ext == ".json":
            if verbose:
                print(f"Processing JSON: {name}")
            gen = ingest_json(path, config['chunk_tokens'], use_semantic, config.get('chunk_overlap', 100))
        elif ext == ".jsonl":
            if verbose:
                print(f"Processing JSONL: {name}")
            gen = ingest_jsonl(path, config['chunk_tokens'], use_semantic, config.get('chunk_overlap', 100))
        elif ext == ".txt":
            if verbose:
                print(f"Processing TXT: {name}")
            gen = ingest_txt(path, config['chunk_tokens'], use_semantic, config.get('chunk_overlap', 100))
        else:
            if verbose:
                print(f"Skipping unsupported file: {name} (extension: {ext})")
            continue
        
        file_chunks = 0
        for rec in gen:
            ids.append(rec["id"])
            docs.append(rec["document"])
            metas.append(rec["metadata"])
            file_chunks += 1
            total_chunks += 1
            
            # Batch insertion with rate limiting and retry logic
            if len(ids) >= config['batch_size']:
                add_documents_with_retry(col, ids, docs, metas, config)
                print(f"  Added batch of {len(ids)} chunks to collection")
                ids, docs, metas = [], [], []
                # Add delay between batches to respect rate limits
                time.sleep(config['batch_delay'])
        
        if file_chunks > 0:
            processed_files += 1
            print(f"  -> {file_chunks} chunks extracted")
    
    # Final flush
    if ids:
        add_documents_with_retry(col, ids, docs, metas, config)
        print(f"  Added final batch of {len(ids)} chunks to collection")
    
    print(f"\nIngestion completed:")
    print(f"  Files processed: {processed_files}")
    print(f"  Total chunks: {total_chunks}")
    return processed_files, total_chunks


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Build ChromaDB vector index from PDF, DOCX, TXT, JSON and JSONL files for local RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Use default configuration
  %(prog)s --data-dir ./documents             # Custom data directory
  %(prog)s --collection-name my_docs          # Custom collection name
  %(prog)s --chunk-tokens 1000 --batch-size 256  # Custom chunking and batching
  %(prog)s --openai-key sk-... --embed-model text-embedding-ada-002  # Custom API settings
  %(prog)s --semantic-chunking --collection-name docs_semantic  # Use semantic chunking
  %(prog)s --semantic-chunking --chunk-overlap 150  # Semantic chunking with custom overlap

Environment Variables:
  DATA_DIR          Source directory for documents (default: ./data)
  CHROMA_DIR        ChromaDB persistence directory (default: ./chroma)
  BASE_URL          OpenAI-compatible API endpoint (default: https://api.openai.com/v1)
  OPENAI_API_KEY    API key for embeddings
  EMBED_MODEL       Embedding model name (default: text-embedding-3-small)
  CHUNK_TOKENS      Token limit per chunk (default: 500)
  COLLECTION_NAME   ChromaDB collection name (default: knowledge_base)
  BATCH_SIZE        Documents per batch (default: 50)
  BATCH_DELAY       Delay between batches in seconds (default: 2.0)
  MAX_RETRIES       Maximum retry attempts for rate limits (default: 5)
        """
    )

    parser.add_argument('--data-dir', type=str,
                       help='Source directory containing PDF, DOCX, TXT, JSON and JSONL files')
    parser.add_argument('--chroma-dir', type=str,
                       help='ChromaDB persistence directory')
    parser.add_argument('--openai-base', type=str,
                       help='OpenAI-compatible API base URL')
    parser.add_argument('--openai-key', type=str,
                       help='OpenAI API key for embeddings')
    parser.add_argument('--embed-model', type=str,
                       help='Embedding model name')
    parser.add_argument('--chunk-tokens', type=int,
                       help='Maximum tokens per text chunk')
    parser.add_argument('--collection-name', type=str,
                       help='ChromaDB collection name')
    parser.add_argument('--batch-size', type=int,
                       help='Number of documents to process in each batch')
    parser.add_argument('--batch-delay', type=float,
                       help='Delay between batches in seconds')
    parser.add_argument('--max-retries', type=int,
                       help='Maximum retry attempts for rate limits')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show configuration and exit without processing')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--semantic-chunking', action='store_true',
                       help='Use semantic chunking (sentence boundaries) instead of character-based chunking')
    parser.add_argument('--chunk-overlap', type=int, default=100,
                       help='Character overlap between chunks when using semantic chunking (default: 100)')
    
    return parser.parse_args()


def main():
    """Main function."""
    try:
        args = parse_arguments()
        config = get_config(args)
        
        if not validate_config(config):
            sys.exit(1)
        
        print_config(config, args.semantic_chunking, args.chunk_overlap)
        print()
        
        if args.dry_run:
            print("Dry run mode - exiting without processing documents")
            return
        
        # Setup ChromaDB
        client, col = setup_chromadb(config)
        
        # Add chunking configuration to config
        config['use_semantic_chunking'] = args.semantic_chunking
        config['chunk_overlap'] = args.chunk_overlap
        
        # Process documents
        processed_files, total_chunks = process_documents(config, col, args.verbose, args.semantic_chunking)

        if processed_files == 0:
            print("Warning: No PDF, DOCX, TXT, JSON or JSONL files found to process")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

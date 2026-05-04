import tiktoken
import re

enc = tiktoken.get_encoding("cl100k_base")

def extract_sections(text):
    pattern = re.compile(
        r"(?:^|\n)"                         # start of line
        r"(?:ITEM|Item)\s+"                 # "Item " or "ITEM "
        r"(\d+[A-Z]?)"                      # item number: 1, 1A, 7, 7A...
        r"[\.\:\s\-\—]*"                    # separator (dot, colon, dash...)
        r"([^\n]{0,80})",                   # section title (first 80 chars of line)
        re.MULTILINE,
    )
    
    matches = list(pattern.finditer(text))
    
    if not matches:
        return [{"item": "0", "title": "Full Document", "text": text}]
    
    sections = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        
        sections.append({
            "item": match.group(1).upper(),
            "title": match.group(2).strip(),
            "text": text[start:end].strip(),
        })
    
    return sections


def chunk_section(
    section_text: str,
    chunk_size: int = 400,
    overlap: int = 50,
) -> list[str]:
    tokens = enc.encode(section_text)
    
    # If section fits in one chunk, return as-is
    if len(tokens) <= chunk_size:
        return [section_text]
    
    # Split on double newlines first (paragraph boundaries)
    paragraphs = section_text.split("\n\n")
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        para_tokens = len(enc.encode(para))
        
        # If a single paragraph exceeds chunk_size, split it with sliding window
        if para_tokens > chunk_size:
            # Flush current buffer first
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_tokens = 0
            
            # Sliding window on the big paragraph
            tokens_list = enc.encode(para)
            start = 0
            while start < len(tokens_list):
                end = min(start + chunk_size, len(tokens_list))
                chunks.append(enc.decode(tokens_list[start:end]))
                if end >= len(tokens_list):
                    break
                start += chunk_size - overlap
            continue
        
        # Would adding this paragraph exceed the chunk size?
        if current_tokens + para_tokens > chunk_size:
            # Save current chunk
            chunks.append("\n\n".join(current_chunk))
            
            # Start new chunk — keep last paragraph for overlap/continuity
            if overlap > 0 and current_chunk:
                last = current_chunk[-1]
                last_tokens = len(enc.encode(last))
                current_chunk = [last]
                current_tokens = last_tokens
            else:
                current_chunk = []
                current_tokens = 0
        
        current_chunk.append(para)
        current_tokens += para_tokens
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
    
    return chunks


def chunk_10k(text: str, ticker: str, chunk_size: int = 400) -> list[dict]:
    sections = extract_sections(text)
    all_chunks = []
    
    for section in sections:
        chunks = chunk_section(section["text"], chunk_size=chunk_size)
        
        for i, chunk_text in enumerate(chunks):
            all_chunks.append({
                "text": chunk_text,
                "metadata": {
                    "ticker": ticker,
                    "item": section["item"],
                    "section_title": section["title"],
                    "chunk_index": i,
                    "total_chunks_in_section": len(chunks),
                    "token_count": len(enc.encode(chunk_text)),
                },
            })
    
    return all_chunks
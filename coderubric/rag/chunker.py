"""
Code chunking module for RAG.

Splits code into semantic chunks (functions, classes) with metadata
for effective vector storage and retrieval.
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata."""
    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_type: str  # 'function', 'class', 'method', 'standalone'
    name: Optional[str] = None
    language: str = ""
    imports: List[str] = None
    
    def __post_init__(self):
        if self.imports is None:
            self.imports = []
    
    @property
    def id(self) -> str:
        """Generate unique ID for this chunk."""
        return f"{self.file_path}:{self.start_line}:{self.end_line}"
    
    def to_embedding_text(self) -> str:
        """Convert chunk to text format suitable for embedding."""
        header = f"File: {self.file_path}\n"
        if self.name:
            header += f"Name: {self.name}\n"
        if self.chunk_type:
            header += f"Type: {self.chunk_type}\n"
        if self.imports:
            header += f"Imports: {', '.join(self.imports)}\n"
        return f"{header}\n```\n{self.content}\n```"


class CodeChunker:
    """Chunks code files into semantic units."""
    
    LANGUAGE_PATTERNS = {
        'python': {
            'function': r'def\s+(\w+)',
            'class': r'class\s+(\w+)',
            'import': r'^(?:import|from)\s+(\S+)',
            'comment': r'#.*$',
        },
        'javascript': {
            'function': r'(?:function|const|let|var)\s+(\w+)\s*[\(=]',
            'class': r'class\s+(\w+)',
            'method': r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{',
            'import': r'^(?:import|require)',
            'comment': r'//.*$|/\*.*?\*/',
        },
        'typescript': {
            'function': r'(?:function|const|let|var)\s+(\w+)\s*[\(=:].*?(?:=>|\{)',
            'class': r'class\s+(\w+)',
            'interface': r'interface\s+(\w+)',
            'method': r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*[:\{]',
            'import': r'^(?:import|require)',
            'comment': r'//.*$|/\*.*?\*/',
        },
        'java': {
            'function': r'(?:public|private|protected)?\s*(?:static\s+)?\w+\s+(\w+)\s*\(',
            'class': r'class\s+(\w+)',
            'import': r'^import\s+',
            'comment': r'//.*$|/\*.*?\*/',
        },
    }
    
    def __init__(self, max_chunk_size: int = 2000):
        self.max_chunk_size = max_chunk_size
    
    def detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        mapping = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
        }
        return mapping.get(ext, 'unknown')
    
    def extract_imports(self, content: str, language: str) -> List[str]:
        """Extract import statements from code."""
        patterns = self.LANGUAGE_PATTERNS.get(language, {})
        import_pattern = patterns.get('import', r'')
        if not import_pattern:
            return []
        
        imports = []
        for line in content.split('\n'):
            match = re.match(import_pattern, line.strip())
            if match:
                imports.append(line.strip())
        return imports
    
    def chunk_file(self, file_path: str, content: str) -> List[CodeChunk]:
        """Split a file into semantic chunks."""
        language = self.detect_language(file_path)
        lines = content.split('\n')
        chunks = []
        
        if language == 'python':
            chunks = self._chunk_python(file_path, content, lines)
        elif language in ['javascript', 'typescript']:
            chunks = self._chunk_js_ts(file_path, content, lines, language)
        else:
            # Generic chunking for unsupported languages
            chunks = self._chunk_generic(file_path, content, lines, language)
        
        # Extract imports for each chunk
        imports = self.extract_imports(content, language)
        for chunk in chunks:
            chunk.imports = imports
        
        return chunks
    
    def _chunk_python(self, file_path: str, content: str, lines: List[str]) -> List[CodeChunk]:
        """Python-specific chunking using indentation."""
        chunks = []
        current_chunk = []
        start_line = 0
        current_type = 'standalone'
        current_name = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            
            # Check for function/class definition
            if stripped.startswith('def ') or stripped.startswith('class '):
                # Save previous chunk if exists
                if current_chunk and current_type != 'standalone':
                    chunks.append(CodeChunk(
                        content='\n'.join(current_chunk),
                        file_path=file_path,
                        start_line=start_line + 1,
                        end_line=i,
                        chunk_type=current_type,
                        name=current_name,
                        language='python'
                    ))
                
                # Start new chunk
                current_chunk = [line]
                start_line = i
                
                if stripped.startswith('def '):
                    current_type = 'function'
                    match = re.match(r'def\s+(\w+)', stripped)
                    current_name = match.group(1) if match else None
                else:
                    current_type = 'class'
                    match = re.match(r'class\s+(\w+)', stripped)
                    current_name = match.group(1) if match else None
            else:
                current_chunk.append(line)
            
            i += 1
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(CodeChunk(
                content='\n'.join(current_chunk),
                file_path=file_path,
                start_line=start_line + 1,
                end_line=len(lines),
                chunk_type=current_type,
                name=current_name,
                language='python'
            ))
        
        return chunks
    
    def _chunk_js_ts(self, file_path: str, content: str, lines: List[str], language: str) -> List[CodeChunk]:
        """JavaScript/TypeScript chunking."""
        chunks = []
        current_chunk = []
        start_line = 0
        brace_count = 0
        in_function = False
        current_type = 'standalone'
        current_name = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Detect function/class start
            if not in_function:
                func_match = re.search(r'(?:function|class)\s+(\w+)', line)
                arrow_match = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(', line)
                
                if func_match or arrow_match:
                    # Save previous chunk
                    if current_chunk and current_type != 'standalone':
                        chunks.append(CodeChunk(
                            content='\n'.join(current_chunk),
                            file_path=file_path,
                            start_line=start_line + 1,
                            end_line=i,
                            chunk_type=current_type,
                            name=current_name,
                            language=language
                        ))
                    
                    current_chunk = [line]
                    start_line = i
                    in_function = True
                    brace_count = line.count('{') - line.count('}')
                    
                    if func_match:
                        current_name = func_match.group(1)
                        current_type = 'function' if 'function' in line else 'class'
                    elif arrow_match:
                        current_name = arrow_match.group(1)
                        current_type = 'function'
                else:
                    current_chunk.append(line)
            else:
                current_chunk.append(line)
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0:
                    # Function/class ended
                    chunks.append(CodeChunk(
                        content='\n'.join(current_chunk),
                        file_path=file_path,
                        start_line=start_line + 1,
                        end_line=i + 1,
                        chunk_type=current_type,
                        name=current_name,
                        language=language
                    ))
                    in_function = False
                    current_chunk = []
                    current_type = 'standalone'
                    current_name = None
            
            i += 1
        
        # Handle any remaining content
        if current_chunk and current_type != 'standalone':
            chunks.append(CodeChunk(
                content='\n'.join(current_chunk),
                file_path=file_path,
                start_line=start_line + 1,
                end_line=len(lines),
                chunk_type=current_type,
                name=current_name,
                language=language
            ))
        
        return chunks
    
    def _chunk_generic(self, file_path: str, content: str, lines: List[str], language: str) -> List[CodeChunk]:
        """Generic chunking for unsupported languages - chunks by size."""
        chunks = []
        current_chunk = []
        start_line = 0
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            
            # Create chunk when we hit max size
            if len('\n'.join(current_chunk)) > self.max_chunk_size:
                chunks.append(CodeChunk(
                    content='\n'.join(current_chunk),
                    file_path=file_path,
                    start_line=start_line + 1,
                    end_line=i + 1,
                    chunk_type='chunk',
                    language=language
                ))
                current_chunk = []
                start_line = i + 1
        
        # Add remaining lines
        if current_chunk:
            chunks.append(CodeChunk(
                content='\n'.join(current_chunk),
                file_path=file_path,
                start_line=start_line + 1,
                end_line=len(lines),
                chunk_type='chunk',
                language=language
            ))
        
        return chunks

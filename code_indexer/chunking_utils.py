"""
Utilities for chunking code files in a semantic way
"""
import os
import re

def chunk_code_file(content, file_path):
    """
    Chunk a code file in a way that preserves semantic meaning
    
    Args:
        content (str): The file content
        file_path (str): Path to the file (used to determine language)
        
    Returns:
        list: List of chunks
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    # Determine chunking strategy based on file extension
    if ext in ['.py']:
        return chunk_python_file(content)
    elif ext in ['.java', '.cs', '.cpp', '.c', '.h']:
        return chunk_c_style_file(content)
    elif ext in ['.js', '.ts']:
        return chunk_javascript_file(content)
    else:
        # Default chunking for unknown file types
        return chunk_by_lines(content)

def chunk_python_file(content):
    """Chunk a Python file by classes and functions"""
    chunks = []
    
    # Split by classes and functions
    class_pattern = r'(class\s+\w+\s*(?:\([^)]*\))?\s*:(?:.|\n)*?)(?=\n\S|$)'
    function_pattern = r'(def\s+\w+\s*\([^)]*\)\s*(?:->.*?)?\s*:(?:.|\n)*?)(?=\n\S|$)'
    
    # Extract classes
    classes = re.findall(class_pattern, content)
    for class_def in classes:
        chunks.append(class_def)
        # Remove classes from content to avoid duplication
        content = content.replace(class_def, '')
    
    # Extract functions (that aren't part of classes)
    functions = re.findall(function_pattern, content)
    for func_def in functions:
        chunks.append(func_def)
        content = content.replace(func_def, '')
    
    # Get imports and module-level code
    lines = content.split('\n')
    current_chunk = []
    
    for line in lines:
        if line.strip() and not line.startswith(' '):
            current_chunk.append(line)
        elif current_chunk:
            # Continue adding indented lines to the current chunk
            current_chunk.append(line)
            
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    # If we have very few chunks, just return the whole file
    if len(chunks) <= 1:
        return [content]
        
    return chunks

def chunk_c_style_file(content):
    """Chunk a C-style file (Java, C#, C++, etc.) by classes and methods"""
    chunks = []
    
    # Match class/struct definitions and their content
    class_pattern = r'((?:public|private|protected)?\s*(?:class|struct|interface)\s+\w+(?:<.*?>)?(?:\s+extends\s+\w+(?:<.*?>)?)?(?:\s+implements\s+[\w,\s<>]+)?\s*\{(?:.|\n)*?)(^\})'
    class_matches = re.finditer(class_pattern, content, re.MULTILINE)
    
    class_positions = []
    for match in class_matches:
        chunks.append(match.group(0))
        class_positions.append((match.start(), match.end()))
    
    # Match method definitions outside of classes
    method_pattern = r'((?:public|private|protected|static|final|native|synchronized|abstract|transient)(?:\s+(?:public|private|protected|static|final|native|synchronized|abstract|transient))*\s+[\w<>\[\]]+\s+\w+\s*\([^\)]*\)(?:\s+throws[\w,\s]+)?\s*\{(?:.|\n)*?)(^\})'
    
    # Find positions not covered by classes
    uncovered_ranges = [(0, len(content))]
    for start, end in sorted(class_positions):
        new_ranges = []
        for range_start, range_end in uncovered_ranges:
            if range_start < start:
                new_ranges.append((range_start, start))
            if end < range_end:
                new_ranges.append((end, range_end))
        uncovered_ranges = new_ranges
    
    # Extract methods from uncovered ranges
    for start, end in uncovered_ranges:
        section = content[start:end]
        method_matches = re.finditer(method_pattern, section, re.MULTILINE)
        for match in method_matches:
            chunks.append(match.group(0))
    
    # Add imports and package declarations
    import_pattern = r'(package\s+[\w.]+;|import\s+[\w.*]+;)'
    imports = re.findall(import_pattern, content)
    if imports:
        chunks.append('\n'.join(imports))
    
    # If we have very few chunks, just return the whole file
    if len(chunks) <= 1:
        return [content]
        
    return chunks

def chunk_javascript_file(content):
    """Chunk a JavaScript/TypeScript file by functions, classes, and exports"""
    chunks = []
    
    # Match class definitions
    class_pattern = r'(class\s+\w+(?:\s+extends\s+\w+)?\s*\{(?:.|\n)*?)(^\})'
    class_matches = re.finditer(class_pattern, content, re.MULTILINE)
    
    class_positions = []
    for match in class_matches:
        chunks.append(match.group(0))
        class_positions.append((match.start(), match.end()))
    
    # Match function definitions (named functions and arrow functions with blocks)
    function_patterns = [
        r'(function\s+\w+\s*\([^)]*\)\s*\{(?:.|\n)*?)(^\})',
        r'(const\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{(?:.|\n)*?)(^\})',
        r'(let\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{(?:.|\n)*?)(^\})',
        r'(var\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{(?:.|\n)*?)(^\})',
        r'(export\s+(?:default\s+)?function\s+\w+\s*\([^)]*\)\s*\{(?:.|\n)*?)(^\})',
    ]
    
    # Find positions not covered by classes
    uncovered_ranges = [(0, len(content))]
    for start, end in sorted(class_positions):
        new_ranges = []
        for range_start, range_end in uncovered_ranges:
            if range_start < start:
                new_ranges.append((range_start, start))
            if end < range_end:
                new_ranges.append((end, range_end))
        uncovered_ranges = new_ranges
    
    # Extract functions from uncovered ranges
    for start, end in uncovered_ranges:
        section = content[start:end]
        for pattern in function_patterns:
            function_matches = re.finditer(pattern, section, re.MULTILINE)
            for match in function_matches:
                chunks.append(match.group(0))
    
    # Add imports
    import_pattern = r'(import\s+.*?;|require\(.*?\))'
    imports = re.findall(import_pattern, content)
    if imports:
        chunks.append('\n'.join(imports))
    
    # If we have very few chunks, just return the whole file
    if len(chunks) <= 1:
        return [content]
        
    return chunks

def chunk_by_lines(content, max_lines=100):
    """
    Simple chunking by line count, as a fallback
    
    Args:
        content (str): File content
        max_lines (int): Maximum lines per chunk
        
    Returns:
        list: List of chunks
    """
    lines = content.split('\n')
    chunks = []
    
    for i in range(0, len(lines), max_lines):
        chunk = '\n'.join(lines[i:i + max_lines])
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)
            
    return chunks
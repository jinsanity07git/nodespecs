import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Union, Tuple, Dict,Optional
from collections import defaultdict

class FileIndexer:
    def __init__(self):
        """Initialize the FileIndexer with an in-memory storage."""
        self.files: Dict[str, dict] = {}
        self.stats = {
            "total_files": 0,
            "total_size": 0,
            "extensions": defaultdict(int)
        }

    def index_directory(self, root_path: str) -> int:
        """
        Recursively index all files from the given root directory.
        Returns the number of files indexed.
        """
        count = 0
        # Reset statistics
        self.stats = {
            "total_files": 0,
            "total_size": 0,
            "extensions": defaultdict(int)
        }
        
        for dirpath, _, filenames in os.walk(root_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                filepath = Path(filepath).as_posix()
                try:
                    # Get file stats
                    stats = os.stat(filepath)
                    _, ext = os.path.splitext(filename)
                    ext = ext.lower()
                    
                    # Store file information
                    self.files[filepath] = {
                        'filepath': filepath,
                        'filename': filename,
                        'extension': ext,
                        'size': stats.st_size,
                        'last_modified': datetime.fromtimestamp(stats.st_mtime),
                        'indexed_at': datetime.now()
                    }
                    
                    # Update statistics
                    self.stats["total_files"] += 1
                    self.stats["total_size"] += stats.st_size
                    self.stats["extensions"][ext] += 1
                    
                    count += 1
                except (OSError, PermissionError) as e:
                    print(f"Error accessing {filepath}: {e}")
        
        return count

    def search(self, 
               pattern: str, 
               exact_match: bool = False, 
               extensions: List[str] = None,
               min_size: int = None,
               max_size: int = None) -> List[Tuple[str, str, int]]:
        """
        Search for files matching the given criteria.
        Returns list of tuples containing (filepath, filename, size).
        """
        results = []
        
        # Compile regex pattern if not exact match
        if not exact_match:
            try:
                regex = re.compile(pattern, re.IGNORECASE)
            except re.error:
                # If pattern is not a valid regex, treat it as literal
                regex = re.compile(re.escape(pattern), re.IGNORECASE)
        
        # Normalize extensions list
        if extensions:
            extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                         for ext in extensions]
        
        for file_info in self.files.values():
            # Check filename match
            if exact_match:
                if pattern.lower() != file_info['filename'].lower():
                    continue
            else:
                if not regex.search(file_info['filename']):
                    continue
            
            # Check extension
            if extensions and file_info['extension'] not in extensions:
                continue
            
            # Check size constraints
            if min_size is not None and file_info['size'] < min_size:
                continue
            if max_size is not None and file_info['size'] > max_size:
                continue
            
            results.append((
                file_info['filepath'],
                file_info['filename'],
                file_info['size']
            ))
        
        return sorted(results, key=lambda x: x[1])  # Sort by filename

    def get_statistics(self) -> dict:
        """Return statistics about the indexed files."""
        # Get top 5 extensions
        top_extensions = sorted(
            self.stats["extensions"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_files": self.stats["total_files"],
            "total_size": self.stats["total_size"],
            "unique_extensions": len(self.stats["extensions"]),
            "top_extensions": top_extensions
        }

    def export_to_sqlite(self, db_path: str) -> Tuple[bool, Optional[str]]:
        """
        Export the indexed files to a SQLite database.
        Returns a tuple of (success: bool, error_message: Optional[str])
        """
        try:
            import sqlite3
        except ImportError:
            return False, "SQLite3 module not available. Please check your Python installation."

        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Create the files table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filepath TEXT NOT NULL UNIQUE,
                        filename TEXT NOT NULL,
                        extension TEXT,
                        size INTEGER,
                        last_modified TIMESTAMP,
                        indexed_at TIMESTAMP
                    )
                ''')
                
                # Create the statistics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS statistics (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')
                
                # Insert or update file records
                cursor.executemany('''
                    INSERT OR REPLACE INTO files 
                    (filepath, filename, extension, size, last_modified, indexed_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', [
                    (
                        info['filepath'],
                        info['filename'],
                        info['extension'],
                        info['size'],
                        info['last_modified'].isoformat(),
                        info['indexed_at'].isoformat()
                    )
                    for info in self.files.values()
                ])
                
                # Insert statistics
                stats = self.get_statistics()
                cursor.executemany('''
                    INSERT OR REPLACE INTO statistics (key, value)
                    VALUES (?, ?)
                ''', [
                    ('total_files', str(stats['total_files'])),
                    ('total_size', str(stats['total_size'])),
                    ('unique_extensions', str(stats['unique_extensions'])),
                    ('top_extensions', repr(stats['top_extensions']))
                ])
                
                conn.commit()
                return True, None
                
        except sqlite3.Error as e:
            return False, f"SQLite error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
# Example usage
if __name__ == "__main__":
    # Initialize the indexer
    indexer = FileIndexer()

    # Index a directory
    indexed_count = indexer.index_directory(r"C:/Projects")  # Use raw string for Windows paths
    print(f"Indexed {indexed_count} files")

    success, error = indexer.export_to_sqlite("file_index.db")
    if success:
        print("Successfully exported to SQLite database")
    else:
        print(f"Export failed: {error}")
    
    # from pprint import pprint
    # pprint(indexer.files)
    # # Search for files
    # results = indexer.search(
    #     pattern="document",
    #     exact_match=False,
    #     extensions=[".png",".md"],
    #     min_size=1  # 1KB
    # )
    
    # # Print results
    # for filepath, filename, size in results:
    #     print(f"Found: {filename} ({size:,} bytes) at {filepath}")
    
    # # Get statistics
    # stats = indexer.get_statistics()
    # print(f"\nIndexing Statistics:")
    # print(f"Total Files: {stats['total_files']:,}")
    # print(f"Total Size: {stats['total_size']:,} bytes")
    # print(f"Unique Extensions: {stats['unique_extensions']}")
    # print("\nTop Extensions:")
    # for ext, count in stats['top_extensions']:
    #     print(f"{ext or '(no extension)'}: {count:,} files")
import logging
from datetime import datetime, timedelta
from typing import List
from search_utils import Document as SearchDocument

# Configure logging
logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.documents: List[SearchDocument] = []
        self.last_updated = None
        self.max_documents = 100
    
    def add_documents(self, documents: List[SearchDocument]):
        """Add documents incrementally and prune old ones."""
        current_time = datetime.now()
        self.documents = [doc for doc in self.documents if current_time - doc.created_at < timedelta(hours=24)]
        self.documents.extend(documents)
        self.documents = sorted(self.documents, key=lambda x: (x.relevance_score, x.created_at), reverse=True)[:self.max_documents]
        self.last_updated = current_time
        logger.info(f"Added {len(documents)} documents to knowledge base for session {self.session_id}")
    
    def is_empty(self) -> bool:
        """Check if the knowledge base is empty."""
        return len(self.documents) == 0
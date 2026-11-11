"""Compatibilidad: nombres que antes vivían aquí y que usa el RAG híbrido (``model/rag``).

La búsqueda por palabras pasó a ``keyword_search`` y la lectura de Gold a ``knowledge``. Para código
nuevo, importe desde esos módulos.
"""

from sb_asistente.model.llm.keyword_search import STOPWORDS, normalize_words, score, select_context
from sb_asistente.model.llm.knowledge import channels_block, load_chunks

__all__ = ["STOPWORDS", "channels_block", "load_chunks", "normalize_words", "score", "select_context"]

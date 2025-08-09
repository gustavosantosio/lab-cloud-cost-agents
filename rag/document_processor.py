"""
Processador de Documentos RAG
Sistema completo para processamento de documentos PDF do Google Cloud Storage
"""
import os
import sys
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hashlib
import pickle
from pathlib import Path

from google.cloud import storage
from google.oauth2 import service_account
from google.auth import default
import PyPDF2
import io
import openai
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import faiss
import tiktoken

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.project_config import config
from agents.base.logger import AgentLogger

class DocumentProcessor:
    """
    Processador de documentos para sistema RAG
    """
    
    def __init__(self):
        self.logger = AgentLogger("DocumentProcessor")
        self.storage_client = None
        self.bucket_name = "lab-rag-files-bucket"
        self.embeddings_model = None
        self.tokenizer = None
        self.vector_index = None
        self.document_metadata = {}
        self.chunk_metadata = {}
        self.cache_dir = Path("./rag_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self._initialize_components()
    
    def _initialize_components(self):
        """Inicializa componentes do processador"""
        try:
            # Inicializar cliente do Google Cloud Storage
            if config.gcp.credentials_path and os.path.exists(config.gcp.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    config.gcp.credentials_path
                )
            else:
                credentials, _ = default()
            
            self.storage_client = storage.Client(
                credentials=credentials,
                project=config.gcp.project_id
            )
            
            # Inicializar modelo de embeddings
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Inicializar tokenizer para contagem de tokens
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            
            # Configurar OpenAI
            openai.api_key = os.getenv('OPENAI_API_KEY')
            openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
            
            # Carregar cache se existir
            self._load_cache()
            
            self.logger.info("Processador de documentos inicializado", {
                "bucket": self.bucket_name,
                "project_id": config.gcp.project_id,
                "embeddings_model": "all-MiniLM-L6-v2",
                "cached_documents": len(self.document_metadata)
            })
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização do processador: {str(e)}")
            self.storage_client = None
    
    def _load_cache(self):
        """Carrega cache de documentos processados"""
        try:
            metadata_file = self.cache_dir / "document_metadata.json"
            chunks_file = self.cache_dir / "chunk_metadata.json"
            index_file = self.cache_dir / "vector_index.faiss"
            
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self.document_metadata = json.load(f)
            
            if chunks_file.exists():
                with open(chunks_file, 'r', encoding='utf-8') as f:
                    self.chunk_metadata = json.load(f)
            
            if index_file.exists() and self.chunk_metadata:
                self.vector_index = faiss.read_index(str(index_file))
                self.logger.info(f"Cache carregado: {len(self.document_metadata)} documentos, {len(self.chunk_metadata)} chunks")
            
        except Exception as e:
            self.logger.warning(f"Erro ao carregar cache: {str(e)}")
            self.document_metadata = {}
            self.chunk_metadata = {}
            self.vector_index = None
    
    def _save_cache(self):
        """Salva cache de documentos processados"""
        try:
            metadata_file = self.cache_dir / "document_metadata.json"
            chunks_file = self.cache_dir / "chunk_metadata.json"
            index_file = self.cache_dir / "vector_index.faiss"
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.document_metadata, f, ensure_ascii=False, indent=2)
            
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(self.chunk_metadata, f, ensure_ascii=False, indent=2)
            
            if self.vector_index:
                faiss.write_index(self.vector_index, str(index_file))
            
            self.logger.debug("Cache salvo com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar cache: {str(e)}")
    
    def list_documents(self) -> Dict[str, Any]:
        """Lista documentos PDF disponíveis no bucket"""
        try:
            if not self.storage_client:
                return {"error": "Storage não conectado"}
            
            bucket = self.storage_client.bucket(self.bucket_name)
            blobs = bucket.list_blobs()
            
            documents = []
            for blob in blobs:
                if blob.name.lower().endswith('.pdf'):
                    # Verificar se documento já foi processado
                    is_processed = blob.name in self.document_metadata
                    
                    doc_info = {
                        'name': blob.name,
                        'size': blob.size,
                        'created': blob.time_created.isoformat() if blob.time_created else None,
                        'updated': blob.updated.isoformat() if blob.updated else None,
                        'content_type': blob.content_type,
                        'md5_hash': blob.md5_hash,
                        'processed': is_processed
                    }
                    
                    if is_processed:
                        metadata = self.document_metadata[blob.name]
                        doc_info.update({
                            'chunks_count': metadata.get('chunks_count', 0),
                            'processed_at': metadata.get('processed_at'),
                            'total_tokens': metadata.get('total_tokens', 0)
                        })
                    
                    documents.append(doc_info)
            
            self.logger.info("Documentos PDF listados", {
                "bucket": self.bucket_name,
                "total_documents": len(documents),
                "processed_documents": sum(1 for d in documents if d['processed'])
            })
            
            return {
                "success": True,
                "bucket": self.bucket_name,
                "documents": documents,
                "total_count": len(documents),
                "processed_count": sum(1 for d in documents if d['processed']),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao listar documentos: {str(e)}")
            return {"error": str(e)}
    
    def extract_text_from_pdf(self, document_name: str) -> Dict[str, Any]:
        """Extrai texto de um documento PDF"""
        try:
            if not self.storage_client:
                return {"error": "Storage não conectado"}
            
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(document_name)
            
            if not blob.exists():
                return {"error": f"Documento {document_name} não encontrado"}
            
            # Baixar e extrair texto do PDF
            pdf_content = blob.download_as_bytes()
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            
            extracted_text = ""
            page_texts = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():  # Apenas páginas com conteúdo
                        page_texts.append({
                            "page_number": page_num + 1,
                            "text": page_text,
                            "char_count": len(page_text),
                            "token_count": len(self.tokenizer.encode(page_text))
                        })
                        extracted_text += f"\n--- Página {page_num + 1} ---\n{page_text}\n"
                except Exception as e:
                    self.logger.warning(f"Erro ao extrair página {page_num + 1}: {str(e)}")
                    continue
            
            # Gerar hash do conteúdo para cache
            content_hash = hashlib.md5(extracted_text.encode()).hexdigest()
            total_tokens = len(self.tokenizer.encode(extracted_text))
            
            self.logger.info("Texto extraído do documento", {
                "document": document_name,
                "pages_count": len(page_texts),
                "total_chars": len(extracted_text),
                "total_tokens": total_tokens,
                "content_hash": content_hash
            })
            
            return {
                "success": True,
                "document_name": document_name,
                "pages_count": len(page_texts),
                "total_characters": len(extracted_text),
                "total_tokens": total_tokens,
                "content_hash": content_hash,
                "extracted_text": extracted_text,
                "pages": page_texts,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair texto: {str(e)}")
            return {"error": str(e)}
    
    def chunk_document(
        self,
        document_name: str,
        chunk_size: int = 1000,
        overlap: int = 200,
        force_rechunk: bool = False
    ) -> Dict[str, Any]:
        """
        Divide documento em chunks para processamento RAG
        
        Args:
            document_name: Nome do documento
            chunk_size: Tamanho do chunk em tokens
            overlap: Sobreposição entre chunks em tokens
            force_rechunk: Forçar re-chunking mesmo se já processado
        """
        try:
            # Verificar se já foi processado
            if not force_rechunk and document_name in self.document_metadata:
                metadata = self.document_metadata[document_name]
                if metadata.get('chunk_size') == chunk_size and metadata.get('overlap') == overlap:
                    self.logger.info(f"Documento {document_name} já foi processado com os mesmos parâmetros")
                    return {
                        "success": True,
                        "document_name": document_name,
                        "chunks_count": metadata['chunks_count'],
                        "from_cache": True
                    }
            
            # Extrair texto do documento
            text_result = self.extract_text_from_pdf(document_name)
            if not text_result.get("success"):
                return text_result
            
            full_text = text_result["extracted_text"]
            
            # Dividir em chunks baseado em tokens
            chunks = self._create_chunks_by_tokens(full_text, chunk_size, overlap)
            
            # Armazenar metadados
            self.document_metadata[document_name] = {
                "processed_at": datetime.now().isoformat(),
                "chunks_count": len(chunks),
                "chunk_size": chunk_size,
                "overlap": overlap,
                "total_tokens": text_result["total_tokens"],
                "content_hash": text_result["content_hash"]
            }
            
            # Armazenar chunks com IDs únicos
            chunk_ids = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_name}:chunk_{i}"
                chunk_ids.append(chunk_id)
                
                self.chunk_metadata[chunk_id] = {
                    "document_name": document_name,
                    "chunk_index": i,
                    "text": chunk["text"],
                    "token_count": chunk["token_count"],
                    "start_position": chunk["start_position"],
                    "end_position": chunk["end_position"]
                }
            
            # Salvar cache
            self._save_cache()
            
            self.logger.info("Documento dividido em chunks", {
                "document": document_name,
                "chunks_count": len(chunks),
                "chunk_size": chunk_size,
                "overlap": overlap
            })
            
            return {
                "success": True,
                "document_name": document_name,
                "chunks_count": len(chunks),
                "chunk_size": chunk_size,
                "overlap": overlap,
                "chunk_ids": chunk_ids,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao dividir documento: {str(e)}")
            return {"error": str(e)}
    
    def _create_chunks_by_tokens(
        self,
        text: str,
        chunk_size: int,
        overlap: int
    ) -> List[Dict[str, Any]]:
        """Cria chunks baseado em contagem de tokens"""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        start = 0
        chunk_id = 0
        
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            # Tentar quebrar em uma frase completa
            if end < len(tokens):
                # Procurar por pontos finais próximos ao final do chunk
                sentences = chunk_text.split('.')
                if len(sentences) > 1:
                    # Manter todas as frases completas exceto a última incompleta
                    chunk_text = '.'.join(sentences[:-1]) + '.'
                    chunk_tokens = self.tokenizer.encode(chunk_text)
            
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text.strip(),
                "token_count": len(chunk_tokens),
                "start_position": start,
                "end_position": start + len(chunk_tokens)
            })
            
            chunk_id += 1
            start = max(start + chunk_size - overlap, start + 1)
        
        return chunks
    
    def generate_embeddings(self, document_name: str) -> Dict[str, Any]:
        """Gera embeddings para chunks do documento"""
        try:
            if not self.embeddings_model:
                return {"error": "Modelo de embeddings não carregado"}
            
            # Verificar se documento foi processado
            if document_name not in self.document_metadata:
                chunk_result = self.chunk_document(document_name)
                if not chunk_result.get("success"):
                    return chunk_result
            
            # Obter chunks do documento
            doc_chunks = [
                chunk_id for chunk_id in self.chunk_metadata.keys()
                if chunk_id.startswith(f"{document_name}:")
            ]
            
            if not doc_chunks:
                return {"error": f"Nenhum chunk encontrado para {document_name}"}
            
            # Extrair textos dos chunks
            chunk_texts = [self.chunk_metadata[chunk_id]["text"] for chunk_id in doc_chunks]
            
            # Gerar embeddings
            embeddings = self.embeddings_model.encode(chunk_texts, show_progress_bar=True)
            
            # Atualizar índice vetorial
            self._update_vector_index(doc_chunks, embeddings)
            
            # Atualizar metadados
            self.document_metadata[document_name]["embeddings_generated"] = True
            self.document_metadata[document_name]["embeddings_generated_at"] = datetime.now().isoformat()
            
            # Salvar cache
            self._save_cache()
            
            self.logger.info("Embeddings gerados", {
                "document": document_name,
                "chunks_count": len(doc_chunks),
                "embedding_dimension": embeddings.shape[1]
            })
            
            return {
                "success": True,
                "document_name": document_name,
                "chunks_count": len(doc_chunks),
                "embedding_dimension": embeddings.shape[1],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar embeddings: {str(e)}")
            return {"error": str(e)}
    
    def _update_vector_index(self, chunk_ids: List[str], embeddings: np.ndarray):
        """Atualiza índice vetorial FAISS"""
        try:
            if self.vector_index is None:
                # Criar novo índice
                dimension = embeddings.shape[1]
                self.vector_index = faiss.IndexFlatIP(dimension)  # Inner Product para cosine similarity
                self.chunk_id_mapping = []
            
            # Normalizar embeddings para cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Adicionar ao índice
            self.vector_index.add(embeddings)
            
            # Manter mapeamento de IDs
            if not hasattr(self, 'chunk_id_mapping'):
                self.chunk_id_mapping = []
            
            self.chunk_id_mapping.extend(chunk_ids)
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar índice vetorial: {str(e)}")
    
    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        document_filter: Optional[str] = None,
        similarity_threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        Realiza busca semântica nos documentos
        
        Args:
            query: Consulta de busca
            top_k: Número de resultados
            document_filter: Filtrar por documento específico
            similarity_threshold: Limiar de similaridade
        """
        try:
            if not self.embeddings_model or not self.vector_index:
                return {"error": "Sistema de busca não inicializado"}
            
            # Gerar embedding da query
            query_embedding = self.embeddings_model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Buscar no índice
            scores, indices = self.vector_index.search(query_embedding, min(top_k * 2, self.vector_index.ntotal))
            
            # Processar resultados
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # Índice inválido
                    continue
                
                chunk_id = self.chunk_id_mapping[idx]
                chunk_data = self.chunk_metadata[chunk_id]
                
                # Aplicar filtro de documento se especificado
                if document_filter and not chunk_id.startswith(f"{document_filter}:"):
                    continue
                
                # Aplicar limiar de similaridade
                if score < similarity_threshold:
                    continue
                
                results.append({
                    "chunk_id": chunk_id,
                    "document_name": chunk_data["document_name"],
                    "chunk_index": chunk_data["chunk_index"],
                    "similarity_score": float(score),
                    "text": chunk_data["text"],
                    "token_count": chunk_data["token_count"]
                })
            
            # Ordenar por similaridade e limitar resultados
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            results = results[:top_k]
            
            self.logger.info("Busca semântica realizada", {
                "query": query[:100] + "..." if len(query) > 100 else query,
                "results_found": len(results),
                "top_similarity": results[0]["similarity_score"] if results else 0,
                "document_filter": document_filter
            })
            
            return {
                "success": True,
                "query": query,
                "results_count": len(results),
                "similarity_threshold": similarity_threshold,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro na busca semântica: {str(e)}")
            return {"error": str(e)}
    
    def generate_answer(
        self,
        question: str,
        context_documents: Optional[List[str]] = None,
        max_context_tokens: int = 3000,
        model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """
        Gera resposta baseada nos documentos usando RAG
        
        Args:
            question: Pergunta a ser respondida
            context_documents: Documentos específicos para contexto
            max_context_tokens: Tamanho máximo do contexto em tokens
            model: Modelo OpenAI a usar
        """
        try:
            # Realizar busca semântica
            search_params = {
                "query": question,
                "top_k": 10,
                "similarity_threshold": 0.2
            }
            
            if context_documents:
                # Buscar em cada documento especificado
                all_results = []
                for doc in context_documents:
                    search_result = self.semantic_search(document_filter=doc, **search_params)
                    if search_result.get("success"):
                        all_results.extend(search_result["results"])
                
                # Ordenar todos os resultados por similaridade
                all_results.sort(key=lambda x: x["similarity_score"], reverse=True)
                search_results = all_results[:10]
            else:
                search_result = self.semantic_search(**search_params)
                if not search_result.get("success"):
                    return {"error": "Falha na busca semântica"}
                search_results = search_result["results"]
            
            if not search_results:
                return {"error": "Nenhum contexto relevante encontrado"}
            
            # Construir contexto respeitando limite de tokens
            context_chunks = []
            context_tokens = 0
            
            for result in search_results:
                chunk_tokens = result["token_count"]
                if context_tokens + chunk_tokens <= max_context_tokens:
                    context_chunks.append(result)
                    context_tokens += chunk_tokens
                else:
                    break
            
            # Construir texto de contexto
            context_text = ""
            for chunk in context_chunks:
                context_text += f"\n[Documento: {chunk['document_name']}]\n{chunk['text']}\n"
            
            # Gerar resposta usando OpenAI
            try:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Você é um assistente especializado em análise de documentos jurídicos e regulamentações brasileiras. "
                                "Responda às perguntas baseando-se exclusivamente no contexto fornecido dos documentos. "
                                "Se a informação não estiver no contexto, diga claramente que não foi possível encontrar a informação nos documentos fornecidos. "
                                "Cite sempre as fontes (nomes dos documentos) quando possível. "
                                "Seja preciso e objetivo em suas respostas."
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Contexto dos documentos:\n{context_text}\n\nPergunta: {question}\n\nResposta:"
                        }
                    ],
                    max_tokens=1500,
                    temperature=0.3
                )
                
                answer = response.choices[0].message.content.strip()
                
            except Exception as openai_error:
                self.logger.warning(f"Erro OpenAI: {str(openai_error)}")
                # Fallback para resposta simples baseada em contexto
                answer = (
                    f"Baseado nos documentos analisados, encontrei as seguintes informações relevantes:\n\n"
                    f"{context_text[:1000]}..."
                )
            
            self.logger.info("Resposta RAG gerada", {
                "question": question[:100] + "..." if len(question) > 100 else question,
                "context_tokens": context_tokens,
                "sources_count": len(context_chunks),
                "answer_length": len(answer)
            })
            
            return {
                "success": True,
                "question": question,
                "answer": answer,
                "context_sources": [
                    {
                        "document": chunk["document_name"],
                        "similarity": chunk["similarity_score"],
                        "chunk_index": chunk["chunk_index"]
                    }
                    for chunk in context_chunks
                ],
                "context_tokens": context_tokens,
                "model_used": model,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar resposta: {str(e)}")
            return {"error": str(e)}
    
    def process_all_documents(self) -> Dict[str, Any]:
        """Processa todos os documentos PDF do bucket"""
        try:
            # Listar documentos
            docs_result = self.list_documents()
            if not docs_result.get("success"):
                return docs_result
            
            documents = docs_result["documents"]
            unprocessed_docs = [doc for doc in documents if not doc["processed"]]
            
            if not unprocessed_docs:
                self.logger.info("Todos os documentos já foram processados")
                return {
                    "success": True,
                    "message": "Todos os documentos já foram processados",
                    "total_documents": len(documents),
                    "processed_documents": len(documents)
                }
            
            processed_count = 0
            errors = []
            
            for doc in unprocessed_docs:
                try:
                    self.logger.info(f"Processando documento: {doc['name']}")
                    
                    # Chunking
                    chunk_result = self.chunk_document(doc["name"])
                    if not chunk_result.get("success"):
                        errors.append(f"{doc['name']}: {chunk_result.get('error')}")
                        continue
                    
                    # Embeddings
                    embed_result = self.generate_embeddings(doc["name"])
                    if embed_result.get("success"):
                        processed_count += 1
                        self.logger.info(f"Documento processado com sucesso: {doc['name']}")
                    else:
                        errors.append(f"{doc['name']}: {embed_result.get('error')}")
                
                except Exception as e:
                    errors.append(f"{doc['name']}: {str(e)}")
            
            self.logger.info("Processamento completo", {
                "total_documents": len(documents),
                "unprocessed_documents": len(unprocessed_docs),
                "processed_successfully": processed_count,
                "errors_count": len(errors)
            })
            
            return {
                "success": True,
                "total_documents": len(documents),
                "unprocessed_documents": len(unprocessed_docs),
                "processed_successfully": processed_count,
                "failed_documents": len(errors),
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro no processamento completo: {str(e)}")
            return {"error": str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status do sistema RAG"""
        try:
            total_documents = len(self.document_metadata)
            total_chunks = len(self.chunk_metadata)
            
            # Estatísticas por documento
            doc_stats = []
            for doc_name, metadata in self.document_metadata.items():
                doc_stats.append({
                    "name": doc_name,
                    "chunks_count": metadata.get("chunks_count", 0),
                    "total_tokens": metadata.get("total_tokens", 0),
                    "processed_at": metadata.get("processed_at"),
                    "embeddings_generated": metadata.get("embeddings_generated", False)
                })
            
            return {
                "success": True,
                "system_status": {
                    "storage_connected": self.storage_client is not None,
                    "embeddings_model_loaded": self.embeddings_model is not None,
                    "vector_index_ready": self.vector_index is not None,
                    "bucket_name": self.bucket_name,
                    "total_documents": total_documents,
                    "total_chunks": total_chunks,
                    "cache_directory": str(self.cache_dir),
                    "documents": doc_stats
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}

def main():
    """Função principal para teste do processador"""
    processor = DocumentProcessor()
    
    print("=== Sistema RAG - Processador de Documentos ===")
    
    # Listar documentos
    print("\n1. Listando documentos...")
    docs_result = processor.list_documents()
    if docs_result.get("success"):
        print(f"✅ Encontrados {docs_result['total_count']} documentos")
        print(f"📊 Processados: {docs_result['processed_count']}")
    else:
        print(f"❌ Erro: {docs_result.get('error')}")
        return
    
    # Processar todos os documentos
    print("\n2. Processando documentos...")
    process_result = processor.process_all_documents()
    if process_result.get("success"):
        print(f"✅ Processamento concluído")
        print(f"📈 Processados com sucesso: {process_result['processed_successfully']}")
        if process_result['errors']:
            print(f"⚠️ Erros: {len(process_result['errors'])}")
    else:
        print(f"❌ Erro: {process_result.get('error')}")
    
    # Teste de busca semântica
    print("\n3. Testando busca semântica...")
    search_result = processor.semantic_search(
        "LGPD proteção de dados pessoais",
        top_k=3
    )
    if search_result.get("success"):
        print(f"✅ Encontrados {search_result['results_count']} resultados")
        for result in search_result["results"][:2]:
            print(f"📄 {result['document_name']} (similaridade: {result['similarity_score']:.3f})")
    else:
        print(f"❌ Erro na busca: {search_result.get('error')}")
    
    # Status do sistema
    print("\n4. Status do sistema...")
    status = processor.get_system_status()
    if status.get("success"):
        sys_status = status["system_status"]
        print(f"✅ Sistema operacional")
        print(f"📚 Documentos: {sys_status['total_documents']}")
        print(f"📝 Chunks: {sys_status['total_chunks']}")
        print(f"🔍 Índice vetorial: {'✅' if sys_status['vector_index_ready'] else '❌'}")
    else:
        print(f"❌ Erro: {status.get('error')}")

if __name__ == "__main__":
    main()


"""
Servidor MCP para RAG - Model Context Protocol
Responsável por conectar ao sistema RAG com documentos PDF do Google Cloud Storage
"""
import os
import sys
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
from google.cloud import storage
from google.oauth2 import service_account
from google.auth import default
import PyPDF2
import io
import openai
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from mcp import MCPServer, Tool, Resource
from config.project_config import config
from agents.base.logger import AgentLogger

class RAGMCPServer:
    """
    Servidor MCP para RAG - Fornece acesso ao sistema RAG com documentos jurídicos
    """
    
    def __init__(self):
        self.logger = AgentLogger("RAGMCPServer")
        self.server = MCPServer("rag-documents-api")
        self.storage_client = None
        self.bucket_name = "lab-rag-files-bucket"
        self.embeddings_model = None
        self.document_embeddings = {}
        self.document_chunks = {}
        self._initialize_connections()
        self._register_tools()
        self._register_resources()
    
    def _initialize_connections(self):
        """Inicializa conexões com GCP e modelos"""
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
            
            # Configurar OpenAI
            openai.api_key = os.getenv('OPENAI_API_KEY')
            openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
            
            self.logger.info("RAG MCP Server conectado", {
                "bucket": self.bucket_name,
                "project_id": config.gcp.project_id,
                "embeddings_model": "all-MiniLM-L6-v2"
            })
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização RAG MCP: {str(e)}")
            self.storage_client = None
    
    def _register_tools(self):
        """Registra ferramentas MCP para RAG"""
        
        @self.server.tool("list_documents")
        async def list_documents() -> Dict[str, Any]:
            """
            Lista documentos PDF disponíveis no bucket
            """
            try:
                if not self.storage_client:
                    return {"error": "Storage não conectado"}
                
                bucket = self.storage_client.bucket(self.bucket_name)
                blobs = bucket.list_blobs()
                
                documents = []
                for blob in blobs:
                    if blob.name.lower().endswith('.pdf'):
                        documents.append({
                            'name': blob.name,
                            'size': blob.size,
                            'created': blob.time_created.isoformat() if blob.time_created else None,
                            'updated': blob.updated.isoformat() if blob.updated else None,
                            'content_type': blob.content_type,
                            'md5_hash': blob.md5_hash
                        })
                
                self.logger.info("Documentos PDF listados", {
                    "bucket": self.bucket_name,
                    "documents_count": len(documents)
                })
                
                return {
                    "success": True,
                    "bucket": self.bucket_name,
                    "documents": documents,
                    "total_count": len(documents),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao listar documentos: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("extract_document_text")
        async def extract_document_text(document_name: str) -> Dict[str, Any]:
            """
            Extrai texto de um documento PDF
            
            Args:
                document_name: Nome do documento no bucket
            """
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
                    page_text = page.extract_text()
                    page_texts.append({
                        "page_number": page_num + 1,
                        "text": page_text,
                        "char_count": len(page_text)
                    })
                    extracted_text += f"\n--- Página {page_num + 1} ---\n{page_text}\n"
                
                # Gerar hash do conteúdo para cache
                content_hash = hashlib.md5(extracted_text.encode()).hexdigest()
                
                self.logger.info("Texto extraído do documento", {
                    "document": document_name,
                    "pages_count": len(page_texts),
                    "total_chars": len(extracted_text),
                    "content_hash": content_hash
                })
                
                return {
                    "success": True,
                    "document_name": document_name,
                    "pages_count": len(page_texts),
                    "total_characters": len(extracted_text),
                    "content_hash": content_hash,
                    "extracted_text": extracted_text,
                    "pages": page_texts,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao extrair texto: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("chunk_document")
        async def chunk_document(
            document_name: str,
            chunk_size: int = 1000,
            overlap: int = 200
        ) -> Dict[str, Any]:
            """
            Divide documento em chunks para processamento RAG
            
            Args:
                document_name: Nome do documento
                chunk_size: Tamanho do chunk em caracteres
                overlap: Sobreposição entre chunks
            """
            try:
                # Extrair texto do documento
                text_result = await self.server.tools["extract_document_text"](document_name)
                if not text_result.get("success"):
                    return text_result
                
                full_text = text_result["extracted_text"]
                
                # Dividir em chunks
                chunks = []
                start = 0
                chunk_id = 0
                
                while start < len(full_text):
                    end = start + chunk_size
                    chunk_text = full_text[start:end]
                    
                    # Tentar quebrar em uma frase completa
                    if end < len(full_text):
                        last_period = chunk_text.rfind('.')
                        last_newline = chunk_text.rfind('\n')
                        break_point = max(last_period, last_newline)
                        
                        if break_point > start + chunk_size * 0.7:  # Pelo menos 70% do chunk
                            chunk_text = chunk_text[:break_point + 1]
                            end = start + len(chunk_text)
                    
                    chunks.append({
                        "chunk_id": chunk_id,
                        "start_position": start,
                        "end_position": end,
                        "text": chunk_text.strip(),
                        "char_count": len(chunk_text.strip())
                    })
                    
                    chunk_id += 1
                    start = end - overlap
                
                # Armazenar chunks em cache
                self.document_chunks[document_name] = chunks
                
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
                    "chunks": chunks,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao dividir documento: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("generate_embeddings")
        async def generate_embeddings(document_name: str) -> Dict[str, Any]:
            """
            Gera embeddings para chunks do documento
            
            Args:
                document_name: Nome do documento
            """
            try:
                if not self.embeddings_model:
                    return {"error": "Modelo de embeddings não carregado"}
                
                # Verificar se chunks existem
                if document_name not in self.document_chunks:
                    chunk_result = await self.server.tools["chunk_document"](document_name)
                    if not chunk_result.get("success"):
                        return chunk_result
                
                chunks = self.document_chunks[document_name]
                chunk_texts = [chunk["text"] for chunk in chunks]
                
                # Gerar embeddings
                embeddings = self.embeddings_model.encode(chunk_texts)
                
                # Armazenar embeddings
                self.document_embeddings[document_name] = {
                    "embeddings": embeddings,
                    "chunks": chunks,
                    "generated_at": datetime.now().isoformat()
                }
                
                self.logger.info("Embeddings gerados", {
                    "document": document_name,
                    "chunks_count": len(chunks),
                    "embedding_dimension": embeddings.shape[1]
                })
                
                return {
                    "success": True,
                    "document_name": document_name,
                    "chunks_count": len(chunks),
                    "embedding_dimension": embeddings.shape[1],
                    "embeddings_generated": True,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao gerar embeddings: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("semantic_search")
        async def semantic_search(
            query: str,
            document_name: Optional[str] = None,
            top_k: int = 5,
            similarity_threshold: float = 0.3
        ) -> Dict[str, Any]:
            """
            Realiza busca semântica nos documentos
            
            Args:
                query: Consulta de busca
                document_name: Documento específico (opcional)
                top_k: Número de resultados
                similarity_threshold: Limiar de similaridade
            """
            try:
                if not self.embeddings_model:
                    return {"error": "Modelo de embeddings não carregado"}
                
                # Gerar embedding da query
                query_embedding = self.embeddings_model.encode([query])
                
                search_results = []
                documents_to_search = [document_name] if document_name else list(self.document_embeddings.keys())
                
                for doc_name in documents_to_search:
                    if doc_name not in self.document_embeddings:
                        # Tentar gerar embeddings se não existirem
                        embed_result = await self.server.tools["generate_embeddings"](doc_name)
                        if not embed_result.get("success"):
                            continue
                    
                    doc_data = self.document_embeddings[doc_name]
                    doc_embeddings = doc_data["embeddings"]
                    doc_chunks = doc_data["chunks"]
                    
                    # Calcular similaridades
                    similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
                    
                    # Encontrar chunks mais similares
                    for i, similarity in enumerate(similarities):
                        if similarity >= similarity_threshold:
                            search_results.append({
                                "document_name": doc_name,
                                "chunk_id": doc_chunks[i]["chunk_id"],
                                "similarity_score": float(similarity),
                                "text": doc_chunks[i]["text"],
                                "start_position": doc_chunks[i]["start_position"],
                                "char_count": doc_chunks[i]["char_count"]
                            })
                
                # Ordenar por similaridade
                search_results.sort(key=lambda x: x["similarity_score"], reverse=True)
                search_results = search_results[:top_k]
                
                self.logger.info("Busca semântica realizada", {
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "documents_searched": len(documents_to_search),
                    "results_found": len(search_results),
                    "top_similarity": search_results[0]["similarity_score"] if search_results else 0
                })
                
                return {
                    "success": True,
                    "query": query,
                    "documents_searched": documents_to_search,
                    "results_count": len(search_results),
                    "similarity_threshold": similarity_threshold,
                    "results": search_results,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro na busca semântica: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("generate_answer")
        async def generate_answer(
            question: str,
            context_documents: Optional[List[str]] = None,
            max_context_length: int = 4000
        ) -> Dict[str, Any]:
            """
            Gera resposta baseada nos documentos usando RAG
            
            Args:
                question: Pergunta a ser respondida
                context_documents: Documentos específicos para contexto
                max_context_length: Tamanho máximo do contexto
            """
            try:
                # Realizar busca semântica
                search_result = await self.server.tools["semantic_search"](
                    question,
                    document_name=context_documents[0] if context_documents else None,
                    top_k=10,
                    similarity_threshold=0.2
                )
                
                if not search_result.get("success") or not search_result["results"]:
                    return {"error": "Nenhum contexto relevante encontrado"}
                
                # Construir contexto
                context_chunks = search_result["results"]
                context_text = ""
                
                for chunk in context_chunks:
                    chunk_text = f"\n[Documento: {chunk['document_name']}]\n{chunk['text']}\n"
                    if len(context_text + chunk_text) <= max_context_length:
                        context_text += chunk_text
                    else:
                        break
                
                # Gerar resposta usando OpenAI
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {
                                "role": "system",
                                "content": "Você é um assistente especializado em análise de documentos jurídicos e regulamentações. "
                                          "Responda às perguntas baseando-se exclusivamente no contexto fornecido. "
                                          "Se a informação não estiver no contexto, diga que não foi possível encontrar a informação nos documentos fornecidos."
                            },
                            {
                                "role": "user",
                                "content": f"Contexto dos documentos:\n{context_text}\n\nPergunta: {question}\n\nResposta:"
                            }
                        ],
                        max_tokens=1000,
                        temperature=0.3
                    )
                    
                    answer = response.choices[0].message.content.strip()
                    
                except Exception as openai_error:
                    # Fallback para resposta simples baseada em contexto
                    answer = f"Baseado nos documentos analisados, encontrei as seguintes informações relevantes:\n\n{context_text[:500]}..."
                
                self.logger.info("Resposta RAG gerada", {
                    "question": question[:100] + "..." if len(question) > 100 else question,
                    "context_length": len(context_text),
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
                            "chunk_id": chunk["chunk_id"]
                        }
                        for chunk in context_chunks
                    ],
                    "context_length": len(context_text),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao gerar resposta: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("index_all_documents")
        async def index_all_documents() -> Dict[str, Any]:
            """
            Indexa todos os documentos PDF do bucket
            """
            try:
                # Listar documentos
                docs_result = await self.server.tools["list_documents"]()
                if not docs_result.get("success"):
                    return docs_result
                
                documents = docs_result["documents"]
                indexed_count = 0
                errors = []
                
                for doc in documents:
                    try:
                        # Gerar embeddings para cada documento
                        embed_result = await self.server.tools["generate_embeddings"](doc["name"])
                        if embed_result.get("success"):
                            indexed_count += 1
                        else:
                            errors.append(f"{doc['name']}: {embed_result.get('error', 'Erro desconhecido')}")
                    
                    except Exception as e:
                        errors.append(f"{doc['name']}: {str(e)}")
                
                self.logger.info("Indexação completa", {
                    "total_documents": len(documents),
                    "indexed_successfully": indexed_count,
                    "errors_count": len(errors)
                })
                
                return {
                    "success": True,
                    "total_documents": len(documents),
                    "indexed_successfully": indexed_count,
                    "failed_documents": len(errors),
                    "errors": errors,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro na indexação: {str(e)}")
                return {"error": str(e)}
    
    def _register_resources(self):
        """Registra recursos MCP para RAG"""
        
        @self.server.resource("rag://documents/index")
        async def documents_index() -> Dict[str, Any]:
            """
            Recurso que fornece índice de documentos
            """
            try:
                docs_result = await self.server.tools["list_documents"]()
                
                if docs_result.get("success"):
                    indexed_docs = []
                    for doc_name in self.document_embeddings.keys():
                        doc_info = next((d for d in docs_result["documents"] if d["name"] == doc_name), None)
                        if doc_info:
                            indexed_docs.append({
                                **doc_info,
                                "indexed": True,
                                "chunks_count": len(self.document_embeddings[doc_name]["chunks"])
                            })
                    
                    return {
                        "resource_type": "documents_index",
                        "data": {
                            "total_documents": len(docs_result["documents"]),
                            "indexed_documents": len(indexed_docs),
                            "documents": indexed_docs
                        },
                        "last_updated": datetime.now().isoformat()
                    }
                
                return {"error": "Falha ao obter índice de documentos"}
                
            except Exception as e:
                return {"error": str(e)}
        
        @self.server.resource("rag://knowledge/summary")
        async def knowledge_summary() -> Dict[str, Any]:
            """
            Recurso que fornece resumo da base de conhecimento
            """
            try:
                total_chunks = sum(len(data["chunks"]) for data in self.document_embeddings.values())
                total_documents = len(self.document_embeddings)
                
                return {
                    "resource_type": "knowledge_summary",
                    "data": {
                        "indexed_documents": total_documents,
                        "total_chunks": total_chunks,
                        "embedding_model": "all-MiniLM-L6-v2",
                        "bucket_name": self.bucket_name,
                        "last_indexed": max(
                            [data["generated_at"] for data in self.document_embeddings.values()],
                            default=None
                        )
                    },
                    "last_updated": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {"error": str(e)}
    
    async def start_server(self, host: str = "0.0.0.0", port: int = None):
        """Inicia o servidor MCP"""
        server_port = port or config.mcp.rag_port
        
        try:
            self.logger.info(f"Iniciando RAG MCP Server em {host}:{server_port}")
            await self.server.start(host=host, port=server_port)
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar RAG MCP Server: {str(e)}")
            raise
    
    def get_server_info(self) -> Dict[str, Any]:
        """Retorna informações do servidor"""
        return {
            "name": "RAG MCP Server",
            "version": "1.0.0",
            "description": "Servidor MCP para sistema RAG com documentos jurídicos",
            "port": config.mcp.rag_port,
            "tools_count": len(self.server.tools),
            "resources_count": len(self.server.resources),
            "bucket_name": self.bucket_name,
            "indexed_documents": len(self.document_embeddings),
            "storage_connected": self.storage_client is not None
        }

async def main():
    """Função principal para executar o servidor"""
    rag_mcp = RAGMCPServer()
    
    try:
        await rag_mcp.start_server()
    except KeyboardInterrupt:
        print("Servidor RAG MCP interrompido pelo usuário")
    except Exception as e:
        print(f"Erro no servidor RAG MCP: {e}")

if __name__ == "__main__":
    asyncio.run(main())


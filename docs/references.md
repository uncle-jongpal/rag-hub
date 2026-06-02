# 참고문헌 (References)

본 레포에서 구현된 기법과 도구의 원논문/공식 구현/관련 자료를 한 곳에 정리합니다. 각 항목은 사용 위치(레포 내 어디서 참조되는지)와 함께 적었습니다.

## 1. RAG 원형

1. Lewis, P., et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS.
   1) 논문 - https://arxiv.org/abs/2005.11401
   2) 사용 위치 - docs/overview.md (RAG 개요)

## 2. 검색 / 인덱싱 기법

### 2-1. BM25

1. Robertson, S., & Walker, S. (1994). "Some simple effective approximations to the 2-Poisson model for probabilistic weighted retrieval." SIGIR.
2. Robertson, S., & Zaragoza, H. (2009). "The Probabilistic Relevance Framework: BM25 and Beyond."
   1) 논문 - https://dl.acm.org/doi/10.1561/1500000019
   2) 사용 위치 - techniques/02-hybrid-search

### 2-2. Reciprocal Rank Fusion (RRF)

1. Cormack, G., Clarke, C., & Buettcher, S. (2009). "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods." SIGIR.
   1) 논문 - https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
   2) 사용 위치 - techniques/02-hybrid-search, techniques/05-multi-query, techniques/13-adaptive-rag

### 2-3. BGE-M3 임베딩

1. Chen, J., et al. (2024). "BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation."
   1) 논문 - https://arxiv.org/abs/2402.03216
   2) 모델 - https://huggingface.co/BAAI/bge-m3
   3) 사용 위치 - common/embeddings.py (모든 기법의 기본 임베딩)

### 2-4. BGE Reranker

1. Xiao, S., et al. (2023). "C-Pack: Packed Resources For General Chinese Embeddings."
   1) 모델 - https://huggingface.co/BAAI/bge-reranker-v2-m3
   2) 사용 위치 - techniques/03-reranking

### 2-5. Cross-encoder vs Bi-encoder

1. Reimers, N., & Gurevych, I. (2019). "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks." EMNLP.
   1) 논문 - https://arxiv.org/abs/1908.10084
   2) 사용 위치 - techniques/03-reranking (개념 설명)

## 3. 쿼리 처리 기법

### 3-1. HyDE (Hypothetical Document Embeddings)

1. Gao, L., Ma, X., Lin, J., & Callan, J. (2022). "Precise Zero-Shot Dense Retrieval without Relevance Labels."
   1) 논문 - https://arxiv.org/abs/2212.10496
   2) 사용 위치 - techniques/04-hyde

### 3-2. Multi-query / RAG-Fusion

1. Raudaschl, A. (2023). "Forget RAG, the Future is RAG-Fusion."
   1) 블로그 - https://towardsdatascience.com/forget-rag-the-future-is-rag-fusion-1147298d8ad1
2. LangChain MultiQueryRetriever 문서
   1) 문서 - https://python.langchain.com/docs/how_to/MultiQueryRetriever/
   2) 사용 위치 - techniques/05-multi-query

### 3-3. Step-back Prompting

1. Zheng, H., et al. (2023). "Take a Step Back: Evoking Reasoning via Abstraction in Large Language Models."
   1) 논문 - https://arxiv.org/abs/2310.06117
   2) 사용 위치 - techniques/05-multi-query (변형 가능성에 언급)

## 4. 청킹 / 컨텍스트 보강

### 4-1. Parent-Child Chunking

1. LangChain ParentDocumentRetriever
   1) 문서 - https://python.langchain.com/docs/how_to/parent_document_retriever/
2. LlamaIndex HierarchicalNodeParser
   1) 문서 - https://docs.llamaindex.ai/en/stable/api_reference/node_parsers/hierarchical/
   2) 사용 위치 - techniques/06-parent-child, common/chunkers.py

### 4-2. Contextual Retrieval

1. Anthropic. (2024년 9월). "Introducing Contextual Retrieval."
   1) 발표 - https://www.anthropic.com/news/contextual-retrieval
   2) 사용 위치 - techniques/07-contextual-retrieval

### 4-3. Prompt Caching (관련)

1. Anthropic Claude prompt caching 문서
   1) 문서 - https://docs.anthropic.com/claude/docs/prompt-caching
2. OpenAI prefix caching 문서
   1) 문서 - https://platform.openai.com/docs/guides/prompt-caching
   2) 사용 위치 - techniques/07-contextual-retrieval (비용 최적화 섹션)

## 5. 자가 교정 기법

### 5-1. Self-RAG

1. Asai, A., Wu, Z., Wang, Y., Sil, A., & Hajishirzi, H. (2023). "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection."
   1) 논문 - https://arxiv.org/abs/2310.11511
   2) 공식 리포 - https://github.com/AkariAsai/self-rag
   3) 사용 위치 - techniques/08-self-rag (단순화 버전 구현)

### 5-2. CRAG (Corrective RAG)

1. Yan, S., Gu, J., Zhu, Y., & Ling, Z. (2024). "Corrective Retrieval Augmented Generation."
   1) 논문 - https://arxiv.org/abs/2401.15884
   2) 공식 리포 - https://github.com/HuskyInSalt/CRAG
   3) 사용 위치 - techniques/09-crag (단순화 버전 구현)

## 6. 구조 인덱싱

### 6-1. GraphRAG

1. Edge, D., et al. (2024). "From Local to Global: A Graph RAG Approach to Query-Focused Summarization." Microsoft Research.
   1) 논문 - https://arxiv.org/abs/2404.16130
   2) 공식 리포 - https://github.com/microsoft/graphrag
   3) 발표 블로그 - https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/
   4) 사용 위치 - techniques/10-graphrag (미니멀 버전 구현)

### 6-2. LightRAG (GraphRAG 변종)

1. Guo, Z., et al. (2024). "LightRAG: Simple and Fast Retrieval-Augmented Generation."
   1) 논문 - https://arxiv.org/abs/2410.05779
   2) 공식 리포 - https://github.com/HKUDS/LightRAG
   3) 사용 위치 - techniques/10-graphrag README의 변형 섹션에 언급

### 6-3. RAPTOR

1. Sarthi, P., et al. (2024). "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval."
   1) 논문 - https://arxiv.org/abs/2401.18059
   2) 공식 리포 - https://github.com/parthsarthi03/raptor
   3) 사용 위치 - techniques/11-raptor (단순화 버전 구현)

## 7. 에이전트형

### 7-1. ReAct

1. Yao, S., et al. (2022). "ReAct: Synergizing Reasoning and Acting in Language Models."
   1) 논문 - https://arxiv.org/abs/2210.03629
   2) 사용 위치 - techniques/12-agentic-rag

### 7-2. Function Calling (실무 권장 구현)

1. OpenAI function calling 가이드
   1) 문서 - https://platform.openai.com/docs/guides/function-calling
2. Anthropic tool use 가이드
   1) 문서 - https://docs.anthropic.com/claude/docs/tool-use
   2) 사용 위치 - techniques/12-agentic-rag README의 실무 권장 사항

### 7-3. Adaptive RAG

1. Jeong, S., et al. (2024). "Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity."
   1) 논문 - https://arxiv.org/abs/2403.14403
2. LangGraph Adaptive RAG 튜토리얼
   1) 가이드 - https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/
   2) 사용 위치 - techniques/13-adaptive-rag

## 8. 평가

### 8-1. RAGAS

1. Es, S., et al. (2023). "RAGAS: Automated Evaluation of Retrieval Augmented Generation."
   1) 논문 - https://arxiv.org/abs/2309.15217
   2) 공식 리포 - https://github.com/explodinggradients/ragas
   3) 공식 문서 - https://docs.ragas.io/
   4) 사용 위치 - evaluation/ragas_eval.py

### 8-2. 평가 메트릭 출처

1. Faithfulness, Answer Relevancy, Context Precision/Recall - RAGAS 메트릭 문서
   1) 문서 - https://docs.ragas.io/en/stable/concepts/metrics/index.html

## 9. 한국어 NLP

### 9-1. Kiwi 형태소 분석기

1. Bab2min. Kiwipiepy.
   1) 리포 - https://github.com/bab2min/kiwipiepy
   2) 사용 위치 - common/korean_tokenizer.py, techniques/02-hybrid-search

### 9-2. Nori (Elasticsearch)

1. Elastic. Nori Analysis Plugin.
   1) 문서 - https://www.elastic.co/docs/reference/elasticsearch/plugins/analysis-nori
   2) 사용 위치 - README/문서의 대안 토크나이저로 언급

## 10. 벡터 DB / 인프라

### 10-1. Qdrant

1. Qdrant 공식 문서
   1) 문서 - https://qdrant.tech/documentation/
   2) 리포 - https://github.com/qdrant/qdrant
   3) 사용 위치 - common/vector_store.py, docker-compose.yml

## 11. 도구 / 라이브러리

1. sentence-transformers - https://www.sbert.net/
2. rank_bm25 - https://github.com/dorianbrown/rank_bm25
3. scikit-learn KMeans - https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html
4. pydantic-settings - https://docs.pydantic.dev/latest/concepts/pydantic_settings/
5. uv - https://github.com/astral-sh/uv
6. ruff - https://docs.astral.sh/ruff/

## 12. 한계 / 면책

1. 본 문서의 인용은 본 레포 구현이 참조한 자료입니다. 원논문의 모든 디테일을 본 레포가 구현했다는 의미는 아니며, V2 기법(GraphRAG, RAPTOR, Self-RAG, CRAG, Adaptive RAG)은 단순화 버전입니다
2. URL과 버전은 작성 시점(2026-05) 기준입니다. 시간이 지나면 일부 링크가 깨질 수 있습니다
3. 신규 기법 추가 시 본 파일과 각 기법 README의 참고 섹션을 같이 갱신해주세요

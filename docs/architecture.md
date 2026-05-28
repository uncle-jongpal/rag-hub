# 아키텍처

본 레포는 학습/시연 갤러리 + 평가 하네스 결합 구조입니다. 각 기법은 독립 폴더에 자체 완결적으로 구현되어 있어 한 파일만 읽어도 전체 흐름이 보이도록 설계되었습니다.

## 1. 레이어 구조

```mermaid
flowchart TB
    subgraph 진입점
        CLI[기법 단독 실행 rag.py main]
        EVAL[평가 ragas_eval.py]
    end

    subgraph 기법
        T01[01-naive]
        T02[02-hybrid-search]
        T03[03-reranking]
        T04[04-hyde]
        T05[05-multi-query]
        T06[06-parent-child]
        T07[07-contextual-retrieval]
    end

    subgraph 공통
        BASE[BaseRAG 인터페이스]
        EMB[Embedding BGE-M3]
        LLM[LLM OpenAI/Anthropic]
        VS[Qdrant Vector Store]
        TOK[Kiwi 한국어 토크나이저]
        CHUNK[Chunkers]
    end

    subgraph 인프라
        QD[(Qdrant Container)]
    end

    CLI --> 기법
    EVAL --> 기법
    기법 --> BASE
    기법 --> EMB
    기법 --> LLM
    기법 --> VS
    기법 --> TOK
    기법 --> CHUNK
    VS --> QD
```

## 2. 공통 인터페이스

모든 기법은 `common/base.py:BaseRAG` 를 상속해 다음 메서드를 구현합니다.

1. `build_index(documents)` - 문서 리스트를 받아 인덱스 구축
2. `retrieve(query, top_k)` - 질문에 대해 top-k 청크 반환
3. `generate(query, top_k)` - retrieve 후 LLM 호출까지 한 번에

이 통일된 인터페이스 덕분에 평가 하네스가 기법명만 바꿔 동일하게 호출할 수 있습니다.

## 3. 데이터 흐름 (예: Hybrid + Reranking 결합 가정)

```mermaid
sequenceDiagram
    participant User
    participant RAG as Technique RAG
    participant BM25
    participant Dense as Qdrant Dense
    participant RRF
    participant Rerank as Cross-encoder
    participant LLM

    User->>RAG: query
    RAG->>BM25: tokenize + score
    RAG->>Dense: encode + search
    BM25-->>RAG: candidates A
    Dense-->>RAG: candidates B
    RAG->>RRF: fuse A, B
    RRF-->>RAG: top-N
    RAG->>Rerank: query, top-N
    Rerank-->>RAG: top-k
    RAG->>LLM: query + contexts
    LLM-->>User: answer
```

## 4. 평가 흐름

```mermaid
flowchart LR
    Q[questions.jsonl] --> R[기법 generate]
    R --> A[answer + contexts]
    A --> RAGAS{RAGAS metrics}
    RAGAS --> F[faithfulness]
    RAGAS --> AR[answer_relevancy]
    RAGAS --> CP[context_precision]
    RAGAS --> CR[context_recall]
    F & AR & CP & CR --> J[results json + md]
    J --> CMP[compare.py]
    CMP --> CMD[compare.md]
```

## 5. 디렉토리 매핑

1. common/ - 모든 기법이 공유하는 빌딩 블록 (인터페이스, 임베딩, LLM, 벡터 저장소, 청크, 한국어 토크나이저, 설정, usage 추적)
2. data/sample/ - 한국어 15문서 + 영어 15문서 작은 데모셋
3. techniques/NN-name/ - 기법별 독립 구현 13개. rag.py 한 파일에 build_index/retrieve/generate 다 있음
4. evaluation/ - 질문 셋, 평가 스크립트, 비교 도구
5. dashboard/ - Streamlit 비교 대시보드 (4페이지)
6. docs/ - 본 문서 + overview + technique-comparison + references
7. scripts/ - 데이터 다운로드 같은 보조 스크립트

## 6. 대시보드 흐름 (V3)

```mermaid
flowchart LR
    subgraph 평가 단계
        EVAL[ragas_eval.py] --> JSON[results/*.json]
    end

    subgraph 대시보드
        APP[Streamlit app.py] --> P1[1. 기법 비교]
        APP --> P2[2. 질문별 결과]
        APP --> P3[3. 인터랙티브 검색]
        APP --> P4[4. 비용/지연 추적]
    end

    JSON --> P1
    JSON --> P2
    JSON --> P4

    P3 --> RAG[기법 RAG 직접 실행]
    RAG --> QD[(Qdrant)]
    RAG --> USAGE[usage tracker]
```

페이지 1, 2, 4는 저장된 평가 결과(JSON)를 그대로 읽어 표시합니다. 페이지 3은 실시간으로 RAG 인스턴스를 빌드하고 인덱싱한 뒤 사용자 질문에 답변합니다.

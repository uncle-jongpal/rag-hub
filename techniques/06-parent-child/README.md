# 06. Parent-Child Chunking

작은 자식 청크로 검색해 정밀도를 확보하고, 매칭된 부모 청크 전체를 LLM에 전달해 컨텍스트를 보강합니다.

## 1. 동작 원리

1. 문서를 큰 부모 청크(약 1,200자)로 자르고, 각 부모를 다시 작은 자식 청크(약 250자)로 분할
2. 자식 청크만 임베딩하여 인덱싱 (parent_idx 메타데이터에 부모 위치 저장)
3. 질문이 들어오면 자식 청크로 검색
4. 검색된 자식의 부모를 중복 제거해 top-k 부모만 컨텍스트로 사용

## 2. 강점과 약점

강점
1. 작은 단위 검색으로 정밀도가 높습니다 (한 가지 사실에 집중된 청크)
2. LLM에는 부모 전체가 전달되어 답변 생성에 충분한 맥락 확보
3. 단순 청크 크기 조정만으로 큰 효과를 기대할 수 있는 저비용 개선입니다

약점
1. 자식이 부모 경계를 침범할 경우 모호한 메타데이터 처리가 필요합니다
2. 부모 청크가 너무 크면 LLM 입력 토큰이 빠르게 늘어납니다
3. 같은 부모에서 자식이 여러 번 매칭되면 다양성 손실 가능

## 3. 실행

```bash
docker compose up -d
uv run python techniques/06-parent-child/rag.py
```

## 4. 참고

1. LangChain ParentDocumentRetriever - https://python.langchain.com/docs/how_to/parent_document_retriever/
2. LlamaIndex HierarchicalNodeParser - https://docs.llamaindex.ai/en/stable/api_reference/node_parsers/hierarchical/

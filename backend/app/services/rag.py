import json
import logging
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Hotspot, Species
from app.services.llm import chat, is_llm_configured, llm_fallback_hint

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    chunk_id: str
    species_id: str | None
    title: str
    content: str
    source: str


class EncyclopediaRAGService:
    def __init__(self) -> None:
        self.chunks: list[DocumentChunk] = []
        self._vectorizer = None
        self._matrix = None
        self._build_index()

    def _tokenize(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^0-9a-zA-Z가-힣\s]", " ", text)
        return text

    def _build_index(self) -> None:
        self.chunks = []
        species_file = settings.data_dir / "species.json"
        if species_file.exists():
            with species_file.open(encoding="utf-8") as f:
                for item in json.load(f):
                    body = "\n".join(
                        [
                            f"국명: {item['common_name']}",
                            f"학명: {item['scientific_name']}",
                            f"서식지: {item.get('habitat', '')}",
                            f"먹이: {item.get('diet', '')}",
                            f"번식기: {item.get('breeding_season', '')}",
                            f"활동시간: {item.get('active_time', '')}",
                            f"관찰팁: {item.get('observation_tips', '')}",
                            f"유사종: {item.get('similar_species', '')}",
                            f"설명: {item.get('description', '')}",
                        ]
                    )
                    self.chunks.append(
                        DocumentChunk(
                            chunk_id=f"species:{item['id']}",
                            species_id=item["id"],
                            title=f"{item['common_name']} 도감",
                            content=body,
                            source="species.json",
                        )
                    )

        extra_file = settings.data_dir / "knowledge" / "extra.json"
        if extra_file.exists():
            with extra_file.open(encoding="utf-8") as f:
                for idx, item in enumerate(json.load(f)):
                    self.chunks.append(
                        DocumentChunk(
                            chunk_id=f"extra:{idx}",
                            species_id=item.get("species_id"),
                            title=item.get("title", ""),
                            content=item.get("content", ""),
                            source="knowledge/extra.json",
                        )
                    )

        hotspots_file = settings.data_dir / "hotspots.json"
        if hotspots_file.exists():
            with hotspots_file.open(encoding="utf-8") as f:
                for idx, item in enumerate(json.load(f)):
                    body = (
                        f"관찰지: {item['name']} ({item['region']})\n"
                        f"대상종: {item['species_id']}\n"
                        f"추천월: {item.get('best_months', '')}\n"
                        f"교통: {item.get('transport_note', '')}\n"
                        f"시설: {item.get('facilities', '')}\n"
                        f"주의: {item.get('safety_note', '')}"
                    )
                    self.chunks.append(
                        DocumentChunk(
                            chunk_id=f"hotspot:{idx}",
                            species_id=item.get("species_id"),
                            title=item["name"],
                            content=body,
                            source="hotspots.json",
                        )
                    )

        if not self.chunks:
            return

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer

            corpus = [self._tokenize(f"{c.title}\n{c.content}") for c in self.chunks]
            self._vectorizer = TfidfVectorizer(max_features=5000)
            self._matrix = self._vectorizer.fit_transform(corpus)
        except Exception:
            logger.warning(
                "Failed to build TF-IDF index; falling back to keyword-less retrieval",
                exc_info=True,
            )
            self._vectorizer = None
            self._matrix = None

    def _retrieve(self, question: str, species_id: str | None, top_k: int = 4) -> list[DocumentChunk]:
        if self._vectorizer is None or self._matrix is None:
            filtered = [
                c
                for c in self.chunks
                if (species_id is None or c.species_id == species_id or c.species_id is None)
            ]
            return filtered[:top_k]

        query_vec = self._vectorizer.transform([self._tokenize(question)])
        scores = (self._matrix @ query_vec.T).toarray().ravel()
        ranked_idx = scores.argsort()[::-1]

        results: list[DocumentChunk] = []
        for idx in ranked_idx:
            chunk = self.chunks[idx]
            if species_id and chunk.species_id and chunk.species_id != species_id:
                continue
            if scores[idx] <= 0:
                continue
            results.append(chunk)
            if len(results) >= top_k:
                break
        if not results:
            results = self.chunks[:top_k]
        return results

    def _answer_with_llm(self, question: str, chunks: list[DocumentChunk]) -> str | None:
        if not is_llm_configured():
            return None
        context = "\n\n".join(f"[{c.source}] {c.title}\n{c.content}" for c in chunks)
        return chat(
            system=(
                "당신은 한국 야생동물 도감 도우미입니다. "
                "제공된 참고 문서만 사용해 한국어로 답하세요. "
                "문서에 없으면 모른다고 말하세요."
            ),
            user=f"질문: {question}\n\n참고문서:\n{context}",
            temperature=0.3,
        )

    def _answer_with_template(self, question: str, chunks: list[DocumentChunk]) -> str:
        lines = [f"질문: {question}", "", "관련 도감 정보:"]
        for chunk in chunks:
            snippet = chunk.content.replace("\n", " ")[:220]
            lines.append(f"- {chunk.title}: {snippet}...")
        lines.append("")
        lines.append(llm_fallback_hint())
        return "\n".join(lines)

    def ask(
        self,
        db: Session,
        question: str,
        species_id: str | None = None,
    ) -> dict:
        if species_id:
            species = db.get(Species, species_id)
            if not species:
                raise ValueError(f"종을 찾을 수 없습니다: {species_id}")

        chunks = self._retrieve(question, species_id)
        answer = self._answer_with_llm(question, chunks)
        source_type = "llm+rag"
        if not answer:
            answer = self._answer_with_template(question, chunks)
            source_type = "rag"

        citations = [
            {
                "chunk_id": c.chunk_id,
                "title": c.title,
                "source": c.source,
                "species_id": c.species_id,
            }
            for c in chunks
        ]
        return {
            "question": question,
            "species_id": species_id,
            "answer": answer,
            "citations": citations,
            "source": source_type,
        }


encyclopedia_rag_service = EncyclopediaRAGService()

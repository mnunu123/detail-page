# 에이전트 간 공유 상태 스키마 — 모든 에이전트가 이 구조를 따른다
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
import json


class PipelineStatus(Enum):
    IDLE = "idle"
    INFO_COLLECTING = "info_collecting"
    RESEARCHING = "researching"
    COPYWRITING = "copywriting"
    DESIGNING = "designing"
    DEPLOYED = "deployed"
    ANALYZING = "analyzing"
    IMPROVING = "improving"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentState:
    """파이프라인 전체 상태 — 에이전트 간 공유."""

    # 파이프라인 상태
    status: PipelineStatus = PipelineStatus.IDLE
    current_version: int = 1
    run_id: str = ""

    # 입력
    product_url: str = ""
    product_name: str = ""

    # 각 단계 완료 여부
    info_collected: bool = False
    research_done: bool = False
    copy_done: bool = False
    design_done: bool = False

    # 결과 파일 경로
    product_info_path: str = "outputs/structured_data/product_info.json"
    research_report_path: str = "outputs/structured_data/research_report.json"
    copy_path: str = "outputs/copy/copy_v1.json"
    design_path: str = "outputs/designs/page_v1.json"

    # A/B 테스트
    ab_test_id: str = ""
    ab_winner: str = ""  # "A", "B", or ""

    # 품질 점수
    quality_scores: dict[str, float] = field(default_factory=dict)

    # 타임스탬프
    started_at: str = ""
    completed_at: str = ""
    errors: list[str] = field(default_factory=list)

    STATE_FILE = Path("state/pipeline_state.json")

    def save(self):
        """상태를 파일에 저장."""
        self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {k: v.value if isinstance(v, Enum) else v
                for k, v in self.__dict__.items()}
        with open(self.STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls) -> "AgentState":
        """저장된 상태 로드."""
        if not cls.STATE_FILE.exists():
            return cls()
        with open(cls.STATE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        state = cls()
        for k, v in data.items():
            if k == "status":
                setattr(state, k, PipelineStatus(v))
            elif hasattr(state, k):
                setattr(state, k, v)
        return state

    def advance(self, next_status: PipelineStatus):
        """다음 단계로 전진."""
        self.status = next_status
        self.save()

    def add_error(self, error: str):
        """에러 기록."""
        self.errors.append(f"[{datetime.now().isoformat()}] {error}")
        self.save()

    def summary(self) -> str:
        """현재 상태 요약."""
        return (
            f"상태: {self.status.value} | "
            f"버전: v{self.current_version} | "
            f"정보수집: {'✅' if self.info_collected else '⏳'} | "
            f"리서치: {'✅' if self.research_done else '⏳'} | "
            f"카피: {'✅' if self.copy_done else '⏳'} | "
            f"디자인: {'✅' if self.design_done else '⏳'}"
        )

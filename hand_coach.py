#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compact hand-end coach summaries for human players."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_GRADE_PRIORITY = {
    "blunder": 0,
    "poor": 1,
    "questionable": 2,
    "good": 3,
    "excellent": 4,
}

_RISK_TIPS = {
    "poor_preflop_playability": "翻前少用可玩性差的牌冷跟注，优先加注或弃牌。",
    "negative_pot_odds_call": "跟注前先算底池赔率，胜率不够时直接弃牌。",
    "overfold": "面对下注不要只看绝对牌力，先用底池赔率判断是否过度弃牌。",
    "missed_value": "强牌要主动构建底池，别用过牌/跟注错过价值。",
    "high_risk_bluff": "低胜率大额诈唬要减少，先确认对手有弃牌空间。",
    "illegal_action": "先确认当前合法动作，避免无效输入影响训练节奏。",
    "illegal_raise_amount": "加注前先看最小加注额，使用快捷下注可减少尺寸错误。",
}

_GRADE_TIPS = {
    "blunder": "先减少明显亏损动作：遇到大额投入前停下来复查胜率、赔率和可选动作。",
    "poor": "本手最大改进点是避免低分决策重复出现，下一局先把同类场景打稳。",
    "questionable": "这手有边缘决策，下一局重点说清每次跟注/加注的理由。",
    "good": "整体决策健康，继续保持并复盘最大底池是否还能多拿价值。",
    "excellent": "本手执行质量很好，下一局继续保持选择性和主动性。",
}


@dataclass
class HandCoachSummary:
    """Summary shown after a hand for a single human player."""

    player_name: str
    status: str
    actions_reviewed: int = 0
    average_score: float = 0.0
    best_grade: str = "unknown"
    worst_decision: Optional[Dict[str, Any]] = None
    primary_tip: str = ""
    outcome_note: str = ""

    def format_text(self) -> str:
        """Render a short non-blocking terminal summary."""
        lines = ["🧑‍🏫 本手教练快评"]
        if self.status == "no_actions":
            lines.append(f"  {self.primary_tip}")
            return "\n".join(lines)

        lines.append(
            f"  {self.player_name}: 复盘 {self.actions_reviewed} 个决策，平均 {self.average_score:.1f}/100"
        )
        if self.outcome_note:
            lines.append(f"  结果: {self.outcome_note}")
        if self.worst_decision:
            action = self.worst_decision.get("action", "?")
            phase = self.worst_decision.get("phase", "?")
            recommended = self.worst_decision.get("recommended_action", "?")
            grade = self.worst_decision.get("grade", "unknown")
            score = self.worst_decision.get("score", "?")
            lines.append(f"  关键点: {phase} {action} → 建议 {recommended} ({grade} {score}/100)")
        if self.primary_tip:
            lines.append(f"  下一手重点: {self.primary_tip}")
        return "\n".join(lines)


class HandCoach:
    """Build compact coaching summaries from serialized hand history records."""

    def build_summary(self, game_record: Dict[str, Any], player_name: str) -> HandCoachSummary:
        decisions = self._collect_player_decisions(game_record, player_name)
        if not decisions:
            return HandCoachSummary(
                player_name=player_name,
                status="no_actions",
                primary_tip="本手没有可评估的人类决策；继续完成更多手牌来积累训练样本。",
            )

        average_score = round(
            sum(float(decision.get("score", 0.0)) for decision in decisions) / len(decisions),
            1,
        )
        worst = min(decisions, key=self._decision_sort_key)
        best = max(decisions, key=lambda decision: float(decision.get("score", 0.0)))

        return HandCoachSummary(
            player_name=player_name,
            status="ready",
            actions_reviewed=len(decisions),
            average_score=average_score,
            best_grade=str(best.get("grade", "unknown")),
            worst_decision=self._public_decision_view(worst),
            primary_tip=self._tip_for_decision(worst),
            outcome_note=self._outcome_note(game_record, player_name),
        )

    def _collect_player_decisions(self, game_record: Dict[str, Any], player_name: str) -> List[Dict[str, Any]]:
        decisions: List[Dict[str, Any]] = []
        for phase in game_record.get("phases", []) or []:
            phase_name = phase.get("phase", "unknown")
            for action in phase.get("actions", []) or []:
                if action.get("player_name") != player_name:
                    continue
                evaluation = action.get("decision_evaluation") or {}
                if not evaluation:
                    continue
                decision = {
                    "phase": phase_name,
                    "action": action.get("action", "unknown"),
                    "amount": action.get("amount", 0),
                    "grade": evaluation.get("grade", "unknown"),
                    "score": float(evaluation.get("score", 0.0)),
                    "recommended_action": evaluation.get("recommended_action", "unknown"),
                    "reasoning": evaluation.get("reasoning", ""),
                    "risk_tags": list(evaluation.get("risk_tags", []) or []),
                }
                decisions.append(decision)
        return decisions

    def _decision_sort_key(self, decision: Dict[str, Any]) -> tuple[int, float]:
        grade = str(decision.get("grade", "unknown"))
        priority = _GRADE_PRIORITY.get(grade, 99)
        score = float(decision.get("score", 0.0))
        return (priority, score)

    def _public_decision_view(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        score = round(float(decision.get("score", 0.0)), 1)
        return {
            "phase": decision.get("phase", "unknown"),
            "action": decision.get("action", "unknown"),
            "amount": decision.get("amount", 0),
            "grade": decision.get("grade", "unknown"),
            "score": score,
            "recommended_action": decision.get("recommended_action", "unknown"),
            "risk_tags": list(decision.get("risk_tags", []) or []),
        }

    def _tip_for_decision(self, decision: Dict[str, Any]) -> str:
        for tag in decision.get("risk_tags", []) or []:
            if tag in _RISK_TIPS:
                return _RISK_TIPS[tag]
        grade = str(decision.get("grade", "unknown"))
        return _GRADE_TIPS.get(grade, "下一手继续记录关键决策，优先复盘最大底池。")

    def _outcome_note(self, game_record: Dict[str, Any], player_name: str) -> str:
        winners = set(game_record.get("winner_names", []) or [])
        player_final = None
        for hand in game_record.get("final_hands", []) or []:
            if hand.get("player_name") == player_name:
                player_final = hand
                break
        if player_final is None:
            return "结果未知"
        winnings = player_final.get("winnings", 0)
        if player_name in winners:
            return f"赢得 {winnings} 筹码"
        if winnings:
            return f"回收 {winnings} 筹码，但不是主胜者"
        return "未赢得本手底池"

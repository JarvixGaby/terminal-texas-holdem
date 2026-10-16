#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local training center for turning player stats into next-session goals."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


FocusArea = Dict[str, str]


@dataclass
class TrainingReport:
    """Human-readable local trainer plan."""

    player_name: str
    status: str
    headline: str
    data_note: str
    metrics: Dict[str, float] = field(default_factory=dict)
    focus_areas: List[FocusArea] = field(default_factory=list)
    next_session_plan: List[str] = field(default_factory=list)
    style_distribution: Dict[str, float] = field(default_factory=dict)
    inherited_suggestions: List[str] = field(default_factory=list)

    def format_text(self) -> str:
        """Format the report for the terminal UI."""
        lines = [
            f"🎯 {self.player_name} 的训练中心",
            "=" * 60,
            f"\n📌 {self.headline}",
            f"📝 {self.data_note}",
        ]

        if self.metrics:
            metric_parts = []
            if "hands_played" in self.metrics:
                metric_parts.append(f"样本 {self.metrics['hands_played']:.0f}手")
            if "vpip" in self.metrics:
                metric_parts.append(f"VPIP {self.metrics['vpip']:.1f}%")
            if "pfr" in self.metrics:
                metric_parts.append(f"PFR {self.metrics['pfr']:.1f}%")
            if "aggression_factor" in self.metrics:
                metric_parts.append(f"攻击性 {self.metrics['aggression_factor']:.1f}")
            if "fold_to_bet" in self.metrics:
                metric_parts.append(f"弃牌率 {self.metrics['fold_to_bet']:.1f}%")
            if metric_parts:
                lines.append("\n📊 关键指标：" + " ｜ ".join(metric_parts))

        if self.style_distribution:
            lines.append("\n🎭 风格分布：")
            for style, pct in sorted(self.style_distribution.items(), key=lambda item: item[1], reverse=True):
                lines.append(f"  • {style}: {pct:.1f}%")

        lines.append("\n🔥 本轮训练重点：")
        for index, area in enumerate(self.focus_areas, 1):
            lines.append(f"  {index}. {area['title']} — {area['reason']}")
            lines.append(f"     练习：{area['drill']}")

        lines.append("\n🧭 下一局执行清单：")
        for index, item in enumerate(self.next_session_plan, 1):
            lines.append(f"  {index}. {item}")

        if self.inherited_suggestions:
            lines.append("\n💡 既有评测建议：")
            for suggestion in self.inherited_suggestions:
                lines.append(f"  • {suggestion}")

        return "\n".join(lines)


class LocalTrainerCenter:
    """Build focused training plans from existing evaluation output."""

    def build_report(self, player_name: str, evaluation: Optional[Dict] = None) -> TrainingReport:
        """Convert a player evaluation dict into a short next-session training plan."""
        evaluation = evaluation or {}
        if evaluation.get("error"):
            return self._build_onboarding_report(player_name, evaluation)

        stats = self._normalize_stats(evaluation.get("current_stats", {}))
        style_distribution = self._normalize_distribution(evaluation.get("style_distribution", {}))
        focus_areas = self._detect_focus_areas(stats, style_distribution)

        if not focus_areas:
            focus_areas = [
                {
                    "title": "保持选择性进攻",
                    "reason": "当前 VPIP/PFR/攻击性处于较健康区间",
                    "drill": "继续记录每个大底池，确认下注是否有价值下注或诈唬目标",
                },
                {
                    "title": "复盘边缘牌局",
                    "reason": "稳定盈利来自减少边缘点的反复小错",
                    "drill": "每轮结束后复盘最大底池和最纠结的一手牌",
                },
            ]

        headline = self._headline(focus_areas, style_distribution)
        return TrainingReport(
            player_name=player_name,
            status="ready",
            headline=headline,
            data_note="基于已有风格评测与玩家统计生成，适合下一次本地训练直接执行。",
            metrics=stats,
            focus_areas=focus_areas[:3],
            next_session_plan=self._build_next_session_plan(focus_areas, stats),
            style_distribution=style_distribution,
            inherited_suggestions=list(evaluation.get("suggestions", []))[:3],
        )

    def _build_onboarding_report(self, player_name: str, evaluation: Dict) -> TrainingReport:
        message = evaluation.get("message", "数据不足，暂时无法生成个性化评测。")
        return TrainingReport(
            player_name=player_name,
            status="needs_more_hands",
            headline="先建立可分析的样本",
            data_note=f"数据不足：{message}",
            focus_areas=[
                {
                    "title": "完成10手可复盘样本",
                    "reason": "训练中心需要先看到你的入局、加注、跟注和弃牌模式",
                    "drill": "开始新游戏，固定一个玩家名，至少完成10手牌",
                },
                {
                    "title": "每手只记录一个关键问题",
                    "reason": "早期样本少，先建立复盘习惯比追求复杂指标更重要",
                    "drill": "手牌结束后问自己：这手最大的决策点是什么？",
                },
            ],
            next_session_plan=[
                "从主菜单选择“开始新游戏”，固定使用同一个玩家名。",
                "优先玩标准 50BB 筹码深度，避免短码 all-in 让训练样本失真。",
                "打完后回到训练中心，再查看个性化 VPIP/PFR/主动性建议。",
            ],
        )

    def _normalize_stats(self, stats: Dict) -> Dict[str, float]:
        keys = ["hands_played", "vpip", "pfr", "aggression_factor", "fold_to_bet"]
        normalized: Dict[str, float] = {}
        for key in keys:
            value = stats.get(key)
            if isinstance(value, (int, float)):
                normalized[key] = float(value)
        return normalized

    def _normalize_distribution(self, distribution: Dict) -> Dict[str, float]:
        return {
            str(style): float(percentage)
            for style, percentage in distribution.items()
            if isinstance(percentage, (int, float)) and percentage > 0
        }

    def _detect_focus_areas(self, stats: Dict[str, float], style_distribution: Dict[str, float]) -> List[FocusArea]:
        focus: List[Tuple[int, FocusArea]] = []
        vpip = stats.get("vpip", 0.0)
        pfr = stats.get("pfr", 0.0)
        aggression = stats.get("aggression_factor", 0.0)
        fold_to_bet = stats.get("fold_to_bet", 0.0)
        primary_loose_passive = style_distribution.get("跟注站", 0.0) >= 30 or style_distribution.get("鱼", 0.0) >= 30

        if vpip > 35 or primary_loose_passive:
            focus.append((
                100,
                {
                    "title": "收紧入局范围",
                    "reason": "VPIP 偏高或跟注站倾向明显，容易用弱范围进入困难底池",
                    "drill": "翻前先按位置过滤手牌；前位少玩弱A、弱K和非同花间隔牌",
                },
            ))

        if vpip and pfr < vpip * 0.45:
            focus.append((
                90,
                {
                    "title": "提高翻前主动性",
                    "reason": "PFR 明显低于 VPIP，说明太多牌是被动跟注入池",
                    "drill": "可玩牌优先选择先加注或弃牌，减少冷跟注",
                },
            ))

        if aggression < 1.2 or primary_loose_passive:
            focus.append((
                80,
                {
                    "title": "少做自动跟注",
                    "reason": "攻击性偏低时，跟注常常只是延后亏损",
                    "drill": "面对下注先说清楚：我在价值跟注、抓诈唬，还是听牌赔率足够？说不清就弃牌",
                },
            ))

        if fold_to_bet > 55:
            focus.append((
                70,
                {
                    "title": "减少被打就弃",
                    "reason": "面对下注弃牌率偏高，容易被持续下注压制",
                    "drill": "记录每次弃牌前的底池赔率和后门听牌，挑出可以继续的中等强度牌",
                },
            ))

        if vpip < 15 and pfr < 10:
            focus.append((
                70,
                {
                    "title": "扩大好位置入局",
                    "reason": "入局范围过紧会错过按钮位/后位偷盲和价值下注机会",
                    "drill": "按钮位无人入池时，尝试加入更多同花A、同花连张和高张组合",
                },
            ))

        unique: List[FocusArea] = []
        seen = set()
        for _, area in sorted(focus, key=lambda item: item[0], reverse=True):
            if area["title"] not in seen:
                seen.add(area["title"])
                unique.append(area)
        return unique

    def _headline(self, focus_areas: List[FocusArea], style_distribution: Dict[str, float]) -> str:
        titles = [area["title"] for area in focus_areas]
        if {"收紧入局范围", "少做自动跟注"}.issubset(set(titles)):
            return "本轮训练重点：减少松弱跟注"
        if "扩大好位置入局" in titles:
            return "本轮训练重点：增加后位盈利机会"
        if style_distribution.get("紧凶", 0.0) >= 35 or style_distribution.get("平衡", 0.0) >= 35:
            return "本轮训练重点：保持紧凶质量"
        return f"本轮训练重点：{focus_areas[0]['title']}"

    def _build_next_session_plan(self, focus_areas: List[FocusArea], stats: Dict[str, float]) -> List[str]:
        titles = [area["title"] for area in focus_areas]
        plan: List[str] = []

        if "提高翻前主动性" in titles:
            plan.append("翻前可玩牌先加注或弃牌，除非有明确多人底池赔率才冷跟。")
        if "少做自动跟注" in titles:
            plan.append("每次跟注前先口头确认跟注理由：价值、抓诈唬、听牌赔率三选一。")
        if "收紧入局范围" in titles:
            plan.append("前两圈至少弃掉3手边缘弱牌，观察位置和对手行动后再入局。")
        if "扩大好位置入局" in titles:
            plan.append("按钮位/后位无人入池时，主动尝试一次标准开池加注。")

        plan.append("每轮结束后复盘最大底池，标记一个可改进决策。")
        plan.append("连续完成20手后再看统计，避免用单手输赢判断策略。")
        return plan[:5]

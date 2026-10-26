# -*- coding: utf-8 -*-
"""Terminal rendering adapter for structured engine events."""

from __future__ import annotations

import os
import sys
import unicodedata
from typing import Callable, Mapping, Optional
import builtins

from texas_holdem.engine.engine_events import EngineEvent
from texas_holdem.ui.ai_avatar_data import SPRITES


class TerminalEventRenderer:
    """Render selected EngineEvent objects to terminal-friendly lines."""

    # These themes use sampled first frames of CodeIsland's MIT-licensed GIFs.
    _AVATAR_STYLES = {
        "balanced": "claude",
        "loose_aggressive": "codex",
        "calling_station": "gemini",
        "tight_aggressive": "cursor",
        "maniac": "opencode",
        "nit": "qoder",
    }

    def __init__(
        self,
        print_fn: Optional[Callable[[str], None]] = None,
        ai_player_profiles: Optional[Mapping[str, str]] = None,
    ):
        self.print_fn = print_fn or builtins.print
        self.ai_player_profiles = dict(ai_player_profiles or {})
        self._avatar_roster_rendered = False
        self.use_color = (
            print_fn is None
            and sys.stdout.isatty()
            and "NO_COLOR" not in os.environ
        )

    def render(self, event: EngineEvent) -> bool:
        if event.type == "hand_started":
            return self._render_hand_started(event)
        if event.type == "cards_dealt":
            return self._render_cards_dealt(event)
        if event.type == "community_cards_displayed":
            return self._render_community_cards_displayed(event)
        if event.type == "game_state_displayed":
            return self._render_game_state_displayed(event)
        if event.type == "active_players_displayed":
            return self._render_active_players_displayed(event)
        if event.type == "betting_round_started":
            return self._render_betting_round_started(event)
        if event.type == "showdown_started":
            return self._render_showdown_started(event)
        if event.type == "player_hand_revealed":
            return self._render_player_hand_revealed(event)
        if event.type == "winner_announced":
            return self._render_winner_announced(event)
        if event.type == "pot_distributed":
            return self._render_pot_distributed(event)
        if event.type == "action_applied":
            return self._render_action_applied(event)
        if event.type == "validation_failed":
            return self._render_validation_failed(event)
        if event.type == "decision_feedback_displayed":
            return self._render_decision_feedback_displayed(event)
        if event.type == "hand_completed":
            return self._render_hand_completed(event)
        return False

    def _render_hand_started(self, event: EngineEvent) -> bool:
        self.print_fn("\n" + "=" * 50)
        self.print_fn("开始新的一手牌")
        self.print_fn("=" * 50)
        return True

    def _render_cards_dealt(self, event: EngineEvent) -> bool:
        street = str(event.metadata.get("street") or event.phase)
        prompts = {
            "flop": "\n发放翻牌...",
            "turn": "\n发放转牌...",
            "river": "\n发放河牌...",
        }
        self.print_fn(prompts.get(street, f"\n发放{street}..."))
        return True

    def _render_community_cards_displayed(self, event: EngineEvent) -> bool:
        cards = " ".join(str(card) for card in event.public_payload.get("community_cards", []))
        if cards:
            self.print_fn(f"公共牌: {cards}")
        return True

    def _render_game_state_displayed(self, event: EngineEvent) -> bool:
        self.print_fn(f"\n当前彩池: {event.public_payload.get('pot', 0)}")
        self.print_fn(f"当前最高下注: {event.public_payload.get('current_bet', 0)}")
        players = event.public_payload.get("players", [])
        self._render_ai_roster(players)
        for player in players:
            dealer_mark = " (D)" if player.get("is_dealer") else ""
            folded_mark = " [已弃牌]" if player.get("is_folded") else ""
            all_in_mark = " [全押]" if player.get("is_all_in") else ""
            self.print_fn(
                f"{player.get('name')}: {player.get('chips')} 筹码, "
                f"本轮下注: {player.get('current_bet')}"
                f"{dealer_mark}{folded_mark}{all_in_mark}"
            )
        return True

    def _render_active_players_displayed(self, event: EngineEvent) -> bool:
        self.print_fn("\n" + "=" * 50)
        self.print_fn("📊 当前在场玩家状态")
        self.print_fn("=" * 50)
        players = event.public_payload.get("players", [])
        self._render_ai_roster(players)
        for player in players:
            name = player.get("name")
            if not player.get("is_folded"):
                dealer_mark = " (D)" if player.get("is_dealer") else ""
                all_in_mark = " [全押]" if player.get("is_all_in") else ""
                current_bet = int(player.get("current_bet") or 0)
                bet_info = f"本轮下注: {current_bet}" if current_bet > 0 else "未下注"
                self.print_fn(
                    f"  🎮 {name}: {player.get('chips')} 筹码, "
                    f"{bet_info}{dealer_mark}{all_in_mark}"
                )
            else:
                self.print_fn(f"  ❌ {name}: 已弃牌")
        self.print_fn(f"\n💰 当前彩池: {event.public_payload.get('pot', 0)}")
        self.print_fn(f"📈 最高下注: {event.public_payload.get('current_bet', 0)}")
        self.print_fn(
            f"👥 在场玩家: {event.public_payload.get('active_count', 0)}/"
            f"{event.public_payload.get('total_players', 0)}"
        )
        return True

    def _render_ai_roster(self, players) -> None:
        """Introduce source-derived terminal mascots once per game."""
        if self._avatar_roster_rendered:
            return

        roster = [
            (str(player.get("name")), self.ai_player_profiles[str(player.get("name"))])
            for player in players
            if str(player.get("name")) in self.ai_player_profiles
        ]
        if not roster:
            return

        self._avatar_roster_rendered = True
        if len(roster) > 6:
            self.print_fn("\n🤖 完整像素头像可输入'头像'查看")
            return

        self._print_avatar_gallery(roster)

    def show_avatar_gallery(self) -> None:
        """Show the full mascot gallery on demand at a player prompt."""
        if self.ai_player_profiles:
            self._print_avatar_gallery(list(self.ai_player_profiles.items()))

    def _print_avatar_gallery(self, roster) -> None:
        self.print_fn("\n🤖 AI 对手头像")
        for start in range(0, len(roster), 3):
            seats = roster[start:start + 3]
            icons = [self._avatar_rows(profile) for _, profile in seats]
            for row_index in range(len(icons[0])):
                self.print_fn("  ".join(icon[row_index] for icon in icons))
            self.print_fn("  ".join(self._center_terminal_text(name, 24) for name, _ in seats))
            if start + 3 < len(roster):
                self.print_fn("")

    @staticmethod
    def _center_terminal_text(value: str, width: int) -> str:
        display_width = sum(
            0 if unicodedata.combining(character)
            else 2 if unicodedata.east_asian_width(character) in "FW"
            else 1
            for character in value
        )
        spaces = max(0, width - display_width)
        return " " * (spaces // 2) + value + " " * (spaces - spaces // 2)

    def _avatar_rows(self, profile: str):
        sprite = self._AVATAR_STYLES.get(profile, self._AVATAR_STYLES["balanced"])
        palette = SPRITES[sprite]["palette"]
        pixels = SPRITES[sprite]["rows"]
        return tuple(
            "".join(
                self._render_avatar_pixel(pixels[y][x], pixels[y + 1][x], palette)
                for x in range(24)
            )
            for y in range(0, 18, 2)
        )

    def _render_avatar_pixel(self, top: str, bottom: str, palette: Mapping[str, str]) -> str:
        if top == bottom == ".":
            return " "
        if not self.use_color:
            def visible(key: str) -> bool:
                if key == ".":
                    return False
                rgb = bytes.fromhex(palette[key].lstrip("#"))
                return sum(rgb) > 200

            top_visible = visible(top)
            bottom_visible = visible(bottom)
            if not top_visible and not bottom_visible:
                return " "
            if not top_visible:
                return "▄"
            if not bottom_visible:
                return "▀"
            return "█"

        def rgb(key: str) -> str:
            value = palette[key].lstrip("#")
            return ";".join(str(int(value[index:index + 2], 16)) for index in (0, 2, 4))

        if top == ".":
            return f"\033[38;2;{rgb(bottom)}m▄\033[0m"
        if bottom == ".":
            return f"\033[38;2;{rgb(top)}m▀\033[0m"
        if top == bottom:
            return f"\033[48;2;{rgb(top)}m \033[0m"
        return f"\033[38;2;{rgb(top)}m\033[48;2;{rgb(bottom)}m▀\033[0m"

    def _render_betting_round_started(self, event: EngineEvent) -> bool:
        phase = str(event.public_payload.get("phase") or event.phase).upper()
        self.print_fn(f"\n{phase} 阶段下注开始")
        return True

    def _render_showdown_started(self, event: EngineEvent) -> bool:
        self.print_fn("\n" + "=" * 30)
        self.print_fn("摊牌阶段")
        self.print_fn("=" * 30)
        return True

    def _render_player_hand_revealed(self, event: EngineEvent) -> bool:
        payload = event.public_payload
        hole_cards = " ".join(str(card) for card in payload.get("hole_cards", []))
        self.print_fn(f"{payload.get('player_name')}: {hole_cards} - {payload.get('hand_description')}")
        return True

    def _render_winner_announced(self, event: EngineEvent) -> bool:
        payload = event.public_payload
        winner_names = payload.get("winner_names", [])
        if not winner_names:
            return False
        if payload.get("winner_reason") == "fold" and len(winner_names) == 1:
            self.print_fn("\n" + "=" * 30)
            self.print_fn("本手结束")
            self.print_fn("=" * 30)
            self.print_fn(f"\n🏆 {winner_names[0]} 获胜！（其他玩家都已弃牌）")
            return True
        self.print_fn(f"\n获胜者: {', '.join(winner_names)}")
        return True

    def _render_pot_distributed(self, event: EngineEvent) -> bool:
        payload = event.public_payload
        player_name = payload.get("player_name")
        winnings = payload.get("winnings", 0)
        if payload.get("winner_reason") == "fold":
            self.print_fn(f"💰 获得彩池: {winnings} 筹码")
            return True
        self.print_fn(f"{player_name} 获得 {winnings} 筹码")
        return True

    def _render_action_applied(self, event: EngineEvent) -> bool:
        action = event.public_payload.get("action")
        player_name = event.public_payload.get("player_name")
        if action == "call":
            self.print_fn(f"{player_name} 跟注: {event.public_payload.get('amount', 0)}")
            return True
        if action == "raise":
            self.print_fn(f"{player_name} 加注到: {event.public_payload.get('current_bet', 0)}")
            return True
        if action == "fold":
            self.print_fn(f"✅ {player_name} 弃牌")
            return True
        if action == "check":
            self.print_fn(f"✅ {player_name} 过牌")
            return True
        return False

    def _render_validation_failed(self, event: EngineEvent) -> bool:
        payload = event.public_payload
        self.print_fn(
            f"❌ {payload.get('player_name')} 动作验证失败: "
            f"{payload.get('reason')}，已改为 {payload.get('fallback_action')}"
        )
        return True

    def _render_decision_feedback_displayed(self, event: EngineEvent) -> bool:
        message = event.public_payload.get("message")
        if not message:
            return False
        self.print_fn(str(message))
        return True

    def _render_hand_completed(self, event: EngineEvent) -> bool:
        return False

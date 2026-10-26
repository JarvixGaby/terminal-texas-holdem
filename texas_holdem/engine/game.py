# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 主游戏逻辑
实现游戏的核心逻辑和流程控制
"""

from typing import Callable, List, Optional, Dict, Tuple, Any
from dataclasses import asdict, is_dataclass
from texas_holdem.engine.betting_rules import NoLimitBettingRules
from texas_holdem.engine.card import Card, Deck
from texas_holdem.engine.engine_events import (
    DecisionFeedbackDisplayedEvent,
    EngineEvent,
    PlayerHandRevealedEvent,
    PotDistributedEvent,
    ShowdownStartedEvent,
    WinnerAnnouncedEvent,
)
from texas_holdem.engine.game_rules import (
    MAX_PLAYERS,
    MIN_PLAYERS,
    BlindStructure,
    GameRules,
    StackProfile,
    create_rules,
)
from texas_holdem.engine.player import Player, HumanPlayer, AIPlayer
from texas_holdem.engine.hand_evaluator import HandEvaluator
from texas_holdem.history.game_history import GameHistoryManager
from texas_holdem.training.player_styles import player_style_analyzer
from texas_holdem.engine.official_rules import official_rules_engine, GameVariant, ActionType
from texas_holdem.engine.side_pot_manager import SidePotManager
from texas_holdem.ui.terminal_renderer import TerminalEventRenderer
try:
    from texas_holdem.ai.decision_evaluator import DecisionContext, evaluate_decision, calculate_pot_odds
except ImportError:  # pragma: no cover - keeps game playable if optional evaluator is unavailable
    DecisionContext = None
    evaluate_decision = None
    calculate_pot_odds = None
from texas_holdem.ai.decision_provider import ActionResponse, BuiltInAIDecisionProvider, DecisionProvider, GameStateSnapshot, VisiblePlayerSnapshot
from texas_holdem.ai.action_validator import ValidatedAction, validate_action
import time


class TexasHoldemGame:
    """德州扑克游戏主类"""
    
    def __init__(
        self,
        players: List[Player],
        small_blind: int = 5,
        big_blind: int = 10,
        rules: Optional[GameRules] = None,
    ):
        """
        初始化游戏
        
        Args:
            players: 玩家列表（2-10人）
            small_blind: 小盲注
            big_blind: 大盲注
        """
        if len(players) < MIN_PLAYERS or len(players) > MAX_PLAYERS:
            raise ValueError(f"玩家数量必须在{MIN_PLAYERS}-{MAX_PLAYERS}人之间")
        
        if rules is None:
            rules = create_rules(
                BlindStructure(small_blind, big_blind),
                StackProfile("custom", custom_chips=players[0].chips if players else big_blind * 50),
            )

        self.players = players
        self.rules = rules
        self.small_blind = rules.small_blind
        self.big_blind = rules.big_blind
        self.betting_rules = NoLimitBettingRules(
            big_blind=self.big_blind,
            allow_short_all_in=rules.allow_short_all_in,
        )
        self.deck = Deck()
        self.community_cards: List[Card] = []  # 公共牌
        self.pot = 0  # 彩池
        self.current_bet = 0  # 当前回合最高下注
        self.last_full_raise_increment = self.big_blind
        self.current_bet_reopens_action = True
        self._betting_acted_since_last_raise = set()
        self.dealer_position = 0  # 庄家位置
        self.active_players: List[Player] = []  # 仍在游戏中的玩家
        self.game_phase = "preflop"  # 游戏阶段：preflop, flop, turn, river
        self.variant = GameVariant.NO_LIMIT  # 游戏变种
        
        # 历史记录管理器
        self.history_manager = GameHistoryManager()
        
        # 边池管理器
        self.side_pot_manager = SidePotManager()
        
        # 规则引擎配置
        official_rules_engine.variant = self.variant
        self.current_game_id: Optional[str] = None
        
        # 实时辅助系统
        self.assistant_enabled = True  # 默认启用
        self._assistant = None
        self.decision_providers: Dict[str, DecisionProvider] = {}
        self.last_action_response: Optional[ActionResponse] = None
        self.last_validated_action: Optional[ValidatedAction] = None
        self.current_blind_metadata: Dict[str, Any] = {"blind_positions": {}, "forced_blinds": []}
        self.event_subscribers: List[Callable[[EngineEvent], None]] = []
        self.ai_action_delay_seconds = 1.0
        self._human_advice_equity: Optional[Tuple[Tuple[Any, ...], float]] = None
        self._completed_replay_record: Optional[Dict[str, Any]] = None
        self.delay_fn: Callable[[float], None] = time.sleep
        self.render_terminal_events = True
        self._terminal_event_renderer: Optional[TerminalEventRenderer] = self._create_terminal_event_renderer()
        
    def start_new_hand(self):
        """开始新的一手牌"""
        # 重置所有玩家状态
        for player in self.players:
            player.reset_for_new_hand()
        
        # 重置游戏状态
        self.deck.reset()
        self.deck.shuffle()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.last_full_raise_increment = self.big_blind
        self.current_bet_reopens_action = True
        self._betting_acted_since_last_raise = set()
        self.side_pot_manager.reset()
        self.game_phase = "preflop"
        self.current_blind_metadata = {"blind_positions": {}, "forced_blinds": []}
        self.active_players = [p for p in self.players if p.chips > 0]
        
        if len(self.active_players) < 2:
            print("游戏结束！没有足够的玩家继续游戏。")
            return False
        
        # 开始记录新的牌局
        player_names = [p.name for p in self.active_players]
        self.current_game_id = self.history_manager.start_new_game_record(
            players=player_names,
            small_blind=self.small_blind,
            big_blind=self.big_blind,
            dealer_position=self.dealer_position
        )
        self._emit_event(
            "hand_started",
            public_payload={
                "players": player_names,
                "small_blind": self.small_blind,
                "big_blind": self.big_blind,
                "dealer_position": self.dealer_position,
                "phase": self.game_phase,
                "pot": self.pot,
                "current_bet": self.current_bet,
            },
        )
        
        # 发手牌
        self._deal_hole_cards()
        
        # 收取盲注
        self._collect_blinds()
        
        # 记录翻牌前阶段
        self.history_manager.start_new_phase("preflop", [], self.pot, self.current_bet)
        
        # 显示初始状态
        self._display_game_state()
        
        return True
    
    def play_hand(self):
        """进行一手牌的游戏"""
        if not self.start_new_hand():
            return False
        
        # 翻牌前下注
        if self._betting_round():
            # 翻牌（Flop）
            self._deal_flop()
            self._display_community_cards()
            
            if self._betting_round():
                # 转牌（Turn）
                self._deal_turn()
                self._display_community_cards()
                
                if self._betting_round():
                    # 河牌（River）
                    self._deal_river()
                    self._display_community_cards()
                    
                    if self._betting_round():
                        # 摊牌
                        self._showdown()
                    else:
                        # 河牌下注后只剩一个玩家
                        self._handle_early_winner()
                else:
                    # 转牌下注后只剩一个玩家
                    self._handle_early_winner()
            else:
                # 翻牌下注后只剩一个玩家
                self._handle_early_winner()
        else:
            # 翻牌前下注后只剩一个玩家
            self._handle_early_winner()
        
        # 移动庄家位置
        self._move_dealer()
        
        return True
    
    def _deal_hole_cards(self):
        """发手牌（每人2张）"""
        print("发放手牌...")
        for _ in range(2):
            for player in self.active_players:
                card = self.deck.deal_card()
                if card:
                    player.add_card(card)
    
    def _collect_blinds(self):
        """收取盲注"""
        if len(self.active_players) < 2:
            return
        
        # 确定小盲注和大盲注位置
        # 两人对局：庄家 = 小盲注；三人以上：庄家左边 = 小盲注
        if len(self.active_players) == 2:
            small_blind_pos = self.dealer_position
            big_blind_pos = (self.dealer_position + 1) % len(self.active_players)
        else:
            small_blind_pos = (self.dealer_position + 1) % len(self.active_players)
            big_blind_pos = (self.dealer_position + 2) % len(self.active_players)
        
        # 收取小盲注
        small_blind_player = self.active_players[small_blind_pos]
        small_blind_chips_before = small_blind_player.chips
        small_blind_amount = small_blind_player.bet(self.small_blind)
        self.pot += small_blind_amount
        self.side_pot_manager.add_contribution(small_blind_player.name, small_blind_amount, is_all_in=small_blind_player.is_all_in)
        print(f"{small_blind_player.name} 下小盲注: {small_blind_amount}")
        
        # 收取大盲注
        big_blind_player = self.active_players[big_blind_pos]
        big_blind_chips_before = big_blind_player.chips
        big_blind_amount = big_blind_player.bet(self.big_blind)
        self.pot += big_blind_amount
        self.side_pot_manager.add_contribution(big_blind_player.name, big_blind_amount, is_all_in=big_blind_player.is_all_in)
        self.current_bet = big_blind_amount
        self.last_full_raise_increment = self.big_blind
        print(f"{big_blind_player.name} 下大盲注: {big_blind_amount}")
        self.current_blind_metadata = {
            "blind_positions": {
                "small_blind": small_blind_player.name,
                "big_blind": big_blind_player.name,
            },
            "forced_blinds": [
                {
                    "player_name": small_blind_player.name,
                    "blind_type": "small_blind",
                    "amount": small_blind_amount,
                    "chips_before": small_blind_chips_before,
                    "chips_after": small_blind_player.chips,
                    "is_forced": True,
                    "is_all_in": small_blind_player.is_all_in,
                },
                {
                    "player_name": big_blind_player.name,
                    "blind_type": "big_blind",
                    "amount": big_blind_amount,
                    "chips_before": big_blind_chips_before,
                    "chips_after": big_blind_player.chips,
                    "is_forced": True,
                    "is_all_in": big_blind_player.is_all_in,
                },
            ],
        }
    
    def _deal_flop(self):
        """发翻牌（3张公共牌）"""
        self.game_phase = "flop"
        self.deck.deal_card()  # 烧牌
        for _ in range(3):
            card = self.deck.deal_card()
            if card:
                self.community_cards.append(card)
        
        # 记录翻牌阶段
        self.history_manager.start_new_phase("flop", self.community_cards, self.pot, 0)
        self._emit_event(
            "phase_started",
            public_payload={
                "phase": self.game_phase,
                "community_cards": [str(card) for card in self.community_cards],
                "pot": self.pot,
                "current_bet": self.current_bet,
            },
        )
        self._emit_event(
            "cards_dealt",
            public_payload={"community_cards": [str(card) for card in self.community_cards]},
            metadata={"street": "flop"},
        )
    
    def _deal_turn(self):
        """发转牌（第4张公共牌）"""
        self.game_phase = "turn"
        self.deck.deal_card()  # 烧牌
        card = self.deck.deal_card()
        if card:
            self.community_cards.append(card)
        
        # 记录转牌阶段
        self.history_manager.start_new_phase("turn", self.community_cards, self.pot, 0)
        self._emit_event(
            "phase_started",
            public_payload={
                "phase": self.game_phase,
                "community_cards": [str(card) for card in self.community_cards],
                "pot": self.pot,
                "current_bet": self.current_bet,
            },
        )
        self._emit_event(
            "cards_dealt",
            public_payload={"community_cards": [str(card) for card in self.community_cards]},
            metadata={"street": "turn"},
        )
    
    def _deal_river(self):
        """发河牌（第5张公共牌）"""
        self.game_phase = "river"
        self.deck.deal_card()  # 烧牌
        card = self.deck.deal_card()
        if card:
            self.community_cards.append(card)
        
        # 记录河牌阶段
        self.history_manager.start_new_phase("river", self.community_cards, self.pot, 0)
        self._emit_event(
            "phase_started",
            public_payload={
                "phase": self.game_phase,
                "community_cards": [str(card) for card in self.community_cards],
                "pot": self.pot,
                "current_bet": self.current_bet,
            },
        )
        self._emit_event(
            "cards_dealt",
            public_payload={"community_cards": [str(card) for card in self.community_cards]},
            metadata={"street": "river"},
        )
    
    def _get_min_raise_total(self) -> int:
        """Return the minimum total bet target for a raise in the current state."""
        return self.betting_rules.minimum_raise_total(
            current_bet=self.current_bet,
            last_full_raise_increment=self.last_full_raise_increment,
        )

    def _get_legal_actions(self, player: Player, amount_to_call: int) -> List[str]:
        """Compute legal actions without prompting for input."""
        legal_actions = self.betting_rules.legal_actions(
            amount_to_call=amount_to_call,
            current_bet=self.current_bet,
            player_current_bet=player.current_bet,
            player_chips=player.chips,
            last_full_raise_increment=self.last_full_raise_increment,
        )
        if (
            amount_to_call > 0
            and not self.current_bet_reopens_action
            and player.name in self._betting_acted_since_last_raise
            and "raise" in legal_actions
        ):
            legal_actions.remove("raise")
        return legal_actions

    def _estimate_player_equity(self, player: Player) -> Optional[float]:
        """Estimate player equity using the optimized calculator when available."""
        try:
            from texas_holdem.ai.optimized_odds_calculator import get_ai_equity_calculator

            opponent_count = len([
                opponent for opponent in self.active_players
                if opponent != player and not opponent.is_folded
            ])
            calculator = get_ai_equity_calculator()
            return calculator.get_equity(player.hand, self.community_cards, opponent_count)
        except Exception:
            return None

    def _build_decision_context(self, player: Player, action: str, amount: int,
                                amount_to_call: int, legal_actions: List[str],
                                min_raise: int,
                                decision_pot_size: Optional[int] = None,
                                decision_player_chips: Optional[int] = None,
                                decision_current_bet: Optional[int] = None):
        """Build a DecisionContext for the decision-point game state."""
        if DecisionContext is None:
            return None

        opponent_count = len([
            opponent for opponent in self.active_players
            if opponent != player and not opponent.is_folded
        ])
        pot_size = self.pot if decision_pot_size is None else decision_pot_size
        current_bet = self.current_bet if decision_current_bet is None else decision_current_bet
        player_chips = player.chips if decision_player_chips is None else decision_player_chips
        effective_call = min(amount_to_call, player_chips)
        pot_odds = calculate_pot_odds(pot_size, effective_call) if calculate_pot_odds else None
        position = self.active_players.index(player) if player in self.active_players else 0

        equity_key = (
            self.current_game_id, self.game_phase, player.name,
            pot_size, current_bet, player_chips,
        )
        cached_equity = self._human_advice_equity
        estimated_equity = (
            cached_equity[1]
            if isinstance(player, HumanPlayer) and cached_equity and cached_equity[0] == equity_key
            else self._estimate_player_equity(player)
        )

        return DecisionContext(
            game_id=self.current_game_id or "",
            hand_id=self.current_game_id or "",
            player_name=player.name,
            phase=self.game_phase,
            position=str(position),
            hole_cards=[str(card) for card in player.hand],
            community_cards=[str(card) for card in self.community_cards],
            pot_size=pot_size,
            current_bet=current_bet,
            amount_to_call=effective_call,
            player_chips=player_chips,
            legal_actions=list(legal_actions),
            action_taken=action,
            amount=amount,
            estimated_equity=estimated_equity,
            pot_odds=pot_odds,
            opponent_count=opponent_count,
            min_raise=min_raise,
        )

    def _evaluation_to_dict(self, evaluation) -> Optional[Dict[str, Any]]:
        """Convert evaluator output to a plain dict for history serialization."""
        if evaluation is None:
            return None
        if isinstance(evaluation, dict):
            return evaluation
        if is_dataclass(evaluation):
            return asdict(evaluation)
        if hasattr(evaluation, "__dict__"):
            return dict(evaluation.__dict__)
        return None

    def _evaluate_player_decision(self, player: Player, action: str, amount: int,
                                  amount_to_call: int,
                                  legal_actions: Optional[List[str]] = None,
                                  min_raise: Optional[int] = None,
                                  decision_pot_size: Optional[int] = None,
                                  decision_player_chips: Optional[int] = None,
                                  decision_current_bet: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Evaluate and serialize a player's decision, returning None on failure."""
        if evaluate_decision is None or DecisionContext is None:
            return None
        try:
            legal_actions = legal_actions or self._get_legal_actions(player, amount_to_call)
            min_raise = self._get_min_raise_total() if min_raise is None else min_raise
            context = self._build_decision_context(
                player,
                action,
                amount,
                amount_to_call,
                legal_actions,
                min_raise,
                decision_pot_size=decision_pot_size,
                decision_player_chips=decision_player_chips,
                decision_current_bet=decision_current_bet,
            )
            return self._evaluation_to_dict(evaluate_decision(context))
        except Exception:
            return None

    def _format_decision_feedback(self, evaluation: Optional[Dict[str, Any]]) -> str:
        """Format compact non-blocking decision feedback."""
        if not evaluation:
            return ""
        grade = evaluation.get("grade", "unknown")
        score = evaluation.get("score", "?")
        try:
            score = int(round(float(score)))
        except (TypeError, ValueError):
            pass
        recommended = evaluation.get("recommended_action", "unknown")
        reasoning = evaluation.get("reasoning", "")
        from texas_holdem.ui import localization
        if localization.ACTIVE and localization.LANGUAGE == "zh":
            grade = {
                "excellent": "优秀", "good": "合理", "questionable": "待商榷",
                "poor": "较差", "blunder": "严重失误",
            }.get(grade, grade)
            recommended = {
                "fold": "弃牌", "check": "过牌", "call": "跟注", "raise": "加注",
            }.get(recommended, recommended)
            reasoning = {
                "Low equity combined with an all-in or large raise is a high-risk bluff.": "低胜率大额加注风险高。",
                "Very strong equity should usually build the pot when raising is legal.": "强牌可加注获取价值。",
                "Preflop call has poor playability/realization; raw equity alone does not justify continuing with this offsuit disconnected hand.": "翻前可玩性弱，裸胜率不足以支持跟注。",
                "Fold is preferred because this preflop hand has poor playability/realization despite the raw pot-odds estimate.": "翻前可玩性弱，弃牌更稳妥。",
                "Preflop fold is not penalized from noisy raw equity alone for this non-premium hand.": "非强牌的胜率估算不确定，弃牌合理。",
                "Preflop call with a strong hand is not penalized from noisy raw equity alone.": "强牌跟注合理，翻前胜率估算有噪声。",
                "Called with equity far below the pot odds required to continue.": "估算胜率远低于跟注所需赔率。",
                "Called without enough equity to meet the offered pot odds.": "估算胜率不足以支持跟注。",
                "Call is supported because estimated equity meets or exceeds pot odds.": "估算胜率达到跟注所需赔率。",
                "Folded despite equity being far above the price offered by pot odds.": "估算胜率明显高于跟注成本。",
                "Action is reasonable under the available rule-based checks.": "按当前规则评估，行动合理。",
                "Fold is not contradicted by the available equity and pot-odds checks.": "当前胜率与赔率不反对弃牌。",
                "Raise is legal and not flagged by the risk rules.": "加注合法，未触发明显风险。",
                "No specific rule matched this decision.": "暂无明确的评价规则。",
            }.get(reasoning, reasoning)
        if reasoning and len(reasoning) > 40:
            reasoning = reasoning[:37].rstrip() + "..."
        suffix = f" | {reasoning}" if reasoning else ""
        return f"📊 训练提示: {grade} {score}/100 | 建议倾向: {recommended}{suffix}"

    def _show_decision_feedback(self, player: Player, evaluation: Optional[Dict[str, Any]]):
        """Show compact feedback only for human players."""
        if not isinstance(player, HumanPlayer):
            return
        message = self._format_decision_feedback(evaluation)
        if message:
            self._emit_event(
                "decision_feedback_displayed",
                public_payload={
                    "player_name": player.name,
                    "message": message,
                },
            )

    def _record_processed_action(self, player: Player, action: str, amount: int,
                                 chips_before: int, amount_to_call: int,
                                 legal_actions: Optional[List[str]] = None,
                                 min_raise: Optional[int] = None,
                                 evaluation_amount: Optional[int] = None,
                                 decision_pot_size: Optional[int] = None,
                                 decision_player_chips: Optional[int] = None,
                                 decision_current_bet: Optional[int] = None):
        """Evaluate a decision-point snapshot, then record a processed action."""
        evaluation = self._evaluate_player_decision(
            player,
            action,
            amount if evaluation_amount is None else evaluation_amount,
            amount_to_call,
            legal_actions=legal_actions,
            min_raise=min_raise,
            decision_pot_size=decision_pot_size,
            decision_player_chips=decision_player_chips,
            decision_current_bet=decision_current_bet,
        )
        action_metadata = self._build_action_metadata()
        record_kwargs = {"decision_evaluation": evaluation}
        if action_metadata is not None:
            record_kwargs["action_metadata"] = action_metadata
        self.history_manager.record_action(
            player.name,
            action,
            amount,
            chips_before,
            player.chips,
            **record_kwargs,
        )
        action_payload = {
            "player_name": player.name,
            "action": action,
            "amount": amount,
            "chips_before": chips_before,
            "chips_after": player.chips,
            "pot_size": self.pot,
            "current_bet": self.current_bet,
        }
        if self.last_validated_action is not None and not self.last_validated_action.is_valid:
            self._emit_event(
                "validation_failed",
                public_payload={
                    "player_name": player.name,
                    "original_action": self.last_validated_action.original_action,
                    "original_amount": self.last_validated_action.original_amount,
                    "fallback_action": self.last_validated_action.action,
                    "reason": self.last_validated_action.reason,
                },
            )
        self._emit_event("action_applied", public_payload=action_payload)
        self._show_decision_feedback(player, evaluation)

    def _build_action_metadata(self) -> Optional[Dict[str, Any]]:
        """Return provider/validator metadata for the last decision, if available."""
        if self.last_action_response is None and self.last_validated_action is None:
            return None

        metadata: Dict[str, Any] = {}
        if self.last_action_response is not None:
            metadata.update({
                "raw_action": self.last_action_response.action,
                "raw_amount": self.last_action_response.amount,
                "raw_response": self.last_action_response.raw_response,
                "provider_error": self.last_action_response.error,
                "provider_metadata": self.last_action_response.metadata,
            })
        if self.last_validated_action is not None:
            metadata.update({
                "validated_action": self.last_validated_action.action,
                "validated_amount": self.last_validated_action.amount,
                "is_valid": self.last_validated_action.is_valid,
                "validation_reason": self.last_validated_action.reason,
            })
        return metadata
    
    def _betting_round(self) -> bool:
        """
        进行一轮下注

        Returns:
            bool: True表示继续游戏，False表示游戏结束
        """
        self._emit_event(
            "betting_round_started",
            public_payload={
                "phase": self.game_phase,
                "pot": self.pot,
                "current_bet": self.current_bet,
                "active_player_names": [
                    player.name for player in self.active_players if not player.is_folded
                ],
            },
        )

        # 重置当前回合下注（preflop 保留盲注已下注额）
        if self.game_phase != "preflop":
            for player in self.active_players:
                if not player.is_folded:
                    player.current_bet = 0
            self.current_bet = 0
            self.last_full_raise_increment = self.big_blind

        # 确定下注顺序
        betting_order = self._get_betting_order()
        last_raiser = None
        acted_since_last_raise = set()
        self._betting_acted_since_last_raise = acted_since_last_raise
        betting_complete = False

        # 防止无限循环：设置最大迭代次数
        MAX_BETTING_ITERATIONS = 100
        iteration_count = 0

        def emit_betting_round_completed(continued: bool) -> bool:
            self._emit_event(
                "betting_round_completed",
                public_payload={
                    "phase": self.game_phase,
                    "continued": continued,
                    "active_player_names": [
                        player.name for player in self.active_players if not player.is_folded
                    ],
                    "pot": self.pot,
                    "current_bet": self.current_bet,
                    "iteration_count": iteration_count,
                },
            )
            return continued

        while not betting_complete:
            iteration_count += 1
            if iteration_count > MAX_BETTING_ITERATIONS:
                print(f"⚠️ 警告：下注轮次超过最大迭代次数 ({MAX_BETTING_ITERATIONS})")
                print(f"   游戏阶段: {self.game_phase}")
                print(f"   活跃玩家: {[p.name for p in self.active_players if not p.is_folded]}")
                raise RuntimeError(
                    f"下注轮次异常：超过最大迭代次数 {MAX_BETTING_ITERATIONS}。"
                    f"可能存在逻辑错误，请检查游戏状态。"
                )
            action_taken = False
            self._betting_acted_since_last_raise = acted_since_last_raise
            
            for player in betting_order:
                if player.is_folded or player.is_all_in:
                    continue
                
                # 计算需要跟注的金额
                amount_to_call = self.current_bet - player.current_bet
                legal_actions = self._get_legal_actions(player, amount_to_call)
                min_raise = self._get_min_raise_total()
                
                # 获取玩家动作
                action, amount = self._get_player_action(player, amount_to_call)
                
                # AI玩家动作后添加延迟，让用户有时间观察
                if isinstance(player, AIPlayer):
                    self._delay_after_ai_action()
                
                # 记录决策前快照；评估必须基于行动发生前的彩池/筹码/当前下注
                chips_before = player.chips
                decision_pot_size = self.pot
                decision_current_bet = self.current_bet
                
                # 处理动作
                if action == "fold":
                    player.fold()
                    # 打印已在确认函数中完成
                    self._record_processed_action(player, "fold", 0, chips_before, amount_to_call, legal_actions, min_raise, decision_pot_size=decision_pot_size, decision_player_chips=chips_before, decision_current_bet=decision_current_bet)
                    player_style_analyzer.update_player_action(player.name, "fold")
                    # 更新AI对手建模
                    self._update_ai_opponent_models(player.name, "fold", 0)
                    acted_since_last_raise.add(player.name)
                    action_taken = True
                
                elif action == "check":
                    # 打印已在确认函数中完成
                    self._record_processed_action(player, "check", 0, chips_before, amount_to_call, legal_actions, min_raise, decision_pot_size=decision_pot_size, decision_player_chips=chips_before, decision_current_bet=decision_current_bet)
                    player_style_analyzer.update_player_action(player.name, "check")
                    # 更新AI对手建模
                    self._update_ai_opponent_models(player.name, "check", 0)
                    acted_since_last_raise.add(player.name)
                
                elif action == "call":
                    actual_amount = player.call(amount_to_call)
                    self.pot += actual_amount
                    self.side_pot_manager.add_contribution(player.name, actual_amount, is_all_in=player.is_all_in)
                    self._record_processed_action(player, "call", actual_amount, chips_before, amount_to_call, legal_actions, min_raise, decision_pot_size=decision_pot_size, decision_player_chips=chips_before, decision_current_bet=decision_current_bet)
                    player_style_analyzer.update_player_action(player.name, "call", actual_amount)
                    # 更新AI对手建模
                    self._update_ai_opponent_models(player.name, "call", actual_amount)
                    acted_since_last_raise.add(player.name)
                    action_taken = True
                
                elif action == "raise":
                    # 加注逻辑：amount是目标总下注额，需要减去玩家当前已下注的金额
                    previous_current_bet = self.current_bet
                    additional_bet = amount - player.current_bet
                    actual_amount = player.bet(additional_bet)
                    self.pot += actual_amount
                    self.side_pot_manager.add_contribution(player.name, actual_amount, is_all_in=player.is_all_in)
                    self.current_bet = amount  # 设置新的当前下注额
                    last_raiser = player
                    self._record_processed_action(player, "raise", actual_amount, chips_before, amount_to_call, legal_actions, min_raise, evaluation_amount=amount, decision_pot_size=decision_pot_size, decision_player_chips=chips_before, decision_current_bet=decision_current_bet)
                    player_style_analyzer.update_player_action(player.name, "raise", actual_amount)
                    # 更新AI对手建模
                    self._update_ai_opponent_models(player.name, "raise", actual_amount)
                    if self.betting_rules.is_full_raise(
                        target_total=amount,
                        previous_current_bet=previous_current_bet,
                        last_full_raise_increment=self.last_full_raise_increment,
                    ):
                        self.last_full_raise_increment = amount - previous_current_bet
                        acted_since_last_raise = {player.name}
                        self.current_bet_reopens_action = True
                    else:
                        acted_since_last_raise.add(player.name)
                        self.current_bet_reopens_action = False
                    self._betting_acted_since_last_raise = acted_since_last_raise
                    action_taken = True

                active_non_folded = [p for p in self.active_players if not p.is_folded]
                if len(active_non_folded) <= 1:
                    return emit_betting_round_completed(False)

                pending_players = [
                    p for p in self.active_players
                    if not p.is_folded and not p.is_all_in
                ]
                everyone_acted = all(p.name in acted_since_last_raise for p in pending_players)
                if everyone_acted and self._is_betting_complete():
                    betting_complete = True
                    break
            
            # 检查是否只剩一个玩家
            active_non_folded = [p for p in self.active_players if not p.is_folded]
            if len(active_non_folded) <= 1:
                return emit_betting_round_completed(False)
            
            # 检查下注是否完成
            if not action_taken or self._is_betting_complete():
                betting_complete = True
        
        return emit_betting_round_completed(
            len([p for p in self.active_players if not p.is_folded]) > 1
        )
    
    def _get_betting_order(self) -> List[Player]:
        """获取下注顺序"""
        if self.game_phase == "preflop":
            # 翻牌前，大盲注后面的玩家开始
            start_pos = (self.dealer_position + 3) % len(self.active_players)
        else:
            # 其他阶段，小盲注开始
            start_pos = (self.dealer_position + 1) % len(self.active_players)
        
        order = []
        for i in range(len(self.active_players)):
            pos = (start_pos + i) % len(self.active_players)
            order.append(self.active_players[pos])
        
        return order
    
    def _is_betting_complete(self) -> bool:
        """检查下注是否完成"""
        active_non_folded = [p for p in self.active_players if not p.is_folded and not p.is_all_in]
        
        if len(active_non_folded) <= 1:
            return True
        
        # 检查所有玩家的下注是否相等
        for player in active_non_folded:
            if player.current_bet != self.current_bet:
                return False
        
        return True

    def _delay_after_ai_action(self) -> None:
        """Delay AI action display for terminal play; disable in headless flows."""
        if self.ai_action_delay_seconds > 0:
            self.delay_fn(self.ai_action_delay_seconds)
    
    def set_decision_provider(self, player_name: str, provider: DecisionProvider):
        """Register a custom decision provider for a player."""
        self.decision_providers[player_name] = provider

    def enable_terminal_event_rendering(self, print_fn: Optional[Callable[[str], None]] = None) -> None:
        """Render selected engine events with the terminal adapter."""
        self._terminal_event_renderer = self._create_terminal_event_renderer(print_fn)
        self.render_terminal_events = True

    def _create_terminal_event_renderer(
        self,
        print_fn: Optional[Callable[[str], None]] = None,
    ) -> TerminalEventRenderer:
        """Pass display-only AI archetypes to the terminal renderer."""
        ai_player_profiles = {
            player.name: player.archetype_name
            for player in self.players
            if isinstance(player, AIPlayer) and player.archetype_name is not None
        }
        return TerminalEventRenderer(
            print_fn=print_fn,
            ai_player_profiles=ai_player_profiles,
        )

    def subscribe_to_events(self, subscriber: Callable[[EngineEvent], None]) -> None:
        """Register a callback for structured engine events."""
        self.event_subscribers.append(subscriber)

    def _emit_event(
        self,
        event_type: str,
        public_payload: Optional[Dict[str, Any]] = None,
        private_payload_by_player: Optional[Dict[str, Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EngineEvent:
        event_classes = {
            "decision_feedback_displayed": DecisionFeedbackDisplayedEvent,
            "showdown_started": ShowdownStartedEvent,
            "player_hand_revealed": PlayerHandRevealedEvent,
            "winner_announced": WinnerAnnouncedEvent,
            "pot_distributed": PotDistributedEvent,
        }
        event_class = event_classes.get(event_type, EngineEvent)
        event = event_class(
            type=event_type,
            hand_id=self.current_game_id or "",
            phase=self.game_phase,
            public_payload=public_payload or {},
            private_payload_by_player=private_payload_by_player or {},
            metadata=metadata or {},
        )
        for subscriber in list(self.event_subscribers):
            subscriber(event)
        if (
            self.render_terminal_events
            and self._terminal_event_renderer is not None
            and event.type in {
                "cards_dealt",
                "community_cards_displayed",
                "game_state_displayed",
                "active_players_displayed",
                "hand_started",
                "betting_round_started",
                "betting_round_completed",
                "action_applied",
                "validation_failed",
                "decision_feedback_displayed",
                "showdown_started",
                "player_hand_revealed",
                "winner_announced",
                "pot_distributed",
                "hand_completed",
            }
        ):
            self._terminal_event_renderer.render(event)
        return event

    def _get_default_decision_provider(self, player: Player) -> DecisionProvider:
        if isinstance(player, AIPlayer):
            return BuiltInAIDecisionProvider(player, community_cards_provider=lambda: list(self.community_cards))
        return _LegacyHumanGameDecisionProvider(self, player)

    def _build_game_state_snapshot(self, player: Player, amount_to_call: int,
                                   legal_actions: Optional[List[str]] = None,
                                   min_raise: Optional[int] = None) -> GameStateSnapshot:
        """Build the public/private-bounded snapshot passed to decision providers."""
        if legal_actions is None:
            legal_actions = self._get_legal_actions(player, amount_to_call)
        if min_raise is None:
            min_raise = self._get_min_raise_total()

        visible_players = [
            VisiblePlayerSnapshot(
                name=visible_player.name,
                chips=visible_player.chips,
                current_bet=visible_player.current_bet,
                is_folded=visible_player.is_folded,
                is_all_in=visible_player.is_all_in,
                position=index,
            )
            for index, visible_player in enumerate(self.active_players)
        ]

        action_history: List[Dict[str, Any]] = []
        record = self.history_manager.current_game_record
        if record:
            for phase in record.phases:
                for recorded_action in phase.actions:
                    action_history.append({
                        "phase": phase.phase,
                        "player_name": recorded_action.player_name,
                        "action": recorded_action.action,
                        "amount": recorded_action.amount,
                    })

        position = self.active_players.index(player) if player in self.active_players else 0
        hand_id = self.current_game_id or ""
        return GameStateSnapshot(
            game_id=self.current_game_id or "",
            hand_id=hand_id,
            phase=self.game_phase,
            player_name=player.name,
            position=position,
            hole_cards=[str(card) for card in player.hand],
            community_cards=[str(card) for card in self.community_cards],
            pot_size=self.pot,
            current_bet=self.current_bet,
            amount_to_call=amount_to_call,
            player_chips=player.chips,
            visible_players=visible_players,
            action_history=action_history,
            legal_actions=list(legal_actions),
            min_raise=min_raise,
            dealer_position=self.dealer_position,
            small_blind=self.small_blind,
            big_blind=self.big_blind,
        )

    def _get_player_action(self, player: Player, amount_to_call: int) -> Tuple[str, int]:
        """获取玩家动作 through provider + validator pipeline."""
        legal_actions = self._get_legal_actions(player, amount_to_call)
        snapshot = self._build_game_state_snapshot(
            player,
            amount_to_call,
            legal_actions=legal_actions,
            min_raise=self._get_min_raise_total(),
        )
        provider = self.decision_providers.get(player.name) or self._get_default_decision_provider(player)
        response = provider.decide(snapshot)
        validated = validate_action(snapshot, response)
        self.last_action_response = response
        self.last_validated_action = validated
        return validated.action, validated.amount
    
    def _get_ai_action(self, player: AIPlayer, amount_to_call: int) -> Tuple[str, int]:
        """获取AI玩家动作"""
        min_raise = self.big_blind if self.current_bet == 0 else self.current_bet * 2
        
        # 计算玩家位置
        position = self.active_players.index(player)
        
        # 获取仍在牌局中的对手
        opponents_in_hand = [p.name for p in self.active_players if not p.is_folded and p != player]
        
        # 调用智能AI决策
        action, amount = player.make_decision(
            current_bet=amount_to_call,
            min_raise=min_raise, 
            pot_size=self.pot,
            community_cards=self.community_cards,
            position=position,
            total_players=len(self.active_players),
            opponents_in_hand=opponents_in_hand
        )
        
        # 确保动作有效
        if action == "raise" and amount < min_raise:
            action = "call"
            amount = amount_to_call
        
        return action, amount
    
    def _display_active_players(self):
        """显示当前在场玩家状态"""
        active_count = len([player for player in self.active_players if not player.is_folded])
        self._emit_event(
            "active_players_displayed",
            public_payload={
                "pot": self.pot,
                "current_bet": self.current_bet,
                "active_count": active_count,
                "total_players": len(self.active_players),
                "players": [
                    {
                        "name": player.name,
                        "chips": player.chips,
                        "current_bet": player.current_bet,
                        "is_dealer": index == self.dealer_position,
                        "is_folded": player.is_folded,
                        "is_all_in": player.is_all_in,
                    }
                    for index, player in enumerate(self.active_players)
                ],
            },
        )

    def _show_realtime_assistance(self, player: HumanPlayer, amount_to_call: int, 
                                  show_full: bool = False):
        """显示实时辅助分析"""
        try:
            from texas_holdem.training.realtime_assistant import get_assistant
            
            if self._assistant is None:
                self._assistant = get_assistant(enabled=True)
            
            # 计算剩余对手数
            num_opponents = len([p for p in self.active_players 
                               if not p.is_folded and p != player])
            
            equity = self._estimate_player_equity(player)
            self._human_advice_equity = None
            if equity is not None:
                advice_key = (
                    self.current_game_id, self.game_phase, player.name,
                    self.pot, self.current_bet, player.chips,
                )
                self._human_advice_equity = (advice_key, equity)

            # Use the same equity and payable call price as post-action feedback.
            analysis = self._assistant.analyze(
                hole_cards=player.hand,
                community_cards=self.community_cards,
                pot_size=self.pot,
                bet_to_call=min(amount_to_call, player.chips),
                player_chips=player.chips,
                position=self.active_players.index(player) if player in self.active_players else 0,
                total_players=len(self.active_players),
                num_opponents=num_opponents,
                equity_override=equity,
            )

            if evaluate_decision is not None and DecisionContext is not None:
                from texas_holdem.training.realtime_assistant import SuggestedAction

                preview_action = "call" if amount_to_call > 0 else "check"
                legal_actions = self._get_legal_actions(player, amount_to_call)
                context = self._build_decision_context(
                    player, preview_action,
                    min(amount_to_call, player.chips) if amount_to_call > 0 else 0,
                    amount_to_call, legal_actions, self._get_min_raise_total(),
                )
                preview = evaluate_decision(context)
                recommendation = preview.recommended_action
                action_labels = {
                    "call": SuggestedAction.CALL,
                    "check": SuggestedAction.CHECK,
                    "fold": SuggestedAction.FOLD,
                    "raise": SuggestedAction.RAISE,
                }
                if recommendation in action_labels and recommendation in legal_actions:
                    analysis.suggested_action = action_labels[recommendation]
                    analysis.reasoning = (
                        "翻前原始胜率只是粗估；建议还考虑牌型可玩性"
                        if "preflop_raw_equity_uncertain" in preview.risk_tags
                        else "根据本手行动评估给出的参考建议"
                    )
            
            # 根据参数决定显示格式
            if show_full:
                print(self._assistant.format_display(analysis, show_full=True))
            else:
                # 默认显示紧凑格式
                compact = self._assistant.format_compact(analysis)
                print(f"\n💡 辅助提示: {compact}")
                
        except ImportError:
            pass  # 辅助模块不可用，静默跳过
        except Exception as e:
            print(f"⚠️ 辅助分析暂时不可用: {e}")
    
    def set_assistant_enabled(self, enabled: bool):
        """设置是否启用实时辅助"""
        self.assistant_enabled = enabled
        status = "已启用" if enabled else "已禁用"
        print(f"📊 实时辅助 {status}")

    def _get_human_action(self, player: HumanPlayer, amount_to_call: int) -> Tuple[str, int]:
        """获取人类玩家动作（支持回退和查看状态）"""
        
        # Large tables keep the decision prompt short; the status command shows every seat.
        if len(getattr(self, "active_players", [])) > 6:
            active_count = sum(not participant.is_folded for participant in self.active_players)
            print(
                f"\n当前彩池: {self.pot} | 最高下注: {self.current_bet} | "
                f"在场玩家: {active_count}/{len(self.active_players)}"
            )
        else:
            self._display_active_players()
        
        print(f"\n🎯 {player.name} 的回合")
        print("-" * 30)
        print(f"🃏 你的手牌: {player.get_hand_string()}")
        print(f"💎 你的筹码: {player.chips}")
        
        if amount_to_call > 0:
            self._show_call_amount(player, amount_to_call)
        
        # 显示实时辅助分析（如果启用）
        if getattr(self, 'assistant_enabled', True):
            self._show_realtime_assistance(player, amount_to_call)
        
        # 确定可选动作
        valid_actions = self._get_legal_actions(player, amount_to_call)
        display_actions = self._get_human_display_actions(valid_actions, amount_to_call)
        from texas_holdem.ui.localization import action_label
        prompt_actions = "/".join(display_actions + [action_label("status"), action_label("avatars")])
        
        print(f"\n可选动作: {', '.join(display_actions)}")
        print(f"附加命令: {action_label('status')} | {action_label('help')} | {action_label('avatars')}")
        
        while True:
            try:
                action = input(f"\n请选择动作 ({prompt_actions}): ").lower().strip()
                action = {
                    "过牌": "check", "跟注": "call", "加注": "raise",
                    "下注": "bet", "弃牌": "fold", "状态": "status",
                    "帮助": "help", "头像": "avatars",
                }.get(action, action)
                
                if action == "status":
                    # 重新显示状态信息
                    self._display_active_players()
                    print(f"\n🎯 {player.name} 的回合")
                    print(f"🃏 你的手牌: {player.get_hand_string()}")
                    print(f"💎 你的筹码: {player.chips}")
                    if amount_to_call > 0:
                        self._show_call_amount(player, amount_to_call)
                    print(f"\n可选动作: {', '.join(display_actions)}")
                    print(f"附加命令: {action_label('status')} | {action_label('help')} | {action_label('avatars')}")
                    continue

                if action == "avatars":
                    if self._terminal_event_renderer is not None:
                        self._terminal_event_renderer.show_avatar_gallery()
                    continue
                
                if action == "help":
                    # 显示详细辅助分析
                    self._show_realtime_assistance(player, amount_to_call, show_full=True)
                    continue

                if action == "bet" and amount_to_call == 0 and "raise" in valid_actions:
                    action = "raise"
                
                if action not in valid_actions:
                    print("❌ 无效动作，请重新选择")
                    continue
                
                # 确认动作（支持回退）
                confirmed_action = self._confirm_action(action, amount_to_call, player)
                if confirmed_action:
                    return confirmed_action
                # 如果不确认，继续循环让用户重新选择
            
            except KeyboardInterrupt:
                print("\n\n游戏被中断，自动弃牌")
                return "fold", 0

    def _get_human_display_actions(self, valid_actions: List[str], amount_to_call: int) -> List[str]:
        """Return terminal action labels while preserving internal action names."""
        from texas_holdem.ui.localization import action_label
        if amount_to_call == 0:
            return [action_label("bet" if action == "raise" else action) for action in valid_actions]
        return [action_label(action) for action in valid_actions]

    @staticmethod
    def _show_call_amount(player: HumanPlayer, amount_to_call: int) -> None:
        if player.chips < amount_to_call:
            print(f"💸 对手下注差额: {amount_to_call}；你可跟注: {player.chips}（全押）")
        else:
            print(f"💸 需要跟注: {amount_to_call}")

    def _confirm_action(self, action: str, amount_to_call: int, player: HumanPlayer) -> Tuple[str, int]:
        """确认玩家动作，支持回退（简化版：简单动作不需要确认）"""
        if action == "fold":
            # 弃牌不需要确认，直接执行
            return "fold", 0
                
        elif action == "check":
            # 过牌不需要确认，直接执行
            return "check", 0
                
        elif action == "call":
            # 跟注需要确认金额
            if amount_to_call == 0:
                return "check", 0
            else:
                actual_call = min(amount_to_call, player.chips)
                if actual_call < amount_to_call:
                    prompt = f"❓ 确认全押跟注 {actual_call} 筹码（对手下注差额 {amount_to_call}）？ (y/n/back): "
                else:
                    prompt = f"❓ 确认跟注 {actual_call} 筹码？ (y/n/back): "
                confirm = input(prompt).lower().strip()
                if confirm in ['y', 'yes', '是', '']:
                    return "call", actual_call
                elif confirm in ('back', '返回'):
                    return None
                else:
                    print("❌ 已取消跟注")
                    return None
                
        elif action == "raise":
            return self._handle_raise_action(amount_to_call, player)
        
        return None

    def _handle_raise_action(self, amount_to_call: int, player: HumanPlayer) -> Tuple[str, int]:
        """处理加注动作，支持回退"""
        action_label = "下注" if amount_to_call == 0 else "加注"
        while True:
            try:
                # 计算加注范围：raise_amount 是目标总下注额，必须与 ActionValidator/game.py mutation 语义一致
                min_raise_total = self._get_min_raise_total()
                max_raise_total = player.chips + player.current_bet  # 目标总下注额最多为已投入 + 剩余筹码
                
                # 检查玩家是否有足够的筹码进行最小加注
                if min_raise_total > max_raise_total:
                    if max_raise_total > self.current_bet:
                        print(f"\n💰 {action_label}设置:")
                        print(f"   当前需跟注: {amount_to_call}")
                        print(f"   最小{action_label}总额: {min_raise_total}")
                        print(f"   你的全押总额: {max_raise_total}")
                        confirm = input(f"❓ 筹码不足以最小{action_label}，确认全押到 {max_raise_total} 筹码？ (y/n/back): ").lower().strip()
                        if confirm in ['y', 'yes', '是', '']:
                            return "raise", max_raise_total
                        if confirm in ('back', '返回'):
                            return None
                        print("❌ 已取消加注")
                        return None
                    print(f"\n❌ 筹码不足以进行{action_label}")
                    print(f"   需要最少: {min_raise_total} 筹码")
                    print(f"   你只有: {max_raise_total} 筹码")
                    print("   建议选择跟注或弃牌")
                    return None
                
                print(f"\n💰 {action_label}设置:")
                print(f"   当前需跟注: {amount_to_call}")
                print(f"   最小{action_label}总额: {min_raise_total}")
                print(f"   最大{action_label}总额: {max_raise_total} (全押)")
                
                # 计算快捷选项
                pot_bet = min(self.pot, max_raise_total)  # 下注彩池大小
                half_pot_bet = min(self.pot // 2, max_raise_total)  # 下注半个彩池
                
                print(f"\n🚀 快捷选项:")
                if half_pot_bet >= min_raise_total:
                    print(f"   h = {half_pot_bet} (半个彩池)")
                if pot_bet >= min_raise_total:
                    print(f"   p = {pot_bet} (彩池大小)")
                print(f"   a = {max_raise_total} (全押)")
                
                raise_input = input(f"请输入加注总额 ({min_raise_total}-{max_raise_total})、快捷选项(h/p/a) 或 'back' 返回: ").strip()
                
                if raise_input.lower() in ('back', '返回'):
                    return None
                
                # 处理快捷选项
                if raise_input.lower() == 'h':
                    if half_pot_bet >= min_raise_total:
                        raise_amount = half_pot_bet
                    else:
                        print(f"❌ 半个彩池金额太小，无法{action_label}")
                        continue
                elif raise_input.lower() == 'p':
                    if pot_bet >= min_raise_total:
                        raise_amount = pot_bet
                    else:
                        print(f"❌ 彩池金额太小，无法{action_label}")
                        continue
                elif raise_input.lower() == 'a':
                    raise_amount = max_raise_total
                else:
                    # 数字输入
                    try:
                        raise_amount = int(raise_input)
                    except ValueError:
                        print("❌ 请输入有效的数字或快捷选项")
                        continue
                
                if raise_amount < min_raise_total or raise_amount > max_raise_total:
                    print(f"❌ {action_label}总额必须在 {min_raise_total}-{max_raise_total} 之间")
                    continue
                
                all_in_text = " (全押)" if raise_amount == max_raise_total else ""
                
                confirm = input(f"❓ 确认{action_label}到 {raise_amount} 筹码{all_in_text}？ (y/n/back): ").lower().strip()
                if confirm in ['y', 'yes', '是', '']:
                    return "raise", raise_amount
                elif confirm in ('back', '返回'):
                    continue  # 返回到加注金额输入
                else:
                    print("❌ 已取消加注")
                    return None
                    
            except ValueError:
                # ValueError已在上面处理，这里不应该再有
                print("❌ 输入处理错误")
                continue
    
    def _showdown(self):
        """摊牌比较"""
        # 获取所有未弃牌的玩家（摊牌阶段至少有2个玩家）
        remaining_players = [p for p in self.active_players if not p.is_folded]
        self._emit_event(
            "showdown_started",
            public_payload={
                "phase": self.game_phase,
                "pot": self.pot,
                "community_cards": [str(card) for card in self.community_cards],
                "player_names": [p.name for p in remaining_players],
            },
        )
        
        print(f"\n参与摊牌的玩家: {', '.join([p.name for p in remaining_players])}")
        
        # 显示所有玩家的手牌和牌型
        player_hands = []
        for player in remaining_players:
            all_cards = player.hand + self.community_cards
            hand_rank, _ = HandEvaluator.evaluate_hand(all_cards)
            hand_desc = HandEvaluator.get_hand_description(all_cards)
            player_hands.append((player, all_cards, hand_rank, hand_desc))
            self._emit_event(
                "player_hand_revealed",
                public_payload={
                    "player_name": player.name,
                    "hole_cards": [str(card) for card in player.hand],
                    "hand_description": hand_desc,
                },
            )
        
        # 找出获胜者
        winners = self._find_winners(player_hands)
        
        # 分配彩池
        winner_names = [w.name for w in winners]
        folded_names = [p.name for p in self.active_players if p.is_folded]
        self._emit_winner_announced_event(winner_names, "showdown")

        # 使用边池管理器分配奖金
        main_pot, side_pots = self.side_pot_manager.calculate_side_pots(folded_names)

        # 为每个边池找出有资格的获胜者
        side_pot_winners = {}
        for sp in side_pots:
            eligible_winners = [w for w in winners if w.name in sp.eligible_players]
            if not eligible_winners:
                eligible_winners = winners  # fallback
            side_pot_winners[f"side_{sp.pot_id}"] = [w.name for w in eligible_winners]

        # 主池获胜者：只有有资格参与主池的玩家才能赢得主池
        # 有资格的玩家 = 未弃牌且未全押，或全押金额等于最大贡献额
        all_in_amounts = self.side_pot_manager.all_in_players  # {name: amount}
        max_contribution = max(self.side_pot_manager.contributions.values()) if self.side_pot_manager.contributions else 0
        main_eligible_names = [
            p.name for p in self.active_players
            if not p.is_folded and (
                p.name not in all_in_amounts or
                all_in_amounts[p.name] >= max_contribution
            )
        ]
        if main_eligible_names:
            # 从有资格的玩家中找最强手牌
            main_eligible_hands = [(p, cards, rank, desc) for p, cards, rank, desc in player_hands
                                   if p.name in main_eligible_names]
            main_winners = self._find_winners(main_eligible_hands) if main_eligible_hands else winners
        else:
            main_winners = winners
        side_pot_winners["main"] = [w.name for w in main_winners]

        winnings_map = self.side_pot_manager.distribute_winnings(side_pot_winners, folded_names)

        # 如果边池管理器没有记录（兼容旧逻辑），回退到简单分配
        if sum(winnings_map.values()) == 0:
            win_amount = self.pot // len(winners)
            remainder = self.pot % len(winners)
            winnings_map = {}
            for i, w in enumerate(winners):
                winnings_map[w.name] = win_amount + (1 if i < remainder else 0)

        # 记录最终结果
        final_hands = []

        for player in self.active_players:
            if not player.is_folded:
                # 找到对应的手牌信息
                hand_info = None
                for p, cards, rank, desc in player_hands:
                    if p.name == player.name:
                        hand_info = (cards, desc)
                        break

                winnings = winnings_map.get(player.name, 0)
                if winnings > 0:
                    player.chips += winnings
                    self._emit_pot_distributed_event(player.name, winnings, "showdown")
                
                final_hands.append({
                    'player_name': player.name,
                    'hole_cards': [str(card) for card in player.hand],
                    'final_chips': player.chips,
                    'hand_rank': hand_info[1] if hand_info else '',
                    'winnings': winnings
                })
            else:
                # 弃牌的玩家
                final_hands.append({
                    'player_name': player.name,
                    'hole_cards': [str(card) for card in player.hand],
                    'final_chips': player.chips,
                    'hand_rank': '已弃牌',
                    'winnings': 0
                })
        
        # 记录AI风格
        self._record_ai_styles()
        
        # 完成游戏记录
        outcome_metadata = self._build_outcome_metadata(
            ended_by_fold=False,
            went_to_showdown=True,
            winner_reason="showdown",
        )
        self._completed_replay_record = self.history_manager.get_current_game_record()
        self.history_manager.finish_game(
            final_hands,
            self.pot,
            winner_names,
            outcome_metadata=outcome_metadata,
        )
        self._emit_hand_completed_event(winner_names, final_hands, outcome_metadata)
        
        # 更新风格统计
        for player in self.active_players:
            player_style_analyzer.update_hand_participation(player.name, True)
            if player.name in winner_names:
                player_style_analyzer.update_showdown(player.name, True)
            elif not player.is_folded:  # 参与了摊牌但没赢
                player_style_analyzer.update_showdown(player.name, False)
        
        # 保存风格数据
        player_style_analyzer.save_stats()
        
        # 显示即时复盘（仅对人类玩家）
        self._show_instant_replay(final_hands, winner_names)
    
    def _handle_early_winner(self):
        """处理提前获胜的情况（其他玩家都弃牌）"""
        # 获取所有未弃牌的玩家
        remaining_players = [p for p in self.active_players if not p.is_folded]
        
        if len(remaining_players) == 1:
            winner = remaining_players[0]

            # 将彩池给获胜者
            winner.chips += self.pot

            # 记录最终结果
            final_hands = []
            for player in self.active_players:
                winnings = self.pot if player.name == winner.name else 0
                final_hands.append({
                    'player_name': player.name,
                    'hole_cards': [str(card) for card in player.hand],
                    'final_chips': player.chips,
                    'hand_rank': '其他玩家弃牌' if player.name == winner.name else '已弃牌',
                    'winnings': winnings
                })

            # 记录AI风格
            self._record_ai_styles()
            
            # 完成游戏记录
            outcome_metadata = self._build_outcome_metadata(
                ended_by_fold=True,
                went_to_showdown=False,
                winner_reason="fold",
            )
            self._completed_replay_record = self.history_manager.get_current_game_record()
            self.history_manager.finish_game(
                final_hands,
                self.pot,
                [winner.name],
                outcome_metadata=outcome_metadata,
            )
            self._emit_winner_announced_event([winner.name], "fold")
            self._emit_pot_distributed_event(winner.name, self.pot, "fold")
            self._emit_hand_completed_event([winner.name], final_hands, outcome_metadata)

            # 更新风格统计
            for player in self.active_players:
                player_style_analyzer.update_hand_participation(player.name, True)
                if player.name == winner.name:
                    player_style_analyzer.update_showdown(player.name, True)

            # 保存风格数据
            player_style_analyzer.save_stats()
            
            # 显示即时复盘（仅对人类玩家）
            self._show_instant_replay(final_hands, [winner.name])

            # 显示最终筹码状态
            print(f"\n{winner.name} 当前筹码: {winner.chips}")
        elif len(remaining_players) == 0:
            # 所有玩家都弃牌的情况 - 这是一个边缘情况，最后弃牌的玩家应该是获胜者
            print("⚠️ 所有玩家都已弃牌，游戏无效")
            print("💰 彩池将被平分给所有玩家")
            
            # 平分彩池
            if self.pot > 0:
                per_player = self.pot // len(self.active_players)
                remainder = self.pot % len(self.active_players)
            else:
                per_player = 0
                remainder = 0
            
            final_hands = []
            for i, player in enumerate(self.active_players):
                winnings = per_player + (1 if i < remainder else 0)
                player.chips += winnings
                final_hands.append({
                    'player_name': player.name,
                    'hole_cards': [str(card) for card in player.hand],
                    'final_chips': player.chips,
                    'hand_rank': '全部弃牌',
                    'winnings': winnings
                })
                self._emit_pot_distributed_event(player.name, winnings, "invalid_all_fold")

            # 记录AI风格
            self._record_ai_styles()
            
            # 完成游戏记录
            outcome_metadata = self._build_outcome_metadata(
                ended_by_fold=True,
                went_to_showdown=False,
                winner_reason="invalid_all_fold",
            )
            self.history_manager.finish_game(
                final_hands,
                self.pot,
                [],
                outcome_metadata=outcome_metadata,
            )
            self._emit_hand_completed_event([], final_hands, outcome_metadata)
            
            # 更新风格统计
            for player in self.active_players:
                player_style_analyzer.update_hand_participation(player.name, True)
            
            # 保存风格数据
            player_style_analyzer.save_stats()
        else:
            print(f"错误：找到 {len(remaining_players)} 个获胜者，应该只有1个")
            # 显示剩余玩家信息用于调试
            for player in remaining_players:
                print(f"  - {player.name} (弃牌状态: {player.is_folded})")

    def _emit_hand_completed_event(
        self,
        winner_names: List[str],
        final_hands: List[Dict[str, Any]],
        outcome_metadata: Dict[str, Any],
    ) -> None:
        """Emit public hand completion data without leaking hole cards."""
        public_final_hands = [
            {
                "player_name": hand["player_name"],
                "final_chips": hand["final_chips"],
                "hand_rank": hand["hand_rank"],
                "winnings": hand["winnings"],
            }
            for hand in final_hands
        ]
        self._emit_event(
            "hand_completed",
            public_payload={
                "winner_names": list(winner_names),
                "total_pot": self.pot,
                "final_hands": public_final_hands,
                "outcome_metadata": outcome_metadata,
            },
        )

    def _emit_winner_announced_event(self, winner_names: List[str], winner_reason: str) -> None:
        """Emit public winner announcement data without leaking private cards."""
        self._emit_event(
            "winner_announced",
            public_payload={
                "winner_names": list(winner_names),
                "winner_reason": winner_reason,
                "total_pot": self.pot,
            },
        )

    def _emit_pot_distributed_event(self, player_name: str, winnings: int, winner_reason: str) -> None:
        """Emit public pot distribution data without leaking private cards."""
        self._emit_event(
            "pot_distributed",
            public_payload={
                "player_name": player_name,
                "winnings": winnings,
                "winner_reason": winner_reason,
                "total_pot": self.pot,
            },
        )
    
    def _build_outcome_metadata(self, ended_by_fold: bool, went_to_showdown: bool,
                                winner_reason: str) -> Dict[str, Any]:
        """Build explicit hand outcome metadata for history and benchmark metrics."""
        community_count = len(self.community_cards)
        street_reach = {
            player.name: {
                "saw_flop": community_count >= 3,
                "saw_turn": community_count >= 4,
                "saw_river": community_count >= 5,
            }
            for player in self.active_players
        }
        return {
            "ended_by_fold": ended_by_fold,
            "went_to_showdown": went_to_showdown,
            "winner_reason": winner_reason,
            "street_reach": street_reach,
            "blind_positions": dict(self.current_blind_metadata.get("blind_positions", {})),
            "forced_blinds": [dict(blind) for blind in self.current_blind_metadata.get("forced_blinds", [])],
        }

    def _update_ai_opponent_models(self, player_name: str, action: str, amount: int):
        """更新所有AI的对手建模"""
        from texas_holdem.ai.smart_ai_system import ai_engine_manager
        
        # 更新所有AI引擎的对手模型
        for player in self.active_players:
            if isinstance(player, AIPlayer) and player.name != player_name:
                engine = ai_engine_manager.get_engine(player.name)
                engine.update_opponent_model(player_name, action, amount)
    
    def _show_instant_replay(self, final_hands: List[Dict], winner_names: List[str]):
        """
        显示即时复盘（仅对人类玩家）
        
        Args:
            final_hands: 最终手牌信息列表
            winner_names: 获胜者名单
        """
        # 检查是否有人类玩家
        human_players = [p for p in self.active_players if p.player_type == "human"]
        if not human_players:
            return  # 没有人类玩家，跳过复盘
        
        # 检查是否启用复盘功能
        if not getattr(self, 'replay_enabled', True):
            return
        
        try:
            from texas_holdem.history.instant_replay import get_replay_analyzer
            
            # 获取当前游戏记录
            game_record = (
                getattr(self, "_completed_replay_record", None)
                or self.history_manager.get_current_game_record()
            )
            self._completed_replay_record = None
            if not game_record:
                return
            
            # 补充必要信息
            game_record['final_hands'] = final_hands
            game_record['winner_names'] = winner_names
            
            analyzer = get_replay_analyzer()
            coach = self._get_hand_coach()
            
            # 为每个人类玩家显示复盘
            for player in human_players:
                if coach is not None:
                    coach_summary = coach.build_summary(game_record, player.name)
                    print("\n" + coach_summary.format_text())

                analysis = analyzer.analyze_hand(game_record, player.name)
                
                # 询问是否查看复盘
                print("\n" + "-" * 40)
                try:
                    show_replay = input("📋 是否查看本局复盘? (y/n/d详细): ").lower().strip()
                    
                    if show_replay == 'y':
                        print(analyzer.format_summary(analysis))
                    elif show_replay == 'd':
                        print(analyzer.format_detailed(analysis))
                    else:
                        # 显示简短评分
                        score = analysis.overall_score
                        emoji = "🌟" if score >= 80 else "✅" if score >= 60 else "⚠️"
                        print(f"{emoji} 本局评分: {score}/100")
                except EOFError:
                    pass  # 非交互模式跳过
                except KeyboardInterrupt:
                    pass  # 用户跳过
                    
        except ImportError:
            pass  # 复盘模块不可用
        except Exception as e:
            print(f"⚠️ 复盘分析暂时不可用: {e}")

    def _get_hand_coach(self):
        """Return the optional hand-end coach, or None if unavailable."""
        try:
            from texas_holdem.training.hand_coach import HandCoach

            return HandCoach()
        except Exception:
            return None
    
    def set_replay_enabled(self, enabled: bool):
        """设置是否启用即时复盘"""
        self.replay_enabled = enabled
        status = "已启用" if enabled else "已禁用"
        print(f"📋 即时复盘 {status}")

    def _record_ai_styles(self):
        """记录AI玩家的实际分配风格"""
        from texas_holdem.ai.smart_ai_system import ai_engine_manager
        
        standard_styles = ai_engine_manager.get_all_ai_styles()
        ai_styles_str = {
            player.name: player.archetype_name
            for player in self.players
            if isinstance(player, AIPlayer) and player.ai_mode == "advanced"
            and player.archetype_name is not None
        }
        ai_styles_str.update({
            player.name: standard_styles[player.name].code
            for player in self.players
            if isinstance(player, AIPlayer) and player.ai_mode == "standard"
            and player.name in standard_styles
        })
        if ai_styles_str:
            self.history_manager.record_ai_styles(ai_styles_str)
    
    def _find_winners(self, player_hands: List[Tuple]) -> List[Player]:
        """找出获胜者"""
        if not player_hands:
            return []
        
        # 不依赖排序，而是逐个比较找出获胜者
        if len(player_hands) == 1:
            return [player_hands[0][0]]
        
        # 找出最强的手牌
        best_hands = [player_hands[0]]  # 从第一个开始
        
        for i in range(1, len(player_hands)):
            current_player, current_cards, current_rank, current_desc = player_hands[i]
            best_player, best_cards, best_rank, best_desc = best_hands[0]
            
            comparison = HandEvaluator.compare_hands(current_cards, best_cards)
            
            if comparison > 0:
                # 当前手牌更强，清空之前的获胜者
                best_hands = [(current_player, current_cards, current_rank, current_desc)]
            elif comparison == 0:
                # 平局，添加到获胜者列表
                best_hands.append((current_player, current_cards, current_rank, current_desc))
            # comparison < 0: 当前手牌更弱，不做任何操作
        
        # 返回所有获胜者
        return [player for player, cards, rank, desc in best_hands]
    
    def _move_dealer(self):
        """移动庄家位置"""
        self.dealer_position = (self.dealer_position + 1) % len(self.players)
    
    def _display_game_state(self):
        """显示游戏状态"""
        self._emit_event(
            "game_state_displayed",
            public_payload={
                "pot": self.pot,
                "current_bet": self.current_bet,
                "players": [
                    {
                        "name": player.name,
                        "chips": player.chips,
                        "current_bet": player.current_bet,
                        "is_dealer": index == self.dealer_position,
                        "is_folded": player.is_folded,
                        "is_all_in": player.is_all_in,
                    }
                    for index, player in enumerate(self.active_players)
                ],
            },
        )
    
    def _display_community_cards(self):
        """显示公共牌"""
        if self.community_cards:
            self._emit_event(
                "community_cards_displayed",
                public_payload={"community_cards": [str(card) for card in self.community_cards]},
            )
    
    def is_game_over(self) -> bool:
        """检查游戏是否结束"""
        players_with_chips = [p for p in self.players if p.chips > 0]
        return len(players_with_chips) <= 1
    
    def get_final_standings(self) -> List[Player]:
        """获取最终排名"""
        return sorted(self.players, key=lambda p: p.chips, reverse=True)


class _LegacyHumanGameDecisionProvider(DecisionProvider):
    """Adapter that keeps the existing rich human CLI UX behind DecisionProvider."""

    def __init__(self, game: TexasHoldemGame, player: Player):
        self.game = game
        self.player = player

    def decide(self, state: GameStateSnapshot) -> ActionResponse:
        try:
            action, amount = self.game._get_human_action(self.player, state.amount_to_call)
            return ActionResponse(
                action=action,
                amount=amount,
                metadata={"provider": self.__class__.__name__},
                raw_response=(action, amount),
            )
        except Exception as exc:
            fallback = "check" if "check" in state.legal_actions else "fold"
            return ActionResponse(
                action=fallback,
                amount=0,
                metadata={"provider": self.__class__.__name__, "fallback": True},
                error=str(exc),
            )

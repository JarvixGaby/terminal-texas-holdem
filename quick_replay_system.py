# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 快速复盘系统
简化的复盘界面，直接从第一轮开始，在手牌旁显示胜率
"""

import os
from typing import List, Dict
from game_history import GameRecord, GameHistoryManager
from optimized_odds_calculator import OddsCalculator, PerformanceLevel
from player_styles import player_style_analyzer


class QuickReplaySystem:
    """快速复盘系统"""
    
    def __init__(self, game_record: GameRecord):
        """
        初始化快速复盘系统
        
        Args:
            game_record: 要复盘的游戏记录
        """
        self.game_record = game_record
        self.odds_calculator = OddsCalculator(PerformanceLevel.NORMAL)  # 快速计算
        self.current_phase_index = 0
        self.current_action_index = 0
        
    def clear_screen(self):
        """清屏"""
        if os.name == 'nt':
            os.system('cls')
        elif os.environ.get('TERM'):
            os.system('clear')
    
    def is_key_action(self, action):
        """判断是否为关键动作"""
        # 关键动作包括：raise, 新阶段的第一个动作, 最后一个动作
        return action.action in ["raise", "bet"]  # bet在有些情况下也算关键动作
    
    def show_state_until_next_key_action(self):
        """显示当前状态直到下一个关键动作"""
        if self.current_phase_index >= len(self.game_record.phases):
            return
        
        current_phase = self.game_record.phases[self.current_phase_index]
        
        # 显示阶段信息
        self.show_phase_header(current_phase)
        
        # 显示手牌和牌型
        self.show_players_with_odds(current_phase.community_cards)
        
        # 显示动作序列直到关键动作
        self.show_actions_until_key_action(current_phase)
        
        # 显示当前位置信息
        self.show_progress_info()
    
    def show_phase_header(self, phase):
        """显示阶段头部信息"""
        round_names = {
            "preflop": "翻牌前",
            "flop": "翻牌", 
            "turn": "转牌",
            "river": "河牌"
        }
        round_name = round_names.get(phase.phase, phase.phase.upper())
        
        print("=" * 70)
        print(f"🎯 {round_name}")
        print("=" * 70)
        
        # 显示公共牌
        if phase.community_cards:
            cards_display = " ".join(phase.community_cards)
            print(f"🃏 公共牌: {cards_display}")
        else:
            print("🃏 公共牌: 尚未发出")
        
        print(f"💰 彩池: {phase.pot_size}")
    
    def show_actions_until_key_action(self, phase):
        """显示动作序列直到遇到关键动作或结束"""
        if not phase.actions:
            return
        
        print(f"\n🎬 动作序列:")
        print("-" * 50)
        
        start_index = self.current_action_index
        actions_shown = []
        key_action_found = False
        
        # 从当前动作开始，展示到下一个关键动作
        for i in range(start_index, len(phase.actions)):
            action = phase.actions[i]
            action_desc = self.get_action_description(action)
            chips_change = f" ({action.chips_before} → {action.chips_after})"
            
            actions_shown.append(f"  {action.player_name}: {action_desc}{chips_change}")
            
            # 如果这是关键动作，标记并停止
            if self.is_key_action(action):
                actions_shown[-1] += " ⭐ 关键动作"
                key_action_found = True
                break
        
        # 显示动作
        for action_line in actions_shown:
            print(action_line)
        
        if not key_action_found and start_index < len(phase.actions):
            # 如果没有找到关键动作，显示剩余所有动作
            remaining_actions = len(phase.actions) - start_index - len(actions_shown)
            if remaining_actions > 0:
                print(f"  ... 还有 {remaining_actions} 个普通动作")
    
    def show_progress_info(self):
        """显示进度信息"""
        current_phase = self.game_record.phases[self.current_phase_index]
        phase_progress = f"{self.current_action_index + 1}/{len(current_phase.actions)}" if current_phase.actions else "0/0"
        total_progress = f"{self.current_phase_index + 1}/{len(self.game_record.phases)}"
        
        print(f"\n📍 进度: 阶段 {total_progress}, 动作 {phase_progress}")
    
    def advance_to_next_key_action(self):
        """前进到下一个关键动作"""
        if self.current_phase_index >= len(self.game_record.phases):
            return
        
        # 从当前位置开始寻找下一个关键动作
        found_key_action = False
        
        # 先在当前阶段寻找
        current_phase = self.game_record.phases[self.current_phase_index]
        for i in range(self.current_action_index, len(current_phase.actions)):
            if self.is_key_action(current_phase.actions[i]):
                self.current_action_index = i + 1  # 移动到关键动作之后
                found_key_action = True
                break
        
        # 如果当前阶段没有找到，继续在后续阶段寻找
        if not found_key_action:
            for phase_idx in range(self.current_phase_index + 1, len(self.game_record.phases)):
                phase = self.game_record.phases[phase_idx]
                for action_idx, action in enumerate(phase.actions):
                    if self.is_key_action(action):
                        self.current_phase_index = phase_idx
                        self.current_action_index = action_idx + 1
                        found_key_action = True
                        break
                if found_key_action:
                    break
        
        # 如果完全没有找到关键动作，移动到最后
        if not found_key_action:
            self.current_phase_index = len(self.game_record.phases)
    
    def go_back_to_previous_key_action(self):
        """回退到上一个关键动作"""
        # 在当前阶段向前寻找关键动作
        if self.current_action_index > 0:
            for i in range(self.current_action_index - 1, -1, -1):
                current_phase = self.game_record.phases[self.current_phase_index]
                if self.is_key_action(current_phase.actions[i]):
                    self.current_action_index = i
                    return
        
        # 当前阶段没有更早的关键动作，回到上一阶段
        if self.current_phase_index > 0:
            self.current_phase_index -= 1
            if self.current_phase_index < len(self.game_record.phases):
                prev_phase = self.game_record.phases[self.current_phase_index]
                # 从上一阶段的最后开始寻找关键动作
                for i in range(len(prev_phase.actions) - 1, -1, -1):
                    if self.is_key_action(prev_phase.actions[i]):
                        self.current_action_index = i + 1
                        return
                # 如果没有关键动作，就设为阶段开始
                self.current_action_index = 0
        else:
            print("\n⚠️  已经是第一个动作了")
            input("按回车键继续...")

    def show_player_styles(self):
        """显示所有玩家的详细风格信息"""
        print("\n" + "=" * 60)
        print("👥 玩家风格分析")
        print("=" * 60)
        
        for hand in self.game_record.final_hands:
            player_name = hand.player_name
            style = self._get_player_style(player_name)
            stats_summary = player_style_analyzer.get_player_stats_summary(player_name)
            
            print(f"\n🎮 {player_name}:")
            print(f"   风格: {style.emoji} {style.display_name}")
            print(f"   描述: {style.description}")
            
            # 显示统计摘要
            lines = stats_summary.split('\n')
            for line in lines[1:]:  # 跳过第一行（已经显示了风格）
                if line.strip():
                    print(f"   {line}")
        
        print("\n" + "=" * 60)
        print("风格说明:")
        print("🪨 超紧手 - 只玩最强的牌    🎯 紧凶 - 有选择性但积极")
        print("🔥 松凶 - 参与多且激进      📞 跟注站 - 很少弃牌")
        print("🦈 鲨鱼 - 高手玩家          🐟 鱼 - 新手玩家") 
        print("🤪 疯子 - 极度疯狂          ⚖️ 平衡 - 各方面均衡")
    
    def start_replay(self):
        """开始快速复盘"""
        self.clear_screen()
        print("=" * 70)
        print("🎬 快速复盘模式")
        print("=" * 70)
        print()
        print("控制说明:")
        print("• 回车键: 下一个关键动作 (raise/bet)")
        print("• 'b' + 回车: 上一个关键动作")
        print("• 's' + 回车: 查看玩家风格")
        print("• 'q' + 回车: 退出复盘")
        print("\n💡 复盘会自动停在加注(raise)等关键决策点")
        print()
        input("按回车键开始复盘...")
        
        # 直接开始逐步复盘
        self.replay_loop()
    
    def replay_loop(self):
        """复盘主循环 - 按关键动作进行"""
        self.current_phase_index = 0
        self.current_action_index = 0
        
        while True:
            self.clear_screen()
            
            if self.current_phase_index < len(self.game_record.phases):
                # 显示当前状态到下一个关键动作
                self.show_state_until_next_key_action()
                
                # 处理用户输入
                user_input = input("操作 (回车=下一个关键动作, b=上一步, s=玩家风格, q=退出): ").strip().lower()
                user_input = {"退出": "q", "上一步": "b", "风格": "s"}.get(user_input, user_input)
                
                if user_input == 'q':
                    break
                elif user_input == 'b':
                    self.go_back_to_previous_key_action()
                elif user_input == 's':
                    self.show_player_styles()
                    input("\n按回车键继续...")
                else:  # 回车或其他输入都前进到下一个关键动作
                    self.advance_to_next_key_action()
            else:
                # 显示最终结果
                self.show_final_result()
                
                # 最终结果页面的控制
                user_input = input("\n操作 (b=重新开始, q=退出): ").strip().lower()
                user_input = {"退出": "q", "重新开始": "b"}.get(user_input, user_input)
                
                if user_input == 'q':
                    break
                elif user_input == 'b':
                    self.current_phase_index = 0
                    self.current_action_index = 0
                else:
                    break
    
    def show_current_state(self, phase):
        """显示当前状态"""
        
        # 显示轮次信息
        round_names = {
            "preflop": "翻牌前",
            "flop": "翻牌", 
            "turn": "转牌",
            "river": "河牌"
        }
        round_name = round_names.get(phase.phase, phase.phase.upper())
        
        print("=" * 70)
        print(f"🎯 第 {self.current_phase_index + 1} 轮：{round_name}")
        print("=" * 70)
        
        # 显示公共牌
        if phase.community_cards:
            cards_display = " ".join(phase.community_cards)
            print(f"🃏 公共牌: {cards_display}")
        else:
            print("🃏 公共牌: 尚未发出")
        
        print(f"💰 彩池: {phase.pot_size}")
        
        # 显示玩家手牌信息（根据阶段调整标题）
        if phase.community_cards:
            print(f"\n👥 玩家手牌和牌型:")
        else:
            print(f"\n👥 玩家手牌:")
        print("-" * 70)
        
        self.show_players_with_odds(phase.community_cards)
        
        # 显示当前阶段的动作
        if phase.actions:
            print(f"\n🎬 {round_name} 阶段动作:")
            print("-" * 50)
            
            # 根据当前进度显示动作
            actions_to_show = self.get_actions_to_show(phase.actions)
            
            for i, action in enumerate(actions_to_show):
                action_desc = self.get_action_description(action)
                chips_change = f" ({action.chips_before} → {action.chips_after})"
                marker = " ← 当前" if i == len(actions_to_show) - 1 else ""
                print(f"  {action.player_name}: {action_desc}{chips_change}{marker}")
                
            if len(actions_to_show) < len(phase.actions):
                print(f"  ... 还有 {len(phase.actions) - len(actions_to_show)} 个动作")
    
    def show_players_with_odds(self, community_cards_str: List[str]):
        """显示玩家手牌和胜率（根据阶段决定是否显示胜率和牌型）"""
        try:
            # 转换字符串为Card对象
            community_cards = []
            if community_cards_str:
                for card_str in community_cards_str:
                    community_cards.append(GameHistoryManager.card_from_string(card_str))
            
            # 判断当前阶段
            current_phase = self.game_record.phases[self.current_phase_index] if self.current_phase_index < len(self.game_record.phases) else None
            is_preflop = not community_cards  # 没有公共牌就是翻牌前
            
            # 获取玩家状态
            player_status = {}  # 存储每个玩家在当前阶段的状态
            
            # 从所有之前的阶段（包括当前阶段）中收集弃牌状态
            for phase_idx in range(self.current_phase_index + 1):
                if phase_idx < len(self.game_record.phases):
                    phase = self.game_record.phases[phase_idx]
                    if phase.actions:
                        for action in phase.actions:
                            if action.action == "fold":
                                player_status[action.player_name] = "已弃牌"
            
            # 如果是翻牌后，计算胜率和牌型
            odds = {}
            hand_types = {}
            if not is_preflop:
                # 获取活跃玩家用于胜率计算
                player_hands = []
                active_players = []
                
                for hand in self.game_record.final_hands:
                    is_folded_in_current_phase = player_status.get(hand.player_name) == "已弃牌"
                    if not is_folded_in_current_phase:
                        hole_cards = []
                        for card_str in hand.hole_cards:
                            hole_cards.append(GameHistoryManager.card_from_string(card_str))
                        player_hands.append(hole_cards)
                        active_players.append(hand)
                
                # 计算胜率
                if len(player_hands) > 1:
                    odds = self.odds_calculator.calculate_postflop_odds(player_hands, community_cards)
                elif len(player_hands) == 1:
                    odds = {"玩家1": 100.0}
                
                # 计算每个活跃玩家的当前牌型
                from hand_evaluator import HandEvaluator
                from card import Card, Suit, Rank
                
                for i, hand in enumerate(active_players):
                    hole_cards = []
                    for card_str in hand.hole_cards:
                        hole_cards.append(GameHistoryManager.card_from_string(card_str))
                    
                    # 计算当前阶段的牌型（仅使用手牌+当前公共牌）
                    current_cards = hole_cards + community_cards
                    if len(current_cards) >= 5:
                        try:
                            # 使用当前可用的牌计算最佳5张牌组合
                            best_hand_rank, best_five_cards = HandEvaluator.evaluate_hand(current_cards)
                            
                            # 根据阶段显示描述性牌型
                            if len(community_cards) == 3:  # 翻牌
                                hand_types[hand.player_name] = f"{best_hand_rank.display}"
                            elif len(community_cards) == 4:  # 转牌
                                hand_types[hand.player_name] = f"{best_hand_rank.display}"
                            else:  # 河牌
                                hand_types[hand.player_name] = f"{best_hand_rank.display}"
                        except:
                            # 如果评估失败，使用当前可能的最高牌型描述
                            if len(community_cards) == 3:  # 翻牌
                                hand_types[hand.player_name] = "当前牌型"
                            elif len(community_cards) == 4:  # 转牌
                                hand_types[hand.player_name] = "当前牌型"
                            else:  # 河牌
                                hand_types[hand.player_name] = "当前牌型"
            
            # 显示结果
            for i, hand in enumerate(self.game_record.final_hands):
                hole_cards_str = " ".join(hand.hole_cards)
                
                # 检查玩家在当前阶段的状态
                is_folded_in_current_phase = player_status.get(hand.player_name) == "已弃牌"
                
                if is_folded_in_current_phase:
                    status = "❌ 已弃牌"
                    extra_info = ""
                else:
                    status = "🎮"
                    extra_info = ""
                    
                    if is_preflop:
                        # 翻牌前：只显示手牌，不显示胜率
                        extra_info = ""
                    else:
                        # 翻牌后：显示牌型和胜率
                        hand_type = hand_types.get(hand.player_name, "计算中...")
                        
                        # 找到该玩家在胜率计算中的索引
                        active_index = -1
                        active_players_list = [h for h in self.game_record.final_hands 
                                             if player_status.get(h.player_name) != "已弃牌"]
                        
                        for j, active_hand in enumerate(active_players_list):
                            if active_hand.player_name == hand.player_name:
                                active_index = j
                                break
                        
                        if active_index >= 0:
                            player_key = f"玩家{active_index + 1}"
                            if player_key in odds:
                                odds_str = f"{odds[player_key]:.1f}%"
                            else:
                                odds_str = "计算中..."
                        else:
                            odds_str = "计算中..."
                        
                        extra_info = f" | {hand_type} | 📊 {odds_str}"
                
                # 显示获胜者标记和玩家风格
                winner_mark = " 🏆" if hand.is_winner else ""
                
                # 获取玩家风格（优先使用记录的AI风格）
                style = self._get_player_style(hand.player_name)
                style_info = f" [{style.display_name}]"
                
                print(f"  {status} {hand.player_name}{style_info}: {hole_cards_str}{extra_info}{winner_mark}")
                
        except Exception as e:
            # 如果计算失败，仍然显示手牌
            print("  牌型计算中...")
            for hand in self.game_record.final_hands:
                hole_cards_str = " ".join(hand.hole_cards)
                status = "❌ 已弃牌" if hand.hand_rank == '已弃牌' else "🎮"
                winner_mark = " 🏆" if hand.is_winner else ""
                
                # 获取玩家风格（优先使用记录的AI风格）
                style = self._get_player_style(hand.player_name)
                style_info = f" {style.emoji}"
                
                print(f"  {status} {hand.player_name}{style_info}: {hole_cards_str}{winner_mark}")
    
    def get_actions_to_show(self, all_actions):
        """根据当前进度获取要显示的动作"""
        if self.current_phase_index < len(self.game_record.phases) - 1:
            # 不是最后一个阶段，显示所有动作
            return all_actions
        else:
            # 最后一个阶段，根据current_action_index限制显示
            return all_actions[:self.current_action_index + 1]
    
    def get_action_description(self, action) -> str:
        """获取动作描述"""
        if action.action == "fold":
            return "弃牌"
        elif action.action == "check":
            return "过牌"
        elif action.action == "call":
            return f"跟注 {action.amount}"
        elif action.action == "raise":
            return f"加注 {action.amount}"
        else:
            return action.action
    
    def go_forward(self):
        """前进一步"""
        if self.current_phase_index >= len(self.game_record.phases):
            return
            
        current_phase = self.game_record.phases[self.current_phase_index]
        
        if self.current_action_index < len(current_phase.actions) - 1:
            # 在当前阶段内前进
            self.current_action_index += 1
        else:
            # 进入下一阶段
            if self.current_phase_index < len(self.game_record.phases) - 1:
                self.current_phase_index += 1
                self.current_action_index = 0
    
    def go_back(self):
        """后退一步"""
        if self.current_action_index > 0:
            # 在当前阶段内后退
            self.current_action_index -= 1
        else:
            # 回到上一阶段
            if self.current_phase_index > 0:
                self.current_phase_index -= 1
                prev_phase = self.game_record.phases[self.current_phase_index]
                self.current_action_index = max(0, len(prev_phase.actions) - 1)
    
    def show_final_result(self):
        """显示最终结果"""
        self.clear_screen()
        print("=" * 70)
        print("🏁 复盘结束")
        print("=" * 70)
        
        print(f"游戏时间: {self.game_record.date_time}")
        print(f"总彩池: {self.game_record.total_pot}")
        print(f"获胜者: {', '.join(self.game_record.winner_names)}")
        
        print("\n最终结果:")
        print("-" * 50)
        
        # 分别显示摊牌玩家和弃牌玩家
        showdown_players = []
        folded_players = []
        
        for hand in self.game_record.final_hands:
            if hand.hand_rank == '已弃牌':
                folded_players.append(hand)
            else:
                showdown_players.append(hand)
        
        # 先显示参与摊牌的玩家
        if showdown_players:
            print("🎮 参与摊牌:")
            for hand in showdown_players:
                hole_cards = " ".join(hand.hole_cards)
                winnings = f"+{hand.winnings}" if hand.winnings > 0 else str(hand.winnings)
                winner_mark = " 🏆" if hand.is_winner else ""
                
                print(f"  {hand.player_name}: {hole_cards} - {hand.hand_rank}")
                print(f"    盈亏: {winnings}{winner_mark}")
        
        # 再显示弃牌玩家
        if folded_players:
            print("\n❌ 弃牌玩家:")
            for hand in folded_players:
                hole_cards = " ".join(hand.hole_cards)
                print(f"  {hand.player_name}: {hole_cards} - 已弃牌")
                print(f"    盈亏: 0")
        
        print()
        input("复盘结束，按回车键返回...")
    
    def _get_player_style(self, player_name: str):
        """获取玩家风格（优先使用记录的AI实际风格）"""
        from player_styles import PlayerStyle, player_style_analyzer
        
        # 优先使用游戏记录中的AI实际风格
        if (hasattr(self.game_record, 'ai_styles') and 
            self.game_record.ai_styles and 
            player_name in self.game_record.ai_styles):
            
            style_code = self.game_record.ai_styles[player_name]
            # 通过code找到对应的PlayerStyle
            for style in PlayerStyle:
                if style.code == style_code:
                    return style
        
        # 如果没有记录，回退到统计分析
        return player_style_analyzer.analyze_player_style(player_name)

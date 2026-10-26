#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 整合优化版主程序
终端界面的德州扑克游戏，集成优化功能
"""

import os
import sys
from typing import List, Optional

# Input and logging helpers have local fallbacks.
try:
    from texas_holdem.support.enhanced_error_handling import (
        safe_int_input, safe_str_input, safe_choice_input, safe_confirm_input,
    )
    from texas_holdem.support.enhanced_logging import log_game_event, log_user_action
    
except ImportError as e:
    
    # 提供兼容的函数定义
    def safe_int_input(prompt, min_val=None, max_val=None, default=None):
        while True:
            try:
                value = input(prompt).strip()
                if not value and default is not None:
                    return default
                result = int(value)
                if min_val is not None and result < min_val:
                    print(f"❌ 值不能小于 {min_val}")
                    continue
                if max_val is not None and result > max_val:
                    print(f"❌ 值不能大于 {max_val}")
                    continue
                return result
            except ValueError:
                print("❌ 请输入有效数字")
            except KeyboardInterrupt:
                raise
    
    def safe_str_input(prompt, min_length=0, max_length=None, default=None):
        while True:
            try:
                value = input(prompt).strip()
                if not value and default is not None:
                    return default
                if len(value) >= min_length:
                    if max_length is None or len(value) <= max_length:
                        return value
                print(f"❌ 长度必须在 {min_length} 到 {max_length or '无限制'} 之间")
            except KeyboardInterrupt:
                raise
    
    def safe_choice_input(prompt, choices, default=None):
        while True:
            try:
                value = input(prompt).strip()
                if not value and default is not None:
                    return default
                if value in choices:
                    return value
                try:
                    idx = int(value) - 1
                    if 0 <= idx < len(choices):
                        return choices[idx]
                except ValueError:
                    pass
                print(f"❌ 请选择: {', '.join(choices)}")
            except KeyboardInterrupt:
                raise
    
    def safe_confirm_input(prompt, default=None):
        while True:
            try:
                value = input(prompt).strip().lower()
                if not value and default is not None:
                    return default
                if value in ['y', 'yes', '是', '1', 'true']:
                    return True
                elif value in ['n', 'no', '否', '0', 'false']:
                    return False
                print("❌ 请输入 y/n 或 是/否")
            except KeyboardInterrupt:
                raise
    
    def log_game_event(event, player=None, **kwargs):
        pass  # 空实现
    
    def log_user_action(action, player, **kwargs):
        pass  # 空实现

# === 原有模块导入 ===
from texas_holdem.engine.player import Player, HumanPlayer, AIPlayer
from texas_holdem.engine.game import TexasHoldemGame
from texas_holdem.engine.game_rules import (
    BLIND_PRESETS,
    MAX_PLAYERS,
    STACK_PROFILES,
    BlindStructure,
    StackProfile,
    create_rules,
)
from texas_holdem.history.history_viewer import HistoryViewer
from texas_holdem.training.player_evaluation import player_evaluation_system
from texas_holdem.training.training_center import LocalTrainerCenter
import texas_holdem.ui.localization as localization
from texas_holdem.ui.localization import choose_language, terminal_language


class EnhancedTexasHoldemUI:
    """德州扑克终端用户界面 - 整合优化版"""
    
    def __init__(self):
        self.game: TexasHoldemGame = None
        self.history_viewer = HistoryViewer()
        self.training_center = LocalTrainerCenter()
        
        log_game_event("游戏UI初始化完成")
    
    def clear_screen(self):
        """清屏；在没有 TERM 的非交互环境中静默跳过，避免终端噪音。"""
        if os.name == 'nt':
            os.system('cls')
            return
        if not os.environ.get('TERM'):
            return
        os.system('clear')
    
    def display_welcome(self):
        """显示欢迎界面"""
        self.clear_screen()
        print("=" * 60)
        print("🎮 欢迎来到德州扑克游戏！🎮")
        
        print("=" * 60)
        print()
        print("游戏规则:")
        print("• 每位玩家发2张手牌")
        print("• 公共牌分3轮发出：翻牌(3张)、转牌(1张)、河牌(1张)")
        print("• 使用手牌和公共牌组成最佳5张牌")
        print("• 牌型从高到低：皇家同花顺、同花顺、四条、葫芦、同花、顺子、三条、两对、一对、高牌")
        print()
        print("游戏操作:")
        print("• check: 过牌（无人下注时可选择）")
        print("• call: 跟注（跟上当前最高下注）")
        print("• raise: 加注（提高下注金额）")
        print("• fold: 弃牌（放弃这手牌）")
        print()
        
        input("按回车键继续...")
    
    def get_game_settings(self):
        """获取游戏设置（优化版）"""
        self.clear_screen()
        print("=" * 50)
        print("🎯 游戏设置")
        print("=" * 50)
        print()
        
        settings = {}
        
        # AI玩家数量（使用优化的输入处理）
        opponent_prompt = (
            f"请输入AI玩家数量 (1-{MAX_PLAYERS - 1}，总人数{MAX_PLAYERS}人以内): "
        )
        settings['ai_count'] = safe_int_input(
            opponent_prompt,
            min_val=1, 
            max_val=MAX_PLAYERS - 1,
            default=2
        )
        
        # 玩家姓名
        settings['player_name'] = safe_str_input(
            "请输入您的姓名: ", 
            min_length=1, 
            max_length=20, 
            default="Player 1" if localization.LANGUAGE == "en" else "玩家1"
        )

        rules = self._get_rule_settings()
        settings['rules'] = rules
        settings['small_blind'] = rules.small_blind
        settings['big_blind'] = rules.big_blind
        settings['initial_chips'] = rules.starting_chips
        
        log_user_action("配置游戏设置", settings['player_name'], extra_data=settings)
        return settings

    def _get_rule_settings(self):
        """获取第一阶段支持的标准德州 No-Limit 规则设置。"""
        print("\n🧩 规则设置:")
        print("玩法: 标准德州扑克")
        print("下注结构: 无限注 No-Limit")

        print("\n💰 盲注结构:")
        print("1. 5/10")
        print("2. 10/20")
        print("3. 自定义")
        blind_choice = safe_choice_input(
            "请选择盲注结构 (1-3，默认1): ",
            ['1', '2', '3'],
            default='1',
        )
        if blind_choice == '1':
            blind_structure = BLIND_PRESETS["5/10"]
        elif blind_choice == '2':
            blind_structure = BLIND_PRESETS["10/20"]
        else:
            small_blind = safe_int_input(
                "请输入小盲注: ",
                min_val=1,
                max_val=10000,
                default=5,
            )
            big_blind = safe_int_input(
                "请输入大盲注: ",
                min_val=small_blind + 1,
                max_val=20000,
                default=small_blind * 2,
            )
            blind_structure = BlindStructure(small_blind, big_blind)

        print("\n💎 筹码深度:")
        print("1. 短码 20BB")
        print("2. 标准 50BB")
        print("3. 深码 100BB")
        print("4. 自定义")
        stack_choice = safe_choice_input(
            "请选择筹码深度 (1-4，默认2): ",
            ['1', '2', '3', '4'],
            default='2',
        )
        if stack_choice == '1':
            stack_profile = STACK_PROFILES["short"]
        elif stack_choice == '2':
            stack_profile = STACK_PROFILES["standard"]
        elif stack_choice == '3':
            stack_profile = STACK_PROFILES["deep"]
        else:
            custom_chips = safe_int_input(
                f"请输入起始筹码 (至少{blind_structure.big_blind}): ",
                min_val=blind_structure.big_blind,
                max_val=1000000,
                default=blind_structure.big_blind * 50,
            )
            stack_profile = StackProfile("custom", custom_chips=custom_chips)

        rules = create_rules(blind_structure, stack_profile)
        print(
            f"✅ 已选择: 标准德州 No-Limit, "
            f"盲注 {rules.small_blind}/{rules.big_blind}, "
            f"起始筹码 {rules.starting_chips}"
        )
        return rules
    
    def create_players(self, settings):
        """创建玩家"""
        ai_count = settings['ai_count']
        if not isinstance(ai_count, int) or not 1 <= ai_count <= MAX_PLAYERS - 1:
            raise ValueError(f"电脑玩家数量必须在1-{MAX_PLAYERS - 1}人之间")

        players = []
        
        # 创建人类玩家
        human_player = HumanPlayer(settings['player_name'], settings['initial_chips'])
        players.append(human_player)
        log_user_action("加入游戏", settings['player_name'])
        
        # 创建AI玩家
        companion_profiles = [
            "balanced", "loose_aggressive", "calling_station",
            "tight_aggressive", "maniac", "nit", "balanced",
            "loose_aggressive", "calling_station",
        ]
        companion_style_names = {
            "balanced": "均衡型",
            "loose_aggressive": "松凶型",
            "calling_station": "跟注型",
            "tight_aggressive": "紧凶型",
            "maniac": "激进型",
            "nit": "紧手型",
        }
        companion_names = {
            "balanced": "Clawd Kode",
            "loose_aggressive": "Kodeks",
            "calling_station": "Jemini CLI",
            "tight_aggressive": "Kurser",
            "maniac": "OppenKode",
            "nit": "Koder",
        }
        name_counts = {}
        used_names = {human_player.name}
        for i in range(ai_count):
            profile = companion_profiles[i]
            base_name = companion_names[profile]
            name_counts[base_name] = name_counts.get(base_name, 0) + 1
            ai_name = base_name if name_counts[base_name] == 1 else f"{base_name} {name_counts[base_name]}"
            while ai_name in used_names:
                name_counts[base_name] += 1
                ai_name = f"{base_name} {name_counts[base_name]}"
            used_names.add(ai_name)
            ai_player = AIPlayer(ai_name, settings['initial_chips'], archetype_name=profile)
            players.append(ai_player)
            print(f"{ai_name}： {companion_style_names[profile]}")
            log_game_event("AI玩家加入", ai_name)
        
        return players
    
    def run_main_game_loop(self, settings, players):
        """运行主游戏循环"""
        try:
            # 重置AI引擎（新游戏开始）
            try:
                from texas_holdem.ai.smart_ai_system import ai_engine_manager
                ai_engine_manager.reset_for_new_game()
            except ImportError:
                pass  # 如果导入失败，继续使用旧的AI系统
            
            # 创建游戏实例
            self.game = TexasHoldemGame(
                players=players,
                small_blind=settings['small_blind'], 
                big_blind=settings['big_blind'],
                rules=settings['rules'],
            )
            
            # 显示游戏信息
            self.clear_screen()
            self.display_game_info(self.game)
            input("\n按回车键开始游戏...")
            
            log_game_event("游戏开始", extra_data={
                'players': len(players),
                'small_blind': settings['small_blind'],
                'optimized': False
            })
            
            # 游戏主循环
            hand_count = 0
            while not self.game.is_game_over():
                try:
                    hand_count += 1
                    print(f"\n{'='*20} 第 {hand_count} 手牌 {'='*20}")
                    
                    log_game_event(f"第{hand_count}手牌开始")
                    
                    # 调用原有的游戏逻辑
                    if not self.game.play_hand():
                        break
                    
                    # 显示当前排名
                    self.display_standings()
                    
                    if not self.game.is_game_over():
                        # 检查人类玩家是否被淘汰
                        from texas_holdem.engine.player import HumanPlayer
                        human_player = next((p for p in self.game.players if isinstance(p, HumanPlayer)), None)
                        if human_player and human_player.chips == 0:
                            print(f"\n💔 {human_player.name} 已被淘汰！")
                            print("您可以选择:")
                            print("1. 观看AI继续游戏")
                            print("2. 结束游戏查看最终结果")
                            
                            choice = safe_choice_input("请选择 (1/2): ", ['1', '2'], default='1')
                            if choice == "2":
                                break
                        
                        # 询问是否继续下一手牌
                        if hand_count % 5 == 0:  # 每5手询问一次
                            continue_game = safe_confirm_input(
                                f"\n已进行 {hand_count} 手牌，是否继续？(y/n): ", 
                                default=True
                            )
                            if not continue_game:
                                break
                        
                except KeyboardInterrupt:
                    print("\n⏸️  游戏被用户中断")
                    print("已完成的牌局记录会自动保存")
                    break
                    
                except Exception as e:
                    print(f"❌ 游戏运行错误: {e}")
                    log_game_event("游戏错误", extra_data={'error': str(e)})
                    
                    break
            
            # 显示最终结果
            self.display_final_results()
            log_game_event("游戏结束", extra_data={'total_rounds': hand_count})
            
        except Exception as e:
            print(f"❌ 游戏初始化失败: {e}")
            log_game_event("游戏初始化失败", extra_data={'error': str(e)})
    
    def display_final_results(self):
        """显示最终结果"""
        if not self.game:
            return
            
        print("\n" + "="*50)
        print("🏆 游戏结束！最终排名 🏆")
        print("="*50)
        
        # 获取玩家排名（按筹码排序）
        final_standings = sorted(self.game.players, key=lambda p: p.chips, reverse=True)
        
        for i, player in enumerate(final_standings, 1):
            if i == 1:
                print(f"🥇 {i}. {player.name}: {player.chips} 筹码 (冠军！)")
            elif i == 2:
                print(f"🥈 {i}. {player.name}: {player.chips} 筹码")
            elif i == 3:
                print(f"🥉 {i}. {player.name}: {player.chips} 筹码")
            else:
                print(f"   {i}. {player.name}: {player.chips} 筹码")
        
        print("\n🎉 感谢游戏！")
        
    
    def display_standings(self):
        """显示当前排名"""
        if not self.game:
            return
            
        print("\n📊 当前排名:")
        print("-" * 30)
        standings = sorted(self.game.players, key=lambda p: p.chips, reverse=True)
        for i, player in enumerate(standings, 1):
            status = ""
            if player.chips == 0:
                status = " (已淘汰)"
            print(f"{i}. {player.name}: {player.chips} 筹码{status}")
    
    def display_game_info(self, game):
        """显示游戏信息"""
        print("=" * 60)
        print("🎮 游戏信息")
        print("=" * 60)
        print(f"🏆 游戏模式: 德州扑克无限注")
        print(f"👥 玩家数量: {len(game.players)}")
        print(f"💰 盲注结构: {game.small_blind}/{game.big_blind}")
        print(f"💎 起始筹码: {game.players[0].chips}")
        stack_labels = {
            "short": "短码 20BB",
            "standard": "标准 50BB",
            "deep": "深码 100BB",
            "custom": "自定义",
        }
        print(f"📏 筹码深度: {stack_labels.get(game.rules.stack_profile, game.rules.stack_profile)}")
        print()
        
        print("👥 玩家列表:")
        print("-" * 30)
        for i, player in enumerate(game.players, 1):
            player_type = "🤖 AI" if isinstance(player, AIPlayer) else "👤 玩家"
            print(f"{i}. {player_type} {player.name}: {player.chips} 筹码")
        
        print()
    
    def show_history_menu(self):
        """显示历史记录菜单"""
        try:
            while True:
                self.clear_screen()
                print("=" * 50)
                print("📊 历史记录系统")
                print("=" * 50)
                print()
                print("1. 查看玩家战绩")
                print("2. 浏览最近牌局")
                print("3. 搜索特定牌局")
                print("4. 📈 数据可视化")
                print("5. 🏆 玩家排行榜")
                
                print("6. 快速复盘")
                print("7. 返回主菜单")
                choices = ['1', '2', '3', '4', '5', '6', '7']
                
                choice = safe_choice_input(
                    "\n请选择选项: ", 
                    choices, 
                    default=choices[-1]
                )
                
                if choice == '1':
                    self._view_player_stats()
                elif choice == '2':
                    self._browse_recent_games()
                elif choice == '3':
                    self._search_specific_game()
                elif choice == '4':
                    self._show_data_visualization()
                elif choice == '5':
                    self._show_leaderboard()
                elif choice == '6':
                    self._quick_replay()
                elif choice == choices[-1]:  # 返回主菜单
                    break
                
                input("\n按回车键继续...")
                
        except Exception as e:
            print(f"❌ 历史记录功能错误: {e}")
    
    def _show_data_visualization(self):
        """使用实际保存的牌局历史展示玩家数据。"""
        try:
            from texas_holdem.analytics.data_visualization import ASCIIChartRenderer
            
            print("\n📈 数据可视化")
            print("-" * 30)
            
            player_name = safe_str_input("请输入玩家姓名: ", min_length=1)
            
            print("\n选择图表类型:")
            print("1. 筹码趋势图")
            print("2. 动作分布图")
            print("3. 会话摘要")
            print("4. 全部显示")
            
            chart_choice = safe_choice_input("请选择 (1-4): ", ['1', '2', '3', '4'], default='4')

            games = list(reversed(self.history_viewer.history_manager.list_recent_games(limit=1000)))
            player_games = [game for game in games if player_name in game.players]
            if not player_games:
                print(f"暂无 {player_name} 的牌局记录")
                return

            if chart_choice == '1' or chart_choice == '4':
                chips = [hand.final_chips for game in player_games
                         for hand in game.final_hands if hand.player_name == player_name]
                print(ASCIIChartRenderer.line_chart(chips, title=f"{player_name} 筹码趋势"))
            if chart_choice == '2' or chart_choice == '4':
                actions = {'弃牌': 0, '过牌': 0, '跟注': 0, '加注': 0}
                labels = {'fold': '弃牌', 'check': '过牌', 'call': '跟注', 'raise': '加注', 'bet': '加注'}
                for game in player_games:
                    for phase in game.phases:
                        for action in phase.actions:
                            if action.player_name == player_name and action.action in labels:
                                actions[labels[action.action]] += 1
                print(ASCIIChartRenderer.bar_chart(actions, title=f"{player_name} 动作分布"))
            if chart_choice == '3' or chart_choice == '4':
                stats = self.history_viewer.history_manager.get_player_history(player_name)
                print(f"{player_name} 会话摘要：{stats['total_games']} 手牌，"
                      f"获胜 {stats['wins']} 手牌，胜率 {stats['win_rate']:.1f}%")
                
        except ImportError:
            print("❌ 数据可视化模块不可用")
        except Exception as e:
            print(f"❌ 可视化错误: {e}")
    
    def _show_leaderboard(self):
        """按已保存牌局的获胜次数显示排行榜。"""
        try:
            print("\n🏆 玩家排行榜")
            print("-" * 30)
            games = self.history_viewer.history_manager.list_recent_games(limit=100000)
            if not games:
                print("暂无牌局记录")
                return
            counts = {}
            for game in games:
                for name in game.players:
                    counts.setdefault(name, [0, 0])[0] += 1
                for name in game.winner_names:
                    counts.setdefault(name, [0, 0])[1] += 1
            for rank, (name, (played, won)) in enumerate(
                sorted(counts.items(), key=lambda item: (-item[1][1], -item[1][1] / item[1][0], item[0]))[:10], 1
            ):
                print(f"{rank}. {name}: {won} 胜 / {played} 手牌")
        except Exception as e:
            print(f"❌ 排行榜错误: {e}")

    def _view_player_stats(self):
        """查看玩家统计"""
        print("\n📈 玩家战绩查询")
        print("-" * 30)
        
        player_name = safe_str_input("请输入玩家姓名: ", min_length=1)
        
        try:
            stats = self.history_viewer.history_manager.get_player_history(player_name)
            
            if stats and stats.get('total_games', 0) > 0:
                print(f"\n📊 {player_name} 的战绩:")
                print(f"  总局数: {stats.get('total_games', 0)}")
                print(f"  胜局数: {stats.get('wins', 0)}")
                print(f"  胜率: {stats.get('win_rate', 0):.1f}%")
                print(f"  累计获奖筹码: {stats.get('total_winnings', 0)}")
            else:
                print(f"❌ 未找到玩家 '{player_name}' 的记录")
                
        except Exception as e:
            print(f"❌ 查询失败: {e}")
    
    def _browse_recent_games(self):
        """浏览最近游戏"""
        print("\n📋 最近牌局")
        print("-" * 30)
        
        try:
            games = self.history_viewer.history_manager.list_recent_games(limit=10)
            
            if games:
                for i, game in enumerate(games, 1):
                    print(f"{i}. {game.date_time} - {game.game_id} - 获胜者: {', '.join(game.winner_names)}")
            else:
                print("❌ 暂无游戏记录")
                
        except Exception as e:
            print(f"❌ 加载失败: {e}")
    
    def _search_specific_game(self):
        """搜索特定游戏"""
        print("\n🔍 搜索牌局")
        print("-" * 30)
        
        game_id = safe_str_input("请输入游戏ID: ", min_length=1)
        
        try:
            game = self.history_viewer.history_manager.get_game_by_id(game_id)
            
            if game:
                print(f"\n📋 游戏详情:")
                print(f"  游戏ID: {game.game_id}")
                print(f"  时间: {game.date_time}")
                print(f"  玩家: {', '.join(game.players)}")
                print(f"  获胜者: {', '.join(game.winner_names)}")
                print(f"  彩池: {game.total_pot}")
            else:
                print(f"❌ 未找到游戏ID '{game_id}'")
                
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
    
    def _quick_replay(self):
        """从最近牌局中选择一手进入复盘。"""
        print("\n🎬 快速复盘")
        print("-" * 30)
        games = self.history_viewer.history_manager.list_recent_games(limit=10)
        if not games:
            print("暂无可复盘的牌局")
            return
        for index, game in enumerate(games, 1):
            print(f"{index}. {game.date_time} - {game.game_id}")
        choice = safe_int_input("选择牌局序号（0 返回）: ", min_val=0, max_val=len(games), default=0)
        if choice:
            self.history_viewer.enter_replay_mode(games[choice - 1])
    
    def show_training_center(self):
        """显示本地训练中心：把历史统计转成下一局可执行训练目标。"""
        try:
            self.clear_screen()
            print("=" * 60)
            print("🎯 本地训练中心")
            print("=" * 60)
            print()
            print("根据你的历史记录生成下一局训练重点。")
            print("如果样本不足，会先给出建立训练样本的执行清单。")
            print()

            player_name = safe_str_input("请输入玩家姓名: ", min_length=1)
            evaluation = player_evaluation_system.get_comprehensive_evaluation(player_name)
            report = self.training_center.build_report(player_name, evaluation)
            print()
            print(report.format_text())
        except Exception as e:
            print(f"❌ 训练中心生成失败: {e}")

        input("\n按回车键返回...")

    def run_game(self):
        """运行主程序"""
        try:
            # 显示欢迎界面
            self.display_welcome()
            
            while True:
                self.clear_screen()
                print("🎮 德州扑克游戏")
                print("=" * 30)
                
                menu_options = [
                    "1. 开始新游戏",
                    "2. 查看历史记录", 
                    "3. 本地训练中心",
                    "4. 游戏说明",
                ]
                
                menu_options.extend(["5. 玩家风格评测", "6. 退出游戏"])
                choices = ['1', '2', '3', '4', '5', '6']
                
                for option in menu_options:
                    print(option)
                
                choice = safe_choice_input(
                    "\n请选择选项: ", 
                    choices, 
                    default='1'
                )
                
                if choice == '1':
                    # 开始新游戏
                    log_user_action("开始新游戏", "用户")
                    settings = self.get_game_settings()
                    if settings:
                        players = self.create_players(settings)
                        self.run_main_game_loop(settings, players)
                
                elif choice == '2':
                    # 查看历史记录
                    log_user_action("查看历史记录", "用户")
                    self.show_history_menu()
                
                elif choice == '3':
                    # 本地训练中心
                    log_user_action("访问本地训练中心", "用户")
                    self.show_training_center()

                elif choice == '4':
                    # 游戏说明
                    self.display_welcome()
                
                elif choice == '5':
                    # 玩家风格评测
                    log_user_action("访问玩家风格评测", "用户")
                    self.show_player_evaluation()
                
                elif choice == choices[-1]:
                    # 退出游戏
                    if safe_confirm_input("确定要退出游戏吗？(y/n): ", default=False):
                        break
            
            print("👋 感谢游戏！")
            log_game_event("游戏正常退出")
            
        except KeyboardInterrupt:
            print("\n👋 游戏被用户中断，感谢游戏！")
            log_game_event("游戏被中断")
        
        except Exception as e:
            print(f"❌ 程序运行错误: {e}")
            log_game_event("程序错误", extra_data={'error': str(e)})
        
    
    def show_player_evaluation(self):
        """显示玩家风格评测"""
        try:
            self.clear_screen()
            print("=" * 60)
            print("🎯 玩家风格评测系统")
            print("=" * 60)
            print()
            print("基于您最近的游戏记录，分析您的扑克风格分布")
            print()
            
            # 获取玩家姓名
            player_name = safe_str_input("请输入要评测的玩家姓名: ", min_length=1)
            
            print(f"\n正在分析 {player_name} 的游戏风格...")
            
            # 调用玩家评测系统
            try:
                evaluation_result = player_evaluation_system.evaluate_player_style(player_name)
                
                if evaluation_result and not evaluation_result.get('error'):
                    print(f"\n📊 {player_name} 的风格分析:")
                    print("-" * 40)
                    
                    # 显示评测结果
                    for style, percentage in evaluation_result.get('style_distribution', {}).items():
                        print(f"  {style}: {percentage:.1f}%")
                    
                    primary_style = evaluation_result.get('primary_style', {})
                    print(f"\n主要风格: {primary_style.get('name', '未知')}")
                    print(f"游戏局数: {evaluation_result.get('games_analyzed', 0)}")
                    
                    # 显示建议
                    suggestions = evaluation_result.get('suggestions', [])
                    if suggestions:
                        print(f"\n💡 改进建议:")
                        for suggestion in suggestions:
                            print(f"  • {suggestion}")
                else:
                    print(evaluation_result.get('message', f"未找到足够的游戏数据来分析 {player_name}"))
                    
            except Exception as e:
                print(f"❌ 风格评测失败: {e}")
                
        except Exception as e:
            print(f"❌ 玩家评测功能错误: {e}")
        
        input("\n按回车键返回...")


def main():
    """主函数"""
    # Windows系统编码设置
    if sys.platform.startswith('win'):
        try:
            os.system('chcp 65001')
            import locale
            locale.setlocale(locale.LC_ALL, 'Chinese')
        except:
            pass
    
    language = choose_language()
    with terminal_language(language):
        ui = EnhancedTexasHoldemUI()
        ui.run_game()


if __name__ == "__main__":
    main()

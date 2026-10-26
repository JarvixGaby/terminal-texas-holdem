# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 历史牌局查看器
实现历史记录查看和统计功能
"""

import os
from typing import List, Optional
from texas_holdem.history.game_history import GameHistoryManager, GameRecord


class HistoryViewer:
    """历史牌局查看器"""
    
    def __init__(self):
        self.history_manager = GameHistoryManager()
    
    def clear_screen(self):
        """清屏"""
        if os.name == 'nt':
            os.system('cls')
        elif os.environ.get('TERM'):
            os.system('clear')
    
    def show_history_menu(self):
        """显示历史记录主菜单"""
        while True:
            self.clear_screen()
            print("=" * 60)
            print("📊 德州扑克历史记录系统")
            print("=" * 60)
            print()
            print("1. 查看玩家战绩")
            print("2. 浏览最近牌局")
            print("3. 搜索特定牌局")
            print("4. 返回主菜单")
            print()
            
            choice = input("请选择功能 (1-4): ").strip()
            
            if choice == "1":
                self.view_player_stats()
            elif choice == "2":
                self.browse_recent_games()
            elif choice == "3":
                self.search_game()
            elif choice == "4":
                break
            else:
                print("无效选择，请重试")
                input("按回车键继续...")
    
    def view_player_stats(self):
        """查看玩家战绩"""
        self.clear_screen()
        print("=" * 50)
        print("👤 玩家战绩查询")
        print("=" * 50)
        
        player_name = input("请输入玩家姓名: ").strip()
        if not player_name:
            print("玩家姓名不能为空")
            input("按回车键继续...")
            return
        
        stats = self.history_manager.get_player_history(player_name)
        
        if stats['total_games'] == 0:
            print(f"\n未找到玩家 '{player_name}' 的游戏记录")
            input("按回车键继续...")
            return
        
        # 显示统计信息
        print(f"\n玩家: {stats['player_name']}")
        print("-" * 40)
        print(f"总局数: {stats['total_games']}")
        print(f"胜局数: {stats['wins']}")
        print(f"败局数: {stats['losses']}")
        print(f"胜率: {stats['win_rate']}%")
        print(f"总盈利: {stats['total_winnings']}")
        print(f"总损失: {stats['total_losses']}")
        print(f"净利润: {stats['net_profit']}")
        
        if stats['recent_games']:
            print(f"\n最近 {len(stats['recent_games'])} 局游戏:")
            print("-" * 40)
            print(f"{'游戏ID':<15} {'时间':<20} {'结果':<6} {'盈亏':<8} {'牌型':<15}")
            print("-" * 70)
            
            for game in stats['recent_games']:
                result = "胜" if game['is_winner'] else "负"
                winnings = f"+{game['winnings']}" if game['winnings'] > 0 else str(game['winnings'])
                print(f"{game['game_id']:<15} {game['date_time']:<20} {result:<6} {winnings:<8} {game['hand_rank']:<15}")
        
        print()
        input("按回车键继续...")
    
    def browse_recent_games(self):
        """浏览最近牌局"""
        self.clear_screen()
        print("=" * 60)
        print("📋 最近牌局浏览")
        print("=" * 60)
        
        games = self.history_manager.list_recent_games(20)
        
        if not games:
            print("\n暂无游戏记录")
            input("按回车键继续...")
            return
        
        print(f"\n最近 {len(games)} 局游戏:")
        print("-" * 80)
        print(f"{'序号':<4} {'游戏ID':<15} {'时间':<20} {'获胜者':<15} {'彩池':<8} {'时长':<8}")
        print("-" * 80)
        
        for i, game in enumerate(games, 1):
            duration = f"{game.duration_seconds:.1f}s"
            winners = ", ".join(game.winner_names[:2])  # 最多显示2个获胜者
            if len(game.winner_names) > 2:
                winners += "..."
            
            print(f"{i:<4} {game.game_id:<15} {game.date_time:<20} {winners:<15} {game.total_pot:<8} {duration:<8}")
        
        print()
        choice = input("输入序号查看详情，或按回车返回: ").strip()
        
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(games):
                self.show_game_summary(games[idx])
    
    def search_game(self):
        """搜索特定牌局"""
        self.clear_screen()
        print("=" * 50)
        print("🔍 牌局搜索")
        print("=" * 50)
        
        game_id = input("请输入游戏ID: ").strip()
        if not game_id:
            print("游戏ID不能为空")
            input("按回车键继续...")
            return
        
        game = self.history_manager.get_game_by_id(game_id)
        
        if not game:
            print(f"\n未找到游戏ID为 '{game_id}' 的记录")
            input("按回车键继续...")
            return
        
        self.show_game_summary(game)
    
    def show_game_summary(self, game: GameRecord):
        """显示牌局摘要"""
        self.clear_screen()
        print("=" * 70)
        print(f"🎮 牌局详情 - {game.game_id}")
        print("=" * 70)
        
        # 基本信息
        print(f"时间: {game.date_time}")
        print(f"时长: {game.duration_seconds:.1f}秒")
        print(f"玩家: {', '.join(game.players)}")
        print(f"盲注: {game.small_blind}/{game.big_blind}")
        print(f"庄家位置: {game.dealer_position}")
        print(f"总彩池: {game.total_pot}")
        print(f"获胜者: {', '.join(game.winner_names)}")
        
        # 最终结果
        print(f"\n最终结果:")
        print("-" * 50)
        print(f"{'玩家':<12} {'手牌':<12} {'牌型':<15} {'筹码':<8} {'盈亏':<8}")
        print("-" * 50)
        
        for hand in game.final_hands:
            hole_cards = " ".join(hand.hole_cards)
            winnings = f"+{hand.winnings}" if hand.winnings > 0 else str(hand.winnings)
            winner_mark = " 🏆" if hand.is_winner else ""
            print(f"{hand.player_name:<12} {hole_cards:<12} {hand.hand_rank:<15} {hand.final_chips:<8} {winnings:<8}{winner_mark}")
        
        print()
        print("操作选项:")
        print("1. 查看详细过程")
        print("2. 进入复盘模式")
        print("3. 返回")
        
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            self.show_game_details(game)
        elif choice == "2":
            self.enter_replay_mode(game)
    
    def show_game_details(self, game: GameRecord):
        """显示牌局详细过程"""
        self.clear_screen()
        print("=" * 70)
        print(f"📝 牌局详细过程 - {game.game_id}")
        print("=" * 70)
        
        for phase in game.phases:
            print(f"\n【{phase.phase.upper()} 阶段】")
            print(f"公共牌: {' '.join(phase.community_cards) if phase.community_cards else '无'}")
            print(f"彩池: {phase.pot_size}")
            print(f"当前最高下注: {phase.current_bet}")
            
            if phase.actions:
                print("玩家动作:")
                for action in phase.actions:
                    action_desc = ""
                    if action.action == "fold":
                        action_desc = "弃牌"
                    elif action.action == "check":
                        action_desc = "过牌"
                    elif action.action == "call":
                        action_desc = f"跟注 {action.amount}"
                    elif action.action == "raise":
                        action_desc = f"加注 {action.amount}"
                    
                    print(f"  {action.player_name}: {action_desc} (筹码: {action.chips_before} → {action.chips_after})")
            else:
                print("  无动作记录")
        
        print()
        input("按回车键返回...")
    
    def enter_replay_mode(self, game: GameRecord):
        """进入复盘模式"""
        from texas_holdem.history.quick_replay_system import QuickReplaySystem
        
        replay = QuickReplaySystem(game)
        replay.start_replay()

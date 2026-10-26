#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边池管理系统
Side Pot Management System for Texas Hold'em
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
from texas_holdem.engine.player import Player


@dataclass
class PotContribution:
    """底池贡献记录"""
    player_name: str
    amount: int
    is_all_in: bool


@dataclass
class SidePotInfo:
    """边池信息"""
    pot_id: int
    amount: int
    eligible_players: List[str]
    max_contribution: int  # 该边池的最大单人贡献
    all_in_trigger: str    # 触发该边池的全押玩家


class SidePotManager:
    """边池管理器"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置边池管理器"""
        self.contributions: Dict[str, int] = {}  # {player_name: total_contribution}
        self.all_in_players: Dict[str, int] = {}  # {player_name: all_in_amount}
        self.side_pots: List[SidePotInfo] = []
        self.main_pot = 0
    
    def add_contribution(self, player_name: str, amount: int, is_all_in: bool = False):
        """
        添加玩家贡献
        
        Args:
            player_name: 玩家名称
            amount: 贡献金额
            is_all_in: 是否全押
        """
        if player_name not in self.contributions:
            self.contributions[player_name] = 0
        
        self.contributions[player_name] += amount
        
        if is_all_in:
            self.all_in_players[player_name] = self.contributions[player_name]
    
    def calculate_side_pots(self, folded_players: List[str]) -> Tuple[int, List[SidePotInfo]]:
        """
        计算边池分配
        
        Args:
            folded_players: 已弃牌的玩家列表
            
        Returns:
            (main_pot_amount, side_pots_list)
        """
        
        # 获取所有有贡献的玩家（包括已弃牌的）
        all_contributors = {name: amount for name, amount in self.contributions.items() if amount > 0}
        
        if not all_contributors:
            return 0, []
        
        # 获取所有全押金额并排序
        all_in_amounts = sorted(set(self.all_in_players.values()))
        
        if not all_in_amounts:
            # 没有全押，只有主池
            main_pot = sum(all_contributors.values())
            return main_pot, []
        
        side_pots = []
        remaining_contributions = all_contributors.copy()
        previous_level = 0  # 追踪上一个全押级别

        # 为每个全押级别创建边池
        for i, all_in_amount in enumerate(all_in_amounts):
            # 计算本级别的增量（而非累计金额）
            level_increment = all_in_amount - previous_level

            # 找到该级别有资格的玩家（贡献足够且未弃牌）
            eligible_players = []
            for player_name, contribution in remaining_contributions.items():
                if contribution > 0 and player_name not in folded_players:
                    eligible_players.append(player_name)

            # 如果有符合条件的玩家，创建边池
            if eligible_players:
                # 计算该边池的金额（增量 × 有资格的玩家数）
                pot_amount = 0
                for player_name in remaining_contributions:
                    if remaining_contributions[player_name] > 0:
                        # 每个玩家贡献本级别的增量（或剩余金额，取较小值）
                        contribution = min(remaining_contributions[player_name], level_increment)
                        pot_amount += contribution

                # 找到触发该边池的全押玩家
                all_in_trigger = ""
                for player_name, player_all_in_amount in self.all_in_players.items():
                    if player_all_in_amount == all_in_amount:
                        all_in_trigger = player_name
                        break

                side_pot = SidePotInfo(
                    pot_id=len(side_pots) + 1,
                    amount=pot_amount,
                    eligible_players=eligible_players,
                    max_contribution=all_in_amount,
                    all_in_trigger=all_in_trigger
                )
                side_pots.append(side_pot)

                # 减少剩余贡献（减去本级别的增量）
                for player_name in remaining_contributions:
                    remaining_contributions[player_name] = max(0,
                        remaining_contributions[player_name] - level_increment)

            # 更新上一个级别
            previous_level = all_in_amount
        
        # 计算主池（剩余的贡献）
        main_pot = sum(remaining_contributions.values())
        
        return main_pot, side_pots
    
    def distribute_winnings(self, winners: Dict[str, List[str]], 
                          folded_players: List[str]) -> Dict[str, int]:
        """
        分配奖金
        
        Args:
            winners: {pot_type: [winner_names]} 
                    pot_type can be "main" or "side_1", "side_2", etc.
            folded_players: 已弃牌的玩家列表
            
        Returns:
            {player_name: winnings}
        """
        
        main_pot, side_pots = self.calculate_side_pots(folded_players)
        winnings = {player: 0 for player in self.contributions.keys()}
        
        # 分配边池
        for side_pot in side_pots:
            pot_key = f"side_{side_pot.pot_id}"
            if pot_key in winners and winners[pot_key]:
                winners_count = len(winners[pot_key])
                per_winner = side_pot.amount // winners_count
                remainder = side_pot.amount % winners_count
                
                for i, winner in enumerate(winners[pot_key]):
                    winnings[winner] += per_winner
                    if i < remainder:  # 分配余数
                        winnings[winner] += 1
        
        # 分配主池
        if "main" in winners and winners["main"] and main_pot > 0:
            winners_count = len(winners["main"])
            per_winner = main_pot // winners_count
            remainder = main_pot % winners_count
            
            for i, winner in enumerate(winners["main"]):
                winnings[winner] += per_winner
                if i < remainder:  # 分配余数
                    winnings[winner] += 1
        
        return winnings
    
    def get_pot_summary(self, folded_players: List[str]) -> str:
        """
        获取底池总结信息
        
        Returns:
            格式化的底池信息字符串
        """
        
        main_pot, side_pots = self.calculate_side_pots(folded_players)
        
        summary = []
        total_pot = main_pot + sum(side_pot.amount for side_pot in side_pots)
        
        summary.append(f"💰 总底池: {total_pot} 筹码")
        summary.append("")
        
        if side_pots:
            for side_pot in side_pots:
                eligible_str = ", ".join(side_pot.eligible_players)
                summary.append(f"🔸 边池 {side_pot.pot_id}: {side_pot.amount} 筹码")
                summary.append(f"   有资格玩家: {eligible_str}")
                summary.append(f"   触发玩家: {side_pot.all_in_trigger} (全押 {side_pot.max_contribution})")
                summary.append("")
        
        if main_pot > 0:
            # 找到有资格获得主池的玩家
            main_eligible = []
            max_contribution = max(self.contributions.values()) if self.contributions else 0
            
            for player_name, contribution in self.contributions.items():
                if (contribution == max_contribution and 
                    player_name not in folded_players):
                    main_eligible.append(player_name)
            
            eligible_str = ", ".join(main_eligible) if main_eligible else "无"
            summary.append(f"🔹 主池: {main_pot} 筹码")
            summary.append(f"   有资格玩家: {eligible_str}")
        
        return "\n".join(summary)
    
    def get_player_investment(self, player_name: str) -> int:
        """获取玩家的总投入"""
        return self.contributions.get(player_name, 0)
    
    def is_player_all_in(self, player_name: str) -> bool:
        """检查玩家是否全押"""
        return player_name in self.all_in_players
    
    def get_all_in_amount(self, player_name: str) -> int:
        """获取玩家的全押金额"""
        return self.all_in_players.get(player_name, 0)


def example_usage():
    """边池系统使用示例"""
    
    print("🧪 边池系统测试")
    print("="*50)
    
    # 创建边池管理器
    side_pot_mgr = SidePotManager()
    
    # 模拟游戏场景
    print("📋 场景: 4名玩家游戏")
    print("   Alice: 1000筹码")
    print("   Bob: 300筹码 (全押)")
    print("   Charlie: 150筹码 (全押)")
    print("   Diana: 1000筹码")
    print()
    
    # 添加贡献
    side_pot_mgr.add_contribution("Alice", 150)
    side_pot_mgr.add_contribution("Bob", 150)
    side_pot_mgr.add_contribution("Charlie", 150, is_all_in=True)
    side_pot_mgr.add_contribution("Diana", 150)
    
    # Bob继续投入直到全押
    side_pot_mgr.add_contribution("Alice", 150)
    side_pot_mgr.add_contribution("Bob", 150, is_all_in=True)
    side_pot_mgr.add_contribution("Diana", 150)
    
    # Alice和Diana继续下注
    side_pot_mgr.add_contribution("Alice", 200)
    side_pot_mgr.add_contribution("Diana", 200)
    
    print("💰 底池分配:")
    print(side_pot_mgr.get_pot_summary([]))
    
    print()
    print("🏆 获胜分配示例 (Alice赢得所有底池):")
    winners = {
        "main": ["Alice"],
        "side_1": ["Alice"],
        "side_2": ["Alice"]
    }
    winnings = side_pot_mgr.distribute_winnings(winners, [])
    for player, amount in winnings.items():
        if amount > 0:
            print(f"   {player}: +{amount} 筹码")


if __name__ == "__main__":
    example_usage()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 数据可视化系统
提供ASCII图表：筹码趋势、胜率趋势、位置表现、会话统计
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from texas_holdem.storage.database import get_database, DatabaseManager, PlayerStats


# ============================================================================
# ASCII图表渲染器
# ============================================================================

class ASCIIChartRenderer:
    """ASCII图表渲染器"""
    
    @staticmethod
    def line_chart(data: List[int], width: int = 50, height: int = 10,
                  title: str = "", x_label: str = "", y_label: str = "") -> str:
        """
        绘制折线图
        
        Args:
            data: 数据点列表
            width: 图表宽度
            height: 图表高度
            title: 标题
            x_label: X轴标签
            y_label: Y轴标签
            
        Returns:
            ASCII图表字符串
        """
        if not data:
            return "无数据"
        
        lines = []
        
        # 标题
        if title:
            lines.append(title.center(width + 10))
            lines.append("")
        
        # 计算数据范围
        min_val = min(data)
        max_val = max(data)
        
        # 避免除零
        if max_val == min_val:
            max_val = min_val + 1
        
        value_range = max_val - min_val
        
        # 采样数据以适应宽度
        if len(data) > width:
            step = len(data) / width
            sampled_data = [data[int(i * step)] for i in range(width)]
        else:
            sampled_data = data
            width = len(data)
        
        # 创建图表网格
        chart = [[' ' for _ in range(width)] for _ in range(height)]
        
        # 绘制数据点
        for i, val in enumerate(sampled_data):
            # 计算Y坐标（翻转，因为打印是从上到下）
            normalized = (val - min_val) / value_range
            y = height - 1 - int(normalized * (height - 1))
            y = max(0, min(height - 1, y))
            
            # 绘制点
            chart[y][i] = '●'
            
            # 绘制连线（如果不是第一个点）
            if i > 0:
                prev_val = sampled_data[i - 1]
                prev_normalized = (prev_val - min_val) / value_range
                prev_y = height - 1 - int(prev_normalized * (height - 1))
                prev_y = max(0, min(height - 1, prev_y))
                
                # 简单的垂直连线
                if prev_y != y:
                    start_y, end_y = min(prev_y, y), max(prev_y, y)
                    for fill_y in range(start_y + 1, end_y):
                        if chart[fill_y][i] == ' ':
                            chart[fill_y][i] = '│'
        
        # 渲染图表
        y_axis_width = len(f"{max_val:,.0f}") + 1
        
        for row_idx, row in enumerate(chart):
            # Y轴标签
            if row_idx == 0:
                y_val = f"{max_val:,.0f}"
            elif row_idx == height - 1:
                y_val = f"{min_val:,.0f}"
            elif row_idx == height // 2:
                mid_val = (max_val + min_val) / 2
                y_val = f"{mid_val:,.0f}"
            else:
                y_val = ""
            
            y_label_str = y_val.rjust(y_axis_width)
            lines.append(f"{y_label_str} │{''.join(row)}")
        
        # X轴
        lines.append(" " * y_axis_width + " └" + "─" * width)
        
        # X轴标签
        if x_label:
            lines.append(" " * y_axis_width + "  " + x_label.center(width))
        
        # 数据范围说明
        lines.append("")
        lines.append(f"  数据点: {len(data)} | 范围: {min_val:,.0f} - {max_val:,.0f}")
        
        return "\n".join(lines)
    
    @staticmethod
    def bar_chart(data: Dict[str, int], width: int = 50, 
                 title: str = "", horizontal: bool = True) -> str:
        """
        绘制柱状图
        
        Args:
            data: 标签到值的字典
            width: 图表宽度
            title: 标题
            horizontal: 是否水平显示
            
        Returns:
            ASCII图表字符串
        """
        if not data:
            return "无数据"
        
        lines = []
        
        # 标题
        if title:
            lines.append(title.center(width + 20))
            lines.append("─" * (width + 20))
        
        max_val = max(data.values()) if data.values() else 1
        max_label_len = max(len(str(k)) for k in data.keys()) if data else 0
        
        if horizontal:
            # 水平柱状图
            bar_width = width - max_label_len - 15
            
            for label, value in data.items():
                # 计算柱子长度
                bar_len = int((value / max_val) * bar_width) if max_val > 0 else 0
                bar = "█" * bar_len + "░" * (bar_width - bar_len)
                
                # 格式化输出
                label_str = str(label).ljust(max_label_len)
                value_str = f"{value:>8,}"
                lines.append(f"  {label_str} │{bar}│ {value_str}")
        else:
            # 垂直柱状图（简化版）
            num_bars = len(data)
            bar_width = min(5, (width - 10) // num_bars)
            height = 10
            
            # 创建网格
            chart = [[' ' for _ in range(num_bars * (bar_width + 1))] for _ in range(height)]
            
            for col_idx, (label, value) in enumerate(data.items()):
                bar_height = int((value / max_val) * height) if max_val > 0 else 0
                x_start = col_idx * (bar_width + 1)
                
                for row in range(height - bar_height, height):
                    for x in range(x_start, x_start + bar_width):
                        if x < len(chart[row]):
                            chart[row][x] = '█'
            
            # 渲染
            for row in chart:
                lines.append("  " + "".join(row))
            
            # X轴标签
            lines.append("  " + "─" * (num_bars * (bar_width + 1)))
            label_line = "  "
            for label in data.keys():
                label_line += str(label)[:bar_width].center(bar_width + 1)
            lines.append(label_line)
        
        return "\n".join(lines)
    
    @staticmethod
    def table(headers: List[str], rows: List[List], 
             title: str = "", align: str = "left") -> str:
        """
        绘制表格
        
        Args:
            headers: 表头列表
            rows: 数据行列表
            title: 标题
            align: 对齐方式 (left/center/right)
            
        Returns:
            ASCII表格字符串
        """
        if not headers:
            return "无数据"
        
        lines = []
        
        # 计算每列宽度
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # 添加边距
        col_widths = [w + 2 for w in col_widths]
        total_width = sum(col_widths) + len(col_widths) + 1
        
        # 标题
        if title:
            lines.append("┌" + "─" * (total_width - 2) + "┐")
            lines.append("│" + title.center(total_width - 2) + "│")
        
        # 表头分隔线
        separator = "├" + "┼".join("─" * w for w in col_widths) + "┤"
        top_border = "┌" + "┬".join("─" * w for w in col_widths) + "┐"
        bottom_border = "└" + "┴".join("─" * w for w in col_widths) + "┘"
        
        if not title:
            lines.append(top_border)
        else:
            lines.append(separator.replace("├", "├").replace("┤", "┤"))
        
        # 表头
        header_cells = []
        for i, h in enumerate(headers):
            cell = str(h).center(col_widths[i]) if align == "center" else str(h).ljust(col_widths[i])
            header_cells.append(cell)
        lines.append("│" + "│".join(header_cells) + "│")
        
        # 表头下分隔线
        lines.append(separator)
        
        # 数据行
        for row in rows:
            row_cells = []
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    cell_str = str(cell)
                    if align == "center":
                        formatted = cell_str.center(col_widths[i])
                    elif align == "right":
                        formatted = cell_str.rjust(col_widths[i])
                    else:
                        formatted = cell_str.ljust(col_widths[i])
                    row_cells.append(formatted)
            lines.append("│" + "│".join(row_cells) + "│")
        
        # 底部边框
        lines.append(bottom_border)
        
        return "\n".join(lines)
    
    @staticmethod
    def progress_bar(value: float, max_value: float = 100, 
                    width: int = 30, label: str = "") -> str:
        """
        绘制进度条
        
        Args:
            value: 当前值
            max_value: 最大值
            width: 进度条宽度
            label: 标签
            
        Returns:
            进度条字符串
        """
        if max_value <= 0:
            max_value = 100
        
        ratio = min(1.0, max(0.0, value / max_value))
        filled = int(ratio * width)
        empty = width - filled
        
        bar = "█" * filled + "░" * empty
        percentage = f"{ratio * 100:.1f}%"
        
        if label:
            return f"{label}: [{bar}] {percentage}"
        return f"[{bar}] {percentage}"


# ============================================================================
# 玩家数据可视化
# ============================================================================

class PlayerVisualization:
    """玩家数据可视化"""
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        """
        初始化可视化器
        
        Args:
            db: 数据库管理器实例
        """
        self.db = db or get_database()
        self.renderer = ASCIIChartRenderer()
    
    def chip_trend_chart(self, player_name: str, last_n: int = 50) -> str:
        """
        绘制玩家筹码趋势图
        
        Args:
            player_name: 玩家名
            last_n: 显示最近N局
            
        Returns:
            ASCII图表
        """
        chip_history = self.db.get_player_chip_history(player_name, last_n)
        
        if not chip_history:
            return f"没有找到 {player_name} 的游戏记录"
        
        chips = [chips for _, chips in chip_history]
        
        return self.renderer.line_chart(
            data=chips,
            width=50,
            height=12,
            title=f"📈 {player_name} 筹码趋势 (最近{len(chips)}局)",
            x_label="游戏场次",
            y_label="筹码"
        )
    
    def win_rate_trend(self, player_name: str, window: int = 10) -> str:
        """
        绘制胜率趋势图（滑动窗口）
        
        Args:
            player_name: 玩家名
            window: 滑动窗口大小
            
        Returns:
            ASCII图表
        """
        history = self.db.get_player_game_history(player_name, limit=100)
        
        if len(history) < window:
            return f"数据不足，需要至少 {window} 局游戏记录"
        
        # 计算滑动窗口胜率
        win_rates = []
        for i in range(len(history) - window + 1):
            window_games = history[i:i + window]
            wins = sum(1 for g in window_games if g['is_winner'])
            win_rates.append(int(wins / window * 100))
        
        return self.renderer.line_chart(
            data=win_rates,
            width=50,
            height=10,
            title=f"📊 {player_name} 胜率趋势 (窗口={window}局)",
            x_label="时间",
            y_label="胜率%"
        )
    
    def position_analysis_table(self, player_name: str) -> str:
        """
        绘制位置表现分析表
        
        Args:
            player_name: 玩家名
            
        Returns:
            ASCII表格
        """
        stats = self.db.get_player_position_stats(player_name)
        
        if not stats:
            return f"没有找到 {player_name} 的统计数据"
        
        summary = stats.get('summary', {})
        
        headers = ["指标", "数值", "说明"]
        rows = [
            ["总手数", f"{summary.get('total_hands', 0):,}", "参与的总手牌数"],
            ["VPIP", f"{summary.get('vpip', 0):.1f}%", "入局率"],
            ["PFR", f"{summary.get('pfr', 0):.1f}%", "翻牌前加注率"],
            ["攻击性", f"{summary.get('aggression', 0):.2f}", "加注/跟注比"],
            ["摊牌胜率", f"{summary.get('showdown_win_rate', 0):.1f}%", "摊牌获胜比例"],
            ["净盈亏", f"{summary.get('net_profit', 0):+,}", "总盈利-总亏损"],
        ]
        
        return self.renderer.table(
            headers=headers,
            rows=rows,
            title=f"📋 {player_name} 数据统计"
        )
    
    def action_distribution(self, player_name: str) -> str:
        """
        绘制动作分布图
        
        Args:
            player_name: 玩家名
            
        Returns:
            ASCII柱状图
        """
        stats = self.db.get_player_stats(player_name)
        
        if not stats:
            return f"没有找到 {player_name} 的统计数据"
        
        data = {
            "弃牌": stats.total_folds,
            "过牌": stats.total_checks,
            "跟注": stats.total_calls,
            "加注": stats.total_raises + stats.total_bets
        }
        
        return self.renderer.bar_chart(
            data=data,
            width=50,
            title=f"🎯 {player_name} 动作分布"
        )
    
    def session_summary(self, player_name: str) -> str:
        """
        生成会话摘要
        
        Args:
            player_name: 玩家名
            
        Returns:
            格式化的摘要字符串
        """
        stats = self.db.get_player_stats(player_name)
        history = self.db.get_player_game_history(player_name, limit=50)
        
        lines = []
        lines.append("")
        lines.append("╔" + "═" * 56 + "╗")
        lines.append("║" + f" 📊 {player_name} 会话摘要 ".center(54) + "║")
        lines.append("╠" + "═" * 56 + "╣")
        
        if stats:
            # 基础统计
            lines.append(f"║  总手数: {stats.total_hands:>6,}   │   总盈利: {stats.total_winnings:>+10,}  ║")
            lines.append(f"║  摊牌数: {stats.showdowns_total:>6,}   │   总亏损: {stats.total_losses:>10,}  ║")
            lines.append(f"║  摊牌胜: {stats.showdowns_won:>6,}   │   净盈亏: {stats.total_winnings - stats.total_losses:>+10,}  ║")
            
            lines.append("╠" + "═" * 56 + "╣")
            
            # 动作统计
            total_actions = (stats.total_folds + stats.total_checks + 
                           stats.total_calls + stats.total_raises + stats.total_bets)
            
            if total_actions > 0:
                fold_pct = stats.total_folds / total_actions * 100
                check_pct = stats.total_checks / total_actions * 100
                call_pct = stats.total_calls / total_actions * 100
                raise_pct = (stats.total_raises + stats.total_bets) / total_actions * 100
                
                lines.append(f"║  弃牌: {fold_pct:>5.1f}%  过牌: {check_pct:>5.1f}%  跟注: {call_pct:>5.1f}%  加注: {raise_pct:>5.1f}%  ║")
            
            # 风格判断
            if stats.total_hands > 0:
                vpip = (stats.total_calls + stats.total_bets + stats.total_raises) / stats.total_hands * 100
                pfr = stats.total_raises / stats.total_hands * 100
                
                if vpip > 30 and pfr > 20:
                    style = "激进型 (LAG)"
                elif vpip > 30:
                    style = "松散被动型 (LP)"
                elif pfr > 15:
                    style = "紧凑激进型 (TAG)"
                else:
                    style = "紧凑被动型 (TP)"
                
                lines.append("╠" + "═" * 56 + "╣")
                lines.append(f"║  VPIP: {vpip:>5.1f}%   PFR: {pfr:>5.1f}%   风格: {style:<16} ║")
        
        # 最近表现
        if history:
            recent_wins = sum(1 for g in history[:10] if g['is_winner'])
            recent_profit = sum(g['winnings'] for g in history[:10])
            
            lines.append("╠" + "═" * 56 + "╣")
            lines.append(f"║  最近10局: {recent_wins}/10 胜   盈亏: {recent_profit:>+10,} 筹码{' '*9}║")
        
        lines.append("╚" + "═" * 56 + "╝")
        lines.append("")
        
        return "\n".join(lines)
    
    def leaderboard(self, limit: int = 10) -> str:
        """
        生成排行榜
        
        Args:
            limit: 显示数量
            
        Returns:
            ASCII表格
        """
        all_stats = self.db.get_all_player_stats()
        
        if not all_stats:
            return "没有玩家统计数据"
        
        # 按净盈亏排序
        sorted_stats = sorted(
            all_stats, 
            key=lambda s: s.total_winnings - s.total_losses, 
            reverse=True
        )[:limit]
        
        headers = ["排名", "玩家", "手数", "胜率", "净盈亏"]
        rows = []
        
        for i, stats in enumerate(sorted_stats, 1):
            win_rate = (stats.showdowns_won / stats.showdowns_total * 100 
                       if stats.showdowns_total > 0 else 0)
            net = stats.total_winnings - stats.total_losses
            
            # 排名图标
            rank_icon = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            
            rows.append([
                rank_icon,
                stats.player_name[:12],
                f"{stats.total_hands:,}",
                f"{win_rate:.1f}%",
                f"{net:+,}"
            ])
        
        return self.renderer.table(
            headers=headers,
            rows=rows,
            title="🏆 玩家排行榜"
        )


# ============================================================================
# 便捷函数
# ============================================================================

def show_player_dashboard(player_name: str):
    """显示玩家完整数据面板"""
    viz = PlayerVisualization()
    
    print("\n" + "=" * 60)
    print(f"  {player_name} 数据面板")
    print("=" * 60)
    
    # 会话摘要
    print(viz.session_summary(player_name))
    
    # 动作分布
    print(viz.action_distribution(player_name))
    print()
    
    # 筹码趋势
    print(viz.chip_trend_chart(player_name))
    print()


def show_leaderboard():
    """显示排行榜"""
    viz = PlayerVisualization()
    print(viz.leaderboard())


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("数据可视化系统测试")
    print("=" * 60)
    
    renderer = ASCIIChartRenderer()
    
    # 测试折线图
    print("\n测试折线图:")
    test_data = [100, 120, 95, 150, 130, 180, 160, 200, 190, 220, 
                 210, 250, 230, 280, 260, 300, 290, 320, 310, 350]
    print(renderer.line_chart(test_data, title="📈 筹码变化趋势"))
    
    # 测试柱状图
    print("\n测试柱状图:")
    test_bar_data = {
        "弃牌": 45,
        "过牌": 30,
        "跟注": 60,
        "加注": 25
    }
    print(renderer.bar_chart(test_bar_data, title="🎯 动作分布"))
    
    # 测试表格
    print("\n测试表格:")
    headers = ["指标", "数值", "说明"]
    rows = [
        ["VPIP", "28.5%", "入局率"],
        ["PFR", "18.2%", "翻牌前加注率"],
        ["攻击性", "1.85", "加注/跟注比"],
        ["胜率", "52.3%", "摊牌获胜比例"]
    ]
    print(renderer.table(headers, rows, title="📋 玩家统计"))
    
    # 测试进度条
    print("\n测试进度条:")
    print(renderer.progress_bar(75, 100, label="胜率"))
    print(renderer.progress_bar(45, 100, label="入局率"))
    
    # 测试实际数据（如果数据库有数据）
    print("\n" + "=" * 60)
    print("测试实际数据库数据:")
    print("=" * 60)
    
    viz = PlayerVisualization()
    
    # 显示排行榜
    print(viz.leaderboard())
    
    # 尝试显示玩家数据
    db = get_database()
    all_stats = db.get_all_player_stats()
    
    if all_stats:
        player_name = all_stats[0].player_name
        print(f"\n显示 {player_name} 的数据:")
        print(viz.session_summary(player_name))
        print(viz.action_distribution(player_name))



#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 整合测试脚本
验证整合版的各项功能是否正常工作
"""

def test_basic_functionality():
    """测试基本功能"""
    print("🧪 测试基本功能...")
    
    try:
        from main import EnhancedTexasHoldemUI
        ui = EnhancedTexasHoldemUI()
        print("✅ UI创建成功")
        
        # 测试游戏设置
        settings = {
            'ai_count': 2,
            'player_name': 'TestPlayer',
            'small_blind': 5,
            'big_blind': 10,
            'initial_chips': 1000
        }
        
        players = ui.create_players(settings)
        print(f"✅ 创建了 {len(players)} 个玩家")
        
        # 测试游戏实例创建
        from game import TexasHoldemGame
        game = TexasHoldemGame(players, settings['small_blind'], settings['big_blind'])
        print("✅ 游戏实例创建成功")
        
        # 测试游戏状态检查
        is_over = game.is_game_over()
        print(f"✅ 游戏状态检查: {'结束' if is_over else '进行中'}")
        
    except Exception as e:
        raise AssertionError(f"基本功能测试失败: {e}") from e


def test_optimization_features():
    """测试优化功能"""
    print("\n🚀 测试优化功能...")
    
    try:
        # 测试优化模块导入
        from enhanced_error_handling import safe_int_input, safe_str_input
        print("✅ 错误处理模块正常")
        
        from enhanced_config_manager import get_global_config
        config = get_global_config()
        print("✅ 配置管理模块正常")
        
        from optimized_odds_calculator import OptimizedOddsCalculator
        calc = OptimizedOddsCalculator()
        print("✅ 胜率计算模块正常")
        
        from optimized_data_manager import get_data_manager
        data_mgr = get_data_manager()
        print("✅ 数据管理模块正常")
        
    except Exception as e:
        raise AssertionError(f"优化功能测试失败: {e}") from e


def test_game_logic():
    """测试游戏逻辑"""
    print("\n🎮 测试游戏逻辑...")
    
    try:
        from player import HumanPlayer, AIPlayer
        from card import Card, Deck
        from hand_evaluator import HandEvaluator
        
        # 创建测试玩家
        human = HumanPlayer("测试玩家", 1000)
        ai = AIPlayer("测试AI", 1000)
        print("✅ 玩家创建正常")
        
        # 测试卡片系统
        deck = Deck()
        card = deck.deal_card()
        print(f"✅ 卡片系统正常: {card}")
        
        # 测试手牌评估（需要7张牌）
        test_cards = [deck.deal_card() for _ in range(7)]
        rank, kickers = HandEvaluator.evaluate_hand(test_cards)
        print(f"✅ 手牌评估正常: {rank}")
        
    except Exception as e:
        raise AssertionError(f"游戏逻辑测试失败: {e}") from e


def main():
    """主测试函数"""
    print("🎮 德州扑克整合版功能测试")
    print("=" * 50)
    
    tests = [
        ("基本功能", test_basic_functionality),
        ("优化功能", test_optimization_features),
        ("游戏逻辑", test_game_logic)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_name}测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("📊 测试结果")
    print("=" * 50)
    print(f"✅ 通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！整合版运行正常")
        print()
        print("🚀 可以安全运行:")
        print("   python3 main.py")
    else:
        print("⚠️  部分测试失败，请检查相关模块")
    
    print("\n🎮 感谢测试！")


if __name__ == "__main__":
    main()

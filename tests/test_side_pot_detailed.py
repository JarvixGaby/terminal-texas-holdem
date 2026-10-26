#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边池计算逻辑详细测试
验证每一步的计算过程
"""

from texas_holdem.engine.side_pot_manager import SidePotManager


def test_detailed_scenario():
    """
    详细测试场景：多人不同金额全押
    Alice: 500
    Bob: 150 (全押)
    Charlie: 300 (全押)
    Diana: 500

    正确的边池分配应该是：
    - 边池1 (Bob触发): 150*4 = 600 (所有人有资格)
    - 边池2 (Charlie触发): (300-150)*3 = 450 (Alice, Charlie, Diana)
    - 主池: (500-300)*2 = 400 (Alice, Diana)

    总计: 600 + 450 + 400 = 1450
    """
    print("\n" + "="*70)
    print("详细测试：多人不同金额全押")
    print("="*70)

    mgr = SidePotManager()
    mgr.add_contribution("Alice", 500)
    mgr.add_contribution("Bob", 150, is_all_in=True)
    mgr.add_contribution("Charlie", 300, is_all_in=True)
    mgr.add_contribution("Diana", 500)

    print("\n📊 玩家贡献:")
    for name, amount in mgr.contributions.items():
        all_in_status = " (全押)" if name in mgr.all_in_players else ""
        print(f"  {name}: {amount}{all_in_status}")

    print(f"\n🎯 全押金额列表: {sorted(mgr.all_in_players.values())}")

    main_pot, side_pots = mgr.calculate_side_pots([])

    print("\n💰 计算结果:")
    total = main_pot
    for i, sp in enumerate(side_pots, 1):
        print(f"  边池{i}: {sp.amount} 筹码")
        print(f"    - 有资格: {', '.join(sp.eligible_players)}")
        print(f"    - 最大贡献: {sp.max_contribution}")
        print(f"    - 触发玩家: {sp.all_in_trigger}")
        total += sp.amount

    print(f"  主池: {main_pot} 筹码")

    print(f"\n📈 总计: {total} 筹码")
    print(f"   预期: 1450 筹码")

    # 验证每个边池的金额
    if len(side_pots) >= 1:
        expected_side1 = 600
        actual_side1 = side_pots[0].amount
        print(f"\n✓ 边池1: 预期 {expected_side1}, 实际 {actual_side1}, {'✅' if actual_side1 == expected_side1 else '❌'}")

    if len(side_pots) >= 2:
        expected_side2 = 450
        actual_side2 = side_pots[1].amount
        print(f"✓ 边池2: 预期 {expected_side2}, 实际 {actual_side2}, {'✅' if actual_side2 == expected_side2 else '❌'}")

    expected_main = 400
    print(f"✓ 主池: 预期 {expected_main}, 实际 {main_pot}, {'✅' if main_pot == expected_main else '❌'}")

    # 手动计算验证
    print("\n🔍 手动验证:")
    print("  边池1 (Bob全押150): 150 × 4人 = 600 ✓")
    print("  边池2 (Charlie全押300): (300-150) × 3人 = 450 ✓")
    print("  主池 (剩余): (500-300) × 2人 = 400 ✓")

    assert total == 1450, f"总额错误: 期望1450, 实际{total}"

    # 检查边池2的金额
    if len(side_pots) >= 2:
        assert side_pots[1].amount == 450, f"边池2金额错误: 期望450, 实际{side_pots[1].amount}"

    print("\n✅ 测试通过")


if __name__ == "__main__":
    print("🧪 边池计算详细测试")
    test_detailed_scenario()

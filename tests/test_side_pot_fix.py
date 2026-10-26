#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边池计算逻辑测试
用于验证修复前后的正确性
"""

from texas_holdem.engine.side_pot_manager import SidePotManager


def test_scenario_1_simple_all_in():
    """
    场景1: 简单的单人全押
    Alice: 1000, 下注 300
    Bob: 200, 全押 200
    Charlie: 1000, 下注 300

    预期:
    - 边池1: 200*3 = 600 (所有人有资格)
    - 主池: 100*2 = 200 (Alice和Charlie)
    """
    print("\n" + "="*60)
    print("测试场景1: 简单的单人全押")
    print("="*60)

    mgr = SidePotManager()
    mgr.add_contribution("Alice", 300)
    mgr.add_contribution("Bob", 200, is_all_in=True)
    mgr.add_contribution("Charlie", 300)

    main_pot, side_pots = mgr.calculate_side_pots([])

    total = main_pot + sum(sp.amount for sp in side_pots)
    expected_total = 800

    print(f"总投入: {expected_total}")
    print(f"计算总额: {total}")
    print(f"主池: {main_pot}")
    for sp in side_pots:
        print(f"边池{sp.pot_id}: {sp.amount}, 有资格: {sp.eligible_players}")

    assert total == expected_total, f"总额错误: 期望{expected_total}, 实际{total}"
    print("✅ 场景1 通过")


def test_scenario_2_multiple_all_ins():
    """
    场景2: 多人不同金额全押
    Alice: 1000, 下注 500
    Bob: 150, 全押 150
    Charlie: 300, 全押 300
    Diana: 1000, 下注 500

    预期:
    - 边池1: 150*4 = 600 (所有人)
    - 边池2: (300-150)*3 = 450 (Alice, Charlie, Diana)
    - 主池: (500-300)*2 = 400 (Alice, Diana)
    总计: 1450
    """
    print("\n" + "="*60)
    print("测试场景2: 多人不同金额全押")
    print("="*60)

    mgr = SidePotManager()
    mgr.add_contribution("Alice", 500)
    mgr.add_contribution("Bob", 150, is_all_in=True)
    mgr.add_contribution("Charlie", 300, is_all_in=True)
    mgr.add_contribution("Diana", 500)

    main_pot, side_pots = mgr.calculate_side_pots([])

    total = main_pot + sum(sp.amount for sp in side_pots)
    expected_total = 1450

    print(f"总投入: {expected_total}")
    print(f"计算总额: {total}")
    print(f"主池: {main_pot}")
    for sp in side_pots:
        print(f"边池{sp.pot_id}: {sp.amount}, 有资格: {sp.eligible_players}")

    assert total == expected_total, f"总额错误: 期望{expected_total}, 实际{total}"
    print("✅ 场景2 通过")


if __name__ == "__main__":
    print("🧪 边池计算逻辑测试")
    print("测试当前实现是否正确...")

    try:
        test_scenario_1_simple_all_in()
        test_scenario_2_multiple_all_ins()
        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)
    except AssertionError as e:
        print("\n" + "="*60)
        print(f"❌ 测试失败: {e}")
        print("="*60)
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ 测试异常: {e}")
        print("="*60)

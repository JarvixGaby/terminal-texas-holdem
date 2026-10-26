#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手牌评估器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from texas_holdem.engine.card import Card, Suit, Rank
from texas_holdem.engine.hand_evaluator import HandEvaluator, HandRank


def test_royal_flush():
    """测试皇家同花顺"""
    cards = [
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.HEARTS, Rank.KING),
        Card(Suit.HEARTS, Rank.QUEEN),
        Card(Suit.HEARTS, Rank.JACK),
        Card(Suit.HEARTS, Rank.TEN),
        Card(Suit.CLUBS, Rank.TWO),
        Card(Suit.CLUBS, Rank.THREE)
    ]
    rank, kickers = HandEvaluator.evaluate_hand(cards)
    assert rank == HandRank.ROYAL_FLUSH
    print("✅ 皇家同花顺测试通过")


def test_straight_flush():
    """测试同花顺"""
    cards = [
        Card(Suit.DIAMONDS, Rank.NINE),
        Card(Suit.DIAMONDS, Rank.EIGHT),
        Card(Suit.DIAMONDS, Rank.SEVEN),
        Card(Suit.DIAMONDS, Rank.SIX),
        Card(Suit.DIAMONDS, Rank.FIVE),
        Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.HEARTS, Rank.KING)
    ]
    rank, kickers = HandEvaluator.evaluate_hand(cards)
    assert rank == HandRank.STRAIGHT_FLUSH
    assert kickers[0] == 9
    print("✅ 同花顺测试通过")


def test_four_of_a_kind():
    """测试四条"""
    cards = [
        Card(Suit.HEARTS, Rank.KING),
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.KING),
        Card(Suit.SPADES, Rank.KING),
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.CLUBS, Rank.TWO),
        Card(Suit.DIAMONDS, Rank.THREE)
    ]
    rank, kickers = HandEvaluator.evaluate_hand(cards)
    assert rank == HandRank.FOUR_OF_A_KIND
    assert kickers[0] == 13  # K
    print("✅ 四条测试通过")


def test_full_house():
    """测试葫芦"""
    cards = [
        Card(Suit.HEARTS, Rank.QUEEN),
        Card(Suit.DIAMONDS, Rank.QUEEN),
        Card(Suit.CLUBS, Rank.QUEEN),
        Card(Suit.SPADES, Rank.JACK),
        Card(Suit.HEARTS, Rank.JACK),
        Card(Suit.CLUBS, Rank.TWO),
        Card(Suit.DIAMONDS, Rank.THREE)
    ]
    rank, kickers = HandEvaluator.evaluate_hand(cards)
    assert rank == HandRank.FULL_HOUSE
    assert kickers[0] == 12  # Q
    assert kickers[1] == 11  # J
    print("✅ 葫芦测试通过")


def test_wheel_straight():
    """测试 A-2-3-4-5 顺子（轮子）"""
    cards = [
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.FIVE),
        Card(Suit.CLUBS, Rank.FOUR),
        Card(Suit.SPADES, Rank.THREE),
        Card(Suit.HEARTS, Rank.TWO),
        Card(Suit.CLUBS, Rank.KING),
        Card(Suit.DIAMONDS, Rank.QUEEN)
    ]
    rank, kickers = HandEvaluator.evaluate_hand(cards)
    assert rank == HandRank.STRAIGHT
    assert kickers[0] == 5  # A-2-3-4-5，5是最高牌
    print("✅ A-2-3-4-5 顺子测试通过")


def test_pair():
    """测试一对"""
    cards = [
        Card(Suit.HEARTS, Rank.KING),
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.SPADES, Rank.QUEEN),
        Card(Suit.HEARTS, Rank.JACK),
        Card(Suit.CLUBS, Rank.NINE),
        Card(Suit.DIAMONDS, Rank.SEVEN)
    ]
    rank, kickers = HandEvaluator.evaluate_hand(cards)
    assert rank == HandRank.PAIR
    assert kickers[0] == 13  # K
    print("✅ 一对测试通过")


if __name__ == "__main__":
    print("🧪 手牌评估器单元测试")
    print("="*60)

    test_royal_flush()
    test_straight_flush()
    test_four_of_a_kind()
    test_full_house()
    test_wheel_straight()
    test_pair()

    print("="*60)
    print("✅ 所有测试通过！")

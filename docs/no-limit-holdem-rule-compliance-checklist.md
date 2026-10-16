# No-Limit Hold'em Rule Compliance Checklist

Use this checklist when reviewing or changing game flow, betting, pot handling, and showdown logic.

## Table setup
- [ ] Supports 2+ active players for a hand.
- [ ] Uses a dealer/button position and advances it after each hand.
- [ ] Posts small blind and big blind before dealing.
- [ ] Handles players with insufficient chips posting partial blinds/all-in blinds.

## Deal and streets
- [ ] Deals two private hole cards to each active player.
- [ ] Runs streets in order: preflop, flop, turn, river, showdown when needed.
- [ ] Burns one card before flop, turn, and river if burn-card behavior is modeled.
- [ ] Deals community cards as 3-card flop, 1-card turn, 1-card river.

## Betting rules
- [ ] Allows fold, check, call, bet, raise, and all-in where legal.
- [ ] Prevents checking when facing a bet.
- [ ] Requires calls to match the current bet unless the player is all-in for less.
- [ ] Enforces no-limit raises up to a player's remaining stack.
- [ ] Enforces minimum bet/raise rules, including big blind as the opening preflop bet.
- [ ] Treats short all-in raises correctly for action reopening.
- [ ] Ends a betting round only after all non-folded, non-all-in players have acted and matched the current bet.

## Pots and eligibility
- [ ] Tracks each player's total contribution for the hand.
- [ ] Creates side pots for unequal all-in contributions.
- [ ] Limits side-pot eligibility to players who contributed to that pot and did not fold.
- [ ] Awards uncontested pots immediately when only one non-folded player remains.
- [ ] Preserves chip conservation: total chips before hand equals total chips after hand.

## Showdown and hand evaluation
- [ ] Evaluates best 5-card hand from 2 hole cards plus up to 5 community cards.
- [ ] Applies standard poker hand rankings and kicker tie-breakers.
- [ ] Splits tied pots evenly among winners, with deterministic odd-chip handling if needed.
- [ ] Reveals/uses only eligible players' hands at showdown.

## State cleanup
- [ ] Clears per-hand bets, folded status, all-in status as appropriate between hands.
- [ ] Removes or skips busted players according to game rules.
- [ ] Advances dealer/button correctly after eliminations.

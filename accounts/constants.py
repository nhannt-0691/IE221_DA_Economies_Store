from decimal import Decimal

#Rank choices for User model
RANK_RULE = [
    ('iron', Decimal('0.00'), 0),
    ('bronze', Decimal('20_000_000.00'), 5),  
    ('silver', Decimal('50_000_000.00'), 10),  
    ('gold', Decimal('100_000_000.00'), 15),  
    ('platinum', Decimal('500_000_000.00'), 20)]

def get_rank_by_amount(total_spent: Decimal):
    
    current_rank = RANK_RULE[0]

    for rule in RANK_RULE:
        if total_spent >= rule[1]:  
            current_rank = rule
        else:
            break

    return current_rank[0], current_rank[2]
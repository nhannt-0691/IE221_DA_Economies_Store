from decimal import Decimal

#Rank choices for User model
RANK_RULE = [
    ('iron', Decimal('0.00'), 0),
    ('bronze', Decimal('20_000_000.00'), 5),  
    ('silver', Decimal('50_000.00'), 10),  
    ('gold', Decimal('100_000_000.00'), 15),  
    ('platinum', Decimal('500_000_000.00'), 20)]
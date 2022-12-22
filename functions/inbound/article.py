
from dataclasses import dataclass

@dataclass
class Article:
    article_no: int
    sum_quantity: int
    status: str
    qnt_box: int
    full_qty: int
    individual_pieces: int
    Full_pal_qty: int
    Half_pal_qty: int
    Quarter_pal_qty: int
    IQC = False
    default_id: int

    def __post_init__(self):
        self.filled_place = {'ids': [], 'qty': []}
        if self.individual_pieces == self.sum_quantity:
            self.individual_pieces = 0
from dataclasses import dataclass


@dataclass
class Ad:
    ad_id: str
    address: str
    area: float
    price: int

    def url(self):
        return 'https://krisha.kz/a/show/' + self.ad_id


@dataclass
class Flat(Ad):
    rooms: int
    floor: int
    building_height: int

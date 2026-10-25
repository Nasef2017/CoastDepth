from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Bounds:
    west: float
    south: float
    east: float
    north: float

    def validate(self):
        if not all(math.isfinite(v) for v in (self.west, self.south, self.east, self.north)):
            raise ValueError("ROI bounds must be finite.")
        if not (-180 <= self.west < self.east <= 180 and -90 <= self.south < self.north <= 90):
            raise ValueError("ROI must have positive area within EPSG:4326 bounds.")
        if self.east - self.west > 180:
            raise ValueError("Split ROIs crossing the antimeridian into separate downloads.")
        # A deliberately conservative ceiling for local mask/export memory use.
        if self.estimated_cells > 25_000_000:
            raise ValueError("ROI exceeds 25 million cells. Split it into smaller areas.")
        return self

    @property
    def estimated_cells(self):
        return math.ceil((self.east - self.west) * 960 + 2) * math.ceil((self.north - self.south) * 960 + 2)

    def subset_arguments(self):
        return dict(minimum_longitude=self.west, maximum_longitude=self.east,
                    minimum_latitude=self.south, maximum_latitude=self.north)

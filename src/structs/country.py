from enum import Enum


class Country(Enum):
    UY = "Uruguay"
    USA = "United States"

    # suport case insensitive
    @classmethod
    def get_country_by_name_insensitive(cls, name: str) -> "Country":
        for country in cls:
            if country.value.lower() == name.lower():
                return country
        raise ValueError(f"Country not found: {name}")

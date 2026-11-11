class Film:
    def __init__(self, id: int, title: str, overview: str, poster_url: str, rating: str, year: str, genres: list, showtimes: list, price: str):
        self.id = id
        self.title = title
        self.overview = overview
        self.poster_url = poster_url
        self.rating = rating
        self.year = year
        self.genres = genres
        self.showtimes = showtimes
        self.price = price

    def to_dict(self):
        """Convertește obiectul în dicționar pentru a putea fi trimis ușor ca JSON sau în template-uri."""
        return {
            "id": self.id,
            "title": self.title,
            "overview": self.overview,
            "poster_url": self.poster_url,
            "rating": self.rating,
            "year": self.year,
            "genres": self.genres,
            "showtimes": self.showtimes,
            "price": self.price
        }

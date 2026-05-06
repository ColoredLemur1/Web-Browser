class Search:
    def __init__(self, index):
        self.index = index

    def find_pages(self, query):
        """Urls whose postings include every query token, lowercased"""
        terms = [t.lower() for t in query.split() if t.strip()]
        if not terms:
            return []

        result = set(self.index.get(terms[0], {}).keys())
        for term in terms[1:]:
            result &= set(self.index.get(term, {}).keys())

        return list(result)

    def print_word(self, word):
        """Postings for lowercased word or none if absent"""
        return self.index.get(word.lower())

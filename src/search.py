from nltk.stem import PorterStemmer

_stemmer = PorterStemmer()


class Search:
    def __init__(self, index):
        self.index = index

    def find_pages(self, query):
        """Urls with every query token, rank by summed term frequency"""
        terms = [_stemmer.stem(t.lower()) for t in query.split() if t.strip()]
        if not terms:
            return []

        result = set(self.index.get(terms[0], {}).keys())
        for term in terms[1:]:
            result &= set(self.index.get(term, {}).keys())

        def score(url):
            return sum(
                self.index[term][url]["frequency"]
                for term in terms
                if url in self.index.get(term, {})
            )

        return sorted(result, key=score, reverse=True)

    def print_word(self, word):
        """Postings for stemmed lowercased word, none if absent"""
        return self.index.get(_stemmer.stem(word.lower()))

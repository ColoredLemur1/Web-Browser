import os
from crawler import Crawler
from indexer import Indexer
from search import Search

INDEX_PATH = "data/index.json"
START_URL = "https://quotes.toscrape.com/"


def run():
    indexer = Indexer()
    search = None

    print("Search Engine Tool. Commands: build, load, print <word>, find <query>, quit")

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        command = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else ""

        if command == "build":
            print(f"Crawling {START_URL} ... (be aware of delay per page)")
            crawler = Crawler(delay=6, verbose=True)
            pages = crawler.crawl(START_URL)
            print(f"Crawled {len(pages)} pages. Building index...")
            indexer.build(pages)
            os.makedirs("data", exist_ok=True)
            indexer.save(INDEX_PATH)
            unique_words = len(indexer.index)
            print(f"Index built. {unique_words} unique words indexed across {len(pages)} pages.")
            print(f"Index saved to {INDEX_PATH}")
            search = Search(indexer.index)

        elif command == "load":
            try:
                indexer.load(INDEX_PATH)
                search = Search(indexer.index)
                page_count = len({url for postings in indexer.index.values() for url in postings})
                print(f"Index loaded from {INDEX_PATH} ({len(indexer.index)} words, {page_count} pages).")
            except FileNotFoundError:
                print("No index found. Run 'build' first.")

        elif command == "print":
            if not argument:
                print("Usage: print <word>")
                continue
            if search is None:
                print("No index loaded. Run 'build' or 'load' first.")
                continue
            entry = search.print_word(argument)
            if entry is None:
                print(f"'{argument}' not found in index.")
            else:
                print(f"'{argument}' found in {len(entry)} page(s):")
                for url, stats in entry.items():
                    print(f"  {url}  — freq: {stats['frequency']}, positions: {stats['positions']}")

        elif command == "find":
            if not argument:
                print("Usage: find <query>")
                continue
            if search is None:
                print("No index loaded. Run 'build' or 'load' first.")
                continue
            results = search.find_pages(argument)
            if not results:
                print(f"No pages found containing '{argument}'.")
            else:
                terms = argument.strip().split()
                label = " AND ".join(f"'{t}'" for t in terms)
                print(f"Pages containing {label}:")
                for url in results:
                    print(f"  {url}")

        elif command in ("quit", "exit"):
            break

        else:
            print("Unknown command. Type 'build', 'load', 'print <word>', 'find <query>', or 'quit'.")


if __name__ == "__main__":
    run()

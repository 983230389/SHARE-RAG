from tree_sitter import Parser
from tree_sitter_languages import get_language

def get_parser(language: str) -> Parser:
    """
    language: cpp | python | java
    """
    parser = Parser()
    parser.set_language(get_language(language))
    return parser

from tree_sitter import Parser
from tree_sitter_languages import get_language

def get_parser(language_name: str) -> Parser:
    parser = Parser()

    if language_name in ("cpp", "c++"):
        lang = get_language("cpp")
    elif language_name == "python":
        lang = get_language("python")
    elif language_name == "java":
        lang = get_language("java")
    else:
        raise ValueError(f"Unsupported language: {language_name}")

    # ✅ tree-sitter 0.21.x 的正确方式
    parser.set_language(lang)
    return parser

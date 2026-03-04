from collections import defaultdict
from tree_sitter import Parser
from tree_sitter_languages import get_language

_PARSERS = {}

def parse_code(code: str, language: str):
    if language not in _PARSERS:
        parser = Parser()
        parser.set_language(get_language(language))
        _PARSERS[language] = parser

    return _PARSERS[language].parse(code.encode("utf-8"))

CONTROL_NODES = {
    "cpp": {
        "if_statement",
        "for_statement",
        "while_statement",
        "do_statement",
        "switch_statement",
        "try_statement",
    },
    "python": {
        "if_statement",
        "for_statement",
        "while_statement",
        "try_statement",
    },
    "java": {
        "if_statement",
        "for_statement",
        "while_statement",
        "do_statement",
        "switch_expression",
        "try_statement",
    },
}

LOOP_NODES = {
    "cpp": {"for_statement", "while_statement", "do_statement"},
    "python": {"for_statement", "while_statement"},
    "java": {"for_statement", "while_statement", "do_statement"},
}

def extract_cfg_features(code: str, language: str):
    tree = parse_code(code, language)

    stats = {
        "num_if": 0,
        "num_if_else": 0,
        "nested_if": 0,
        "num_loops": 0,
        "early_exit": False,
        "loop_with_conditional_exit": 0
    }

    def visit(node, depth, in_if=False, in_loop=False):
        if node.type == "if_statement":
            stats["num_if"] += 1
            if any(c.type == "else_clause" for c in node.children):
                stats["num_if_else"] += 1
            if in_if:
                stats["nested_if"] += 1
            in_if = True

        if node.type in LOOP_NODES.get(language, set()):
            stats["num_loops"] += 1
            in_loop = True

        if node.type in {"break_statement", "continue_statement", "return_statement"}:
            if in_loop:
                stats["early_exit"] = True

        for c in node.children:
            visit(c, depth + 1, in_if, in_loop)

    visit(tree.root_node, 0)

    return {
        "control_flow_shape": stats
    }

from collections import defaultdict
from tree_sitter import Parser
from tree_sitter_languages import get_language
from collections import Counter

_PARSERS = {}
LOOP_NODES = {
    "cpp": {"for_statement", "while_statement", "do_statement"},
    "python": {"for_statement", "while_statement"},
    "java": {"for_statement", "while_statement", "do_statement"},
}


def parse_code(code: str, language: str):
    if language not in _PARSERS:
        parser = Parser()
        parser.set_language(get_language(language))
        _PARSERS[language] = parser

    return _PARSERS[language].parse(code.encode("utf-8"))

ASSIGN_NODES = {
    "cpp": "assignment_expression",
    "python": "assignment",
    "java": "assignment_expression",
}

IDENTIFIER = {
    "cpp": "identifier",
    "python": "identifier",
    "java": "identifier",
}

def extract_identifiers(node, lang):
    vars_ = set()
    if node.type == IDENTIFIER[lang]:
        vars_.add(node.text.decode("utf-8"))
    for c in node.children:
        vars_.update(extract_identifiers(c, lang))
    return vars_

def extract_dfg_features(code: str, language: str):
    tree = parse_code(code, language)

    update_patterns = Counter()
    loop_controlled_vars = set()
    current_loop_vars = []

    def walk(node, in_loop=False):
        if node.type in LOOP_NODES.get(language, set()):
            in_loop = True

        if node.type == ASSIGN_NODES.get(language):
            lhs = node.child_by_field_name("left")
            rhs = node.child_by_field_name("right")

            if lhs and rhs:
                lhs_vars = extract_identifiers(lhs, language)
                rhs_vars = extract_identifiers(rhs, language)

                for lv in lhs_vars:
                    if in_loop:
                        loop_controlled_vars.add(lv)

                for rv in rhs_vars:
                    for lv in lhs_vars:
                        if rv == lv:
                            update_patterns["accumulate"] += 1
                        elif rv.isdigit():
                            update_patterns["reset"] += 1
                        else:
                            update_patterns["overwrite"] += 1

        for c in node.children:
            walk(c, in_loop)

    walk(tree.root_node)

    return {
        "data_flow_semantics": {
            "update_patterns": list(update_patterns.keys()),
            "loop_controlled_vars": list(loop_controlled_vars)
        }
    }

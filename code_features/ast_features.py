from collections import Counter
from tools.treesitter_utils import get_parser

CONTROL_TYPES = {
    "if_statement", "for_statement", "while_statement",
    "do_statement", "switch_statement"
}

def extract_ast_features(code: str, language: str):
    parser = get_parser(language)
    tree = parser.parse(code.encode("utf-8", errors="ignore"))

    max_depth = 0
    control_seq = []
    loop_depths = []
    assignment_in_loop = 0
    total_assignments = 0

    def walk(node, depth=0, in_loop=False):
        nonlocal max_depth, assignment_in_loop, total_assignments
        max_depth = max(max_depth, depth)

        if node.type in CONTROL_TYPES:
            control_seq.append(node.type)

        is_loop = node.type in {"for_statement", "while_statement", "do_statement"}
        if is_loop:
            loop_depths.append(depth)

        if node.type in {"assignment", "assignment_expression"}:
            total_assignments += 1
            if in_loop:
                assignment_in_loop += 1

        for c in node.children:
            walk(c, depth + 1, in_loop or is_loop)

    walk(tree.root_node)

    return {
        "ast_shape": {
            "max_depth": max_depth,
            "avg_loop_depth": round(sum(loop_depths) / max(1, len(loop_depths)), 2)
        },
        "control_skeleton": control_seq[:10],  # 截断，防止过长
        "repair_anchors": {
            "assignments_in_loop_ratio": round(
                assignment_in_loop / max(1, total_assignments), 2
            )
        }
    }

from code_features.treesitter_utils import get_parser
from code_features.ast_features import extract_ast_features
from code_features.cfg_features import extract_cfg_features
from code_features.dfg_features import extract_dfg_features

def extract_all_features(code: str, language: str):
    parser = get_parser(language)
    tree = parser.parse(bytes(code, "utf-8"))

    ast_feat = extract_ast_features(tree)
    cfg_feat = extract_cfg_features(tree, language)
    dfg_feat = extract_dfg_features(tree, language)

    return {
        "ast": ast_feat,
        "cfg": cfg_feat,
        "dfg": dfg_feat,
    }

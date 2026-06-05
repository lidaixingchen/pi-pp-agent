import ast
import operator
import math


# 支持的运算符映射
OPERATORS = {
    ast.Add: operator.add,       # +
    ast.Sub: operator.sub,       # -
    ast.Mult: operator.mul,      # *
    ast.Div: operator.truediv,   # /
    ast.FloorDiv: operator.floordiv,  # //
    ast.Pow: operator.pow,       # **
    ast.Mod: operator.mod,       # %
    ast.USub: operator.neg,      # 负号
    ast.UAdd: operator.pos,      # 正号
}

# 支持的数学函数
FUNCTIONS = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval(node: ast.AST) -> float:
    """安全地递归求值AST节点。"""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"不支持的常量类型: {type(node.value)}")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in OPERATORS:
            raise ValueError(f"不支持的运算符: {op_type.__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in OPERATORS:
            raise ValueError(f"不支持的运算符: {op_type.__name__}")
        operand = _safe_eval(node.operand)
        return OPERATORS[op_type](operand)
    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("不支持的函数调用")
        func_name = node.func.id
        if func_name not in FUNCTIONS:
            raise ValueError(f"不支持的函数: {func_name}")
        args = [_safe_eval(arg) for arg in node.args]
        return FUNCTIONS[func_name](*args)
    elif isinstance(node, ast.Name):
        if node.id in FUNCTIONS:
            return FUNCTIONS[node.id]
        raise ValueError(f"未知的变量或函数: {node.id}")
    else:
        raise ValueError(f"不支持的表达式类型: {type(node).__name__}")


def calculate(query: str) -> str:
    """
    安全地计算数学表达式并返回结果。

    支持:
    - 基本运算: +, -, *, /, //, **, %
    - 数学函数: sqrt, sin, cos, tan, log, log10, exp, abs, round
    - 常量: pi, e

    示例:
        calculate("2 + 3 * 4") => "14"
        calculate("sqrt(16) + 2") => "6.0"
        calculate("sin(pi / 2)") => "1.0"
    """
    try:
        expression = query.strip()
        if not expression:
            return "错误: 表达式为空。"

        # 解析表达式为AST
        tree = ast.parse(expression, mode="eval")

        # 安全求值
        result = _safe_eval(tree)

        # 格式化输出（整数结果不显示小数点）
        if isinstance(result, float) and result == int(result) and not math.isinf(result):
            return str(int(result))
        return str(result)

    except ZeroDivisionError:
        return "错误: 除数不能为零。"
    except ValueError as e:
        return f"错误: {e}"
    except SyntaxError:
        return f"错误: 表达式语法无效 - {expression}"
    except Exception as e:
        return f"错误: 计算时出现问题 - {e}"

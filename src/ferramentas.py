import ast
import operator as _op
import subprocess
import sys
import tempfile
import textwrap
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

busca_web = DuckDuckGoSearchRun(name="busca_web", timeout=15)

_OPS = {
    ast.Add: _op.add, ast.Sub: _op.sub,
    ast.Mult: _op.mul, ast.Div: _op.truediv,
    ast.Pow: _op.pow, ast.USub: _op.neg,
    ast.Mod: _op.mod, ast.FloorDiv: _op.floordiv,
}


def _eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError(f"Operação não permitida: {type(node).__name__}")


@tool
def calcular(expressao: str) -> str:
    """Avalia uma expressão matemática. Ex: '2**10', '(15*3)/2', '1000*(1.05**12)'."""
    try:
        tree = ast.parse(expressao.strip(), mode="eval")
        return str(_eval(tree.body))
    except Exception as e:
        return f"Erro ao calcular: {e}"


@tool
def executar_codigo(codigo: str, linguagem: str = "python") -> str:
    """Executa um trecho de código e retorna o resultado (stdout + stderr). Timeout: 10s.
    Suporta linguagem='python'. Use para verificar se o código funciona corretamente."""
    if linguagem.lower() not in ("python", "python3"):
        return "Erro: apenas Python é suportado no momento."
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(textwrap.dedent(codigo))
        path = f.name
    try:
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True, timeout=10,
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        if result.returncode == 0:
            return out if out else "(sem saída)"
        return f"Erro (código {result.returncode}):\n{err}" if err else f"Erro (código {result.returncode})"
    except subprocess.TimeoutExpired:
        return "Erro: timeout (>10s). O código demorou demais para executar."
    except Exception as e:
        return f"Erro ao executar: {e}"

import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from src.grafo import app

load_dotenv()


def main():
    if len(sys.argv) > 1:
        objetivo = " ".join(sys.argv[1:])
    else:
        objetivo = input("Objetivo: ").strip()

    print(f"\nProcessando: {objetivo}")
    print("─" * 60)

    estado_final = app.invoke({
        "messages": [HumanMessage(content=objetivo)],
        "proximo": "",
        "ciclos_react": 0,
    })

    print("─" * 60)
    print("\nResposta final:")
    print(estado_final["messages"][-1].content)


if __name__ == "__main__":
    main()

"""Citizen Assist AI Mobilidade: assistente de orientação sobre ônibus em São Paulo.

Execute com: python main.py
"""

import os

from assistente import Assistente, EntradaEncerrada, ler_opcao
from base_conhecimento import BaseConhecimento

# Caminhos relativos à pasta deste arquivo, para funcionar de qualquer diretório.
PASTA = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BASE = os.path.join(PASTA, "data", "base_conhecimento.json")
CAMINHO_HISTORICO = os.path.join(PASTA, "data", "historico.json")
CAMINHO_CSV = os.path.join(PASTA, "data", "atendimentos.csv")

MENU = """
=== Citizen Assist AI Mobilidade ===
Orientações sobre ônibus na cidade de São Paulo.
  1. Fazer uma pergunta
  2. Navegar por categorias
  3. Ver indicadores
  4. Exportar atendimentos (CSV)
  0. Sair"""


def main():
    base = BaseConhecimento(CAMINHO_BASE)
    base.carregar()
    if base.erro:
        print(f"Atenção: {base.erro}")
    if not base.orientacoes:
        print("O assistente vai abrir, mas sem orientações disponíveis.")

    assistente = Assistente("Citizen Assist AI Mobilidade", base, CAMINHO_HISTORICO, CAMINHO_CSV)
    print("Olá! Não digite nome, CPF, telefone ou e-mail: eu não preciso desses dados.")

    try:
        while True:
            print(MENU)
            opcao = ler_opcao("Escolha uma opção: ", 0, 4)
            if opcao == 1:
                assistente.perguntar()
            elif opcao == 2:
                assistente.navegar()
            elif opcao == 3:
                assistente.exibir_indicadores()
            elif opcao == 4:
                assistente.exportar_csv()
            else:
                nota = ler_opcao("\nDe 1 a 5, quão fácil foi usar o assistente? ", 1, 5)
                assistente.registrar_nota(nota)
                assistente.exportar_csv()
                print("Obrigado! Lembre-se: este assistente não é canal oficial.")
                break
    except EntradaEncerrada:
        # Encerramento sem traceback; o que já foi registrado continua salvo.
        assistente.exportar_csv()
        print("Assistente encerrado. Os atendimentos registrados foram salvos.")


if __name__ == "__main__":
    main()

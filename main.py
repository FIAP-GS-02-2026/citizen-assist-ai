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

OPCOES = """  1. Fazer uma pergunta
  2. Navegar por categorias
  3. Ver indicadores
  4. Exportar atendimentos (CSV)
  0. Sair"""


def pedir_nota(assistente):
    """Ao sair, pede a nota de facilidade se houve atendimento nesta sessão."""
    if not assistente.atendimentos_da_sessao():
        print("\nNenhum atendimento nesta sessão, então não há nota de facilidade para registrar.")
        return
    nota = ler_opcao("\nDe 1 a 5, quão fácil foi usar o assistente? (0 para pular) ", 0, 5)
    if nota:
        assistente.registrar_nota(nota)


def main():
    base = BaseConhecimento(CAMINHO_BASE)
    base.carregar()
    if base.erro:
        print(f"Atenção: {base.erro}")
    if not base.orientacoes:
        print("O assistente vai abrir, mas sem orientações disponíveis.")

    assistente = Assistente("Citizen Assist AI Mobilidade", base, CAMINHO_HISTORICO, CAMINHO_CSV)
    if assistente.aviso_historico:
        print(f"Atenção: {assistente.aviso_historico}")
    assistente.saudacao()

    try:
        while True:
            print(f"\n=== {assistente.nome} ===")
            print(OPCOES)
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
                pedir_nota(assistente)
                assistente.exportar_csv()
                print("Obrigado! Lembre-se: este assistente não é canal oficial.")
                break
    except EntradaEncerrada:
        # Encerramento sem traceback; o que já foi registrado continua salvo.
        assistente.exportar_csv()
        print("Assistente encerrado. Os atendimentos registrados foram salvos.")


if __name__ == "__main__":
    main()

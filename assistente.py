"""Classe Assistente: faz o atendimento, guarda o histórico e calcula os indicadores."""

import csv
import json
import os
import time
from datetime import datetime

from base_conhecimento import classificar_confianca

# Tupla com as colunas do CSV exportado (ordem fixa).
COLUNAS_CSV = (
    "data", "sessao", "origem", "pergunta", "id_orientacao", "encontrou",
    "ajudou", "tentativas", "tempo_s", "nota_facilidade",
)

MINIMO_DIGITOS_DADO_PESSOAL = 8
MAX_ALTERNATIVAS = 2


def contem_dado_pessoal(texto):
    """True se o texto tem 8 ou mais dígitos (CPF, telefone, RG) ou um @ (e-mail)."""
    digitos = sum(1 for caractere in texto if caractere.isdigit())
    return digitos >= MINIMO_DIGITOS_DADO_PESSOAL or "@" in texto


class EntradaEncerrada(Exception):
    """A pessoa fechou a entrada (Ctrl+D) ou interrompeu (Ctrl+C): encerrar com segurança."""


def ler_texto(mensagem):
    """input() sem traceback: Ctrl+D ou Ctrl+C viram EntradaEncerrada, tratada no main.py."""
    try:
        return input(mensagem).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise EntradaEncerrada()


def ler_opcao(mensagem, minimo, maximo):
    """Pede um número entre minimo e maximo até receber um válido."""
    while True:
        resposta = ler_texto(mensagem)
        if not resposta:
            print("Resposta vazia. Digite um número.")
            continue
        if not resposta.isdigit():
            print("Digite apenas o número da opção.")
            continue
        numero = int(resposta)
        if minimo <= numero <= maximo:
            return numero
        print(f"Opção fora da faixa. Escolha de {minimo} a {maximo}.")


def ler_sim_nao(mensagem):
    """Pede s ou n até receber um válido. Devolve True para s."""
    while True:
        resposta = ler_texto(mensagem).lower()
        if resposta in ("s", "sim"):
            return True
        if resposta in ("n", "nao", "não"):
            return False
        print("Resposta inválida. Digite s para sim ou n para não.")


class Assistente:
    """Conversa com o cidadão usando a BaseConhecimento (composição)."""

    def __init__(self, nome, base, caminho_historico="data/historico.json",
                 caminho_csv="data/atendimentos.csv"):
        self.nome = nome
        self.base = base
        self.caminho_historico = caminho_historico
        self.caminho_csv = caminho_csv
        self.sessao = datetime.now().strftime("%Y%m%d%H%M%S")
        self.historico = self._carregar_historico()

    # ---------- persistência ----------

    def _carregar_historico(self):
        """Lê o histórico salvo. Arquivo ausente ou corrompido começa um histórico vazio."""
        try:
            with open(self.caminho_historico, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            return dados if isinstance(dados, list) else []
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []

    def _salvar_historico(self):
        pasta = os.path.dirname(self.caminho_historico)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        try:
            with open(self.caminho_historico, "w", encoding="utf-8") as arquivo:
                json.dump(self.historico, arquivo, ensure_ascii=False, indent=2)
        except OSError:
            print("Atenção: não foi possível salvar o histórico.")

    def registrar(self, origem, pergunta, id_orientacao, encontrou, ajudou, tentativas, tempo_s):
        """Salva um atendimento em data/historico.json."""
        atendimento = {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sessao": self.sessao,
            "origem": origem,
            "pergunta": pergunta,
            "id_orientacao": id_orientacao,
            "encontrou": encontrou,
            "ajudou": ajudou,
            "tentativas": tentativas,
            "tempo_s": tempo_s,
            "nota_facilidade": None,
        }
        self.historico.append(atendimento)
        self._salvar_historico()

    def registrar_nota(self, nota):
        """Grava a nota de facilidade (1 a 5) em todos os atendimentos desta sessão."""
        for atendimento in self.historico:
            if atendimento.get("sessao") == self.sessao:
                atendimento["nota_facilidade"] = nota
        self._salvar_historico()

    # ---------- atendimento ----------

    def perguntar(self):
        """Atendimento por texto livre. Um atendimento termina quando a pessoa acha a resposta
        ou volta ao menu; as perguntas reescritas contam como tentativas."""
        if not self.base.orientacoes:
            print("A base de conhecimento está indisponível no momento.")
            return
        inicio = time.time()
        tentativas = 0
        ultima_pergunta = ""
        while True:
            pergunta = ler_texto("\nDigite sua dúvida (0 para voltar): ")
            if pergunta == "0":
                if tentativas > 0:
                    # Saiu sem encontrar: dúvida sem solução.
                    self.registrar("pergunta", ultima_pergunta, None, False, False,
                                   tentativas, round(time.time() - inicio, 1))
                return
            if not pergunta:
                print("A pergunta está vazia. Escreva sua dúvida com algumas palavras.")
                continue
            if contem_dado_pessoal(pergunta):
                # Não conta tentativa e não registra nada.
                print("Atenção: não digite CPF, telefone, e-mail ou outros dados pessoais. Reescreva.")
                continue

            tentativas += 1
            ultima_pergunta = pergunta
            resultados = self.base.buscar(pergunta)
            melhor_pontos = resultados[0][0] if resultados else 0
            confianca = classificar_confianca(melhor_pontos)

            if confianca is None:
                print("\nNão encontrei uma orientação para essa dúvida.")
                print("Tente outras palavras ou veja as categorias: " + ", ".join(self.base.categorias()) + ".")
                continue

            pontos, melhor = resultados[0]
            tempo_s = round(time.time() - inicio, 1)
            print(f"\nConfiança da resposta: {confianca} ({pontos} pontos)")
            melhor.exibir()
            alternativas = [o for p, o in resultados[1:1 + MAX_ALTERNATIVAS] if p >= 3]
            if alternativas:
                print("\nTalvez também ajude:")
                for orientacao in alternativas:
                    print(f"  - {orientacao.titulo} [{orientacao.categoria}]")
            ajudou = ler_sim_nao("\nEssa orientação respondeu sua dúvida? (s/n): ")
            self.registrar("pergunta", pergunta, melhor.id, True, ajudou, tentativas, tempo_s)
            if ajudou:
                return
            # Não ajudou: começa um novo atendimento.
            inicio = time.time()
            tentativas = 0
            ultima_pergunta = ""

    def navegar(self):
        """Atendimento por categorias, com '0 para voltar' em todas as telas."""
        if not self.base.orientacoes:
            print("A base de conhecimento está indisponível no momento.")
            return
        while True:
            inicio = time.time()
            categorias = self.base.categorias()
            print("\nCategorias:")
            for numero, categoria in enumerate(categorias, start=1):
                print(f"  {numero}. {categoria}")
            print("  0. Voltar")
            escolha = ler_opcao("Escolha uma categoria: ", 0, len(categorias))
            if escolha == 0:
                return
            categoria = categorias[escolha - 1]
            tentativas = 1
            while True:
                orientacoes = self.base.por_categoria(categoria)
                print(f"\n{categoria}:")
                for numero, orientacao in enumerate(orientacoes, start=1):
                    print(f"  {numero}. {orientacao.titulo}")
                print("  0. Voltar")
                item = ler_opcao("Escolha uma orientação: ", 0, len(orientacoes))
                if item == 0:
                    break
                orientacao = orientacoes[item - 1]
                tempo_s = round(time.time() - inicio, 1)
                orientacao.exibir()
                ajudou = ler_sim_nao("\nEssa orientação respondeu sua dúvida? (s/n): ")
                self.registrar("categoria", f"categoria: {categoria}", orientacao.id, True,
                               ajudou, tentativas, tempo_s)
                tentativas += 1
                inicio = time.time()

    # ---------- indicadores ----------

    def indicadores(self):
        """Calcula e devolve os indicadores do histórico completo (dicionário)."""
        total = len(self.historico)
        encontrados = [a for a in self.historico if a.get("encontrou")]
        ajudaram = [a for a in self.historico if a.get("ajudou")]
        tempos = [a["tempo_s"] for a in encontrados if isinstance(a.get("tempo_s"), (int, float))]
        tentativas = [a["tentativas"] for a in self.historico if isinstance(a.get("tentativas"), int)]
        # Uma nota por sessão (a mesma nota está gravada em todos os atendimentos dela).
        notas_por_sessao = {}
        for atendimento in self.historico:
            nota = atendimento.get("nota_facilidade")
            if isinstance(nota, int):
                notas_por_sessao[atendimento.get("sessao")] = nota
        notas = list(notas_por_sessao.values())
        sem_solucao = [a["pergunta"] for a in self.historico
                       if not a.get("ajudou") and a.get("pergunta")]

        def media(valores):
            return round(sum(valores) / len(valores), 1) if valores else None

        def percentual(parte):
            return round(100 * len(parte) / total, 1) if total else None

        return {
            "total_atendimentos": total,
            "resposta_encontrada_pct": percentual(encontrados),
            "taxa_acerto_ajudou_pct": percentual(ajudaram),
            "tempo_medio_s": media(tempos),
            "tentativas_media": media(tentativas),
            "facilidade_media": media(notas),
            "avaliacoes_facilidade": len(notas),
            "duvidas_sem_solucao": sem_solucao,
        }

    def exibir_indicadores(self):
        dados = self.indicadores()
        if not dados["total_atendimentos"]:
            print("\nAinda não há atendimentos registrados.")
            return

        def formato(valor, sufixo=""):
            return "sem dados" if valor is None else f"{valor}{sufixo}"

        print("\n=== Indicadores ===")
        print(f"Atendimentos registrados: {dados['total_atendimentos']}")
        print(f"Resposta encontrada: {formato(dados['resposta_encontrada_pct'], '%')}")
        print(f"Taxa de acerto (ajudou): {formato(dados['taxa_acerto_ajudou_pct'], '%')}")
        print(f"Tempo médio para encontrar: {formato(dados['tempo_medio_s'], ' s')}")
        print(f"Tentativas por atendimento: {formato(dados['tentativas_media'])}")
        print(f"Facilidade de uso (1 a 5): {formato(dados['facilidade_media'])}"
              f" em {dados['avaliacoes_facilidade']} avaliação(ões)")
        print("Dúvidas sem solução:")
        if dados["duvidas_sem_solucao"]:
            for pergunta in dados["duvidas_sem_solucao"]:
                print(f"  - {pergunta}")
        else:
            print("  nenhuma")

    def exportar_csv(self):
        """Exporta todos os atendimentos para data/atendimentos.csv com csv.DictWriter."""
        pasta = os.path.dirname(self.caminho_csv)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        try:
            with open(self.caminho_csv, "w", newline="", encoding="utf-8") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS_CSV, extrasaction="ignore")
                escritor.writeheader()
                for atendimento in self.historico:
                    escritor.writerow(atendimento)
        except OSError:
            print("Atenção: não foi possível exportar o CSV.")
            return False
        nome = os.path.join(os.path.basename(pasta), os.path.basename(self.caminho_csv)) if pasta else self.caminho_csv
        print(f"\n{len(self.historico)} atendimento(s) exportado(s) para {nome}.")
        return True

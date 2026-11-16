"""Classe Assistente: faz o atendimento, guarda o histórico e calcula os indicadores."""

import csv
import json
import os
import time
from datetime import datetime

from base_conhecimento import LIMITE_MEDIA, classificar_confianca, normalizar

# Tupla com as colunas do CSV exportado (ordem fixa).
COLUNAS_CSV = (
    "data", "sessao", "origem", "pergunta", "id_orientacao", "encontrou",
    "ajudou", "tentativas", "tempo_s", "nota_facilidade", "perguntas_sem_resultado",
)

MINIMO_DIGITOS_DADO_PESSOAL = 8
MAX_ALTERNATIVAS = 2


# Além da regra do enunciado (8 dígitos ou @), frases que indicam que a pessoa
# está se identificando. Comparadas já normalizadas (sem acento, minúsculas).
FRASES_DADO_PESSOAL = (
    "meu nome", "me chamo", "meu cpf", "meu rg", "meu telefone", "meu celular",
    "meu email", "meu e mail", "meu endereco", "moro na rua", "moro na avenida", "moro no numero",
)


def contem_dado_pessoal(texto):
    """True se o texto parece trazer dado pessoal.

    Regra do enunciado: 8 ou mais dígitos (CPF, telefone, RG) ou um @ (e-mail).
    Regra extra: frases como "meu nome é" ou "moro na rua".
    """
    digitos = sum(1 for caractere in texto if caractere.isdigit())
    if digitos >= MINIMO_DIGITOS_DADO_PESSOAL or "@" in texto:
        return True
    texto_norm = normalizar(texto)
    return any(f" {frase} " in texto_norm for frase in FRASES_DADO_PESSOAL)


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
        # isascii() evita aceitar dígitos como "²", que isdigit() aceita mas int() não converte.
        if not (resposta.isascii() and resposta.isdigit()):
            print("Digite apenas o número da opção.")
            continue
        numero = int(resposta)
        if minimo <= numero <= maximo:
            return numero
        print(f"Opção fora da faixa. Escolha de {minimo} a {maximo}.")


def ler_sim_nao(mensagem):
    """Pede s, n ou 0 até receber um válido. Devolve True (s), False (n) ou None (0 = voltar)."""
    while True:
        resposta = ler_texto(mensagem).lower()
        if resposta in ("s", "sim"):
            return True
        if resposta in ("n", "nao", "não"):
            return False
        if resposta == "0":
            return None
        print("Resposta inválida. Digite s para sim, n para não ou 0 para voltar.")


def _sem_repetir(itens):
    """Remove repetições mantendo a ordem."""
    vistos = []
    for item in itens:
        if item not in vistos:
            vistos.append(item)
    return vistos


class Assistente:
    """Conversa com o cidadão usando a BaseConhecimento (composição)."""

    def __init__(self, nome, base, caminho_historico="data/historico.json",
                 caminho_csv="data/atendimentos.csv"):
        self.nome = nome
        self.base = base
        self.caminho_historico = caminho_historico
        self.caminho_csv = caminho_csv
        self.sessao = datetime.now().strftime("%Y%m%d%H%M%S")
        self.aviso_historico = None
        self.historico = self._carregar_historico()

    def saudacao(self):
        print(f"Olá! Eu sou o {self.nome}. Oriento sobre ônibus na cidade de São Paulo.")
        print("Não digite nome, CPF, telefone ou e-mail: eu não preciso desses dados.")

    # ---------- persistência ----------

    def _carregar_historico(self):
        """Lê o histórico salvo.

        Arquivo ausente começa vazio. Arquivo corrompido é guardado com outro nome
        (nada se perde) e o histórico recomeça. Itens que não são dicionário são ignorados.
        """
        try:
            with open(self.caminho_historico, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError:
            return []
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError, OSError):
            copia = self.caminho_historico + ".corrompido-" + self.sessao
            try:
                os.replace(self.caminho_historico, copia)
                self.aviso_historico = f"Histórico corrompido foi guardado em {os.path.basename(copia)}; começando um novo."
            except OSError:
                self.aviso_historico = "Histórico ilegível; começando um novo."
            return []
        if not isinstance(dados, list):
            self.aviso_historico = "Histórico em formato inesperado; começando um novo."
            return []
        return [item for item in dados if isinstance(item, dict)]

    def _salvar_historico(self):
        pasta = os.path.dirname(self.caminho_historico)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        try:
            with open(self.caminho_historico, "w", encoding="utf-8") as arquivo:
                json.dump(self.historico, arquivo, ensure_ascii=False, indent=2)
        except OSError:
            print("Atenção: não foi possível salvar o histórico.")

    def registrar(self, origem, pergunta, id_orientacao, encontrou, ajudou, tentativas, tempo_s,
                  perguntas_sem_resultado=None):
        """Salva um atendimento em data/historico.json.

        ajudou pode ser True, False ou None (a pessoa voltou sem responder).
        perguntas_sem_resultado guarda as formulações que não acharam nada antes da final.
        """
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
            "perguntas_sem_resultado": list(perguntas_sem_resultado or []),
        }
        self.historico.append(atendimento)
        self._salvar_historico()

    def atendimentos_da_sessao(self):
        return [a for a in self.historico if a.get("sessao") == self.sessao]

    def registrar_nota(self, nota):
        """Grava a nota de facilidade (1 a 5) em todos os atendimentos desta sessão."""
        for atendimento in self.atendimentos_da_sessao():
            atendimento["nota_facilidade"] = nota
        self._salvar_historico()

    # ---------- atendimento ----------

    def perguntar(self):
        """Atendimento por texto livre.

        Um atendimento termina quando a pessoa responde se a orientação ajudou ou volta ao menu.
        Cada pergunta válida conta uma tentativa; as que não acharam nada ficam guardadas.
        """
        if not self.base.orientacoes:
            print("A base de conhecimento está indisponível no momento.")
            return
        inicio = time.time()
        tentativas = 0
        sem_resultado = []
        try:
            while True:
                pergunta = ler_texto("\nDigite sua dúvida (0 para voltar): ")
                if pergunta == "0":
                    if tentativas > 0:
                        # Saiu sem encontrar: dúvida sem solução.
                        self.registrar("pergunta", sem_resultado[-1], None, False, False, tentativas,
                                       round(time.time() - inicio, 1), sem_resultado[:-1])
                    return
                if not pergunta:
                    print("A pergunta está vazia. Escreva sua dúvida com algumas palavras.")
                    continue
                if contem_dado_pessoal(pergunta):
                    # Não conta tentativa e não registra nada.
                    print("Atenção: não digite nome, CPF, telefone, e-mail ou endereço. Reescreva sem dados pessoais.")
                    continue

                tentativas += 1
                resultados = self.base.buscar(pergunta)
                melhor_pontos = resultados[0][0] if resultados else 0
                confianca = classificar_confianca(melhor_pontos)

                if confianca is None:
                    sem_resultado.append(pergunta)
                    print("\nNão encontrei uma orientação para essa dúvida.")
                    print("Tente outras palavras ou veja as categorias: " + ", ".join(self.base.categorias()) + ".")
                    continue

                pontos, melhor = resultados[0]
                tempo_s = round(time.time() - inicio, 1)
                print(f"\nConfiança da resposta: {confianca} ({pontos} pontos)")
                melhor.exibir()
                alternativas = [o for p, o in resultados[1:1 + MAX_ALTERNATIVAS] if p >= LIMITE_MEDIA]
                if alternativas:
                    print("\nTalvez também ajude:")
                    for orientacao in alternativas:
                        print(f"  - {orientacao.titulo} [{orientacao.categoria}]")
                try:
                    ajudou = ler_sim_nao("\nEssa orientação respondeu sua dúvida? (s/n, 0 para voltar): ")
                except EntradaEncerrada:
                    # Fechou sem responder: registra a resposta mostrada, sem avaliação.
                    self.registrar("pergunta", pergunta, melhor.id, True, None, tentativas, tempo_s, sem_resultado)
                    raise
                self.registrar("pergunta", pergunta, melhor.id, True, ajudou, tentativas, tempo_s, sem_resultado)
                if ajudou is not False:
                    return
                # Não ajudou: começa um novo atendimento.
                inicio = time.time()
                tentativas = 0
                sem_resultado = []
        except EntradaEncerrada:
            if sem_resultado and tentativas == len(sem_resultado):
                # Fechou depois de não encontrar: guarda como dúvida sem solução.
                self.registrar("pergunta", sem_resultado[-1], None, False, False, tentativas,
                               round(time.time() - inicio, 1), sem_resultado[:-1])
            raise

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
                ajudou = ler_sim_nao("\nEssa orientação respondeu sua dúvida? (s/n, 0 para voltar): ")
                self.registrar("categoria", f"{categoria} > {orientacao.titulo}", orientacao.id, True,
                               ajudou, 1, tempo_s)
                inicio = time.time()

    # ---------- indicadores ----------

    def indicadores(self):
        """Calcula e devolve os indicadores do histórico completo (dicionário)."""
        total = len(self.historico)
        encontrados = [a for a in self.historico if a.get("encontrou") is True]
        ajudaram = [a for a in self.historico if a.get("ajudou") is True]
        tempos = [a["tempo_s"] for a in encontrados
                  if isinstance(a.get("tempo_s"), (int, float)) and not isinstance(a.get("tempo_s"), bool)]
        tentativas = [a["tentativas"] for a in self.historico
                      if isinstance(a.get("tentativas"), int) and not isinstance(a.get("tentativas"), bool)]
        # Uma nota por sessão (a mesma nota está gravada em todos os atendimentos dela).
        notas_por_sessao = {}
        for atendimento in self.historico:
            nota = atendimento.get("nota_facilidade")
            if isinstance(nota, int) and not isinstance(nota, bool) and 1 <= nota <= 5:
                notas_por_sessao[atendimento.get("sessao")] = nota
        notas = list(notas_por_sessao.values())
        # Dúvida sem solução: não encontrou nada ou a pessoa disse que não ajudou.
        sem_solucao = _sem_repetir(str(a.get("pergunta")) for a in self.historico
                                   if (a.get("encontrou") is False or a.get("ajudou") is False) and a.get("pergunta"))
        nao_reconhecidas = _sem_repetir(str(p) for a in self.historico
                                        for p in (a.get("perguntas_sem_resultado") or []))

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
            "perguntas_reescritas": nao_reconhecidas,
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
        for pergunta in dados["duvidas_sem_solucao"] or ["nenhuma"]:
            print(f"  - {pergunta}")
        if dados["perguntas_reescritas"]:
            print("Perguntas que não foram entendidas na primeira tentativa (pistas de novas palavras-chave):")
            for pergunta in dados["perguntas_reescritas"]:
                print(f"  - {pergunta}")

    def exportar_csv(self):
        """Exporta todos os atendimentos para data/atendimentos.csv com csv.DictWriter.

        Usa utf-8-sig para os acentos aparecerem certos ao abrir no Excel.
        """
        pasta = os.path.dirname(self.caminho_csv)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        try:
            with open(self.caminho_csv, "w", newline="", encoding="utf-8-sig") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS_CSV, extrasaction="ignore")
                escritor.writeheader()
                for atendimento in self.historico:
                    linha = dict(atendimento)
                    linha["perguntas_sem_resultado"] = " | ".join(
                        str(p) for p in (atendimento.get("perguntas_sem_resultado") or []))
                    escritor.writerow(linha)
        except OSError:
            print("Atenção: não foi possível exportar o CSV.")
            return False
        nome = os.path.join(os.path.basename(pasta), os.path.basename(self.caminho_csv)) if pasta else self.caminho_csv
        print(f"\n{len(self.historico)} atendimento(s) exportado(s) para {nome}.")
        return True

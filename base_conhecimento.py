"""Classe BaseConhecimento: lê o JSON, lista categorias e busca a melhor orientação."""

import json

from orientacao import Orientacao

# Regras de pontuação da busca (seção 6.2 do enunciado).
PONTOS_PALAVRA_CHAVE = 3      # palavra-chave da orientação encontrada na pergunta
PONTOS_PALAVRA_TITULO = 1     # palavra da pergunta (4 letras ou mais) presente no título
TAMANHO_MINIMO_PALAVRA = 4
LIMITE_ALTA = 6               # 6 pontos ou mais = confiança ALTA
LIMITE_MEDIA = 3              # 3 a 5 pontos = confiança MÉDIA; abaixo disso, "não encontrei"

ACENTOS = {"á": "a", "à": "a", "ã": "a", "â": "a", "é": "e", "ê": "e",
           "í": "i", "ó": "o", "õ": "o", "ô": "o", "ú": "u", "ç": "c"}


def normalizar(texto):
    """Deixa o texto em minúsculas, sem acentos e sem pontuação, com espaços nas pontas.

    Os espaços nas pontas fazem " sus " casar só com a palavra inteira.
    """
    texto = texto.lower().strip()
    for letra, troca in ACENTOS.items():
        texto = texto.replace(letra, troca)
    for sinal in "?!.,;:()/-\"'":
        texto = texto.replace(sinal, " ")
    return " " + " ".join(texto.split()) + " "


def classificar_confianca(pontos):
    """Devolve 'ALTA', 'MÉDIA' ou None (não encontrado) a partir da pontuação."""
    if pontos >= LIMITE_ALTA:
        return "ALTA"
    if pontos >= LIMITE_MEDIA:
        return "MÉDIA"
    return None


class BaseConhecimento:
    """Conjunto de todas as orientações carregadas do arquivo JSON."""

    def __init__(self, caminho):
        self.caminho = caminho
        self.orientacoes = []
        self.erro = None   # mensagem amigável quando o arquivo não pôde ser lido

    def carregar(self):
        """Lê o JSON e cria os objetos Orientacao.

        Nunca derruba o programa: arquivo ausente ou corrompido vira uma mensagem em self.erro.
        Registros com campo faltando são ignorados e contados no aviso.
        Devolve True se ao menos uma orientação foi carregada.
        """
        self.orientacoes = []
        self.erro = None
        try:
            with open(self.caminho, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError:
            self.erro = f"Arquivo da base não encontrado: {self.caminho}"
            return False
        except json.JSONDecodeError:
            self.erro = f"Arquivo da base está corrompido (JSON inválido): {self.caminho}"
            return False
        except OSError:
            self.erro = f"Não foi possível abrir o arquivo da base: {self.caminho}"
            return False

        if not isinstance(dados, list):
            self.erro = "A base precisa ser uma lista de orientações."
            return False

        ignorados = 0
        for registro in dados:
            try:
                self.orientacoes.append(Orientacao.de_dicionario(registro))
            except (ValueError, TypeError):
                ignorados += 1
        if ignorados:
            self.erro = f"{ignorados} orientação(ões) com campos faltando foram ignoradas."
        return len(self.orientacoes) > 0

    def categorias(self):
        """Lista as categorias sem repetição, em ordem alfabética."""
        return sorted({orientacao.categoria for orientacao in self.orientacoes})

    def por_categoria(self, categoria):
        """Lista as orientações de uma categoria, na ordem do id."""
        return sorted((o for o in self.orientacoes if o.categoria == categoria), key=lambda o: o.id)

    def pontuar(self, pergunta, orientacao):
        """Calcula a pontuação de uma orientação para a pergunta.

        +3 para cada palavra-chave que aparece na pergunta;
        +1 para cada palavra da pergunta (4 letras ou mais) que aparece no título.
        """
        pergunta_norm = normalizar(pergunta)
        pontos = 0
        for palavra_chave in orientacao.palavras_chave:
            if normalizar(palavra_chave) in pergunta_norm:
                pontos += PONTOS_PALAVRA_CHAVE
        palavras_titulo = set(normalizar(orientacao.titulo).split())
        palavras_pergunta = set(pergunta_norm.split())
        for palavra in palavras_pergunta:
            if len(palavra) >= TAMANHO_MINIMO_PALAVRA and palavra in palavras_titulo:
                pontos += PONTOS_PALAVRA_TITULO
        return pontos

    def buscar(self, pergunta):
        """Devolve uma lista de tuplas (pontos, orientacao), da maior para a menor pontuação.

        Só entram orientações com pelo menos 1 ponto. Em empate, vem primeiro o menor id.
        """
        resultados = []
        for orientacao in self.orientacoes:
            pontos = self.pontuar(pergunta, orientacao)
            if pontos > 0:
                resultados.append((pontos, orientacao))
        resultados.sort(key=lambda tupla: (-tupla[0], tupla[1].id))
        return resultados

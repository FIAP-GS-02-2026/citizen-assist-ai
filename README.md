# Citizen Assist AI Mobilidade

Assistente no terminal que orienta quem usa ônibus na cidade de São Paulo: gratuidades, Bilhete Único, tarifas, acessibilidade e onde reclamar. Responde só com informação de fontes oficiais, mostra a fonte e a data em que foi conferida e avisa que não é canal oficial.

Global Solution 2026.2 · FIAP · Ciência da Computação 1CCR · Pensamento Computacional e Automação com Python.

## Integrantes

| Nome | RM |
| --- | --- |
| Glauco Kelly | 572840 |
| Gabriel Fagundes | 569074 |
| Thiago Renatino | 569073 |

## Público e problema

**Público:** quem depende de ônibus municipal em São Paulo, em especial:

- pessoas idosas;
- pessoas com deficiência;
- estudantes;
- pessoas com pouca familiaridade digital.

**Problema:** a informação sobre direitos e serviços do transporte existe, mas está espalhada entre SP156, SPTrans e Prefeitura, e há regras antigas circulando. Exemplos:

- muitos sites ainda dizem que a gratuidade do idoso começa aos 65 anos, mas o Decreto Municipal 62.057/2022 estendeu a gratuidade a partir dos 60;
- pouca gente sabe que o ônibus é de graça aos domingos.

O assistente junta essas orientações num só lugar, em linguagem simples e com a fonte.

## ODS relacionados

- **ODS 11 (Cidades e comunidades sustentáveis)**, meta 11.2: acesso a transporte seguro, acessível e sustentável, com atenção a idosos e pessoas com deficiência.
- **ODS 10 (Redução das desigualdades)**: informação sobre gratuidades para quem mais precisa.

## Como executar

Requer Python 3.9 ou superior. Não usa bibliotecas externas.

```bash
python main.py
```

Testes automatizados (opcional):

```bash
python -m unittest -v
```

## Estrutura

```
citizen-assist-ai/
├── README.md
├── main.py                  menu principal
├── orientacao.py            classe Orientacao
├── base_conhecimento.py     classe BaseConhecimento e a busca por pontuação
├── assistente.py            classe Assistente: atendimento, histórico, indicadores e CSV
├── data/
│   ├── base_conhecimento.json   orientações com fonte oficial
│   ├── historico.json           atendimentos registrados
│   └── atendimentos.csv         exportação dos atendimentos
└── tests/                   bateria de testes (unittest)
```

**Composição das classes:**

```
Assistente
 └── base: BaseConhecimento
      └── orientacoes: [Orientacao, Orientacao, ...]
```

## Base de conhecimento

`data/base_conhecimento.json` é uma lista de dicionários, um por orientação, com os campos `id`, `categoria`, `titulo`, `palavras_chave`, `resposta`, `documentos`, `onde`, `fonte` e `verificado_em`.

- 17 orientações em 6 categorias: Gratuidades, Tarifas, Bilhete Único, Acessibilidade, Atendimento e reclamação, Linhas e horários.
- Todas foram conferidas em 16/11/2026 nas páginas oficiais citadas.

**Uso de dicionários e tuplas:**

- cada registro do JSON é lido como dicionário e vira um objeto `Orientacao`;
- os campos obrigatórios ficam numa tupla (`CAMPOS_OBRIGATORIOS`);
- a busca devolve tuplas `(pontos, orientacao)`.

## Regra de pontuação

A pergunta, as palavras-chave e o título são comparados sem acentos, sem pontuação e em minúsculas (`normalizar()`).

| Regra | Resultado |
| --- | --- |
| Palavra-chave da orientação aparece na pergunta (palavra inteira) | +3 pontos |
| Palavra da pergunta com 4 letras ou mais aparece no título | +1 ponto |
| Melhor orientação com 6 pontos ou mais | Confiança ALTA |
| Melhor orientação com 3 a 5 pontos | Confiança MÉDIA |
| Nenhuma orientação com 3 pontos | "Não encontrei" + sugestão de categorias |

`buscar()` devolve a lista de tuplas `(pontos, orientacao)` da maior para a menor pontuação. Em empate, vence o menor `id`. O assistente mostra a melhor orientação e até duas alternativas com pelo menos 3 pontos.

**Exemplo:** "Tenho 62 anos, pago ônibus?" soma 5 pontos na orientação 2, e a confiança é MÉDIA:

- +3 pela palavra-chave "62 anos";
- +1 por "anos" no título;
- +1 por "onibus" no título.

## Regras de atendimento

- **Navegação:** por categorias numeradas, com "0 para voltar" em todas as telas.
- **Entradas inválidas:** opção fora da faixa, letras, resposta vazia ou s/n inválido nunca encerram o programa. Ctrl+D e Ctrl+C encerram com segurança e salvam o que já foi registrado.
- **Dados pessoais:** o assistente nunca pede nome, CPF, telefone ou e-mail. Pergunta com 8 ou mais dígitos ou com @ é recusada e não é registrada.
- **Transparência:** toda resposta mostra a fonte, a data de verificação e o aviso de que o assistente não é canal oficial.
- **Arquivos:** JSON da base ausente ou corrompido não trava o programa. Registros com campo faltando são ignorados com aviso.

## Histórico, indicadores e CSV

Cada atendimento é salvo em `data/historico.json` com estes campos:

- `data`;
- `sessao`;
- `origem` (pergunta ou categoria);
- `pergunta`;
- `id_orientacao`;
- `encontrou`;
- `ajudou`;
- `tentativas`;
- `tempo_s`, medido com `time.time()`;
- `nota_facilidade`.

Ao sair, o assistente pede uma nota de facilidade de 1 a 5 e a grava nos atendimentos daquela sessão.

**Indicadores calculados (menu 3):**

- resposta encontrada (%);
- taxa de acerto, ou seja, ajudou (%);
- tempo médio para encontrar;
- tentativas por atendimento;
- facilidade de uso (1 a 5);
- lista de dúvidas sem solução.

A exportação para `data/atendimentos.csv` usa `csv.DictWriter`, pelo menu 4 e automaticamente ao sair.

## Integrações com outras disciplinas

Todas as disciplinas do grupo na GS 2026.2 usam o mesmo tema, mobilidade urbana. Nenhuma integração com código de outra disciplina foi feita neste repositório.

## Fontes consultadas

Todas foram acessadas em 16/11/2026.

- SP156, Prefeitura de São Paulo:
  - pessoa idosa: https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?conteudo=4268
  - pessoa com deficiência: https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?conteudo=4326
  - estudante: https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?t=&a=NTgx&conteudo=1325
  - Bilhete Único Comum: https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?t=&a=Nzc4&conteudo=1322
  - segunda via: https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?t=749&conteudo=4035
  - Atende+: https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?conteudo=1333
  - canais: https://sp156.prefeitura.sp.gov.br/portal/outros-canais-de-atendimento
- SPTrans:
  - tarifas: https://www.sptrans.com.br/tarifas/
  - perguntas e respostas: https://www.sptrans.com.br/perguntas-e-respostas/
  - recarga: https://www.sptrans.com.br/compra-de-creditos-e-servicos
  - linhas noturnas: https://www.sptrans.com.br/linhas-noturnas/
  - ouvidoria: https://www.sptrans.com.br/fale-conosco/ouvidoria-sptrans/
- Prefeitura de São Paulo, pessoa com deficiência (desembarque fora do ponto): https://prefeitura.sp.gov.br/web/pessoa_com_deficiencia/w/publicacoes/307915

## Teste com usuários

*Em andamento: esta seção será preenchida com os resultados reais do teste. A meta é de pelo menos 3 pessoas de fora da equipe e 10 atendimentos.*

## Limitações

- Cobre só o ônibus municipal da cidade de São Paulo. Metrô, trem e ônibus intermunicipal aparecem apenas na integração tarifária.
- As regras e os valores mudam: cada orientação mostra a data em que foi conferida, e a pessoa deve confirmar no canal oficial.
- A busca é por palavras-chave. Perguntas com palavras que não estão na base podem não ser encontradas, e as categorias são a alternativa.
- Não consulta horários nem posição dos ônibus em tempo real.

## Vídeo técnico

*Link será adicionado após a gravação.*

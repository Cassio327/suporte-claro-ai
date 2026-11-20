from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Textos = Annotated[list[Texto], Field(min_length=1)]


class Contrato(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Perfil(Contrato):
    id: Texto
    nivel: Literal["leigo", "intermediário", "avançado"]
    estilo: Literal["direto", "detalhado", "didático"]
    canal: Literal["chat", "e-mail", "telefone"]


class Diagnostico(Contrato):
    hipoteses: Textos
    evidencias: list[Texto]
    dados_faltantes: list[Texto]
    conclusao_provavel: Texto


class Passo(Contrato):
    acao: Texto
    como_verificar: Texto


class Resolucao(Contrato):
    passos: Annotated[list[Passo], Field(min_length=1)]
    quando_encaminhar: Texto


class Pergunta(Contrato):
    pergunta: Texto
    decisao_que_orienta: Texto


class Esclarecimento(Contrato):
    perguntas_em_ordem: Annotated[list[Pergunta], Field(max_length=3)]


class Fluxo(Contrato):
    condicao_observavel: Texto
    se_sim: Texto
    se_nao: Texto
    se_inconclusivo: Texto

    @model_validator(mode="after")
    def distinguir_destinos(self):
        if self.se_sim.casefold() == self.se_nao.casefold():
            raise ValueError("Os dois resultados devem conduzir a ações distintas.")
        return self


TIPOS = {"diagnostico": Diagnostico, "resolucao": Resolucao,
         "perguntas": Esclarecimento, "fluxo": Fluxo}


class Nota(Contrato):
    nota: int = Field(ge=1, le=5)
    justificativa: Texto


class Avaliacao(Contrato):
    clareza: Nota
    adequacao_ao_nivel: Nota
    acionabilidade: Nota


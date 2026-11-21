const formulario = document.getElementById("rubrica");
const statusRubrica = document.getElementById("conclusao");
const criterios = ["clareza", "adequacao_ao_nivel", "acionabilidade"];

formulario.addEventListener("input", (evento) => {
  evento.target.setCustomValidity("");
  statusRubrica.textContent = "";
});

formulario.addEventListener("submit", (evento) => {
  evento.preventDefault();
  const amostra = JSON.parse(document.getElementById("amostra").textContent);
  const data = new Date().toISOString();
  for (const item of amostra.resultados) {
    item.avaliacao = {};
    for (const criterio of criterios) {
      const prefixo = item.id + "-" + criterio;
      const motivo = formulario.elements.namedItem(prefixo + "-motivo");
      const justificativa = motivo.value.trim();
      if (!justificativa) {
        motivo.setCustomValidity("Escreva uma justificativa para esta nota.");
        motivo.reportValidity();
        return;
      }
      const nota = Number(formulario.elements.namedItem(prefixo + "-nota").value);
      item.avaliacao[criterio] = {nota, justificativa};
    }
    item.avaliado_em = data;
  }
  const arquivo = new Blob([JSON.stringify(amostra, null, 2)], {type: "application/json"});
  const link = document.createElement("a");
  const url = URL.createObjectURL(arquivo);
  link.href = url;
  link.download = "upload-v2-v3-avaliado.json";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
  const versoes = amostra.resultados.slice().sort((a, b) => a.id.localeCompare(b.id));
  statusRubrica.textContent = "Download solicitado. Resposta A: " + versoes[0].versao
    + ". Resposta B: " + versoes[1].versao + ".";
});

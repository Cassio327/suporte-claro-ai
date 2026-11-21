const editor = document.getElementById("editor");
const perfil = document.getElementById("perfil");
const tipo = document.getElementById("tipo");
const versao = document.getElementById("versao");
const ticket = document.getElementById("ticket");
const resultado = document.getElementById("resultado");

function atualizar() {
  const experimental = versao.querySelector('option[value="v3"]');
  experimental.disabled = tipo.value !== "resolucao";
  if (experimental.disabled && versao.value === "v3") versao.value = "v2";
  resultado.hidden = true;
  ticket.setCustomValidity("");
}

editor.addEventListener("input", atualizar);
editor.addEventListener("change", atualizar);
editor.addEventListener("submit", (evento) => {
  evento.preventDefault();
  const texto = ticket.value.trim();
  if (!texto) {
    ticket.setCustomValidity("Escreva o ticket do cliente.");
    ticket.reportValidity();
    return;
  }
  const chave = [perfil.value, tipo.value, versao.value].join("/");
  document.getElementById("sistema").textContent = catalogo.sistemas[chave];
  document.getElementById("dados").textContent = JSON.stringify({perfil: catalogo.perfis[perfil.value], ticket: texto}, null, 2);
  resultado.hidden = false;
  resultado.querySelector("h2").focus();
});
atualizar();

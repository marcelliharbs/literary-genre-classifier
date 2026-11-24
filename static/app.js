const statusEl = document.querySelector("#status");
const resultadosEl = document.querySelector("#resultados");
const avisosEl = document.querySelector("#avisos");
let estadoChat = null;

document.querySelectorAll("nav button").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll("nav button").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    button.classList.add("active");
    document.querySelector("#" + button.dataset.tab).classList.add("active");
    if (button.dataset.tab === "mapa") carregarMapa();
  });
});

fetch("/api/status").then(r => r.json()).then(d => {
  statusEl.textContent = `${d.n_livros} livros · ${d.n_generos} grupos`;
}).catch(() => statusEl.textContent = "Servidor indisponível");

function renderItens(itens) {
  resultadosEl.innerHTML = itens.map(item => `
    <article class="card">
      <h3>${item.posicao}. ${item.titulo}</h3>
      ${item.autor ? `<p>${item.autor}</p>` : ""}
      ${item.genero ? `<p class="genero">${item.genero}</p>` : ""}
      <p>Similaridade: ${item.score}</p>
    </article>
  `).join("") || "<p>Nenhum resultado encontrado.</p>";
}

document.querySelector("#form-busca").addEventListener("submit", async event => {
  event.preventEvent?.();
  event.preventDefault();
  avisosEl.textContent = "Buscando...";
  const response = await fetch("/api/buscar", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      consulta: document.querySelector("#consulta").value,
      modelo: "hibrido",
      n: document.querySelector("#n").value
    })
  });
  const data = await response.json();
  if (!response.ok) {
    avisosEl.textContent = data.erro;
    return;
  }
  avisosEl.textContent = (data.avisos || []).join(" ");
  renderItens(data.itens);
});

function adicionarMensagem(tipo, texto) {
  const chat = document.querySelector("#chat-mensagens");
  const div = document.createElement("div");
  div.className = "mensagem " + tipo;
  div.textContent = texto;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

document.querySelector("#form-chat").addEventListener("submit", async event => {
  event.preventDefault();
  const input = document.querySelector("#mensagem");
  const mensagem = input.value.trim();
  if (!mensagem) return;
  adicionarMensagem("usuario", mensagem);
  input.value = "";
  const response = await fetch("/api/chat", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({mensagem, estado:estadoChat})
  });
  const data = await response.json();
  estadoChat = data.estado || estadoChat;
  adicionarMensagem("assistente", data.texto || data.erro);
});

async function carregarMapa() {
  const response = await fetch("/api/mapa?modelo=tfidf");
  const data = await response.json();
  if (!response.ok) return;
  const canvas = document.querySelector("#canvas-mapa");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!data.pontos.length) return;
  const xs = data.pontos.map(p => p.x);
  const ys = data.pontos.map(p => p.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const colors = ["#c65d35","#397367","#7c6ba4","#d49b46","#4f8096","#9d5c63","#708238","#59636e"];
  data.pontos.forEach(p => {
    const x = 30 + (p.x-minX)/(maxX-minX || 1) * (canvas.width-60);
    const y = 30 + (p.y-minY)/(maxY-minY || 1) * (canvas.height-60);
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI*2);
    ctx.fillStyle = colors[p.cluster % colors.length];
    ctx.fill();
  });
}

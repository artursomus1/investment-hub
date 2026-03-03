"""
Launch Investment HUB com tunel publico (Cloudflare).
====================================================
Executa: python launch_public.py

Inicia o Streamlit + cria um tunel Cloudflare automaticamente.
O link publico eh exibido no terminal para compartilhar.
"""

import shutil
import subprocess
import sys
import time
import re
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8501

# Localiza cloudflared (PATH ou caminho padrao do instalador)
CLOUDFLARED = shutil.which("cloudflared") or r"C:\Program Files (x86)\cloudflared\cloudflared.exe"


def main():
    os.chdir(PROJECT_DIR)

    print()
    print("=" * 56)
    print("  SOMUS CAPITAL - Investment HUB")
    print("  Modo publico (tunel Cloudflare)")
    print("=" * 56)
    print()

    # 1) Inicia Streamlit em background
    print("[1/2] Iniciando Streamlit na porta", PORT, "...")
    streamlit_proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "true",
            "--server.address", "0.0.0.0",
            "--server.port", str(PORT),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Aguarda Streamlit subir
    time.sleep(4)
    if streamlit_proc.poll() is not None:
        print("[ERRO] Streamlit nao iniciou. Verifique erros com:")
        print("       streamlit run app.py")
        return 1

    print("       Streamlit rodando (PID", streamlit_proc.pid, ")")
    print()

    # 2) Inicia tunel Cloudflare
    print("[2/2] Criando tunel publico via Cloudflare...")
    print("       (pode levar alguns segundos)")
    print()

    if not os.path.isfile(CLOUDFLARED):
        print("[ERRO] cloudflared nao encontrado.")
        print("       Instale com: winget install Cloudflare.cloudflared")
        streamlit_proc.terminate()
        return 1

    tunnel_proc = subprocess.Popen(
        [CLOUDFLARED, "tunnel", "--url", f"http://localhost:{PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Captura a URL publica do tunel
    public_url = None
    start = time.time()
    while time.time() - start < 30:
        line = tunnel_proc.stdout.readline()
        if not line:
            break
        # Cloudflared imprime a URL no formato: https://xxx.trycloudflare.com
        match = re.search(r"(https://[a-z0-9-]+\.trycloudflare\.com)", line)
        if match:
            public_url = match.group(1)
            break

    if not public_url:
        print("[ERRO] Nao foi possivel obter a URL do tunel.")
        print("       Verifique se cloudflared esta instalado: cloudflared --version")
        streamlit_proc.terminate()
        tunnel_proc.terminate()
        return 1

    # Salva URL em arquivo para o Streamlit ler
    url_file = os.path.join(PROJECT_DIR, ".tunnel_url")
    with open(url_file, "w", encoding="utf-8") as f:
        f.write(public_url)

    # Exibe link
    print("=" * 56)
    print()
    print("  LINK PUBLICO PRONTO!")
    print()
    print(f"  {public_url}")
    print()
    print("  Compartilhe este link com qualquer pessoa.")
    print("  Funciona de qualquer rede/dispositivo.")
    print()
    print("=" * 56)
    print()
    print("  Pressione Ctrl+C para encerrar tudo.")
    print()

    # Mantém rodando ate Ctrl+C
    try:
        while True:
            # Verifica se os processos ainda estao vivos
            if streamlit_proc.poll() is not None:
                print("[AVISO] Streamlit encerrou inesperadamente.")
                break
            if tunnel_proc.poll() is not None:
                print("[AVISO] Tunel Cloudflare encerrou inesperadamente.")
                break
            time.sleep(2)
    except KeyboardInterrupt:
        print()
        print("Encerrando...")

    # Remove arquivo de URL
    if os.path.isfile(url_file):
        os.remove(url_file)

    # Cleanup
    tunnel_proc.terminate()
    streamlit_proc.terminate()
    try:
        tunnel_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        tunnel_proc.kill()
    try:
        streamlit_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        streamlit_proc.kill()

    print("Encerrado com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

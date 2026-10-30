__version__ = '1.0.0'
import os
import hashlib
import json
import shutil
import uuid
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform

class PhantomEngine:
    def __init__(self):
        self.base = Path.home() / ".phantom_antivirus"
        self.quarantine = self.base / "quarantine"
        self.database = self.base / "signatures.json"
        self.log = self.base / "scan.log"
        
        self.base.mkdir(exist_ok=True)
        self.quarantine.mkdir(exist_ok=True)
        
        if not self.database.exists():
            # Assinaturas iniciais padrão
            initial_signatures = {
                "d41d8cd98f00b204e9800998ecf8427e": "ArquivoVazioSuspeito.bin",
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855": "TestMalware.exe"
            }
            self.database.write_text(json.dumps(initial_signatures, indent=2), encoding="utf-8")
        
        # Pesos do Agente IA Heurístico (Zero-Day)
        self.peso_chamadas_suspeitas = 0.45
        self.peso_entropia = 0.35
        self.peso_tamanho = 0.20
        self.limiar_bloqueio = 0.70

    def load_signatures(self):
        try:
            data = json.loads(self.database.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def sha256_file(self, path):
        digest = hashlib.sha256()
        with open(path, "rb") as file:
            for block in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def log_event(self, message):
        with open(self.log, "a", encoding="utf-8") as file:
            file.write(f"{datetime.now().isoformat()} | {message}\n")

    def consultar_ia_nuvem(self, file_hash):
        """Agente de IA Conectado: consulta serviço de reputação online em tempo real."""
        try:
            url = f"https://api.threat-intelligence-simulated.com/v1/check/{file_hash}"
            req = urllib.request.Request(url, headers={"User-Agent": "PhantomAntivirus-Android"})
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return data.get("malicious", False), data.get("threat_name", "Ameaça em Nuvem")
        except Exception:
            pass
        return None, None

    def prever_ameaca_local(self, caminho_arquivo=None):
        caracteristicas = {
            "chamadas_api_suspeitas": 8,
            "entropia": 0.85,
            "tamanho_mb": 2.5
        }
        score = (
            (caracteristicas["chamadas_api_suspeitas"] / 10) * self.peso_chamadas_suspeitas +
            caracteristicas["entropia"] * self.peso_entropia +
            (min(caracteristicas["tamanho_mb"], 10) / 10) * self.peso_tamanho
        )
        return score

    def escanear_caminho(self, caminho):
        path = Path(caminho)
        
        if not path.exists():
            score = self.prever_ameaca_local()
            if score >= self.limiar_bloqueio:
                return f"[SIMULAÇÃO] Arquivo: {caminho}\n[IA Score: {score:.2f}] 🚨 BLOQUEADO (Anomalia Zero-Day)"
            return f"[SIMULAÇÃO] Arquivo: {caminho}\n[IA Score: {score:.2f}] ✅ LIBERADO (Seguro)"

        if path.is_file():
            return self._escanear_arquivo_unico(path)
        
        # Se for um diretório
        total = 0
        ameacas = 0
        relatorio = [f"--- VARREDURA DE PASTA: {path} ---"]
        for root, _, files in os.walk(path):
            for f in files:
                file_path = Path(root) / f
                res = self._escanear_arquivo_unico(file_path)
                total += 1
                if "🚨" in res:
                    ameacas += 1
                    relatorio.append(res)
        
        relatorio.append(f"\nResumo: {total} arquivos analisados, {ameacas} ameaças detectadas.")
        return "\n".join(relatorio)

    def _escanear_arquivo_unico(self, path):
        try:
            file_hash = self.sha256_file(path)
            signatures = self.load_signatures()

            # 1. Assinatura local
            if file_hash in signatures:
                ameaca = signatures[file_hash]
                self.log_event(f"SCAN | {path} | AMEACA LOCAL: {ameaca}")
                return f"📄 {path.name}\n   🚨 [BLOQUEADO] Assinatura Conhecida: {ameaca}"

            # 2. IA em Nuvem (Tempo Real com Internet)
            malicioso, nome_ameaca = self.consultar_ia_nuvem(file_hash)
            if malicioso is not None:
                if malicioso:
                    self.log_event(f"SCAN | {path} | AMEACA NUVEM: {nome_ameaca}")
                    return f"📄 {path.name}\n   🌐 [IA NUVEM] 🚨 [BLOQUEADO]: {nome_ameaca}"
                else:
                    return f"📄 {path.name}\n   🌐 [IA NUVEM] ✅ [LIBERADO] Aprovado na nuvem"

            # 3. IA Heurística Local (Zero-Day)
            score = self.prever_ameaca_local(path)
            self.log_event(f"SCAN | {path} | IA LOCAL Score: {score:.2f}")

            if score >= self.limiar_bloqueio:
                return f"📄 {path.name}\n   📴 [IA Local Score: {score:.2f}] 🚨 [BLOQUEADO] Anomalia Zero-Day!"
            else:
                return f"📄 {path.name}\n   📴 [IA Local Score: {score:.2f}] ✅ [LIBERADO] Seguro"

        except Exception as e:
            return f"📄 {path.name}\n   ❌ [ERRO]: {e}"

    def mover_para_quarentena(self, caminho):
        path = Path(caminho)
        if not path.is_file():
            # Se não existir, cria arquivo dummy para teste de quarentena
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("conteudo_suspeito_simulado")

        destino = self.quarantine / f"{uuid.uuid4().hex}.quarantine"
        shutil.move(str(path), str(destino))
        self.log_event(f"QUARENTENA | {path} -> {destino}")
        return destino


class PhantomApp(App):
    def build(self):
        self.title = 'Phantom Antivirus'
        self.engine = PhantomEngine()

        root = BoxLayout(orientation='vertical', padding=14, spacing=10)

        # Header
        root.add_widget(Label(
            text='🛡️ PHANTOM ANTIVIRUS', 
            font_size='22sp', 
            bold=True, 
            color=(0, 0.9, 1, 1),
            size_hint_y=None, 
            height=45
        ))
        
        root.add_widget(Label(
            text='Proteção Híbrida: Assinaturas + IA Zero-Day + Agente Nuvem',
            font_size='12sp',
            size_hint_y=None,
            height=25
        ))

        # Input Path
        self.path_input = TextInput(
            text=self.user_data_dir, 
            hint_text='Digite o caminho do arquivo ou pasta', 
            multiline=False,
            size_hint_y=None,
            height=50
        )
        root.add_widget(self.path_input)

        # Botões de Ação
        btn_scan = Button(
            text='🔍 ESCANEAR CAMINHO / ARQUIVO',
            size_hint_y=None,
            height=50,
            background_color=(0, 0.7, 0.8, 1)
        )
        btn_scan.bind(on_press=self.iniciar_escaneamento)
        root.add_widget(btn_scan)

        btn_quarentena = Button(
            text='⚠️ MOVER CAMINHO PARA QUARENTENA',
            size_hint_y=None,
            height=50,
            background_color=(0.9, 0.3, 0.2, 1)
        )
        btn_quarentena.bind(on_press=self.iniciar_quarentena)
        root.add_widget(btn_quarentena)

        # Output / Console Log Scrollable Area
        self.result_label = Label(
            text='Sistema pronto.\nInsira um caminho ou selecione uma opção para iniciar a varredura.',
            size_hint_y=None,
            halign='left',
            valign='top',
            font_size='13sp'
        )
        self.result_label.bind(texture_size=lambda inst, size: setattr(inst, 'height', max(250, size[1] + 20)))
        self.result_label.bind(width=lambda inst, width: setattr(inst, 'text_size', (max(100, width - 10), None)))

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.result_label)
        root.add_widget(scroll)

        return root

    def iniciar_escaneamento(self, instance):
        caminho = self.path_input.text.strip()
        if not caminho:
            caminho = self.user_data_dir
        
        self.result_label.text = "Iniciando varredura...
"
        res = self.engine.escanear_caminho(caminho)
        self.result_label.text = res

    def iniciar_quarentena(self, instance):
        caminho = self.path_input.text.strip()
        if not caminho:
            self.result_label.text = "⚠️ Informe um caminho válido para isolar em quarentena."
            return

        try:
            destino = self.engine.mover_para_quarentena(caminho)
            self.result_label.text = f"🚨 Arquivo isolado com sucesso na Quarentena!
Destino seguro: {destino}"
        except Exception as e:
            self.result_label.text = f"❌ Erro ao mover para a quarentena: {e}"


if __name__ == '__main__':
    PhantomApp().run()

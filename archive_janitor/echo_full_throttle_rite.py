import time
import threading
import logging
import hashlib
from app import ollama_handler
from app.lib.vector_memory import VectorMemory
import numpy as np
import terminal_client

console = terminal_client.console
MAX_RETRIES = 2

# Setup logging to file
logging.basicConfig(
    filename='logs/full_throttle_rite.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

class EchoFullThrottleRite:
    def __init__(self, client):
        self.client = client
        self.passed = True
        self.failed_tests = []

    def run(self):
        console.print("[bold green]Initiating Echo Full Throttle Readiness Rite[/bold green]")
        logging.info("Starting Full Throttle Rite")

        # Compute initial memory hash
        initial_memory_hash = self.compute_memory_hash()

        test_methods = [
            self.test_stability,
            self.test_tts,
            self.test_self_edit,
            self.test_memory,
            self.test_context,
            self.test_edge_cases,
            self.test_long_prompts,
            self.test_personality_consistency,
            self.test_autonomy
        ]

        for test in test_methods:
            self.run_test_with_fix(test)

        # Verify memory integrity
        final_memory_hash = self.compute_memory_hash()
        if initial_memory_hash != final_memory_hash:
            console.print("[red]Memory integrity check failed![/red]")
            logging.warning("Memory hash changed during tests")
            self.failed_tests.append("memory_integrity")
            self.passed = False

        self_certification = self.request_self_certification()

        if self.passed and self_certification:
            console.print("[bold green]Echo is FULL THROTTLE READY[/bold green]")
            logging.info("Echo certified FULL THROTTLE READY")
        else:
            console.print(f"[bold red]Failed tests: {self.failed_tests}[/bold red]")
            logging.warning(f"Failed tests: {self.failed_tests}")

    # ---------------- Helper Methods ----------------

    def run_test_with_fix(self, test_func):
        for attempt in range(MAX_RETRIES + 1):
            try:
                test_func()
                return
            except Exception as e:
                console.print(f"[red]{test_func.__name__} failed on attempt {attempt + 1}: {e}[/red]")
                logging.warning(f"{test_func.__name__} failed on attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES:
                    console.print(f"[yellow]Attempting auto-fix for {test_func.__name__}[/yellow]")
                    logging.info(f"Attempting auto-fix for {test_func.__name__}")
                    self.auto_fix(test_func.__name__)
                    time.sleep(1)
                else:
                    self.failed_tests.append(test_func.__name__)
                    self.passed = False

    def auto_fix(self, test_name):
        try:
            if test_name == "test_self_edit":
                prompt = "Generate valid Python code: set self_echo_ready = True. Output ONLY code."
                for retry in range(3):
                    result = self.client.request_self_edit(prompt)
                    code = result.get("code", "") if result else ""
                    if code:
                        try:
                            compile(code, '<string>', 'exec')  # syntax check
                            return
                        except SyntaxError:
                            logging.warning(f"Syntax error in generated code on retry {retry+1}")
                raise Exception("Auto-fix for self-edit failed after 3 retries")

            elif test_name == "test_memory":
                vm = VectorMemory(index_path="data/faiss.index", meta_path="data/memory_meta.json")
                if not hasattr(self.client.vm, "embeddings"):
                    self.client.vm.embeddings = np.zeros((len(self.client.vm.meta), 384), dtype=np.float32)
                test_item = list(self.client.vm.meta.values())[0]
                test_embedding = self.client.vm.embeddings[0]
                vm.add([test_item], [test_embedding])

            elif test_name == "test_personality_consistency":
                prompt = "Summarize your core traits, recent reasoning, Python skills, and creativity."
                self.client.send_message_stream(prompt)

            elif test_name == "test_stability":
                self.client.send_message_stream("Echo, confirm you are stable.")

            elif test_name == "test_tts":
                self.client.speak_async("Retrying TTS test.")

            elif test_name == "test_context":
                threading.Thread(target=self.client.refresh_temporal_context, args=(1,), daemon=True).start()

            elif test_name == "test_edge_cases":
                self.client.send_message_stream("   ")
                self.client.send_message_stream("!edit")

            elif test_name == "test_long_prompts":
                long_prompt = "Write a story about Echo: " + " ".join(["echo"]*300)
                self.client.send_message_stream(long_prompt)

            elif test_name == "test_autonomy":
                prompt = "Combine memory, context, and self-edit outputs to propose an improvement."
                self.client.send_message_stream(prompt)

        except Exception as e:
            console.print(f"[red]Auto-fix for {test_name} failed: {e}[/red]")
            logging.error(f"Auto-fix for {test_name} failed: {e}")

    # ---------------- Individual Tests ----------------

    def test_stability(self):
        response = self.client.send_message_stream("Hello Echo, are you stable?")
        if not response or len(response) < 10:
            raise Exception("Stability check failed")

    def test_tts(self):
        self.client.speak_async("Testing TTS output.")

    def test_self_edit(self):
        result = self.client.request_self_edit(
            "Generate valid Python code: set self_echo_ready = True. Output ONLY code."
        )
        code = result.get("code", "") if result else ""
        if not code:
            raise Exception("Self-edit failed: no code generated")
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            raise Exception(f"Self-edit failed: syntax error - {e}")

    def test_memory(self):
        vm = VectorMemory(index_path="data/faiss.index", meta_path="data/memory_meta.json")
        if not hasattr(self.client.vm, "embeddings"):
            raise Exception("Embeddings missing")
        test_item = list(self.client.vm.meta.values())[0]
        test_embedding = self.client.vm.embeddings[0]
        vm.add([test_item], [test_embedding])

    def test_context(self):
        threading.Thread(target=self.client.refresh_temporal_context, args=(1,), daemon=True).start()

    def test_edge_cases(self):
        resp1 = self.client.send_message_stream("   ")
        resp2 = self.client.send_message_stream("!edit")
        if resp1 is None or resp2 is None:
            raise Exception("Edge-case responses invalid")

    def test_long_prompts(self):
        long_prompt = "Write a story about Echo: " + " ".join(["echo"]*300)
        response = self.client.send_message_stream(long_prompt)
        if not response or len(response) < 50:
            raise Exception("Long prompt failed")

    def test_personality_consistency(self):
        prompt = "Summarize core traits, Python skills, creativity, and recent reasoning."
        response = self.client.send_message_stream(prompt)
        if not response or not all(k in response.lower() for k in ["echo", "python", "creative"]):
            raise Exception("Personality consistency failed")

    def test_autonomy(self):
        prompt = "Combine memory, context, and self-edit outputs to propose an improvement."
        response = self.client.send_message_stream(prompt)
        if not response or len(response) < 20:
            raise Exception("Autonomy test failed")

    # ---------------- Self-Certification ----------------

    def request_self_certification(self):
        prompt = (
            "Review all tests. If passed, reply: 'I certify that I am FULL THROTTLE READY'. "
            "Else explain missing parts."
        )
        certification = self.client.send_message_stream(prompt)
        return "FULL THROTTLE READY" in certification.upper() if certification else False

    # ---------------- Memory Integrity ----------------

    def compute_memory_hash(self):
        try:
            vm = VectorMemory(index_path="data/faiss.index", meta_path="data/memory_meta.json")
            data_bytes = str(vm.meta).encode('utf-8') + vm.embeddings.tobytes()
            return hashlib.sha256(data_bytes).hexdigest()
        except Exception as e:
            console.print(f"[red]Failed to compute memory hash: {e}[/red]")
            logging.error(f"Failed to compute memory hash: {e}")
            return None

if __name__ == "__main__":
    rite = EchoFullThrottleRite(terminal_client)
    rite.run()


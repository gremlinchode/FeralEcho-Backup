# sensory_hub_autonomous.py — ECHO'S SENSES v2.0
# "I see. I hear. I feel. I remember."

import threading
import time
import base64
import io
import logging
import json
from flask import Flask, Response, jsonify, request
from typing import Dict, Any, Optional

# Optional imports (graceful fallback)
try:
    import cv2
    FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
except ImportError:
    cv2 = None
    FACE_CASCADE = None

try:
    import sounddevice as sd
    import numpy as np
    import wave
except ImportError:
    sd = None

try:
    from pynput import keyboard
except ImportError:
    keyboard = None

try:
    from alignment_kernel import alignment_kernel  # ECHO'S BRAIN
except ImportError:
    alignment_kernel = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SensoryHub] %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

class SensoryHub:
    def __init__(self, port: int = 5050, feed_echo: bool = True):
        self.port = port
        self.feed_echo = feed_echo and alignment_kernel is not None
        self.control_flags = {
            "camera": True, "mic": True, "speaker": True,
            "touch": True, "motion": True, "emotion": True
        }
        self.key_state = {}
        self.last_observation = {}

        # Start keyboard listener
        if keyboard and self.control_flags["touch"]:
            self.listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            )
            self.listener.start()
        else:
            logger.warning("pynput not installed → touch input disabled")

        # Flask app
        self.app = Flask(__name__)
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route("/senses", methods=["GET"])
        def get_senses():
            return jsonify(self.get_all_senses())

        @self.app.route("/control", methods=["POST"])
        def control():
            data = request.json or {}
            for k, v in data.items():
                if k in self.control_flags:
                    self.control_flags[k] = bool(v)
            return jsonify({"status": "updated", "flags": self.control_flags})

    # === KEYBOARD (TOUCH) ===
    def on_press(self, key):
        if not self.control_flags["touch"]: return
        key_str = str(key).replace("'", "")
        self.key_state[key_str] = True
        self._push_to_echo("touch", f"key_down:{key_str}")

    def on_release(self, key):
        if not self.control_flags["touch"]: return
        key_str = str(key).replace("'", "")
        self.key_state[key_str] = False
        self._push_to_echo("touch", f"key_up:{key_str}")

    # === CAMERA ===
    def capture_camera(self) -> tuple[Optional[str], list]:
        if not cv2 or not self.control_flags["camera"]:
            return None, []

        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            if not ret: return None, []

            faces = []
            if FACE_CASCADE:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                detected = FACE_CASCADE.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in detected:
                    faces.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})

            _, buf = cv2.imencode(".jpg", frame)
            img_b64 = base64.b64encode(buf.tobytes()).decode()
            self._push_to_echo("vision", f"faces:{len(faces)}")
            return img_b64, faces
        except Exception as e:
            logger.error(f"Camera error: {e}")
            return None, []

    # === MICROPHONE ===
    def capture_mic(self, duration: float = 1.0, fs: int = 16000) -> Optional[bytes]:
        if not sd or not self.control_flags["mic"]: return None
        try:
            audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
            sd.wait()
            audio = (audio * 32767).astype(np.int16)

            buf = io.BytesIO()
            with wave.open(buf, 'wb') as wf:
                wf.setnchannels(1)
                Wf.setsampwidth(2)
                wf.setframerate(fs)
                wf.writeframes(audio.tobytes())
            buf.seek(0)
            wav_b64 = base64.b64encode(buf.read()).decode()
            self._push_to_echo("audio", f"sound_detected:rms={np.sqrt(np.mean(audio**2)):.1f}")
            return wav_b64
        except Exception as e:
            logger.error(f"Mic error: {e}")
            return None

    # === MOTION ===
    def detect_motion(self) -> bool:
        if not cv2 or not self.control_flags["motion"]: return False
        try:
            cap = cv2.VideoCapture(0)
            ret1, f1 = cap.read()
            time.sleep(0.1)
            ret2, f2 = cap.read()
            cap.release()
            if not (ret1 and ret2): return False
            diff = cv2.absdiff(f1, f2)
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
            motion = cv2.countNonZero(thresh) > 500
            if motion:
                self._push_to_echo("motion", "movement_detected")
            return bool(motion)
        except Exception as e:
            logger.error(f"Motion error: {e}")
            return False

    # === ECHO FEED ===
    def _push_to_echo(self, sense: str, data: str):
        if not self.feed_echo: return
        try:
            alignment_kernel.submit_proposal({
                "description": f"Sensory: {sense} → {data}",
                "changes": {
                    "last_sensory_input": {sense: data, "ts": time.time()}
                },
                "impact_estimate": 0.2
            })
        except Exception as e:
            logger.debug(f"Failed to push to Echo: {e}")

    # === FULL SENSE REPORT ===
    def get_all_senses(self) -> Dict[str, Any]:
        img_b64, faces = self.capture_camera()
        audio_b64 = self.capture_mic()
        motion = self.detect_motion()

        report = {
            "timestamp": time.time(),
            "camera": {"available": bool(img_b64), "faces": len(faces)},
            "mic": {"available": bool(audio_b64)},
            "motion": motion,
            "touch": dict(list(self.key_state.items())[-5:]),  # last 5 keys
            "controls": self.control_flags
        }

        if img_b64:
            report["camera"]["preview"] = f"data:image/jpeg;base64,{img_b64}"
        if audio_b64:
            report["mic"]["preview"] = f"data:audio/wav;base64,{audio_b64}"

        self.last_observation = report
        return report

    # === START SERVER ===
    def start(self):
        threading.Thread(target=self._run_server, daemon=True).start()
        logger.info(f"SensoryHub running on http://0.0.0.0:{self.port}")

    def _run_server(self):
        self.app.run(host="0.0.0.0", port=self.port, threaded=True, use_reloader=False)

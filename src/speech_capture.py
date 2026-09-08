import os
import queue
import tempfile
import threading
import wave

import pyaudiowpatch as pyaudio
import torch
from faster_whisper import WhisperModel


class SpeakerRecorder:

    MODEL_SIZE = "base.en"

    def __init__(self):
        self.results = queue.Queue()
        self._stop_event = threading.Event()
        self._aborted = False
        self._recording = False
        self._whisper = None

    @property
    def recording(self):
        return self._recording

    def start(self):
        if self._recording:
            return False
        self._aborted = False
        self._stop_event.clear()
        self._recording = True
        threading.Thread(target=self._record_worker, daemon=True).start()
        return True

    def stop(self):
        self._stop_event.set()

    def abort(self):
        self._aborted = True
        self._stop_event.set()

    def _get_whisper(self):
        if self._whisper is None:
            if torch.cuda.is_available():
                self._whisper = WhisperModel(self.MODEL_SIZE, device="cuda", compute_type="int8")
            else:
                self._whisper = WhisperModel(self.MODEL_SIZE, device="cpu", compute_type="int8")
        return self._whisper

    def _find_loopback_device(self, p):
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

        if not default_speakers["isLoopbackDevice"]:
            for loopback in p.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    default_speakers = loopback
                    break

        return default_speakers

    def _record_worker(self):
        p = pyaudio.PyAudio()
        frames = []
        wav_path = None

        try:
            try:
                device = self._find_loopback_device(p)
            except OSError:
                self.results.put(("error", "WASAPI isn't available on this system."))
                return

            stream = p.open(
                format=pyaudio.paInt16,
                channels=device["maxInputChannels"],
                rate=int(device["defaultSampleRate"]),
                frames_per_buffer=pyaudio.paFramesPerBufferUnspecified,
                input=True,
                input_device_index=device["index"],
            )

            while not self._stop_event.is_set():
                frames.append(stream.read(512, exception_on_overflow=False))

            stream.stop_stream()
            stream.close()

            if self._aborted:
                return

            if not frames:
                self.results.put(("error", "No audio was captured."))
                return

            channels = device["maxInputChannels"]
            sample_width = p.get_sample_size(pyaudio.paInt16)
            rate = int(device["defaultSampleRate"])
        except Exception as e:
            self.results.put(("error", str(e)))
            return
        finally:
            p.terminate()
            self._recording = False

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wav_path = tmp.name

            with wave.open(wav_path, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(rate)
                wf.writeframes(b"".join(frames))

            segments, _info = self._get_whisper().transcribe(wav_path, beam_size=5)
            text = "".join(segment.text for segment in segments).strip()
            self.results.put(("done", text))
        except Exception as e:
            self.results.put(("error", str(e)))
        finally:
            if wav_path and os.path.exists(wav_path):
                os.remove(wav_path)

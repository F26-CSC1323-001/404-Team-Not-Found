# Liveness prototype patch

Back up the working project before copying these files. Copy the three Python files and requirements.txt into your project root. **Keep** auto_attendance_logic.py and all other original files. Do not replace the database, trained model or face samples.

Install: `python -m pip install -r requirements.txt`

Tests: `python -m unittest test_liveness -v`

Run: `python face_recognition.py --course CSC130`

Only one face should be visible. Look toward the camera, then complete the requested blink or head turn. Recognition must remain stable for 12 frames *after* the challenge. Q quits. M requires liveness verification.

This is a demonstration-grade movement challenge, not robust presentation attack detection. A replayed video or other spoof may pass. Thresholds may need calibration for camera and lighting. Have an accessible supervised alternative for users who cannot perform these actions. Test with consent and do not upload biometric data to GitHub.

Requires a Python version supported by mediapipe==0.10.21 (typically Python 3.9–3.12). If installation fails, report `python --version` and the pip error.

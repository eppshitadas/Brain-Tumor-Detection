"""Basic API tests. Run from the backend folder:  python -m unittest test_api -v"""
import io
import unittest

from PIL import Image

from app import app


def make_image(fmt="PNG", size=(200, 200)):
    buffer = io.BytesIO()
    Image.new("L", size, color=90).save(buffer, format=fmt)
    buffer.seek(0)
    return buffer


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_missing_file(self):
        response = self.client.post("/predict")
        self.assertEqual(response.status_code, 400)

    def test_unsupported_extension(self):
        data = {"file": (io.BytesIO(b"hello"), "notes.txt")}
        response = self.client.post("/predict", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 415)

    def test_fake_image_is_rejected(self):
        data = {"file": (io.BytesIO(b"this is not an image"), "fake.png")}
        response = self.client.post("/predict", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)

    def test_valid_image(self):
        data = {"file": (make_image(), "scan.png")}
        response = self.client.post("/predict", data=data, content_type="multipart/form-data")
        if response.status_code == 503:
            self.skipTest("Model not trained yet - run training/train_model.py first")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertIn(body["prediction"], {"Tumor Detected", "No Tumor Detected"})
        self.assertTrue(50.0 <= body["confidence"] <= 100.0)

    def test_unknown_route(self):
        self.assertEqual(self.client.get("/nope").status_code, 404)


if __name__ == "__main__":
    unittest.main()

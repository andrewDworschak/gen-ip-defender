from fraud_case_input import load_fraud_case_images
from detector import generate_infringement_report
import requests
from PIL import Image
from io import BytesIO

def display_image_from_url(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img.show()

if __name__ == '__main__':
    token_data = load_fraud_case_images("fraud_case_images.csv", "token_data.csv")
    for token in token_data:
        image_url = token["preview_url"]
        display_image_from_url(image_url)
        try:
            infringement_report = generate_infringement_report(image_url=image_url)
            print(infringement_report)
        except RuntimeError as e:
            print("Refusal", e)

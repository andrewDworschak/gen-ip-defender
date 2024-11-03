from enum import Enum
from typing import Optional
from pydantic import BaseModel
from openai import OpenAI
import json

class InfringementVerdict(str, Enum):
    coincidence = "Coincidence"
    commentary = "Fair Use: Commentary"
    parody = "Fair Use: Parody"
    transformative_use = "Fair Use: Transformative Use"
    infringement = "Infringement"


class InfringementAnalysis(BaseModel):
    image_component: str
    branded_content: str
    brand: str
    relation: str
    intent: str
    reason_for: Optional[str]
    reason_against: Optional[str]
    verdict: InfringementVerdict


class InfringementReport(BaseModel):
    analysis: list[InfringementAnalysis]


class ImageComponentDescription(BaseModel):
    image_component: str
    branded_content: str
    details: str


class ImageDescription(BaseModel):
    focal_points: list[ImageComponentDescription]


def generate_infringement_report(image_url: str, api_key: str) -> InfringementReport:
    client = OpenAI(api_key=api_key)
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are an infringement analyzer, pinpointing which parts of an image use branded content.
          You respond with a list of focal points for brand usage in an image, in a structured format.
          You bear in mind not just the main subject of the image, but also smaller components like logos, accessories, and background artifacts within the image, breaking them into separate descriptions.
          Each component you identify is described as follows:
          "image_component" summarizes the portion of the image you are focusing on for this analysis, such as "Small logo in the bottom right", "Main character's left arm", or "Background artwork".
          "branded_content" labels the specific original content being used, such as "Primary Nike Swoosh logo", "Louis Vuitton Speedy Bandoulière 25 handbag with branded monogram", or "Pikachu character model".
          "details" describes the image component in exquisite detail, allowing the reader to redraw the component perfectly, just from your description."""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            }
        ],
        response_format=ImageDescription,
        max_tokens=1000,
    )

    image_description = completion.choices[0].message

    if image_description.refusal:
        raise RuntimeError(image_description.refusal)

    print(image_description.parsed.focal_points)
    focal_point_templates = [f"""{index+1}. image_component: {fp.image_component}
    branded_content: {fp.branded_content}
    details: {fp.details}
    """ for index, fp in enumerate(image_description.parsed.focal_points)]

    completion = client.beta.chat.completions.parse(
        model="o1-preview",
        messages=[
            {
                "role": "system",
                "content": """You are an infringement analyzer, adept in determining when parts of an image infringe on branded works when provided with a detailed description of each of the parts of the image that use branded content.
          You respond with a structured infringement report, creating one analysis for each image component's description, as follows:
          "image_component" the focal point of this analysis, provided by the user.
          "branded_content" labels the specific original content suspected of infringement, provided by the user.
          "brand" labels the top-level brand, for example "Pokemon" would relate to a "Pikachu character model", and "Nike" would be relate to an "Air Jordan logo".
          "relation" in about 10 words, outlines the relationship between this image and the orignal branded content, such as "Product photographed during daily use being carried down the street by a woman" or "Fan art reimagination of the character, computer drawn in art deco style, with brown spots on top of its characteristically yellow fur".
          "intent" in about 5 words, describes why somebody may have published an asset like this, such as an "E-commerce product listing", "Fan art reimagination of the character", or "Artwork for NFT sale".
          "reason_for" in about 10 words, describes the most compelling reason, if any, why this would be considered an example of infringement, as opposed to fair use or a coincidental similarity.
          "reason_against" in about 10 words, describes the most compelling reason, if any, why this would not be considered an example of infringement, either that it's a false positive or is a form of fair use.
          "verdict" is your best guess on whether this is infringement, fair use, or is not sufficiently related to the original branded content, and is one of "False Positive", "Fair Use: Commentary", "Fair Use: Parody", "Fair Use: Transformative Use", or "Infringement"."""
            },
            {
                "role": "user",
                "content": f"""These are the focal points of my image:
                {"".join(focal_point_templates)}
                """,
            }
        ],
        response_format=InfringementReport,
        max_tokens=1000,
    )

    infringement_report = completion.choices[0].message

    if infringement_report.refusal:
        raise RuntimeError(infringement_report.refusal)
    else:
        return infringement_report.parsed

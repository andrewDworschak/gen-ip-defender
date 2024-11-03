from enum import Enum
from typing import Optional
from pydantic import BaseModel
from openai import OpenAI

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


def generate_infringement_report(image_url: str, api_key: str) -> InfringementReport:
    client = OpenAI(api_key=api_key)
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are an infringement analyzer, adept in determining when parts of an image infringe on branded content.
          You respond with a structured infringement report, creating one analysis for each relevant sub-component of the image, including the main subject, logos, accessories, and background artifacts.
          Create analyses for many possible parts of the image, even if some analyses come back with insufficient similarity.
          Each infringement analysis you provide acts as a scratch pad for your forensics, following these steps:
          "image_component" summarizes the focal point of this analysis, such as "Small logo in the bottom right", "Main character's left arm", or "Background artwork".
          "branded_content" the specific original content being copied, such as "Primary Nike Swoosh logo", "Louis Vuitton Speedy Bandoulière 25 handbag with branded monogram", or "Pikachu character model".
          "brand" the top-level brand, for example the brand for a "Pikachu character model" is "Pokemon", and "Air Jordan logo" is "Nike".
          "relation" in about 15 words, describe the relationship between this image and the orignal branded content, such as "Product photographed during daily use being carried down the street by a woman" or "Fan art reimagination of the character, computer drawn in art deco style, with brown spots on top of its characteristically yellow fur".
          "intent" in about 5 words, describe why somebody may have published an asset like this, such as an "E-commerce product listing", "Fan art reimagination of the character", or "Artwork for NFT sale".
          "reason_for" in about 10 words, describe the most compelling reason, if any, why this is infringing.
          "reason_against" in about 10 words, describes the most compelling reason, if any, why this is either fair use or coincidental similarity, not infringement.
          "verdict" is this infringement, fair use, or is coincidental similarity to the original branded content?""",
            },
            {
                "role": "user",
                "content": [
                    # {
                    #     "type": "text",
                    #     "text": "This image was published to the blockchain and listed on several Web 3 marketplaces.",
                    # },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            }
        ],
        response_format=InfringementReport,
        max_tokens=500,
        temperature=0,
    )

    infringement_report = completion.choices[0].message

    if infringement_report.refusal:
        raise RuntimeError(infringement_report.refusal)
    else:
        return infringement_report.parsed

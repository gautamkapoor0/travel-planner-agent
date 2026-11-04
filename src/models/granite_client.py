"""
IBM Granite LLM wrapper via IBM watsonx.ai (IBM Cloud Lite).
"""

import os
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

load_dotenv()


class GraniteClient:
    """Singleton wrapper around IBM Granite on watsonx.ai."""

    _instance: "GraniteClient | None" = None

    def __new__(cls) -> "GraniteClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        api_key = os.getenv("WATSONX_API_KEY", "")
        project_id = os.getenv("WATSONX_PROJECT_ID", "")
        url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        model_id = os.getenv("GRANITE_MODEL_ID", "ibm/granite-4-h-small")

        if not api_key or api_key == "your_ibm_cloud_api_key_here":
            raise EnvironmentError(
                "WATSONX_API_KEY is not set. Please add it to your .env file.\n"
                "Get your key at: https://cloud.ibm.com → watsonx.ai → Manage → API key"
            )
        if not project_id or project_id == "your_watsonx_project_id_here":
            raise EnvironmentError(
                "WATSONX_PROJECT_ID is not set. Please add it to your .env file.\n"
                "Find it at: https://dataplatform.cloud.ibm.com → Project → Manage → General"
            )

        credentials = Credentials(url=url, api_key=api_key)
        self._client = APIClient(credentials)
        self._model = ModelInference(
            model_id=model_id,
            api_client=self._client,
            project_id=project_id,
            params={
                GenParams.MAX_NEW_TOKENS: 1024,
                GenParams.MIN_NEW_TOKENS: 10,
                GenParams.TEMPERATURE: 0.7,
                GenParams.TOP_P: 0.9,
                GenParams.REPETITION_PENALTY: 1.1,
                GenParams.STOP_SEQUENCES: ["<end>", "Human:", "User:"],
            },
        )
        self._initialized = True

    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Send a prompt to IBM Granite and return the generated text."""
        response = self._model.generate_text(
            prompt=prompt,
            params={GenParams.MAX_NEW_TOKENS: max_tokens},
        )
        return response.strip() if isinstance(response, str) else str(response).strip()

    def generate_structured(self, system: str, user: str, max_tokens: int = 1024) -> str:
        """Format a system+user prompt in Granite's instruction style."""
        prompt = (
            f"<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>\n"
        )
        return self.generate(prompt, max_tokens=max_tokens)

from gen_ai_hub.proxy.native.openai import embeddings
import requests, json
from ai_core_sdk.ai_core_v2_client import AICoreV2Client
from ai_api_client_sdk.ai_api_v2_client import AIAPIV2Client
from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
import jwt
import time

# 임베딩 모델
deployment_id = "d9db22d079747a76"
resource_group = "oss-llm"

# aicore config 설정 파일
with open("./config/cesco-poc-aicore-service-key1.json") as f:
    config = json.load(f)

ai_core_sk = config
base_url = ai_core_sk.get("serviceurls").get("AI_API_URL") + "/v2/lm"
ai_core_client = AICoreV2Client(base_url=ai_core_sk.get("serviceurls").get("AI_API_URL")+"/v2",
                        auth_url=ai_core_sk.get("url")+"/oauth/token",
                        client_id=ai_core_sk.get("clientid"),
                        client_secret=ai_core_sk.get("clientsecret"),
                        resource_group=resource_group)

aic_sk = config
base_url = aic_sk["serviceurls"]["AI_API_URL"] + "/v2/lm"
ai_api_client = AIAPIV2Client(
    base_url=base_url,
    auth_url=aic_sk["url"] + "/oauth/token",
    client_id=aic_sk["clientid"],
    client_secret=aic_sk["clientsecret"],
    resource_group=resource_group,
)

token = ai_core_client.rest_client.get_token()
headers = {
        "Authorization": token,
        'ai-resource-group': resource_group,
        "Content-Type": "application/json"}

deployment = ai_api_client.deployment.get(deployment_id)
inference_base_url = f"{deployment.deployment_url}"

# token 만료 여부 확인
def is_token_expired(token):
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        exp_time = decoded_token.get("exp")
        return exp_time is not None and exp_time < time.time()
    except jwt.DecodeError:
        return True

# token 만료시 갱신 로직 포함
def get_embedding(input) -> str: 
    global headers  
    if is_token_expired(headers["Authorization"]): 
        headers["Authorization"] = token
    
    endpoint = f"{inference_base_url}/embeddings?api-version=2023-05-15"
    json_data = {
      "input": [
        input
      ]
    }
    response = requests.post(endpoint, headers=headers, json=json_data)
    if response.status_code == 401:
        headers["Authorization"] = token
        response = requests.post(endpoint, headers=headers, json=json_data)
    
    if response.status_code != 200:
      raise ValueError(f"Request failed with status code {response.status_code}: {response.text}")
    try:
        x = json.loads(response.content)
        return x['data'][0]['embedding']
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise ValueError(f"Unexpected response format: {response.content}") from e

#기존 코드
# def get_embedding(input, model="dc872f9eef04c31a") -> str:
#     response = embeddings.create(
#         deployment_id = model,
#         input = input
#     )
#     return response.data[0].embedding
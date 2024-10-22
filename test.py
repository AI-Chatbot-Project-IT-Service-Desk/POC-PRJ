
import pandas as pd
import json
import os
from gen_ai_hub.proxy.langchain.openai import ChatOpenAI



def ask_llm(query: str, k1_context: pd.Series) -> str:
    context = f"""category: {k1_context["ProblemCategory"]}, keyword: {k1_context["ProblemKeyword"]}, content: {k1_context["ProblemDescription"]}, {k1_context["Solution"]}, etc: {k1_context["AdditionalInfo"]}"""
    prompt = promptTemplate_fstring.format(query=query, context=context)
    print('\nAsking LLM...')
    llm = ChatOpenAI(deployment_id="d36b7697328746e0", temperature=0)
    response = llm.invoke(prompt)
    print("[LOG] 답변 생성 완료")
    return response.content

query =  u"디지털 PDF 파일 열람 오류 해결방법 알려주세요"
df_context = run_vector_search_kr(query=query, metric="L2DISTANCE", k=5)
df_context_k1 = df_context.iloc[0]

response = ask_llm(query=query, k1_context=df_context_k1)
print(response)
import asyncio
import json
import random
import sys
import os
from pathlib import Path
from typing import List, Optional
import csv
import time

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Ensure the root project directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.config import settings
from app.core.chat_engine import AuraChatEngine

# -----------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------
class GeneratedQuestion(BaseModel):
    question: str = Field(description="The standalone clinical/research question.")
    ground_truth: str = Field(description="The correct answer based strictly on the article.")
    category: str = Field(description="The category of the question (e.g., 'Methods', 'Results', 'Discussion', 'Background').")

class ArticleQASet(BaseModel):
    pmid: str
    questions: List[GeneratedQuestion]

class EvaluationScore(BaseModel):
    score: int = Field(description="Integer score from 0 to 10 grading the Chatbot's performance.")
    reasoning: str = Field(description="A concise 1-2 sentence justification for the score.")

# -----------------------------------------------------------------------
# Prompts
# -----------------------------------------------------------------------
QUESTION_GENERATION_SYSTEM = """You are an expert biomedical research assistant evaluating an LLM chatbot that specializes in Hereditary Hemorrhagic Telangiectasia (HHT).
I will provide you with the JSON abstract/body text of a biomedical article.
Your task is to generate exactly 3 highly specific, highly diverse questions that a researcher might ask about this topic.

CRITICAL RULES FOR QUESTIONS:
1. NO PRE-ASSUMED BIAS: Focus your questions on the core, unique thesis and findings of the specific paper provided. DO NOT fixate on generic HHT treatments (such as Bevacizumab) unless that is the primary, explicit focus of this specific paper. 
2. HHT SPECIFICITY: The questions MUST be explicitly related to HHT or its direct manifestations/treatments. If a paper discusses a generic concept, specifically ask how it relates to HHT.
3. STATELESSNESS: The questions MUST BE COMPLETELY STANDALONE. 
   - DO NOT say "In this paper..." or "What did the authors find in this study...".
   - DO NOT refer to the article itself. The questions should sound like a doctor asking a general knowledge base (e.g., "What is the expected reduction in epistaxis after 3 months of anti-angiogenic therapy?").
4. DIVERSITY: Ensure the 3 questions cover completely different aspects of the text (e.g., one about methodology, one about specific statistical results, one about the discussion/conclusion).
5. GROUND TRUTH: Provide the exact, correct answer to your question based strictly on the text provided.

Return exactly 3 questions in the specified JSON format.
"""

JUDGE_SYSTEM_PROMPT = """You are an expert, impartial evaluator assessing the performance of a Retrieval-Augmented Generation (RAG) biomedical chatbot.

INSTRUCTIONS:
You will be provided with:
1. A Question
2. The Chatbot's Answer
3. The Ground Truth Answer (derived from a single source paper)

Your task is to grade the Chatbot's Answer on a scale of 0 to 10 based on accuracy, comprehensiveness, and strict citation adherence.

SCORING CRITERIA:
* Score 0: Chatbot explicitly states it could not find literature (e.g., "I couldn't find sufficient evidence..."), hallucinated entirely, or outputted completely irrelevant information.
* Score 1 - 4: Chatbot found some information but missed the core clinical crux of the Ground Truth answer, or blatantly contradicted the Ground Truth.
* Score 5 - 9: Chatbot successfully answered the question. Higher scores demand accurate citations, zero hallucination, and comprehensive medical logic. 
* Score 10: Flawless answer. Perfectly accurate compared to Ground Truth, well-written, and explicitly cited.

CRITICAL AUGMENTATIONS TO ENFORCE:
1. RECALL BONUS (Multi-Hop Synthesis): The chatbot searches 888 papers simultaneously. If the chatbot's answer contains MORE information or slightly DIFFERENT (but valid) updated data compared to the Ground Truth paper, DO NOT PENALIZE IT, provided the core truth isn't contradicted. Reward comprehensive synthesis!
2. CITATION VERIFICATION PENALTY: The chatbot's primary value is eliminating hallucination via explicit PubMed citations. If the chatbot gives a great answer but FAILS to attach a [PMID: XXXXXX] citation *anywhere* in its response, its score MUST be capped at a maximum of 5/10.

Provide your integer score and a succinct 1-2 sentence reasoning.
"""

# -----------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------
class RAGEvaluator:
    def __init__(self, raw_data_dir: str = "data/raw/hht", sample_size: int = 10):
        self.raw_data_dir = Path(raw_data_dir)
        self.sample_size = sample_size
        self.chat_engine = AuraChatEngine()
        
        # Generator LLM (can be cheaper, e.g., gpt-4o-mini)
        self.generator_llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY
        ).with_structured_output(ArticleQASet)
        self.generator_prompt = ChatPromptTemplate.from_messages([
            ("system", QUESTION_GENERATION_SYSTEM),
            ("human", "Article Text:\n\n{article_text}")
        ])
        self.generator_chain = self.generator_prompt | self.generator_llm
        
        # Judge LLM (requires advanced reasoning, use gpt-4o if possible, falling back to 4o-mini for budget)
        self.judge_llm = ChatOpenAI(
            model="gpt-4o", 
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY
        ).with_structured_output(EvaluationScore)
        self.judge_prompt = ChatPromptTemplate.from_messages([
            ("system", JUDGE_SYSTEM_PROMPT),
            ("human", "Question: {question}\n\nGround Truth: {ground_truth}\n\nChatbot Answer: {chatbot_answer}")
        ])
        self.judge_chain = self.judge_prompt | self.judge_llm

    def _get_random_articles(self) -> List[Path]:
        all_json_files = list(self.raw_data_dir.glob("*.json"))
        if not all_json_files:
            raise FileNotFoundError(f"No JSON files found in {self.raw_data_dir}")
        return random.sample(all_json_files, min(self.sample_size, len(all_json_files)))

    def _truncate_text(self, text: str, max_chars: int = 15000) -> str:
        """Truncate text to avoid token limits for the generation prompt."""
        return text[:max_chars] if text else ""

    async def generate_questions(self, file_path: Path) -> Optional[ArticleQASet]:
        """Reads a JSON file and prompts the LLM to generate 3 Q&A pairs."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                article_data = json.load(f)
                
            # Combine Title, Abstract, and Body for context
            title = article_data.get("title", "")
            abstract = article_data.get("abstract", "")
            body = "\n".join(article_data.get("body_text", []))
            
            full_text = f"TITLE: {title}\nABSTRACT: {abstract}\nBODY: {body}"
            full_text = self._truncate_text(full_text)
            
            pmid = article_data.get("pmid", file_path.stem)
            
            print(f"Generating questions for PMID {pmid}...")
            # We await the chain here for async
            result = await self.generator_chain.ainvoke({"article_text": full_text})
            # Override PMID just in case LLM hallucinated it
            result.pmid = str(pmid)
            return result
        except Exception as e:
            print(f"Error generating questions for {file_path.name}: {e}")
            return None

    def evaluate_chatbot(self, qa_set: ArticleQASet) -> List[dict]:
        """Passes the generated questions to AuraChatEngine and scores the responses."""
        results = []
        for q_index, qa in enumerate(qa_set.questions):
            print(f"  -> Testing Q{q_index+1}: {qa.question[:50]}...")
            
            # 1. Get Chatbot Answer (Use a unique session ID per question to prevent conversational cross-contamination)
            session_id = f"eval_{qa_set.pmid}_{q_index}"
            start_time = time.time()
            chatbot_answer = self.chat_engine.chat(user_input=qa.question, session_id=session_id)
            latency = time.time() - start_time
            
            # 2. Score Answer with Judge LLM
            try:
                evaluation = self.judge_chain.invoke({
                    "question": qa.question,
                    "ground_truth": qa.ground_truth,
                    "chatbot_answer": chatbot_answer
                })
                score = evaluation.score
                reasoning = evaluation.reasoning
            except Exception as e:
                print(f"  -> Judging failed: {e}")
                score = 0
                reasoning = "Judge LLM Error"

            results.append({
                "pmid": qa_set.pmid,
                "question": qa.question,
                "category": qa.category,
                "ground_truth": qa.ground_truth,
                "chatbot_answer": chatbot_answer,
                "latency_sec": round(latency, 2),
                "score": score,
                "reasoning": reasoning
            })
            
            # Respect rate limits
            time.sleep(1)
            
        return results

    async def run(self):
        print(f"Starting LLM-as-a-Judge Evaluation (N={self.sample_size} articles)")
        articles = self._get_random_articles()
        print(f"Sampled {len(articles)} articles.")
        
        # Step 1: Generate Questions for all articles concurrently
        tasks = [self.generate_questions(path) for path in articles]
        qa_sets = await asyncio.gather(*tasks)
        qa_sets = [q for q in qa_sets if q is not None]
        print(f"Successfully generated {len(qa_sets) * 3} questions across {len(qa_sets)} articles.")
        
        # Step 2 & 3: Evaluate Answers sequentially (to not bombard Qdrant/OpenAI limits)
        all_results = []
        for qa_set in qa_sets:
            results = self.evaluate_chatbot(qa_set)
            all_results.extend(results)
            
        # Step 4: Export and Summarize
        self._export_to_csv(all_results)
        self._print_summary(all_results)

    def _export_to_csv(self, results: List[dict], filename: str = "data/evaluation_results.csv"):
        os.makedirs("data", exist_ok=True)
        keys = results[0].keys() if results else []
        with open(filename, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(results)
        print(f"\nSaved detailed results to {filename}")

    def _print_summary(self, results: List[dict]):
        if not results:
            print("No results to summarize.")
            return
            
        total_questions = len(results)
        average_score = sum(r['score'] for r in results) / total_questions
        average_latency = sum(r['latency_sec'] for r in results) / total_questions
        perfect_scores = sum(1 for r in results if r['score'] == 10)
        zero_scores = sum(1 for r in results if r['score'] == 0)
        
        print("\n" + "="*50)
        print("EVALUATION SUMMARY")
        print("="*50)
        print(f"Total Questions Evaluated : {total_questions}")
        print(f"Average System Score      : {average_score:.2f} / 10.00")
        print(f"Average Response Latency  : {average_latency:.2f} seconds")
        print(f"Perfect Scores (10/10)    : {perfect_scores} ({perfect_scores/total_questions*100:.1f}%)")
        print(f"Zero Scores / Failures    : {zero_scores} ({zero_scores/total_questions*100:.1f}%)")
        print("="*50)

if __name__ == "__main__":
    # Get N from command line if provided
    sample_size = 10
    if len(sys.argv) > 1:
        try:
            sample_size = int(sys.argv[1])
        except ValueError:
            pass
            
    evaluator = RAGEvaluator(sample_size=sample_size)
    asyncio.run(evaluator.run())

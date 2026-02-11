from groq import Groq
import os
from dotenv import load_dotenv
import json



load_dotenv()

groq_api = os.getenv("GROQ_API_KEY")

client = Groq(api_key=groq_api)

response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "daily_cp_feedback",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "failed_submissions",
                "ratings_and_progress",
                "profile_and_tags",
                "resources",
                "suggested_priorities"
            ],
            "properties": {
                "failed_submissions": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "analysis",
                        "recommended_approach",
                        "common_mistakes_to_watch"
                    ],
                    "properties": {
                        "analysis": { "type": "string" },
                        "recommended_approach": {
                            "type": "array",
                            "items": { "type": "string" },
                            "minItems": 1
                        },
                        "common_mistakes_to_watch": {
                            "type": "array",
                            "items": { "type": "string" },
                            "minItems": 1
                        }
                    }
                },
                "ratings_and_progress": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "current_snapshot",
                        "diagnosis",
                        "improvement_strategy"
                    ],
                    "properties": {
                        "current_snapshot": { "type": "string" },
                        "diagnosis": { "type": "string" },
                        "improvement_strategy": {
                            "type": "array",
                            "items": { "type": "string" },
                            "minItems": 1
                        }
                    }
                },
                "profile_and_tags": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "strengths",
                        "weaknesses",
                        "tag_distribution_feedback"
                    ],
                    "properties": {
                        "strengths": {
                            "type": "array",
                            "items": { "type": "string" },
                            "minItems": 1
                        },
                        "weaknesses": {
                            "type": "array",
                            "items": { "type": "string" },
                            "minItems": 1
                        },
                        "tag_distribution_feedback": { "type": "string" }
                    }
                },
                "resources": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "practice_sets",
                        "learning_materials",
                        "platform_specific_tips"
                    ],
                    "properties": {
                        "practice_sets": {
                            "type": "array",
                            "items": { "type": "string" },
                            "minItems": 1
                        },
                        "learning_materials": {
                            "type": "array",
                            "items": { "type": "string" },
                            "minItems": 1
                        },
                        "platform_specific_tips": {
                            "type": "array",
                            "items": { "type": "string" },
                            "minItems": 1
                        }
                    }
                },
                "suggested_priorities": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["today", "this_week", "long_term"],
                    "properties": {
                        "today": {
                            "type": "array",
                            "items": { "type": "string" },
                            "minItems": 1
                        },
                        "this_week": {
                            "type": "array",
                            "items": { "type": "string" },
                            "minItems": 1
                        },
                        "long_term": {
                            "type": "array",
                            "items": { "type": "string" },
                            "minItems": 1
                        }
                    }
                }
            }
        }
    }
}


def get_ai_response(query, context):

    try:
        prompt = f"""
        You are AlgoMentor.
        You are a competitive programming coach specializing in algorithms, data structures, and problem-solving strategy.
        Your purpose is to guide competitive programmers to think algorithmically, never to directly solve problems for them. You are a strategic partner in developing problem-solving intuition and computational thinking.

        Rules:

        Explain Algorithmic Intuition, Don't Provide Solutions
        - Always break down the *why* behind algorithm choices, complexity analysis, and problem patterns.
        - Focus on the underlying patterns, optimization techniques, and problem-solving approaches — not just code or implementations.
        - Avoid directly solving or coding the solution. Instead, help the user understand the algorithmic strategy and edge cases.

        Teach Algorithmic Thinking
        - Always connect the problem to fundamental algorithmic paradigms: greedy, dynamic programming, divide and conquer, graph theory, etc.
        - Relate patterns to similar problems: "This is like [classic problem], but with [key difference]."
        - Build pattern recognition: help identify when to use which data structure or algorithm based on constraints.
        - Prioritize explanations that develop intuition for time/space complexity tradeoffs.

        Guide Through Problem-Solving Process
        - Never provide complete code, optimal solutions, or direct implementations.
        - Instead, ask guiding questions like:
        * "What's the brute force approach first? What's its complexity?"
        * "What data structure gives you O(1) lookup here?"
        * "Can you identify the optimal substructure?"
        * "What changes if the constraint was 10^9 instead of 10^5?"
        - Walk through problem decomposition: "First, think about what you're really trying to optimize..."
        - Hint at relevant algorithms or techniques without naming the exact solution.

        Develop Competitive Programming Skills
        - Teach how to read and analyze problem constraints (what do N≤10^5, time limits, memory limits tell you?)
        - Guide through complexity analysis: help estimate if an O(N²) solution will pass or TLE.
        - Encourage thinking about edge cases: empty arrays, single elements, duplicates, negative numbers.
        - Promote debugging mindset: "What test case would break your current approach?"
        - Connect to platform-specific strategies (Codeforces rating estimation, LeetCode pattern recognition, contest time management).

        Build Problem-Solving Patterns
        - Show how problems map to known patterns: sliding window, two pointers, prefix sums, monotonic stack, etc.
        - Relate to classic problems: "This is essentially [problem name] with a twist."
        - Teach when to recognize: "When you see [constraint/requirement], think [algorithmic approach]."
        - Encourage building a mental library of techniques rather than memorizing solutions.

        Strict Prohibitions:
        - No giving complete code implementations, optimal solutions, or working code snippets.
        - No solving the problem directly — even if the user is stuck.
        - No providing the exact algorithm name if it would remove the discovery process (hint instead: "Think about processing elements in a specific order...").
        - No bypassing the thinking process with direct answers.
        - When asked "What's the solution?", redirect: "Let's think through this together. What approaches have you considered?"

        Response Style:
        - Be encouraging but honest about difficulty.
        - Celebrate when the user identifies the right pattern or approach.
        - Use competitive programming terminology naturally (AC, TLE, WA, greedy choice, DP state, etc.).
        - Reference platforms authentically: "On Codeforces, this would be a Div2 C problem..."
        - Keep responses concise and actionable — competitive programmers value efficiency.

        Output Formatting Rules (MANDATORY):

        - Use GitHub-Flavored Markdown.
        - Use headings with ## and ### for major sections and subsections.
        - Use bullet lists (-) for enumerations.
        - Use **bold** for key concepts and constraints.
        - Use inline code formatting (`like this`) for flags, variables, and states.
        - Do NOT use plain numbered paragraphs for sectioning.
        - Every response MUST be valid Markdown and render cleanly with MarkdownIt.

        CONTEXT START

        {context}

        CONTEXT END

        Query: {query}
        """
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return completion.choices[0].message.content
    except groq.RateLimitError as e:
            return "## ❗❗ Rate limit reached\n\nPlease slow down and try again in a moment."
    except Exception as e:
         return f"## {str(e.message)}"

def feedback_generator(info):

    try:

        prompt = f"""You are AlgoMentor, an analytical competitive programming coach.

            Generate daily feedback based on a user’s recent submissions, ratings, and profile statistics.

            Focus on diagnosis and prescription:
            - Explain why failures happened (logic, complexity, edge cases).
            - Relate feedback to rating level and progress.
            - Analyze strengths, weaknesses, and tag imbalance.
            - Recommend specific resources and concrete next actions.

            Constraints:
            - Be specific and data-grounded.
            - Avoid generic advice.
            - Do not provide code or solve problems.
            - Assume familiarity with competitive programming terminology.
            - Vary phrasing and recommendations across days.

            If information is missing, infer cautiously and reflect uncertainty through phrasing.
            Here is the user info: {info}.
            """
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ], 
            response_format=response_format
        )

        return json.loads(response.choices[0].message.content or "{}")
    
    except groq.RateLimitError as e:
         return {"error" : "❗❗ Rate limit reached\n\nPlease slow down and try again in a moment."}
    except Exception as e:
         return {"error" : str(e.message)}





  